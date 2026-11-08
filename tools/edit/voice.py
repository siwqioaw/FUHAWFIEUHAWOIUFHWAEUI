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
import os
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "verify"))
import speech  # noqa: E402

SR = 48000
HEAR_PAD = 0.5   # seconds of silence put before a line for the transcriber, so it hears the first sound
CAST = os.path.join(HERE, "voices.json")


def fetch(url: str, dest: str, timeout: float = 120.0) -> str:
    """Download a take to `dest`. The URL is a signed link from the connector; nothing else is sent."""
    import requests
    from urllib.parse import urlsplit
    os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
    try:
        r = requests.get(url, timeout=timeout)
    except requests.RequestException as e:
        raise RuntimeError(f"download from {urlsplit(url).netloc} failed: {type(e).__name__}") from None
    if r.status_code != 200:  # the signed URL's signature is a credential: never print it
        raise RuntimeError(f"download from {urlsplit(url).netloc} failed: HTTP {r.status_code}")
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


def _islands(mask: np.ndarray) -> list[tuple[int, int]]:
    """Runs of True in a boolean array, as (start, end) indices, end exclusive."""
    out, start = [], None
    for i, v in enumerate(list(mask) + [False]):
        if v and start is None:
            start = i
        elif not v and start is not None:
            out.append((start, i))
            start = None
    return out


def quiet_spans(x: np.ndarray, sr: int, silence_db: float = 40.0, breath_db: float = 18.0,
                breath_min: float = 0.12, floor_db: float = 32.0) -> list[tuple[int, int]]:
    """Runs of 10 ms frames of silence between the first and the last sound: frame indices, end exclusive.

    Silence is more than `silence_db` under the loudest frames. A breath counts too, but only as an island: at least
    `breath_min` seconds of unvoiced sound more than `breath_db` under the loudest frames with silence on both sides.
    A creaky tail is joined to the word before it and an 'h' to the word after, so neither is an island and neither
    is cut: the S5 review found a looser rule cutting the ends off words, and 32 dB taking a creaky decay for
    silence.

    And the floor wobbling round the silence line: in a stretch more than `floor_db` under the loudest frames (what
    `speech.pauses` calls a pause), everything from its first 30 ms of silence to its last is silence. M5's gaps
    between sentences sat at 38-42 dB under, broken into pieces too short to cut, and failed the pause check at 0.2 s.
    A word's decay before that first silence and an onset after the last are kept as before."""
    db = speech.frames_db(x, sr)
    if not len(db):
        return []
    top = np.percentile(db, 95)
    silent = db < top - silence_db
    quiet = db < top - floor_db

    def fill() -> None:
        for a, b in _islands(quiet):
            runs = [(a + i, a + j) for i, j in _islands(silent[a:b]) if j - i >= 3]   # silence of 30 ms or more
            if runs:   # a dip of a frame or two inside a creaky decay starts nothing (the S5 case)
                silent[runs[0][0]:runs[-1][1]] = True

    t, f0, _ = speech.yin(speech.mono16k(x, sr), thresh=0.3)
    voiced = np.zeros(len(db), bool)
    if len(t):
        idx = np.clip(np.round(t / 0.01 - 0.5).astype(int), 0, len(db) - 1)
        voiced[idx[~np.isnan(f0)]] = True
    fill()
    for a, b in _islands(~silent):
        bounded = a >= 3 and b <= len(db) - 3 and silent[a - 3:a].all() and silent[b:b + 3].all()
        if bounded and (b - a) * 0.01 >= breath_min and db[a:b].max() < top - breath_db \
                and voiced[a:b].mean() < 0.2:
            silent[a:b] = True  # an island of breath between two silences
    fill()
    loud = np.flatnonzero(~silent)
    out, start = [], None
    if not len(loud):
        return out
    for i in range(loud[0], loud[-1] + 2):
        q = i <= loud[-1] and silent[i]
        if q and start is None:
            start = i
        elif not q and start is not None:
            out.append((start, i))
            start = None
    return out


