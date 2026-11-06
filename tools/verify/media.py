"""Reading the delivered file: probe it, pull its audio, decode frames. Everything here works on the encoded video,
because that's what the audience gets: an AAC encode changes the true peak, and a re-encode changes frames.
ffmpeg and ffprobe must be on PATH."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile

import numpy as np
import soundfile as sf


def probe(video: str) -> dict:
    p = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", video],
                       capture_output=True, text=True, check=True)
    return json.loads(p.stdout)


def video_stream(info: dict) -> dict:
    return next(s for s in info["streams"] if s["codec_type"] == "video")


def fps_of(info: dict) -> float:
    num, den = video_stream(info)["r_frame_rate"].split("/")
    return float(num) / float(den)


def audio(path: str, sr: int = 48000) -> tuple[np.ndarray, int]:
    """The audio of a WAV, or of a video's first audio stream decoded to float, as (samples x channels, rate)."""
    if path.lower().endswith((".wav", ".flac")):
        x, rate = sf.read(path, always_2d=True)
        return x, rate
    fd, tmp = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", path, "-vn", "-ac", "2", "-ar",
                        str(sr), "-c:a", "pcm_f32le", tmp], check=True)
        x, rate = sf.read(tmp, always_2d=True)
    finally:
        os.remove(tmp)
    return x, rate


def frames_small(video: str, width: int = 180) -> np.ndarray:
    """Every frame decoded small (keeping the aspect), as float RGB 0..1: N x H x W x 3. All of it in memory: at
    180 px wide that's 0.7 MB a frame, so a 2.5-minute short at 60 fps would need 6.5 GB. For anything long, use
    `frames_small_chunks`."""
    return np.concatenate(list(frames_small_chunks(video, width)))


def frames_small_chunks(video: str, width: int = 180, chunk: int = 300):
    """The same frames as `frames_small`, in order, as arrays of up to `chunk` frames each, so memory stays flat
    however long the video is."""
    info = probe(video)
    v = video_stream(info)
    w = width
    h = max(2, int(round(width * int(v["height"]) / int(v["width"]) / 2)) * 2)
    size = w * h * 3
    p = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", video, "-vf", f"scale={w}:{h}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    try:
        while True:
            buf = p.stdout.read(size * chunk)  # blocks until a full chunk, or the end of the video
            n = len(buf) // size
            if n == 0:
                break
            yield np.frombuffer(buf[:n * size], dtype=np.uint8).reshape(n, h, w, 3).astype(np.float32) / 255.0
    finally:
        p.stdout.close()
        if p.wait() != 0:
            raise subprocess.CalledProcessError(p.returncode, "ffmpeg")


def extract_frames(video: str, frames: list[int], out_dir: str, width: int | None = None) -> dict[int, str]:
    """Save the given frame numbers (0-based, as decoded) as PNGs: {frame: path}. Full size unless `width`."""
    os.makedirs(out_dir, exist_ok=True)
    wanted = sorted(set(f for f in frames if f >= 0))
    out: dict[int, str] = {}
    # In batches: ffmpeg's select expression gets long.
    for i in range(0, len(wanted), 60):
        batch = wanted[i:i + 60]
        expr = "+".join(f"eq(n\\,{f})" for f in batch)
        vf = f"select='{expr}'" + (f",scale={width}:-2" if width else "")
        tmpl = os.path.join(out_dir, f"_b{i}_%04d.png")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", video, "-vf", vf, "-vsync", "0",
                        tmpl], check=True)
        for j, f in enumerate(batch):
            src = tmpl % (j + 1)
            if os.path.exists(src):
                dest = os.path.join(out_dir, f"f{f:05d}.png")
                os.replace(src, dest)
                out[f] = dest
    return out


def loudness(path: str) -> dict:
    """Integrated loudness (LUFS), loudness range (LU) and true peak (dBTP) of a file's audio, by ffmpeg's EBU R128
    meter. Run it on the encoded file: the true peak there is the one that counts."""
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true",
                        "-f", "null", "-"],
                       capture_output=True, text=True)
    out = p.stderr
    s = out[out.rfind("Summary:"):]

    def grab(label: str) -> float:
        for line in s.splitlines():
            if line.strip().startswith(label):
                return float(line.split(":")[1].split()[0])
        return float("nan")
    return {"I": grab("I:"), "LRA": grab("LRA:"), "TP": grab("Peak:")}
