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
import subprocess
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
    flat_mp4 = os.path.join(OUT, "flat.mp4")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                    "testsrc2=s=180x320:d=0.5:r=30", "-f", "lavfi", "-i", "color=c=white:s=180x320:d=0.2:r=30",
                    "-f", "lavfi", "-i", "color=c=black:s=180x320:d=0.2:r=30", "-filter_complex",
                    "[0:v][1:v][2:v]concat=n=3:v=1:a=0", "-pix_fmt", "yuv420p", flat_mp4], check=True)
    flats = qc.flat_frames(flat_mp4)
    expect(f"qc fails the white frames a camera inside a ceiling makes, not the black ones ({flats})",
           len(flats) == 1 and "frames 15-20" in flats[0])
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
    bare = Timeline({"fps": tl.fps, "clips": [{"name": c["name"], "frames": c["frames"]} for c in tl.clips]})
    b_lines, b_fails = vaudio.crossings(bare, xa, sra)
    expect(f"audio fails a timeline with sound but no cue sheet ({b_fails} failure)",
           b_fails == 1 and any("declares no cues" in line for line in b_lines))
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
    sj, sr = pose.at([(0.0, "sit")], 0.0, drift_amount=0.0)
    seat = min(c[1] for cs in pose.soles(sj, sr).values() for c in cs) + 3.0
    ahead = pose.reach(sj)[2]
    expect(f"pose: 'sit' rests the legs on a seat {seat:.2f} studs up (the cafeteria's benches are 1.0), reaching "
           f"{-ahead:.1f} ahead, the body {-sr[1]:.1f} lower than standing", abs(seat - 1.0) < 0.02 and ahead < -1.9
           and abs(sr[1] + 0.5) < 1e-9)
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

    voice_checks(expect)
    caption_checks(expect)
    pipeline_checks(expect)

    bad = [w for w, ok in results if not ok]
    print(f"\n{len(results) - len(bad)}/{len(results)} as expected. Files in {OUT}")
    return 1 if bad else 0


