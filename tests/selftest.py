"""Build a 6-second vertical test cut with failures planted in it, run every check on the delivered MP4, and confirm
each check catches what it should and passes what it should (docs/VERIFY.md, "Trusting the checks").

    python tests/selftest.py            -> build/selftest/ ; exits 1 if any check misbehaves

Planted: photosensitive flashes; a caption too short to read; an accent number (exempt); a black stretch; a sound
running across a cut undeclared; a declared bridge and a prelap (allowed); a click at a cut; a silence that isn't; a
picture hit with no sound on it; R6 poses that go wrong (an unplanted lean; a walk too fast, at standing height or
not planted; an arm in the head or chest; a swing that jumps speed); camera moves that overshoot, jump, ease the
wrong way or smear wrong; a smear that doubles. It also renders through render.py's worker processes, masters through
master.py (checked against ffmpeg's own loudness meter) and encodes through deliver.py, so a broken tool fails here
first.
"""

from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for sub in ("edit", "verify"):
    sys.path.insert(0, os.path.join(ROOT, "tools", sub))

import fx  # noqa: E402
import look  # noqa: E402
import typeset as ts  # noqa: E402

W, H, FPS = 270, 480, 30
CLIPS = [("hook", 60), ("flash", 45), ("calm", 75)]  # 2.0 s, 1.5 s, 2.5 s
OUT = os.path.join(ROOT, "build", "selftest")


