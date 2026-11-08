"""Make a Short from its spec, every stage checked: videos/<slug>/short.json -> out/<slug>.mp4 (docs/MAKING.md).

    python tools/make.py voice   videos/<slug>   # the takes in build/<slug>/takes.json -> processed, timed lines
    python tools/make.py plan    videos/<slug>   # every shot, line, caption, face, pose, hit in time -> cut.json
    python tools/make.py stills  videos/<slug>   # a frame of each shot from Studio, to look at before the shoot
    python tools/make.py shoot   videos/<slug>   # every shot from Studio, a frame at a time (resumes)
    python tools/make.py cut     videos/<slug>   # master.mov: the frames, captions, streaked swoops
    python tools/make.py mix     videos/<slug>   # mix.wav: voices, effects, music, mastered
    python tools/make.py deliver videos/<slug>   # out/<slug>.mp4, then every check on it
    python tools/make.py all     videos/<slug>   # plan to deliver, stopping at the first FAIL

The voice takes come from the ElevenLabs connector, which only an agent session can call: the agent generates each
line (docs/VOICE.md) and writes `build/<slug>/takes.json`, {line id: [take URL or file, ...]}, before `voice`.
The shoot needs Roblox Studio open on the left monitor in the capture layout, with the bridge running
(docs/ROBLOX_CAPTURE.md).
"""

from __future__ import annotations

import argparse
import functools
import json
import math
import os
import re
import subprocess
import sys
import time

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for _sub in ("edit", "verify", "roblox"):
    sys.path.insert(0, os.path.join(ROOT, "tools", _sub))

CAPTION_STYLE = {"comedy": "comedy", "story": "story", "music": "header"}
OFF = [0.0, 3.0, 400.0]  # actors not in a shot wait far behind the camera, a stud apart
HEAD, FACE = 1.5, 0.6  # an R6 actor's head centre above its torso centre; the face in front of the head


# ---------------------------------------------------------------------------------------------------- the spec


class Short:
    """One video: its spec and where everything it makes goes."""

    def __init__(self, vdir: str):
        self.vdir = os.path.abspath(vdir)
        with open(os.path.join(self.vdir, "short.json"), encoding="utf-8") as f:
            self.spec = json.load(f)
        self.slug = self.spec.get("slug") or os.path.basename(self.vdir.rstrip("/\\"))
        self.fps = int(self.spec.get("fps", 60))
        self.family = self.spec.get("family", "comedy")
        self.build = os.path.join(ROOT, "build", self.slug)
        os.makedirs(self.build, exist_ok=True)

    def path(self, *parts: str) -> str:
        return os.path.join(self.build, *parts)

    @property
    def out(self) -> str:
        return os.path.join(ROOT, "out", self.slug + ".mp4")

    def lines(self) -> dict:
        return {ln["id"]: ln for ln in self.spec.get("lines", [])}


def _load(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)


# ---------------------------------------------------------------------------------------------------- voice


def _raw_name(lid: str, k: int, url: str) -> str:
    """The file a downloaded take is kept in: named by the take itself (its URL's path; the signature after it
    changes with every fetch), so a regenerated line downloads its new takes instead of reusing the old files."""
    import hashlib
    from urllib.parse import urlsplit
    return f"{lid}_{k}_{hashlib.sha1(urlsplit(url).path.encode()).hexdigest()[:8]}.mp3"


def stage_voice(sh: Short) -> bool:
    """Fetch each line's takes, process them, keep the best, time the words (tools/edit/voice.py)."""
    import voice
    takes_path = sh.path("takes.json")
    if not os.path.exists(takes_path):
        print(f"no {takes_path}: generate the lines with the ElevenLabs connector first (docs/VOICE.md)")
        return False
    takes = _load(takes_path)
    lines = []
    for ln in sh.spec.get("lines", []):
        srcs = takes.get(ln["id"])
        if not srcs:
            print(f"line {ln['id']}: no takes in {takes_path}")
            return False
        files = []
        for k, src in enumerate(srcs if isinstance(srcs, list) else [srcs]):
            if src.startswith("http"):
                dest = sh.path("raw", _raw_name(ln["id"], k, src))
                if not os.path.exists(dest):
                    voice.fetch(src, dest)
                files.append(dest)
            else:
                files.append(src if os.path.isabs(src) else os.path.join(ROOT, src))
        entry = {"id": ln["id"], "role": ln["role"], "text": ln["text"], "takes": files}
        for key in ("process", "max_pause"):
            if key in ln:
                entry[key] = ln[key]
        lines.append(entry)
    cast = sh.spec.get("voices", "tools/edit/voices.json")
    lines_path = sh.path("lines.json")
    _save(lines_path, {"cast": cast, "lines": lines})
    cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        fails = voice.make(lines_path, sh.path("voice"))
    finally:
        os.chdir(cwd)
    print(f"voice: {fails} failed checks ({sh.path('voice', 'report.md')})")
    return fails == 0


def _words(sh: Short) -> dict:
    if not sh.spec.get("lines"):  # a music-only video: nothing said
        return {}
    path = sh.path("voice", "words.json")
    if not os.path.exists(path):
        raise SystemExit(f"no {path}: run the voice stage first")
    return {e["id"]: e for e in _load(path)["lines"]}


# ---------------------------------------------------------------------------------------------------- time


_REF = re.compile(r"^(?P<line>[A-Za-z0-9_]+):(?P<what>[^+\-]+?)(?P<off>[+-]\d*\.?\d+)?$")


def _norm(w: str) -> str:
    import speech
    return speech.norm(w)


def _word_time(entry: dict, what: str) -> float:
    """A word's start (or end, 'WORD.end') in a processed line, the nth time it's said with 'WORD#n'."""
    end = what.endswith(".end")
    what = what[:-4] if end else what
    word, _, nth = what.partition("#")
    n = int(nth) if nth else 1
    target = _norm(word)
    seen = 0
    for w in entry["words"]:
        for part in w["word"].replace("-", " ").split():
            if _norm(part) == target:
                seen += 1
                if seen == n:
                    return w["end"] if end else w["start"]
    raise KeyError(f"line {entry['id']}: no word {word!r} (#{n}) in what was heard: {entry.get('heard')}")


def _resolve(ref, shot_start: float, line_starts: dict, words: dict) -> float:
    """A time inside a shot, in seconds from its start: a number, or 'line:start', 'line:end', 'line:WORD' (+/- s)."""
    if isinstance(ref, (int, float)):
        return float(ref)
    m = _REF.match(str(ref).strip())
    if not m:
        raise ValueError(f"can't read the time {ref!r}: a number, or line:start / line:end / line:WORD, +/- seconds")
    lid, what, off = m.group("line"), m.group("what"), float(m.group("off") or 0)
    if lid not in line_starts:
        raise ValueError(f"{ref!r}: line {lid} isn't said by this point")
    start = line_starts[lid]
    if what == "start":
        t = start
    elif what == "end":
        t = start + words[lid]["duration"]
    else:
        t = start + _word_time(words[lid], what)
    return t + off - shot_start


