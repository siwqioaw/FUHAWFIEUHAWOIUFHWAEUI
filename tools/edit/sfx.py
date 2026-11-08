"""Sound effects made here, from code: nothing to license, the same every time (docs/AUDIO.md, "Effects").

    import sfx
    x = sfx.make("boom")              # mono float at 48 kHz
    python tools/edit/sfx.py build/sfx        # every effect as a WAV, to listen to

The references' palette (refs/r6rants/SYNTHESIS.md, "Effects"): a sub-bass boom after nearly every punch (measured at
48 Hz on 004 and 005), pops and whooshes on cuts, a ding and an error tone for in-world notices, a cash register for
money, a shimmer and a dull thud for a rule's two states, a heartbreak sting. The simple ones are here; the rest
(crickets, a door, a crowd) come from a library or the ElevenLabs connector's sound effects, logged in ATTRIBUTION.md.
"""

from __future__ import annotations

import os
import sys

import numpy as np
from scipy import signal as sps

SR = 48000


def _t(dur: float) -> np.ndarray:
    return np.arange(int(dur * SR)) / SR


def _env(dur: float, attack: float, decay: float) -> np.ndarray:
    t = _t(dur)
    return np.minimum(1.0, t / max(attack, 1e-4)) * np.exp(-np.maximum(0.0, t - attack) / decay)


def _norm(x: np.ndarray, peak_db: float = -3.0) -> np.ndarray:
    p = np.max(np.abs(x)) or 1.0
    return x / p * 10 ** (peak_db / 20)


def _noise(dur: float, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).standard_normal(int(dur * SR))


def boom(dur: float = 1.1, f0: float = 58.0, f1: float = 47.0, sub: float = 0.45) -> np.ndarray:
    """The punch on a hit, for the phone it will be heard on as much as for headphones: a sub-bass sine gliding f0 ->
    f1 Hz under a fast attack and a long decay with a soft thump on the front (`sub` of it), a low-mid body (a glide
    from 180 to 110 Hz driven into harmonics up to a few kHz, gone in a third of a second) and a short knock at
    0.8-4 kHz. As pure sub it put -46 dB of its energy above 300 Hz, and M2's turn rose under 3 dB there: on a phone,
    nothing (M2's third review). Now its 300 Hz-8 kHz level is 7 dB higher, the sub 6 dB lower, its peak still 47
    Hz."""
    t = _t(dur)
    f = f1 + (f0 - f1) * np.exp(-t / 0.12)
    low = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(dur, 0.004, 0.32)
    low = np.tanh(2.2 * low) / np.tanh(2.2)
    thump = sps.sosfilt(sps.butter(2, 180, "lowpass", fs=SR, output="sos"), _noise(dur, 1)) * _env(dur, 0.001, 0.025)
    fm = 110.0 + 70.0 * np.exp(-t / 0.06)
    body = np.tanh(4.0 * np.sin(2 * np.pi * np.cumsum(fm) / SR)) * _env(dur, 0.002, 0.11)
    body = sps.sosfilt(sps.butter(2, 140, "highpass", fs=SR, output="sos"), body)
    knock = sps.sosfilt(sps.butter(2, [800, 4000], "bandpass", fs=SR, output="sos"), _noise(dur, 3)) * _env(dur, 0.001, 0.04)
    return _norm(sub * (low + 0.6 * _norm(thump, 0)) + _norm(body, 0) + 0.8 * _norm(knock, 0), -1.0)


def whoosh(dur: float = 0.45, lo: float = 400.0, hi: float = 3200.0, seed: int = 2) -> np.ndarray:
    """Air past the lens: noise through a band-pass sweeping up then down, swelling to the middle."""
    n = int(dur * SR)
    x = _noise(dur, seed)
    out = np.zeros(n)
    hop = 512
    for i in range(0, n, hop):
        u = i / n
        fc = lo + (hi - lo) * np.sin(np.pi * u) ** 1.5
        sos = sps.butter(2, [fc * 0.6, min(fc * 1.6, SR / 2 - 100)], "bandpass", fs=SR, output="sos")
        seg = x[max(0, i - 2048):i + hop]
        y = sps.sosfilt(sos, seg)[-min(hop, n - i):]
        out[i:i + len(y)] = y
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    return _norm(out * env, -6.0)


def pop(dur: float = 0.09, f0: float = 900.0, f1: float = 280.0) -> np.ndarray:
    """A bubble pop for a cut or something appearing: a sine snapping down in pitch."""
    t = _t(dur)
    f = f1 + (f0 - f1) * np.exp(-t / 0.012)
    return _norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(dur, 0.001, 0.025), -6.0)


def ding(dur: float = 1.2, f: float = 1320.0) -> np.ndarray:
    """A notice's chime: a struck bell (partials at 1, 2.76 and 5.4 times, each decaying at its own rate)."""
    t = _t(dur)
    x = sum(a * np.sin(2 * np.pi * f * k * t) * np.exp(-t / d)
            for k, a, d in ((1.0, 1.0, 0.5), (2.76, 0.45, 0.22), (5.4, 0.25, 0.09)))
    return _norm(x * np.minimum(1, t / 0.002), -6.0)