def _scene(r: int) -> np.ndarray:
    """A moving gradient with a moving disc: never frozen, never black."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = 0.25 + 0.2 * np.sin((xx + 4 * r) / 37.0) * np.cos(yy / 53.0)
    img = np.dstack([g * 0.9, g * 1.1, g * 1.4]).astype(np.float32)
    cx, cy = W / 2 + 60 * np.sin(r / 9), H / 2 + 90 * np.cos(r / 13)
    disc = ((xx - cx) ** 2 + (yy - cy) ** 2) < 30 ** 2
    img[disc] = (0.95, 0.75, 0.2)
    return np.clip(img, 0, 1)


def frame_at(r: int) -> np.ndarray:
    if 60 <= r < 90:  # flash: white and black every 2 frames, 7.5 flashes a second
        return np.full((H, W, 3), 1.0 if (r // 2) % 2 == 0 else 0.0, np.float32)
    if 105 <= r < 117:  # 0.4 s of black at the start of calm
        return np.zeros((H, W, 3), np.float32)
    img = _scene(r)
    if r < 60:  # the hook: a reframed wide picture, shaken on its first frames, a word-by-word caption popping up
        wide = look.reframe(np.dstack([_scene(r)[:, :, ::-1]] * 1)[: H // 2], W, H, zoom=1.0)
        img = fx.shake(0.5 * img + 0.5 * wide, max(0.0, 1 - r / 8), seed=r)
        cap = ts.caption("you won't believe this", 30, W - 40, highlight=min(3, r // 12), stroke=0.14)
        layer = fx.pop(cap, r - 5)
        if layer is not None:
            look.centre(img, layer, W / 2, H * 0.72)
    if 90 <= r < 105:
        img = fx.zoom_blur(img, W / 2, H / 2, 0.08 * (r - 90) / 15)
    return look.grain(img, r, 0.01)


def timeline() -> dict:
    return {
        "fps": FPS,
        "clips": [{"name": n, "frames": f} for n, f in CLIPS],
        "texts": [
            {"text": "OK", "start": 0, "frames": 45},  # 1.5 s for 2 characters: passes
            {"text": "This sentence is much too long to read", "start": 110, "frames": 30},  # 1 s: fails
            {"text": "3", "start": 150, "frames": 4, "accent": True},  # exempt
        ],
        "hits": [{"frame": 60, "what": "the flash's first frame (a hit placed on it)"},
                 {"frame": 90, "what": "a hit with nothing on it"}],
    }


def tone(f: float, dur: float, amp: float, sr: int, phase: float = 0.0) -> np.ndarray:
    t = np.arange(int(dur * sr)) / sr
    return amp * np.sin(2 * np.pi * f * t + phase)


def build_audio(tl_path: str, sr: int = 48000) -> str:
    import cues
    import master
    import soundfile as sf
    from timeline import Timeline

    rng = np.random.default_rng(7)
    mix = cues.Mix(Timeline.load(tl_path), sr)
    bed = np.stack([tone(220, 6.5, 0.06, sr) + tone(330, 6.5, 0.045, sr)] * 2, axis=1)
    mix.place("music", bed, "hook", until=("flash", 25), label="bed")  # a declared bridge into flash
    mix.place("music", bed, "calm", label="pad")
    # (A tone, not noise: a click can't be told from noise's own sample-to-sample jumps, so noise just before a
    # cut hides any click there.)
    hum = tone(150, 0.5, 0.2, sr) * np.linspace(1, 0, int(0.5 * sr))
    mix.place("sfx", hum, "hook", at=1.8, label="whoosh")  # choked at the hook's end, 0.2 s in
    burst = rng.standard_normal(int(0.08 * sr)) * 0.08 * np.exp(-np.arange(int(0.08 * sr)) / (0.015 * sr))
    mix.place("sfx", burst, "flash", label="hit")  # on the flash's first frame
    voice = tone(300, 0.8, 0.15, sr) * np.hanning(int(0.8 * sr))
    mix.place("voice", voice, "calm", at=-0.25, prelap=0.3, label="voice")  # a prelap into calm
    mix.silence(4.2, 4.5, "the beat before the end")
    out = mix.render()
    # Planted after the cue sheet, as a careless mix would: a tone across hook -> flash...
    a, b = int(1.75 * sr), int(2.35 * sr)
    out[a:b] += tone(500, 0.6, 0.12, sr)[: b - a, None]
    mix.cues.append({"label": "leaky tone", "bus": "sfx", "scene": "hook", "start": 1.75, "end": 2.35, "bridge": None})
    # ...a tone stopped dead on the flash -> calm cut, at its peak (a click)...
    a, b = int(3.2 * sr), int(3.5 * sr)
    out[a:b] += tone(400, 0.3, 0.3, sr, phase=np.pi / 2 - 2 * np.pi * 400 * 0.3)[: b - a, None]
    # ...and noise in a span the timeline will call silent.
    a, b = int(5.0 * sr), int(5.3 * sr)
    out[a:b] += rng.standard_normal((b - a, 2)) * 0.01
    y = master.master(out, sr, -14.0, -2.4, silences=mix.silences)
    dest = os.path.join(OUT, "mix.wav")
    sf.write(dest, y, sr, subtype="PCM_24")
    mix.export(tl_path)
    data = json.load(open(tl_path, encoding="utf-8"))
    data["silences"].append({"start": 5.0, "end": 5.3, "what": "a silence with noise in it"})
    json.dump(data, open(tl_path, "w", encoding="utf-8"), indent=1)
    return dest


def main() -> int:
    import audio as vaudio
    import deliver
    import master
    import media
    import qc
    import render
    import sheets
    from timeline import Timeline

    os.makedirs(OUT, exist_ok=True)
    tl_path = os.path.join(OUT, "cut.json")
    json.dump(timeline(), open(tl_path, "w", encoding="utf-8"), indent=1)
    n = sum(f for _, f in CLIPS)
    print("rendering the master...")
    mov = render.master(frame_at, n, W, H, FPS, os.path.join(OUT, "master.mov"), workers=4, log=lambda s: None)
    print("mixing and mastering...")
    wav = build_audio(tl_path)
    mp4 = deliver.encode(mov, wav, os.path.join(OUT, "selftest.mp4"))
    tl = Timeline.load(tl_path)

    results: list[tuple[str, bool]] = []

    def expect(what: str, ok: bool):
        results.append((what, ok))
        print(f"{'ok  ' if ok else 'BAD '} {what}")

    import soundfile as sf

    x, sr = sf.read(wav, always_2d=True)
    ref = media.loudness(wav)
    expect(f"master.lufs agrees with ffmpeg ({master.lufs(x, sr):.2f} vs {ref['I']:.2f} LUFS)",
           abs(master.lufs(x, sr) - ref["I"]) < 0.3)
    expect(f"master.true_peak_db agrees with ffmpeg ({master.true_peak_db(x):.2f} vs {ref['TP']:.2f} dBTP)",
           abs(master.true_peak_db(x) - ref["TP"]) < 0.5)

    dest, failed = qc.report(mp4, tl, OUT, -14.0, -1.0, 12.0)
    rep = open(dest, encoding="utf-8").read()
    expect("qc fails the cut overall", failed)
    expect("qc passes the loudness of the delivered file", "- PASS: integrated" in rep)
    expect("qc finds the flashes", "general flashes over the whole frame" in rep)
    expect("qc fails the long caption", "FAIL: 'This sentence is much too long to read'" in rep)
    expect("qc passes the short caption", "PASS: 'OK'" in rep)
    expect("qc leaves the accent number out", "'3'" not in rep)
    expect("qc lists the black stretch", "black_start:3.5" in rep)
    expect("qc finds no duration mismatch", "the timeline is" not in rep)
    xa, sra = media.audio(mp4)
    found, on_hits = qc.clicks(tl, xa, sra)
    expect(f"qc finds the click at flash -> calm ({found})", any("flash -> calm" in c for c in found))
    expect(f"qc takes the onset on the declared hit as a hit ({on_hits})", on_hits == 1)

    lines, fails = vaudio.crossings(tl, xa, sra)
    text = "\n".join(lines)
    expect("audio fails the undeclared crossing", "leaky tone [sfx] from hook" in text and "NOT DECLARED" in text
           and fails == 1)
    expect("audio allows the declared bridge", "bed [music] from hook" in text and "bridge to flash frame 25" in text)
    expect("audio allows the prelap", "voice [voice] from calm" in text and "prelap into it" in text)
    expect("audio: the choked whoosh doesn't cross", "whoosh" not in text)
    s_lines, s_fails = vaudio.silences(tl, xa, sra)
    s_text = "\n".join(s_lines)
    expect("audio passes the muted silence", "ok: the beat before the end" in s_text)
    expect("audio fails the noisy silence", "FAIL: a silence with noise in it" in s_text and s_fails == 1)
    y_lines, y_fails = vaudio.sync(tl, xa, sra)
    y_text = "\n".join(y_lines)
    expect("audio finds the sound on the placed hit", "ok: frame 60" in y_text)
    expect("audio flags the hit with nothing on it", "CHECK: frame 90" in y_text and y_fails == 1)
    vaudio.spectrogram(tl, xa, sra, os.path.join(OUT, "spectrogram.png"))

    import analyze

    res = analyze.analyze(mp4, os.path.join(OUT, "analysis"), 4.0, tl)
    expect(f"analyze finds the cut into calm (cuts at {res['cuts']})", any(abs(t - 3.5) < 0.05 for t in res["cuts"]))
    expect("analyze measures the loudness", res["loudness"] is not None and abs(res["loudness"]["I"] + 14) < 1)

    sheets_out = sheets.contact(mp4, 6, tl, OUT) + sheets.cuts(mp4, tl, OUT)
    expect(f"sheets made {len(sheets_out)} sheets", len(sheets_out) == 2 and all(os.path.exists(p) for p in sheets_out))
    for name, fn in (("slam", lambda: fx.slam(ts.line("GO", 40, stroke=0.1), 2)),
                     ("decode", lambda: fx.decode("HELLO THERE", 6, 3)),
                     ("whip", lambda: fx.whip(_scene(0), 40)),
                     ("tear", lambda: fx.tear(_scene(0), 0.5, 1)),
                     ("datamosh", lambda: fx.datamosh(_scene(0), _scene(9), 0.5, 2)),
                     ("chroma", lambda: fx.chroma(_scene(0), 3)),
                     ("fit_blurred", lambda: look.fit_blurred(_scene(0)[: H // 3], W, H))):
        try:
            fn()
            expect(f"fx/look {name} runs", True)
        except Exception as e:  # noqa: BLE001
            expect(f"fx/look {name} runs ({e})", False)

    sys.path.insert(0, os.path.join(ROOT, "tools", "roblox"))
    import pose

    rest = pose.soles(*pose.at([(0.0, "idle")], 0.0, drift_amount=0.0))

    def feet_off(keys_pose, drifting: bool = True, planted: bool = True) -> float:
        """How far a pose's sole corners are from rest, turned with the body about the hips (studs), with drift."""
        joints, rootpos = pose.at([(0.0, keys_pose)], 1.0, drift_amount=1.0 if drifting else 0.0, seed=2,
                                  planted=planted)
        yaw = pose.body_angles(pose.angles(*joints["root"]))[1]
        ry = pose.angles(0, yaw, 0)
        worst = 0.0
        for leg, cs in pose.soles(joints, rootpos).items():
            for a, b in zip(cs, rest[leg]):
                e = pose._apply(ry, (b[0], b[1] + 1.0, b[2]))
                worst = max(worst, abs(a[0] - e[0]), abs(a[1] - (e[1] - 1.0)), abs(a[2] - e[2]))
        return worst

    off = max(feet_off(p) for p in ("laugh", "slump", "lean_in", {"root": (-12, 25, 0)}))
    expect(f"pose keeps the feet still under leans, a turned lean and drift ({off:.5f} studs)", off < 0.001)
    off = feet_off("laugh", drifting=False, planted=False)
    expect(f"pose: an unplanted lean moves them ({off:.2f} studs)", off > 0.3)
    j, rp = pose.at([(0.0, {"root": (0, 0, 8)})], 0.0, drift_amount=0.0)
    lows = {leg: min(c[1] for c in cs) + 3.0 for leg, cs in pose.soles(j, rp).items()}
    expect(f"pose: a roll lifts a foot and sinks none ({lows['rh']:.3f}, {lows['lh']:.3f} studs above the floor)",
           min(lows.values()) > -0.001 and min(lows.values()) < 0.001 and max(lows.values()) > 0.1)

    def unplanted(t):
        w = pose.walk(t)
        return pose._harness({jn: pose.rotation(jn, w[jn]) for jn in pose.JOINTS}, w["rootpos"])

    good = pose.walk_check()
    fast = pose.walk_check(travel=lambda t: 1.1 * pose.walk_travel(t))
    low = pose.walk_check(frames=lambda t: (lambda jj, r: (jj, [r[0], 0.0, r[2]]))(*pose.walking(t)))
    loose = pose.walk_check(frames=unplanted)
    fmt = lambda r: ", ".join(f"{k} {v:.4f}" for k, v in r.items())  # noqa: E731
    expect(f"pose: the walk keeps its feet ({fmt(good)})",
           good["slip"] < 0.001 and good["sink"] < 0.001 and good["lift"] < 0.001 and good["scrape"] < 0.04)
    expect(f"pose: a walk 10% too fast slips ({fmt(fast)})", fast["slip"] > 0.005)
    expect(f"pose: a walk at standing height sinks ({fmt(low)})", low["sink"] > 0.03)
    expect(f"pose: a walk that isn't planted floats or sinks ({fmt(loose)})",
           loose["lift"] > 0.01 or loose["sink"] > 0.01)
    steps = pose.walk_steps(2.0)
    gaps = [b[0] - a[0] for a, b in zip(steps, steps[1:])]
    expect(f"pose: footsteps every 20 frames, left and right in turn ({steps[:4]}...)",
           all(19 <= g <= 21 for g in gaps) and all(a[1] != b[1] for a, b in zip(steps, steps[1:])))
    against = all(pose.walk(k / 60)["rs"][0] * pose.walk(k / 60)["rh"][0] < 0 for k in range(40)
                  if abs(pose.walk(k / 60)["rh"][0]) > 10)
    expect("pose: the walk's arms swing against its legs", against)

    def speed_jump(leg_angle) -> float:
        """The biggest jump in a leg's angular speed (degrees a frame at 60 fps) where its phases change."""
        d = 1e-7
        rate = lambda p: (leg_angle(p + d) - leg_angle(p - d)) / (2 * d) / 40  # noqa: E731  (40 frames a cycle)
        return max(abs(rate(b + 1e-5) - rate(b - 1e-5)) for b in (0.6, 1.0))
    good_jump = speed_jump(lambda p: math.degrees(pose._leg(p % 1.0, 30.0, 0.6)[0]))
    bad_jump = speed_jump(lambda p: math.degrees(pose._leg(p % 1.0, 30.0, 0.6)[0]) if p % 1.0 < 0.6 else
                          (-30 + 60 * (3 * ((p % 1.0 - 0.6) / 0.4) ** 2 - 2 * ((p % 1.0 - 0.6) / 0.4) ** 3)))
    expect(f"pose: a leg changes phase at an even speed ({good_jump:.3f} deg a frame; a swing that starts and ends "
           f"still jumps {bad_jump:.2f})", good_jump < 0.1 and bad_jump > 0.5)
    try:
        pose.walk(0.1, stance=0.45)
        expect("pose: a walk with a stance under half is refused", False)
    except ValueError:
        expect("pose: a walk with a stance under half is refused", True)

    xs = [pose.pose_at([(0.0, "idle"), (0.1, "point")], 0.1 + k / 60)["rs"][0] for k in range(8)]
    expect(f"pose snaps in 5 frames, two thirds of the way on the first, a little past ({[round(x) for x in xs]})",
           0.6 < xs[1] / 90 < 0.75 and all(abs(x - 90) < 1e-6 for x in xs[5:]) and 90 < max(xs) <= 90 + pose.CAP)
    keys = [(0.0, "arms_out"), (0.1, "hands_on_head")]
    big = [pose.pose_at(keys, 0.1 + k / 60)["rs"] for k in range(8)]
    target, begin = pose.resolve("hands_on_head")["rs"], pose.resolve("arms_out")["rs"]
    beyond = [max((a - b) * (1 if b > c else -1) for a, b, c in zip(f, target, begin) if b != c) for f in big]
    past = max(beyond)
    flat = any(x > past / 2 and y > past / 2 and abs(x - y) < 0.5 for x, y in zip(beyond, beyond[1:]))
    expect(f"pose: a big snap goes at most {pose.CAP:.0f} degrees past, without stalling ({past:.1f})",
           past <= pose.CAP + 0.01 and not flat)
    path = pose.pose_at([(0.0, "hands_on_hips"), (0.1, "cheer")], 0.1 + 1 / 60)["rs"]
    expect(f"pose: a raise follows the numbers, through the front ({tuple(round(v) for v in path)})",
           -10 < path[0] < 176)

    def gap(p):
        return pose.clearance(pose.at([(0.0, p)], 0.0, drift_amount=0.0)[0])

    worst = max((gap(p), p) for p in pose.POSES)
    old = gap({"ls": (158, 0, 32), "rs": (158, 0, -32), "neck": (-8, 0, 0)})
    chest = gap({"ls": (60, 0, 75), "rs": (64, 0, -75)})
    expect(f"pose: every pose keeps its arms out of the head and torso (worst {worst[0]:.3f} studs, {worst[1]}); "
           f"the old hands_on_head went {old:.2f} into the head, forearms pushed in {chest:.2f} into the chest",
           worst[0] <= 0.1 and old > 0.25 and chest > 0.25)
    clips, clean = pose.snap_clearance("idle", "arms_crossed"), pose.snap_clearance("idle", "arms_out")
    expect(f"pose: snap_clearance finds an arm through the chest between poses ({clips:.2f} studs; a clean snap "
           f"{clean:.3f})", clips > 0.2 and clean < 0.01)

    import camera

    def monotone(f) -> bool:
        us = [k / 200 for k in range(201)]
        vals = [f(u) for u in us]
        return abs(vals[0]) < 1e-9 and abs(vals[-1] - 1) < 1e-9 and all(b >= a - 1e-12 for a, b in zip(vals, vals[1:]))

    good_eases = all(monotone(f) for f in camera.EASES.values())
    expect(f"camera: every ease runs from 0 to 1 without going back ({', '.join(camera.EASES)}); one that overshoots "
           f"fails", good_eases and not monotone(pose.ease_out_back))
    a = camera.aim((0, 4.5, 0), distance=9)
    b, c = camera.aim((0, 4.5, 0), distance=5), camera.dutch(camera.aim((2, 4.5, 0), distance=6), 12)
    path = camera.moves([(0.0, a), (0.1, b, 0.25, "out"), (0.2, c, 0.2, "inout")])

    def jump(p) -> float:
        return max(abs(x - y) for x, y in zip(p(0.2 - 1e-6)["pos"], p(0.2 + 1e-6)["pos"]))

    def restart(t):  # a planted failure: the second move starts from the first's target, not where the camera was
        return camera.blend(b, c, camera.ease_in_out(min(1, (t - 0.2) / 0.2))) if t >= 0.2 else path(t)
    ends = max(abs(x - y) for x, y in zip(path(0.45)["pos"], c["pos"])) + abs(path(0.45)["roll"] - 12)
    expect(f"camera: a move cut short by the next carries on from where it was ({jump(path):.5f} studs; restarting "
           f"from its target jumps {jump(restart):.2f}) and ends on its view ({ends:.5f})",
           jump(path) < 0.01 and jump(restart) > 0.3 and ends < 1e-6)
    push = camera.moves([(0.0, a), (0.0, b, 0.25, "out")])
    steps = [math.dist(push((k + 1) / 60)["pos"], push(k / 60)["pos"]) for k in range(15)]
    whip = camera.moves([(0.0, a), (0.0, b, 0.25, "in")])
    wsteps = [math.dist(whip((k + 1) / 60)["pos"], whip(k / 60)["pos"]) for k in range(15)]
    expect(f"camera: an ease-out push is fastest on its first frame ({steps[0]:.2f} studs, then "
           f"{steps[1]:.2f}, {steps[2]:.2f}...); an ease-in one isn't",
           steps[0] == max(steps) and all(x >= y for x, y in zip(steps, steps[1:])) and wsteps[0] < max(wsteps))
    left, right = camera.aim((0, 4.5, 0), distance=5, fov=45), camera.aim((5, 4.5, 0), distance=5, fov=45)
    swoop = camera.moves([(0.0, left), (0.1, right, 0.15, "inout")])
    widths = [camera.smear(swoop, k / 60) for k in range(20)]
    still = camera.smear(camera.moves([(0.0, left)]), 0.2)
    expect(f"camera: a swoop's smear is 0 while it holds and widest mid-move ({[round(w) for w in widths[5:17]]} px); "
           f"a camera that doesn't move gets none ({still:.1f})",
           widths[0] < 1 and widths[-1] < 1 and max(widths) > 100 and widths.index(max(widths)) in (10, 11)
           and still < 1)
    drift = max(math.dist(camera.hold(a, k / 60)["pos"], a["pos"]) for k in range(240))
    expect(f"camera: a hold drifts slowly ({drift:.3f} studs at 9 studs back)", 0.005 < drift < 0.06)

    def rate(f, u):
        lo, hi = max(0.0, u - 1e-4), min(1.0, u + 1e-4)
        return (f(hi) - f(lo)) / (hi - lo)
    io = [rate(camera.ease_in_out, u) for u in (0.0, 0.5, 1.0)]
    lin = [rate(camera.EASES["linear"], u) for u in (0.0, 0.5, 1.0)]
    expect(f"camera: a swoop starts and ends still and is fastest midway ({[round(x, 2) for x in io]}); linear isn't",
           io[0] < 0.01 and io[2] < 0.01 and abs(io[1] - 1.5) < 0.01 and not (lin[0] < 0.01))
    peak = max(widths)
    sym = abs(camera.smear(swoop, 0.175 - 0.02) - camera.smear(swoop, 0.175 + 0.02))
    cut = camera.moves([(0.0, left), (0.1, right, 0.0)])
    expect(f"camera: a swoop's smear peaks at {peak:.0f} px (150-190 for half a frame's slide), evenly either side "
           f"of its middle ({sym:.2f}); a cut gets none ({camera.smear(cut, 0.1):.0f})",
           150 < peak < 190 and sym < 1 and camera.smear(cut, 0.1) == 0)
    near_drift = max(math.dist(camera.hold(b, k / 60)["pos"], b["pos"]) for k in range(240))
    side = camera.view((9, 4.5, 0), (0, 4.5, 0))
    side_drift = max(abs(camera.hold(side, k / 60)["pos"][2]) for k in range(240))
    expect(f"camera: drift grows with distance ({drift:.3f} studs at 9 back, {near_drift:.3f} at 5) and works for a "
           f"camera facing sideways ({side_drift:.3f} across its frame)",
           near_drift > 0 and 1.5 < drift / near_drift < 2.0 and side_drift > 0.01)
    ring = camera.aim((0, 4.5, 0), toward=(0, 0, 1), distance=6)
    swing = camera.moves([(0.0, ring), (0.0, camera.orbit(ring, 90), 0.3, "inout")])
    radius = min(math.dist(swing(k / 60)["pos"], (0, 4.5, 0)) for k in range(19))
    expect(f"camera: a move between orbit views keeps its distance ({radius:.2f} of 6 studs at the closest)",
           abs(radius - 6) < 0.01)
    over = camera.ots((0, 4.2, 7), (0, 4.5, 0), side=1.3, behind=2.8, up=0.6)
    fwd = camera._unit(camera._sub((0, 4.5, 0), (0, 4.2, 7)))
    right = camera._unit(camera._cross(fwd, (0, 1, 0)))
    lowv, topv = camera.low((0, 3.6, 0), eye=2.5), camera.top((0, 3, 0), height=8, up=(0, 0, 1))
    _, _, top_up = camera.axes(topv)
    expect("camera: over the shoulder sits behind the near actor on the side asked; low sits at its eye height; "
           "top-down frames with its up; dutch hands the harness its roll",
           math.dist(over["pos"], (0, 4.5, 0)) > math.dist((0, 4.2, 7), (0, 4.5, 0))
           and camera._dot(camera._sub(over["pos"], (0, 4.2, 7)), right) > 1.2 and abs(lowv["pos"][1] - 2.5) < 1e-9
           and abs(top_up[2] - 1) < 1e-9 and camera.state(camera.dutch(a, 14))["cam"]["roll"] == 14)
    import time as _time
    many = camera.moves([(0.0, a)] + [(0.05 * i, camera.orbit(a, 10 * i), 0.1) for i in range(1, 20)])
    t0 = _time.time()
    for k in range(60):
        many(k / 60)
    took = _time.time() - t0
    expect(f"camera: a path of 20 keys takes {took * 1000:.0f} ms for 60 frames", took < 1.0)
    bar = np.zeros((9, 101, 3), np.float32)
    bar[:, 50] = 1.0
    st, wh = fx.streak(bar, 31)[4, 35:66, 0], fx.whip(bar, 31)[4, 35:66, 0]
    tapered = st.argmax() == 15 and all(st[i] <= st[i + 1] + 1e-6 for i in range(15)) and st[1] < 0.5 * st[15]
    flat = wh.max() - wh[wh > 0].min() < 1e-6
    expect("fx: streak tapers to its ends (one streak per feature); whip's flat sweep doesn't", tapered and flat)

    import look as _look

    lin = _look.srgb_to_linear(bar)
    out = fx.streak(bar, 31)
    spread = int((out[4, :, 0] > 0.01).sum())
    energy = float(_look.srgb_to_linear(out)[4, :, 0].sum() / lin[4, :, 0].sum())
    expect(f"fx: streak spreads a line over its width ({spread} px of 31) and keeps its light ({energy:.3f} in linear "
           f"light); left alone or blended in sRGB it wouldn't", 27 <= spread <= 33 and abs(energy - 1) < 0.02)
    eye = camera.aim((0, 4.5, 0), toward=(0, 0, 1), distance=5, fov=45)
    c0, c_up, c_right = (camera.project(eye, p) for p in ((0, 4.5, 0), (0, 5.5, 0), (1, 4.5, 0)))
    expect(f"camera: project puts the aim at the centre ({c0[0]:.1f}, {c0[1]:.1f}), a point above it higher and one "
           f"to the right further right", abs(c0[0] - 480) < 0.5 and abs(c0[1] - 853.5) < 0.5 and c_up[1] < c0[1]
           and c_right[0] > c0[0])
    hi = camera.aim((0, 4.5, 0), toward=(0, 0, 1), distance=6, height=2)
    around = camera.moves([(0.0, hi), (0.0, camera.orbit(hi, 150), 0.3, "inout")])
    span = [math.dist(around(k / 60)["pos"], (0, 4.5, 0)) for k in range(19)]
    opp = camera.moves([(0.0, camera.view((0, 5.5, 6), (0, 4.5, 0))),
                        (0.0, camera.view((0, 3.5, -6), (0, 4.5, 0)), 0.3)])
    pan = camera.moves([(0.0, camera.view((0, 4, 5), (0, 4, 0))),
                        (0.0, camera.view((0, 4, 5), (5, 4, 5)), 0.3, "inout")])
    still = max(math.dist(pan(k / 60)["pos"], (0, 4, 5)) for k in range(19))
    mid = camera.blend(camera.view((0, 4, 5), (0, 4, 0), fov=40), camera.view((1, 4, 5), (1, 4, 0), fov=60),
                       0.5)
    expect(f"camera: an orbit above its subject keeps its distance ({max(span) - min(span):.4f}), opposite views "
           f"end on the key ({math.dist(opp(0.5)['pos'], (0, 3.5, -6)):.4f}), a pan keeps the camera still "
           f"({still:.4f}), "
           f"the field of view blends ({mid['fov']:.0f})",
           max(span) - min(span) < 1e-6 and math.dist(opp(0.5)["pos"], (0, 3.5, -6)) < 1e-6 and still < 1e-9
           and abs(mid["fov"] - 50) < 1e-9)
    topv2 = camera.top((0, 3, 0), height=8, up=(0, 0, 1))
    to_level = camera.moves([(0.0, topv2),
                             (0.0, camera.aim((0, 4.5, 0), toward=(0, 0, -1), distance=6), 0.3, "inout")])
    over2 = camera.ots((0, 4.2, 7), (0, 4.5, 0))
    focus = camera.back(over2, 1.5)["dof"][0] - over2["dof"][0]
    expect(f"camera: top-down keeps its up in the harness's keys, a move out of it stays valid, and back() moves the "
           f"focus with the camera ({focus:.2f} studs for 1.5)",
           camera.state(topv2)["cam"].get("up") == [0.0, 0.0, 1.0]
           and all(camera.axes(to_level(k / 60)) for k in range(19))
           and abs(focus - 1.5) < 1e-9)
    small_cut = camera.moves([(0.0, left), (0.1, camera.aim((0.5, 4.5, 0), distance=5, fov=45), 0.0)])
    far = camera.moves([(0.0, left), (0.1, camera.aim((20, 4.5, 0), distance=5, fov=45), 0.15, "inout")])
    fast_peak = max(camera.smear(far, k / 60) for k in range(20))
    drifts = {s_: camera.hold(a, 0.5, seed=s_)["pos"][0] for s_ in (0, 1)}
    expect(f"camera: no smear across a half-stud cut ({camera.smear(small_cut, 0.1):.0f}); a 20-stud swoop keeps its "
           f"blur at full speed ({fast_peak:.0f} px); two seeds drift apart",
           camera.smear(small_cut, 0.1) == 0 and fast_peak > 500 and abs(drifts[0] - drifts[1]) > 1e-4)

    bad = [w for w, ok in results if not ok]
    print(f"\n{len(results) - len(bad)}/{len(results)} as expected. Files in {OUT}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
