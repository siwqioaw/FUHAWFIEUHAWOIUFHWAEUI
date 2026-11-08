"""Camera moves for shots: views as data, eased moves between them, and a hold that drifts (docs/ROBLOX_CAPTURE.md,
"Camera").

The references (refs/r6rants/SYNTHESIS.md, "Camera grammar"), measured frame by frame in spike S4:

- a shot opens with a push-in or pull-back of 0.1-0.3 s: 007's eases out (its first step shrinks the face to about
  two thirds), 006's run near-steady and then stop;
- 007's whip-pan at 4.50 speeds up and slows down, fastest in its middle;
- 002's swoop that rolls into a dutch angle speeds up and slows down over about 0.4 s;
- swoops between framings: 001's and 004's are sharp (001's with speed lines), 003's time-jump swoop is blurred;
- low angles at desk height, over the shoulder for exchanges, dutch tilts on witnesses, top-down shots.

A view is a dict: {"pos": [x, y, z], "look": [x, y, z], "roll": degrees, "fov": degrees, "dof": [focus, radius, near,
far] or None, and "up": [x, y, z] when the camera looks straight up or down}. fov is the vertical field of view of the
finished 9:16 frame (capture.take turns it for portrait); dof is Roblox's DepthOfFieldEffect (FocusDistance,
InFocusRadius, NearIntensity, FarIntensity). state(view) gives the harness's "cam", "fov" and "dof" keys.

    import camera
    mcu = camera.aim((0, 4.5, 0), toward=(0, 0, 1), distance=5, fov=45)       # a medium close-up on a head
    shot = camera.moves([(0.0, camera.back(mcu, 3)), (0.0, mcu, 0.25)])     # push in from 3 studs back, 0.25 s
    def frame(t):
        return dict(camera.state(camera.hold(shot(t), t)), actors=[...])
"""

from __future__ import annotations

import math

UP = (0.0, 1.0, 0.0)


def _add(a, b):
    return [x + y for x, y in zip(a, b)]


def _sub(a, b):
    return [x - y for x, y in zip(a, b)]


def _mul(a, k):
    return [x * k for x in a]


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _len(a):
    return math.sqrt(_dot(a, a))


def _unit(a):
    n = _len(a)
    return [x / n for x in a]


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def view(pos, look, roll: float = 0.0, fov: float = 50.0, dof=None, up=None) -> dict:
    v = {"pos": [float(x) for x in pos], "look": [float(x) for x in look], "roll": float(roll), "fov": float(fov),
         "dof": list(dof) if dof else None}
    if up:
        v["up"] = [float(x) for x in up]
    return v


def axes(v: dict) -> tuple[list, list, list]:
    """The view's forward, right and up directions (before its roll). A camera looking straight along its up vector
    has no right: give such a view an "up" (top() does)."""
    f = _unit(_sub(v["look"], v["pos"]))
    r = _cross(f, v.get("up") or UP)
    if _len(r) < 1e-6:
        raise ValueError("the camera looks straight up or down: give the view an 'up' (see top())")
    r = _unit(r)
    return f, r, _cross(r, f)


def aim(target, toward=(0.0, 0.0, 1.0), distance: float = 6.0, height: float = 0.0, fov: float = 50.0,
        roll: float = 0.0) -> dict:
    """A view of `target` from `distance` studs along `toward` (the direction from the target to the camera), raised
    `height` studs."""
    pos = _add(_add(target, _mul(_unit(toward), distance)), (0.0, height, 0.0))
    return view(pos, target, roll, fov)


def top(target, height: float = 10.0, up=(0.0, 0.0, 1.0), fov: float = 50.0) -> dict:
    """Top-down: the camera `height` studs straight above `target`, the frame's top towards `up` (the way an actor
    faces, say)."""
    return view(_add(target, (0.0, height, 0.0)), target, 0.0, fov, up=up)


def back(v: dict, studs: float) -> dict:
    """The same view from `studs` further back along its line of sight (negative: closer), focus kept on the
    subject."""
    d = _unit(_sub(v["pos"], v["look"]))
    out = dict(v, pos=_add(v["pos"], _mul(d, studs)))
    if v.get("dof"):
        out["dof"] = [v["dof"][0] + studs] + list(v["dof"][1:])
    return out


def orbit(v: dict, degrees: float) -> dict:
    """The camera swung `degrees` about the vertical through what it looks at (+: to the camera's right)."""
    a = math.radians(degrees)
    rel = _sub(v["pos"], v["look"])
    x, z = rel[0] * math.cos(a) + rel[2] * math.sin(a), -rel[0] * math.sin(a) + rel[2] * math.cos(a)
    return dict(v, pos=_add(v["look"], [x, rel[1], z]))


