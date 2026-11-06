"""Build a 6-second vertical test cut with failures planted in it, run every check on the delivered MP4, and confirm
each check catches what it should and passes what it should (docs/VERIFY.md, "Trusting the checks").

    python tests/selftest.py            -> build/selftest/ ; exits 1 if any check misbehaves

Planted: photosensitive flashes; a caption too short to read; an accent number (exempt); a black stretch; a sound
running across a cut undeclared; a declared bridge and a prelap (allowed); a click at a cut; a silence that isn't; a
picture hit with no sound on it. It also renders through render.py's worker processes, masters through master.py
(checked against ffmpeg's own loudness meter) and encodes through deliver.py, so a broken tool fails here first.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for sub in ("edit", "verify"):
    sys.path.insert(0, os.path.join(ROOT, "tools", sub))

import fx  # noqa: E402
import look  # noqa: E402
import typeset as ts  # noqa: E402

W, H, FPS = 270, 480, 30
CLIPS = [("hook", 60), ("flash", 45), ("calm", 75)]  # 2.0 s, 1.5 s, 2.5 s
OUT = os.path.join(ROOT, "build", "selftest")


def _scene(r: int) -> np.ndarray:
    """A moving gradient with a moving disc: never frozen, never black."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = 0.25 + 0.2 * np.sin((xx + 4 * r) / 37.0) * np.cos(yy / 53.0)
    img = np.dstack([g * 0.9, g * 1.1, g * 1.4]).astype(np.float32)
    cx, cy = W / 2 + 60 * np.sin(r / 9), H / 2 + 90 * np.cos(r / 13)
    disc = ((xx - cx) ** 2 + (yy - cy) ** 2) < 30 ** 2
    img[disc] = (0.95, 0.75, 0.2)
    return np.clip(img, 0, 1)