def voice_checks(expect) -> None:
    """The voice tools against synthetic speech: harmonic 'words', a silence and a breath between them."""
    import master
    import speech
    import voice

    sr = 48000

    def word(f0: float, dur: float) -> np.ndarray:
        t = np.arange(int(dur * sr)) / sr
        x = sum(np.sin(2 * np.pi * f0 * k * t) / k for k in range(1, 15))
        env = np.minimum(1, np.minimum(t / 0.02, (dur - t) / 0.02))
        return 0.3 * x * env

    tones = {f: speech.pitch(word(f, 1.0), sr)["median"] for f in (110.0, 220.0, 330.0)}
    expect(f"speech: YIN finds 110, 220 and 330 Hz ({tones})",
           all(abs(v - f) / f < 0.01 for f, v in tones.items()))
    rng = np.random.default_rng(5)
    breath = np.convolve(0.02 * rng.standard_normal(int(0.25 * sr)), np.ones(24) / 24, mode="same")  # a dark hiss
    line = np.concatenate([np.zeros(int(0.2 * sr)), word(200, 0.5), np.zeros(int(0.3 * sr)), breath,
                           np.zeros(int(0.1 * sr)), word(240, 0.5), np.zeros(int(0.3 * sr))])
    y, cuts = voice.tighten(voice.trim(line, sr), sr, keep=0.07)
    db = speech.frames_db(y, sr)
    loud = db > np.percentile(db, 95) - 20
    on = np.flatnonzero(loud)
    holes = np.flatnonzero(np.diff(on) > 1)  # where the loud frames break: the gap between the two words
    gap = round((on[holes[0] + 1] - on[holes[0]] - 1) * 0.01, 2) if len(holes) == 1 else None
    kept = int(loud.sum()) * 0.01
    expect(f"voice: tighten cuts a 0.65 s pause and breath to {gap} s and keeps both words ({kept:.2f} of 1.0 s "
           f"loud)", gap is not None and gap <= 0.1 and abs(kept - 1.0) < 0.06 and len(cuts) == 1)
    y2, _ = voice.normalize(line, sr, -18.0)
    expect(f"voice: normalize sets the speech level ({speech.level(y2, sr):.2f} dB) under -1 dBTP "
           f"({master.true_peak_db(y2[:, None]):.2f})",
           abs(speech.level(y2, sr) + 18) < 0.3 and master.true_peak_db(y2[:, None]) <= -0.9)
    heard = [{"word": w} for w in "the title page for a 40 -slide project".split()]
    ok = speech.match("[sarcastic] The title page. For a forty-slide project.", heard)
    miss = speech.match("The title page. For a forty-slide project.", heard[:2] + heard[3:])
    expect(f"speech: match takes '40' for 'forty' and drops tags ({ok['ratio']}); a missing word fails "
           f"({miss['missing']})", ok["ratio"] == 1.0 and miss["missing"] == ["page"])
    role = {"pitch": [175, 265], "max_pause": 0.2, "level_db": -18.0}
    m_good = {"match": {"ratio": 1.0, "missing": [], "extra": []}, "lead": 0.01, "tail": 0.05, "longest_pause": 0.08,
              "pitch": {"median": 210.0, "voiced_s": 1.0}, "words_per_s": 3.5, "level_db": -18.0,
              "true_peak_db": -2.0}
    planted = {"a long pause": dict(m_good, longest_pause=0.4),
               "the wrong voice's pitch": dict(m_good, pitch={"median": 330.0, "voiced_s": 1.0}),
               "a missing word": dict(m_good, match={"ratio": 0.9, "missing": ["page"], "extra": []}),
               "a tag read aloud": dict(m_good, match={"ratio": 1.0, "missing": [], "extra": ["excited"]}),
               "the wrong level": dict(m_good, level_db=-21.0),
               "a peak over -1 dBTP": dict(m_good, true_peak_db=-0.5),
               "silence before the line": dict(m_good, lead=0.3)}
    good = [ok_ for ok_, _ in voice.check(m_good, role, {})]
    caught = {k: sum(1 for ok_, _ in voice.check(m, role, {}) if not ok_) == 1 for k, m in planted.items()}
    unmeasured = voice.check(dict(m_good, pitch={"median": None, "voiced_s": 0.05}), role, {})
    expect(f"voice: check passes a good line and fails each planted fault alone ({caught}); a pitch too short to "
           f"measure is noted, not failed", all(good) and all(caught.values()) and all(ok_ for ok_, _ in unmeasured))
    # the S5 review's cases: a soft 'h' onset after a pause, and a creaky tail before one, are sound, not silence
    t = np.arange(int(0.12 * sr)) / sr
    h_onset = np.convolve(rng.standard_normal(len(t)), np.ones(6) / 6, mode="same") * 0.03  # about 20 dB under
    creak = sum(np.sin(2 * np.pi * 45 * k * t) / k for k in range(1, 6)) * 0.012 * np.exp(-t / 0.08)
    line2 = np.concatenate([word(200, 0.4), creak, np.zeros(int(0.35 * sr)), h_onset, word(220, 0.4)])
    y3, cuts3 = voice.tighten(line2, sr, keep=0.07)
    removed = sum(b - a for a, b in cuts3)
    expect(f"voice: tighten keeps a creaky tail and an 'h' onset, cutting only the silence between them "
           f"({removed:.3f} s cut of the 0.35 s silence)", len(cuts3) == 1 and 0.2 < removed <= 0.29)
    # M3's review: the transcriber starts a sentence's first word straight after the last one, over a scoff and a
    # pause; the word is said 0.47 s later
    said = 0.4 + 0.05 + 0.12 + 0.35   # where its "f" starts: 60 ms of hiss before the voice
    fric = np.convolve(rng.standard_normal(int(0.06 * sr)), [1, -1], mode="same") * 0.05
    line_r = np.concatenate([word(200, 0.4), np.zeros(int(0.05 * sr)), word(150, 0.12), np.zeros(int(0.35 * sr)),
                             fric, word(220, 0.4)])
    heard_r = [{"word": "page", "start": 0.0, "end": 0.42}, {"word": "for", "start": 0.42, "end": 1.3}]
    after_stop = voice.refine_words(heard_r, line_r, sr, "Page. For")
    mid_phrase = voice.refine_words(heard_r, line_r, sr, "Page for")
    expect(f"voice: a sentence's first word timed over the scoff and pause before it starts where its sound does "
           f"({after_stop[1]['start']:.2f} s; its 'f' starts at {said:.2f}); mid-phrase it's left alone "
           f"({mid_phrase[1]['start']:.2f})",
           abs(after_stop[1]["start"] - said) <= 0.02 and mid_phrase[1]["start"] == 0.42)
    narrator = {"pitch": [90, 340], "max_pause": 0.2, "level_db": -18.0, "center": 214, "register_st": [-7, 9]}
    low = voice.check(dict(m_good, pitch={"median": 99.0, "voiced_s": 1.0}), narrator, {})
    shout = voice.check(dict(m_good, pitch={"median": 329.0, "voiced_s": 1.0}), narrator, {})
    expect(f"voice: a line an octave under its voice's own pitch fails the register check; a shout above it passes "
           f"({[w for ok_, w in low if not ok_]})",
           [w for ok_, w in low if not ok_] and all("register" not in w for ok_, w in shout if not ok_)
           and any("register" in w for ok_, w in low if not ok_))
    # M5's case, its measured profile (line a, 4.86-5.08 s): silence 60 ms, the floor 38 dB under for 70 ms, silence
    # 10, floor 10, silence 40, floor 35 dB under for 20, silence 10: a 0.22 s gap the old rule couldn't cut
    w1 = word(200, 0.5)
    top = np.percentile(speech.frames_db(w1, sr), 95)

    def floor(ms, under):
        return rng.standard_normal(int(ms / 1000 * sr)) * 10 ** ((top - under) / 20)

    flick = np.concatenate([np.zeros(int(0.06 * sr)), floor(70, 38), np.zeros(int(0.01 * sr)), floor(10, 38),
                            np.zeros(int(0.04 * sr)), floor(20, 35), np.zeros(int(0.01 * sr))])
    line5 = np.concatenate([w1, flick, word(240, 0.5)])
    y5, cuts5 = voice.tighten(line5, sr, keep=0.05)
    left = max((b - a for a, b in speech.pauses(y5, sr)), default=0.0)
    expect(f"voice: tighten cuts a 0.22 s gap whose floor wobbles round the silence line ({left:.2f} s left, "
           f"{sum(b - a for a, b in cuts5):.2f} s cut)", left <= 0.12 and len(cuts5) >= 1)
    crest = np.concatenate([np.zeros(int(0.1 * sr)), word(80, 0.6) * np.where(np.arange(int(0.6 * sr)) % 600 < 12,
                                                                            4.0, 1.0), np.zeros(int(0.1 * sr))])
    y4, _ = voice.normalize(crest, sr, -18.0)
    expect(f"voice: a deep, peaky line is limited to -1 dBTP ({master.true_peak_db(y4[:, None]):.2f}) and still "
           f"reaches its level ({speech.level(y4, sr):.2f} dB)",
           master.true_peak_db(y4[:, None]) <= -0.95 and abs(speech.level(y4, sr) + 18) < 0.3)
    expect(f"speech: digital silence has no pitch ({speech.pitch(np.zeros(sr), sr)['median']}); a tag read aloud "
           f"is an extra word ({speech.match('[excited] Hi there.', [{'word': 'Excited.'}, {'word': 'Hi'}, {'word': 'there.'}])['extra']})",
           speech.pitch(np.zeros(sr), sr)["median"] is None and
           speech.match("[excited] Hi there.", [{"word": "Excited."}, {"word": "Hi"}, {"word": "there."}])["extra"]
           == ["excited"])


