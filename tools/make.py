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
                dest = sh.path("raw", f"{ln['id']}_{k}.mp3")
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


def _caption_text(line: dict) -> str:
    """A line's caption: its `caption`, or its text without tags, starting lower case unless its first word is
    stressed, and its `emoji` at the end."""
    import speech
    if line.get("caption"):
        return line["caption"]
    text = speech.TAG.sub("", line["text"]).strip()
    text = re.sub(r"\s+", " ", text)
    first = text.split(" ", 1)[0] if text else ""
    if first and not first.isupper():
        text = text[0].lower() + text[1:]
    return text + (" " + line["emoji"] if line.get("emoji") else "")


def _aligned_words(line: dict, entry: dict) -> list[tuple[str, float, float]]:
    """The script's words (its spelling, its CAPS) with the times the transcriber heard them at: matched words take
    their heard times, unmatched ones are spread between their neighbours."""
    import difflib

    import speech
    script = speech.spoken(_caption_text(line).replace("’", "'"))
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


def _clauses(words: list, style: str, emoji: str | None, story: bool) -> list[tuple[str, float, float]]:
    """Words grouped into captions: story captions 1-3 words, breaking after punctuation; comedy captions a clause,
    breaking after sentence ends, and wherever the caption would need a fourth line."""
    import captions
    out, cur = [], []
    for i, (w, s, e) in enumerate(words):
        cur.append((w, s, e))
        last = i == len(words) - 1
        punct = w[-1:] in ".!?,;:" or w.endswith("...")
        if story:
            brk = punct or len(cur) >= 3 or sum(len(x[0]) for x in cur) >= 14
        else:
            brk = w[-1:] in ".!?" and not last
            if not brk and not last:
                trial = " ".join(x[0] for x in cur + [words[i + 1]])
                brk = len(captions.lines_of(trial, style)) > 3  # the references run a clause over 1-3 lines
        if brk or last:
            out.append([" ".join(x[0] for x in cur), cur[0][1], cur[-1][2]])
            cur = []
    if out and emoji:
        out[-1][0] += " " + emoji
    return [tuple(c) for c in out]


def stage_plan(sh: Short) -> bool:
    """Time the whole video: shot lengths (from the lines when 'auto'), every word-anchored key, the captions."""
    words = _words(sh)
    lines = sh.lines()
    fps = sh.fps
    shots, t, line_starts, frame0 = [], 0.0, {}, 0
    # shot lengths first: an 'auto' shot runs to its last line's end plus `pad`
    for spec in sh.spec["shots"]:
        says = spec.get("say", [])
        dur = spec.get("seconds", "auto")
        ends = []
        for s in says:
            at = s.get("at", 0.0)
            if not isinstance(at, (int, float)):
                at = _resolve(at, t, {**line_starts}, words)
            line_starts[s["line"]] = t + at
            ends.append(at + words[s["line"]]["duration"])
        if dur == "auto":
            if not ends:
                raise SystemExit(f"shot {spec['name']}: 'auto' length but no lines")
            dur = max(ends) + spec.get("pad", 0.12)
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
            actors[name] = {"cf": {"pos": pos, "look": [pos[0] + d[0] * 10, pos[1], pos[2] + d[2] * 10]},
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
        plan["shots"].append({"name": spec["name"], "start": st, "frames": s["frames"], "frame0": s["frame0"],
                              "seconds": s["frames"] / fps, "camera": cam, "actors": actors,
                              "drift": spec.get("drift", 1.0), "streak": bool(spec.get("streak")),
                              "seed": k})
    # captions: from the lines, in the family's style
    style = sh.spec.get("caption_style", CAPTION_STYLE.get(sh.family, "comedy"))
    caps = []
    for v in sorted(voices, key=lambda v: v["start"]):
        ln = lines[v["line"]]
        if ln.get("caption") is False:
            continue
        aligned = _aligned_words(ln, words[v["line"]])
        emoji = ln.get("emoji") if not ln.get("caption") else None
        for text, a, b in _clauses(aligned, style, emoji, story=(style == "story")):
            caps.append({"text": text, "start": v["start"] + a, "end": v["start"] + b, "style": style})
    lead = 2 / fps
    for i, c in enumerate(caps):
        nxt = caps[i + 1]["start"] - lead if i + 1 < len(caps) else total
        c["show"] = max(0.0, c["start"] - lead)
        c["hide"] = min(nxt, max(c["end"] + (0.35 if style != "story" else 0.12), c["show"] + 0.3), total)
    for extra in sh.spec.get("texts", []):
        caps.append({"text": extra["text"], "style": extra.get("style", "header"), "show": float(extra["from"]),
                     "hide": float(extra.get("to", total)), "start": float(extra["from"]), "end": float(extra.get("to", total))})
    plan["captions"] = caps
    plan["voices"], plan["sounds"] = voices, sounds
    plan["music"] = sh.spec.get("music")
    _save(sh.path("plan.json"), plan)
    import captions as _c
    cut = {"fps": fps, "clips": [{"name": s["name"], "frames": s["frames"]} for s in plan["shots"]],
           "texts": [{"text": " ".join(t for t in c["text"].split() if not _c.is_emoji(t)),
                      "start": int(round(c["show"] * fps)), "frames": max(1, int(round((c["hide"] - c["show"]) * fps))),
                      "speech": c["style"] in ("comedy", "story")} for c in caps],
           "hits": hits, "silences": [], "cues": []}
    _save(sh.path("cut.json"), cut)
    print(f"plan: {len(plan['shots'])} shots, {total:.2f} s ({frame0} frames at {fps}), {len(voices)} lines, "
          f"{len(caps)} captions, {len(sounds)} effects ({len(hits)} hits)")
    for s in plan["shots"]:
        print(f"  {s['name']}: {s['start']:.2f}-{s['start'] + s['seconds']:.2f} s ({s['frames']} frames)")
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
                    joints, rootpos = pose.at(a["poses"], t, drift_amount=a.get("drift", 1.0), seed=i + 1)
            else:
                joints, rootpos = pose.at(a["poses"], t, drift_amount=a.get("drift", 1.0), seed=i + 1)
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
    t = r / fps
    for c in plan["captions"]:
        if c["show"] <= t < c["hide"]:
            layer, (x, y) = _caption_layer(c["text"], c["style"])
            look.over(out, layer, x, y)
    return out


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
        end_clip, _ = _clip_at(plan, min(s["start"] + len(y) / sr, plan["seconds"] - 1e-6))
        mix.place("sfx", y, clip, at=at, gain_db=s.get("gain_db", 0.0),
                  until=end_clip if end_clip != clip else None, label=os.path.basename(s["sound"]))
    music = plan.get("music")
    gains = {"voice": 0.0, "sfx": -2.0, "music": -14.0}
    if music:
        start = float(music.get("start", 0.0))
        bed = _music(music, plan["seconds"] - start, sr)
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
