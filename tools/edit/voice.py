"""Voice lines, from a TTS take to a clip the mix can place: breaths cut, sped up, levelled, words timed and checked.

    python tools/edit/voice.py fetch URL build/voice/raw/l1.mp3     # download a take (a connector's signed URL)
    python tools/edit/voice.py make lines.json --out build/voice    # process every line, time its words, check it
    python tools/edit/voice.py reel lines.json --out build/voice    # the processed lines in one file, to listen to

The takes come from ElevenLabs. An agent session with the ElevenLabs connector generates each take there (one node
per line on one flow) and downloads it with `fetch`. `lines.json` then says which take each line uses:

    {"cast": "tools/edit/voices.json",
     "lines": [{"id": "l1", "role": "narrator", "text": "[excited] Why does every group project have that ONE person?",
                "take": "build/s5/raw/l1.mp3"}, ...]}

For each line, `make` writes `<out>/<id>.wav` (48 kHz mono) and adds the line to `<out>/words.json` with the word
times the transcriber hears in the processed file, and `<out>/report.md` with every check. A FAIL there is a line to
regenerate or reprocess, never one to ship: every scripted word must be heard, the pauses and the speed must be the
role's, and the level must be the cast's (docs/VOICE.md).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf
from scipy import signal as sps

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "verify"))
import speech  # noqa: E402

SR = 48000
CAST = os.path.join(HERE, "voices.json")


def fetch(url: str, dest: str, timeout: float = 120.0) -> str:
    """Download a take to `dest`. The URL is a signed link from the connector; nothing else is sent."""
    import requests
    os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    with open(dest, "wb") as f:
        f.write(r.content)
    return dest


def decode(path: str, sr: int = SR) -> np.ndarray:
    """Any audio file as mono float at `sr` (ffmpeg decodes it)."""
    fd, tmp = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", path, "-ac", "1", "-ar", str(sr),
                        "-c:a", "pcm_f32le", tmp], check=True)
        x, _ = sf.read(tmp, dtype="float64")
    finally:
        os.remove(tmp)
    return np.asarray(x, dtype=float)


def frames(x: np.ndarray, sr: int) -> dict:
    """Per 10 ms frame: level (dBFS), voiced (YIN), and spectral centroid (Hz), all the same length."""
    db = speech.frames_db(x, sr)
    t, f0, _ = speech.yin(speech.mono16k(x, sr))
    voiced = np.zeros(len(db), bool)
    if len(t):
        idx = np.clip(np.round(t / 0.01 - 0.5).astype(int), 0, len(db) - 1)
        voiced[idx[~np.isnan(f0)]] = True
    f = int(0.01 * sr)
    n = len(db)
    spec = np.abs(np.fft.rfft(x[: n * f].reshape(n, f) * np.hanning(f), axis=1)) if n else np.zeros((0, f // 2 + 1))
    freqs = np.fft.rfftfreq(f, 1 / sr)
    cent = (spec * freqs).sum(axis=1) / np.maximum(spec.sum(axis=1), 1e-12)
    return {"db": db, "voiced": voiced, "centroid": cent}


def quiet_spans(x: np.ndarray, sr: int, silence_db: float = 32.0, breath_db: float = 14.0,
                breath_hz: float = 3500.0) -> list[tuple[int, int]]:
    """Runs of 10 ms frames that are silence (more than `silence_db` under the loudest frames) or breath (unvoiced,
    more than `breath_db` under them, and dark: centroid under `breath_hz`, where an 's' is bright). Frame indices,
    end exclusive; only runs between the first and last loud frames."""
    fr = frames(x, sr)
    db, top = fr["db"], np.percentile(fr["db"], 95) if len(fr["db"]) else 0.0
    silent = db < top - silence_db
    breath = (~fr["voiced"]) & (db < top - breath_db) & (fr["centroid"] < breath_hz)
    soft = silent | breath
    loud = np.flatnonzero(~silent)
    out, start = [], None
    if not len(loud):
        return out
    for i in range(loud[0], loud[-1] + 2):
        q = i <= loud[-1] and soft[i]
        if q and start is None:
            start = i
        elif not q and start is not None:
            out.append((start, i))
            start = None
    return out


def _sentence_ends(text: str) -> int:
    return sum(text.count(c) for c in ".!?")


def tighten(x: np.ndarray, sr: int, keep: float = 0.07, xfade: float = 0.01, tail: float = 0.6) -> tuple:
    """Cut every pause and breath between words down to `keep` seconds, keeping `tail` of what's kept on the side of
    the word before (its decay) and the rest before the next word (its onset), with `xfade`-second crossfades.
    Returns (audio, [(start, end) seconds removed, in the input's time])."""
    f = int(0.01 * sr)
    xf = max(1, int(xfade * sr))
    k = int(keep * sr)
    cuts = []
    for a, b in quiet_spans(x, sr):
        s0, s1 = a * f, b * f
        if s1 - s0 <= k + 2 * xf:
            continue
        c0 = s0 + int(k * tail)
        c1 = s1 - (k - int(k * tail))
        if c1 - c0 > 2 * xf:
            cuts.append((c0, c1))
    if not cuts:
        return x.copy(), []
    parts, prev = [], 0
    for c0, c1 in cuts:
        parts.append((prev, c0 + xf))
        prev = c1 - xf
    parts.append((prev, len(x)))
    out = x[parts[0][0]:parts[0][1]].copy()
    ramp = np.linspace(0, 1, xf)
    for p0, p1 in parts[1:]:
        seg = x[p0:p1]
        out[-xf:] = out[-xf:] * (1 - ramp) + seg[:xf] * ramp
        out = np.concatenate([out, seg[xf:]])
    return out, [(c0 / sr, c1 / sr) for c0, c1 in cuts]


def trim(x: np.ndarray, sr: int, lead: float = 0.012, tail: float = 0.06, below_db: float = 40.0) -> np.ndarray:
    """Cut the silence before the first sound and after the last, leaving `lead` and `tail` seconds, with short
    fades."""
    db = speech.frames_db(x, sr)
    if not len(db):
        return x
    loud = np.flatnonzero(db > np.percentile(db, 95) - below_db)
    if not len(loud):
        return x[:0]
    f = int(0.01 * sr)
    a = max(0, loud[0] * f - int(lead * sr))
    b = min(len(x), (loud[-1] + 1) * f + int(tail * sr))
    y = x[a:b].copy()
    fi, fo = min(len(y), int(0.004 * sr)), min(len(y), int(0.02 * sr))
    y[:fi] *= np.linspace(0, 1, fi)
    y[len(y) - fo:] *= np.linspace(1, 0, fo)
    return y


def tempo(x: np.ndarray, sr: int, factor: float, method: str = "atempo") -> np.ndarray:
    """Speed speech up by `factor` without changing its pitch: ffmpeg's atempo (overlap-add, natural on speech) or
    rubberband (a phase vocoder)."""
    if abs(factor - 1.0) < 1e-6:
        return x.copy()
    fd, src = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    dst = src[:-4] + "_t.wav"
    try:
        sf.write(src, x.astype(np.float32), sr, subtype="FLOAT")
        flt = f"atempo={factor:.5f}" if method == "atempo" else f"rubberband=tempo={factor:.5f}"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src, "-af", flt, "-ar", str(sr),
                        "-c:a", "pcm_f32le", dst], check=True)
        y, _ = sf.read(dst, dtype="float64")
    finally:
        for p in (src, dst):
            if os.path.exists(p):
                os.remove(p)
    return np.asarray(y, dtype=float)