def caption_checks(expect) -> None:
    """The caption styles against what was measured on the reference frames (docs/CAPTIONS.md)."""
    import cv2

    import captions

    def fill_lines(layer, x, y):
        """Each line's (left, right, baseline) on the frame: rows of white fill, grouped."""
        fill = ((layer[..., :3].min(axis=2) > 0.84) & (layer[..., 3] > 0.84)).astype(np.uint8)
        n, lab, stats, _ = cv2.connectedComponentsWithStats(fill, 8)
        gl = sorted((stats[i] for i in range(1, n) if stats[i][4] > 15), key=lambda s: s[1] + s[3] / 2)
        rows = []
        for s in gl:
            c = s[1] + s[3] / 2
            if rows and abs(c - rows[-1][0]) < 25:
                rows[-1][1].append(s)
            else:
                rows.append([c, [s]])
        return [(x + min(s[0] for s in g), x + max(s[0] + s[2] for s in g),
                 y + int(np.median([s[1] + s[3] for s in g]))) for _, g in rows if len(g) > 1]  # not an i's dot

    layer, (x, y) = captions.render("why are popular GIRLS so ANNOYING?\U0001F940", "comedy")
    lines = fill_lines(layer, x, y)
    colour = layer[..., 3] > 0.5
    red = colour & (layer[..., 0] > 0.6) & (layer[..., 1] < 0.4)
    expect(f"captions: the comedy test line wraps as the reference's ({captions.lines_of('why are popular GIRLS so ANNOYING?', 'comedy')}), "
           f"baselines at {[b for _, _, b in lines]} (reference 1485, 1548), width {lines[0][1] - lines[0][0]} "
           f"(773), the emoji drawn", len(lines) == 2 and abs(lines[0][2] - 1485) <= 3 and abs(lines[1][2] - 1548)
           <= 3 and abs((lines[0][1] - lines[0][0]) - 773) <= 15 and red.sum() > 200)
    layer, (x, y) = captions.render("until you TOUCH", "story")
    lines = fill_lines(layer, x, y)
    expect(f"captions: the story test line's baselines at {[b for _, _, b in lines]} (reference 460, 557)",
           len(lines) == 2 and abs(lines[0][2] - 460) <= 3 and abs(lines[1][2] - 557) <= 3)
    long = captions.lines_of("this caption keeps going and going well past the width of any phone screen", "comedy")
    try:
        captions.render("no picture for this ☃", "comedy")  # a snowman: not in the emoji set
        raised = False
    except FileNotFoundError:
        raised = True
    expect(f"captions: a long caption wraps to {len(long)} lines; an emoji without a picture raises instead of "
           f"drawing a box ({raised})", len(long) >= 2 and raised)


