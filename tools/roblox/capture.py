"""Capture a shot frame by frame from a playtest's client, through the harness (harness.luau; docs/ROBLOX_CAPTURE.md).

A shot is a function of time t (seconds into the shot) that returns that frame's state, as harness.luau's header
describes it. take() applies it a frame at a time, waits until the client has drawn it, and saves the viewport. What
the harness holds stays still between frames, so each frame is exactly 1/fps after the one before however long it
took to capture (about a second each). Anything it doesn't hold (the game's own NPCs, tweens, physics) moves in real
time between frames: hold it, drive it from the frame state, or keep it out of shot.

    import capture
    capture.install()                                    # once per playtest
    def shot(t):
        return {"cam": {"pos": [0, 8, 20 - 2 * t], "look": [0, 5, 0]}, "fov": 60,
                "actors": [{"name": "kid", "cf": {"pos": [0, 3, 0], "look": [0, 3, 10]}, "anims": [["walk", t, 1]]}]}
    capture.take("build/shots/intro", shot, seconds=3.0, fps=30)
    capture.release()                                    # the game's camera and HUD back

    python tools/roblox/capture.py smoke [OUT_DIR] [--portrait]   # install, then one frame of the view as it is

Portrait (docs/ROBLOX_CAPTURE.md, "Resolution"): a vertical short needs a tall picture from a wide viewport, so with
portrait=True every frame's camera is rolled 90 degrees and each saved frame is turned upright and cropped to 9:16.
The shot still describes an ordinary upright camera: its fov is the vertical field of view of the finished 9:16
frame. The frame's width is the viewport's height and its height the viewport's width, so widen Studio's viewport
(hide the panels, collapse the ribbon) for the pixels.
"""

from __future__ import annotations

import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import studio  # noqa: E402

FPS = 30
PORTRAIT = (9, 16)
_fid = 0
_H = "game:GetService('Players').LocalPlayer.PlayerGui:FindFirstChild('_CaptureHarness')"


def viewport() -> tuple[int, int]:
    """The playtest client's viewport in pixels (width, height): what screen_capture returns."""
    out = studio.luau("local v = workspace.CurrentCamera.ViewportSize return v.X .. ',' .. v.Y", dm="Client")
    w, h = (int(round(float(x))) for x in out.strip().split(","))
    return w, h


def rolled(cam, degrees: float):
    """A harness camera ({pos, look, roll} or 12 CFrame components) rolled `degrees` more about its own look axis,
    as the harness applies roll: the CFrame times CFrame.Angles(0, 0, roll)."""
    if isinstance(cam, dict):
        return dict(cam, roll=cam.get("roll", 0) + degrees)
    x, y, z, r00, r01, r02, r10, r11, r12, r20, r21, r22 = cam
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return [x, y, z, r00 * c + r01 * s, r01 * c - r00 * s, r02, r10 * c + r11 * s, r11 * c - r10 * s, r12,
            r20 * c + r21 * s, r21 * c - r20 * s, r22]


def portrait_fov(vfov: float, view: tuple[int, int], aspect: tuple[int, int] = PORTRAIT) -> float:
    """The camera's FieldOfView, rolled 90 degrees in a (width, height) viewport, that gives the upright frame cropped
    to `aspect` a vertical field of view of `vfov`. Rolled, the viewport's height spans the frame's width."""
    w, h = view
    crop_h = min(w, h * aspect[1] / aspect[0])
    return math.degrees(2 * math.atan(math.tan(math.radians(vfov) / 2) * h / crop_h))


def upright(path: str, aspect: tuple[int, int] = PORTRAIT) -> tuple[int, int]:
    """Turn a capture taken with the camera rolled +90 degrees upright (the picture turns 90 degrees anticlockwise),
    crop it to `aspect` about its centre, and save it in place at its own pixels. Returns the new size.
    Measured on 2026-11-07: in a playtest, roll +90 needs the anticlockwise turn; Studio's edit-mode camera applies
    the roll the other way, so don't shoot in edit mode."""
    from PIL import Image

    im = Image.open(path)
    im.load()
    im = im.transpose(Image.Transpose.ROTATE_90)
    w, h = im.size
    if w * aspect[1] > h * aspect[0]:
        nw = int(round(h * aspect[0] / aspect[1]))
        x0 = (w - nw) // 2
        im = im.crop((x0, 0, x0 + nw, h))
    else:
        nh = int(round(w * aspect[1] / aspect[0]))
        y0 = (h - nh) // 2
        im = im.crop((0, y0, w, y0 + nh))
    im.save(path, compress_level=1)  # light compression: the default costs about 0.3 s a frame
    return im.size