def _vec(v) -> list:
    return [float(x) for x in v]


def _actor_pos(shot: dict, name: str) -> list:
    a = shot.get("actors", {}).get(name)
    if not a:
        raise KeyError(f"shot {shot['name']}: camera aims at {name}, who isn't in it")
    return _vec(a.get("at", [0, 3, 0]))


def _actor_dir(shot: dict, name: str) -> list:
    a = shot["actors"][name]
    pos = _vec(a.get("at", [0, 3, 0]))
    if "look" in a:
        d = [a["look"][0] - pos[0], 0.0, a["look"][2] - pos[2]]
    else:
        d = _vec(a.get("facing", [0, 0, 1]))
    n = math.hypot(d[0], d[2]) or 1.0
    return [d[0] / n, 0.0, d[2] / n]


def _point(shot: dict, p) -> list:
    """A point: [x, y, z], or 'actor.head' / 'actor.face' / 'actor.torso' / 'actor.feet', with '+[dx,dy,dz]'."""
    if isinstance(p, (list, tuple)):
        return _vec(p)
    base, _, extra = str(p).partition("+")
    name, _, part = base.partition(".")
    pos = _actor_pos(shot, name)
    d = _actor_dir(shot, name)
    if part in ("", "torso"):
        out = pos
    elif part == "head":
        out = [pos[0], pos[1] + HEAD, pos[2]]
    elif part == "face":
        out = [pos[0] + d[0] * FACE, pos[1] + HEAD, pos[2] + d[2] * FACE]
    elif part == "feet":
        out = [pos[0], pos[1] - 3.0, pos[2]]
    else:
        raise ValueError(f"no point {p!r}")
    if extra:
        dx = json.loads(extra)
        out = [a + b for a, b in zip(out, dx)]
    return out


def _view(shot: dict, v: dict) -> dict:
    """A camera view from its spec (docs/MAKING.md, "Camera"): aim / pos+look / ots / low / top, then dutch, back."""
    import camera
    if "aim" in v:
        target = _point(shot, v["aim"])
        toward = v.get("toward")
        if v.get("between"):  # a two-shot: framed on the point between two heads, from the side both face
            name_b = v["between"].split(".")[0]
            other = _point(shot, name_b + ".head")
            target = [(p + q) / 2 for p, q in zip(target, other)]
            if toward is None:
                da, db = _actor_dir(shot, v["aim"].split(".")[0]), _actor_dir(shot, name_b)
                toward = [da[0] + db[0], 0.0, da[2] + db[2]]
                if math.hypot(toward[0], toward[2]) < 0.3:  # facing each other: from the side, +z first
                    line = [other[0] - target[0], 0.0, other[2] - target[2]]
                    toward = [-line[2], 0.0, line[0]]
                    if toward[2] < 0 or (abs(toward[2]) < 1e-6 and toward[0] < 0):
                        toward = [-toward[0], 0.0, -toward[2]]
        if toward is None and isinstance(v["aim"], str) and "." in v["aim"]:
            toward = _actor_dir(shot, v["aim"].split(".")[0])  # in front of whoever it aims at
        out = camera.aim(target, toward=toward or (0, 0, 1), distance=v.get("distance", 6.0),
                         height=v.get("height", 0.0), fov=v.get("fov", 45.0), roll=v.get("roll", 0.0))
    elif "pos" in v:
        out = camera.view(_vec(v["pos"]), _point(shot, v["look"]), roll=v.get("roll", 0.0), fov=v.get("fov", 45.0))
    elif "ots" in v:
        o = v["ots"]
        near, far = o["near"], o["far"]
        out = camera.ots(_point(shot, near + ".head"), _point(shot, far + ".face"), side=o.get("side", 1.5),
                         behind=o.get("behind", 2.8), up=o.get("up", 0.4), fov=o.get("fov", 45.0),
                         blur=o.get("blur", 0.6), lift=o.get("lift", 1.0))
    elif "low" in v:
        o = v["low"]
        target = _point(shot, o["aim"])
        toward = o.get("toward") or (_actor_dir(shot, o["aim"].split(".")[0]) if isinstance(o["aim"], str) else (0, 0, 1))
        out = camera.low(target, toward=toward, distance=o.get("distance", 5.0), eye=o.get("eye", 2.5),
                         fov=o.get("fov", 55.0))
    elif "top" in v:
        o = v["top"]
        out = camera.top(_point(shot, o["aim"]), height=o.get("height", 8.0), up=o.get("up", (0, 0, 1)),
                         fov=o.get("fov", 50.0))
    else:
        raise ValueError(f"shot {shot['name']}: a camera key needs aim, pos, ots, low or top: {v}")
    if v.get("dutch"):
        out = camera.dutch(out, v["dutch"])
    if v.get("back"):
        out = camera.back(out, v["back"])
    if v.get("orbit"):
        out = camera.orbit(out, v["orbit"])
    return out


def _root(token: str) -> str:
    """A word without the punctuation around it or a possessive 's: '"Max's,' -> 'Max'."""
    core = token.strip("\"'“”‘’()[],.!?;:…-—")
    return re.sub(r"['’]s$", "", core)


def _names(lines: dict) -> set:
    """The names in a script, kept capitalized where a caption starts with one: every word it capitalizes in the
    middle of a sentence ('so Leo stopped' makes 'Leo had never' keep its capital)."""
    import speech
    out = set()
    for ln in lines.values():
        toks = speech.TAG.sub("", ln.get("text", "")).split()
        for i, t in enumerate(toks):
            core = _root(t)
            if i and toks[i - 1][-1:] not in ".!?" and core[:1].isupper() and not core.isupper():
                out.add(core.lower())
    return out


def _lower_first(text: str, names=frozenset()) -> str:
    """Captions run in lower case: the first letter lowered, unless the first word is stressed (CAPS), 'I' or a
    name."""
    first = text.split(" ", 1)[0] if text else ""
    root = _root(first)
    if not root or root.isupper() or root == "I" or root.startswith(("I'", "I’")) or root.lower() in names:
        return text
    i = next((k for k, ch in enumerate(text) if ch.isalpha()), None)
    return text if i is None else text[:i] + text[i].lower() + text[i + 1:]


