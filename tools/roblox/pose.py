"""R6 acting for the capture harness: poses as data, pose-to-pose snaps, drift while holding, and a walk cycle
(docs/ROBLOX_CAPTURE.md, "Posing R6").

The references animate pose to pose: a big pose reached in about 5 frames at 60 fps, the hardest hits in 1-2, then
held with slight drift (refs/r6rants/SYNTHESIS.md, "Animation"). Here a shot computes each frame's joints in Python
and the harness applies them, so a take is exact and can be redone frame by frame.

    import pose
    keys = [(0.0, "idle"), (0.35, "arms_out"), (0.9, "hands_on_head", 2 / 60)]
    joints, rootpos = pose.at(keys, t)                     # this frame's joints for one actor
    actor = {"name": "kid", "cf": ..., "joints": joints, "rootpos": rootpos}

Angles are degrees, with the character facing -Z:

- x pitches: + swings an arm or leg forward and up (90 is straight ahead, 180 straight up), tips the head back to
  look up, and leans the whole body back;
- y turns: + turns the head or body to the character's left, and swings an arm held out towards its left;
- z rolls: + lifts a right arm out to the side, - lifts a left arm out; + tilts the head toward its left shoulder.

Joints: neck, ls, rs (shoulders), lh, rh (hips), root (the whole body). Every joint turns by z, then x, then y about
its parent's axes, y last so that it aims: an arm pitched forward by x = 90 swings toward the character's left with
y > 0, and a nodding head turns with y. The root's angles lean, turn and roll the whole body; at() pivots it at the
hips and keeps the feet on the floor (plant()). rootpos moves the body in studs (y: up). Keys blend each angle
straight from its value to the next, so a path follows the numbers: an arm going from x = -10 to 176 rises through
the front, never round the back. What at() and walking() return is what the harness takes: every joint as
CFrame.Angles (x, y, z).
"""

from __future__ import annotations

import math

import numpy as np

JOINTS = ("neck", "ls", "rs", "lh", "rh", "root")
LEG = 2.0  # an R6 leg, hip to sole, in studs
FOOT = 0.5  # half a foot's depth, front to back, in studs
HIPS = (0.0, -1.0, 0.0)  # the hips' centre from the root joint, which sits at the torso's centre
CAP = 6.0  # the most a snap goes past its pose, in degrees: 7% of a 140 degree swing would be 10
HEAD = (0.6, 0.6)  # the R6 head mesh as an upright cylinder: radius, half its height (about 1.2 studs each way)
TORSO = (1.0, 1.0, 0.5)  # half the torso's box

# Each pose names only the joints it moves; every other joint is at rest (arms down, legs straight). Every pose keeps
# its arms out of the head (clearance(); tests/selftest.py checks them all). A straight R6 arm can't put its hand on
# the face without its forearm cutting into the head, so facepalm and think hold the hand just before it.
POSES: dict[str, dict] = {
    "idle": {"ls": (0, 0, -3), "rs": (0, 0, 3)},
    "arms_out": {"ls": (18, 0, -58), "rs": (18, 0, 58), "neck": (0, 0, 9)},           # the exasperated "bro" spread
    "hands_on_head": {"ls": (174, 0, 16), "rs": (174, 0, -16), "neck": (-8, 0, 0)},     # beside the head's top
    "point": {"rs": (90, 6, 0), "ls": (0, 0, -4), "neck": (-3, 0, 0)},                 # right arm straight ahead
    "point_left": {"ls": (90, -6, 0), "rs": (0, 0, 4), "neck": (-3, 0, 0)},
    "arms_crossed": {"ls": (78, 0, 40), "rs": (84, 0, -40), "neck": (4, 0, 0)},
    "hands_on_hips": {"ls": (-10, 0, -30), "rs": (-10, 0, 30)},
    "laugh": {"root": (12, 0, 0), "neck": (20, 0, 0), "ls": (12, 0, -22), "rs": (12, 0, 22)},
    "facepalm": {"rs": (114, 36, -6), "ls": (0, 0, -4), "neck": (-18, 0, 0)},          # the hand before the face
    "cheer": {"ls": (176, 0, -22), "rs": (176, 0, 22), "neck": (14, 0, 0)},
    "slump": {"root": (-9, 0, 0), "neck": (-28, 0, 0), "ls": (4, 0, -2), "rs": (4, 0, 2)},
    "think": {"rs": (104, 36, -16), "neck": (6, 0, 8)},                                # the hand before the chin
    "lean_in": {"root": (-12, 0, 0), "neck": (10, 0, 0), "ls": (24, 0, -8), "rs": (24, 0, 8)},
}