def pipeline_checks(expect) -> None:
    """make.py's plan on a made-up video with made-up word times; sfx, kit, facekit and qc's speech captions."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    sys.path.insert(0, os.path.join(ROOT, "tools", "roblox"))
    import make
    import qc
    import sfx
    from timeline import Timeline

    vdir = os.path.join(OUT, "video")
    os.makedirs(vdir, exist_ok=True)
    words = {"l1": [("Why", 0.0, 0.2), ("does", 0.2, 0.4), ("every", 0.4, 0.7), ("group", 0.7, 1.0),
                    ("project", 1.0, 1.4), ("have", 1.4, 1.6), ("that", 1.6, 1.8), ("ONE", 1.8, 2.1),
                    ("person?", 2.1, 2.6)],
             "s": [("In", 0.0, 0.1), ("this", 0.1, 0.25), ("world,", 0.25, 0.5), ("every", 0.5, 0.8),
                   ("ding", 0.8, 1.1), ("is", 1.1, 1.2), ("a", 1.2, 1.3), ("ding.", 1.3, 1.6),
                   ("Then", 1.6, 1.8), ("he", 1.8, 1.9), ("left.", 1.9, 2.3)]}
    spec = {"slug": "selftest-video", "family": "comedy", "fps": 30, "set": "baseplate",
            "sets": [{"id": "far", "name": "hallway", "at": [400, 0, 0]}],
            "cast": {"a": {"skin": [255, 204, 153]}},
            "lines": [{"id": "l1", "role": "narrator", "text": "[excited] Why does every group project have that ONE person?",
                       "emoji": "\U0001F62D"},
                      {"id": "s", "role": "story", "text": "In this world, every ding is a ding. Then he left."}],
            "shots": [{"name": "one", "seconds": "auto", "pad": 0.3,
                       "actors": {"a": {"at": [0, 3, 0], "facing": [0, 0, 1], "faces": [[0, "smile"], ["l1:one", "angry"]],
                                        "poses": [[0, "idle"], ["l1:ONE-0.1", "arms_out"]]}},
                       "camera": [{"t": 0, "aim": "a.head", "distance": 6}], "say": [{"line": "l1", "at": 0.0}],
                       "sfx": [{"sound": "boom", "at": "l1:end+0.05"}]},
                      {"name": "two", "until": "s:ding#2", "set": "far",
                       "actors": {"a": {"at": [0, 3, 0], "facing": [0, 0, 1]}},
                       "camera": [{"t": 0, "pos": [0, 4, 8], "look": [0, 4, 0]}], "say": [{"line": "s", "at": 0.1}],
                       "overlays": [{"icon": "bell", "over": "a.head", "at": "s:ding"},
                                    {"icon": "bell", "over": [1.0, 2.0, 0.0], "at": "s:ding"}]},
                      {"name": "three", "until": "s:end+0.2", "actors": {}, "camera": [{"t": 0, "pos": [0, 5, 9],
                                                                                         "look": [0, 4, 0]}]}]}
    json.dump(spec, open(os.path.join(vdir, "short.json"), "w", encoding="utf-8"), ensure_ascii=False)
    sh = make.Short(vdir)
    os.makedirs(sh.path("voice"), exist_ok=True)
    json.dump({"lines": [{"id": k, "duration": v[-1][2], "heard": " ".join(w for w, _, _ in v),
                          "words": [{"word": w, "start": a, "end": b, "p": 1.0} for w, a, b in v]}
                         for k, v in words.items()]}, open(sh.path("voice", "words.json"), "w", encoding="utf-8"))
    make.stage_plan(sh)
    plan = json.load(open(sh.path("plan.json"), encoding="utf-8"))
    one, two = plan["shots"][0], plan["shots"][1]
    face_t = one["actors"]["a"]["faces"][1][0]
    pose_t = one["actors"]["a"]["poses"][1][0]
    expect(f"make: a face keyed to 'l1:one' lands on the word ({face_t:.2f} s), 'ONE-0.1' before it ({pose_t:.2f}); "
           f"an auto shot runs to its line's end plus pad ({one['seconds']:.2f} s of 2.90)",
           abs(face_t - 1.8) < 1e-6 and abs(pose_t - 1.7) < 1e-6 and abs(one["seconds"] - 2.9) < 1 / 30 + 1e-6)
    s_start = two["start"] + 0.1
    expect(f"make: 'until s:ding#2' ends a shot on the word's second time ({two['start'] + two['seconds']:.2f} s, "
           f"expected {s_start + 1.3:.2f}); its overlay on the first 'ding' ({two['overlays'][0]['start']:.2f} s in)",
           abs(two["start"] + two["seconds"] - (s_start + 1.3)) < 1 / 30 + 1e-6
           and abs(two["overlays"][0]["start"] - 0.9) < 1e-6)
    expect(f"make: a shot in another set is moved by its offset (the actor at x {two['actors']['a']['cf']['pos'][0]}, "
           f"an icon over a point at x {two['overlays'][1]['over'][0]})",
           abs(two["actors"]["a"]["cf"]["pos"][0] - 400) < 1e-6 and abs(two["overlays"][1]["over"][0] - 401) < 1e-6)
    caps = [c["text"] for c in plan["captions"]]
    sh.family = "story"
    make.stage_plan(sh)
    story_caps = [c["text"] for c in json.load(open(sh.path("plan.json"), encoding="utf-8"))["captions"]]
    sh.family = "comedy"
    make.stage_plan(sh)
    expect(f"make: comedy captions a clause each, lower case, its emoji ({caps}); story captions 1-3 words "
           f"({story_caps})",
           caps[0].endswith("\U0001F62D") and caps[0].startswith("why does") and caps[-1] == "then he left."
           and all(1 <= len(c.split()) <= 3 for c in story_caps) and len(story_caps) >= 5)
    boom = sfx.make("boom")
    ducked = make._duck_tail(boom, 48000, 10.0, [10.3])
    tail_db = 20 * np.log10(np.abs(ducked[int(0.4 * 48000):int(0.6 * 48000)]).max()
                            / np.abs(boom[int(0.4 * 48000):int(0.6 * 48000)]).max())
    expect(f"make: a boom's tail is pulled down under the line that starts while it rings ({tail_db:.1f} dB), its "
           f"hit left alone", abs(tail_db + 12) < 0.5 and np.allclose(ducked[:int(0.2 * 48000)], boom[:int(0.2 * 48000)]))
    hits = {"fps": 30, "shots": [{"frame0": 0}, {"frame0": 60}],
            "sounds": [{"start": 1.0, "hit": True, "sound": "boom"}, {"start": 2.0, "hit": True, "sound": "boom"},
                       {"start": 1.5, "hit": False, "sound": "pop"}, {"start": 1.6, "hit": True, "sound": "ding"}]}
    z = [make._punch(hits, r) for r in (29, 30, 34, 39, 45, 60)]
    expect(f"make: a boom inside a shot punches in 7% on its frame and settles in 0.3 s; one on a cut doesn't "
           f"({[round(v, 3) for v in z]})",
           z[0] == 1.0 and abs(z[1] - 1.07) < 1e-9 and z[1] > z[2] > z[3] >= 1.0 and z[4] == 1.0 and z[5] == 1.0)
    snaps = [{"text": "a", "style": "comedy", "show": 0.0, "hide": 1.05}, {"text": "b", "style": "comedy",
                                                                           "show": 1.05, "hide": 2.0}]
    make._snap_to_cuts(snaps, [0, 30], 30)
    pre = [{"text": "a", "style": "comedy", "show": 0.0, "hide": 0.9333}, {"text": "b", "style": "comedy",
                                                                            "show": 0.9333, "hide": 2.0}]
    make._snap_to_cuts(pre, [0, 30], 30)
    expect(f"make: a caption due 2 frames before a cut waits for it, the one before staying up ({pre[1]['show']:.3f} s, "
           f"the cut at 1.000)", abs(pre[1]["show"] - 1.0) < 1e-9 and abs(pre[0]["hide"] - 1.0) < 1e-9)
    long_words = [(w, k * 0.25, k * 0.25 + 0.2) for k, w in enumerate(
        "then there's this guy, who hasn't answered the group chat since September.".split())]
    split = [c[0] for c in make._clauses(long_words, "comedy", None, False)]
    expect(f"make: a comedy sentence too long for one caption splits at its comma ({split})",
           split == ["then there's this guy,", "who hasn't answered the group chat since September."])
    chain = [{"show": 0.0, "hide": 0.26}, {"show": 0.26, "hide": 0.54}, {"show": 0.54, "hide": 0.8}]   # the old rule drew 2 on frame 32
    spans = [make._caption_frames(c, 60) for c in chain]
    expect(f"make: captions back to back never share a frame ({spans})",
           all(a[1] == b[0] for a, b in zip(spans, spans[1:])))
    expect(f"make: a caption due 1-4 frames after a cut comes in on it ({snaps[1]['show']:.3f} s, the cut at 1.000)",
           abs(snaps[1]["show"] - 1.0) < 1e-9 and abs(snaps[0]["hide"] - 1.0) < 1e-9)
    def faced(family, look_y):
        cam = [[0.0, {"pos": [0, 4.5, -10], "look": [0, look_y, 0], "roll": 0.0, "fov": 50.0, "dof": None}, 0.0, "out"]]
        return make._framing({"family": family, "shots": [{"name": "s", "seconds": 1.0, "camera": cam,
                                                           "actors": {"a": {"cf": {"pos": [0, 3, 0]}}}}]})
    high, level, low_ = faced("story", 2.5), faced("story", 4.5), faced("comedy", 6.5)
    expect(f"make: the plan flags a face under the captions: a story's high block ({high}), a comedy's low one "
           f"({low_}); a face mid-frame passes ({level})",
           len(high) == 1 and "story captions" in high[0] and len(low_) == 1 and "comedy captions" in low_[0]
           and not level)
    framed = json.load(open(sh.path("plan.json"), encoding="utf-8"))
    clean = make._framing(framed)
    framed["shots"][0]["actors"]["far"] = {"cf": {"pos": [30.0, 3.0, 0.0], "look": [30.0, 3.0, 10.0]}}
    flagged = make._framing(framed)
    expect(f"make: the framing check passes actors in shot ({clean}) and flags one the camera never sees ({flagged})",
           not clean and len(flagged) == 1 and "far" in flagged[0])
    def edged(x, look_y):
        cam = [[0.0, {"pos": [0, 4.5, -10], "look": [0, look_y, 0], "roll": 0.0, "fov": 50.0, "dof": None}, 0.0, "out"]]
        return make._framing({"family": "music", "shots": [{"name": "s", "seconds": 1.0, "camera": cam,
                                                           "actors": {"a": {"cf": {"pos": [x, 3, 0]}}}}]})
    side, bottom, middle = edged(-2.5, 4.5), edged(0.0, 8.5), edged(0.0, 4.5)
    expect(f"make: the plan flags a face cut by the frame's edge ({side}) and one down on the bottom edge under the "
           f"Shorts UI ({bottom}); a centred face passes ({middle})",
           len(side) == 1 and "right edge" in side[0] and len(bottom) == 1 and "Shorts UI" in bottom[0] and not middle)
    walker = {"camera": [[0.0, {"pos": [0, 5, 10], "look": [0, 4, 0], "roll": 0.0, "fov": 50.0, "dof": None}, 0.0,
                          "out"]], "drift": 0.0, "seed": 0,
              "actors": {"a": {"cf": {"pos": [0, 3, 0], "look": [0, 3, 10]}, "poses": [[0.0, "idle"]],
                               "faces": [[0, "smile"]],
                               "walk": {"from": [-4, 3, 0], "to": [0, 3, 0], "start": 0.5, "freq": 1.5}}}}
    walk_at = make.shot_fn({}, walker, ["a"])
    before, after = walk_at(0.2)["actors"][0]["cf"], walk_at(2.5)["actors"][0]["cf"]
    turned = [round(after["look"][k] - after["pos"][k], 2) for k in (0, 2)]
    expect(f"make: an actor waits at its walk's start ({before['pos']}), and on arriving turns to its mark's facing "
           f"({turned}, not the walk's way; M4's 'Leo sat down' stayed in profile)",
           before["pos"] == [-4, 3, 0] and abs(turned[0]) < 1e-6 and turned[1] > 0.99)
    def cam_at(pos):
        return {"name": "c", "set": None, "seconds": 0.5,
                "camera": [[0.0, {"pos": pos, "look": [0, 4, 0], "roll": 0.0, "fov": 50.0, "dof": None}, 0.0, "out"]]}
    in_set = make._cameras_in_sets({"shots": [cam_at([-9, 3.1, -12]), cam_at([0, 16, 0]), cam_at([3, 5, 0])]},
                                   {"set": "classroom", "set_options": {}})
    expect(f"make: the plan flags a camera inside a part of its set (the teacher's desk) and one above its ceiling, and "
           f"passes one in the open ({in_set})",
           len(in_set) == 2 and "inside a part" in in_set[0] and "leaves the room" in in_set[1])
    def staged(a_pos, b_pos, a_look, b_look, walk=None):
        acts = {"a": {"cf": {"pos": a_pos, "look": a_look}, "poses": [[0.0, "idle"]]},
                "b": {"cf": {"pos": b_pos, "look": b_look}, "poses": [[0.0, "idle"]]}}
        if walk:
            acts["w"] = {"cf": {"pos": walk[1], "look": walk[1]}, "walk": {"from": walk[0], "to": walk[1]}}
        return make._staging({"shots": [{"name": "s", "actors": acts}]})
    close_pair = staged([0, 3, 0], [3, 3, 0], [0, 3, 10], [3, 3, 10])
    apart = staged([0, 3, 0], [4.4, 3, 0], [0, 3, 10], [4.4, 3, 10])
    facing = staged([0, 3, 0], [2.0, 3, 0], [10, 3, 0], [-10, 3, 0])
    through = staged([-20, 3, 0], [20, 3, 0], [-20, 3, 10], [20, 3, 10], walk=([-20, 3, -10], [-17.3, 3, 10]))
    past_ok = staged([-20, 3, 0], [20, 3, 0], [-20, 3, 10], [20, 3, 10], walk=([-15.6, 3, -10], [-15.6, 3, 10]))
    expect(f"make: the plan flags actors inside each other (side by side 3 studs apart: {close_pair}; a walk 2.7 studs "
           f"from someone: {through}) and passes 4.4 apart, two facing each other 2 apart, a walk 4.4 off "
           f"({apart}, {facing}, {past_ok})",
           len(close_pair) == 1 and "overlap" in close_pair[0] and len(through) == 1 and "walk passes through a"
           in through[0] and not apart and not facing and not past_ok)
    rig = {"name": "x", "actors": {"m": {"at": [0, 3, 0], "facing": [0, 0, -1]}}}
    rest = make._point(rig, "m.face")
    rig["_poses"] = {"m": [[0.0, "idle"]]}
    idle = make._point(rig, "m.face", 0.0)
    rig["_poses"] = {"m": [[0.0, "idle"], [1.0, "slump"]]}
    early, slumped = make._point(rig, "m.face", 0.5), make._point(rig, "m.face", 2.0)
    expect(f"make: a camera aims at the face where the pose puts it: a slump's {slumped[1] - rest[1]:+.2f} studs down "
           f"and {rest[2] - slumped[2]:+.2f} forward, an idle face where it was ({idle}, before the slump {early})",
           max(abs(a - b) for a, b in zip(idle, rest)) < 1e-9 and max(abs(a - b) for a, b in zip(early, rest)) < 1e-9
           and slumped[1] - rest[1] < -0.4 and rest[2] - slumped[2] > 0.4 and abs(slumped[0]) < 1e-9)
    u1 = make._raw_name("b", 0, "https://cdn.example/gen/AAA/content.mp3?Expires=1&Signature=x")
    u2 = make._raw_name("b", 0, "https://cdn.example/gen/AAA/content.mp3?Expires=2&Signature=y")
    u3 = make._raw_name("b", 0, "https://cdn.example/gen/BBB/content.mp3?Expires=1&Signature=x")
    expect(f"make: a downloaded take is named by the take, not its signature, so new takes aren't skipped "
           f"({u1}, {u3})", u1 == u2 and u1 != u3 and "Signature" not in u1)
    names = make._names({"x": {"text": "[sad] Leo had never heard one. So Leo stopped. Then Max's dog barked."}})
    named = [c[0] for c in make._clauses([("Leo", 0, .2), ("had", .2, .4), ("never.", .4, .6), ("Max's", .6, .8),
                                          ("dog", .8, 1.0), ("barked.", 1.0, 1.2), ("I'd", 1.2, 1.3),
                                          ("go.", 1.3, 1.4), ("The", 1.4, 1.5), ("end.", 1.5, 1.7)],
                                         "story", None, True, names)]
    expect(f"make: a caption keeps a name's capital (one the script capitalizes mid-sentence) and 'I', and lowers "
           f"the rest ({named}, names {sorted(names)})",
           named == ["Leo had never.", "Max's dog barked.", "I'd go.", "the end."] and names == {"leo", "max"})
    even = [(w, i * 0.3, i * 0.3 + 0.25) for i, w in enumerate("you hear a ding. most people hear a few a day.".split())]
    broken = [c[0] for c in make._clauses(even, "story", None, True)]
    expect(f"make: story captions don't end on 'a' or leave a word alone ({broken})",
           broken[:2] == ["you hear", "a ding."]
           and all(1 < len(c.split()) <= 4 and c.split()[-1] not in make.WEAK_END for c in broken))
    caps_b = [{"text": "liked him.", "show": 0.0, "hide": 1.0}, {"text": "then he", "show": 1.0, "hide": 1.2},
              {"text": "switched schools.", "show": 1.2, "hide": 2.0}]
    make._balance(caps_b, 60)
    up = [round(c["hide"] - c["show"], 3) for c in caps_b]
    expect(f"make: a caption said too fast to read borrows time from a neighbour with some to spare ({up} s up)",
           up[1] >= qc.SPEECH_MIN + 1 / 60 - 1e-9 and caps_b[1]["show"] >= 1.0 - 0.12 - 1e-9
           and abs(caps_b[0]["hide"] - caps_b[1]["show"]) < 1e-9 and up[0] > 0.9)
    early_cap = [{"text": "everyone just liked him.", "show": 7.75, "hide": 8.74, "style": "story"},
                 {"text": "then he", "show": 8.807, "hide": 9.073, "style": "story"},
                 {"text": "switched schools.", "show": 9.073, "hide": 9.72, "style": "story"}]
    make._snap_to_cuts(early_cap, [530], 60)
    expect(f"make: a caption that waits for a cut just after it keeps its time on screen ({early_cap[1]['show']:.3f}-"
           f"{early_cap[1]['hide']:.3f} s, the cut at 8.833; M4's 'then he' lost 2 frames and failed its read)",
           abs(early_cap[1]["show"] - 530 / 60) < 1e-9
           and early_cap[1]["hide"] - early_cap[1]["show"] >= 0.266 - 1e-9 and early_cap[2]["show"] == early_cap[1]["hide"])
    tight = [{"text": "liked him.", "show": 0.0, "hide": 1.0}, {"text": "then he", "show": 1.0, "hide": 1.2},
             {"text": "switched schools forever.", "show": 1.2, "hide": 1.75}]
    make._balance(tight, 60)
    expect(f"make: a caption short of reading time hides later before it shows earlier ({caps_b[1]['show']:.3f} s, "
           f"its words at 1.000), and never shows more than 2 frames before its words ({tight[1]['show']:.3f} s)",
           abs(caps_b[1]["show"] - 1.0) < 1e-9 and 1.0 - 2 / 60 - 1e-9 <= tight[1]["show"] < 1.0)
    tl = Timeline.load(sh.path("cut.json"))
    expect(f"make: the boom after the line is a picture hit ({tl.hits})",
           len(tl.hits) == 1 and abs(tl.hits[0]["frame"] - round(2.65 * 30)) <= 1)
    fast = Timeline({"fps": 30, "clips": [{"name": "a", "frames": 30}],
                     "texts": [{"text": "a caption far too long to say in the time it's up", "start": 0, "frames": 15,
                                "speech": True},
                               {"text": "ok then", "start": 15, "frames": 12, "speech": True}]})
    rows = qc.text_times(fast, 12.0)
    expect(f"qc: a speech caption needs only its saying time; one up too short still fails ({[r[0] for r in rows]})",
           rows[0][0] == "FAIL" and rows[1][0] == "PASS")
    import look as _look
    img = np.zeros((1920, 1080, 3), np.float32)
    view = {"pos": [0, 4, 8], "look": [0, 4, 0], "roll": 0.0, "fov": 50.0, "dof": None}
    make._overlay(img, {"icon": "bell", "over": [0, 3, 0], "size": 150, "lift": 1.4}, view, 0.5)
    ys, xs = np.nonzero(img.max(axis=2) > 0.05)
    expect(f"make: an overlay pops up over its point, centred ({xs.mean():.0f}, {ys.mean():.0f} of 1080 x 1920)",
           len(xs) > 500 and abs(xs.mean() - 540) < 20 and ys.mean() < 960)
    img_o = np.zeros((1920, 1080, 3), np.float32)
    make._overlay(img_o, {"icon": "bell", "over": [9, 7, 0], "size": 150, "lift": 1.4}, view, 0.5,
                  keep=make.ICON_BAND["story"])
    ys_o, xs_o = np.nonzero(img_o.max(axis=2) > 0.05)
    expect(f"make: an icon set off the frame (M4's bells around a head in a close-up) is pulled inside it, clear of "
           f"the story captions ({len(xs_o)} pixels, x {xs_o.min() if len(xs_o) else -1}-{xs_o.max() if len(xs_o) else -1}"
           f", top {ys_o.min() if len(ys_o) else -1})",
           len(xs_o) > 500 and xs_o.max() < 1080 and ys_o.min() >= 0.33 * 1920 - 2)
    close = {"pos": [0, 4.5, 3], "look": [0, 4.5, 0], "roll": 0.0, "fov": 50.0, "dof": None}   # a head 3 studs off
    on_face, off_face = np.zeros((1920, 1080, 3), np.float32), np.zeros((1920, 1080, 3), np.float32)
    bell_ov = {"icon": "bell", "over": [0, 4.5, 0], "size": 150, "lift": 1.4}
    make._overlay(on_face, bell_ov, close, 0.5, keep=make.ICON_BAND["story"])
    make._overlay(off_face, bell_ov, close, 0.5, keep=make.ICON_BAND["story"], heads=[[0, 4.5, 0]])
    box = (slice(int(960 - 0.9 * 412), int(960 + 0.9 * 412)), slice(int(540 - 0.8 * 412), int(540 + 0.8 * 412)))
    n_on, n_off = int((on_face[box].max(axis=2) > 0.05).sum()), int((off_face[box].max(axis=2) > 0.05).sum())
    ys_f, xs_f = np.nonzero(off_face.max(axis=2) > 0.05)
    expect(f"make: an icon the captions' band pushes onto a face in a close-up moves beside the head ({n_on} pixels "
           f"on the face without the heads, {n_off} with them; drawn at x {xs_f.min() if len(xs_f) else -1}-"
           f"{xs_f.max() if len(xs_f) else -1})", n_on > 500 and n_off == 0 and len(xs_f) > 500 and xs_f.max() < 1080)
    img_t = np.zeros((1920, 1080, 3), np.float32)
    make._overlay(img_t, {"icon": None, "text": "99%", "over": [0, 3, 0], "size": 150, "lift": 1.4}, view, 0.5)
    ys_t, xs_t = np.nonzero(img_t.min(axis=2) > 0.9)   # the white fill of the label's letters
    expect(f"make: a text overlay draws its line over the point, centred ({len(xs_t)} white pixels at "
           f"{xs_t.mean() if len(xs_t) else 0:.0f}, {ys_t.mean() if len(ys_t) else 0:.0f})",
           len(xs_t) > 300 and abs(xs_t.mean() - 540) < 25 and abs(ys_t.mean() - ys.mean()) < 60)
    effects = {name: sfx.make(name) for name in sfx.EFFECTS}
    boom = effects["boom"]
    spec_b = np.abs(np.fft.rfft(boom))
    f0 = np.fft.rfftfreq(len(boom), 1 / sfx.SR)[spec_b.argmax()]
    expect(f"sfx: every effect stays under full scale; the boom peaks at {f0:.0f} Hz (the references' 48)",
           all(np.abs(x).max() <= 1.0 for x in effects.values()) and 42 <= f0 <= 52)
    import kit
    import facekit
    sizes = {}
    for name, fn in kit.SETS.items():
        st = fn({})
        code = st.luau((400, 0, 0), append=True)
        sizes[name] = len(st.parts)
        assert "_Set" in code and "Atmosphere" not in code  # an appended set leaves the lighting alone
    first = kit.SETS["hallway"]({})
    shifted = [r[4] for r in first.parts[:5]]
    code_shift = json.loads(json.loads(first.luau((100, 0, 0)).split("JSONDecode(")[1].split(")\n")[0]))["p"][0][4]
    expect(f"kit: every set's code builds ({sizes}); an offset moves its parts ({shifted[0]} -> {code_shift})",
           all(n > 0 for n in sizes.values()) and abs(code_shift - shifted[0] - 100) < 1e-6)
    prop_parts = {}
    for name in kit.PROPS:
        st = kit.SETS["stage_void"]({"props": [{"kind": name, "at": [0, 0, 0]}]})
        prop_parts[name] = len(st.parts) + len(st.signs) - len(kit.SETS["stage_void"]({}).parts)
    expect(f"kit: every prop builds in a set's options ({prop_parts})", all(n > 0 for n in prop_parts.values()))
    worded = {name: [g["text"] for g in kit.SETS[name]({}).signs if g["text"]] for name in kit.SETS}
    plain = {name: [g["text"] for g in kit.SETS[name]({"signs": False}).signs if g["text"]] for name in kit.SETS}
    gym_dance = kit.SETS["gym"]({"dance": True})
    expect(f"kit: a set's writing ({sum(len(v) for v in worded.values())} signs) all goes blank with signs False "
           f"({sum(len(v) for v in plain.values())} left); the gym dresses for a dance ({len(gym_dance.parts)} parts, "
           f"{len(gym_dance.lights)} lights against {len(kit.SETS['gym']({}).parts)} and {len(kit.SETS['gym']({}).lights)})",
           sum(len(v) for v in worded.values()) >= 6 and not any(plain.values())
           and len(gym_dance.parts) > len(kit.SETS["gym"]({}).parts) + 50
           and len(gym_dance.lights) > len(kit.SETS["gym"]({}).lights))
    bad = []
    for name in facekit.NAMES:
        a = np.asarray(facekit.draw(name))[..., 3]
        ys, xs = np.nonzero(a > 20)
        if not len(xs) or xs.min() < 110 or xs.max() > 402 or ys.min() < 64 or ys.max() > 448:
            bad.append(name)
    stray = np.zeros((512, 512), np.uint8)
    stray[20:40, 20:40] = 255  # a mark in the texture's corner, which wraps round the side of the head
    caught = np.nonzero(stray > 20)[1].min() < 110
    expect(f"facekit: all {len(facekit.NAMES)} faces draw on the front of the head ({bad or 'none outside'}); a mark "
           f"in the corner would fail", not bad and caught)


if __name__ == "__main__":
    sys.exit(main())