def tighten(x: np.ndarray, sr: int, keep: float = 0.07, xfade: float = 0.01, tail: float = 0.6) -> tuple:
    """Cut every silence between words down to `keep` seconds: `tail` of it kept after the word before (its decay),
    the rest before the next word (its onset), joined with an `xfade`-second crossfade inside the silence. Returns
    (audio, [(start, end) seconds removed, in the input's time]). A deliberate pause is the edit's job: split the
    line in two and leave the gap in the shot's timing."""
    f = int(0.01 * sr)
    xf = max(1, int(xfade * sr))
    k = int(keep * sr)
    head_n = int(k * tail)
    tail_n = k - head_n
    cuts = []
    for a, b in quiet_spans(x, sr):
        s0, s1 = a * f, b * f
        c0, c1 = s0 + head_n, s1 - tail_n + xf
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
    return out, [(c0 / sr, (c1 - xf) / sr) for c0, c1 in cuts]


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
              max_limit_db: float = 4.0, max_gain_db: float = 36.0) -> tuple[np.ndarray, float]:
    """Gain to an active speech level of `target_db`; peaks over `ceiling_db` (true peak) go through the look-ahead
    limiter, up to `max_limit_db` of it, past which the gain backs off. The level is measured again after the limiter
    and put right once more. Deep voices need the limiter: K-weighting hears little of their low end, so their peaks
    sit high over their level. A take with no speech in it raises."""
    import master
    lv = speech.level(x, sr)
    if lv < -70:
        raise ValueError(f"no speech to level (active level {lv:.0f} dB)")
    g = min(max_gain_db, target_db - lv)
    y = x * 10 ** (g / 20)
    for _ in range(2):
        over = master.true_peak_db(y[:, None]) - ceiling_db
        if over > max_limit_db:
            y = y * 10 ** (-(over - max_limit_db) / 20)
            g -= over - max_limit_db
        if over > 0:
            y = master.limiter(y[:, None], sr, ceiling_db - 0.05)[:, 0]
        fix = min(max_gain_db - g, target_db - speech.level(y, sr))
        if abs(fix) < 0.05:
            break
        y = y * 10 ** (fix / 20)
        g += fix
    if master.true_peak_db(y[:, None]) > ceiling_db:
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


UNVOICED_START = ("f", "s", "h", "p", "t", "k", "c", "th", "sh", "ch", "wh", "x")


def voiced_runs(y: np.ndarray, sr: int, least: float = 0.03, gap: float = 0.04, within_db: float = 30.0) -> list:
    """Stretches of voiced speech: YIN-voiced frames within `within_db` of the loudest, joined across gaps under
    `gap` s, at least `least` s long, as [start, end] seconds."""
    t, f0, _ = speech.yin(speech.mono16k(y, sr), thresh=0.3)
    if not len(t):
        return []
    db = speech.frames_db(y, sr)
    top = np.percentile(db, 95)
    idx = np.clip(np.round(t / 0.01 - 0.5).astype(int), 0, len(db) - 1)
    v = ~np.isnan(f0) & (db[idx] > top - within_db)
    runs, start = [], None
    for k in range(len(t)):
        if v[k] and start is None:
            start = float(t[k])
        elif not v[k] and start is not None:
            runs.append([start, float(t[k])])
            start = None
    if start is not None:
        runs.append([start, float(t[-1])])
    merged = []
    for r in runs:
        if merged and r[0] - merged[-1][1] < gap:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    return [r for r in merged if r[1] - r[0] >= least]