def install() -> str:
    out = studio.luau(studio.read("harness.luau"), dm="Client")
    if "harness true" not in out:
        raise RuntimeError(f"harness not ready: {out}")
    return out


def frame(state: dict, settle_frames: int = 3, timeout: float = 20) -> None:
    """Apply one frame's state and wait until the client has drawn it `settle_frames` times."""
    global _fid
    _fid += 1
    payload = json.dumps(dict(state, id=_fid), ensure_ascii=False, separators=(",", ":"))
    code = (
        f"local h = {_H}\n"
        "if not h then return 'no harness|' end\n"
        "h:SetAttribute('Applied', 0)\n"
        f"h:SetAttribute('Frame', {json.dumps(payload, ensure_ascii=False)})\n"
        "local t0 = os.clock()\n"
        f"while h:GetAttribute('Applied') ~= {_fid} and h:GetAttribute('Applied') ~= -1 and os.clock() - t0 < {timeout}"
        " do task.wait() end\n"
        f"for _ = 1, {settle_frames} do game:GetService('RunService').RenderStepped:Wait() end\n"
        "return tostring(h:GetAttribute('Applied')) .. '|' .. tostring(h:GetAttribute('Err'))"
    )
    out = studio.luau(code, dm="Client")
    applied, _, err = out.partition("|")
    if applied.strip() != str(_fid):
        raise RuntimeError(f"frame {_fid} not applied: {out}")


def preload(urls: list[str], timeout: float = 60) -> str:
    """Load textures on the client before a take (faces above all), so a swap never shows a frame of blank texture."""
    code = ("local list = game:GetService('HttpService'):JSONDecode(" + json.dumps(json.dumps(list(urls))) + ")\n"
            "local t0 = os.clock()\n"
            "game:GetService('ContentProvider'):PreloadAsync(list)\n"
            "return string.format('preloaded %d in %.2f s', #list, os.clock() - t0)")
    return studio.luau(code, dm="Client", timeout=timeout)


def release() -> str:
    """The game's camera, HUD, lights and particles back, and Studio's rendering quality as install() found it."""
    code = (f"local h = {_H}\n"
            "if not h then return 'no harness' end\n"
            "h:SetAttribute('Release', true)\n"
            "local was = h:GetAttribute('WasQuality')\n"
            "if was then settings().Rendering.QualityLevel = Enum.QualityLevel[was] end\n"
            "return 'released, quality ' .. tostring(settings().Rendering.QualityLevel)")
    return studio.luau(code, dm="Client")


def settle(out_dir: str, quiet: float = 15.0, timeout: float = 120.0, log=print) -> float:
    """Capture the held first frame about once a second until no pixel has changed by more than 8 grey levels for
    `quiet` seconds. At Studio's Automatic quality level a new scene keeps refining for up to about 45 s, in steps 2 to
    11 s apart with only small changes between them, so two captures that nearly agree don't mean it's done (spike S3:
    the steps landed in a take's first 10 frames as pops). The harness now fixes the level at the highest (install()),
    which stops the steps, and this stays as the check: it then ends after its `quiet` seconds. Returns the seconds it
    took."""
    from PIL import Image, ImageChops

    path = os.path.join(out_dir, "_settle.png")
    t0 = last = time.time()
    prev = None
    while True:
        studio.capture(path)
        with Image.open(path) as im:
            cur = im.convert("L")
        if prev is not None and ImageChops.difference(cur, prev).point(lambda v: 255 if v > 8 else 0).getbbox():
            last = time.time()
        prev = cur
        now = time.time()
        if now - last >= quiet:
            break
        if now - t0 > timeout:
            log(f"  still changing after {timeout:.0f} s: capturing anyway")
            break
        time.sleep(0.5)
    os.remove(path)
    return time.time() - t0


