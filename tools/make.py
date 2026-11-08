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
# Actors not in a shot wait 200 studs under the floor, 4 studs apart. "Far behind the camera" (z = 400) was in
# front of every camera looking north on the open street: two extras stood in the sky in M5's first frames.
OFF = [0.0, -200.0, 0.0]
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
                    legacy = sh.path("raw", f"{ln['id']}_{k}.mp3")   # fetched before takes were named by the take
                    try:
                        voice.fetch(src, dest)
                    except RuntimeError as e:   # a signed link expires: use the copy fetched while it worked
                        if not os.path.exists(legacy):
                            raise
                        import shutil
                        shutil.copyfile(legacy, dest)
                        print(f"line {ln['id']} take {k + 1}: {e}; using the copy fetched earlier "
                              f"({os.path.basename(legacy)})")
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


def _posed_points(pos, d, keys: list, t: float, planted: bool = True) -> tuple[list, list]:
    """An actor's head centre and face in world studs, where its pose at time t puts them: a slump drops the face
    half a stud and tips it forward, a laugh throws it back (M5's "twice": a close-up aimed at the upright face
    framed the slumped one on the frame's bottom edge). pos is the torso's centre at rest, d the way it faces, keys
    the poses [[t, pose], ...] in seconds into the shot. The joints as the harness poses them (pose.clearance())."""
    import pose
    joints, rootpos = pose.at(keys, float(t), drift_amount=0.0, planted=planted)
    r_root = pose.angles(*joints["root"])
    r_head = pose._mul(r_root, pose.angles(*joints["neck"]))
    neck = pose._apply(r_root, (0.0, 1.0, 0.0))
    rise = pose._apply(r_head, (0.0, HEAD - 1.0, 0.0))
    ahead = pose._apply(r_head, (0.0, 0.0, -FACE))
    head = [rootpos[i] + neck[i] + rise[i] for i in range(3)]
    face = [head[i] + ahead[i] for i in range(3)]
    right = (-d[2], 0.0, d[0])

    def world(v):   # the character's axes (x its right, y up, z its back) to the world's
        return [pos[i] + v[0] * right[i] + (v[1] if i == 1 else 0.0) - v[2] * d[i] for i in range(3)]
    return world(head), world(face)


def _point(shot: dict, p, t: float | None = None) -> list:
    """A point: [x, y, z], or 'actor.head' / 'actor.face' / 'actor.torso' / 'actor.feet', with '+[dx,dy,dz]'. With
    the time t (seconds into the shot) a head or face is where the actor's pose then puts it (_posed_points)."""
    if isinstance(p, (list, tuple)):
        return _vec(p)
    base, _, extra = str(p).partition("+")
    name, _, part = base.partition(".")
    pos = _actor_pos(shot, name)
    d = _actor_dir(shot, name)
    keys = (shot.get("_poses") or {}).get(name)
    if part in ("", "torso"):
        out = pos
    elif part in ("head", "face") and keys and t is not None:
        head, face = _posed_points(pos, d, keys, t, shot["actors"][name].get("planted", True))
        out = head if part == "head" else face
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