def dutch(v: dict, degrees: float) -> dict:
    """The same view with its roll set to `degrees`, a dutch angle: + tilts the picture clockwise, the horizon falling
    to the right (spike S4 measured 14.2 degrees for 14)."""
    return dict(v, roll=float(degrees))


def low(target, toward=(0.0, 0.0, 1.0), distance: float = 6.0, eye: float = 2.4, fov: float = 55.0) -> dict:
    """A low angle: the camera `eye` studs above the floor (desk height: an R6 body is 5 tall), looking up at
    `target` from `distance` studs along `toward` (made level)."""
    d = _unit([toward[0], 0.0, toward[2]])
    return view([target[0] + d[0] * distance, eye, target[2] + d[2] * distance], target, 0.0, fov)


def ots(shoulder, face, side: float = 1.0, behind: float = 2.4, up: float = 0.7, fov: float = 40.0,
        blur: float = 0.6, lift: float = 0.0) -> dict:
    """Over the shoulder: the camera `behind` studs behind a near actor's `shoulder` and `side` studs to one side
    (+: the near actor's right as they face `face`), `up` studs above it, looking at the far actor's `face`, or
    `lift` studs below it to raise the face in the frame, clear of the captions. Depth of field keeps the face sharp
    and blurs the near actor by `blur` (0 for none)."""
    fwd = _unit(_sub(face, shoulder))
    right = _cross(fwd, UP)
    if _len(right) < 1e-6:
        raise ValueError("the face is straight above or below the shoulder: no 'over the shoulder' there")
    right = _unit(right)
    pos = _add(_add(_add(shoulder, _mul(fwd, -behind)), _mul(right, side)), (0.0, up, 0.0))
    dof = [_len(_sub(face, pos)), 1.5, blur, 0.0] if blur > 0 else None
    return view(pos, _sub(face, (0.0, lift, 0.0)), 0.0, fov, dof)


def ease_out(u: float) -> float:
    """Fastest at the start, settling into the hold: about a fifth of the way on the first of 12 frames."""
    return 1 - (1 - u) ** 3


def ease_in(u: float) -> float:
    """Speeding up all the way, to cut on the move."""
    return u ** 3


def ease_in_out(u: float) -> float:
    """Speeding up and slowing down: a swoop or a whip-pan."""
    return u * u * (3 - 2 * u) if u < 1 else 1.0


EASES = {"out": ease_out, "in": ease_in, "inout": ease_in_out, "linear": lambda u: u}


def _turn(a, b, u):
    """Direction a turned u of the way towards direction b (unit vectors), the short way round; half way round goes
    about the vertical."""
    d = max(-1.0, min(1.0, _dot(a, b)))
    th = math.acos(d)
    if th < 1e-6:
        return a
    if math.pi - th < 1e-3:  # opposite: swing round the vertical
        c, s = math.cos(math.pi * u), math.sin(math.pi * u)
        return [a[0] * c + a[2] * s, a[1], -a[0] * s + a[2] * c]
    s = math.sin(th)
    return _add(_mul(a, math.sin((1 - u) * th) / s), _mul(b, math.sin(u * th) / s))


def blend(a: dict, b: dict, u: float) -> dict:
    """The view u of the way from a to b. The aim moves straight; the camera swings round it, its distance changing
    straight, so a move between two orbit views goes round the circle instead of cutting across it. Roll, field of
    view and depth of field change straight."""
    dof = None
    if a["dof"] or b["dof"]:
        da, db = a["dof"] or [b["dof"][0], b["dof"][1], 0.0, 0.0], b["dof"] or [a["dof"][0], a["dof"][1], 0.0, 0.0]
        dof = [x + (y - x) * u for x, y in zip(da, db)]
    look = [x + (y - x) * u for x, y in zip(a["look"], b["look"])]
    ra, rb = _sub(a["pos"], a["look"]), _sub(b["pos"], b["look"])
    la, lb = _len(ra), _len(rb)
    rel = _mul(_turn(_unit(ra), _unit(rb), u), la + (lb - la) * u)
    out = {"pos": _add(look, rel), "look": look, "roll": a["roll"] + (b["roll"] - a["roll"]) * u,
           "fov": a["fov"] + (b["fov"] - a["fov"]) * u, "dof": dof}
    if a.get("up") or b.get("up"):
        out["up"] = _unit(_add(_mul(a.get("up") or list(UP), 1 - u), _mul(b.get("up") or list(UP), u)))
    return out