def frame_at(r: int) -> np.ndarray:
    if 60 <= r < 90:  # flash: white and black every 2 frames, 7.5 flashes a second
        return np.full((H, W, 3), 1.0 if (r // 2) % 2 == 0 else 0.0, np.float32)
    if 105 <= r < 117:  # 0.4 s of black at the start of calm
        return np.zeros((H, W, 3), np.float32)
    img = _scene(r)
    if r < 60:  # the hook: a reframed wide picture, shaken on its first frames, a word-by-word caption popping up
        wide = look.reframe(np.dstack([_scene(r)[:, :, ::-1]] * 1)[: H // 2], W, H, zoom=1.0)
        img = fx.shake(0.5 * img + 0.5 * wide, max(0.0, 1 - r / 8), seed=r)
        cap = ts.caption("you won't believe this", 30, W - 40, highlight=min(3, r // 12), stroke=0.14)
        layer = fx.pop(cap, r - 5)
        if layer is not None:
            look.centre(img, layer, W / 2, H * 0.72)
    if 90 <= r < 105:
        img = fx.zoom_blur(img, W / 2, H / 2, 0.08 * (r - 90) / 15)
    return look.grain(img, r, 0.01)


def timeline() -> dict:
    return {
        "fps": FPS,
        "clips": [{"name": n, "frames": f} for n, f in CLIPS],
        "texts": [
            {"text": "OK", "start": 0, "frames": 45},  # 1.5 s for 2 characters: passes
            {"text": "This sentence is much too long to read", "start": 110, "frames": 30},  # 1 s: fails
            {"text": "3", "start": 150, "frames": 4, "accent": True},  # exempt
        ],
        "hits": [{"frame": 60, "what": "the flash's first frame (a hit placed on it)"},
                 {"frame": 90, "what": "a hit with nothing on it"}],
    }


def tone(f: float, dur: float, amp: float, sr: int, phase: float = 0.0) -> np.ndarray:
    t = np.arange(int(dur * sr)) / sr
    return amp * np.sin(2 * np.pi * f * t + phase)


def build_audio(tl_path: str, sr: int = 48000) -> str:
    import cues
    import master
    import soundfile as sf
    from timeline import Timeline

    rng = np.random.default_rng(7)
    mix = cues.Mix(Timeline.load(tl_path), sr)
    bed = np.stack([tone(220, 6.5, 0.06, sr) + tone(330, 6.5, 0.045, sr)] * 2, axis=1)
    mix.place("music", bed, "hook", until=("flash", 25), label="bed")  # a declared bridge into flash
    mix.place("music", bed, "calm", label="pad")
    # (A tone, not noise: a click can't be told from noise's own sample-to-sample jumps, so noise just before a
    # cut hides any click there.)
    hum = tone(150, 0.5, 0.2, sr) * np.linspace(1, 0, int(0.5 * sr))
    mix.place("sfx", hum, "hook", at=1.8, label="whoosh")  # choked at the hook's end, 0.2 s in
    burst = rng.standard_normal(int(0.08 * sr)) * 0.08 * np.exp(-np.arange(int(0.08 * sr)) / (0.015 * sr))
    mix.place("sfx", burst, "flash", label="hit")  # on the flash's first frame
    voice = tone(300, 0.8, 0.15, sr) * np.hanning(int(0.8 * sr))
    mix.place("voice", voice, "calm", at=-0.25, prelap=0.3, label="voice")  # a prelap into calm
    mix.silence(4.2, 4.5, "the beat before the end")
    out = mix.render()
    # Planted after the cue sheet, as a careless mix would: a tone across hook -> flash...
    a, b = int(1.75 * sr), int(2.35 * sr)
    out[a:b] += tone(500, 0.6, 0.12, sr)[: b - a, None]
    mix.cues.append({"label": "leaky tone", "bus": "sfx", "scene": "hook", "start": 1.75, "end": 2.35, "bridge": None})
    # ...a tone stopped dead on the flash -> calm cut, at its peak (a click)...
    a, b = int(3.2 * sr), int(3.5 * sr)
    out[a:b] += tone(400, 0.3, 0.3, sr, phase=np.pi / 2 - 2 * np.pi * 400 * 0.3)[: b - a, None]
    # ...and noise in a span the timeline will call silent.
    a, b = int(5.0 * sr), int(5.3 * sr)
    out[a:b] += rng.standard_normal((b - a, 2)) * 0.01
    y = master.master(out, sr, -14.0, -2.4, silences=mix.silences)
    dest = os.path.join(OUT, "mix.wav")
    sf.write(dest, y, sr, subtype="PCM_24")
    mix.export(tl_path)
    data = json.load(open(tl_path, encoding="utf-8"))
    data["silences"].append({"start": 5.0, "end": 5.3, "what": "a silence with noise in it"})
    json.dump(data, open(tl_path, "w", encoding="utf-8"), indent=1)
    return dest


def main() -> int:
    import audio as vaudio
    import deliver
    import master
    import media
    import qc
    import render
    import sheets
    from timeline import Timeline

    os.makedirs(OUT, exist_ok=True)
    tl_path = os.path.join(OUT, "cut.json")
    json.dump(timeline(), open(tl_path, "w", encoding="utf-8"), indent=1)
    n = sum(f for _, f in CLIPS)
    print("rendering the master...")
    mov = render.master(frame_at, n, W, H, FPS, os.path.join(OUT, "master.mov"), workers=4, log=lambda s: None)
    print("mixing and mastering...")
    wav = build_audio(tl_path)
    mp4 = deliver.encode(mov, wav, os.path.join(OUT, "selftest.mp4"))
    tl = Timeline.load(tl_path)

    results: list[tuple[str, bool]] = []

    def expect(what: str, ok: bool):
        results.append((what, ok))
        print(f"{'ok  ' if ok else 'BAD '} {what}")

    import soundfile as sf

    x, sr = sf.read(wav, always_2d=True)
    ref = media.loudness(wav)
    expect(f"master.lufs agrees with ffmpeg ({master.lufs(x, sr):.2f} vs {ref['I']:.2f} LUFS)",
           abs(master.lufs(x, sr) - ref["I"]) < 0.3)
    expect(f"master.true_peak_db agrees with ffmpeg ({master.true_peak_db(x):.2f} vs {ref['TP']:.2f} dBTP)",
           abs(master.true_peak_db(x) - ref["TP"]) < 0.5)

    dest, failed = qc.report(mp4, tl, OUT, -14.0, -1.0, 12.0)
    rep = open(dest, encoding="utf-8").read()
    expect("qc fails the cut overall", failed)
    expect("qc passes the loudness of the delivered file", "- PASS: integrated" in rep)
    expect("qc finds the flashes", "general flashes over the whole frame" in rep)
    expect("qc fails the long caption", "FAIL: 'This sentence is much too long to read'" in rep)
    expect("qc passes the short caption", "PASS: 'OK'" in rep)
    expect("qc leaves the accent number out", "'3'" not in rep)
    expect("qc lists the black stretch", "black_start:3.5" in rep)
    expect("qc finds no duration mismatch", "the timeline is" not in rep)
    xa, sra = media.audio(mp4)
    found, on_hits = qc.clicks(tl, xa, sra)
    expect(f"qc finds the click at flash -> calm ({found})", any("flash -> calm" in c for c in found))
    expect(f"qc takes the onset on the declared hit as a hit ({on_hits})", on_hits == 1)

    lines, fails = vaudio.crossings(tl, xa, sra)
    text = "\n".join(lines)
    expect("audio fails the undeclared crossing", "leaky tone [sfx] from hook" in text and "NOT DECLARED" in text
           and fails == 1)
    expect("audio allows the declared bridge", "bed [music] from hook" in text and "bridge to flash frame 25" in text)
    expect("audio allows the prelap", "voice [voice] from calm" in text and "prelap into it" in text)
    expect("audio: the choked whoosh doesn't cross", "whoosh" not in text)
    s_lines, s_fails = vaudio.silences(tl, xa, sra)
    s_text = "\n".join(s_lines)
    expect("audio passes the muted silence", "ok: the beat before the end" in s_text)
    expect("audio fails the noisy silence", "FAIL: a silence with noise in it" in s_text and s_fails == 1)
    y_lines, y_fails = vaudio.sync(tl, xa, sra)
    y_text = "\n".join(y_lines)
    expect("audio finds the sound on the placed hit", "ok: frame 60" in y_text)
    expect("audio flags the hit with nothing on it", "CHECK: frame 90" in y_text and y_fails == 1)
    vaudio.spectrogram(tl, xa, sra, os.path.join(OUT, "spectrogram.png"))

    import analyze

    res = analyze.analyze(mp4, os.path.join(OUT, "analysis"), 4.0, tl)
    expect(f"analyze finds the cut into calm (cuts at {res['cuts']})", any(abs(t - 3.5) < 0.05 for t in res["cuts"]))
    expect("analyze measures the loudness", res["loudness"] is not None and abs(res["loudness"]["I"] + 14) < 1)

    sheets_out = sheets.contact(mp4, 6, tl, OUT) + sheets.cuts(mp4, tl, OUT)
    expect(f"sheets made {len(sheets_out)} sheets", len(sheets_out) == 2 and all(os.path.exists(p) for p in sheets_out))
    for name, fn in (("slam", lambda: fx.slam(ts.line("GO", 40, stroke=0.1), 2)),
                     ("decode", lambda: fx.decode("HELLO THERE", 6, 3)),
                     ("whip", lambda: fx.whip(_scene(0), 40)),
                     ("tear", lambda: fx.tear(_scene(0), 0.5, 1)),
                     ("datamosh", lambda: fx.datamosh(_scene(0), _scene(9), 0.5, 2)),
                     ("chroma", lambda: fx.chroma(_scene(0), 3)),
                     ("fit_blurred", lambda: look.fit_blurred(_scene(0)[: H // 3], W, H))):
        try:
            fn()
            expect(f"fx/look {name} runs", True)
        except Exception as e:  # noqa: BLE001
            expect(f"fx/look {name} runs ({e})", False)

    bad = [w for w, ok in results if not ok]
    print(f"\n{len(results) - len(bad)}/{len(results)} as expected. Files in {OUT}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