def error(dur: float = 0.5) -> np.ndarray:
    """A denied notice: two short buzzy tones stepping down."""
    out = []
    for f, d in ((440.0, 0.16), (330.0, 0.26)):
        t = _t(d)
        sq = np.sign(np.sin(2 * np.pi * f * t)) * 0.5 + np.sin(2 * np.pi * f * t) * 0.5
        sq = sps.sosfilt(sps.butter(2, 2500, "lowpass", fs=SR, output="sos"), sq)
        out += [sq * np.minimum(1, t / 0.004) * np.minimum(1, (d - t) / 0.02), np.zeros(int(0.03 * SR))]
    return _norm(np.concatenate(out)[: int(dur * SR)], -6.0)


def shimmer(dur: float = 1.4, seed: int = 3) -> np.ndarray:
    """A rule switching on: rising bright partials with sparkle."""
    t = _t(dur)
    rng = np.random.default_rng(seed)
    x = np.zeros(len(t))
    for k in range(9):
        f = 900 * 2 ** (k / 4) * (1 + 0.25 * t / dur)
        x += np.sin(2 * np.pi * np.cumsum(np.full(len(t), f) if np.isscalar(f) else f) / SR + rng.uniform(0, 6)) * \
            np.exp(-((t - 0.08 * k - 0.1) ** 2) / 0.02)
    sparkle = sps.sosfilt(sps.butter(2, 6000, "highpass", fs=SR, output="sos"), rng.standard_normal(len(t)))
    sparkle *= (rng.random(len(t)) < 0.002) * 1.0
    sparkle = np.convolve(sparkle, np.exp(-np.arange(400) / 60), mode="same")
    return _norm(x * _env(dur, 0.05, 0.6) + 0.3 * sparkle, -6.0)


def thud(dur: float = 0.7) -> np.ndarray:
    """A rule draining away: a dull low knock, darker and shorter than the boom."""
    t = _t(dur)
    f = 70 + 50 * np.exp(-t / 0.03)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(dur, 0.002, 0.12)
    knock = sps.sosfilt(sps.butter(2, 400, "lowpass", fs=SR, output="sos"), _noise(dur, 4)) * _env(dur, 0.001, 0.02)
    return _norm(x + 0.5 * _norm(knock, 0), -2.0)


def riser(dur: float = 1.2, seed: int = 5) -> np.ndarray:
    """Tension into a reveal: filtered noise and a tone both rising, cut off at the top."""
    n = int(dur * SR)
    u = np.linspace(0, 1, n)
    tone = np.sin(2 * np.pi * np.cumsum(200 * 2 ** (3 * u)) / SR) * 0.4
    nz = sps.sosfilt(sps.butter(2, 1500, "highpass", fs=SR, output="sos"), _noise(dur, seed)) * 0.6
    return _norm((tone + nz) * u ** 2, -6.0)


def tick(dur: float = 0.05) -> np.ndarray:
    """A text pop's click."""
    return _norm(np.sin(2 * np.pi * 2200 * _t(dur)) * _env(dur, 0.0005, 0.006), -9.0)


def siren(dur: float = 0.9, lo: float = 620.0, hi: float = 960.0, rate: float = 3.3) -> np.ndarray:
    """A lie detector's siren: a tone sweeping between two pitches a few times a second, with a little edge."""
    t = _t(dur)
    f = lo + (hi - lo) * (0.5 - 0.5 * np.cos(2 * np.pi * rate * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph)
    return _norm(x * np.minimum(1, t / 0.01) * np.minimum(1, (dur - t) / 0.06), -6.0)


def whistle(dur: float = 0.55, f: float = 2900.0) -> np.ndarray:
    """A coach's whistle: a high tone with the pea's trill (a fast wobble) and breath."""
    t = _t(dur)
    wobble = 1 + 0.035 * np.sin(2 * np.pi * 38 * t)
    ph = 2 * np.pi * np.cumsum(f * wobble) / SR
    breath = np.convolve(_noise(dur, 7), np.ones(8) / 8, mode="same") * 0.08
    env = np.minimum(1, t / 0.015) * np.minimum(1, (dur - t) / 0.05)
    return _norm((np.sin(ph) + 0.2 * np.sin(2 * ph) + breath) * env, -6.0)


EFFECTS = {"boom": boom, "whoosh": whoosh, "pop": pop, "ding": ding, "error": error, "shimmer": shimmer,
           "thud": thud, "riser": riser, "tick": tick,
           "siren": siren, "whistle": whistle}


def make(name: str, **kw) -> np.ndarray:
    """An effect by name, mono float at 48 kHz."""
    if name not in EFFECTS:
        raise KeyError(f"no effect {name!r}: {sorted(EFFECTS)}")
    return EFFECTS[name](**kw)


def main() -> int:
    import soundfile as sf
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join("build", "sfx")
    os.makedirs(out, exist_ok=True)
    for name in EFFECTS:
        x = make(name)
        sf.write(os.path.join(out, name + ".wav"), x.astype(np.float32), SR, subtype="PCM_24")
        print(f"{name}: {len(x) / SR:.2f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
