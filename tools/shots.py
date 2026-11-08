"""Shot helpers: the camera grammar and staging the references use, as short calls that write a Short's spec
(docs/MAKING.md). A video's `videos/<slug>/direct.py` uses them to write its `short.json`.

    from shots import Spec, shot, actor, push, pull, swoop, hold, ots, low, top, two_shot
    s = Spec("group-project", family="comedy", set="classroom", cast={"me": "narrator", "girl": "popular_girl"})
    s.line("l1", "narrator", "[excited] Nah, why does every group project have that ONE person?", emoji="😭")
    s.add(shot("open", {"me": actor("teacher", poses=[(0, "arms_out")], faces=[(0, "smug"), ("l1:one", "angry")])},
               push("me.head", 9, 5.5), say=[("l1", 0.0)], sfx=[("boom", "l1:end+0.05")]))
    s.write("videos/group-project")

Camera moves (spike S4, `docs/ROBLOX_CAPTURE.md`): a shot opens with a move nearly every time: a fast push-in that
eases out over 0.25-0.3 s, a pull-back from a close-up, a 0.15 s swoop from speaker to listener, a dutch roll for
chaos, a low angle for power, over the shoulder for an exchange, top-down for the absurd.
"""

from __future__ import annotations

import json
import os

MARKS_CACHE: dict = {}


def _marks(set_name: str) -> dict:
    if set_name not in MARKS_CACHE:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "roblox"))
        import sets
        MARKS_CACHE[set_name] = sets.marks(set_name)
    return MARKS_CACHE[set_name]