def _caption_text(line: dict, names=frozenset()) -> str:
    """A line's caption: its `caption`, or its text without tags, starting lower case unless its first word is
    stressed or a name, and its `emoji` at the end."""
    import speech
    if line.get("caption"):
        return line["caption"]
    text = speech.TAG.sub("", line["text"]).strip()
    text = _lower_first(re.sub(r"\s+", " ", text), names)
    return text + (" " + line["emoji"] if line.get("emoji") else "")


def _aligned_words(line: dict, entry: dict, names=frozenset()) -> list[tuple[str, float, float]]:
    """The script's words (its spelling, its CAPS) with the times the transcriber heard them at: matched words take
    their heard times, unmatched ones are spread between their neighbours."""
    import difflib

    import speech
    script = speech.spoken(_caption_text(line, names).replace("’", "'"))
    script = [w for w in script if not _is_emoji(w)]
    heard = [(p, w["start"], w["end"]) for w in entry["words"] for p in w["word"].replace("-", " ").split()
             if speech.norm(p)]
    a = [speech.norm(w) for w in script]
    b = [speech.norm(w) for w, _, _ in heard]
    times: list = [None] * len(script)
    for blk in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            times[blk.a + k] = (heard[blk.b + k][1], heard[blk.b + k][2])
    dur = entry["duration"]
    known = [i for i, t in enumerate(times) if t]
    for i, t in enumerate(times):
        if t:
            continue
        prev = max((j for j in known if j < i), default=None)
        nxt = min((j for j in known if j > i), default=None)
        lo = times[prev][1] if prev is not None else 0.0
        hi = times[nxt][0] if nxt is not None else dur
        gap_n = (nxt if nxt is not None else len(script)) - (prev if prev is not None else -1) - 1
        k = i - (prev if prev is not None else -1)
        times[i] = (lo + (hi - lo) * (k - 1) / gap_n, lo + (hi - lo) * k / gap_n)
    return [(w, s, e) for w, (s, e) in zip(script, times)]


def _is_emoji(token: str) -> bool:
    import captions
    return captions.is_emoji(token)


# A story caption shouldn't end on one of these (they belong with the word after: articles, determiners, possessives,
# prepositions, conjunctions), less so on a word that leans forward (only, never) or a subject.
WEAK_END = {"a", "an", "the", "this", "that", "these", "those", "every", "each", "some", "any", "most", "many", "few",
            "no", "another", "my", "your", "his", "her", "its", "our", "their", "to", "of", "at", "in", "on", "for",
            "with", "from", "into", "onto", "about", "through", "over", "under", "after", "before", "than", "as", "by",
            "between", "behind", "without", "and", "but", "or", "nor", "because", "if"}
LEAN_END = {"only", "just", "even", "very", "really", "not", "never", "so", "too"}
SUBJECT_END = {"he", "she", "they", "we", "i"}


def _story_groups(seg: list) -> list[list]:
    """One phrase (words up to a punctuation mark) split into story captions of 1-3 words (each at most two lines),
    the split that costs least: a caption per group, more for one ending before the phrase does on 'a', 'the', 'to',
    'about'... (3), on 'only' or 'never' (1), on a possessive before its noun (1) or on a subject (0.5), for a word
    left alone (2 at the start, 1.5 at the end), for one the read-time check would fail (4; 1.5 if `_balance` can
    lend it the time) and one quicker than nine in ten of the references' (1). Four
    words cost 2 more: the references use them now and then (006: 'They turned around to'), so one is used where
    three would leave a word alone. 'you hear a | ding.' becomes 'you hear | a ding.'; 'most people hear | a few a |
    day.' becomes 'most people | hear a few | a day.'; 'at the school | dance,' becomes 'at the school dance,'."""
    import captions
    import qc
    import speech
    n = len(seg)
    best, back = [0.0] + [math.inf] * n, [0] * (n + 1)
    for j in range(1, n + 1):
        for k in range(max(0, j - 4), j):
            grp = seg[k:j]
            if len(grp) > 1 and len(captions.lines_of(" ".join(x[0] for x in grp), "story")) > 2:
                continue  # wider than two lines of story caption
            cost = 1.0 + (2.0 if len(grp) == 4 else 0.0)
            end = speech.norm(grp[-1][0])
            if j < n:
                cost += 3.0 if end in WEAK_END else 1.0 if end in LEAN_END else 0.5 if end in SUBJECT_END else 0.0
                nxt = speech.norm(seg[j][0])
                if end.endswith("'s") and nxt not in WEAK_END | LEAN_END:
                    cost += 1.0  # a possessive parted from its noun: "Max's | dog" ("Jake's | the" is "Jake is")
            if len(grp) == 1 and n > 1:
                cost += 1.5 if j == n else 2.0
            up = (seg[j][1] if j < n else seg[j - 1][2] + 0.12) - seg[k][1]   # about its time on screen
            chars = len(" ".join(x[0] for x in grp))
            need = max(qc.SPEECH_MIN, chars / qc.SPEECH_CPS) + 1 / 30
            if up < need:   # faster than nearly all the references' captions: the read-time check fails it, unless
                cost += 1.5 if up + 0.12 >= need else 4.0   # _balance can lend it the difference
            elif up < 0.34 or chars / up > 28:
                cost += 1.0  # quicker than nine in ten of theirs (p10 0.34-0.42 s up; p90 28-39 characters a second)
            if best[k] + cost < best[j]:
                best[j], back[j] = best[k] + cost, k
    groups, j = [], n
    while j:
        groups.append(seg[back[j]:j])
        j = back[j]
    return groups[::-1]


def _clauses(words: list, style: str, emoji: str | None, story: bool,
             names=frozenset()) -> list[tuple[str, float, float]]:
    """Words grouped into captions: story captions 1-3 words (4 only when said too fast to split), a phrase at a
    time (`_story_groups`); comedy captions a clause, breaking after sentence ends, and wherever the caption would
    need a fourth line. Each starts in lower case unless its first word is stressed, 'I' or one of the script's
    `names`."""
    import captions
    if story:
        out, seg = [], []
        for i, (w, s, e) in enumerate(words):
            seg.append((w, s, e))
            if w[-1:] in ".!?,;:" or w.endswith("...") or i == len(words) - 1:
                for grp in _story_groups(seg):
                    out.append([_lower_first(" ".join(x[0] for x in grp), names), grp[0][1], grp[-1][2]])
                seg = []
        return [tuple(c) for c in out]  # stories carry no emoji
    out, cur = [], []
    for i, (w, s, e) in enumerate(words):
        cur.append((w, s, e))
        last = i == len(words) - 1
        brk = w[-1:] in ".!?" and not last
        if not brk and not last:
            trial = " ".join(x[0] for x in cur + [words[i + 1]])
            brk = len(captions.lines_of(trial, style)) > 3  # the references run a clause over 1-3 lines
        if brk or last:
            text = _lower_first(" ".join(x[0] for x in cur), names)  # lower case; CAPS only where stressed
            out.append([text, cur[0][1], cur[-1][2]])
            cur = []
    if out and emoji:
        out[-1][0] += " " + emoji
    return [tuple(c) for c in out]


