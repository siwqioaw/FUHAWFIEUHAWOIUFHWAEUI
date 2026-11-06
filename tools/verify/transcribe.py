"""Speech with word timings, from any video or audio file (a speech-to-text model that runs on this machine).

    python tools/verify/transcribe.py MEDIA [MEDIA ...] [--out DIR] [--model NAME] [--device auto]

For each file, writes DIR/<name>.json (segments, each with its words and their times) and DIR/<name>.md (one line per
segment with its times, then the speech rate and the pauses). Two uses:

- studying reference videos: what is said, when, and how fast (words a second, pauses between lines);
- timing word-by-word captions to a voice track you made, and checking the captions against the delivered file.

The word times are good to about a tenth of a second and can drift under music or effects; a word the model mishears
is spelled as it heard it. Where a video has burned-in captions, read the transcript against them.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time


def load(name: str, device: str):
    """(model, device). Tries the GPU first when device is auto; ctranslate2 needs CUDA 12 and cuDNN 9 for it."""
    from faster_whisper import WhisperModel
    tries = [("cuda", "float16"), ("cpu", "int8")] if device == "auto" else \
        [(device, "float16" if device == "cuda" else "int8")]
    last: Exception | None = None
    for dev, ct in tries:
        try:
            return WhisperModel(name, device=dev, compute_type=ct), dev
        except Exception as e:  # noqa: BLE001 - no GPU libraries: fall back to the CPU
            last = e
    raise RuntimeError(f"could not load {name}: {last}")


def run(model, path: str, language: str | None) -> dict:
    segs, info = model.transcribe(path, language=language, word_timestamps=True, beam_size=5,
                                  condition_on_previous_text=False, vad_filter=False)
    out = []
    for s in segs:  # the work happens here: the segments are a generator
        words = [{"start": round(w.start, 3), "end": round(w.end, 3), "word": w.word.strip(),
                  "p": round(w.probability, 3)} for w in (s.words or [])]
        out.append({"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip(), "words": words})
    return {"language": info.language, "duration": round(info.duration, 2), "segments": out}


def stats(res: dict, gap: float = 0.35) -> dict:
    words = [w for s in res["segments"] for w in s["words"]]
    if not words:
        return {"words": 0}
    span = words[-1]["end"] - words[0]["start"]
    pauses = [(round(a["end"], 2), round(b["start"], 2)) for a, b in zip(words, words[1:])
              if b["start"] - a["end"] >= gap]
    return {"words": len(words), "first_word": words[0]["start"], "last_word_end": words[-1]["end"],
            "words_per_s": round(len(words) / span, 2) if span > 0 else None,
            "pauses": [{"from": a, "to": b, "s": round(b - a, 2)} for a, b in pauses],
            "low_confidence": [{"t": w["start"], "word": w["word"], "p": w["p"]} for w in words if w["p"] < 0.5]}


def write(res: dict, name: str, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    st = res["stats"]
    lines = [f"# {name}", "", f"- {res['language']}, {res['duration']} s; {st['words']} words"]
    if st["words"]:
        lines += [f"- first word at {st['first_word']:.2f} s, last word ends at {st['last_word_end']:.2f} s",
                  f"- {st['words_per_s']} words a second over the spoken span",
                  "- pauses of 0.35 s or more: " + (", ".join(f"{p['from']:.2f}-{p['to']:.2f} ({p['s']:.2f} s)"
                                                            for p in st["pauses"]) or "none"),
                  "- words heard with low confidence: " + (", ".join(f"{w['t']:.2f} '{w['word']}' ({w['p']})"
                                                                     for w in st["low_confidence"]) or "none")]
    lines += ["", "## Lines", ""]
    lines += [f"- `{s['start']:6.2f}-{s['end']:6.2f}` {s['text']}" for s in res["segments"]]
    lines += ["", "## Words", "", " ".join(f"{w['word']}@{w['start']:.2f}" for s in res["segments"]
                                          for w in s["words"]), ""]
    with open(os.path.join(out_dir, name + ".md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("media", nargs="+")
    ap.add_argument("--out", default="build/transcripts")
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"])
    ap.add_argument("--language", default="en", help="'' to detect it")
    args = ap.parse_args()
    model, dev = load(args.model, args.device)
    print(f"model {args.model} on {dev}", flush=True)
    for path in args.media:
        name = os.path.splitext(os.path.basename(path))[0]
        t0 = time.time()
        try:
            res = run(model, path, args.language or None)
        except RuntimeError as e:  # the GPU libraries fail at the first inference, not at load
            if dev != "cuda":
                raise
            print(f"GPU failed ({e}); using the CPU", flush=True)
            model, dev = load(args.model, "cpu")
            res = run(model, path, args.language or None)
        res["file"] = os.path.basename(path)
        res["stats"] = stats(res)
        write(res, name, args.out)
        print(f"{name}: {res['stats']['words']} words, {time.time() - t0:.1f} s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