def normalize(x: np.ndarray, sr: int, target_db: float = -18.0, ceiling_db: float = -1.0,
              max_limit_db: float = 4.0) -> tuple[np.ndarray, float]:
    """Gain to an active speech level of `target_db`; peaks over `ceiling_db` (true peak) go through the look-ahead
    limiter, up to `max_limit_db` of it, past which the gain backs off. Deep voices need the limiter: K-weighting
    hears little of their low end, so their peaks sit higher over their level."""
    import master
    g = target_db - speech.level(x, sr)
    y = x * 10 ** (g / 20)
    over = master.true_peak_db(y[:, None]) - ceiling_db
    if over > max_limit_db:
        y = y * 10 ** (-(over - max_limit_db) / 20)
        g -= over - max_limit_db
    if over > 0:
        y = master.limiter(y[:, None], sr, ceiling_db - 0.05)[:, 0]
    return y, g


def process(x: np.ndarray, sr: int, role: dict) -> tuple[np.ndarray, dict]:
    """One take through the chain: trim, tighten (pauses and breaths to `keep`), tempo, trim, level."""
    y = trim(x, sr)
    y, cuts = tighten(y, sr, keep=role.get("keep", 0.07))
    y = tempo(y, sr, role.get("tempo", 1.0), role.get("tempo_method", "atempo"))
    y = trim(y, sr)
    y, gain = normalize(y, sr, role.get("level_db", -18.0))
    return y, {"cut_s": round(sum(b - a for a, b in cuts), 3), "cuts": len(cuts), "gain_db": round(gain, 2),
               "in_s": round(len(x) / sr, 3), "out_s": round(len(y) / sr, 3)}