def _balance(caps: list, fps: float, most: float = 0.12) -> None:
    """A caption up too briefly to read (a phrase said very fast) takes up to `most` seconds from its neighbours: it
    shows earlier, into a gap or from the caption before when that one has time to spare, then hides later, from the
    one after. So it stays within a few frames of its words, and nothing it borrows from drops below its own need."""
    import qc

    def need(c):
        import captions as _c
        text = " ".join(t for t in c["text"].split() if not _c.is_emoji(t))
        return max(qc.SPEECH_MIN, len(text) / qc.SPEECH_CPS) + 1.0 / fps   # a frame for rounding

    def spare(c):
        return (c["hide"] - c["show"]) - need(c)

    for i, c in enumerate(caps):
        short = -spare(c)
        if short <= 0:
            continue
        early = min(short, most)
        if i and caps[i - 1]["hide"] <= c["show"] - 1e-9:   # a gap before it
            take = min(early, c["show"] - caps[i - 1]["hide"])
            c["show"] -= take
            early -= take
            short -= take
        if short > 0 and early > 0 and i and abs(caps[i - 1]["hide"] - c["show"]) < 1e-6:
            take = min(early, max(0.0, spare(caps[i - 1])))
            caps[i - 1]["hide"] -= take
            c["show"] -= take
            short -= take
        if short > 0 and i + 1 < len(caps) and abs(caps[i + 1]["show"] - c["hide"]) < 1e-6:
            take = min(short, most, max(0.0, spare(caps[i + 1])))
            c["hide"] += take
            caps[i + 1]["show"] += take


def _snap_to_cuts(caps: list, cuts: list, fps: float, most: int = 4) -> None:
    """A caption due up to `most` frames after a cut comes in on the cut instead: captions cut in with the picture,
    on the cut or a frame or two before (M3's review: five came in 1-3 frames after one). The caption before it
    gives way, if it can spare the frames."""
    for i, c in enumerate(caps):
        if c.get("style") not in ("comedy", "story"):
            continue
        f = int(round(c["show"] * fps))
        cut = max((x for x in cuts if 0 < f - x <= most), default=None)
        if cut is None:
            continue
        t = cut / fps
        if i and caps[i - 1]["hide"] > t:
            if t - caps[i - 1]["show"] < 0.3:
                continue  # the one before can't give the frames
            caps[i - 1]["hide"] = t
        c["show"] = t


def _framing(plan: dict, size=(1080, 1920)) -> list[str]:
    """Actors a shot lists but its camera never shows: each one's head (and a walk's both ends) projected through
    the camera at the shot's start, middle and end. A portrait frame is narrow: at 15 studs, a 58-degree camera sees
    about 4.7 studs either side of its centre, so a hallway's sides are out of shot (M4's first stills: the gossips
    by the lockers never appeared). Warnings, not failures: an actor can be meant to wait out of shot."""
    import camera
    out = []
    w, h = size
    for s in plan["shots"]:
        path = camera.moves([(k[0], k[1], k[2], k[3]) for k in s["camera"]])
        views = [path(t) for t in (0.0, s["seconds"] / 2, max(0.0, s["seconds"] - 1e-3))]
        for name, a in s.get("actors", {}).items():
            spots = [a["cf"]["pos"]] + ([a["walk"]["from"], a["walk"]["to"]] if a.get("walk") else [])
            seen = False
            for v in views:
                for p in spots:
                    xy = camera.project(v, [p[0], p[1] + 1.5, p[2]], size=size)
                    if xy and -0.05 * w <= xy[0] <= 1.05 * w and -0.05 * h <= xy[1] <= 1.05 * h:
                        seen = True
            if not seen:
                out.append(f"{s['name']}: {name} is never in frame (head out of shot at its start, middle and end)")
    return out


def _offset_shot(spec: dict, off) -> None:
    """A shot staged in another set: its coordinates (not its actor-relative points) moved by the set's offset."""
    if spec.get("_shifted"):
        return

    def mv(p):
        return [a + b for a, b in zip(p, off)] if isinstance(p, (list, tuple)) and len(p) == 3 else p

    for a in spec.get("actors", {}).values():
        for k in ("at", "look"):
            if k in a:
                a[k] = mv(a[k])
        if a.get("walk"):
            a["walk"]["from"], a["walk"]["to"] = mv(a["walk"]["from"]), mv(a["walk"]["to"])
    for key in spec.get("camera", []):
        for k in ("pos", "look", "aim"):
            if k in key:
                key[k] = mv(key[k])
        for sub in ("low", "top"):
            if sub in key and "aim" in key[sub]:
                key[sub]["aim"] = mv(key[sub]["aim"])
    spec["_shifted"] = True


