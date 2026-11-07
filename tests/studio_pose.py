"""Spike S3 in Roblox Studio: pose.py checked against Roblox's own positions, the posing takes, and their measurements
(docs/ROBLOX_CAPTURE.md, "Posing R6").

Needs Roblox Studio open on a Baseplate place in the capture layout (docs/ROBLOX_CAPTURE.md, "Resolution"), the
bridge running (`python tools/roblox/studio_mcp.py serve`) and the test faces installed
(`python tools/roblox/faces.py test`). Everything it makes lives in a playtest, which it stops at the end.

    python tests/studio_pose.py check      # pose.soles() against the sole corners Roblox reports, for several poses
    python tests/studio_pose.py takes [acting walk feet]   # takes at 60 fps into build/s3/, encoded with a preview
    python tests/studio_pose.py measure    # no Studio: motion around each snap, and how steady the walk sits in frame
"""

from __future__ import annotations

import math
import os
import subprocess
import sys
import time

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "roblox"))

import capture  # noqa: E402
import faces  # noqa: E402
import pose  # noqa: E402
import stage  # noqa: E402
import studio  # noqa: E402

OUT = os.path.join(ROOT, "build", "s3")
FPS = 60
CAST = {
    "kid": {"skin": (255, 204, 153), "hair": [63690008], "face_acc": [130858694386007],
            "shirt": 4047884046, "pants": 382538503},
    "girl": {"skin": (240, 196, 160), "hair": [376526888], "shirt": 398634295, "pants": 398634487},
}
KEYS = [(0.0, "idle"), (0.35, "arms_out"), (0.85, "hands_on_head"), (1.35, "laugh"), (1.85, "point")]
FACES = [(0.0, "smile"), (0.35, "shock"), (0.85, "angry"), (1.35, "smile"), (1.85, "angry")]
OFF = {"pos": [0, 3, 60], "look": [0, 3, 70]}  # whoever isn't in the shot waits behind the camera
X0 = -3.0  # where the walk starts


def face_at(t: float) -> str:
    """The face for time t: each changes on the first frame the body moves, a frame after its key."""
    name = FACES[0][1]
    for tk, f in FACES[1:]:
        if t + 1e-9 >= tk + 1 / FPS:
            name = f
    return faces.url(name)


def acting(t: float) -> dict:
    joints, rootpos = pose.at(KEYS, t, seed=1)
    cam_x = 0.04 * math.sin(2 * math.pi * 0.3 * t)  # the camera drifts a little while it holds
    return {"cam": {"pos": [cam_x, 3.6, 12.0], "look": [0, 3.0, 0]}, "fov": 55,
            "actors": [{"name": "kid", "cf": {"pos": [0, 3, 0], "look": [0, 3, 10]}, "face": face_at(t),
                        "joints": joints, "rootpos": rootpos},
                       {"name": "girl", "cf": OFF}]}


def walking(t: float) -> dict:
    x = X0 + pose.walk_travel(t)
    joints, rootpos = pose.walking(t)
    return {"cam": {"pos": [x + 0.6, 3.0, 11.0], "look": [x + 0.6, 2.6, 0]}, "fov": 50,
            "actors": [{"name": "girl", "cf": {"pos": [x, 3, 0], "look": [x + 10, 3, 0]}, "face": faces.url("smile"),
                        "joints": joints, "rootpos": rootpos},
                       {"name": "kid", "cf": OFF}]}


def feet(t: float) -> dict:
    """The walk again, with the camera at ankle height beside the feet: does any sole go into the floor?"""
    s = walking(t)
    x = X0 + pose.walk_travel(t)
    s["cam"], s["fov"] = {"pos": [x, 0.35, 6.0], "look": [x, 0.35, 0]}, 30
    return s


def _start() -> None:
    print(studio.play(True))
    studio.wait_for("Client", timeout=90)
    print(stage.park((0, 3, -60)))


def _stop() -> None:
    """Undo everything, each step on its own, so that one failing (no client yet) still stops the playtest."""
    for step in (capture.release, stage.clear_actors, lambda: studio.play(False)):
        try:
            print(step())
        except Exception as e:  # noqa: BLE001
            print("cleanup step failed:", e)
    time.sleep(1)
    print(studio.state().splitlines()[0])


READ = """
local m = workspace:FindFirstChild('_Actor_girl')
local hrp = m.HumanoidRootPart
local out = {}
for _, n in {'Right Leg', 'Left Leg'} do
	local p = m[n]
	for _, sx in {-0.5, 0.5} do
		for _, sz in {-0.5, 0.5} do
			local corner = Vector3.new(sx * p.Size.X, -p.Size.Y / 2, sz * p.Size.Z)
			local v = hrp.CFrame:PointToObjectSpace(p.CFrame:PointToWorldSpace(corner))
			table.insert(out, string.format('%s,%.5f,%.5f,%.5f', n, v.X, v.Y, v.Z))
		end
	end
end
return table.concat(out, ';')
"""

