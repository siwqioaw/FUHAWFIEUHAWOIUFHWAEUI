"""Measure reference videos (docs/KIDS_SHORTS.md, "Study the references by measurement"): their cuts and shot
lengths, pace over time, loudness, flashes, black and frozen stretches, and a sheet with one frame from every shot.

    python tools/verify/analyze.py VIDEO [VIDEO ...] [--out DIR] [--ratio 4] [--truth cut.json]

Writes DIR/<video name>/analysis.md, analysis.json and shots_NN.jpg, and DIR/summary.md comparing the videos.
--truth scores the cut detection against a timeline whose cuts are known (one of your own renders): run that first to
see how far to trust the numbers on footage like yours.

A cut is a frame that differs from the one before it by at least `ratio` times the usual frame-to-frame change
around it (and by 2% at least); a jump that comes back within three frames (a flash, a glitch) is not counted. It
can't see a cut between near-identical pictures (black to black), and it counts big jumps inside a shot (a light
banging on, a glitch effect) as cuts. On the trailer this kit comes from, a hard case full of glitches, typing cards
and cuts to black, it found 22 of 28 cuts and 27 other jumps. (ffmpeg's scdet found 14, with 8 others.) Treat shot
lengths as estimates and look at the sheets: one frame from every detected shot.

Reference videos are someone else's work: measure and describe them, don't copy their footage, music or characters.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import media  # noqa: E402
import qc  # noqa: E402
import sheets  # noqa: E402
from timeline import Timeline  # noqa: E402

def detect_cuts(video: str, ratio: float = 4.0, floor: float = 0.02, fps: float | None = None
                ) -> tuple[list[tuple[float, float]], int]:
    """([(time, strength)], transients): the cuts (time of the first frame after each), and how many jumps came back
    within three frames. Decodes the video small (180 px wide) into memory: fine for shorts."""
    fps = fps or media.fps_of(media.probe(video))
    fr = media.frames_small(video)
    n = len(fr)
    d = np.concatenate([[0.0], np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2, 3))])
    cuts, transients = [], 0
    for i in range(1, n):
        around = np.concatenate([d[max(1, i - 12):max(1, i - 1)], d[i + 2:i + 13]])
        usual = float(np.median(around)) if len(around) else 0.0
        if d[i] < floor or d[i] < ratio * max(usual, 1e-3) or d[i] < d[max(1, i - 2):i + 3].max():
            continue
        if any(i + k < n and float(np.abs(fr[i + k] - fr[i - 1]).mean()) < 0.35 * d[i] for k in (1, 2, 3)):
            transients += 1
            continue
        cuts.append((i / fps, float(d[i])))
    return cuts, transients


def score(found: list[float], truth: list[float], tol: float) -> tuple[int, int, int]:
    """(hits, misses, false alarms) with a tolerance in seconds."""
    used, hits = set(), 0
    for t in truth:
        best = min((abs(f - t), i) for i, f in enumerate(found) if i not in used) if len(used) < len(found) else None
        if best and best[0] <= tol:
            used.add(best[1])
            hits += 1
    return hits, len(truth) - hits, len(found) - len(used)


def analyze(video: str, out_dir: str, ratio: float, truth: Timeline | None = None) -> dict:
    info = media.probe(video)
    v = media.video_stream(info)
    fps = media.fps_of(info)
    dur = float(info["format"]["duration"])
    has_audio = any(s["codec_type"] == "audio" for s in info["streams"])
    cuts, transients = detect_cuts(video, ratio, fps=fps)
    times = [t for t, _ in cuts]
    bounds = [0.0] + times + [dur]
    shots = [b - a for a, b in zip(bounds, bounds[1:]) if b - a > 1e-3]
    lens = np.array(shots)
    buckets = [(0, 0.5), (0.5, 1), (1, 2), (2, 4), (4, 1e9)]
    hist = {f"{a:g}-{b:g} s" if b < 1e9 else f"over {a:g} s": int(((lens >= a) & (lens < b)).sum())
            for a, b in buckets}
    pace = [int(sum(1 for t in times if k <= t < k + 5)) for k in range(0, int(np.ceil(dur)), 5)]
    loud = media.loudness(video) if has_audio else None
    flashes = qc.flashes(video, fps)
    blacks, freezes = qc.blacks_and_freezes(video)
    res = {
        "file": os.path.basename(video), "size": f"{v['width']}x{v['height']}", "fps": round(fps, 3),
        "duration": round(dur, 2), "cuts": [round(t, 3) for t in times], "shots": len(shots),
        "shot_median": round(float(np.median(lens)), 2), "shot_mean": round(float(lens.mean()), 2),
        "shot_min": round(float(lens.min()), 2), "shot_max": round(float(lens.max()), 2),
        "first_cut": round(times[0], 2) if times else None, "shot_lengths": hist, "transients": transients,
        "cuts_per_5s": pace, "loudness": loud, "flash_problems": flashes, "black": blacks, "freeze": freezes,
    }
    if truth:
        tc = [truth.sec(f) for _, _, f in truth.cuts()]
        h, m, fa = score(times, tc, 1.5 / fps)
        res["detection"] = {"true_cuts": len(tc), "found": h, "missed": m, "false_alarms": fa}
    os.makedirs(out_dir, exist_ok=True)
    mids = [int(round((a + b) / 2 * fps)) for a, b in zip(bounds, bounds[1:]) if b - a > 1e-3]
    paths = media.extract_frames(video, mids, os.path.join(out_dir, "_shots"),
                                 width=360 if int(v["height"]) > int(v["width"]) else 640)
    portrait = int(v["height"]) > int(v["width"])
    res["sheets"] = []
    for k in range(0, len(mids), 40):
        chunk = [(i, f) for i, f in enumerate(mids[k:k + 40], start=k) if f in paths]
        labels = [f"shot {i + 1}  {bounds[i]:.2f}s  {shots[i]:.2f}s long" for i, _ in chunk]
        dest = os.path.join(out_dir, f"shots_{k // 40:02d}.jpg")
        res["sheets"].append(sheets.tile([paths[f] for _, f in chunk], labels, dest, 10 if portrait else 6,
                                         200 if portrait else 320))
    with open(os.path.join(out_dir, "analysis.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    lines = [f"# {res['file']}", "",
             f"- {res['size']}, {res['fps']} fps, {res['duration']} s",
             f"- {len(times)} cuts detected, {res['shots']} shots: median {res['shot_median']} s, mean "
             f"{res['shot_mean']} s, {res['shot_min']}-{res['shot_max']} s; first cut at {res['first_cut']} s; "
             f"{transients} flashes or glitches (jumps that came back) not counted",
             "- shot lengths: " + ", ".join(f"{k}: {n}" for k, n in hist.items()),
             "- cuts in each 5 s: " + " ".join(str(n) for n in pace)]
    if loud:
        lines.append(f"- loudness {loud['I']:.1f} LUFS integrated, range {loud['LRA']:.1f} LU, true peak "
                     f"{loud['TP']:.1f} dBTP")
    lines.append(f"- flashes (WCAG 2.3.1): {len(flashes)} problems" + "".join(f"\n  - {p}" for p in flashes))
    lines += [f"- black: {b}" for b in blacks] + [f"- freeze: {f}" for f in freezes]
    if truth:
        d = res["detection"]
        lines.append(f"- detection against the timeline: {d['found']} of {d['true_cuts']} cuts found, "
                     f"{d['false_alarms']} false alarms")
    lines += ["", "Cut times (s): " + ", ".join(f"{t:.2f}" for t in times), ""]
    with open(os.path.join(out_dir, "analysis.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("videos", nargs="+")
    ap.add_argument("--out", default="build/analysis")
    ap.add_argument("--ratio", type=float, default=4.0, help="a cut's jump against the usual change (lower finds more)")
    ap.add_argument("--truth", help="a timeline with the video's true cuts, to score the detection")
    args = ap.parse_args()
    truth = Timeline.load(args.truth) if args.truth else None
    rows = []
    for v in args.videos:
        name = os.path.splitext(os.path.basename(v))[0]
        r = analyze(v, os.path.join(args.out, name), args.ratio, truth)
        rows.append(r)
        print(f"{name}: {r['duration']} s, {r['shots']} shots, median {r['shot_median']} s"
              + (f", {r['loudness']['I']:.1f} LUFS" if r["loudness"] else "")
              + (f"; detection {r['detection']}" if truth else ""))
    head = "| video | size | s | shots | median shot | first cut | LUFS | true peak | flash problems |"
    table = [head, "|" + "---|" * 9]
    for r in rows:
        ld = r["loudness"] or {}
        table.append(f"| {r['file']} | {r['size']} | {r['duration']} | {r['shots']} | {r['shot_median']} s | "
                     f"{r['first_cut']} s | {ld.get('I', '')} | {ld.get('TP', '')} | {len(r['flash_problems'])} |")
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "summary.md"), "w", encoding="utf-8") as f:
        f.write("# Reference videos\n\n" + "\n".join(table) + "\n")
    print(os.path.join(args.out, "summary.md"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
