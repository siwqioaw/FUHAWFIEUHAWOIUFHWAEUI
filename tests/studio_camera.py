"""Spike S4 in Roblox Studio: the camera moves the references use, shot as takes, and their measurements
(docs/ROBLOX_CAPTURE.md, "Camera").

Needs what tests/studio_pose.py needs: Studio open on a Baseplate place in the capture layout, the bridge running
(`python tools/roblox/studio_mcp.py serve`) and the test faces installed (`python tools/roblox/faces.py test`).
Everything it makes lives in a playtest, which it stops at the end.

    python tests/studio_camera.py takes [push pull swoop dutch low ots top]   # takes at 60 fps into build/s4/
    python tests/studio_camera.py post [swoop]                                  # no Studio: the swoop's smear, encodes
    python tests/studio_camera.py measure                                       # no Studio: profiles, angles, framing
"""

from __future__ import annotations

import math
import os
import subprocess
import sys
import time

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "roblox"))
sys.path.insert(0, os.path.join(ROOT, "tools", "edit"))
sys.path.insert(0, os.path.join(ROOT, "tests"))

import camera  # noqa: E402
import capture  # noqa: E402
import faces  # noqa: E402
import pose  # noqa: E402
import stage  # noqa: E402
import studio  # noqa: E402
from studio_pose import CAST, OFF  # noqa: E402

OUT = os.path.join(ROOT, "build", "s4")
FPS = 60
SIZE = (960, 1707)  # the upright frame capture.take saves
KID, KID_HEAD, KID_FACE = (0.0, 3.0, 0.0), (0.0, 4.5, 0.0), (0.0, 4.5, 0.6)  # torso centre; head centre; face
FACING = {"pos": [0.0, 3.0, 7.0], "look": [0.0, 3.0, -10.0]}  # the girl facing the kid, for over the shoulder
BESIDE = {"pos": [5.0, 3.0, 0.0], "look": [5.0, 3.0, 10.0]}  # the girl beside him, both facing the camera
GIRL_HEAD_FACING, GIRL_HEAD_BESIDE = (0.0, 4.5, 7.0), (5.0, 4.5, 0.0)
CAPTIONS = 0.70  # a face lower than this, as a fraction of the frame's height, sits where captions go
DESK = """
local desk = Instance.new('Part')
desk.Name = '_S4Desk'
desk.Anchored = true
desk.Size = Vector3.new(4, 2.2, 1.6)
desk.Position = Vector3.new(0, 1.1, 1.6)
desk.Color = Color3.fromRGB(150, 105, 70)
desk.Material = Enum.Material.Wood
desk.Parent = workspace
out('desk')"""

MOVES = {  # name: (seconds, the move's start and length in seconds, what it is)
    "push": (1.0, 0.10, 0.25, "a shot's opening push-in, easing out"),
    "pull": (1.0, 0.10, 0.20, "an extreme close-up's fast pull-back, easing out (as 007 at 3.73)"),
    "swoop": (0.8, 0.20, 0.15, "a 0.15 s swoop from speaker to listener, smeared in the edit"),
    "dutch": (1.0, 0.10, 0.35, "a swoop in that rolls to a dutch angle (as 002 at 0.2-0.6)"),
    "low": (0.8, 0.10, 0.30, "a low angle from just above the desk, pushing in"),
    "ots": (0.8, 0.10, 0.25, "over the shoulder with depth of field, pushing in"),
    "top": (0.8, 0.10, 0.30, "top-down, pushing in"),
}


def _actors(t: float, kid_face="smile", girl_face="smile", girl=None) -> list:
    """The kid behind his desk, and the girl where `girl` puts her (FACING, BESIDE, or None: out of shot)."""
    kj, kr = pose.at([(0.0, "idle")], t, seed=1)
    out = [{"name": "kid", "cf": {"pos": list(KID), "look": [0, 3, 10]}, "face": faces.url(kid_face),
            "joints": kj, "rootpos": kr}]
    if girl:
        gj, gr = pose.at([(0.0, "idle")], t, seed=2)
        out.append({"name": "girl", "cf": girl, "face": faces.url(girl_face), "joints": gj, "rootpos": gr})
    else:
        out.append({"name": "girl", "cf": OFF})
    return out


