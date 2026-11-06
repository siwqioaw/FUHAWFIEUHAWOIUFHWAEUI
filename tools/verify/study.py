"""Study sheets for reference videos: what a viewer sees and hears, laid out to be read, since an agent can't watch
or listen (docs/KIDS_SHORTS.md, "Study the references by measurement").

    python tools/verify/study.py VIDEO [VIDEO ...] [--out DIR] [--every 0] [--words DIR] [--analysis DIR]

For each video, writes DIR/<name>/:

- hook.jpg: the first 3 seconds, a frame every quarter second, large enough to read the captions and the faces;
- contact_NN.jpg: a frame every --every seconds (0: every 0.5 s up to 40 s long, every 1 s past that), each labelled
  with its time and the words being said around it (from transcribe.py's <name>.json in --words, when there);
- audio.png: the sound in strips of 15 s: a spectrogram (40 Hz at the bottom to 14 kHz at the top), the loudness
  (white line, -60 to 0 dBFS), the words under it, the cuts (yellow, from analyze.py's <name>/analysis.json in
  --analysis) and the onsets that come outside any word (red ticks: likely sound effects, music hits or stings);
- audio.md: the same as numbers: voice level against the bed between words, an estimated tempo, every onset outside
  the words, how many cuts land on an onset, and the loudness each half second.

The onsets and the tempo are estimates: a spectrogram can show that something hit, not what it was. Name the sounds
by listening (or ask the owner, or a model that can hear), and use these numbers to say where to listen.

Reference videos are someone else's work: study and measure them, don't reuse their footage, sound or characters.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import media  # noqa: E402

HOP = 0.01  # spectrogram hop, seconds


def font(size: int) -> ImageFont.ImageFont:
    for name in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def load_words(words_dir: str | None, name: str) -> list[dict]:
    p = os.path.join(words_dir or "", name + ".json")
    if not words_dir or not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        return [w for s in json.load(f)["segments"] for w in s["words"]]


def load_cuts(analysis_dir: str | None, name: str) -> list[float]:
    p = os.path.join(analysis_dir or "", name, "analysis.json")
    if not analysis_dir or not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        return list(json.load(f)["cuts"])


def said(words: list[dict], t: float, half: float) -> str:
    return " ".join(w["word"] for w in words if w["end"] > t - half and w["start"] < t + half)


def wrap(d: ImageDraw.ImageDraw, text: str, fnt, width: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if not cur or d.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    return lines + ([cur] if cur else [])


def sheet(paths: list[str], heads: list[str], texts: list[str], dest: str, cols: int, tile_w: int,
          text_lines: int = 3) -> str:
    ims = [Image.open(p).convert("RGB") for p in paths]
    tile_h = int(tile_w * ims[0].height / ims[0].width)
    fh, ft = font(16), font(14)
    band = 22 + 17 * text_lines
    rows = (len(ims) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * tile_w, rows * (tile_h + band)), (14, 14, 16))
    d = ImageDraw.Draw(canvas)
    for i, (im, head, text) in enumerate(zip(ims, heads, texts)):
        x, y = (i % cols) * tile_w, (i // cols) * (tile_h + band)
        canvas.paste(im.resize((tile_w, tile_h), Image.LANCZOS), (x, y))
        d.rectangle((x, y + tile_h, x + tile_w - 1, y + tile_h + band - 1), outline=(40, 40, 46))
        d.text((x + 5, y + tile_h + 3), head, fill=(255, 220, 0), font=fh)
        for k, line in enumerate(wrap(d, text, ft, tile_w - 10)[:text_lines]):
            d.text((x + 5, y + tile_h + 22 + 17 * k), line, fill=(235, 235, 235), font=ft)
    canvas.save(dest, quality=90)
    return dest


def frames_at(video: str, times: list[float], fps: float, n_frames: int, out: str, width: int
              ) -> list[tuple[float, str]]:
    idx = [min(n_frames - 1, int(round(t * fps))) for t in times]
    paths = media.extract_frames(video, idx, out, width=width)
    return [(t, paths[i]) for t, i in zip(times, idx) if i in paths]


def bands(mono: np.ndarray, sr: int, rows: int = 140) -> tuple[np.ndarray, np.ndarray]:
    """(dB per log band x time, times): 40 Hz to 14 kHz, a column every HOP seconds."""
    from scipy import signal as sps
    from scipy.interpolate import interp1d

    hop = int(HOP * sr)
    f, t, z = sps.spectrogram(mono, sr, nperseg=1024, noverlap=1024 - hop)
    db = 10 * np.log10(np.maximum(z, 1e-12))
    edges = np.geomspace(40, min(14000, sr / 2 - 1), rows + 1)
    between = interp1d(f, db, axis=0)(np.sqrt(edges[:-1] * edges[1:]))
    img = np.stack([db[(f >= a) & (f < b)].mean(axis=0) if np.any((f >= a) & (f < b)) else between[k]
                    for k, (a, b) in enumerate(zip(edges, edges[1:]))])
    return img, t


def onsets(b: np.ndarray, t: np.ndarray) -> list[tuple[float, float]]:
    """[(time, strength)]: peaks of spectral flux over a local threshold. Strength is the peak over the threshold."""
    from scipy import ndimage, signal as sps

    flux = np.concatenate([[0.0], np.maximum(np.diff(b, axis=1), 0).mean(axis=0)])
    mad = 1.4826 * float(np.median(np.abs(flux - np.median(flux)))) + 1e-6
    thr = ndimage.median_filter(flux, size=51) + 3.0 * mad
    peaks, _ = sps.find_peaks(flux, height=thr, distance=int(0.08 / HOP))
    return [(float(t[p]), float(flux[p] / thr[p])) for p in peaks]


def tempo(b: np.ndarray) -> tuple[float, float]:
    """(BPM, confidence) from the autocorrelation of the flux, 70-180 BPM. Confidence is the peak over the median of
    that range: under about 1.5, there's no steady beat to speak of (speech alone, or rubato)."""
    flux = np.maximum(np.diff(b, axis=1), 0).mean(axis=0)
    flux = flux - flux.mean()
    ac = np.correlate(flux, flux, mode="full")[len(flux) - 1:]
    lo, hi = int(60 / 180 / HOP), int(60 / 70 / HOP)
    seg = ac[lo:hi + 1]
    k = int(np.argmax(seg))
    conf = float(seg[k] / max(np.median(np.abs(seg)), 1e-9))
    return round(60 / ((lo + k) * HOP), 1), round(conf, 2)