def take(out_dir: str, shot, seconds: float, fps: float = FPS, start: int = 0, warmup: float = 4.0, blur: int = 1,
         shutter: float = 0.5, speed: float = 1.0, only: list[int] | None = None, portrait: bool = False,
         log=print) -> int:
    """Capture shot(t) for `seconds` at `fps` into out_dir/f00000.png, f00001.png...

    blur > 1: each frame is `blur` sub-frames spread over the shutter (a fraction of the frame: 0.5 is a film
    camera's 180 degrees), saved as f00000_0.png...; look.load_avg averages them in linear light. At a cut or a camera
    jump inside a shot, use only the last sub-frame.
    speed < 1: slow motion (t advances `speed` seconds per second of output). Everything posed from t slows with it.
    warmup: real seconds to wait on the first frame (animations and textures load, lights settle), which is then
    applied again and captured until the picture stops changing (settle()). only: just these frame numbers (to redo
    a bad frame).
    portrait: roll the camera 90 degrees and save each frame upright, cropped to 9:16 (the module's docstring)."""
    os.makedirs(out_dir, exist_ok=True)
    n = int(round(seconds * fps))
    frames = list(only) if only is not None else list(range(start, n))
    view = viewport() if portrait else None
    if view:
        fw = int(round(min(view[1], view[0] * PORTRAIT[0] / PORTRAIT[1])))
        fh = int(round(min(view[0], view[1] * PORTRAIT[1] / PORTRAIT[0])))
        scale = 1080 / fw
        log(f"  portrait from a {view[0]}x{view[1]} viewport: {fw}x{fh} frames"
            + ("" if scale <= 1 else f", scaled {scale:.3f}x to 1080 wide")
            + ("" if scale <= 1.2 else ": soft, use the capture layout (docs/ROBLOX_CAPTURE.md, \"Resolution\")"))
    first = True
    t_start = time.time()
    for k, f in enumerate(frames):
        subs = [0.0] if blur <= 1 else [(-0.5 + (j + 0.5) / blur) * shutter for j in range(blur)]
        for j, off in enumerate(subs):
            t = (f + off) / fps * speed
            state = dict(shot(t), t=t)
            if view:
                state["cam"] = rolled(state["cam"], 90)
                state["fov"] = portrait_fov(state.get("fov", 70), view)
            if first:
                frame(dict(state, freeze=True))
                time.sleep(warmup)
                frame(state)
                log(f"  settled in {settle(out_dir, log=log):.1f} s")
                first = False
            frame(state)
            name = f"f{f:05d}.png" if blur <= 1 else f"f{f:05d}_{j}.png"
            path = studio.capture(os.path.join(out_dir, name))
            if view:
                upright(path)
        if k % 12 == 0:
            log(f"  {os.path.basename(out_dir)}: frame {f} ({k + 1}/{len(frames)}, "
                f"{(time.time() - t_start) / (k + 1):.2f} s a frame)")
    return len(frames)


def smoke(out_dir: str, portrait: bool = False) -> str:
    """Install the harness and capture the view as it is, with the HUD hidden: look at it before a real take. With
    portrait, the same view rolled, turned upright and cropped as take(portrait=True) saves it."""
    install()
    cf = studio.luau("local c = workspace.CurrentCamera.CFrame return table.concat({c:GetComponents()}, ',')",
                     dm="Client")
    cam = [float(v) for v in cf.strip().split(",")]
    fov = 70.0
    if portrait:
        view = viewport()
        cam, fov = rolled(cam, 90), portrait_fov(70.0, view)
    frame({"cam": cam, "fov": fov, "freeze": True})
    time.sleep(1.0)
    frame({"cam": cam, "fov": fov})
    path = studio.capture(os.path.join(out_dir, "smoke_portrait.png" if portrait else "smoke.png"))
    if portrait:
        upright(path)
    return path


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "smoke":
        args = [a for a in sys.argv[2:] if a != "--portrait"]
        print(smoke(args[0] if args else os.path.join("build", "capture"), portrait="--portrait" in sys.argv))
        print("look at it: no HUD, no cursor, no character, nothing at the edges; then capture.release()")
    else:
        print(__doc__)