def stage_plan(sh: Short) -> bool:
    """Time the whole video: shot lengths (from the lines when 'auto'), every word-anchored key, the captions."""
    words = _words(sh)
    lines = sh.lines()
    fps = sh.fps
    shots, t, line_starts, frame0 = [], 0.0, {}, 0
    # shot lengths first: an 'auto' shot runs to its last line's end plus `pad`
    offsets = {e.get("id", e["name"]): e["at"] for e in sh.spec.get("sets", [])}
    for spec in sh.spec["shots"]:
        if spec.get("set") and spec["set"] in offsets:
            _offset_shot(spec, offsets[spec["set"]])
        says = spec.get("say", [])
        dur = spec.get("seconds", "auto")
        ends = []
        for s in says:
            at = s.get("at", 0.0)
            if not isinstance(at, (int, float)):
                at = _resolve(at, t, {**line_starts}, words)
            line_starts[s["line"]] = t + at
            ends.append(at + words[s["line"]]["duration"])
        if spec.get("until") is not None:  # the shot ends on a time: 'b:switched' cuts on that word
            dur = _resolve(spec["until"], t, line_starts, words)
        elif dur == "auto":
            if not ends:
                raise SystemExit(f"shot {spec['name']}: 'auto' length but no lines")
            dur = max(ends) + spec.get("pad", 0.12)
        if float(dur) <= 0:
            raise SystemExit(f"shot {spec['name']}: {float(dur):.2f} s long")
        n = int(round(float(dur) * fps))
        shots.append({"spec": spec, "start": t, "frames": n, "frame0": frame0})
        frame0 += n
        t = frame0 / fps
    total = frame0 / fps
    plan = {"slug": sh.slug, "fps": fps, "family": sh.family, "frames": frame0, "seconds": total, "shots": []}
    hits, texts, sounds, voices = [], [], [], []
    for k, s in enumerate(shots):
        spec, st = s["spec"], s["start"]

        def res(ref, _st=st):
            return _resolve(ref, _st, line_starts, words)

        cam = []
        for key in spec.get("camera", []):
            v = _view(spec, key)
            cam.append([res(key.get("t", 0.0)), v, float(key.get("move", 0.0)), key.get("ease", "out")])
        if not cam:
            raise SystemExit(f"shot {spec['name']}: no camera")
        actors = {}
        for name, a in spec.get("actors", {}).items():
            pos = _vec(a.get("at", [0, 3, 0]))
            d = _actor_dir(spec, name)
            actors[name] = {"planted": a.get("planted", True),
                            "cf": {"pos": pos, "look": [pos[0] + d[0] * 10, pos[1], pos[2] + d[2] * 10]},
                            "poses": [[res(p[0]), p[1]] for p in a.get("poses", [[0, "idle"]])],
                            "faces": [[res(f[0]), f[1]] for f in a.get("faces", [[0, "smile"]])],
                            "drift": a.get("drift", 1.0)}
            if a.get("walk"):
                w = a["walk"]
                actors[name]["walk"] = {"from": _vec(w["from"]), "to": _vec(w["to"]), "start": res(w.get("start", 0)),
                                        "freq": w.get("freq", 1.5)}
        for say in spec.get("say", []):
            lid = say["line"]
            voices.append({"line": lid, "shot": spec["name"], "start": line_starts[lid],
                           "end": line_starts[lid] + words[lid]["duration"], "gain_db": say.get("gain_db", 0.0)})
        for fx_ in spec.get("sfx", []):
            at = st + res(fx_.get("at", 0.0))
            sounds.append({"sound": fx_["sound"], "start": at, "gain_db": fx_.get("gain_db", 0.0),
                           "shot": spec["name"], "hit": bool(fx_.get("hit", fx_["sound"] in ("boom", "thud")))})
            if sounds[-1]["hit"]:
                hits.append({"frame": int(round(at * fps)), "what": f"{fx_['sound']} in {spec['name']}"})
        overlays = []
        for ov in spec.get("overlays", []):
            overlays.append({"icon": ov.get("icon"), "text": ov.get("text"), "over": _point(spec, ov["over"]),
                             "start": res(ov.get("at", 0.0)), "dur": float(ov.get("dur", 0.6)),
                             "size": float(ov.get("size", 150)), "lift": float(ov.get("lift", 1.4))})
        plan["shots"].append({"overlays": overlays, "name": spec["name"], "start": st, "frames": s["frames"],
                              "frame0": s["frame0"],
                              "seconds": s["frames"] / fps, "camera": cam, "actors": actors,
                              "drift": spec.get("drift", 1.0), "streak": bool(spec.get("streak")),
                              "seed": k})
    # captions: from the lines, in the family's style
    style = sh.spec.get("caption_style", CAPTION_STYLE.get(sh.family, "comedy"))
    caps = []
    names = _names(lines) | {n.lower() for n in sh.spec.get("names", [])}
    for v in sorted(voices, key=lambda v: v["start"]):
        ln = lines[v["line"]]
        if ln.get("caption") is False:
            continue
        aligned = _aligned_words(ln, words[v["line"]], names)
        emoji = ln.get("emoji") if not ln.get("caption") and style == "comedy" else None  # stories: no emoji
        for text, a, b in _clauses(aligned, style, emoji, story=(style == "story"), names=names):
            caps.append({"text": text, "start": v["start"] + a, "end": v["start"] + b, "style": style})
    lead = 2 / fps
    for i, c in enumerate(caps):
        nxt = caps[i + 1]["start"] - lead if i + 1 < len(caps) else total
        c["show"] = max(0.0, c["start"] - lead)
        c["hide"] = min(nxt, max(c["end"] + (0.35 if style != "story" else 0.12), c["show"] + 0.3), total)
    _balance(caps, fps)
    _snap_to_cuts(caps, [s["frame0"] for s in plan["shots"]], fps)
    for extra in sh.spec.get("texts", []):
        caps.append({"text": extra["text"], "style": extra.get("style", "header"), "show": float(extra["from"]),
                     "hide": float(extra.get("to", total)), "start": float(extra["from"]), "end": float(extra.get("to", total))})
    plan["captions"] = caps
    plan["voices"], plan["sounds"] = voices, sounds
    plan["music"] = sh.spec.get("music")
    plan["punch"] = sh.spec.get("punch", True)
    _save(sh.path("plan.json"), plan)
    import captions as _c
    cut = {"fps": fps, "clips": [{"name": s["name"], "frames": s["frames"]} for s in plan["shots"]],
           "texts": [{"text": re.sub(r"\{\w+:([^}]*)\}", r"\1",   # the words as read: no emoji, no {colour:...}
                                     " ".join(t for t in c["text"].split() if not _c.is_emoji(t))),
                      "start": _caption_frames(c, fps)[0],
                      "frames": _caption_frames(c, fps)[1] - _caption_frames(c, fps)[0],
                      "speech": c["style"] in ("comedy", "story")} for c in caps],
           "hits": hits, "silences": [], "cues": []}
    _save(sh.path("cut.json"), cut)
    print(f"plan: {len(plan['shots'])} shots, {total:.2f} s ({frame0} frames at {fps}), {len(voices)} lines, "
          f"{len(caps)} captions, {len(sounds)} effects ({len(hits)} hits)")
    for s in plan["shots"]:
        print(f"  {s['name']}: {s['start']:.2f}-{s['start'] + s['seconds']:.2f} s ({s['frames']} frames)")
    for warn in _framing(plan):
        print(f"  framing: {warn}")
    import qc
    from timeline import Timeline
    short = [row for row in qc.text_times(Timeline(cut), 12.0) if row[0] == "FAIL"]
    for _, what in short:
        print(f"  caption too brief to read: {what}")
    if short:  # the same rule qc.py applies to the delivered file: better found before the shoot
        print(f"plan: {len(short)} captions up too briefly to read; split the line or slow its read")
        return False
    return True


# ---------------------------------------------------------------------------------------------------- shoot


def _face_at(keys: list, t: float) -> str:
    name = keys[0][1]
    for tk, f in keys:
        if t + 1e-9 >= tk:
            name = f
    return name


