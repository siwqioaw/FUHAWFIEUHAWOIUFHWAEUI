"""How fast captions change, measured from the picture: each caption's time on screen and the characters the voice
says while it's up. Run on the references, it sets what the read-time check asks of a spoken caption; run on our
file, it shows ours keeps their pace.

    python tools/verify/caption_pace.py VIDEO --words TRANSCRIPT.json --band 0.15 0.36
    python tools/verify/caption_pace.py refs/r6rants/videos/006*.mp4 --words refs/r6rants/transcripts --band 0.15 0.36

A caption is found as text: white fill (over 225) within 3 px of black outline (under 40), in a band of the frame
(story captions sit 22-29% down, comedy about 78%). A new caption is a frame where that mask changes by more than
half (its overlap with the last frame's under 0.5). The words a caption shows are the transcript's words starting
while it's up; its pace is their characters over its time on screen.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys

import numpy as np

W, H = 540, 960


def frames(path: str, band: tuple[float, float]):
    """The video's luma in a band of rows, frame by frame, at 540 x 960, with the frame rate."""
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=avg_frame_rate", "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    num, den = probe.stdout.strip().split("/")
    fps = float(num) / float(den)
    y0, y1 = int(band[0] * H), int(band[1] * H)
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    size = W * H
    out = []
    while True:
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        out.append(np.frombuffer(buf, np.uint8).reshape(H, W)[y0:y1])
    proc.wait()
    return out, fps


def text_mask(y: np.ndarray) -> np.ndarray:
    """White fill beside black outline: caption text, not a white wall."""
    white = y > 225
    black = y < 40
    near = np.zeros_like(black)
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            near |= np.roll(np.roll(black, dy, 0), dx, 1)
    return white & near


def changes(masks: list, least: int = 150) -> list[tuple[int, bool]]:
    """Frames where the caption changes: (frame, a caption is up after it)."""
    out = []
    prev = None
    for i, m in enumerate(masks):
        up = int(m.sum()) >= least
        if prev is None:
            if up:
                out.append((i, True))
        else:
            p_up = int(prev.sum()) >= least
            if up != p_up:
                out.append((i, up))
            elif up:
                inter = int((m & prev).sum())
                union = int((m | prev).sum())
                if union and inter / union < 0.5:
                    out.append((i, True))
        prev = m
    return out


def words_of(transcript: str) -> list[tuple[str, float, float]]:
    d = json.load(open(transcript, encoding="utf-8"))
    return [(w["word"].strip(), w["start"], w["end"]) for s in d.get("segments", []) for w in s.get("words", [])]


def pace(video: str, transcript: str, band: tuple[float, float]) -> list[dict]:
    """Each caption: when it's up, its time on screen, the words said while it's up, characters a second."""
    raw, fps = frames(video, band)
    masks = [text_mask(f) for f in raw]
    ch = changes(masks)
    words = words_of(transcript)
    caps = []
    for k, (f, up) in enumerate(ch):
        if not up:
            continue
        end = ch[k + 1][0] if k + 1 < len(ch) else len(masks)
        t0, t1 = f / fps, end / fps
        said = [w for w, s, _ in words if t0 - 0.05 <= s < t1 - 0.05]
        text = " ".join(said)
        caps.append({"start": round(t0, 3), "seconds": round(t1 - t0, 3), "words": len(said), "text": text,
                     "cps": round(len(text) / (t1 - t0), 1) if said and t1 > t0 else None})
    return caps


def summary(caps: list[dict]) -> dict:
    spoken = [c for c in caps if c["words"]]
    secs = np.array([c["seconds"] for c in spoken]) if spoken else np.zeros(1)
    cps = np.array([c["cps"] for c in spoken]) if spoken else np.zeros(1)
    return {"captions": len(spoken), "seconds_median": float(np.median(secs)), "seconds_p10": float(np.percentile(secs, 10)),
            "seconds_min": float(secs.min()), "cps_median": float(np.median(cps)), "cps_p90": float(np.percentile(cps, 90)),
            "cps_p95": float(np.percentile(cps, 95)), "cps_max": float(cps.max()),
            "words_median": float(np.median([c["words"] for c in spoken])) if spoken else 0.0}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("videos", nargs="+")
    ap.add_argument("--words", required=True, help="a transcript .json, or a folder of them named like the videos")
    ap.add_argument("--band", nargs=2, type=float, default=(0.15, 0.36), help="the rows the captions sit in (fractions)")
    ap.add_argument("--out", help="write every caption to this .json")
    ap.add_argument("--list", action="store_true", help="print every caption")
    a = ap.parse_args(argv)
    paths = [p for v in a.videos for p in (glob.glob(v) or [v])]
    report = {}
    for p in paths:
        stem = os.path.splitext(os.path.basename(p))[0]
        tr = a.words if a.words.endswith(".json") else os.path.join(a.words, stem + ".json")
        caps = pace(p, tr, tuple(a.band))
        s = summary(caps)
        report[stem] = {"summary": s, "captions": caps}
        print(f"{stem[:60]}: {s['captions']} captions, on screen median {s['seconds_median']:.2f} s (p10 "
              f"{s['seconds_p10']:.2f}, min {s['seconds_min']:.2f}); {s['words_median']:.0f} words; characters a second "
              f"median {s['cps_median']:.1f}, p90 {s['cps_p90']:.1f}, p95 {s['cps_p95']:.1f}, max {s['cps_max']:.1f}")
        if a.list:
            for c in caps:
                print(f"  {c['start']:7.2f}  {c['seconds']:.2f} s  {c['cps']}  {c['text']!r}")
    if a.out:
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        json.dump(report, open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
