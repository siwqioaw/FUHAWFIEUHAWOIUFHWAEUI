"""The timeline file: the one description of a cut that every check reads (docs/VERIFY.md, "The timeline file").

    {
      "fps": 30,
      "clips":    [{"name": "hook", "frames": 45}, ...],           in order, back to back (record frames)
      "texts":    [{"text": "WAIT FOR IT", "start": 10, "frames": 40}],   words on screen to be read (frames)
      "hits":     [{"frame": 45, "what": "zoom punch"}],           picture accents a sound must land on
      "silences": [{"start": 4.0, "end": 4.25, "what": "beat"}],   seconds; meant to be silent in the final mix
      "cues":     [{"label": "boom", "bus": "sfx", "scene": "hook", "start": 1.5, "end": 2.3, "bridge": null}]
    }

Cues are every placed sound, in seconds, as the mix placed them (tools/edit/cues.py writes them). A cue's `bridge` is
null, or names the clip (or ["clip", frame]) it was deliberately allowed to run on into. Clip starts are derived:
`start` may be given, but it must agree with the running total.
"""

from __future__ import annotations

import json
from typing import Any


class Timeline:
    def __init__(self, data: dict[str, Any]):
        self.fps: float = float(data.get("fps", 30))
        self.clips: list[dict[str, Any]] = []
        at = 0
        for c in data.get("clips", []):
            c = dict(c)
            if "start" in c and int(c["start"]) != at:
                raise ValueError(f"clip {c.get('name')} starts at {c['start']}, but the clips before it end at {at}")
            c["start"] = at
            at += int(c["frames"])
            self.clips.append(c)
        self.total_frames = at
        self.texts: list[dict[str, Any]] = list(data.get("texts", []))
        self.hits: list[dict[str, Any]] = list(data.get("hits", []))
        self.silences: list[dict[str, Any]] = list(data.get("silences", []))
        self.cues: list[dict[str, Any]] = list(data.get("cues", []))
        self.raw = data

    @classmethod
    def load(cls, path: str) -> "Timeline":
        with open(path, encoding="utf-8") as f:
            return cls(json.load(f))

    def sec(self, frames: float) -> float:
        return frames / self.fps

    def cuts(self) -> list[tuple[str, str, int]]:
        """(clip before, clip after, the cut's frame) for every cut."""
        return [(a["name"], b["name"], b["start"]) for a, b in zip(self.clips, self.clips[1:])]

    def clip_at(self, frame: int) -> tuple[str, int]:
        """The clip a record frame is in, and the frame's offset into it."""
        for c in self.clips:
            if c["start"] <= frame < c["start"] + c["frames"]:
                return c["name"], frame - c["start"]
        return "?", 0

    def clip(self, name: str) -> dict[str, Any]:
        for c in self.clips:
            if c["name"] == name:
                return c
        raise KeyError(name)

    def duration(self) -> float:
        return self.sec(self.total_frames)