def load_cast(path: str | None) -> dict:
    with open(path or CAST, encoding="utf-8") as f:
        return json.load(f)


def measure(y: np.ndarray, sr: int, text: str, words: list[dict]) -> dict:
    """Everything `check` judges a processed line by."""
    lead, tail = speech.edges(y, sr)
    ps = speech.pauses(y, sr)
    sp = words[-1]["end"] - words[0]["start"] if len(words) > 1 else 0.0
    import master
    return {"duration": round(len(y) / sr, 3), "lead": lead, "tail": tail,
            "longest_pause": round(max((b - a for a, b in ps), default=0.0), 3),
            "pitch": speech.pitch(y, sr), "level_db": round(speech.level(y, sr), 2),
            "true_peak_db": round(master.true_peak_db(y[:, None]), 2),
            "words_per_s": round(len(words) / sp, 2) if sp > 0 else None,
            "match": speech.match(text, words)}


def check(m: dict, role: dict, line: dict) -> list[tuple[bool, str]]:
    """(ok, what) for every check on one processed line."""
    out = [(m["match"]["ratio"] == 1.0, "every scripted word heard" + (
        "" if m["match"]["ratio"] == 1.0 else f": missing {m['match']['missing']}"))]
    out.append((m["lead"] <= 0.05 and m["tail"] <= 0.15, f"starts within 50 ms and ends within 150 ms of its sound "
                f"({m['lead']:.3f}, {m['tail']:.3f} s)"))
    most = line.get("max_pause", role.get("max_pause", 0.2))
    out.append((m["longest_pause"] <= most, f"no pause over {most:.2f} s ({m['longest_pause']:.2f})"))
    lo, hi = role.get("pitch", [0, 10000])
    med = m["pitch"]["median"]
    out.append((med is not None and lo <= med <= hi, f"median pitch in {lo}-{hi} Hz ({med})"))
    if role.get("rate") and m["words_per_s"] is not None:
        rlo, rhi = role["rate"]
        out.append((rlo <= m["words_per_s"] <= rhi, f"{rlo}-{rhi} words a second ({m['words_per_s']})"))
    target = role.get("level_db", -18.0)
    out.append((abs(m["level_db"] - target) <= 0.6 and m["true_peak_db"] <= -0.9,
                f"speech level {target} dB ({m['level_db']}), true peak under -1 dBTP ({m['true_peak_db']})"))
    return [(bool(ok), what) for ok, what in out]


def _take_paths(line: dict, base: str) -> list[str]:
    out = []
    for t in line.get("takes") or [line["take"]]:
        p = t if os.path.isabs(t) else os.path.join(os.getcwd(), t)
        out.append(p if os.path.exists(p) else os.path.join(base, t))
    return out