def moves(keys: list):
    """A camera path from keys [(time, view) or (time, view, seconds, ease)]: from each key's time the camera moves
    from wherever it was to the key's view over `seconds` (default 0.25; 0 cuts) with the ease ("out", "in", "inout",
    "linear"; default "out"), then holds. A move cut short by the next carries on from where it was, but not at its
    speed: cut it with an "out" move, which starts at speed, or the camera pauses. Returns a function of t."""
    keys = sorted(keys, key=lambda k: k[0])
    steps = [(k[0], k[1], k[2] if len(k) > 2 else 0.25, EASES[k[3] if len(k) > 3 else "out"]) for k in keys]

    def during(i: int, start: dict, t: float) -> dict:
        t0, target, dur, ease = steps[i]
        u = 1.0 if dur <= 0 else min(1.0, max(0.0, (t - t0) / dur))
        return blend(start, target, ease(u))

    def at(t: float) -> dict:
        start = steps[0][1]
        cur = start
        for i in range(1, len(steps)):
            if t < steps[i][0]:
                break
            if i > 1:
                start = during(i - 1, start, steps[i][0])  # where the move before had the camera
            cur = during(i, start, t)
        return cur

    return at


def hold(v: dict, t: float, amount: float = 1.0, seed: int = 0) -> dict:
    """The view with slight slow drift, as a hand-held hold: the camera wanders across the frame about 0.02 studs for
    every 5 studs it stands back, its aim a little more, the roll a tenth of a degree. A different seed per shot
    keeps them from drifting alike."""
    f, r, u = axes(v)
    k = 0.004 * _len(_sub(v["pos"], v["look"])) * amount
    ph = [(seed * 1.618 + i * 2.399) % (2 * math.pi) for i in range(5)]
    w = 2 * math.pi
    pos = _add(_add(v["pos"], _mul(r, k * math.sin(w * 0.31 * t + ph[0]))),
               _mul(u, k * math.sin(w * 0.23 * t + ph[1])))
    look = _add(_add(v["look"], _mul(r, 1.5 * k * math.sin(w * 0.19 * t + ph[2]))),
                _mul(u, 1.5 * k * math.sin(w * 0.27 * t + ph[3])))
    return dict(v, pos=pos, look=look, roll=v["roll"] + 0.1 * amount * math.sin(w * 0.17 * t + ph[4]))


def state(v: dict) -> dict:
    """The harness's camera keys for a view: {"cam", "fov"} and "dof" when it has one."""
    cam = {"pos": [round(x, 4) for x in v["pos"]], "look": [round(x, 4) for x in v["look"]],
           "roll": round(v["roll"], 3)}
    if v.get("up"):
        cam["up"] = [round(x, 4) for x in v["up"]]
    out = {"cam": cam, "fov": round(v["fov"], 3)}
    if v.get("dof"):
        out["dof"] = [round(x, 3) for x in v["dof"]]
    return out


def shift_px(a: dict, b: dict, size: tuple[int, int] = (960, 1707)) -> tuple[float, float]:
    """Where view b sees the point view a looks at, in pixels from b's centre (x right, y down) in an upright frame of
    `size` (the portrait frame capture.take saves): how far the picture slides between the two views. Roll is
    ignored. A move that keeps its aim (an orbit) slides its subject 0, though the background moves."""
    f, r, u = axes(b)
    d = _sub(a["look"], b["pos"])
    z = _dot(d, f)
    if z <= 1e-6:
        return float("inf"), float("inf")  # behind the camera: a cut
    w, h = size
    half_v = math.tan(math.radians(b["fov"] / 2))
    half_h = half_v * w / h
    return (_dot(d, r) / z) / half_h * w / 2, -(_dot(d, u) / z) / half_v * h / 2


def smear(path, t: float, fps: float = 60, shutter: float = 0.5, size: tuple[int, int] = (960, 1707)) -> float:
    """How many pixels wide fx.streak's smear should be on frame t of a camera path: how far the picture slides
    sideways while a shutter is open for `shutter` of a frame (0.5, a film camera's 180 degrees). A slide over half
    the frame's width is a cut, not a move: 0. Captured as three sub-frames instead, a fast swoop showed three
    separate copies of each face (spike S4). Sideways only."""
    dx = abs(shift_px(path(t - shutter / 2 / fps), path(t + shutter / 2 / fps), size)[0])
    return 0.0 if dx > size[0] / 2 else dx


def project(v: dict, point, size: tuple[int, int] = (960, 1707)):
    """Where `point` lands in view v's upright frame of `size`, in pixels (x right, y down from the top left), or None
    behind the camera. Roll is ignored. For framing checks: a face under about 70% of the frame's height sits where
    captions go."""
    f, r, u = axes(v)
    d = _sub(point, v["pos"])
    z = _dot(d, f)
    if z <= 1e-6:
        return None
    w, h = size
    half_v = math.tan(math.radians(v["fov"] / 2))
    half_h = half_v * w / h
    return w / 2 * (1 + _dot(d, r) / z / half_h), h / 2 * (1 - _dot(d, u) / z / half_v)