CHECKS = [("walk 0.00", lambda: pose.walking(0.00)), ("walk 0.10", lambda: pose.walking(0.10)),
          ("walk 0.25", lambda: pose.walking(0.25)), ("walk 0.37", lambda: pose.walking(0.37)),
          ("walk 0.55", lambda: pose.walking(0.55)),
          ("laugh", lambda: pose.at([(0.0, "laugh")], 1.0, drift_amount=0.0)),
          ("lean_in", lambda: pose.at([(0.0, "lean_in")], 1.0, drift_amount=0.0)),
          ("turned lean", lambda: pose.at([(0.0, {"root": (-12, 25, 0)})], 1.0, drift_amount=0.0)),
          ("roll", lambda: pose.at([(0.0, {"root": (0, 0, 8)})], 1.0, drift_amount=0.0)),
          ("idle, drifting", lambda: pose.at([(0.0, "idle")], 0.77, seed=3)),
          ("rootpos alone", lambda: ({j: v for j, v in pose.at([(0.0, "idle")], 0.0, drift_amount=0.0)[0].items()
                                      if j != "root"}, [0.0, 0.25, 0.0]))]


def check() -> float:
    """Pose one actor in a playtest and compare every sole corner with pose.soles(). Returns the worst gap."""
    worst = 0.0
    try:
        _start()
        print(stage.actors({"girl": CAST["girl"]}))
        capture.install()
        for name, make in CHECKS:
            joints, rootpos = make()
            capture.frame({"cam": {"pos": [0, 4, 12], "look": [0, 3, 0]}, "fov": 50,
                           "actors": [{"name": "girl", "cf": {"pos": [0, 3, 0], "look": [0, 3, -10]},
                                       "joints": joints, "rootpos": rootpos}]})
            got = {"rh": [], "lh": []}
            for row in studio.luau(READ, dm="Client").strip().split(";"):
                n, *v = row.split(",")
                got["rh" if n == "Right Leg" else "lh"].append(tuple(float(x) for x in v))
            if "root" not in joints:  # the harness poses a missing root at rest when rootpos is given
                joints = dict(joints, root=[0.0, 0.0, 0.0])
            want = pose.soles(joints, rootpos)
            gap = max(min(math.dist(w, g) for g in got[leg]) for leg in want for w in want[leg])
            low = min(c[1] for cs in got.values() for c in cs) + 3.0
            worst = max(worst, gap)
            print(f"{name:15s} worst corner gap {gap:.5f} studs; lowest corner {low:+.4f} above the floor")
        print(f"worst gap, pose.soles() to Roblox: {worst:.5f} studs")
    finally:
        _stop()
    return worst


def _encode(name: str) -> str:
    src, dst = os.path.join(OUT, name, "f%05d.png"), os.path.join(OUT, name + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", src, "-vf",
                    "scale=1080:1920:flags=lanczos,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
                    dst], check=True)
    return dst


def takes(only: list[str] | None = None) -> None:
    try:
        _start()
        print(stage.actors(CAST))
        print(capture.install().strip()[-40:])
        print(capture.preload([faces.url(n) for n in ("smile", "shock", "angry")]))
        for name, shot, secs in (("acting", acting, 2.4), ("walk", walking, 1.5), ("feet", feet, 1.0)):
            if only and name not in only:
                continue
            t0 = time.time()
            capture.take(os.path.join(OUT, name), shot, seconds=secs, fps=FPS, warmup=4.0, portrait=True)
            print(f"{name}: {time.time() - t0:.0f} s")
    finally:
        _stop()
    parts = [_encode(n) for n in ("acting", "walk", "feet")]
    preview = os.path.join(OUT, "s3_preview.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *sum((["-i", p] for p in parts), []), "-filter_complex",
                    "".join(f"[{i}:v]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=1:a=0[v]",
                    "-map", "[v]", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", preview],
                   check=True)
    print("preview:", preview)


def _grey(video: str, width: int = 180) -> np.ndarray:
    h = width * 16 // 9
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"scale={width}:{h}", "-pix_fmt", "gray",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, width).astype(np.float32)


def measure() -> None:
    """Motion (mean difference between frames, grey levels at 180 px wide) around each key of the acting take, and
    how far the walker's hair moves about the frame (the camera tracks her at her own speed: it should stay put)."""
    f = _grey(os.path.join(OUT, "acting.mp4"))
    motion = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))
    print(f"acting: first 12 frames {' '.join(f'{m:.2f}' for m in motion[:12])}")
    for tk, name in KEYS[1:]:
        k = int(round(tk * FPS))
        print(f"  {name:14s} key at frame {k}: frames {k}-{k + 7}: {' '.join(f'{m:.1f}' for m in motion[k - 1:k + 7])}")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(OUT, "walk.mp4"), "-vf", "scale=540:960",
                          "-pix_fmt", "rgb24", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    rgb = np.frombuffer(raw, np.uint8).reshape(-1, 960, 540, 3).astype(np.int16)
    hair = (rgb[..., 0] > 170) & (rgb[..., 1] > 130) & (rgb[..., 2] < 110) & (rgb[..., 0] - rgb[..., 2] > 90)
    edges = np.array([(np.nonzero(m)[1].min() * 2, np.nonzero(m)[1].max() * 2, np.nonzero(m)[0].min() * 2)
                      if m.any() else (np.nan,) * 3 for m in hair])  # px at 1080 wide: left, right, top
    for name, col in (("left edge", 0), ("right edge", 1), ("top", 2)):
        v = edges[:, col]
        print(f"walk: hair {name} {np.nanmin(v):.0f}-{np.nanmax(v):.0f} px (range {np.nanmax(v) - np.nanmin(v):.0f}), "
              f"biggest jump between frames {np.nanmax(np.abs(np.diff(v))):.0f} px")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else ""
    if what == "check":
        check()
    elif what == "takes":
        takes(sys.argv[2:])
    elif what == "measure":
        measure()
    else:
        print(__doc__)
