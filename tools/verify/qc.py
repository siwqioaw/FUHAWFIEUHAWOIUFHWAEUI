"""Measured checks on a delivered video (docs/VERIFY.md): its specs, loudness and true peak, photosensitive flashes
(WCAG 2.3.1), black and frozen frames, and, with a timeline, whether each piece of on-screen text stays up long
enough to read and whether the audio clicks at the cuts. Writes a Markdown report; exits 1 if anything FAILs.

    python tools/verify/qc.py VIDEO.mp4 [--timeline cut.json] [--out DIR] [--lufs -14] [--tp -1.0] [--cps 12]

Run it on the file you deliver, not the master or the WAV: the encoder changes the true peak (AAC added up to 3 dB on
sharp clicks in the project this comes from) and can change frames.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import media  # noqa: E402
from timeline import Timeline  # noqa: E402


def text_times(tl: Timeline, cps: float) -> list[tuple[str, str]]:
    """Each on-screen text's time up against the time to read it: 0.5 s plus its characters at `cps` a second, and at
    least 1.2 s. Texts marked "accent": true (a number slammed on a beat, read at a glance) are left out."""
    rows = []
    for t in tl.texts:
        if t.get("accent"):
            continue
        chars = len(t["text"]) + len(t.get("sub", ""))
        need = max(1.2, 0.5 + chars / cps)
        have = tl.sec(t["frames"])
        ok = have >= need - 1e-6
        rows.append(("PASS" if ok else "FAIL", f"{t['text']!r}: {have:.2f} s on screen, needs {need:.2f} s"))
    return rows


def clicks(tl: Timeline, x: np.ndarray, sr: int) -> tuple[list[str], int]:
    """Discontinuities at the cuts: a sample-to-sample jump in the 10 ms round a cut far bigger than the sound's own
    just before it. A sound starting out of silence is an onset, not a click; so is one at a cut with a declared hit
    within 2 frames of it (a hit placed on the cut looks the same to this measure). Returns what's left, and how many
    were put down to hits."""
    m = x.mean(axis=1)
    d = np.abs(np.diff(m))
    found, on_hits = [], 0
    hit_frames = [h["frame"] for h in tl.hits]
    for a, b, f in tl.cuts():
        t = tl.sec(f)
        i = int(t * sr)
        lo, hi = max(0, i - int(0.01 * sr)), min(len(d), i + int(0.01 * sr))
        pre = d[max(0, i - int(0.06 * sr)):lo]
        if hi <= lo or len(pre) == 0:
            continue
        before, peak = pre.max(), d[lo:hi].max()
        if before > 0.005 and peak > 4 * before and peak > 0.05:
            if any(abs(h - f) <= 2 for h in hit_frames):
                on_hits += 1
            else:
                found.append(f"{a} -> {b} at {t:.2f} s: jump {peak:.3f} against {before:.3f} before it")
    return found, on_hits


def flashes(video: str, fps: float) -> list[str]:
    """WCAG 2.3.1 general flashes: a pair of opposing changes in relative luminance of 10% or more of the maximum,
    where the darker state is below 0.80, over 25% of the frame or more (the whole frame, and every 2 x 2 block of a
    4 x 4 grid), more than 3 times in any second. Red flashes: changes to or from saturated red (R/(R+G+B) >= 0.8) over
    a quarter of a region, counted the same way. A simplification of the guideline, on the safe side."""
    # Each frame comes down to two numbers per region, so the video is read a chunk at a time.
    regions: list[tuple[slice, slice]] = []
    lums: list[list[np.ndarray]] = []
    reds: list[list[np.ndarray]] = []
    for raw in media.frames_small_chunks(video):
        lin = np.where(raw <= 0.04045, raw / 12.92, ((raw + 0.055) / 1.055) ** 2.4)
        lum = lin @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
        if not regions:
            h, w = lum.shape[1:]
            regions = [(slice(0, h), slice(0, w))]
            for gy in range(3):
                for gx in range(3):
                    regions.append((slice(gy * h // 4, (gy + 2) * h // 4), slice(gx * w // 4, (gx + 2) * w // 4)))
            lums, reds = [[] for _ in regions], [[] for _ in regions]
        for ri, (sy, sx) in enumerate(regions):
            lums[ri].append(lum[:, sy, sx].mean(axis=(1, 2)))
            reds[ri].append((raw[:, sy, sx, 0] / np.maximum(raw[:, sy, sx].sum(axis=-1), 1e-6) >= 0.8)
                            .mean(axis=(1, 2)))
    per_second = int(round(fps))
    problems = []
    for ri in range(len(regions)):
        series, redness = np.concatenate(lums[ri]), np.concatenate(reds[ri])
        n = len(series)
        for name, s, thresh in (("general", series, 0.1), ("red", redness, 0.25)):
            events = []
            last_ext, last_dir = s[0], 0
            for i in range(1, n):
                dv = s[i] - last_ext
                if name == "general" and min(s[i], last_ext) >= 0.8:
                    continue
                if abs(dv) >= thresh:
                    direction = 1 if dv > 0 else -1
                    if direction != last_dir:
                        events.append(i)
                        last_dir = direction
                    last_ext = s[i]
                elif (dv > 0 and last_dir > 0) or (dv < 0 and last_dir < 0):
                    last_ext = s[i]
            # A flash is a pair of opposing changes; more than 3 flashes (6 changes) in any second fails.
            ev = np.array(events)
            for i in range(len(ev)):
                within = ev[(ev >= ev[i]) & (ev < ev[i] + per_second)]
                if len(within) > 6:
                    where = "the whole frame" if ri == 0 else f"region {ri}"
                    problems.append(f"{name} flashes over {where}: {len(within) // 2} in the second from "
                                    f"{ev[i] / fps:.2f} s")
                    break
    return problems


def blacks_and_freezes(video: str) -> tuple[list[str], list[str]]:
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", video, "-vf",
                        "blackdetect=d=0.1:pix_th=0.05,freezedetect=n=0.001:d=0.3", "-an", "-f", "null", "-"],
                       capture_output=True, text=True)
    blacks = [ln.split("]", 1)[1].strip() for ln in p.stderr.splitlines() if "black_start" in ln]
    freezes = [ln.split("]", 1)[1].strip() for ln in p.stderr.splitlines() if "freeze_start" in ln or
               "freeze_duration" in ln]
    return blacks, freezes


def report(video: str, tl: Timeline | None, out_dir: str, lufs: float, tp: float, cps: float) -> tuple[str, bool]:
    info = media.probe(video)
    v = media.video_stream(info)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    fps = media.fps_of(info)
    dur = float(info["format"]["duration"])
    failed = False
    lines = ["# QC report", "", f"File: `{os.path.basename(video)}`", "", "## Specs", "",
             f"- {v['width']}x{v['height']}, {v['r_frame_rate']} fps, {v['codec_name']} {v.get('profile', '')}, "
             f"{v.get('pix_fmt')}, {dur:.2f} s, {int(info['format']['size']) / 1e6:.1f} MB",
             f"- audio: {a['codec_name']} {a.get('sample_rate')} Hz, {a.get('channels')} ch" if a else "- no audio", ""]
    if tl and abs(tl.duration() - dur) > 1.5 / fps:
        lines += [f"- FAIL: the timeline is {tl.duration():.2f} s, the file {dur:.2f} s", ""]
        failed = True
    if a:
        loud = media.loudness(video)
        ok = abs(loud["I"] - lufs) <= 1 and loud["TP"] <= tp
        failed |= not ok
        lines += ["## Loudness (measured on this file)", "",
                  f"- {'PASS' if ok else 'FAIL'}: integrated {loud['I']:.1f} LUFS (target {lufs:g} +/- 1), true peak "
                  f"{loud['TP']:.1f} dBTP (at most {tp:g}), range {loud['LRA']:.1f} LU", ""]
    if tl:
        rows = text_times(tl, cps)
        lines += [f"## Text read time (0.5 s + characters at {cps:g} a second, at least 1.2 s)", ""]
        lines += [f"- {s}: {m}" for s, m in rows] or ["- no texts in the timeline"]
        lines += [""]
        failed |= any(s == "FAIL" for s, _ in rows)
        if a:
            x, sr = media.audio(video)
            cl, on_hits = clicks(tl, x, sr)
            lines += ["## Clicks at the cuts (listen to each: a click, or a sound you placed on the cut?)", "",
                      f"- {'PASS' if not cl else 'CHECK'}: {len(cl)} found"
                      + (f" ({on_hits} more at cuts with a declared hit, taken as its onset)" if on_hits else "")]
            lines += [f"  - {c}" for c in cl] + [""]
    fl = flashes(video, fps)
    failed |= bool(fl)
    lines += ["## Photosensitive flashes (WCAG 2.3.1)", "", f"- {'PASS' if not fl else 'FAIL'}: {len(fl)} problems"]
    lines += [f"  - {p}" for p in fl] + [""]
    blacks, freezes = blacks_and_freezes(video)
    lines += ["## Black and frozen frames (check each was meant)", ""]
    lines += [f"- black: {b}" for b in blacks] + [f"- freeze: {f}" for f in freezes]
    lines += ["- none"] if not blacks and not freezes else []
    lines += ["", f"**{'FAILED' if failed else 'All measured checks passed.'}**", ""]
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, "qc_report.md")
    with open(dest, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return dest, failed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--timeline")
    ap.add_argument("--out", default="build/verify")
    ap.add_argument("--lufs", type=float, default=-14.0, help="integrated loudness target (LUFS)")
    ap.add_argument("--tp", type=float, default=-1.0, help="most true peak allowed (dBTP)")
    ap.add_argument("--cps", type=float, default=12.0, help="reading speed for the read-time check (characters/s)")
    args = ap.parse_args()
    tl = Timeline.load(args.timeline) if args.timeline else None
    dest, failed = report(args.video, tl, args.out, args.lufs, args.tp, args.cps)
    print(dest)
    print(open(dest, encoding="utf-8").read())
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
