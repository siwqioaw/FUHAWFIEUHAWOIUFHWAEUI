"""Measure speech: pitch, speaking rate, pauses, level, and whether every scripted word is heard.

    python tools/verify/speech.py refs VIDEO [VIDEO ...] --words refs/r6rants/transcripts --out build/speech
    python tools/verify/speech.py file AUDIO [AUDIO ...]           # pitch, level and pauses of any file

`refs` measures each reference video's voice over the words its transcript found: the median pitch and its spread,
the speaking rate inside runs of speech, and the gaps between words. Those are the targets `voice.py` checks our
lines against (docs/VOICE.md). The pitch tracker is YIN on the mid channel at 16 kHz, so a music bed 12-15 dB under
the voice doesn't move it; where two voices talk, the median follows the one that talks most.
"""

from __future__ import annotations

import argparse
import difflib
import glob
import json
import math
import os
import re
import sys

import numpy as np
from scipy import signal as sps

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "edit"))

SR = 16000
TAG = re.compile(r"\[[^\]]*\]")


def mono16k(x: np.ndarray, sr: int) -> np.ndarray:
    """The mid channel (mono average), at 16 kHz."""
    x = np.asarray(x, dtype=float)
    if x.ndim == 2:
        x = x.mean(axis=1)
    if sr != SR:
        g = math.gcd(int(sr), SR)
        x = sps.resample_poly(x, SR // g, int(sr) // g)
    return x


def yin(x: np.ndarray, sr: int = SR, fmin: float = 60.0, fmax: float = 600.0, win: float = 0.025,
        hop: float = 0.01, thresh: float = 0.15, gate_db: float = -45.0):
    """Pitch every `hop` seconds by YIN (de Cheveigne and Kawahara, 2002): (frame centres in s, f0 in Hz with NaN
    where unvoiced, aperiodicity 0..1). A frame is voiced when its normalised difference dips under `thresh` and it
    is within `gate_db` of the loudest frames."""
    x = np.asarray(x, dtype=float)
    w, tmax, tmin, h = int(win * sr), int(sr / fmin), max(2, int(sr / fmax)), max(1, int(hop * sr))
    if len(x) < w + tmax + 1:
        return np.zeros(0), np.zeros(0), np.zeros(0)
    n = 1 + (len(x) - w - tmax) // h
    idx = np.arange(n)[:, None] * h + np.arange(w + tmax)[None, :]
    fr = x[idx]
    size = 1 << int(math.ceil(math.log2(2 * (w + tmax))))
    r = np.fft.irfft(np.conj(np.fft.rfft(fr[:, :w], size)) * np.fft.rfft(fr, size), size)[:, :tmax + 1]
    sq = np.concatenate([np.zeros((n, 1)), np.cumsum(fr ** 2, axis=1)], axis=1)
    taus = np.arange(tmax + 1)
    d = sq[:, [w]] + (sq[:, taus + w] - sq[:, taus]) - 2 * r
    d[:, 0] = 0.0
    d = np.maximum(d, 0.0)
    cum = np.cumsum(d[:, 1:], axis=1)
    cm = np.ones_like(d)
    cm[:, 1:] = d[:, 1:] * taus[1:] / np.maximum(cum, 1e-12)
    sub = cm[:, tmin:tmax + 1]
    rows = np.arange(n)
    below = sub < thresh
    has = below.any(axis=1)
    k = np.where(has, below.argmax(axis=1), sub.argmin(axis=1))
    last = sub.shape[1] - 1
    for _ in range(last):
        nxt = np.minimum(k + 1, last)
        move = has & (k < last) & (sub[rows, nxt] < sub[rows, k])
        if not move.any():
            break
        k = np.where(move, k + 1, k)
    a = sub[rows, np.maximum(k - 1, 0)]
    b = sub[rows, k]
    c = sub[rows, np.minimum(k + 1, last)]
    den = a - 2 * b + c
    shift = np.where((k > 0) & (k < last) & (np.abs(den) > 1e-12), 0.5 * (a - c) / np.where(den == 0, 1, den), 0.0)
    f0 = sr / (k + tmin + np.clip(shift, -1, 1))
    rms = np.sqrt(sq[:, w] / w)
    loud = 20 * np.log10(np.maximum(rms, 1e-12))
    ok = has & (loud > np.percentile(loud, 95) + gate_db) & (loud > -60.0)  # digital silence isn't 615 Hz
    f0 = np.where(ok, f0, np.nan)
    times = (rows * h + w / 2) / sr
    return times, f0, b


def pitch(x: np.ndarray, sr: int, spans=None, thresh: float = 0.25, least: float = 0.12) -> dict:
    """Median pitch, its 10th and 90th percentiles and the spread between them in semitones, over the voiced frames
    (inside `spans`, a list of (start, end) seconds, when given). The voicing threshold is looser than YIN's usual
    0.15, which voiced only 8 frames of a deep, creaky punch line (S5 review); under `least` seconds voiced, the
    median is None: too little to say."""
    t, f0, _ = yin(mono16k(x, sr), thresh=thresh)
    keep = ~np.isnan(f0)
    if spans:
        inside = np.zeros(len(t), bool)
        for s, e in spans:
            inside |= (t >= s) & (t <= e)
        keep &= inside
    v = f0[keep]
    if len(v) * 0.01 < least:
        return {"median": None, "p10": None, "p90": None, "spread_st": None, "voiced_s": round(len(v) * 0.01, 2)}
    p10, med, p90 = np.percentile(v, [10, 50, 90])
    return {"median": round(float(med), 1), "p10": round(float(p10), 1), "p90": round(float(p90), 1),
            "spread_st": round(float(12 * math.log2(p90 / p10)), 2), "voiced_s": round(len(v) * 0.01, 2)}


def frames_db(x: np.ndarray, sr: int, frame: float = 0.01) -> np.ndarray:
    """Each 10 ms frame's level in dBFS (mono, high-passed at 40 Hz so rumble doesn't count as speech, while a deep
    voice's fundamental and a creaky tail still do)."""
    x = np.asarray(x, dtype=float)
    if x.ndim == 2:
        x = x.mean(axis=1)
    x = sps.sosfilt(sps.butter(2, 40, "highpass", fs=sr, output="sos"), x)
    f = max(1, int(frame * sr))
    n = len(x) // f
    if n == 0:
        return np.zeros(0)
    p = (x[: n * f].reshape(n, f) ** 2).mean(axis=1)
    return 10 * np.log10(np.maximum(p, 1e-14))


def level(x: np.ndarray, sr: int) -> float:
    """Active speech level in dB (K-weighted, like LUFS): the mean power of the 20 ms frames within 25 dB of the
    loudest ones, so pauses and short lines don't drag it down."""
    import master
    x = np.asarray(x, dtype=float)
    if x.ndim == 2:
        x = x.mean(axis=1)
    y = sps.sosfilt(master.k_weighting(sr), x)
    f = int(0.02 * sr)
    n = len(y) // f
    if n == 0:
        return -120.0
    p = (y[: n * f].reshape(n, f) ** 2).mean(axis=1)
    db = 10 * np.log10(np.maximum(p, 1e-20))
    act = p[db > np.percentile(db, 95) - 25]
    return float(-0.691 + 10 * np.log10(act.mean()))


def pauses(x: np.ndarray, sr: int, below_db: float = 32.0, least: float = 0.05) -> list[tuple[float, float]]:
    """Quiet stretches inside the speech (not before the first sound or after the last): runs of 10 ms frames more
    than `below_db` under the loudest frames, at least `least` seconds long, as (start, end) seconds."""
    db = frames_db(x, sr)
    if not len(db):
        return []
    quiet = db < np.percentile(db, 95) - below_db
    loud = np.flatnonzero(~quiet)
    if not len(loud):
        return []
    out, start = [], None
    for i in range(loud[0], loud[-1] + 1):
        if quiet[i] and start is None:
            start = i
        elif not quiet[i] and start is not None:
            if (i - start) * 0.01 >= least:
                out.append((round(start * 0.01, 3), round(i * 0.01, 3)))
            start = None
    return out


def edges(x: np.ndarray, sr: int, below_db: float = 40.0) -> tuple[float, float]:
    """Seconds of near-silence before the first sound and after the last."""
    db = frames_db(x, sr)
    if not len(db):
        return 0.0, 0.0
    loud = np.flatnonzero(db > np.percentile(db, 95) - below_db)
    if not len(loud):
        return len(db) * 0.01, 0.0
    return round(loud[0] * 0.01, 3), round((len(db) - 1 - loud[-1]) * 0.01, 3)


def spoken(text: str) -> list[str]:
    """The words a line says, as written: audio tags like [excited] dropped, split at spaces, hyphens, dashes and
    ellipses ('forty-slide' is two words, 'Wait, WHAT?' two)."""
    return [w for w in _SPLIT.split(TAG.sub(" ", text)) if norm(w)]


_ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "     "seventeen eighteen nineteen".split()
_TENS = "twenty thirty forty fifty sixty seventy eighty ninety".split()


def number_words(n: int) -> str:
    """An integer under a million in words, space-separated ('forty', 'twenty one', 'one hundred five')."""
    if n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10 - 2] + (" " + _ONES[n % 10] if n % 10 else "")
    if n < 1000:
        return _ONES[n // 100] + " hundred" + (" " + number_words(n % 100) if n % 100 else "")
    return number_words(n // 1000) + " thousand" + (" " + number_words(n % 1000) if n % 1000 else "")


def norm(word: str) -> str:
    """A word for matching: lower case, letters, digits and apostrophes only, a number spelled out, so the
    transcriber's '40' matches the script's 'forty'."""
    w = re.sub(r"[^a-z0-9']", "", word.lower().replace("’", "'")).strip("'")
    if w.isdigit() and len(w) < 7:
        return number_words(int(w)).replace(" ", "")
    return w


_SPLIT = re.compile(r"[\s\-–—]+|\.{2,}|…")


# Words a transcriber can't tell apart by sound: matched as one (S5's "Seen." came back as "Scene.").
HOMOPHONES = {w: group[0] for group in (
    ("seen", "scene"), ("there", "their", "theyre"), ("to", "too", "two"), ("your", "youre"), ("its", "it's"),
    ("no", "know"), ("right", "write"), ("here", "hear"), ("for", "four"), ("one", "won"), ("eight", "ate"),
    ("by", "buy", "bye"), ("new", "knew"), ("whole", "hole"), ("weak", "week"), ("wait", "weight"),
    ("sun", "son"), ("meet", "meat"), ("which", "witch"), ("ok", "okay"), ("alright", "allright"))
    for w in group}


def tokens(text: str) -> list[str]:
    """A line's words for matching: split at spaces, hyphens, dashes and ellipses; a number becomes its words, one
    token each ('21' -> 'twenty', 'one'), as a script that spells it out reads."""
    out = []
    for w in _SPLIT.split(text):
        n = re.sub(r"[^a-z0-9']", "", w.lower().replace("’", "'")).strip("'")
        if not n:
            continue
        if n.isdigit() and len(n) < 7:
            out += number_words(int(n)).split()
        else:
            out.append(HOMOPHONES.get(n.replace("'", ""), n))
    return out


def match(text: str, heard: list[dict]) -> dict:
    """How many of the script's words the transcript heard, in order: {"ratio", "missing", "extra"}."""
    a = tokens(TAG.sub(" ", text))
    b = [t for w in heard for t in tokens(w["word"])]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    got = set()
    hit = set()
    for blk in sm.get_matching_blocks():
        got.update(range(blk.a, blk.a + blk.size))
        hit.update(range(blk.b, blk.b + blk.size))
    return {"ratio": round(len(got) / len(a), 3) if a else 1.0,
            "missing": [a[i] for i in range(len(a)) if i not in got],
            "extra": [b[i] for i in range(len(b)) if i not in hit]}


def runs(words: list[dict], gap: float = 0.35) -> list[list[dict]]:
    """Words grouped into runs of speech, split where the gap between two words is `gap` seconds or more."""
    out: list[list[dict]] = []
    for w in words:
        if out and w["start"] - out[-1][-1]["end"] < gap:
            out[-1].append(w)
        else:
            out.append([w])
    return out


def rates(words: list[dict], gap: float = 0.35) -> dict:
    """Words a second over the whole span, and inside runs of speech only (pauses of `gap` s or more left out), with
    the gaps between words inside runs (median and 90th percentile, seconds)."""
    if len(words) < 2:
        return {"words": len(words)}
    span = words[-1]["end"] - words[0]["start"]
    rs = runs(words, gap)
    talk = sum(r[-1]["end"] - r[0]["start"] for r in rs)
    inner = [b["start"] - a["end"] for r in rs for a, b in zip(r, r[1:])]
    inner = [g for g in inner if g >= 0]
    return {"words": len(words), "per_s": round(len(words) / span, 2) if span > 0 else None,
            "in_runs_per_s": round(len(words) / talk, 2) if talk > 0 else None,
            "gap_median": round(float(np.median(inner)), 3) if inner else 0.0,
            "gap_p90": round(float(np.percentile(inner, 90)), 3) if inner else 0.0,
            "pauses": sum(1 for a, b in zip(words, words[1:]) if b["start"] - a["end"] >= gap)}


def _words_of(transcript: str) -> list[dict]:
    d = json.load(open(transcript, encoding="utf-8"))
    return [w for s in d["segments"] for w in s["words"]]


def refs(videos: list[str], words_dir: str, out_dir: str) -> list[dict]:
    import media
    rows = []
    for v in videos:
        name = os.path.splitext(os.path.basename(v))[0]
        tr = os.path.join(words_dir, name + ".json")
        if not os.path.exists(tr):
            continue
        words = _words_of(tr)
        if len(words) < 10:  # a music video: lyrics only, or none
            continue
        x, sr = media.audio(v)
        row = {"video": name[:3], "pitch": pitch(x, sr, [(w["start"], w["end"]) for w in words]),
               "rate": rates(words)}
        rows.append(row)
        p, r = row["pitch"], row["rate"]
        print(f"{name[:3]}: pitch {p['median']} Hz ({p['p10']}-{p['p90']}, {p['spread_st']} st); "
              f"{r['per_s']} words/s, {r['in_runs_per_s']} in runs; gaps {r['gap_median']}/{r['gap_p90']} s; "
              f"{r['pauses']} pauses", flush=True)
    os.makedirs(out_dir, exist_ok=True)
    json.dump(rows, open(os.path.join(out_dir, "refs.json"), "w", encoding="utf-8"), indent=1)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("refs")
    r.add_argument("videos", nargs="+")
    r.add_argument("--words", default="refs/r6rants/transcripts")
    r.add_argument("--out", default="build/speech")
    f = sub.add_parser("file")
    f.add_argument("audio", nargs="+")
    args = ap.parse_args()
    if args.cmd == "refs":
        vids = [p for a in args.videos for p in (glob.glob(a) or [a])]
        refs(vids, args.words, args.out)
        return 0
    import media
    for path in args.audio:
        x, sr = media.audio(path)
        lead, tail = edges(x, sr)
        ps = pauses(x, sr)
        print(f"{os.path.basename(path)}: {len(x) / sr:.2f} s, pitch {pitch(x, sr)}, level {level(x, sr):.1f} dB, "
              f"lead {lead:.2f} s, tail {tail:.2f} s, longest pause {max((b - a for a, b in ps), default=0):.2f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