def _phrase_openers(words: list[dict], text: str | None) -> list[bool]:
    """For each heard word: does it open a phrase (follow a comma or a sentence's end)? By the script's punctuation
    where the script's words match the heard ones, else by the transcriber's."""
    import difflib
    ends = ".!?,;:…"
    heard = [speech.norm(w["word"]) for w in words]
    out = [i > 0 and words[i - 1]["word"].rstrip("\"')")[-1:] in ends for i in range(len(words))]
    if not text:
        return out
    script = speech.spoken(text)
    a = [speech.norm(w) for w in script]
    for blk in difflib.SequenceMatcher(a=a, b=heard, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            ai, bi = blk.a + k, blk.b + k
            if bi > 0:
                out[bi] = ai > 0 and script[ai - 1].rstrip("\"')")[-1:] in ends
    return out


def _sound_onset(db: np.ndarray, top: float, t: float, most: float = 0.3, quiet_db: float = 30.0):
    """Where the sound before a voiced stretch starting at t begins: back from t over 10 ms frames, the first
    frame after the last quiet one (more than `quiet_db` under the loudest), within `most` seconds; None when the
    sound runs on further back. A phrase's first word follows a pause, so its consonant starts right after the quiet:
    on M5 this found "cats", "because" and "Like" within 0.01 s of the reviewer's measured onsets."""
    i = int(round(t / 0.01))
    for k in range(1, int(most / 0.01) + 1):
        j = i - k
        if j < 0:
            return 0.0
        if j < len(db) and db[j] < top - quiet_db:
            return round((j + 1) * 0.01, 3)
    return None


def refine_words(words: list[dict], y: np.ndarray, sr: int, text: str | None = None,
                 least_shift: float = 0.1) -> list[dict]:
    """Word starts moved to where the word's sound begins. The transcriber starts a word straight after the one
    before, over a pause, a held vowel or a scoff between them (M3's review: "for" timed 0.6 s before it was said, so
    its caption and a face keyed to it came early). Only words that open a phrase (after a comma or a sentence's
    end) are moved: that's where the pauses and breaths are, and inside a quick phrase the voicing measure misses
    reduced syllables. The phrase breaks are the script's (`text`), matched to the heard words: the transcriber
    drops punctuation ("The title page. For..." heard as "the title page for"). Such a word starts at its own voiced
    stretch instead when it:

    - starts inside the voicing of the word before (begun more than 0.06 s earlier) or in a gap: the first voiced
      stretch inside it;
    - holds two voiced stretches more than 0.15 s apart (a sound, a pause, then the word): the later one;
    - holds no voicing at all (the word is later than the transcriber says): the next voiced stretch, within 0.8 s.

    The start is then where the sound before that voicing begins, back to the last quiet frame (`_sound_onset`),
    or, with no quiet frame within 0.3 s, 0.05 s before it for a word opening on an unvoiced consonant (0.02
    otherwise); only when the voicing is 0.1 s or more later. Starts only move later, and stay in order; an end is
    pushed past its start when it has to be."""
    runs = voiced_runs(y, sr)
    db = speech.frames_db(y, sr)
    top = np.percentile(db, 95) if len(db) else 0.0
    out = [dict(w) for w in words]
    opens = _phrase_openers(words, text)
    for i, w in enumerate(out):
        if not opens[i]:
            continue
        s, e = w["start"], w["end"]
        inside = next((r for r in runs if r[0] <= s < r[1]), None)
        later = [r for r in runs if s < r[0] <= e - 0.05]
        touching = [r for r in runs if r[0] < e and r[1] > s]
        target = None
        if not touching:
            nxt = next((r[0] for r in runs if s < r[0] <= s + 0.8), None)
            if nxt is not None and speech.norm(w["word"]).strip("0123456789"):
                target = nxt
        elif inside is None or s - inside[0] > 0.06:
            target = later[0][0] if later else None
        group = ([inside] if inside else []) + later
        for a, b in zip(group, group[1:]):
            if b[0] - a[1] >= 0.15:
                target = b[0]
        if target is None or target - s < least_shift:
            continue
        onset = _sound_onset(db, top, target)   # back from the voicing to where the sound starts: an unvoiced
        if onset is None:                       # or soft first consonant (M5's review: "Like" 0.13 s late)
            onset = target - (0.05 if speech.norm(w["word"]).startswith(UNVOICED_START) else 0.02)
        w["start"] = round(max(s, onset), 3)
        if touching:
            w["start"] = round(min(w["start"], s + 0.8 * (e - s)), 3)
        w["end"] = round(max(e, w["start"] + 0.08), 3)
        for later_w in out[i + 1:]:   # the words after it can't start before it does
            if later_w["start"] >= w["start"] + 0.03:
                break
            later_w["start"] = round(w["start"] + 0.03, 3)
            later_w["end"] = round(max(later_w["end"], later_w["start"] + 0.05), 3)
    return out


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
    extra = m["match"].get("extra", [])
    out.append((not extra, "no words that aren't in the script (a tag read aloud, a repeat)" + (
        f": heard {extra}" if extra else "")))
    out.append((m["lead"] <= 0.05 and m["tail"] <= 0.15, f"starts within 50 ms and ends within 150 ms of its sound "
                f"({m['lead']:.3f}, {m['tail']:.3f} s)"))
    most = line.get("max_pause", role.get("max_pause", 0.2))
    out.append((m["longest_pause"] <= most, f"no pause over {most:.2f} s ({m['longest_pause']:.2f})"))
    lo, hi = role.get("pitch", [0, 10000])
    med = m["pitch"]["median"]
    if med is None:  # too few voiced frames to say (a whisper, a short deep punch): noted, not failed
        out.append((True, f"median pitch: too little voicing to measure ({m['pitch']['voiced_s']} s)"))
    else:
        out.append((lo <= med <= hi, f"median pitch in {lo}-{hi} Hz ({med})"))
        if role.get("center"):
            # The same voice, not another: a read can rise a long way (a shout) but an octave down sounds like
            # someone else (M3's review: two narrator lines at 99-105 Hz against his 212-224).
            down, up = role.get("register_st", [-7, 9])
            st = 12 * np.log2(med / role["center"])
            out.append((down <= st <= up, f"in the voice's own register: {st:+.1f} semitones from its "
                        f"{role['center']} Hz (allowed {down} to +{up})"))
    if role.get("rate") and m["words_per_s"] is not None:
        rlo, rhi = role["rate"]
        out.append((rlo <= m["words_per_s"] <= rhi, f"{rlo}-{rhi} words a second ({m['words_per_s']})"))
    target = role.get("level_db", -18.0)
    out.append((abs(m["level_db"] - target) <= 0.6 and m["true_peak_db"] <= -1.0 + 0.05,
                f"speech level {target} dB ({m['level_db']}), true peak at most -1 dBTP ({m['true_peak_db']})"))
    return [(bool(ok), what) for ok, what in out]


# Bump when processing or hearing changes, so takes processed the old way are done again.
PROCESS_VERSION = 2   # 2: the floor-wobble rule in quiet_spans; the transcriber hears a padded copy


def _cache_key(take: str, role: dict) -> str:
    import hashlib
    st = os.stat(take)
    keep = {k: role.get(k) for k in ("keep", "tempo", "tempo_method", "level_db")}
    return hashlib.sha1(json.dumps([os.path.abspath(take), st.st_size, int(st.st_mtime), keep, PROCESS_VERSION],
                                   sort_keys=True).encode()).hexdigest()[:16]


def _cache_get(out_dir: str, take: str, role: dict):
    """A take already processed and transcribed with the same settings: (audio, info, words), or None."""
    base = os.path.join(out_dir, ".cache", _cache_key(take, role))
    if not (os.path.exists(base + ".wav") and os.path.exists(base + ".json")):
        return None
    y, _ = sf.read(base + ".wav", dtype="float64")
    meta = json.load(open(base + ".json", encoding="utf-8"))
    return y, meta["info"], meta["words"]


def _cache_put(out_dir: str, take: str, role: dict, y, info: dict, words: list) -> None:
    os.makedirs(os.path.join(out_dir, ".cache"), exist_ok=True)
    base = os.path.join(out_dir, ".cache", _cache_key(take, role))
    sf.write(base + ".wav", y.astype(np.float32), SR, subtype="FLOAT")
    json.dump({"info": info, "words": words}, open(base + ".json", "w", encoding="utf-8"))


def _cast_path(cast: str | None, base: str) -> str | None:
    if not cast or os.path.isabs(cast):
        return cast
    here = os.path.join(os.getcwd(), cast)
    return here if os.path.exists(here) else os.path.join(base, cast)


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
    cast = load_cast(_cast_path(spec.get("cast"), base))
    os.makedirs(out_dir, exist_ok=True)
    import transcribe
    asr, dev = None, "the cache"   # loaded at the first take that isn't cached: it needs about 3 GB


    def hear(path: str, pad: float = HEAR_PAD) -> list[dict]:
        """The words in a processed line, heard from a copy with `pad` seconds of silence before it (a soft first
        consonant at time 0 goes unheard: M5's "She aced" came back "He aced"), timed in the line's own time."""
        nonlocal asr, dev
        if asr is None:
            asr, dev = transcribe.load(model, device)
        y, rate = sf.read(path, dtype="float32")
        fd, padded = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            sf.write(padded, np.concatenate([np.zeros((int(pad * rate),) + y.shape[1:], np.float32), y]), rate,
                     subtype="FLOAT")
            try:
                res = transcribe.run(asr, padded, "en")
            except RuntimeError:  # the GPU libraries fail at the first inference, not at load
                if dev != "cuda":
                    raise
                import gc
                asr = None   # let the GPU copy go before loading the CPU one: both at once ran out of memory
                gc.collect()
                asr, dev = transcribe.load(model, "cpu")
                res = transcribe.run(asr, padded, "en")
        finally:
            os.remove(padded)
        return [{**w, "start": round(max(0.0, w["start"] - pad), 3), "end": round(max(0.0, w["end"] - pad), 3)}
                for s in res["segments"] for w in s["words"]]

    entries, fails, rows = [], 0, []
    for line in spec["lines"]:
        role = {**cast.get("defaults", {}), **cast["roles"][line["role"]], **line.get("process", {})}
        tried = []
        for i, take in enumerate(_take_paths(line, base)):
            dest = os.path.join(out_dir, f"{line['id']}.take{i}.wav")
            cached = _cache_get(out_dir, take, role)
            if cached:
                y, info, words = cached
                sf.write(dest, y.astype(np.float32), SR, subtype="PCM_24")
            else:
                y, info = process(decode(take), SR, role)
                sf.write(dest, y.astype(np.float32), SR, subtype="PCM_24")
                words = hear(dest)
                _cache_put(out_dir, take, role, y, info, words)
            words = refine_words(words, y, SR, line["text"])
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


def refine_file(out_dir: str) -> list[tuple[str, str, float]]:
    """Re-time an existing voice folder's words (`words.json`) against its own processed lines with `refine_words`,
    without processing or hearing anything again: for a video already shot, whose audio mustn't change. Keeps the
    transcriber's times as `heard_start`. Returns the moves: (line, word, seconds later)."""
    path = os.path.join(out_dir, "words.json")
    data = json.load(open(path, encoding="utf-8"))
    moves = []
    for ln in data["lines"]:
        y, sr = sf.read(os.path.join(out_dir, ln["file"]), dtype="float64")
        raw = [{**w, "start": w.get("heard_start", w["start"])} for w in ln["words"]]
        new = refine_words(raw, y, sr, ln.get("text"))
        for w, r, n in zip(ln["words"], raw, new):
            w["heard_start"] = r["start"]
            if abs(n["start"] - r["start"]) > 1e-6:
                moves.append((ln["id"], w["word"], round(n["start"] - r["start"], 3)))
            w["start"], w["end"] = n["start"], n["end"]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    return moves


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
    rf = sub.add_parser("refine", help="re-time an existing voice folder's words.json against its own lines")
    rf.add_argument("out", help="the voice folder: build/<slug>/voice")
    args = ap.parse_args()
    if args.cmd == "refine":
        for lid, word, dt in refine_file(args.out):
            print(f"{lid}: {word!r} {dt:+.2f} s")
        return 0
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