class Spec:
    def __init__(self, slug: str, family: str = "comedy", set: str = "baseplate", cast: dict | None = None,
                 fps: int = 60, title: str = "", set_options: dict | None = None, extra_sets=None, names=()):
        self.d = {"slug": slug, "title": title, "family": family, "fps": fps, "set": set,
                  "set_options": set_options or {}, "cast": {k: ({"look": v} if isinstance(v, str) else v)
                                                             for k, v in (cast or {}).items()},
                  "lines": [], "shots": []}
        if names:  # names that only start sentences, kept capitalized in captions (mid-sentence ones are found)
            self.d["names"] = list(names)
        if extra_sets:  # [(id, set name, (x, y, z), options), ...]: more places, built beside the first
            self.d["sets"] = [{"id": e[0], "name": e[1], "at": list(e[2]), "options": e[3] if len(e) > 3 else {}}
                              for e in extra_sets]

    def line(self, lid: str, role: str, text: str, emoji: str | None = None, caption=None, **kw):
        ln = {"id": lid, "role": role, "text": text}
        if emoji:
            ln["emoji"] = emoji
        if caption is not None:
            ln["caption"] = caption
        ln.update(kw)
        self.d["lines"].append(ln)
        return self

    def add(self, *shots: dict):
        for sh in shots:
            sh = dict(sh)
            for name, a in sh.get("actors", {}).items():
                if isinstance(a.get("at"), str):  # a mark of the shot's set (unshifted: plan adds the offset)
                    sid = sh.get("set")
                    name = next((e["name"] for e in self.d.get("sets", []) if e["id"] == sid), self.d["set"])
                    m = _marks(name)[a["at"]]
                    a["at"] = m["pos"]
                    a.setdefault("look", m["look"])
            self.d["shots"].append(sh)
        return self

    def music(self, track: str, start: float = 0.0, gain_db: float = -14.0, **kw):
        self.d["music"] = dict(track=track, start=start, gain_db=gain_db, **kw)
        return self

    def text(self, text: str, start: float, end: float, style: str = "header"):
        self.d.setdefault("texts", []).append({"text": text, "from": start, "to": end, "style": style})
        return self

    def write(self, vdir: str) -> str:
        os.makedirs(vdir, exist_ok=True)
        path = os.path.join(vdir, "short.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.d, f, indent=1, ensure_ascii=False)
        return path


def actor(at, look=None, facing=None, poses=None, faces=None, walk=None, drift: float = 1.0) -> dict:
    """An actor in a shot: where (a set mark's name or [x, 3, z]), facing (`look`: a point, or `facing`: a direction),
    pose keys and face keys [(time, name), ...]."""
    a = {"at": at, "poses": [list(p) for p in (poses or [(0, "idle")])],
         "faces": [list(f) for f in (faces or [(0, "smile")])], "drift": drift}
    if look is not None:
        a["look"] = list(look)
    if facing is not None:
        a["facing"] = list(facing)
    if walk:
        a["walk"] = walk
    return a


def shot(name: str, actors: dict, camera: list, say=None, sfx=None, seconds="auto", pad: float = 0.2,
         streak: bool = False, drift: float = 1.0, until=None, set: str | None = None, overlays=None) -> dict:
    """One shot. `say`: [(line id, at)], `sfx`: [(sound, at)] or [(sound, at, gain_db)]; `until`: end on a time
    ('b:switched'); `set`: another of the video's sets; `overlays`: [(icon, over, at)] icons popping over a point."""
    out = {"name": name, "seconds": seconds, "pad": pad, "actors": actors, "camera": camera,
           "say": [{"line": s[0], "at": s[1]} for s in (say or [])],
           "sfx": [{"sound": s[0], "at": s[1], **({"gain_db": s[2]} if len(s) > 2 else {})} for s in (sfx or [])],
           "drift": drift}
    if streak:
        out["streak"] = True
    if until is not None:
        out["until"] = until
    if set:
        out["set"] = set
    if overlays:
        out["overlays"] = [{"icon": o[0], "over": o[1], "at": o[2], **(o[3] if len(o) > 3 else {})} for o in overlays]
    return out


# ---------------------------------------------------------------------------------------------------- camera


def hold(target, distance: float = 5.5, fov: float = 45, height: float = -0.3, toward=None, dutch: float = 0) -> list:
    """A still framing (the hold's own drift keeps it alive)."""
    v = {"t": 0, "aim": target, "distance": distance, "fov": fov, "height": height}
    if toward:
        v["toward"] = list(toward)
    if dutch:
        v["dutch"] = dutch
    return [v]


def push(target, start: float = 9.0, end: float = 5.5, fov: float = 45, height: float = -0.3, at: float = 0.04,
         move: float = 0.28, toward=None) -> list:
    """The references' opening move: a fast push-in that eases out (a fifth of the way on its first frame)."""
    a = {"t": 0, "aim": target, "distance": start, "fov": fov, "height": height}
    b = {"t": at, "aim": target, "distance": end, "fov": fov, "height": height, "move": move, "ease": "out"}
    if toward:
        a["toward"] = b["toward"] = list(toward)
    return [a, b]


def pull(target, start: float = 2.6, end: float = 7.5, fov: float = 45, height: float = -0.2, at: float = 0.04,
         move: float = 0.22, toward=None) -> list:
    """A pull-back from an extreme close-up, easing out: the reveal. `toward`: the side to film from, for a point
    that isn't an actor."""
    a = {"t": 0, "aim": target, "distance": start, "fov": fov, "height": height}
    b = {"t": at, "aim": target, "distance": end, "fov": fov, "height": height, "move": move, "ease": "out"}
    if toward:
        a["toward"] = b["toward"] = list(toward)
    return [a, b]


def swoop(a, b, at: float = 0.15, move: float = 0.16, distance: float = 5.5, fov: float = 45,
          height: float = -0.3) -> list:
    """From one subject to another in a 0.15 s swing, speeding up and slowing down (smear it with streak=True)."""
    return [{"t": 0, "aim": a, "distance": distance, "fov": fov, "height": height},
            {"t": at, "aim": b, "distance": distance, "fov": fov, "height": height, "move": move, "ease": "inout"}]


def dutch_in(target, degrees: float = 14, start: float = 9.0, end: float = 5.0, fov: float = 48, move: float = 0.35):
    """A swoop in that rolls to a dutch angle: chaos, panic."""
    return [{"t": 0, "aim": target, "distance": start, "fov": fov},
            {"t": 0.05, "aim": target, "distance": end, "fov": fov, "dutch": degrees, "move": move, "ease": "inout"}]


def ots(near: str, far: str, push_in: float = 1.0, fov: float = 45) -> list:
    """Over the near actor's shoulder at the far one's face, depth of field on, pushing in a little."""
    return [{"t": 0, "ots": {"near": near, "far": far, "fov": fov}, "back": push_in},
            {"t": 0.04, "ots": {"near": near, "far": far, "fov": fov}, "move": 0.25, "ease": "out"}]


def low(target, distance: float = 5.0, eye: float = 2.5, fov: float = 55, toward=None) -> list:
    """From just above the floor or a desk, looking up: power, or the desk huge in the foreground. Aimed at an actor
    it stands in front of them; aimed at a point, give `toward` (the side the camera stands on)."""
    a = {"aim": target, "distance": distance + 1.5, "eye": eye, "fov": fov}
    b = {"aim": target, "distance": distance, "eye": eye, "fov": fov}
    if toward is not None:
        a["toward"] = b["toward"] = list(toward)
    return [{"t": 0, "low": a}, {"t": 0.04, "low": b, "move": 0.3, "ease": "out"}]


def top(target, height: float = 8.0, fov: float = 50) -> list:
    """Straight down: the absurd, the overview."""
    return [{"t": 0, "top": {"aim": target, "height": height + 2, "fov": fov}},
            {"t": 0.04, "top": {"aim": target, "height": height, "fov": fov}, "move": 0.3, "ease": "out"}]


def wide(pos, look, fov: float = 60, push_in: float = 0.0) -> list:
    """A wide from a fixed point (a set's camera mark), with an optional push."""
    keys = [{"t": 0, "pos": list(pos), "look": look, "fov": fov}]
    if push_in:
        keys[0]["back"] = push_in
        keys.append({"t": 0.04, "pos": list(pos), "look": look, "fov": fov, "move": 0.3, "ease": "out"})
    return keys


def two_shot(a: str, b: str, distance: float = 8.0, fov: float = 50, height: float = -0.2, push_in: float = 1.5):
    """Both actors in frame, framed on the point between their heads."""
    return [{"t": 0, "aim": f"{a}.head", "distance": distance + push_in, "fov": fov, "height": height, "between": b},
            {"t": 0.04, "aim": f"{a}.head", "distance": distance, "fov": fov, "height": height, "between": b,
             "move": 0.3, "ease": "out"}]