def _end_view(name: str) -> dict:
    """Each take's framing when its move ends."""
    if name == "push":
        return camera.aim(KID_HEAD, toward=(0, 0, 1), distance=5.5, height=-0.2, fov=45)
    if name == "pull":
        return camera.view((0.0, 4.4, 9.0), (0.0, 3.6, 0.0), fov=45)
    if name == "dutch":
        return camera.dutch(camera.aim(KID_HEAD, toward=(0.3, 0, 1), distance=5.0, fov=45), 14)
    if name == "low":
        return camera.low((0.0, 3.6, 0.0), toward=(0, 0, 1), distance=5.0, eye=2.5, fov=55)
    if name == "ots":
        return camera.ots((0.0, 4.2, 7.0), KID_FACE, side=1.5, behind=2.8, up=0.4, fov=45, blur=0.6, lift=1.0)
    if name == "top":
        return camera.top((0.0, 3.0, 0.0), height=8.0, up=(0, 0, 1), fov=50)
    raise KeyError(name)


def _path(name: str):
    _, start, length, _ = MOVES[name]
    if name == "swoop":
        a = camera.aim(KID_HEAD, toward=(0, 0, 1), distance=5.0, height=-0.2, fov=45)
        b = camera.aim(GIRL_HEAD_BESIDE, toward=(0, 0, 1), distance=5.0, height=-0.2, fov=45)
        return camera.moves([(0.0, a), (start, b, length, "inout")])
    end = _end_view(name)
    if name == "pull":  # the extreme close-up keeps the face above the captions: eyes and mouth in the upper half
        first = camera.view((0.0, 4.5, 2.4), (0.0, 4.1, 0.0), fov=45)
        return camera.moves([(0.0, first), (start, end, length, "out")])
    if name == "dutch":
        first = camera.aim((0, 4.0, 0), toward=(0, 0, 1), distance=8.0, fov=50)
        return camera.moves([(0.0, first), (start, end, length, "inout")])
    return camera.moves([(0.0, camera.back(end, {"push": 4.0, "low": 1.5, "ots": 1.0, "top": 2.0}[name])),
                         (start, end, length, "out")])


def shot(name: str, dof: bool = True):
    path = _path(name)
    seed = list(MOVES).index(name)

    def at(t: float) -> dict:
        v = camera.hold(path(t), t, seed=seed)
        if not dof:
            v = dict(v, dof=None)
        s = camera.state(v)
        s["actors"] = _actors(t, kid_face="smile", girl_face="shock" if name == "swoop" else "smile",
                              girl={"swoop": BESIDE, "ots": FACING}.get(name))
        return s

    return at


def _encode(name: str) -> str:
    src, dst = os.path.join(OUT, name, "f%05d.png"), os.path.join(OUT, name.replace("_smeared", "") + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", src, "-vf",
                    "scale=1080:1920:flags=lanczos,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
                    dst], check=True)
    return dst


def _smear(name: str) -> str:
    """The swoop's motion blur, added as the edit will: each frame streaked sideways by how far the picture slides
    while a 180 degree shutter is open (camera.smear, fx.streak), into <name>_smeared/."""
    import fx
    import look

    src, dst = os.path.join(OUT, name), os.path.join(OUT, name + "_smeared")
    os.makedirs(dst, exist_ok=True)
    path = _path(name)
    for k in range(int(round(MOVES[name][0] * FPS))):
        img = look.load(os.path.join(src, f"f{k:05d}.png"))
        look.save(os.path.join(dst, f"f{k:05d}.png"), fx.streak(img, camera.smear(path, k / FPS)))
    return dst


