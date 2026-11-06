"""Placing sounds so nothing runs across a cut by accident (docs/AUDIO.md, "The cue sheet").

Every sound is placed in a clip of the timeline and cut off at that clip's end, with a short fade, unless the placement
says how far it may run (`until`: a later clip's name, or (clip, frame)). A sound that starts before its clip (a
prelap) must say how far back it may start (`prelap`). Every placement is recorded; `export` writes them into the
timeline file, where tools/verify/audio.py lists what crosses every cut and fails what wasn't declared.

    from cues import Mix, load
    mix = Mix(Timeline.load("cut.json"))
    mix.place("sfx", load("boom.wav"), "hook", at=1.5, gain_db=-6, label="boom")
    mix.place("music", load("theme.wav"), "hook", until="ending", label="theme")   # a declared bridge
    mix.silence(4.0, 4.25, "the beat before the reveal")
    out = mix.render({"voice": 0, "music": -8, "sfx": -3})
    mix.write("build/mix.wav", out); mix.export("cut.json")

Times are seconds unless `frames=True`. Audio is float stereo at `sr`.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

import numpy as np
import soundfile as sf
from scipy import signal as sps

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "verify"))
from timeline import Timeline  # noqa: E402


def load(path: str, sr: int = 48000) -> np.ndarray:
    """A sound file as float stereo at `sr`."""
    x, rate = sf.read(path, always_2d=True, dtype="float64")
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    x = x[:, :2]
    if rate != sr:
        g = np.gcd(int(rate), int(sr))
        x = sps.resample_poly(x, sr // g, int(rate) // g, axis=0)
    return x


def _stereo(x: np.ndarray, pan: float) -> np.ndarray:
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    if pan:
        left, right = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        x = np.stack([x[:, 0] * left * 1.414, x[:, 1] * right * 1.414], axis=1)
    return x


class Mix:
    def __init__(self, timeline: Timeline, sr: int = 48000, buses=("voice", "music", "sfx", "ambience")):
        self.tl = timeline
        self.sr = sr
        n = int((timeline.duration() + 2.0) * sr)
        self.buses: dict[str, np.ndarray] = {b: np.zeros((n, 2)) for b in buses}
        self.cues: list[dict[str, Any]] = []
        self.silences: list[dict[str, Any]] = []

    def _at(self, clip: str, frames: float = 0) -> float:
        return self.tl.sec(self.tl.clip(clip)["start"] + frames)

    def _end(self, clip: str) -> float:
        c = self.tl.clip(clip)
        return self.tl.sec(c["start"] + c["frames"])

    def place(self, bus: str, sound: np.ndarray, clip: str, at: float = 0.0, gain_db: float = 0.0, pan: float = 0.0,
              until: Any = None, prelap: float = 0.0, fade: float = 0.03, label: str = "", frames: bool = False):
        """Put `sound` on `bus`, `at` into `clip`. Cut off at the clip's end (fading over `fade` s) unless `until`
        names a later clip (to its end) or a (clip, frame) point."""
        off = self.tl.sec(at) if frames else at
        if off < -prelap - 1e-6:
            raise ValueError(f"{label or clip}: starts {off:.2f} s before its clip without a prelap")
        start = self._at(clip) + off
        if until is None:
            stop = self._end(clip)
        elif isinstance(until, (tuple, list)):
            stop = self._at(until[0], until[1])
        else:
            stop = self._end(until)
        y = _stereo(np.asarray(sound, dtype=float), pan) * 10 ** (gain_db / 20)
        n = min(len(y), max(0, int(round((stop - start) * self.sr))))
        if n <= 0:
            return
        y = y[:n].copy()
        if n < len(sound):  # cut short: fade into the cut
            r = min(n, int(fade * self.sr))
            y[n - r:] *= (np.linspace(1, 0, r) ** 2)[:, None]
        i = int(round(start * self.sr))
        buf = self.buses[bus]
        lo, hi = max(0, i), min(len(buf), i + n)
        if hi > lo:
            buf[lo:hi] += y[lo - i:hi - i]
        self.cues.append({"label": label or clip, "bus": bus, "scene": clip, "start": round(start, 4),
                          "end": round(start + n / self.sr, 4),
                          "bridge": list(until) if isinstance(until, tuple) else until})

    def silence(self, start: float, end: float, what: str = ""):
        """A span meant to be silent: muted in the render (and again after any mastering: see mute_silences)."""
        self.silences.append({"start": start, "end": end, "what": what})

    def render(self, gains_db: dict[str, float] | None = None) -> np.ndarray:
        gains_db = gains_db or {}
        out = sum(b * 10 ** (gains_db.get(name, 0.0) / 20) for name, b in self.buses.items())
        out = out[: int(round(self.tl.duration() * self.sr))]
        return mute_silences(out, self.sr, self.silences)

    def write(self, path: str, x: np.ndarray):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        sf.write(path, np.clip(x, -1, 1), self.sr, subtype="PCM_24")

    def export(self, timeline_path: str):
        """Write the placements and silences into the timeline file, for tools/verify/audio.py."""
        with open(timeline_path, encoding="utf-8") as f:
            data = json.load(f)
        data["cues"], data["silences"] = self.cues, self.silences
        with open(timeline_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1)


def mute_silences(x: np.ndarray, sr: int, silences: list[dict[str, Any]], ramp: float = 0.006) -> np.ndarray:
    """Zero each silence, with a 6 ms ramp each side. Run it again after the master chain: a limiter or a high-pass
    rings on for a few milliseconds after loud low end, and the silence measured after mastering is the one heard."""
    m = np.ones(len(x))
    r = int(ramp * sr)
    for s in silences:
        a, b = int(s["start"] * sr), int(s["end"] * sr)
        m[a:b] = 0
        lo = max(0, a - r)
        m[lo:a] = np.minimum(m[lo:a], np.linspace(1, 0, a - lo))
        hi = min(len(m), b + r)
        m[b:hi] = np.minimum(m[b:hi], np.linspace(0, 1, hi - b))
    return x * m[:, None]


def duck(music: np.ndarray, voice: np.ndarray, sr: int, depth_db: float = -9.0, threshold_db: float = -45.0,
         attack: float = 0.04, release: float = 0.35) -> np.ndarray:
    """Music pulled down under the voice: by `depth_db` wherever the voice is above `threshold_db`, easing in over
    `attack` and back over `release` seconds."""
    env = np.abs(voice).max(axis=1)
    hop = max(1, int(sr * 0.01))
    frames = env[: len(env) // hop * hop].reshape(-1, hop).max(axis=1)
    on = (20 * np.log10(np.maximum(frames, 1e-9)) > threshold_db).astype(float)
    g = np.ones_like(on)
    target = 10 ** (depth_db / 20)
    a, r = 1 - np.exp(-0.01 / attack), 1 - np.exp(-0.01 / release)
    cur = 1.0
    for i, v in enumerate(on):
        want = target if v else 1.0
        cur += (want - cur) * (a if want < cur else r)
        g[i] = cur
    gain = np.repeat(g, hop)
    gain = np.concatenate([gain, np.full(len(music) - len(gain), gain[-1] if len(gain) else 1.0)])[: len(music)]
    return music * gain[:, None]