def _view(shot: dict, v: dict, t: float | None = None) -> dict:
    """A camera view from its spec (docs/MAKING.md, "Camera"): aim / pos+look / ots / low / top, then dutch, back.
    t is the key's time in the shot: a head or face is aimed at where the actor's pose has it then."""
    import camera
    if "aim" in v:
        target = _point(shot, v["aim"], t)
        toward = v.get("toward")
        if v.get("between"):  # a two-shot: framed on the point between two heads, from the side both face
            name_b = v["between"].split(".")[0]
            other = _point(shot, name_b + ".head", t)
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
        out = camera.view(_vec(v["pos"]), _point(shot, v["look"], t), roll=v.get("roll", 0.0), fov=v.get("fov", 45.0))
    elif "ots" in v:
        o = v["ots"]
        near, far = o["near"], o["far"]
        out = camera.ots(_point(shot, near + ".head", t), _point(shot, far + ".face", t), side=o.get("side", 1.5),
                         behind=o.get("behind", 2.8), up=o.get("up", 0.4), fov=o.get("fov", 45.0),
                         blur=o.get("blur", 0.6), lift=o.get("lift", 1.0))
    elif "low" in v:
        o = v["low"]
        target = _point(shot, o["aim"], t)
        toward = o.get("toward") or (_actor_dir(shot, o["aim"].split(".")[0]) if isinstance(o["aim"], str) else (0, 0, 1))
        out = camera.low(target, toward=toward, distance=o.get("distance", 5.0), eye=o.get("eye", 2.5),
                         fov=o.get("fov", 55.0))
    elif "top" in v:
        o = v["top"]
        out = camera.top(_point(shot, o["aim"], t), height=o.get("height", 8.0), up=o.get("up", (0, 0, 1)),
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
        if not brk and not last and w[-1:] in ",;:" and len(cur) >= 2:   # a clause each: its punch isn't up before
            rest = 0                                                     # it's said (M3's third review: "I'll do
            for x in words[i + 1:]:                                      # the title page!" up 1.3 s early)
                rest += 1
                if x[0][-1:] in ".!?,;:":
                    break
            brk = rest >= 2
        carry = []
        if not brk and not last:
            trial = " ".join(x[0] for x in cur + [words[i + 1]])
            brk = len(captions.lines_of(trial, style)) > 3  # the references run a clause over 1-3 lines
            if brk:   # too long for one caption: split at its last comma, not a word from its end (M3's second
                commas = [k for k, x in enumerate(cur[:-1]) if x[0][-1:] in ",;:"]   # review: "September." alone)
                if commas and commas[-1] >= 1:
                    carry, cur = cur[commas[-1] + 1:], cur[:commas[-1] + 1]
        if brk or last:
            text = _lower_first(" ".join(x[0] for x in cur), names)  # lower case; CAPS only where stressed
            out.append([text, cur[0][1], cur[-1][2]])
            cur = carry
    if out and emoji:
        out[-1][0] += " " + emoji
    return [tuple(c) for c in out]


def _audible_onset(path: str, below: float = 18.0) -> float:
    """When a voice take is first heard: the first 10 ms whose level comes within `below` dB of the take's loudest.
    A line can open on a soft glide the transcriber counts as its first word (M3's "WE?!": 0.17 s at -61 to -32 dB,
    lost under the music, so the caption came up 13 frames before the shout)."""
    import soundfile as _sf
    try:
        y, sr = _sf.read(path, dtype="float32")
    except (OSError, RuntimeError):
        return 0.0
    if y.ndim > 1:
        y = y.mean(axis=1)
    hop = max(1, int(sr * 0.01))
    n = len(y) // hop
    if n == 0:
        return 0.0
    db = 10 * np.log10(np.mean(y[:n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    hit = np.nonzero(db >= db.max() - below)[0]
    return float(hit[0] * hop / sr) if len(hit) else 0.0


def _cap_need(c: dict, fps: float) -> float:
    """The seconds a speech caption needs on screen: qc.py's read rule, and a frame for rounding."""
    import captions as _c
    import qc
    text = " ".join(t for t in c["text"].split() if not _c.is_emoji(t))
    return max(qc.SPEECH_MIN, len(text) / qc.SPEECH_CPS) + 1.0 / fps


def _balance(caps: list, fps: float, most: float = 0.12) -> None:
    """A caption up too briefly to read (a phrase said very fast) takes up to `most` seconds from its neighbours:
    first it hides later, into a gap or from the caption after when that one has time to spare; then it shows earlier,
    but never more than two frames before its words (M4's second review: "then he" came up 7 frames early, over the
    shot before). Nothing it borrows from drops below its own need."""
    def spare(c):
        return (c["hide"] - c["show"]) - _cap_need(c, fps)

    for i, c in enumerate(caps):
        short = -spare(c)
        if short <= 0:
            continue
        later = min(short, most)
        nxt = caps[i + 1] if i + 1 < len(caps) else None
        if nxt is None or nxt["show"] > c["hide"] + 1e-9:   # a gap after it, or the end
            take = later if nxt is None else min(later, nxt["show"] - c["hide"])
            c["hide"] += take
            later -= take
            short -= take
        if short > 0 and later > 0 and nxt is not None and abs(nxt["show"] - c["hide"]) < 1e-6:
            take = min(later, max(0.0, spare(nxt)))
            c["hide"] += take
            nxt["show"] += take
            short -= take
        early = min(short, 2.0 / fps)
        if early > 0 and i:
            prev = caps[i - 1]
            if prev["hide"] <= c["show"] - 1e-9:   # a gap before it
                take = min(early, c["show"] - prev["hide"])
                c["show"] -= take
                early -= take
            if early > 0 and abs(prev["hide"] - c["show"]) < 1e-6:
                take = min(early, max(0.0, spare(prev)))
                prev["hide"] -= take
                c["show"] -= take


def _snap_to_cuts(caps: list, cuts: list, fps: float, most: int = 4, early: int = 2) -> None:
    """A caption due up to `most` frames after a cut, or up to `early` frames before one, comes in on the cut
    instead: captions cut in with the picture (M3's reviews: five came in 1-3 frames after a cut, and four 2 frames
    before one, over the shot before). The caption before it gives way, if it can spare the frames."""
    for i, c in enumerate(caps):
        if c.get("style") not in ("comedy", "story"):
            continue
        f = int(round(c["show"] * fps))
        word = int(round(c.get("start", c["show"]) * fps))
        cut = max((x for x in cuts if 0 < f - x <= most and word - x <= 2), default=None)   # back to a cut only
        if cut is None:   # while its word is 2 frames off at most, the lead it has anyway: never before its word by
            #               more (M3's third review: "seen." 6 frames early; at 3, "then there's this guy," was 3)
            cut = min((x for x in cuts if 0 < x - f <= early), default=None)
        if cut is None:
            continue
        t = cut / fps
        if i and caps[i - 1]["hide"] > t:
            if t - caps[i - 1]["show"] < 0.3:
                continue  # the one before can't give the frames
            caps[i - 1]["hide"] = t
        nxt = caps[i + 1] if i + 1 < len(caps) else None
        hide = c["hide"] + max(0.0, t - c["show"])   # waiting for the cut, it keeps its time on screen (M4's
        if nxt is not None and hide > nxt["show"] + 1e-9:   # "then he" lost 2 of its frames and failed its read)
            if (nxt["hide"] - hide) < _cap_need(nxt, fps):
                continue   # the one after can't give the frames either: it stays before the cut
            nxt["show"] = hide
        if i and caps[i - 1]["hide"] < t and caps[i - 1]["hide"] >= c["show"] - 1e-9:
            caps[i - 1]["hide"] = t   # waiting for the cut: the one before stays up till then
        c["show"], c["hide"] = t, hide


def _plan_hands(a: dict, t: float) -> dict:
    """A planned standing actor's hands at time t in world studs, as its pose puts them, with whether each is a
    gesture (raised above the shoulder, flung out past 2.2 studs from the body's centre line, or held out ahead;
    arms folded across the chest, the hands ahead of it but within 0.8 of the centre line, aren't: a close-up cuts
    their shoulders as it cuts any arm, and the fold still reads)."""
    import pose
    pos = a["cf"]["pos"]
    look = a["cf"].get("look") or [pos[0], pos[1], pos[2] + 1.0]
    d = [look[0] - pos[0], 0.0, look[2] - pos[2]]
    n = math.hypot(d[0], d[2]) or 1.0
    d = [d[0] / n, 0.0, d[2] / n]
    right = (-d[2], 0.0, d[0])
    joints, rootpos = pose.at(a.get("poses") or [[0.0, "idle"]], float(t), drift_amount=0.0,
                              planted=a.get("planted", True))
    out = {}
    limbs = pose.limbs(joints, rootpos)
    for arm, (x, y, z) in pose.hands(joints, rootpos).items():
        world = [pos[i] + x * right[i] + (y if i == 1 else 0.0) - z * d[i] for i in range(3)]
        outer = [[pos[i] + c[0] * right[i] + (c[1] if i == 1 else 0.0) - c[2] * d[i] for i in range(3)]
                 for c in limbs[arm]]
        span = max(abs(c[0]) for c in limbs[arm])   # elbows out (hands on hips) count, not only the hand
        folded = abs(x) < 0.8 and y < 0.5
        out[arm] = (world, y > 0.5 or abs(x) > 2.2 or span > 2.3 or (z < -1.4 and not folded), outer)
    return out


def _plan_face(a: dict, t: float) -> list:
    """A planned actor's face at time t in its shot, as its pose puts it (_posed_points); a walker's rest face at
    the walk's end."""
    pos = a["walk"]["to"] if a.get("walk") else a["cf"]["pos"]
    look = a["cf"].get("look") or [pos[0], pos[1], pos[2] + 1.0]
    d = [look[0] - pos[0], 0.0, look[2] - pos[2]]
    n = math.hypot(d[0], d[2]) or 1.0
    d = [d[0] / n, 0.0, d[2] / n]
    keys = [[0.0, "idle"]] if a.get("walk") else (a.get("poses") or [[0.0, "idle"]])
    return _posed_points(pos, d, keys, t, a.get("planted", True))[1]


def _framing(plan: dict, size=(1080, 1920)) -> list[str]:
    """Actors a shot lists but its camera never shows: each one's head (and a walk's both ends) projected through
    the camera at the shot's start, middle and end. A portrait frame is narrow: at 15 studs, a 58-degree camera sees
    about 4.7 studs either side of its centre, so a hallway's sides are out of shot (M4's first stills: the gossips
    by the lockers never appeared). Then each face mid-shot, where its pose puts it: under the caption block, cut by
    an edge of the frame (M3's second review: half-faces at both edges of the chat), or down where the Shorts UI
    covers it (M5's slumped close-up). Warnings, not failures: an actor can be meant to wait out of shot."""
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
                continue
            # the face against the caption block: stories caption high (centre 24.8% down), comedy low (77.9%)
            face = _plan_face(a, s["seconds"] / 2)
            xy = camera.project(views[1], face, size=size)
            if not xy or not 0 <= xy[0] <= w:
                continue
            look = a["cf"].get("look")
            fwd = ([a["walk"]["to"][0] - a["walk"]["from"][0], a["walk"]["to"][2] - a["walk"]["from"][2]] if a.get("walk")
                   else [look[0] - a["cf"]["pos"][0], look[2] - a["cf"]["pos"][2]] if look else None)
            cam = views[1]["pos"]
            if fwd and fwd[0] * (cam[0] - face[0]) + fwd[1] * (cam[2] - face[2]) < 0:
                continue   # its back to the camera (an over-the-shoulder's near actor): no face to cut or cover
            if not a.get("walk") and 0 <= xy[1] <= h:
                said = set()   # at a quarter, half, three quarters and the end: a gesture can come late (M3's cheer)
                for tq in (0.25, 0.5, 0.75, 0.98):
                    vq = path(s["seconds"] * tq)
                    for arm, (hand, gesture, block) in _plan_hands(a, s["seconds"] * tq).items():
                        if not gesture or arm in said:
                            continue
                        pts = [camera.project(vq, q, size=size) for q in [hand] + block]
                        # the hand outside, or half the arm's block: the gesture is lost (M3's hook: the hands in,
                        cut = sum(1 for q in pts[1:] if not q or not (0 <= q[0] <= w and 0 <= q[1] <= h))   # the
                        hp = pts[0]                                                          # arms off both edges)
                        if not hp or not (0 <= hp[0] <= w and 0 <= hp[1] <= h) or cut >= 4:
                            said.add(arm)
                            out.append(f"{s['name']}: {name}'s {'right' if arm == 'rs' else 'left'} arm leaves the "
                                       f"frame at {s['seconds'] * tq:.1f} s (a gesture cut off: frame wider, or turn "
                                       f"the camera toward it)")
            frac = xy[1] / h
            top = camera.project(views[1], [face[0], face[1] + 0.6, face[2]], size=size)
            r = abs(xy[1] - top[1]) if top else 0.0   # the head's radius on screen, in pixels
            edge = min((xy[0], "left"), (w - xy[0], "right"), (xy[1], "top"), key=lambda e: e[0])
            if 0 <= frac <= 1.0 and edge[0] < 0.6 * r:   # past an eye
                out.append(f"{s['name']}: {name}'s face is cut by the frame's {edge[1]} edge")
            elif 0.85 < frac <= 1.0:
                out.append(f"{s['name']}: {name}'s face is {frac:.0%} down, on the frame's bottom edge where the "
                           f"Shorts UI covers it (frame it above 85%)")
            if plan.get("family") == "story" and 0.0 <= frac < 0.36:
                out.append(f"{s['name']}: {name}'s face is {frac:.0%} down, under the story captions (frame it "
                           f"below 36%)")
            elif plan.get("family") == "comedy" and 0.66 < frac <= 1.0:
                out.append(f"{s['name']}: {name}'s face is {frac:.0%} down, under the comedy captions (frame it "
                           f"above 66%)")
    return out


def _head_on_screen(view: dict, a: dict, t: float, size) -> tuple | None:
    """Where an actor's head lands and how big it is (radius in pixels), and the camera's angle round it (degrees
    from its face, and above it), or None when the head is out of frame or behind the camera."""
    import camera
    if a.get("walk"):   # where the walk has it at t (shot_fn's walk)
        import pose
        w = a["walk"]
        dist = math.dist(w["from"], w["to"])
        u = min(1.0, pose.walk_travel(max(0.0, t - w.get("start", 0.0)), freq=w.get("freq", 1.5)) / dist) if dist else 1.0
        p = [w["from"][k] + (w["to"][k] - w["from"][k]) * u for k in range(3)]
        head = [p[0], p[1] + HEAD, p[2]]
        d = [w["to"][0] - w["from"][0], 0.0, w["to"][2] - w["from"][2]]
    else:
        pos = a["cf"]["pos"]
        look = a["cf"].get("look") or [pos[0], pos[1], pos[2] + 1.0]
        d = [look[0] - pos[0], 0.0, look[2] - pos[2]]
        n = math.hypot(d[0], d[2]) or 1.0
        head = _posed_points(pos, [d[0] / n, 0.0, d[2] / n], a.get("poses") or [[0.0, "idle"]], t,
                             a.get("planted", True))[0]
    xy = camera.project(view, head, size=size)
    top = camera.project(view, [head[0], head[1] + 0.6, head[2]], size=size)
    if not xy or not top or not (0 <= xy[0] <= size[0] and 0 <= xy[1] <= size[1]):
        return None
    c = view["pos"]
    v = [c[0] - head[0], c[1] - head[1], c[2] - head[2]]
    yaw = math.degrees(math.atan2(v[0] * d[2] - v[2] * d[0], v[0] * d[0] + v[2] * d[2]))   # 0: in front of it
    pitch = math.degrees(math.atan2(v[1], math.hypot(v[0], v[2])))
    return abs(xy[1] - top[1]), yaw, pitch


def _hidden_subjects(plan: dict, size=(1080, 1920)) -> list[str]:
    """Each overlay's point (what the icon pops over, before its lift) against every standing actor nearer the
    camera when it pops: inside that actor's silhouette on screen (its body and arms as a box), the subject is
    hidden and the icon lands on the actor. An overlay over an actor's own head isn't counted against it."""
    import camera
    out = []
    for s in plan["shots"]:
        path = None
        for ov in s.get("overlays", []):
            if path is None:
                path = camera.moves([(k[0], k[1], k[2], k[3]) for k in s["camera"]])
            t = min(max(0.0, ov["start"] + 0.1), s["seconds"] - 1e-3)
            v = path(t)
            p = ov["over"]
            xy = camera.project(v, p, size=size)
            if not xy:
                continue
            dp = math.dist(v["pos"], p)
            for name, a in s.get("actors", {}).items():
                if a.get("walk"):
                    continue
                pos = a["cf"]["pos"]
                look = a["cf"].get("look") or [pos[0], pos[1], pos[2] + 1.0]
                d = [look[0] - pos[0], 0.0, look[2] - pos[2]]
                n = math.hypot(d[0], d[2]) or 1.0
                d = [d[0] / n, 0.0, d[2] / n]
                right = (-d[2], 0.0, d[0])
                x0, x1, z0, z1 = _reach(a.get("poses"))
                # round its own head (M4's bells set about it): the icon's subject, not hidden by it
                if math.dist(p, [pos[0], pos[1] + HEAD, pos[2]]) < 2.0:
                    continue
                corners = [[pos[i] + lx * right[i] + (ly if i == 1 else 0.0) - lz * d[i] for i in range(3)]
                           for lx in (x0, x1) for ly in (-3.0, HEAD + 0.6) for lz in (z0, z1)]
                pts = [camera.project(v, c, size=size) for c in corners]
                if any(q is None for q in pts) or math.dist(v["pos"], pos) >= dp - 1.0:
                    continue   # not a stud nearer the camera than the point: beside it, not in front
                xs, ys = [q[0] for q in pts], [q[1] for q in pts]
                # the silhouette's box, arms and all: an arm hangs at its sides, so no narrowing across (a 12% cut
                mx, my = 0.0, 0.05 * (max(ys) - min(ys))   # let a bubble on Max's sleeve pass: M5's round 2)
                if min(xs) + mx < xy[0] < max(xs) - mx and min(ys) + my < xy[1] < max(ys) - my:
                    out.append(f"{s['name']}: the {ov.get('icon') or 'text'} at {ov['start']:.2f} s pops over a point "
                               f"hidden behind {name} (it lands on {name}): move the subject or the camera")
                    break
    return out


def _jump_cuts(plan: dict, size=(1080, 1920)) -> list[str]:
    """Across each cut, anyone in frame on both sides at nearly the same size (under 1.4x) and from nearly the same
    angle (under 25 degrees round, 15 up or down): a jump cut. Change the size 1.5x or more, or the angle 30
    degrees or more, or cut to someone else."""
    import camera
    out = []
    shots = plan["shots"]
    for a, b in zip(shots, shots[1:]):
        va = camera.moves([(k[0], k[1], k[2], k[3]) for k in a["camera"]])(max(0.0, a["seconds"] - 1e-3))
        vb = camera.moves([(k[0], k[1], k[2], k[3]) for k in b["camera"]])(0.0)
        for name in set(a.get("actors", {})) & set(b.get("actors", {})):
            ha = _head_on_screen(va, a["actors"][name], a["seconds"], size)
            hb = _head_on_screen(vb, b["actors"][name], 0.0, size)
            if not ha or not hb or min(ha[0], hb[0]) < 1:
                continue
            ratio = max(ha[0], hb[0]) / min(ha[0], hb[0])
            turn = abs((ha[1] - hb[1] + 180) % 360 - 180)
            tilt = abs(ha[2] - hb[2])
            if ratio < 1.4 and turn < 25 and tilt < 15:
                out.append(f"{a['name']} -> {b['name']}: {name} at {ratio:.2f}x the size, {turn:.0f} degrees round, "
                           f"{tilt:.0f} up or down across the cut: a jump cut (change the size 1.5x, or the angle "
                           f"30 degrees)")
    return out


def _reach(poses: list) -> tuple:
    """The floor box an actor covers over every pose it takes, in its own axes (pose.reach())."""
    import pose
    boxes = [pose.reach(pose.at([[0.0, p[1]]], 0.0, drift_amount=0.0)[0]) for p in (poses or [[0.0, "idle"]])]
    return (min(b[0] for b in boxes), max(b[1] for b in boxes), min(b[2] for b in boxes), max(b[3] for b in boxes))


def _footprint(pos, d, box) -> tuple:
    """A floor box in the world: its corners, and its two axes (the actor's right and back)."""
    right, back = (-d[2], d[0]), (-d[0], -d[2])
    corners = [(pos[0] + lx * right[0] + lz * back[0], pos[2] + lx * right[1] + lz * back[1])
               for lx in box[:2] for lz in box[2:]]
    return corners, (right, back)


def _overlap(a, b) -> float:
    """How deep two floor boxes (_footprint) overlap, in studs; 0 when they're apart (the separating axis test)."""
    depth = float("inf")
    for ax in a[1] + b[1]:
        pa = [c[0] * ax[0] + c[1] * ax[1] for c in a[0]]
        pb = [c[0] * ax[0] + c[1] * ax[1] for c in b[0]]
        o = min(max(pa), max(pb)) - max(min(pa), min(pb))
        if o <= 0:
            return 0.0
        depth = min(depth, o)
    return depth


def _staging(plan: dict, least: float = 0.15) -> list[str]:
    """Actors inside each other: each one's floor box (body and arms, over every pose it takes) against every other
    standing within 2 studs of its height, and a walk's box at every half stud of its path against those standing
    (M4's second review: Leo walked through two students 2.6-2.8 studs from his path; M3's first, her elbow through
    his arm at 3 studs). Two R6s side by side need 4 studs between them. Warnings, like the framing ones."""
    from itertools import combinations
    out = []
    for s in plan["shots"]:
        boxes, walks = {}, {}
        for name, a in s.get("actors", {}).items():
            if a.get("walk"):
                w = a["walk"]
                walks[name] = (w["from"], w["to"])
                continue
            pos = a["cf"]["pos"]
            look = a["cf"].get("look") or [pos[0], pos[1], pos[2] + 1.0]
            d = [look[0] - pos[0], 0.0, look[2] - pos[2]]
            n = math.hypot(d[0], d[2]) or 1.0
            boxes[name] = (pos, _footprint(pos, [d[0] / n, 0.0, d[2] / n], _reach(a.get("poses"))))
        for (n1, (p1, f1)), (n2, (p2, f2)) in combinations(boxes.items(), 2):
            depth = _overlap(f1, f2) if abs(p1[1] - p2[1]) < 2.0 else 0.0
            if depth > least:
                out.append(f"{s['name']}: {n1} and {n2} overlap by {depth:.1f} studs (an arm through the other: stand "
                           f"them further apart)")
        for name, (p0, p1) in walks.items():
            run = [p1[0] - p0[0], 0.0, p1[2] - p0[2]]
            length = math.hypot(run[0], run[2])
            if length < 1e-6:
                continue
            d = [run[0] / length, 0.0, run[2] / length]
            x0, x1, z0, z1 = _reach([[0.0, "idle"]])
            box = (x0, x1, z0 - 0.4, z1 + 0.4)   # the arms swing
            worst = {}
            for k in range(int(length / 0.5) + 1):
                f = min(1.0, k * 0.5 / length)
                here = [p0[0] + run[0] * f, p0[1], p0[2] + run[2] * f]
                mine = _footprint(here, d, box)
                for other, (q, fo) in boxes.items():
                    if abs(q[1] - here[1]) < 2.0:
                        worst[other] = max(worst.get(other, 0.0), _overlap(mine, fo))
            for other, depth in worst.items():
                if depth > least:
                    out.append(f"{s['name']}: {name}'s walk passes through {other} (by {depth:.1f} studs: give the "
                               f"path 4 studs' room)")
    return out


def _cameras_in_sets(plan: dict, spec: dict, step: float = 0.25) -> list[str]:
    """Each shot's camera, every `step` seconds, against its set as built (kit.boxes): outside the room (above its
    ceiling, behind a wall) or inside any part, with 0.08 studs' margin for the lens. M4's first top-down shot sat
    above the classroom's ceiling and filmed white; M5's first push in `aced` started inside a parked car."""
    import camera
    import kit
    places = {None: (spec.get("set", "baseplate"), spec.get("set_options", {}), (0.0, 0.0, 0.0))}
    for extra in spec.get("sets", []):
        places[extra["id"]] = (extra["name"], extra.get("options", {}), tuple(extra["at"]))
    built = {}
    out = []
    for s in plan["shots"]:
        key = s.get("set")
        if key not in places or places[key][0] not in kit.SETS:
            continue
        if key not in built:
            name, opt, off = places[key]
            st = kit.SETS[name](opt)
            room = st.bounds and tuple(v + off[i // 2] for i, v in enumerate(st.bounds))
            built[key] = (room, kit.boxes(st, off))
        room, parts = built[key]
        path = camera.moves([(k[0], k[1], k[2], k[3]) for k in s["camera"]])
        t, said = 0.0, set()
        while t <= s["seconds"] + 1e-9:
            p = path(min(t, s["seconds"] - 1e-3))["pos"]
            if room and not (room[0] < p[0] < room[1] and room[2] < p[1] < room[3] and room[4] < p[2] < room[5]):
                if "room" not in said:
                    out.append(f"{s['name']}: the camera leaves the room at {t:.2f} s (at {[round(v, 1) for v in p]}: "
                               f"above the ceiling or behind a wall)")
                    said.add("room")
            else:
                m = 0.08
                for b in parts:
                    if b[0] - m < p[0] < b[1] + m and b[2] - m < p[1] < b[3] + m and b[4] - m < p[2] < b[5] + m:
                        if b not in said:
                            out.append(f"{s['name']}: the camera is inside a part of the set at {t:.2f} s (a box "
                                       f"{b[1] - b[0]:.1f} x {b[3] - b[2]:.1f} x {b[5] - b[4]:.1f} at "
                                       f"{[round((b[0] + b[1]) / 2, 1), round((b[2] + b[3]) / 2, 1), round((b[4] + b[5]) / 2, 1)]})")
                            said.add(b)
                        break
            t += step
    return out


def _in_furniture(plan: dict, spec: dict, least: float = 0.15) -> list[str]:
    """Each standing actor's parts (torso, head, arms and legs, each where its poses put it: pose.limbs) against every
    part of its set as built, props and pets included: overlapping one by more than `least` studs on all three axes,
    it is inside it (M5's round 2: Max and his dog in the coffee table for four shots, the dog's head on the tabletop).
    The room's shell and anything flat on the floor don't count."""
    import kit
    import pose
    places = {None: (spec.get("set", "baseplate"), spec.get("set_options", {}), (0.0, 0.0, 0.0))}
    for extra in spec.get("sets", []):
        places[extra["id"]] = (extra["name"], extra.get("options", {}), tuple(extra["at"]))
    built, out = {}, []
    for s in plan["shots"]:
        key = s.get("set")
        if key not in places or places[key][0] not in kit.SETS:
            continue
        if key not in built:
            name, opt, off = places[key]
            st = kit.SETS[name](opt)
            room = st.bounds and tuple(v + off[i // 2] for i, v in enumerate(st.bounds))
            parts = []
            for b in kit.boxes(st, off):
                if b[3] - b[2] < 0.2 and b[3] < 0.3:
                    continue   # flat on the floor: a rug, a court line, the floor
                if room and (b[0] < room[0] - 0.5 or b[1] > room[1] + 0.5 or b[4] < room[4] - 0.5 or b[5] > room[5] + 0.5
                             or b[2] > room[3] - 0.6):
                    continue   # a wall, the ceiling, the floor slab: the room's shell
                parts.append(b)
            built[key] = parts
        for name, a in s.get("actors", {}).items():
            if a.get("walk"):
                continue
            pos = a["cf"]["pos"]
            look = a["cf"].get("look") or [pos[0], pos[1], pos[2] + 1.0]
            d = [look[0] - pos[0], 0.0, look[2] - pos[2]]
            n = math.hypot(d[0], d[2]) or 1.0
            d = [d[0] / n, 0.0, d[2] / n]
            right = (-d[2], 0.0, d[0])
            worst, what = 0.0, None
            for p in (a.get("poses") or [[0.0, "idle"]]):
                joints, rootpos = pose.at([[0.0, p[1]]], 0.0, drift_amount=0.0, planted=a.get("planted", True))
                for corners in pose.limbs(joints, rootpos).values():
                    w = [[pos[i] + c[0] * right[i] + (c[1] if i == 1 else 0.0) - c[2] * d[i] for i in range(3)]
                         for c in corners]
                    lo = [min(v[i] for v in w) for i in range(3)]
                    hi = [max(v[i] for v in w) for i in range(3)]
                    for b in built[key]:
                        depth = min(min(hi[0], b[1]) - max(lo[0], b[0]), min(hi[1], b[3]) - max(lo[1], b[2]),
                                    min(hi[2], b[5]) - max(lo[2], b[4]))
                        if depth > worst:
                            worst, what = depth, b
            if worst > least:
                size = [round(what[1] - what[0], 1), round(what[3] - what[2], 1), round(what[5] - what[4], 1)]
                at = [round((what[0] + what[1]) / 2, 1), round((what[2] + what[3]) / 2, 1), round((what[4] + what[5]) / 2, 1)]
                out.append(f"{s['name']}: {name} is inside a part of the set by {worst:.1f} studs (a box "
                           f"{size[0]} x {size[1]} x {size[2]} at {at}): move one of them")
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
    for ov in spec.get("overlays", []):   # an icon over a point given in the set's own frame (M5: every bubble
        ov["over"] = mv(ov["over"])       # outside the street sat 600-900 studs off and was never drawn)
    spec["_shifted"] = True


def _seeds(plan_path: str, names: list) -> list:
    """Each shot's seed (its hold's drift): the one it had in the plan already made, by name, so a shot put in
    before others doesn't change theirs and make every later shot stale (M3's third round: "slides" put in before
    five shots); a new shot takes the lowest seed not taken, its place in a first plan."""
    old = {}
    if os.path.exists(plan_path):
        try:
            old = {x["name"]: x["seed"] for x in _load(plan_path).get("shots", []) if "seed" in x}
        except (ValueError, KeyError):
            old = {}
    kept = {n: old[n] for n in names if n in old}
    taken, out = set(kept.values()), []
    for k, n in enumerate(names):
        if n in kept:
            out.append(kept[n])
            continue
        seed = k
        while seed in taken:
            seed += 1
        taken.add(seed)
        out.append(seed)
    return out


def stage_plan(sh: Short, keep_shots: bool = False, replan: list | None = None, write: bool = True) -> bool:
    """Time the whole video: shot lengths (from the lines when 'auto'), every word-anchored key, the captions.

    `keep_shots`, for a video already shot: every shot's timing, camera and actors (what its frames show) stay as
    in the plan already made; the overlays, effects and captions (drawn and mixed after the shoot) follow the
    current word times. Refused if a shot or a line would move. `replan`: shots that take the spec's current camera
    and actors within their kept timing, to be shot again (`shoot --only`). `write` False (`plan --check`): print
    the times and every warning but write nothing, to try a restage while that video's shots are being shot."""
    words = _words(sh)
    lines = sh.lines()
    fps = sh.fps
    before = _load(sh.path("plan.json")) if keep_shots else None
    seeds = _seeds(sh.path("plan.json"), [x["name"] for x in sh.spec["shots"]])
    if before and [x["name"] for x in before["shots"]] != [x["name"] for x in sh.spec["shots"]]:
        print("plan --keep-shots: the spec's shots aren't the ones planned; plan and shoot again instead")
        return False
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
        if before:   # the timing the frames were shot to
            kept = before["shots"][len(shots)]
            n, t = kept["frames"], kept["start"]
            frame0 = kept["frame0"]
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

        spec["_poses"] = {name: [[res(p[0]), p[1]] for p in a.get("poses", [[0, "idle"]])]
                          for name, a in spec.get("actors", {}).items() if not a.get("walk")}
        cam = []
        for key in spec.get("camera", []):
            kt = res(key.get("t", 0.0))
            cam.append([kt, _view(spec, key, kt), float(key.get("move", 0.0)), key.get("ease", "out")])
        if not cam:
            raise SystemExit(f"shot {spec['name']}: no camera")
        actors = {}
        for name, a in spec.get("actors", {}).items():
            pos = _vec(a.get("at", [0, 3, 0]))
            d = _actor_dir(spec, name)
            actors[name] = {"planted": a.get("planted", True),
                            "cf": {"pos": pos, "look": [pos[0] + d[0] * 10, pos[1], pos[2] + d[2] * 10]},
                            "poses": [[res(p[0]), p[1]] + [float(x) for x in p[2:3]]   # (t, pose, snap s)
                                      for p in a.get("poses", [[0, "idle"]])],
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
                           "shot": spec["name"],
                           "hit": bool(fx_.get("hit", fx_["sound"] in ("boom", "thud", "ding")))})
            if sounds[-1]["hit"]:
                hits.append({"frame": int(round(at * fps)), "what": f"{fx_['sound']} in {spec['name']}"})
        overlays = []
        for ov in spec.get("overlays", []):
            ot = res(ov.get("at", 0.0))
            overlays.append({"icon": ov.get("icon"), "text": ov.get("text"), "over": _point(spec, ov["over"], ot),
                             "start": ot, "dur": float(ov.get("dur", 0.6)),
                             "size": float(ov.get("size", 150)), "lift": float(ov.get("lift", 1.4))})
        plan["shots"].append({"overlays": overlays, "name": spec["name"], "set": spec.get("set"), "start": st,
                              "frames": s["frames"],
                              "frame0": s["frame0"],
                              "seconds": s["frames"] / fps, "camera": cam, "actors": actors,
                              "drift": spec.get("drift", 1.0), "streak": bool(spec.get("streak")),
                              "seed": seeds[k]})
    if before:
        moved = [v["line"] for v, w in zip(sorted(voices, key=lambda v: v["line"]),
                                           sorted(before["voices"], key=lambda v: v["line"]))
                 if v["line"] != w["line"] or abs(v["start"] - w["start"]) > 1e-6]
        if moved or len(voices) != len(before["voices"]):
            print(f"plan --keep-shots: lines would move ({moved}); plan and shoot again instead")
            return False
        for new_shot, old_shot in zip(plan["shots"], before["shots"]):
            if new_shot["name"] not in (replan or []):   # what the frames show stays as shot
                new_shot["camera"], new_shot["actors"] = old_shot["camera"], old_shot["actors"]
        print(f"plan --keep-shots: {len(plan['shots'])} shots kept as shot"
              + (f", {len(replan)} restaged to shoot again ({', '.join(replan)})" if replan else "")
              + "; overlays, effects and captions timed again")
    # A ding rung within 0.3 s of another is part of its burst, not a hit of its own: its onset can't rise 6 dB over
    # the last one's ring, so the sync check would flag every one (M4's "then twenty": six dings 0.07 s apart).
    last_ding = -1e9
    for x in sorted(sounds, key=lambda x: x["start"]):
        if x["sound"] == "ding":
            if x["start"] - last_ding < 0.3:
                x["hit"] = False
            last_ding = x["start"]
    hits = [{"frame": int(round(x["start"] * fps)), "what": f"{x['sound']} in {x['shot']}"} for x in sounds if x["hit"]]
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
        heard = _audible_onset(sh.path("voice", words[v["line"]].get("file", v["line"] + ".wav")))
        for k, (text, a, b) in enumerate(_clauses(aligned, style, emoji, story=(style == "story"), names=names)):
            if k == 0:
                a = min(max(a, heard), b - 0.05)   # not before the line is heard
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
    if write:
        _save(sh.path("plan.json"), plan)
    import captions as _c
    cut = {"fps": fps, "clips": [{"name": s["name"], "frames": s["frames"]} for s in plan["shots"]],
           "texts": [{"text": re.sub(r"\{\w+:([^}]*)\}", r"\1",   # the words as read: no emoji, no {colour:...}
                                     " ".join(t for t in c["text"].split() if not _c.is_emoji(t))),
                      "start": _caption_frames(c, fps)[0],
                      "frames": _caption_frames(c, fps)[1] - _caption_frames(c, fps)[0],
                      "speech": c["style"] in ("comedy", "story")} for c in caps],
           "hits": hits, "silences": [], "cues": []}
    if write:
        _save(sh.path("cut.json"), cut)
    else:
        print("plan --check: nothing written")
    print(f"plan: {len(plan['shots'])} shots, {total:.2f} s ({frame0} frames at {fps}), {len(voices)} lines, "
          f"{len(caps)} captions, {len(sounds)} effects ({len(hits)} hits)")
    for s in plan["shots"]:
        print(f"  {s['name']}: {s['start']:.2f}-{s['start'] + s['seconds']:.2f} s ({s['frames']} frames)")
    for warn in _framing(plan):
        print(f"  framing: {warn}")
    for warn in _staging(plan):
        print(f"  staging: {warn}")
    for warn in _jump_cuts(plan):
        print(f"  cut: {warn}")
    for warn in _hidden_subjects(plan):
        print(f"  overlay: {warn}")
    for warn in _cameras_in_sets(plan, sh.spec):
        print(f"  camera: {warn}")
    for warn in _in_furniture(plan, sh.spec):
        print(f"  staging: {warn}")
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
            if a.get("walk"):
                w = a["walk"]
                tw = max(0.0, t - w["start"])   # before it starts: waiting at the start, facing the way it'll go
                dist = math.dist(w["from"], w["to"])
                trav = min(pose.walk_travel(tw, freq=w["freq"]), dist)
                u = trav / dist if dist else 1.0
                pos = [w["from"][j] + (w["to"][j] - w["from"][j]) * u for j in range(3)]
                d = [w["to"][0] - w["from"][0], 0.0, w["to"][2] - w["from"][2]]
                if trav >= dist:   # arrived: turn to the mark's facing over 0.3 s (M4's "Leo sat down" stayed in
                    arrive = dist / max(pose.walk_travel(1.0, freq=w["freq"]), 1e-6)   # profile, the walk's way)
                    k = min(1.0, max(0.0, (tw - arrive) / 0.3))
                    k = k * k * (3 - 2 * k)
                    f = [cf["look"][0] - cf["pos"][0], 0.0, cf["look"][2] - cf["pos"][2]]
                    n0, n1 = math.hypot(d[0], d[2]) or 1.0, math.hypot(f[0], f[2]) or 1.0
                    a0, a1 = math.atan2(d[2] / n0, d[0] / n0), math.atan2(f[2] / n1, f[0] / n1)
                    turn = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
                    d = [math.cos(a0 + turn * k), 0.0, math.sin(a0 + turn * k)]
                cf = {"pos": pos, "look": [pos[0] + d[0], pos[1], pos[2] + d[2]]}
                if t >= w["start"] and trav < dist:   # walking from its first frame (a walk from 0 held its pose
                    joints, rootpos = pose.walking(tw, freq=w["freq"])   # on frame 0: M2's run flicked a cheer)
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


def _shot_key(plan: dict, shot: dict) -> str:
    """What a shot's frames depend on in the plan (its camera, actors, length, frame rate), as a short hash. The shoot
    stamps each shot's folder with it, and shoots a shot again when its plan has changed since."""
    import hashlib
    keep = {"fps": plan["fps"], "frames": shot["frames"], "camera": shot["camera"], "actors": shot["actors"],
            "drift": shot.get("drift", 1.0), "seed": shot.get("seed", 0)}
    return hashlib.sha1(json.dumps(keep, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def _stale_frames(d: str, key: str) -> bool:
    """True when a shot's folder was shot from another plan (its stamp differs). A folder without a stamp (shot before
    stamps) counts as current."""
    stamp = os.path.join(d, "_shot.json")
    if not os.path.exists(stamp):
        return False
    try:
        return json.load(open(stamp, encoding="utf-8")).get("key") != key
    except (OSError, ValueError):
        return True


def stage_shoot(sh: Short, only: list[str] | None = None, stills: bool = False, frames: list[int] | None = None) -> bool:
    """Shoot every shot's frames (or `only` some), resuming each from its last frame; a shot whose plan has changed
    since it was shot is shot again. `stills`: one frame from the middle of each, to look at first. `frames`: take
    just these frames of each shot again, over the ones there (a fix to a frame or two)."""
    import capture
    plan = _load(sh.path("plan.json"))
    todo = [s for s in plan["shots"] if not only or s["name"] in only]

    def body(cast):
        for s in todo:
            d = sh.path("stills" if stills else "shots", s["name"])
            if frames:
                want = [k for k in frames if 0 <= k < s["frames"]]
                capture.take(d, shot_fn(plan, s, cast), seconds=s["seconds"], fps=plan["fps"], only=want,
                             warmup=3.0, portrait=True)
                print(f"{s['name']}: frames {want} again")
                continue
            if stills:
                mid = s["frames"] // 2
                capture.take(d, shot_fn(plan, s, cast), seconds=s["seconds"], fps=plan["fps"], only=[mid],
                             warmup=2.0, portrait=True)
                continue
            key = _shot_key(plan, s)
            if _stale_frames(d, key):   # restaged since it was shot: its frames are from another plan
                print(f"{s['name']}: its plan changed since it was shot: shooting it again")
                for f in os.listdir(d):
                    if f.startswith("f") and f.endswith(".png"):
                        os.remove(os.path.join(d, f))
            have = _done_frames(d, s["frames"])
            if have >= s["frames"]:
                print(f"{s['name']}: done")
                continue
            t0 = time.time()
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "_shot.json"), "w", encoding="utf-8") as fh:
                json.dump({"key": key, "frames": s["frames"]}, fh)
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


def _heads(shot: dict, t: float) -> list:
    """The head centres of a planned shot's standing actors at time t, as posed (a walker's isn't known here)."""
    out = []
    for a in shot.get("actors", {}).values():
        if a.get("walk"):
            continue
        pos = a["cf"]["pos"]
        look = a["cf"].get("look") or [pos[0], pos[1], pos[2] + 1.0]
        d = [look[0] - pos[0], 0.0, look[2] - pos[2]]
        n = math.hypot(d[0], d[2]) or 1.0
        out.append(_posed_points(pos, [d[0] / n, 0.0, d[2] / n], a.get("poses") or [[0.0, "idle"]], t,
                                 a.get("planted", True))[0])
    return out


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
    heads = None
    for ov in shot.get("overlays", []):
        u = (k / fps - ov["start"]) / max(ov["dur"], 1e-3)
        if 0.0 <= u < 1.0:
            if heads is None:
                heads = _heads(shot, k / fps)
            out = _overlay(out, ov, _path_for(plan_path, shot["name"])(k / fps), u,
                           keep=ICON_BAND.get(plan.get("family"), (0.03, 0.97)), heads=heads)
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
    cut.json disagreed by a frame). Both ends are rounded as times, not the end as a length: a caption that hides
    when the next shows then ends on the frame the next begins (M4's review: rounding the length drew two captions
    on one frame, five times)."""
    f0 = int(round(c["show"] * fps))
    return f0, max(f0 + 1, int(round(c["hide"] * fps)))


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
        if not snd.get("hit") or snd.get("sound") not in ("boom", "thud"):
            continue   # a ding is a hit for the sync check, but the bell is its picture: no punch
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


# Where an icon may sit, as fractions of the height: clear of the family's caption block.
ICON_BAND = {"story": (0.33, 0.97), "comedy": (0.03, 0.70), "music": (0.20, 0.97)}


def _clear_of_faces(cx: float, cy: float, hw: float, hh: float, faces: list, size, keep, m: float) -> tuple:
    """An icon's centre moved off any face it would cover: beside that head, on the side it was nearer, level with
    the top of the head (M4's second review: in close-ups the captions' band pushed every bell onto a forehead).
    faces: (x, y, r) on screen, r the head's radius in pixels. Left where it is when no side has room."""
    w, h = size

    def covers(x, y):
        return [f for f in faces if abs(x - f[0]) < hw + 0.8 * f[2] and abs(y - f[1]) < hh + 0.9 * f[2]]

    hit = covers(cx, cy)
    if not hit:
        return cx, cy
    fx, fy, r = max(hit, key=lambda f: f[2])
    y = min(max(fy - 0.6 * r, keep[0] * h + hh), keep[1] * h - hh)
    for x in sorted((fx + 0.8 * r + hw + 6, fx - 0.8 * r - hw - 6), key=lambda v: abs(v - cx)):
        if hw + m <= x <= w - hw - m and not covers(x, y):
            return x, y
    return cx, cy


def _overlay(img: np.ndarray, ov: dict, view: dict, u: float, keep=(0.03, 0.97), heads=()) -> np.ndarray:
    """An icon, a line of text or both (the text over the icon) popping up over a point in the scene: projected
    through the shot's camera, scaled in with a little overshoot over the first fifth of its time, faded out over the
    last fifth. Text is drawn in the `label` style, its natural size at `size` 150 ("99%" over a head, a text in a
    speech bubble). An icon that would land off the frame, or in the captions' band, is pulled just inside `keep`
    (M4's review: in close-ups, 13 of 26 bells set around a head projected off screen), then moved off any face it
    would cover: `heads` are the head centres of the shot's actors, as posed (_clear_of_faces)."""
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
    h, w = img.shape[:2]
    faces = []
    for hd in heads:
        c = camera.project(view, hd, size=(w, h))
        top = camera.project(view, [hd[0], hd[1] + 0.6, hd[2]], size=(w, h))
        if c and top:
            faces.append((c[0], c[1], abs(c[1] - top[1])))
    for pic in pics:
        pic = pic.copy()
        pic[..., 3] *= alpha
        hw, hh = pic.shape[1] / 2, pic.shape[0] / 2
        m = 0.02 * w
        cx = min(max(xy[0], hw + m), w - hw - m)
        cy = min(max(xy[1], keep[0] * h + hh), keep[1] * h - hh)
        cx, cy = _clear_of_faces(cx, cy, hw, hh, faces, (w, h), keep, m)
        look.over(img, pic, int(cx - hw), int(cy - hh))
    return img


def stage_cut(sh: Short) -> bool:
    import render
    plan = _load(sh.path("plan.json"))
    missing = [s["name"] for s in plan["shots"] if _done_frames(sh.path("shots", s["name"]), s["frames"]) < s["frames"]]
    if missing:
        print("cut: shots not shot yet:", missing)
        return False
    stale = [s["name"] for s in plan["shots"] if _stale_frames(sh.path("shots", s["name"]), _shot_key(plan, s))]
    if stale:
        print("cut: shots shot from another plan (restaged since): shoot them again:", stale)
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
        # a bed under a voice fades at the end: a note cut off there clicked on every loop (M3's review); a music
        # format's track runs to the end, its length whole bars, so the loop comes round in phase (M2's review)
        n = min(len(bed), int(float(music.get("fade_out", 0.35 if music.get("duck", True) else 0.0)) * sr))
        if n:
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
    ap.add_argument("--frames", type=int, nargs="*", help="shoot: take only these frames of each shot again")
    ap.add_argument("--keep-shots", action="store_true",
                    help="plan: keep every shot's timing, camera and actors as shot; time overlays, effects and "
                         "captions again")
    ap.add_argument("--replan", nargs="*", default=[],
                    help="plan --keep-shots: shots that take the spec's current camera and actors, to shoot again")
    ap.add_argument("--check", action="store_true",
                    help="plan: print the times and warnings, write nothing (safe while the video is being shot)")
    args = ap.parse_args()
    sh = Short(args.video)
    t0 = time.time()
    if args.stage == "stills":
        ok = stage_shoot(sh, args.only, stills=True)
    elif args.stage == "shoot":
        ok = stage_shoot(sh, args.only, frames=args.frames)
    elif args.stage == "plan":
        ok = stage_plan(sh, keep_shots=args.keep_shots, replan=args.replan, write=not args.check)
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