def takes(only: list[str] | None = None) -> None:
    names = [n for n in MOVES if not only or n in only]
    try:
        print(studio.play(True))
        studio.wait_for("Client", timeout=90)
        print(stage.park((0, 3, -60)))
        print(stage.actors(CAST))
        print(studio.server(DESK))
        print(capture.install().strip()[-40:])
        print(capture.preload([faces.url(n) for n in ("smile", "shock", "angry")]))
        for name in names:
            secs = MOVES[name][0]
            t0 = time.time()
            capture.take(os.path.join(OUT, name), shot(name), seconds=secs, fps=FPS, warmup=4.0, portrait=True)
            if name == "ots":  # the last frame again without depth of field, to measure what it does
                capture.take(os.path.join(OUT, "ots_sharp"), shot(name, dof=False), seconds=secs, fps=FPS,
                             only=[int(secs * FPS) - 1], warmup=1.0, portrait=True)
            print(f"{name}: {time.time() - t0:.0f} s")
    finally:
        for step in (capture.release, stage.clear_actors, lambda: studio.play(False)):
            try:
                print(step())
            except Exception as e:  # noqa: BLE001
                print("cleanup step failed:", e)
        time.sleep(1)
        print(studio.state().splitlines()[0])
    post(names)


def post(names: list[str]) -> None:
    """Smear the swoop and encode every take named."""
    for name in names:
        if name == "swoop":
            _smear(name)
        print("encoded", _encode(name + "_smeared" if name == "swoop" else name))


def _grey(video: str, width: int = 180) -> np.ndarray:
    h = width * 16 // 9
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"scale={width}:{h}", "-pix_fmt", "gray",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, width).astype(np.float32)


def _horizon(path: str) -> tuple[float, int]:
    """The angle of the floor's far edge where it meets the sky, in columns where sky (bluer than red) runs straight
    down onto mid-grey floor: (degrees, + when it rises to the right; how many columns showed it). Grey highlights on
    a jacket can pass for floor, so look at the frame too."""
    rgb = np.asarray(Image.open(path).convert("RGB"), np.float32)
    sky = rgb[..., 2] > rgb[..., 0] + 12
    floor = (rgb.max(axis=2) - rgb.min(axis=2) < 18) & (rgb.mean(axis=2) > 70) & (rgb.mean(axis=2) < 170)
    h, w = sky.shape
    xs, ys = [], []
    for x in range(0, w, 4):
        y = int(np.argmax(~sky[:, x]))
        if y > 0 and floor[y:min(h, y + 12), x].all():
            xs.append(x)
            ys.append(y)
    if len(xs) < 8:
        return float("nan"), len(xs)
    return math.degrees(math.atan(-np.polyfit(xs, ys, 1)[0])), len(xs)


def _sharpness(path: str, centre, radius: float) -> float:
    """Variance of the Laplacian in a square of `radius` pixels about `centre` (clipped to the frame): higher is
    sharper."""
    g = np.asarray(Image.open(path).convert("L"), np.float32)
    h, w = g.shape
    x0, x1 = max(0, int(centre[0] - radius)), min(w, int(centre[0] + radius))
    y0, y1 = max(0, int(centre[1] - radius)), min(h, int(centre[1] + radius))
    a = g[y0:y1, x0:x1]
    lap = a[1:-1, 1:-1] * 4 - a[:-2, 1:-1] - a[2:, 1:-1] - a[1:-1, :-2] - a[1:-1, 2:]
    return float(lap.var())


