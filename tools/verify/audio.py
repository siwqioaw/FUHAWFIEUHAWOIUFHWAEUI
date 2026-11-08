"""Check the sound against the cut, by measurement, since an agent can't listen (docs/VERIFY.md, "Sound"):

- crossings: every placed sound running across every cut. One the cue sheet didn't declare (a `bridge`, or a prelap:
  a sound placed in the next clip that starts just before it) FAILS. This is the check that would have caught a
  scream bleeding into the next scene.
- silences: each span meant to be silent, measured on the final mix (peak under -60 dBFS).
- sync: each picture hit has a sound landing on it (a rise of 6 dB or more, or a loud onset, within 2 frames).
- a spectrogram of the mix with every cut marked and named: a tail running past a cut shows as energy past its line.

    python tools/verify/audio.py cut.json MIX.wav|VIDEO.mp4 [--out DIR]

Writes DIR/audio_report.md and DIR/spectrogram.png; exits 1 if anything FAILs.
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import media  # noqa: E402
from timeline import Timeline  # noqa: E402


def _db(x: np.ndarray) -> float:
    r = float(np.sqrt(np.mean(x * x))) if len(x) else 0.0
    return 20 * np.log10(max(r, 1e-9))


def _peak_db(x: np.ndarray) -> float:
    return 20 * np.log10(max(float(np.abs(x).max()) if len(x) else 0.0, 1e-9))


def crossings(tl: Timeline, x: np.ndarray, sr: int) -> tuple[list[str], int]:
    lines, fails = [], 0
    if not tl.cues and len(x) and _peak_db(x) > -60:
        # Sound with nothing declared: the cue sheet is missing (the plan re-run after the mix wipes it), and every
        # crossing below would pass unchecked (M3's review: a timeline rewritten after delivery passed).
        lines += ["## The cue sheet: FAIL", "- the timeline declares no cues but the file has sound: run the mix "
                  "again so every crossing is checked", ""]
        fails += 1
    for a, b, f in tl.cuts():
        t = tl.sec(f)
        i = int(t * sr)
        pre, post = _db(x[max(0, i - int(0.12 * sr)):i]), _db(x[i:i + int(0.12 * sr)])
        over = [c for c in tl.cues if c["start"] < t - 1e-3 and c["end"] > t + 0.012]
        # Allowed across this cut: a declared bridge, or a prelap (placed in the clip after the cut).
        bad = [c for c in over if not c.get("bridge") and c.get("scene") != b]
        fails += len(bad)
        lines.append(f"## {a} -> {b} at {t:.2f} s: {'FAIL' if bad else 'ok'}  "
                     f"(mix {pre:5.1f} dB before, {post:5.1f} dB after)")
        for c in over:
            br = c.get("bridge")
            why = ((f"bridge to {br[0]} frame {br[1]}" if isinstance(br, list) else f"bridge to {br}") if br else
                   "prelap into it" if c.get("scene") == b else "NOT DECLARED")
            lines.append(f"- {c.get('label', '?')} [{c.get('bus', '?')}] from {c.get('scene', '?')}, "
                         f"runs {c['end'] - t:.2f} s on: {why}")
        lines.append("")
    return lines, fails


def silences(tl: Timeline, x: np.ndarray, sr: int) -> tuple[list[str], int]:
    lines, fails = ["## Intended silences (peak under -60 dBFS)", ""], 0
    for s in tl.silences:
        trim = int(0.004 * sr)
        seg = x[int(s["start"] * sr) + trim:int(s["end"] * sr) - trim]
        pk = _peak_db(seg)
        ok = pk < -60
        fails += 0 if ok else 1
        lines.append(f"- {'ok' if ok else 'FAIL'}: {s.get('what', '')} {s['start']:.2f}-{s['end']:.2f} s, "
                     f"peak {pk:.1f} dBFS")
    if not tl.silences:
        lines.append("- none declared")
    return lines + [""], fails


def sync(tl: Timeline, x: np.ndarray, sr: int) -> tuple[list[str], int]:
    mono = np.abs(x).mean(axis=1)
    steps = 10 * tl.fps  # tenth-of-a-frame envelope
    hop = max(1, int(sr / steps))
    env = np.array([mono[k:k + hop].mean() for k in range(0, len(mono) - hop, hop)])
    env_db = 20 * np.log10(np.maximum(env, 1e-7))
    lines, fails = ["## Picture hits against the sound (a sound must land within 2 frames)", ""], 0
    for h in sorted(tl.hits, key=lambda h: h["frame"]):
        k = int(h["frame"] * 10)
        before = env_db[max(0, k - 48):max(1, k - 6)].mean()
        after = env_db[max(0, k - 20):k + 20].max() if k < len(env_db) else -140.0
        rise = after - before
        ok = rise > 6 or after > -14
        fails += 0 if ok else 1
        lines.append(f"- {'ok' if ok else 'CHECK'}: frame {h['frame']} ({tl.sec(h['frame']):.2f} s, "
                     f"{h.get('what', '')}):"
                     f" rises {rise:+.1f} dB to {after:.1f} dB")
    if not tl.hits:
        lines.append("- none declared")
    return lines + [""], fails


def spectrogram(tl: Timeline, x: np.ndarray, sr: int, dest: str) -> str:
    """Log frequency (30 Hz to 16 kHz), a strip per 22 seconds, a line at every cut with the clip's name."""
    from scipy import signal as sps

    mono = x.mean(axis=1)
    f, t, z = sps.spectrogram(mono, sr, nperseg=2048, noverlap=2048 - 480)
    db = 10 * np.log10(np.maximum(z, 1e-12))
    from scipy.interpolate import interp1d

    rows = 180
    edges = np.geomspace(30, min(16000, sr / 2 - 1), rows + 1)
    # A band with FFT bins in it takes their mean; the narrow low bands, between bins, are interpolated.
    between = interp1d(f, db, axis=0)(np.sqrt(edges[:-1] * edges[1:]))
    img = np.stack([db[(f >= a) & (f < b)].mean(axis=0) if np.any((f >= a) & (f < b)) else between[k]
                    for k, (a, b) in enumerate(zip(edges, edges[1:]))])[::-1]
    img = np.clip((img + 110) / 80, 0, 1)
    px_per_s, strip = 90, 22.0
    total = len(mono) / sr
    n = max(1, int(np.ceil(total / strip)))
    out = Image.new("RGB", (int(strip * px_per_s) + 40, n * (rows + 34)), (12, 12, 14))
    d = ImageDraw.Draw(out)
    for k in range(n):
        a, b = k * strip, min(total, (k + 1) * strip)
        seg = img[:, (t >= a) & (t < b)]
        if seg.shape[1] == 0:
            continue
        w = max(1, int((b - a) * px_per_s))
        col = (np.stack([seg ** 1.3, seg ** 0.8, seg ** 2.2], axis=-1) * 255).astype(np.uint8)
        y0 = k * (rows + 34) + 18
        out.paste(Image.fromarray(col).resize((w, rows)), (20, y0))
        for c in tl.clips:
            ts = tl.sec(c["start"])
            if a <= ts < b:
                xx = 20 + int((ts - a) * px_per_s)
                d.line([(xx, y0 - 4), (xx, y0 + rows)], fill=(255, 220, 60), width=1)
                d.text((xx + 2, y0 - 16), c["name"], fill=(255, 220, 60))
    out.save(dest)
    return dest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("timeline")
    ap.add_argument("audio", help="the final mix (WAV) or the delivered video")
    ap.add_argument("--out", default="build/verify")
    args = ap.parse_args()
    tl = Timeline.load(args.timeline)
    x, sr = media.audio(args.audio)
    os.makedirs(args.out, exist_ok=True)
    report = ["# Sound at every cut", ""]
    c_lines, c_fails = crossings(tl, x, sr)
    s_lines, s_fails = silences(tl, x, sr)
    y_lines, y_fails = sync(tl, x, sr)
    report += c_lines + s_lines + y_lines
    fails = c_fails + s_fails
    report += [f"**{fails} failures, {y_fails} hits to check.**", ""]
    dest = os.path.join(args.out, "audio_report.md")
    with open(dest, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    png = spectrogram(tl, x, sr, os.path.join(args.out, "spectrogram.png"))
    print(dest)
    print(png)
    print("\n".join(line for line in report if "FAIL" in line or "CHECK" in line or line.startswith("**")))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