def make(lines_path: str, out_dir: str, model: str = "large-v3", device: str = "auto") -> int:
    """Process every line in lines.json, transcribe the results, check them, and write words.json and report.md.
    A line with several `takes` keeps the best: fewest failed checks, then the clearest words (the transcriber's
    mean confidence), then the widest pitch (the liveliest read). Returns the number of failed checks."""
    spec = json.load(open(lines_path, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(lines_path))
    cast = load_cast(spec.get("cast") and os.path.join(os.getcwd(), spec["cast"]))
    os.makedirs(out_dir, exist_ok=True)
    import transcribe
    asr, dev = transcribe.load(model, device)

    def hear(path: str) -> list[dict]:
        nonlocal asr, dev
        try:
            res = transcribe.run(asr, path, "en")
        except RuntimeError:  # the GPU libraries fail at the first inference, not at load
            if dev != "cuda":
                raise
            asr, dev = transcribe.load(model, "cpu")
            res = transcribe.run(asr, path, "en")
        return [w for s in res["segments"] for w in s["words"]]

    entries, fails, rows = [], 0, []
    for line in spec["lines"]:
        role = dict(cast.get("defaults", {}), **cast["roles"][line["role"]], **line.get("process", {}))
        tried = []
        for i, take in enumerate(_take_paths(line, base)):
            y, info = process(decode(take), SR, role)
            dest = os.path.join(out_dir, f"{line['id']}.take{i}.wav")
            sf.write(dest, y.astype(np.float32), SR, subtype="PCM_24")
            words = hear(dest)
            m = measure(y, SR, line["text"], words)
            checks = check(m, role, line)
            bad = sum(1 for ok, _ in checks if not ok)
            clear = float(np.mean([w["p"] for w in words])) if words else 0.0
            tried.append({"take": os.path.relpath(take), "wav": dest, "y": y, "info": info, "words": words, "m": m,
                          "checks": checks, "score": (bad, -round(clear, 3), -(m["pitch"]["spread_st"] or 0)),
                          "clear": round(clear, 3)})
        best = min(tried, key=lambda t: t["score"])
        final = os.path.join(out_dir, line["id"] + ".wav")
        sf.write(final, best["y"].astype(np.float32), SR, subtype="PCM_24")
        for t in tried:
            os.remove(t["wav"])
        m, checks, info, words = best["m"], best["checks"], best["info"], best["words"]
        fails += sum(1 for ok, _ in checks if not ok)
        entries.append({"id": line["id"], "role": line["role"], "voice": role.get("name"), "text": line["text"],
                        "file": os.path.basename(final), "duration": m["duration"], "take": best["take"],
                        "takes": [{"take": t["take"], "failed": t["score"][0], "clear": t["clear"],
                                   "spread_st": t["m"]["pitch"]["spread_st"]} for t in tried],
                        "words": [{"word": w["word"], "start": w["start"], "end": w["end"], "p": w["p"]}
                                  for w in words],
                        "heard": " ".join(w["word"] for w in words), "process": info, "measure": m,
                        "checks": [{"ok": ok, "what": what} for ok, what in checks]})
        rows.append((line, m, checks, info, best, tried))
        print(f"{line['id']} ({line['role']}): {m['duration']:.2f} s, {m['words_per_s']} w/s, pitch "
              f"{m['pitch']['median']} Hz, longest pause {m['longest_pause']:.2f} s, "
              f"{'all checks pass' if all(ok for ok, _ in checks) else 'FAIL'}"
              + (f" (take {tried.index(best) + 1} of {len(tried)})" if len(tried) > 1 else ""), flush=True)
    with open(os.path.join(out_dir, "words.json"), "w", encoding="utf-8") as f:
        json.dump({"sr": SR, "lines": entries}, f, indent=1, ensure_ascii=False)
    rep = ["# Voice lines", "", f"From `{os.path.relpath(lines_path)}`, transcribed on {dev}.", "",
           "| line | role | voice | s | words/s | pitch Hz (spread st) | longest pause | level | heard |",
           "|---|---|---|---|---|---|---|---|---|"]
    for line, m, checks, info, best, tried in rows:
        p = m["pitch"]
        rep.append(f"| {line['id']} | {line['role']} | {cast['roles'][line['role']].get('name', '')} | "
                   f"{m['duration']:.2f} | {m['words_per_s']} | {p['median']} ({p['spread_st']}) | "
                   f"{m['longest_pause']:.2f} | {m['level_db']} | {m['match']['ratio']:.0%} |")
    rep += [""]
    for line, m, checks, info, best, tried in rows:
        rep.append(f"## {line['id']}: {speech.TAG.sub('', line['text']).strip()}")
        rep.append("")
        if len(tried) > 1:
            rep.append(f"- take {tried.index(best) + 1} of {len(tried)} kept: " + "; ".join(
                f"take {i + 1} {t['score'][0]} failed, clarity {t['clear']}, spread {t['m']['pitch']['spread_st']} st"
                for i, t in enumerate(tried)))
        rep.append(f"- processed: {info['in_s']:.2f} s in, {info['cuts']} pauses cut ({info['cut_s']:.2f} s), "
                   f"{info['out_s']:.2f} s out, gain {info['gain_db']:+.1f} dB")
        rep.append(f"- heard: {' '.join(w['word'] for w in best['words'])}")
        rep += [f"- {'PASS' if ok else 'FAIL'}: {what}" for ok, what in checks]
        rep.append("")
    rep.append(f"**{fails} failed check{'s' if fails != 1 else ''}.**")
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(rep) + "\n")
    return fails