def ease_out_cubic(u: float) -> float:
    return 1 - (1 - u) ** 3


def ease_out_back(u: float, s: float = 1.4) -> float:
    """Two thirds of the way on the first of 5 frames, about 7% past the pose on the third, settled on the fifth:
    the snap of the references."""
    u -= 1
    return 1 + u * u * ((s + 1) * u + s)


EASES = {"back": ease_out_back, "cubic": ease_out_cubic, "linear": lambda u: u}


def overshoot(s: float) -> float:
    """How far ease_out_back(u, s) goes past 1 at its peak, as a fraction of the move: 4s^3 / 27(s+1)^2 (0.0706 at
    s = 1.4)."""
    return 4 * s ** 3 / (27 * (s + 1) ** 2)


def _softer(frac: float, s: float = 1.4) -> float:
    """The largest s up to `s` whose overshoot is at most `frac`."""
    if overshoot(s) <= frac:
        return s
    lo, hi = 0.0, s
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if overshoot(mid) <= frac else (lo, mid)
    return lo


# Rotations: 3x3 matrices as tuples of rows.
def _rx(a):
    c, s = math.cos(a), math.sin(a)
    return ((1, 0, 0), (0, c, -s), (0, s, c))


def _ry(a):
    c, s = math.cos(a), math.sin(a)
    return ((c, 0, s), (0, 1, 0), (-s, 0, c))


def _rz(a):
    c, s = math.cos(a), math.sin(a)
    return ((c, -s, 0), (s, c, 0), (0, 0, 1))