def shot_fn(plan: dict, shot: dict, cast: list[str]):
    """The harness's state for each moment of one shot: camera (with hold drift) and every actor."""
    import camera
    import faces
    import pose

    path = camera.moves([(k[0], k[1], k[2], k[3]) for k in shot["camera"]])

    def at(t: float) -> dict:
        v = camera.hold(path(t), t, amount=shot.get("drift", 1.0), seed=shot["seed"])
        st = camera.state(v)
        acts = []
        for i, name in enumerate(cast):
            a = shot["actors"].get(name)
            if not a:
                acts.append({"name": name, "cf": {"pos": [OFF[0] + 4 * i, OFF[1], OFF[2]],
                                                  "look": [OFF[0] + 4 * i, OFF[1], OFF[2] + 10]}})
                continue
            cf = a["cf"]
            if a.get("walk") and t >= a["walk"]["start"]:
                w = a["walk"]
                tw = t - w["start"]
                dist = math.dist(w["from"], w["to"])
                trav = min(pose.walk_travel(tw, freq=w["freq"]), dist)
                u = trav / dist if dist else 1.0
                pos = [w["from"][j] + (w["to"][j] - w["from"][j]) * u for j in range(3)]
                d = [w["to"][0] - w["from"][0], 0.0, w["to"][2] - w["from"][2]]
                cf = {"pos": pos, "look": [pos[0] + d[0], pos[1], pos[2] + d[2]]}
                if trav < dist:
                    joints, rootpos = pose.walking(tw, freq=w["freq"])
                else:
                    joints, rootpos = pose.at(a["poses"], t, drift_amount=a.get("drift", 1.0), seed=i + 1,
                                              planted=a.get("planted", True))
            else:
                joints, rootpos = pose.at(a["poses"], t, drift_amount=a.get("drift", 1.0), seed=i + 1,
                                          planted=a.get("planted", True))
            acts.append({"name": name, "cf": cf, "face": faces.url(_face_at(a["faces"], t), _face_set()),
                         "joints": joints, "rootpos": rootpos})
        st["actors"] = acts
        return st

    return at


def _face_set() -> str:
    import faces
    return getattr(faces, "SET", "vidfaces")


def _cast_specs(sh: Short) -> dict:
    """The actors' looks: an archetype from tools/roblox/cast.json, or a stage.py spec written in the short."""
    lib_path = os.path.join(ROOT, "tools", "roblox", "cast.json")
    lib = _load(lib_path)["looks"] if os.path.exists(lib_path) else {}
    out = {}
    for name, c in sh.spec["cast"].items():
        if isinstance(c, str):
            c = {"look": c}
        look = dict(lib.get(c.get("look"), {})) if c.get("look") else {}
        look.update({k: v for k, v in c.items() if k != "look"})
        out[name] = look
    return out


def _studio_session(sh: Short, plan: dict, body) -> None:
    """Play, stage the set and cast, run `body`, and always put Studio back as it was."""
    import capture
    import faces
    import sets
    import stage
    import studio

    cast = _cast_specs(sh)
    face_names = sorted({f[1] for s in plan["shots"] for a in s["actors"].values() for f in a["faces"]})
    try:
        print(studio.play(True))
        studio.wait_for("Client", timeout=120)
        print(stage.park(sets.park_point(sh.spec.get("set", "baseplate"))))
        print(stage.actors(cast))
        print(sets.build(sh.spec.get("set", "baseplate"), sh.spec.get("set_options", {})))
        for extra in sh.spec.get("sets", []):  # more places, each at its own offset
            print(sets.build(extra["name"], extra.get("options", {}), tuple(extra["at"]), append=True))
        print(capture.install().strip()[-60:])
        print(capture.preload([faces.url(n, _face_set()) for n in face_names]))
        body(list(cast))
    finally:
        for step in (capture.release, stage.clear_actors, sets.clear, lambda: studio.play(False)):
            try:
                print(step())
            except Exception as e:  # noqa: BLE001
                print("cleanup step failed:", e)
        time.sleep(1)


def _done_frames(d: str, n: int) -> int:
    k = 0
    while k < n and os.path.exists(os.path.join(d, f"f{k:05d}.png")):
        k += 1
    return k


def stage_shoot(sh: Short, only: list[str] | None = None, stills: bool = False) -> bool:
    import capture
    plan = _load(sh.path("plan.json"))
    todo = [s for s in plan["shots"] if not only or s["name"] in only]

    def body(cast):
        for s in todo:
            d = sh.path("stills" if stills else "shots", s["name"])
            if stills:
                mid = s["frames"] // 2
                capture.take(d, shot_fn(plan, s, cast), seconds=s["seconds"], fps=plan["fps"], only=[mid],
                             warmup=2.0, portrait=True)
                continue
            have = _done_frames(d, s["frames"])
            if have >= s["frames"]:
                print(f"{s['name']}: done")
                continue
            t0 = time.time()
            capture.take(d, shot_fn(plan, s, cast), seconds=s["seconds"], fps=plan["fps"], start=have,
                         warmup=3.0, portrait=True)
            print(f"{s['name']}: {s['frames'] - have} frames in {time.time() - t0:.0f} s")

    for attempt in range(4):  # a playtest can drop out mid-take ("Target is not reachable"): start again, resume
        try:
            _studio_session(sh, plan, body)
            break
        except RuntimeError as e:
            print(f"shoot: the session failed ({str(e)[:160]}); attempt {attempt + 2} resumes from the frames on disk")
            time.sleep(5)
    if stills:
        return True
    missing = [s["name"] for s in plan["shots"] if _done_frames(sh.path("shots", s["name"]), s["frames"]) < s["frames"]]
    if missing:
        print("shoot: frames missing from", missing)
    return not missing


# ---------------------------------------------------------------------------------------------------- cut


@functools.lru_cache(maxsize=4)
def _plan_cached(path: str) -> dict:
    return _load(path)


@functools.lru_cache(maxsize=8)
def _path_for(plan_path: str, shot_name: str):
    import camera
    plan = _plan_cached(plan_path)
    shot = next(s for s in plan["shots"] if s["name"] == shot_name)
    return camera.moves([(k[0], k[1], k[2], k[3]) for k in shot["camera"]])


@functools.lru_cache(maxsize=64)
def _caption_layer(text: str, style: str):
    import captions
    return captions.render(text, style)