def in_words(words: list[dict], t: float, before: float = 0.05, after: float = 0.03) -> bool:
    return any(w["start"] - before <= t <= w["end"] + after for w in words)


def audio_map(video: str, words: list[dict], cuts: list[float], dest_png: str, dest_md: str) -> None:
    x, sr = media.audio(video, sr=32000)
    mono = x.mean(axis=1)
    dur = len(mono) / sr
    b, t = bands(mono, sr)
    ons = onsets(b, t)
    outside = [(s, k) for s, k in ons if not in_words(words, s)]
    bpm, conf = tempo(b)

    hop = int(0.05 * sr)
    rms = np.array([np.sqrt(np.mean(mono[i:i + hop] ** 2)) for i in range(0, len(mono) - hop + 1, hop)])
    rms_db = 20 * np.log10(np.maximum(rms, 1e-7))
    centers = (np.arange(len(rms_db)) + 0.5) * 0.05
    speech = np.array([in_words(words, c, 0, 0) for c in centers]) if words else np.zeros(len(centers), bool)
    gap = np.array([all(abs(c - w["start"]) > 0.15 and abs(c - w["end"]) > 0.15 and not w["start"] <= c <= w["end"]
                        for w in words) for c in centers]) if words else np.ones(len(centers), bool)

    # The picture: strips of 15 s.
    img = np.clip((b + 110) / 80, 0, 1)[::-1]
    rows, px_s, strip, left = img.shape[0], 100, 15.0, 44
    strip_h = 18 + rows + 10 + 30 + 12
    n = max(1, int(np.ceil(dur / strip)))
    out = Image.new("RGB", (int(strip * px_s) + left + 10, n * strip_h), (12, 12, 14))
    d = ImageDraw.Draw(out)
    fs, fw = font(12), font(11)
    for k in range(n):
        a, e = k * strip, min(dur, (k + 1) * strip)
        y0 = k * strip_h + 18
        seg = img[:, (t >= a) & (t < e)]
        if seg.shape[1]:
            w = max(1, int((e - a) * px_s))
            col = (np.stack([seg ** 1.3, seg ** 0.8, seg ** 2.2], axis=-1) * 255).astype(np.uint8)
            out.paste(Image.fromarray(col).resize((w, rows)), (left, y0))
        for hz, lab in ((100, "100"), (1000, "1k"), (5000, "5k")):
            yy = y0 + rows - int(rows * np.log(hz / 40) / np.log(14000 / 40))
            d.text((4, yy - 6), lab, fill=(150, 150, 150), font=fs)
        for s in range(int(a), int(np.ceil(e)) + 1):
            xx = left + int((s - a) * px_s)
            d.line([(xx, y0 - 4), (xx, y0)], fill=(160, 160, 160))
            if s % 5 == 0:
                d.text((xx + 2, y0 - 17), f"{s}s", fill=(200, 200, 200), font=fs)
        pts = [(left + int((c - a) * px_s), y0 + rows - int(rows * (np.clip(v, -60, 0) + 60) / 60))
               for c, v in zip(centers, rms_db) if a <= c < e]
        if len(pts) > 1:
            d.line(pts, fill=(255, 255, 255), width=1)
        for c in cuts:
            if a <= c < e:
                xx = left + int((c - a) * px_s)
                d.line([(xx, y0), (xx, y0 + rows)], fill=(255, 220, 60), width=2)
        for s, strength in outside:
            if a <= s < e:
                xx = left + int((s - a) * px_s)
                d.line([(xx, y0), (xx, y0 + min(40, int(10 * strength)))], fill=(255, 60, 60), width=2)
        yb = y0 + rows + 4
        for i, w in enumerate(words):
            if a <= w["start"] < e:
                x1, x2 = left + int((w["start"] - a) * px_s), left + int((min(w["end"], e) - a) * px_s)
                d.rectangle((x1, yb, max(x1 + 1, x2), yb + 5), fill=(70, 130, 255))
                d.text((x1, yb + 7 + 13 * (i % 2)), w["word"], fill=(210, 220, 255), font=fw)
    out.save(dest_png)

    sp = float(np.median(rms_db[speech])) if speech.any() else float("nan")
    gp = float(np.median(rms_db[gap])) if gap.any() else float("nan")
    on_cut = sum(1 for c in cuts if any(abs(s - c) <= 0.1 for s, _ in ons))
    lines = [f"# Sound of {os.path.basename(video)}", "",
             f"- {dur:.2f} s; {len(words)} words; {len(ons)} onsets, {len(outside)} of them outside the words",
             f"- level: {sp:.1f} dBFS median while words are said, {gp:.1f} dBFS in the gaps of 0.15 s or more from "
             f"any word (the bed: music, ambience, effects; nan when there are no such gaps)",
             f"- steady beat: {bpm} BPM, confidence {conf} (under about 1.5: no steady beat)",
             f"- cuts landing within 0.1 s of an onset: {on_cut} of {len(cuts)}", "",
             "## Onsets outside the words (time, strength over threshold; * within 0.1 s of a cut)", ""]
    lines += [", ".join(f"{s:.2f} ({k:.1f}){'*' if any(abs(s - c) <= 0.1 for c in cuts) else ''}"
                        for s, k in outside) or "none", "", "## Loudness each 0.5 s (dBFS RMS)", ""]
    per = [float(np.mean(rms_db[int(i * 10):int(i * 10) + 10])) for i in range(int(len(rms_db) / 10))]
    lines += [" ".join(f"{v:.0f}" for v in per), ""]
    with open(dest_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def study(video: str, out_root: str, every: float, words_dir: str | None, analysis_dir: str | None) -> list[str]:
    name = os.path.splitext(os.path.basename(video))[0]
    out = os.path.join(out_root, name)
    os.makedirs(out, exist_ok=True)
    info = media.probe(video)
    v = media.video_stream(info)
    fps = media.fps_of(info)
    dur = float(info["format"]["duration"])
    n_frames = int(v.get("nb_frames") or int(dur * fps))
    words = load_words(words_dir, name)
    cuts = load_cuts(analysis_dir, name)
    every = every or (0.5 if dur <= 40 else 1.0)
    made = []

    hook = frames_at(video, [round(k * 0.25, 2) for k in range(13)], fps, n_frames, os.path.join(out, "_hook"), 540)
    made.append(sheet([p for _, p in hook], [f"{t:.2f}s" for t, _ in hook],
                      [said(words, t, 0.125) for t, _ in hook], os.path.join(out, "hook.jpg"), 7, 270, 2))

    times = [round(k * every, 3) for k in range(int(dur / every) + 1) if k * every < dur - 0.02]
    shots = frames_at(video, times, fps, n_frames, os.path.join(out, "_contact"), 600)
    per = 18
    for k in range(0, len(shots), per):
        chunk = shots[k:k + per]
        heads = [f"{t:.1f}s" + ("  CUT" if any(t - every / 2 < c <= t + every / 2 for c in cuts) else "")
                 for t, _ in chunk]
        made.append(sheet([p for _, p in chunk], heads, [said(words, t, every / 2) for t, _ in chunk],
                          os.path.join(out, f"contact_{k // per:02d}.jpg"), 6, 300))

    audio_map(video, words, cuts, os.path.join(out, "audio.png"), os.path.join(out, "audio.md"))
    made += [os.path.join(out, "audio.png"), os.path.join(out, "audio.md")]
    return made


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("videos", nargs="+")
    ap.add_argument("--out", default="build/study")
    ap.add_argument("--every", type=float, default=0.0)
    ap.add_argument("--words", help="transcribe.py's output folder")
    ap.add_argument("--analysis", help="analyze.py's output folder")
    args = ap.parse_args()
    for vid in args.videos:
        made = study(vid, args.out, args.every, args.words, args.analysis)
        print(f"{os.path.basename(vid)}: {len(made)} files in {os.path.dirname(made[0])}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