def _mul(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def _apply(m, v):
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


def _inv(m):
    return tuple(tuple(m[j][i] for j in range(3)) for i in range(3))


def angles(x: float, y: float, z: float):
    """The rotation of Roblox's CFrame.Angles(x, y, z) in degrees: Rx * Ry * Rz."""
    return _mul(_mul(_rx(math.radians(x)), _ry(math.radians(y))), _rz(math.radians(z)))


def euler(m) -> tuple[float, float, float]:
    """angles()'s inverse: (x, y, z) degrees with angles(x, y, z) == m."""
    y = math.asin(max(-1.0, min(1.0, m[0][2])))
    x = math.atan2(-m[1][2], m[2][2])
    z = math.atan2(-m[0][1], m[0][0])
    return math.degrees(x), math.degrees(y), math.degrees(z)


def body(x: float, y: float, z: float):
    """A pose's rotation for any joint: by z, then x, then y about the parent's axes (Ry * Rx * Rz)."""
    return _mul(_mul(_ry(math.radians(y)), _rx(math.radians(x))), _rz(math.radians(z)))


def body_angles(m) -> tuple[float, float, float]:
    """body()'s inverse: (x, y, z) degrees."""
    x = math.asin(max(-1.0, min(1.0, -m[1][2])))
    y = math.atan2(m[0][2], m[2][2])
    z = math.atan2(m[1][0], m[1][1])
    return math.degrees(x), math.degrees(y), math.degrees(z)


def rotation(joint: str, xyz) -> tuple:
    """A pose's (x, y, z) for `joint` as a rotation matrix (body())."""
    return body(*xyz)


def resolve(p) -> dict:
    """A pose name or dict as {joint: (x, y, z) degrees} for every joint, plus 'rootpos' (studs)."""
    src = POSES[p] if isinstance(p, str) else (p or {})
    out = {j: tuple(float(v) for v in src.get(j, (0, 0, 0))) for j in JOINTS}
    out["rootpos"] = tuple(float(v) for v in src.get("rootpos", (0, 0, 0)))
    return out


def pose_at(keys: list, t: float, snap: float = 5 / 60, ease: str = "back", cap: float = CAP) -> dict:
    """The pose at time t from keys [(time, pose) or (time, pose, snap_seconds)]: each key snaps from wherever the
    body was at its time to its pose over its snap time, then holds. Each angle moves straight from its value to the
    next. With the "back" ease a joint goes past its pose and settles back; a joint with a long way to go eases more
    gently, so that it goes at most `cap` degrees past. Returns {joint: (x, y, z), 'rootpos': studs}."""
    keys = sorted(keys, key=lambda k: k[0])
    later = [i for i, k in enumerate(keys) if k[0] <= t]
    if not later or later[-1] == 0:
        return resolve(keys[0][1])  # the first pose holds from the start: nothing snaps into it
    i = later[-1]
    tk, target = keys[i][0], resolve(keys[i][1])
    dur = keys[i][2] if len(keys[i]) > 2 else snap
    start = pose_at(keys[:i], tk, snap, ease, cap)  # where the earlier keys had the body at tk, even mid-snap
    u = 1.0 if dur <= 0 else min(1.0, (t - tk) / dur)
    out = {}
    for j in JOINTS:
        span = max(abs(b - a) for a, b in zip(start[j], target[j]))
        if ease == "back":
            e = ease_out_back(u, _softer(cap / span) if span > 1e-9 else 1.4)
        else:
            e = EASES[ease](u)
        out[j] = tuple(a + (b - a) * e for a, b in zip(start[j], target[j]))
    e = ease_out_cubic(u)
    out["rootpos"] = tuple(a + (b - a) * e for a, b in zip(start["rootpos"], target["rootpos"]))
    return out


def drift(t: float, amount: float = 1.0, seed: int = 0) -> dict:
    """Small slow offsets so a held pose stays alive: breathing, a head that settles, arms that hang. Degrees."""
    ph = [(seed * 1.618 + k * 2.399) % (2 * math.pi) for k in range(6)]
    w = 2 * math.pi
    out = {j: (0.0, 0.0, 0.0) for j in JOINTS}
    out["neck"] = (1.4 * math.sin(w * 0.45 * t + ph[0]), 1.8 * math.sin(w * 0.29 * t + ph[1]), 0.0)
    out["root"] = (0.8 * math.sin(w * 0.27 * t + ph[2]), 0.6 * math.sin(w * 0.19 * t + ph[3]), 0.0)
    out["ls"] = (0.0, 0.0, -1.0 * math.sin(w * 0.37 * t + ph[4]))
    out["rs"] = (0.0, 0.0, 1.0 * math.sin(w * 0.33 * t + ph[5]))
    return {j: tuple(v * amount for v in out[j]) for j in JOINTS}


def _corners(rot: dict, rootpos) -> dict:
    r = rot["root"]
    out = {}
    for leg, hip, xs in (("rh", (1, -1, 0), (-1.0, 0.0)), ("lh", (-1, -1, 0), (0.0, 1.0))):
        corners = []
        for x in xs:
            for z in (-FOOT, FOOT):
                local = [h + v for h, v in zip(hip, _apply(rot[leg], (x, -LEG, z)))]
                corners.append(tuple(p + w for p, w in zip(rootpos, _apply(r, local))))
        out[leg] = corners
    return out


def plant(rot: dict, rootpos, floor: bool = True) -> tuple[dict, list]:
    """Pivot the body about the hips, not the torso's centre, and keep each leg's pose relative to the ground, so a
    lean, a laugh or a slump leaves the feet where they were. The legs still turn with the body (the root's turn), so
    on a turn the feet turn about the hips' centre: each slides about 0.2 studs over 25 degrees, so for a big turn,
    step instead. A roll tilts the hips, so one foot would go into the floor: with `floor`, the
    body is raised until no sole is under it, and the other foot lifts. `rot` is {joint: rotation matrix}; returns
    the same with the legs changed, and the root's new position."""
    r = rot["root"]
    lean, yaw, roll = body_angles(r)
    moved = _apply(r, HIPS)
    pos = [rootpos[i] + HIPS[i] - moved[i] for i in range(3)]
    undo = _mul(_inv(r), _ry(math.radians(yaw)))  # undo the lean and roll, keep the turn
    out = dict(rot)
    for leg in ("lh", "rh"):
        out[leg] = _mul(undo, rot[leg])
    if floor:
        low = min(c[1] for cs in _corners(out, pos).values() for c in cs)
        if low < -LEG - 1:
            pos[1] += -LEG - 1 - low
    return out, pos


def _harness(rot: dict, rootpos) -> tuple[dict, list]:
    return ({j: [round(v, 3) for v in euler(rot[j])] for j in JOINTS}, [round(v, 4) for v in rootpos])


def at(keys: list, t: float, drift_amount: float = 1.0, seed: int = 0, planted: bool = True, **kw) -> tuple[dict, list]:
    """(joints, rootpos) for the harness: the keyed pose at t plus drift, planted on its feet (plant())."""
    p = pose_at(keys, t, **kw)
    d = drift(t, drift_amount, seed)
    rot = {j: rotation(j, [a + b for a, b in zip(p[j], d[j])]) for j in JOINTS}
    rootpos = p["rootpos"]
    if planted:
        rot, rootpos = plant(rot, rootpos)
    return _harness(rot, rootpos)


# The walk. An R6 leg is a straight 1 x 2 x 1 block hinged at the top, so a planted foot rolls over the edge of its
# sole: over the heel while the leg is ahead of the hip, over the toe once it's behind. REACH is the hip to either
# edge, TILT the angle between that line and the leg.
REACH = math.hypot(LEG, FOOT)
TILT = math.atan2(FOOT, LEG)


def _depth(a: float) -> float:
    """How far below the hip a leg at `a` radians reaches: its sole's lowest edge."""
    return LEG * math.cos(a) + FOOT * abs(math.sin(a))


def stride(swing: float = 30.0) -> float:
    """Studs a planted foot rolls back under the body while the leg goes from +swing to -swing degrees."""
    return 2 * (REACH * math.sin(math.radians(swing) - TILT) + FOOT)


def _leg(p: float, swing: float, stance: float) -> tuple[float, bool]:
    """A leg's angle in radians at phase p of its cycle (0 at heel strike), and whether it's in its stance.
    In its stance (0 <= p < stance), the foot's edge on the floor moves back at a steady rate, so a body moving at a
    steady speed leaves it still. Swinging, the leg goes from -swing to +swing on a smooth curve that starts and ends
    at the stance's rate: the foot reaches a little past the stride and comes back onto it."""
    big = math.radians(swing)
    d = stride(swing)
    if p < stance:
        s = d * p / stance
        if s < d / 2:  # over the heel
            return TILT + math.asin((REACH * math.sin(big - TILT) - s) / REACH), True
        return math.asin((FOOT - (s - d / 2)) / REACH) - TILT, True  # over the toe
    span = 1 - stance
    w = -d / (stance * REACH * math.cos(big - TILT)) * span  # the stance's rate, in radians per unit of u
    u = (p - stance) / span
    return ((2 * u ** 3 - 3 * u ** 2 + 1) * -big + (u ** 3 - 2 * u ** 2 + u) * w + (-2 * u ** 3 + 3 * u ** 2) * big
            + (u ** 3 - u ** 2) * w), False


def _legs(t: float, freq: float, swing: float, stance: float):
    if not 0.5 < stance < 1:
        raise ValueError(f"stance {stance}: a walk keeps a foot down, so stance must be over 0.5 and under 1")
    if not 15 <= swing <= 60:
        raise ValueError(f"swing {swing}: under 15 degrees a foot never rolls onto its heel; keep it 15-60")
    ph = freq * t
    ar, on_r = _leg(ph % 1.0, swing, stance)
    al, on_l = _leg((ph + 0.5) % 1.0, swing, stance)
    reach = max(_depth(a) for a, on in ((ar, on_r), (al, on_l)) if on)
    return ph, ar, on_r, al, on_l, reach


def walk_planted(t: float, freq: float = 1.5, swing: float = 30.0, stance: float = 0.6) -> dict:
    """{"rh": bool, "lh": bool}: which feet are on the floor and holding still at t. A foot moves with the floor from
    the start of its stance but comes down onto it a frame or two later, as the body settles onto it; both are down
    for a moment at each change of step."""
    _, ar, on_r, al, on_l, reach = _legs(t, freq, swing, stance)
    return {"rh": on_r and _depth(ar) > reach - 1e-4, "lh": on_l and _depth(al) > reach - 1e-4}


def walk_steps(seconds: float, fps: float = 60, freq: float = 1.5, swing: float = 30.0, stance: float = 0.6) -> list:
    """[(frame, leg)]: the frames on which a foot comes down, for footsteps."""
    out, prev = [], {"rh": True, "lh": True}
    for k in range(int(round(seconds * fps)) + 1):
        now = walk_planted(k / fps, freq, swing, stance)
        out += [(k, leg) for leg in ("rh", "lh") if now[leg] and not prev[leg]]
        prev = now
    return out


def walk(t: float, freq: float = 1.5, swing: float = 30.0, stance: float = 0.6, arm: float = 24.0) -> dict:
    """A walking frame, in pose angles (degrees) and rootpos (studs): `freq` cycles a second (two steps each), the
    legs reaching `swing` degrees each way, each foot's stance `stance` of the cycle (over half, so a foot is always
    down), arms swinging against the legs, a slight lean in. The body sits as high as the feet in their stance put
    it: highest while one balances on an edge, 0.06 studs up, lowest as a sole lies flat. An R6 body has no knees,
    so the passing foot skims the floor. Move the actor by walk_travel(t)."""
    ph, ar, on_r, al, on_l, reach = _legs(t, freq, swing, stance)
    apart = (math.degrees(ar) - math.degrees(al)) / (2 * swing)  # +1 with the right leg ahead
    out = {j: (0.0, 0.0, 0.0) for j in JOINTS}
    out["rh"], out["lh"] = (math.degrees(ar), 0.0, 0.0), (math.degrees(al), 0.0, 0.0)
    out["rs"], out["ls"] = (-arm * apart, 0.0, 3.0), (arm * apart, 0.0, -3.0)
    out["root"] = (-3.0, 0.0, 0.0)
    out["neck"] = (2.0, -1.5 * math.sin(2 * math.pi * ph), 0.0)
    out["rootpos"] = (0.0, reach - LEG, 0.0)
    return out


def walk_speed(freq: float = 1.5, swing: float = 30.0, stance: float = 0.6) -> float:
    """Studs a second: each planted foot rolls back one stride() in `stance` of a cycle."""
    return stride(swing) * freq / stance


def walk_travel(t: float, freq: float = 1.5, swing: float = 30.0, stance: float = 0.6) -> float:
    """Studs walked by time t: a steady walk_speed(), which keeps the planted feet still."""
    return walk_speed(freq, swing, stance) * t


def walking(t: float, freq: float = 1.5, swing: float = 30.0, stance: float = 0.6) -> tuple[dict, list]:
    """(joints, rootpos) for the harness at time t of a walk: move the actor by walk_travel(t)."""
    w = walk(t, freq, swing, stance)
    rot = {j: rotation(j, w[j]) for j in JOINTS}
    return _harness(*plant(rot, w["rootpos"], floor=False))


# Checks, as the harness poses an R6 body.
def soles(joints: dict, rootpos) -> dict:
    """Each sole's four corners as the harness poses an R6 body from at() or walking() output, in studs in the
    actor's own space (facing -Z) from where its torso's centre rests: {"rh": [(x, y, z) x 4], "lh": [...]}. The
    floor is at y = -3."""
    return _corners({j: angles(*joints[j]) for j in ("root", "rh", "lh")}, rootpos)


def feet(joints: dict, rootpos) -> dict:
    """Each sole's centre: {"rh": (x, y, z), "lh": (x, y, z)}, as soles(). At rest (0.5, -3, 0) and (-0.5, -3, 0)."""
    return {leg: tuple(sum(c[i] for c in cs) / 4 for i in range(3)) for leg, cs in soles(joints, rootpos).items()}


def _grid(step: float = 0.05) -> np.ndarray:
    """Points through an R6 arm's 1 x 2 x 1 block, about its centre."""
    axes = [np.linspace(-h, h, int(round(2 * h / step)) + 1) for h in (0.5, 1.0, 0.5)]
    return np.stack(np.meshgrid(*axes, indexing="ij"), -1).reshape(-1, 3)


_ARM = _grid()


def clearance(joints: dict) -> float:
    """How deep either arm goes into the head, or its lower half into the torso, in studs, as the harness poses an R6
    body from at() output. The head is an upright cylinder 1.2 studs across and tall, about its rounded mesh; the
    torso a 2 x 2 x 1 box. The top of an R6 arm swings into the torso's shoulder whenever the arm is raised, on every
    R6 rig, so that isn't counted. 0 for a pose that keeps its arms clear."""
    neck = np.array(angles(*joints["neck"]))
    head = np.array((0.0, 1.0, 0.0)) + neck @ np.array((0.0, 0.5, 0.0))
    worst = 0.0
    for arm, shoulder, side in (("rs", (1.0, 0.5, 0.0), 0.5), ("ls", (-1.0, 0.5, 0.0), -0.5)):
        m = np.array(angles(*joints[arm]))
        p = (_ARM + (side, -0.5, 0.0)) @ m.T + shoulder  # the arm's points in the torso's axes
        q = (p - head) @ neck  # and in the head's
        worst = max(worst, float(np.minimum(HEAD[0] - np.hypot(q[:, 0], q[:, 2]), HEAD[1] - np.abs(q[:, 1])).max()))
        low = p[_ARM[:, 1] <= -0.25]  # the forearm and hand
        worst = max(worst, float((np.array(TORSO) - np.abs(low)).min(axis=1).max()))
    return max(0.0, worst)


def snap_clearance(a, b, snap: float = 5 / 60, fps: float = 60) -> float:
    """clearance() at its worst over the frames of a snap from pose a to pose b: the in-between frames can clip
    where neither pose does (an arm swinging inward before it swings forward goes through the chest)."""
    keys = [(0.0, a), (1.0, b, snap)]
    return max(clearance(at(keys, 1.0 + k / fps, drift_amount=0.0)[0]) for k in range(1, int(round(snap * fps)) + 2))


def walk_check(frames=None, travel=None, planted=None, seconds: float = 2.0, fps: float = 60,
               touch: float = 0.003) -> dict:
    """How well a walk keeps its feet, frame by frame at `fps` (defaults: walking(), walk_travel(), walk_planted()),
    in studs: slip, the most a planted foot's corner on the floor moves in a frame (the edge it rolls over stays put);
    sink, the deepest a planted foot goes under the floor; lift, the most a planted foot floats above it, or the body
    with no foot down; scrape, the deepest a foot that isn't planted goes under the floor as it passes. walk() scores
    about 0 on the first three and 0.025 on scrape: straight R6 legs can't quite clear the floor."""
    frames = frames or walking
    travel = travel or walk_travel
    planted = planted or walk_planted
    out = {"slip": 0.0, "sink": 0.0, "lift": 0.0, "scrape": 0.0}
    prev = None
    for k in range(int(round(seconds * fps)) + 1):
        t = k / fps
        x = travel(t)
        world = {leg: [(x - c[2], c[1] + 3.0, c[0]) for c in cs] for leg, cs in soles(*frames(t)).items()}
        on = [leg for leg, yes in planted(t).items() if yes]
        off = [leg for leg in world if leg not in on]
        low = {leg: min(c[1] for c in world[leg]) for leg in world}
        if on:
            out["sink"] = max(out["sink"], -min(low[leg] for leg in on))
            out["lift"] = max(out["lift"], max(low[leg] for leg in on))
        out["lift"] = max(out["lift"], min(low.values()))
        if off:
            out["scrape"] = max(out["scrape"], -min(low[leg] for leg in off))
        if prev:
            for leg in on:
                if leg not in prev[1]:
                    continue
                moves = [math.hypot(a[0] - b[0], a[2] - b[2]) for a, b in zip(world[leg], prev[0][leg])
                         if a[1] < touch and b[1] < touch]
                if moves:
                    out["slip"] = max(out["slip"], min(moves))
        prev = (world, on)
    return out
