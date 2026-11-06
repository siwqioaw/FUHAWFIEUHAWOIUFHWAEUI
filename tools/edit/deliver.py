"""Encode a delivery file from the master (render.py) and the mastered mix (master.py), then check it with
tools/verify/qc.py (the encoder changes true peak and can change frames: measure the file you upload).

    python tools/edit/deliver.py MASTER.mov MIX.wav OUT.mp4 [--size shorts|landscape|square|WxH] [--fit-mb N]

The encode: H.264 High, CRF 17, 4:2:0, a closed GOP of half a second (frame-exact review, and clean cuts for the
platform's own re-encode), BT.709 tags, AAC 320 kb/s at 48 kHz, the index at the front (+faststart). With --fit-mb, two
passes to a bitrate that fits the size (for a chat app's upload limit) with AAC at 128 kb/s.

Platforms re-encode whatever they get: give them a clean, high-bitrate file at their native size (1080 x 1920 for a
vertical short) and the right frame rate, and check their current specs, which change.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

COLOR = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"]
SIZES = {"shorts": (1080, 1920), "landscape": (1920, 1080), "square": (1080, 1080)}


def _run(args: list[str]):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def _probe(path: str, entry: str) -> str:
    return subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", entry, "-of",
                           "csv=p=0", path], capture_output=True, text=True, check=True).stdout.strip()


def _fps(path: str) -> float:
    num, _, den = _probe(path, "stream=r_frame_rate").partition("/")
    return float(num) / float(den or 1)


def _scale(master: str, size: tuple[int, int] | None) -> list[str]:
    if not size:
        return []
    w, h = (int(v) for v in _probe(master, "stream=width,height").split(","))
    return [] if (w, h) == size else ["-vf", f"scale={size[0]}:{size[1]}:flags=lanczos"]


def encode(master: str, mix: str, dest: str, size: tuple[int, int] | None = None, crf: int = 17) -> str:
    gop = max(1, round(_fps(master) / 2))
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    _run(["-i", master, "-i", mix, "-map", "0:v", "-map", "1:a", *_scale(master, size),
          "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-profile:v", "high", "-pix_fmt", "yuv420p",
          "-g", str(gop), "-bf", "2", "-x264-params", "open-gop=0", *COLOR,
          "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-shortest", "-movflags", "+faststart", dest])
    return dest


def fit(master: str, mix: str, dest: str, limit_mb: float, size: tuple[int, int] | None = None) -> str:
    """Two passes to a bitrate that fits `limit_mb` (3% margin), audio at 128 kb/s. 128 kb/s AAC adds a few tenths of
    a dB of true peak: the audio goes in 0.4 dB lower."""
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                master], capture_output=True, text=True, check=True).stdout.strip())
    kbps = int((limit_mb * 8 * 1000 * 0.97) / dur - 128)
    log = os.path.splitext(dest)[0] + "_pass"
    common = [*_scale(master, size), "-c:v", "libx264", "-preset", "slow", "-b:v", f"{kbps}k",
              "-maxrate", f"{int(kbps * 1.6)}k", "-bufsize", f"{kbps * 3}k", "-profile:v", "high",
              "-pix_fmt", "yuv420p", "-g", str(max(1, round(_fps(master) * 2))), *COLOR, "-passlogfile", log]
    _run(["-i", master, *common, "-pass", "1", "-an", "-f", "mp4", os.devnull])
    _run(["-i", master, "-i", mix, "-map", "0:v", "-map", "1:a", *common, "-pass", "2", "-af", "volume=-0.4dB",
          "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-shortest", "-movflags", "+faststart", dest])
    folder = os.path.dirname(os.path.abspath(dest))
    for f in os.listdir(folder):
        if f.startswith(os.path.basename(log)):
            os.remove(os.path.join(folder, f))
    return dest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("master")
    ap.add_argument("mix")
    ap.add_argument("out")
    ap.add_argument("--size", help="shorts, landscape, square or WxH (default: the master's own size)")
    ap.add_argument("--fit-mb", type=float, help="two-pass to fit this many megabytes")
    args = ap.parse_args()
    size = None
    if args.size:
        size = SIZES.get(args.size) or tuple(int(v) for v in args.size.lower().split("x"))
    dest = fit(args.master, args.mix, args.out, args.fit_mb, size) if args.fit_mb else \
        encode(args.master, args.mix, args.out, size)
    print(f"{dest}: {os.path.getsize(dest) / 1e6:.1f} MB")
    print(f"next: python tools/verify/qc.py {dest} --timeline <cut.json>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
