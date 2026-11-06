"""Render a cut to a ProRes 422 HQ master, its frames rendered in parallel (docs/PIPELINE.md, "Render").

    from render import master, stills

    def frame_at(r: int) -> np.ndarray:      # float32 RGB, H x W x 3, 0..1
        ...

    if __name__ == "__main__":               # required: worker processes import this module
        master(frame_at, n_frames, 1080, 1920, 30, "build/master.mov")
        stills(frame_at, [0, 45, 90], "build/stills")   # a few frames to look at before the full render

`frame_at` must be a module-level function and a pure function of the frame number (and of files it reads): the
workers render frames out of order. Any state carried from one frame to the next breaks it. The master is 10-bit
4:2:2 from 16-bit RGB, so the delivery encode starts from more than it keeps.

The trailer this comes from: 1,600 frames at 1920 x 1080 took 12 to 20 minutes with 12 processes.
"""

from __future__ import annotations

import functools
import multiprocessing as mp
import os
import subprocess
from typing import Callable

import cv2
import numpy as np

COLOR = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"]


def _bytes(frame_at: Callable[[int], np.ndarray], w: int, h: int, r: int) -> bytes:
    f = frame_at(r)
    if f.shape[:2] != (h, w):
        raise ValueError(f"frame {r} is {f.shape[1]}x{f.shape[0]}, not {w}x{h}")
    return (np.clip(f, 0, 1) * 65535.0 + 0.5).astype("<u2").tobytes()


def master(frame_at: Callable[[int], np.ndarray], n: int, w: int, h: int, fps: float, dest: str,
           workers: int | None = None, log=print) -> str:
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb48le",
           "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
           "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", *COLOR, dest]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    job = functools.partial(_bytes, frame_at, w, h)
    try:
        with mp.Pool(workers or min(12, os.cpu_count() or 4)) as pool:
            for k, buf in enumerate(pool.imap(job, range(n), chunksize=2)):
                p.stdin.write(buf)
                if k % 120 == 0:
                    log(f"  frame {k}/{n}")
    finally:
        p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg failed writing the master")
    return dest


def _save(frame_at: Callable[[int], np.ndarray], out_dir: str, r: int) -> str:
    f = frame_at(r)
    path = os.path.join(out_dir, f"r{r:05d}.png")
    cv2.imwrite(path, cv2.cvtColor((np.clip(f, 0, 1) * 255 + 0.5).astype(np.uint8), cv2.COLOR_RGB2BGR))
    return path


def stills(frame_at: Callable[[int], np.ndarray], frames: list[int], out_dir: str,
           workers: int | None = None) -> list[str]:
    """Chosen frames as PNGs, to look at before rendering the whole cut."""
    os.makedirs(out_dir, exist_ok=True)
    with mp.Pool(workers or min(12, os.cpu_count() or 4)) as pool:
        return pool.map(functools.partial(_save, frame_at, out_dir), frames, chunksize=1)