def frame_at(build: str, r: int) -> np.ndarray:
    """Record frame r of the cut: the shot's captured frame at 1080 x 1920, a swoop's streak, the captions."""
    import cv2

    import camera
    import fx
    import look
    plan_path = os.path.join(build, "plan.json")
    plan = _plan_cached(plan_path)
    fps = plan["fps"]
    shot = next(s for s in plan["shots"] if s["frame0"] <= r < s["frame0"] + s["frames"])
    k = r - shot["frame0"]
    img = cv2.imread(os.path.join(build, "shots", shot["name"], f"f{k:05d}.png"), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"shot {shot['name']} frame {k} missing")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    if img.shape[:2] != (1920, 1080):
        img = cv2.resize(img, (1080, 1920), interpolation=cv2.INTER_LANCZOS4)
    out = img.astype(np.float32) / 255.0
    if shot.get("streak"):
        px = camera.smear(_path_for(plan_path, shot["name"]), k / fps, fps=fps) * 1080 / 960
        if px > 1.5:
            out = fx.streak(out, px)
    for ov in shot.get("overlays", []):
        u = (k / fps - ov["start"]) / max(ov["dur"], 1e-3)
        if 0.0 <= u < 1.0:
            out = _overlay(out, ov, _path_for(plan_path, shot["name"])(k / fps), u)
    zoom = _punch(plan, r)
    if zoom > 1.0005:
        h, w = out.shape[:2]
        ch, cw = int(round(h / zoom)), int(round(w / zoom))
        y0, x0 = (h - ch) // 2, (w - cw) // 2
        out = cv2.resize(out[y0:y0 + ch, x0:x0 + cw], (w, h), interpolation=cv2.INTER_LINEAR)
    for c in plan["captions"]:
        f0, f1 = _caption_frames(c, fps)
        if f0 <= r < f1:
            layer, (x, y) = _caption_layer(c["text"], c["style"])
            look.over(out, layer, x, y)
    return out


def _caption_frames(c: dict, fps: float) -> tuple[int, int]:
    """The frames a caption is up for, by the one rule the timeline uses too (M3's review: the render and
    cut.json disagreed by a frame)."""
    f0 = int(round(c["show"] * fps))
    return f0, f0 + max(1, int(round((c["hide"] - c["show"]) * fps)))


PUNCH = (0.07, 0.3)   # how far a hit punches in, and how long it takes to settle


def _punch(plan: dict, r: int) -> float:
    """The picture's zoom at frame r: a boom or a thud that doesn't land on a cut punches in 7% on its frame and
    eases back over 0.3 s, so the hit is in the picture as well as the sound (M3's review: booms on static holds).
    `"punch": false` in the spec turns it off."""
    if plan.get("punch") is False:
        return 1.0
    fps = plan["fps"]
    cuts = [s["frame0"] for s in plan["shots"]]
    z = 1.0
    for snd in plan.get("sounds", []):
        if not snd.get("hit"):
            continue
        f = int(round(snd["start"] * fps))
        if any(abs(f - c) <= 2 for c in cuts):
            continue  # the cut is the hit
        u = (r - f) / (PUNCH[1] * fps)
        if 0.0 <= u < 1.0:
            z = max(z, 1.0 + PUNCH[0] * (1.0 - u) ** 2)
    return z