def measure() -> None:
    for name, (secs, start, length, what) in MOVES.items():
        video = os.path.join(OUT, name + ".mp4")
        if not os.path.exists(video):
            continue
        m = np.abs(np.diff(_grey(video), axis=0)).mean(axis=(1, 2))
        a, b = int(round(start * FPS)), int(round((start + length) * FPS))
        move, after = m[a:b + 2], m[b + 2:]
        face = _end_view(name) if name != "swoop" else None
        where = ""
        if face is not None:
            p = camera.project(face, KID_FACE if name not in ("top",) else KID_HEAD, SIZE)
            where = f"; the kid's face ends {p[1] / SIZE[1]:.0%} down" + (" (under the captions)" if p[1] / SIZE[1] >
                                                                            CAPTIONS else "")
        print(f"{name} ({what}): frames {a}-{b}: {' '.join(f'{v:.1f}' for v in move)}; before it "
              f"{m[:a].max() if a else 0:.2f}, after it at most {after.max():.2f}{where}")
    pull = _path("pull")
    d = [math.dist(pull(k / FPS)["pos"], KID_FACE) for k in range(6, 20)]
    print("pull: the face's size frame to frame (by its distance), as a share of the frame before: "
          + " ".join(f"{a / b:.2f}" for a, b in zip(d, d[1:])))
    first = camera.view((0.0, 4.5, 2.4), (0.0, 4.1, 0.0), fov=45)
    mouth = camera.project(first, (0, 4.25, 0.6), SIZE)
    print(f"pull: in the extreme close-up the mouth sits {mouth[1] / SIZE[1]:.0%} down (captions from about "
          f"{CAPTIONS:.0%})")
    last = lambda n: os.path.join(OUT, n, f"f{int(MOVES[n][0] * FPS) - 1:05d}.png")  # noqa: E731
    if os.path.exists(last("dutch")):
        ang, n = _horizon(last("dutch"))
        print(f"dutch: the floor's edge at {ang:+.1f} degrees at the end (asked: 14; {n} columns)")
    v = _end_view("low")
    pitch = math.degrees(math.atan2(v["look"][1] - v["pos"][1], math.dist(v["look"][::2], v["pos"][::2])))
    desk = camera.project(v, (0.0, 2.2, 2.4), SIZE)
    print(f"low: the camera {v['pos'][1]:.1f} studs up, looking up {pitch:.1f} degrees; the desk's front edge "
          f"{desk[1] / SIZE[1]:.0%} down, the desk filling the frame below it")
    sharp = os.path.join(OUT, "ots_sharp", f"f{int(MOVES['ots'][0] * FPS) - 1:05d}.png")
    if os.path.exists(last("ots")) and os.path.exists(sharp):
        v = _end_view("ots")
        near = camera.project(v, GIRL_HEAD_FACING, SIZE)
        px_per_stud = (SIZE[0] / 2) / (math.tan(math.radians(v["fov"] / 2)) * SIZE[0] / SIZE[1])
        edge = near[0] + 0.75 * px_per_stud / math.dist(v["pos"], GIRL_HEAD_FACING)  # its edge, hair and all
        far = camera.project(v, KID_FACE, SIZE)
        for label, centre, r in (("the near head's edge", (edge - 30, near[1]), 40),
                                 ("the near shoulder", (SIZE[0] * 0.25, SIZE[1] * 0.85), 120),
                                 ("the far face", far, 50)):
            a, b = _sharpness(last("ots"), centre, r), _sharpness(sharp, centre, r)
            print(f"ots, {label} at ({centre[0]:.0f}, {centre[1]:.0f}): sharpness {a:.1f} with depth of field, "
                  f"{b:.1f} without ({100 * (1 - a / b):.0f}% softer)")
    for name, (secs, start, length, _) in MOVES.items():  # a strip of every move, for the eye
        video = os.path.join(OUT, name + ".mp4")
        if os.path.exists(video):
            subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "verify", "sheets.py"), "strip", video,
                            "--from", f"{max(0.0, start - 2 / FPS):.3f}", "--to", f"{start + length + 4 / FPS:.3f}",
                            "--step", "2", "--out", os.path.join(OUT, "strips"), "--name", name + ".jpg"],
                           check=True, capture_output=True)
    print("strips of every move in", os.path.join(OUT, "strips"))


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else ""
    if what == "takes":
        takes(sys.argv[2:])
    elif what == "post":
        post(sys.argv[2:] or list(MOVES))
    elif what == "measure":
        measure()
    else:
        print(__doc__)
