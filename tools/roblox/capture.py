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

    python tools/roblox/capture.py smoke [OUT_DIR]       # install, then one frame of the view as it is
"""

from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import studio  # noqa: E402

FPS = 30
_fid = 0
_H = "game:GetService('Players').LocalPlayer.PlayerGui:FindFirstChild('_CaptureHarness')"


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


def release() -> str:
    return studio.luau(f"local h = {_H} if h then h:SetAttribute('Release', true) end return 'released'", dm="Client")


def take(out_dir: str, shot, seconds: float, fps: float = FPS, start: int = 0, warmup: float = 4.0, blur: int = 1,
         shutter: float = 0.5, speed: float = 1.0, only: list[int] | None = None, log=print) -> int:
    """Capture shot(t) for `seconds` at `fps` into out_dir/f00000.png, f00001.png...

    blur > 1: each frame is `blur` sub-frames spread over the shutter (a fraction of the frame: 0.5 is a film
    camera's 180 degrees), saved as f00000_0.png...; look.load_avg averages them in linear light. At a cut or a camera
    jump inside a shot, use only the last sub-frame.
    speed < 1: slow motion (t advances `speed` seconds per second of output). Everything posed from t slows with it.
    warmup: real seconds to wait on the first frame (animations and textures load, lights settle), which is then
    applied again. only: just these frame numbers (to redo a bad frame)."""
    os.makedirs(out_dir, exist_ok=True)
    n = int(round(seconds * fps))
    frames = list(only) if only is not None else list(range(start, n))
    first = True
    t_start = time.time()
    for k, f in enumerate(frames):
        subs = [0.0] if blur <= 1 else [(-0.5 + (j + 0.5) / blur) * shutter for j in range(blur)]
        for j, off in enumerate(subs):
            t = (f + off) / fps * speed
            state = dict(shot(t), t=t)
            if first:
                frame(dict(state, freeze=True))
                time.sleep(warmup)
                first = False
            frame(state)
            name = f"f{f:05d}.png" if blur <= 1 else f"f{f:05d}_{j}.png"
            studio.capture(os.path.join(out_dir, name))
        if k % 12 == 0:
            log(f"  {os.path.basename(out_dir)}: frame {f} ({k + 1}/{len(frames)}, "
                f"{(time.time() - t_start) / (k + 1):.2f} s a frame)")
    return len(frames)


def smoke(out_dir: str) -> str:
    """Install the harness and capture the view as it is, with the HUD hidden: look at it before a real take."""
    install()
    cf = studio.luau("local c = workspace.CurrentCamera.CFrame return table.concat({c:GetComponents()}, ',')",
                     dm="Client")
    cam = [float(v) for v in cf.strip().split(",")]
    frame({"cam": cam, "fov": 70, "freeze": True})
    time.sleep(1.0)
    frame({"cam": cam, "fov": 70})
    return studio.capture(os.path.join(out_dir, "smoke.png"))


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "smoke":
        print(smoke(sys.argv[2] if len(sys.argv) > 2 else os.path.join("build", "capture")))
        print("look at it: no HUD, no cursor, no character, nothing at the edges; then capture.release()")
    else:
        print(__doc__)