@functools.lru_cache(maxsize=16)
def _icon(name: str, size: int):
    """An icon for an overlay: an emoji picture from the caption set, by name or emoji."""
    import captions
    token = {"bell": "\U0001F514", "heart": "\u2764", "money": "\U0001F4B8", "skull": "\U0001F480",
             "fire": "\U0001F525", "eyes": "\U0001F440", "warning": "\u26A0"}.get(name, name)
    return captions._outlined_emoji(token, size, max(3, size // 22))


def _overlay(img: np.ndarray, ov: dict, view: dict, u: float) -> np.ndarray:
    """An icon, a line of text or both (the text over the icon) popping up over a point in the scene: projected
    through the shot's camera, scaled in with a little overshoot over the first fifth of its time, faded out over the
    last fifth. Text is drawn in the `label` style, its natural size at `size` 150 ("99%" over a head, a text in a
    speech bubble)."""
    import cv2

    import camera
    import look
    p = list(ov["over"])
    p[1] += ov.get("lift", 1.4)
    xy = camera.project(view, p, size=(1080, 1920))
    if not xy:
        return img
    pop = min(1.0, u / 0.2)
    scale = 1.0 + 0.18 * math.sin(math.pi * pop) if pop < 1 else 1.0
    scale *= pop ** 0.5
    alpha = 1.0 if u < 0.8 else max(0.0, (1.0 - u) / 0.2)
    pics = []
    if ov.get("icon"):
        size = max(4, int(ov["size"] * scale))
        pic = _icon(ov["icon"], 256)
        pics.append(cv2.resize(pic, (max(1, int(pic.shape[1] * size / pic.shape[0])), size),
                               interpolation=cv2.INTER_AREA))
    if ov.get("text"):
        layer, _ = _caption_layer(ov["text"], "label")
        k = max(0.02, ov["size"] / 150.0 * scale)
        pics.append(cv2.resize(layer, (max(1, int(layer.shape[1] * k)), max(1, int(layer.shape[0] * k))),
                               interpolation=cv2.INTER_AREA))
    for pic in pics:
        pic = pic.copy()
        pic[..., 3] *= alpha
        look.over(img, pic, int(xy[0] - pic.shape[1] / 2), int(xy[1] - pic.shape[0] / 2))
    return img


def stage_cut(sh: Short) -> bool:
    import render
    plan = _load(sh.path("plan.json"))
    missing = [s["name"] for s in plan["shots"] if _done_frames(sh.path("shots", s["name"]), s["frames"]) < s["frames"]]
    if missing:
        print("cut: shots not shot yet:", missing)
        return False
    _plan_cached.cache_clear()
    render.master(functools.partial(frame_at, sh.build), plan["frames"], 1080, 1920, plan["fps"],
                  sh.path("master.mov"), log=lambda m: print(m, flush=True))
    print("cut:", sh.path("master.mov"))
    return True


# ---------------------------------------------------------------------------------------------------- mix


def _clip_at(plan: dict, t: float) -> tuple[str, float]:
    for s in plan["shots"]:
        if s["start"] - 1e-9 <= t < s["start"] + s["seconds"] - 1e-9:
            return s["name"], t - s["start"]
    last = plan["shots"][-1]
    return last["name"], t - last["start"]


def _music(spec: dict, seconds: float, sr: int) -> np.ndarray | None:
    """The music bed: a file looped to length, from `start` s into it."""
    import cues
    path = spec["track"] if os.path.isabs(spec["track"]) else os.path.join(ROOT, spec["track"])
    x = cues.load(path, sr)
    x = x[int(spec.get("offset", 0.0) * sr):]
    n = int(seconds * sr)
    if len(x) < n:
        x = np.concatenate([x] * (n // len(x) + 1))
    return x[:n]


def _duck_tail(y: np.ndarray, sr: int, start: float, line_starts: list, depth_db: float = -12.0) -> np.ndarray:
    """A boom's long low tail pulled down under the next line that starts while it rings (M3's review: the tails sat
    at -16 dBFS in the low band under the next line's first word, the speech at -26), from 50 ms before the line."""
    nxt = [t - start for t in line_starts if 0.05 < t - start < len(y) / sr]
    if not nxt:
        return y
    i0 = max(0, int((min(nxt) - 0.05) * sr))
    n = int(0.06 * sr)
    g = np.ones(len(y))
    g[i0:i0 + n] = np.linspace(1.0, 10 ** (depth_db / 20), len(g[i0:i0 + n]))
    g[i0 + n:] = 10 ** (depth_db / 20)
    return y * (g[:, None] if y.ndim == 2 else g)


def stage_mix(sh: Short) -> bool:
    import cues
    import master
    import soundfile as sf

    import sfx
    from timeline import Timeline

    plan = _load(sh.path("plan.json"))
    sr = 48000
    tl = Timeline.load(sh.path("cut.json"))
    mix = cues.Mix(tl, sr)
    for v in plan["voices"]:
        clip, at = _clip_at(plan, v["start"])
        end_clip, _ = _clip_at(plan, min(v["end"], plan["seconds"] - 1e-6))
        y = cues.load(sh.path("voice", v["line"] + ".wav"), sr)
        mix.place("voice", y, clip, at=at, gain_db=v.get("gain_db", 0.0),
                  until=end_clip if end_clip != clip else None, label=v["line"])
    for s in plan["sounds"]:
        clip, at = _clip_at(plan, s["start"])
        y = sfx.make(s["sound"]) if s["sound"] in sfx.EFFECTS else cues.load(
            s["sound"] if os.path.isabs(s["sound"]) else os.path.join(ROOT, s["sound"]), sr)
        if s.get("hit"):
            y = _duck_tail(y, sr, s["start"], [v["start"] for v in plan["voices"]])
        end_clip, _ = _clip_at(plan, min(s["start"] + len(y) / sr, plan["seconds"] - 1e-6))
        mix.place("sfx", y, clip, at=at, gain_db=s.get("gain_db", 0.0),
                  until=end_clip if end_clip != clip else None, label=os.path.basename(s["sound"]))
    music = plan.get("music")
    gains = {"voice": 0.0, "sfx": -2.0, "music": -14.0}
    if music:
        start = float(music.get("start", 0.0))
        bed = _music(music, plan["seconds"] - start, sr)
        n = min(len(bed), int(0.35 * sr))
        if n:   # faded at the end: a note cut off there clicks every time the Short loops (M3's review)
            bed[-n:] = bed[-n:] * np.linspace(1.0, 0.0, n)[:, None] if bed.ndim == 2 else bed[-n:] * np.linspace(1.0, 0.0, n)
        clip, at = _clip_at(plan, start)
        mix.place("music", bed, clip, at=at, until=plan["shots"][-1]["name"], label="music")
        gains["music"] = float(music.get("gain_db", -14.0))
        if music.get("duck", True):
            mix.buses["music"] = cues.duck(mix.buses["music"], mix.buses["voice"], sr, depth_db=music.get("duck_db", -6.0))
    for s in sh.spec.get("silences", []):
        mix.silence(float(s["start"]), float(s["end"]), s.get("what", ""))
    raw = mix.render(gains)
    mix.write(sh.path("mix_raw.wav"), raw)
    y = master.master(raw, sr, -14.0, -2.4, silences=mix.silences)
    n = min(len(y), int(0.015 * sr))
    if n:
        y[-n:] = y[-n:] * (np.linspace(1.0, 0.0, n)[:, None] if y.ndim == 2 else np.linspace(1.0, 0.0, n))
    sf.write(sh.path("mix.wav"), y, sr, subtype="PCM_24")
    mix.export(sh.path("cut.json"))
    print(f"mix: {sh.path('mix.wav')} ({master.lufs(y, sr):.1f} LUFS, {master.true_peak_db(y):.1f} dBTP)")
    return True


# ---------------------------------------------------------------------------------------------------- deliver


def stage_deliver(sh: Short) -> bool:
    import audio as vaudio
    import deliver
    import media
    import qc
    import sheets
    from timeline import Timeline

    mp4 = deliver.encode(sh.path("master.mov"), sh.path("mix.wav"), sh.out, size=(1080, 1920))
    tl = Timeline.load(sh.path("cut.json"))
    vdir = sh.path("verify")
    dest, failed = qc.report(mp4, tl, vdir, -14.0, -1.0, 12.0)
    x, sr = media.audio(mp4)
    lines = ["# Sound against the cut", ""]
    total_fails = 0
    for name, fn in (("crossings", vaudio.crossings), ("silences", vaudio.silences), ("sync", vaudio.sync)):
        out, fails = fn(tl, x, sr)
        total_fails += fails
        lines += [f"## {name}", ""] + out + [""]
    with open(os.path.join(vdir, "audio_report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    vaudio.spectrogram(tl, x, sr, os.path.join(vdir, "spectrogram.png"))
    made = sheets.cuts(mp4, tl, vdir) + sheets.contact(mp4, 12, tl, vdir)
    print(f"deliver: {mp4}\n  qc {'FAILED' if failed else 'passed'} ({dest})\n  audio: {total_fails} failures "
          f"({os.path.join(vdir, 'audio_report.md')})\n  sheets: {len(made)}")
    return not failed and total_fails == 0


STAGES = {"voice": stage_voice, "plan": stage_plan, "shoot": stage_shoot, "cut": stage_cut, "mix": stage_mix,
          "deliver": stage_deliver}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=list(STAGES) + ["stills", "all"])
    ap.add_argument("video", help="videos/<slug>")
    ap.add_argument("--only", nargs="*", help="shoot only these shots")
    args = ap.parse_args()
    sh = Short(args.video)
    t0 = time.time()
    if args.stage == "stills":
        ok = stage_shoot(sh, args.only, stills=True)
    elif args.stage == "shoot":
        ok = stage_shoot(sh, args.only)
    elif args.stage == "all":
        ok = True
        for name in ("plan", "shoot", "cut", "mix", "deliver"):
            print(f"== {name}", flush=True)
            ok = STAGES[name](sh)
            if not ok:
                print(f"stopped at {name}")
                break
    else:
        ok = STAGES[args.stage](sh)
    print(f"{args.stage}: {'done' if ok else 'FAILED'} in {time.time() - t0:.0f} s")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