def reel(lines_path: str, out_dir: str, gap: float = 0.6) -> str:
    """The processed lines back to back with `gap` seconds between, as reel.wav and reel.mp4 (a card per line saying
    who speaks, in which voice, and the line), to listen to."""
    from PIL import Image, ImageDraw, ImageFont
    spec = json.load(open(lines_path, encoding="utf-8"))
    cast = load_cast(spec.get("cast") and os.path.join(os.getcwd(), spec["cast"]))
    clips, cards = [], []
    tmp = tempfile.mkdtemp(prefix="reel_")
    face = "C:/Windows/Fonts/arialbd.ttf" if os.path.exists("C:/Windows/Fonts/arialbd.ttf") else None
    big = ImageFont.truetype(face, 44) if face else ImageFont.load_default()
    small = ImageFont.truetype(face, 30) if face else ImageFont.load_default()
    for i, line in enumerate(spec["lines"]):
        y, _ = sf.read(os.path.join(out_dir, line["id"] + ".wav"), dtype="float64")
        clips.append(np.concatenate([y, np.zeros(int(gap * SR))]))
        img = Image.new("RGB", (540, 960), (18, 20, 28))
        d = ImageDraw.Draw(img)
        role = cast["roles"][line["role"]]
        d.text((40, 300), f"{line['id']}  {line['role']}", font=big, fill=(255, 214, 80))
        d.text((40, 360), role.get("name", ""), font=small, fill=(200, 200, 210))
        words, row, yy = speech.TAG.sub("", line["text"]).split(), "", 450
        for w in words:
            if d.textlength(row + " " + w, font=small) > 460:
                d.text((40, yy), row.strip(), font=small, fill=(240, 240, 240))
                row, yy = "", yy + 42
            row += " " + w
        d.text((40, yy), row.strip(), font=small, fill=(240, 240, 240))
        p = os.path.join(tmp, f"c{i:03d}.png")
        img.save(p)
        cards.append((p, len(clips[-1]) / SR))
    audio = np.concatenate(clips)
    wav = os.path.join(out_dir, "reel.wav")
    sf.write(wav, audio.astype(np.float32), SR, subtype="PCM_24")
    listing = os.path.join(tmp, "cards.txt")
    with open(listing, "w", encoding="utf-8") as f:
        for p, dur in cards:
            f.write(f"file '{p}'\nduration {dur:.4f}\n")
        f.write(f"file '{cards[-1][0]}'\n")
    mp4 = os.path.join(out_dir, "reel.mp4")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", listing,
                    "-i", wav, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", mp4], check=True)
    return mp4


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("url")
    f.add_argument("dest")
    m = sub.add_parser("make")
    m.add_argument("lines")
    m.add_argument("--out", default="build/voice")
    m.add_argument("--model", default="large-v3")
    m.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"])
    r = sub.add_parser("reel")
    r.add_argument("lines")
    r.add_argument("--out", default="build/voice")
    args = ap.parse_args()
    if args.cmd == "fetch":
        print(fetch(args.url, args.dest))
        return 0
    if args.cmd == "make":
        fails = make(args.lines, args.out, args.model, args.device)
        print(f"{fails} failed checks; report in {os.path.join(args.out, 'report.md')}")
        return 1 if fails else 0
    print(reel(args.lines, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
