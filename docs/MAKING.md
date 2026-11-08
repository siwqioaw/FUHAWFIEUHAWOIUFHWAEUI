# Making a Short

`tools/make.py` turns one file, `videos/<slug>/short.json`, into `out/<slug>.mp4`, checking every stage. Spike S7
(2026-11-08) ran it end to end: `videos/s7-test/` made a 6.4 s file that passed every check.

```
python tools/make.py voice   videos/<slug>    # takes -> processed lines, words.json      (needs build/<slug>/takes.json)
python tools/make.py plan    videos/<slug>    # everything in time -> plan.json, cut.json
python tools/make.py stills  videos/<slug>    # one frame per shot from Studio, to look at first
python tools/make.py shoot   videos/<slug>    # every shot from Studio (resumes, retries)
python tools/make.py cut     videos/<slug>    # master.mov
python tools/make.py mix     videos/<slug>    # mix.wav, mastered to -14 LUFS
python tools/make.py deliver videos/<slug>    # out/<slug>.mp4 and every check on it
python tools/make.py all     videos/<slug>    # plan to deliver, stopping at the first FAIL
```

Everything a run makes goes in `build/<slug>/` (ignored by git); the spec, and the notes that go with it, are the
video's record and are committed.

## The stages

| Stage | Reads | Writes | Fails when |
|---|---|---|---|
| voice | `short.json` lines, `build/<slug>/takes.json` (the agent writes it after generating each line with the ElevenLabs connector: {line id: [take URL or file, ...]}) | `voice/<id>.wav`, `voice/words.json`, `voice/report.md` | any voice check fails (`docs/VOICE.md`) |
| plan | the spec, `words.json` | `plan.json` (every shot's camera path, actors' pose and face keys, voices, effects, captions), `cut.json` (the timeline every check reads) | a time can't be resolved, a shot has no camera |
| shoot | `plan.json` | `shots/<shot>/f00000.png ...` (960 x 1707) | frames are missing after 4 attempts |
| cut | `plan.json`, the frames | `master.mov` (1080 x 1920, ProRes) | a frame is missing |
| mix | `plan.json`, `cut.json`, the voice files | `mix_raw.wav`, `mix.wav`; the placements into `cut.json` | |
| deliver | `master.mov`, `mix.wav`, `cut.json` | `out/<slug>.mp4`; `verify/qc_report.md`, `audio_report.md`, a spectrogram, cut and contact sheets | any check fails |

Time, measured on S7: voice 63 s for two lines (the transcriber on the CPU); plan 3 s; the shoot 385 frames at 1-1.8 s
each, plus about a minute to start the playtest and stage the cast; cut 35 s; mix 3 s; deliver 24 s.

## The spec

```json
{
 "slug": "s7-test", "title": "...", "family": "comedy", "fps": 60,
 "set": "baseplate", "set_options": {"lighting": "day"},
 "cast": {"kid": {"look": "narrator"}, "girl": {"skin": [240, 196, 160], "hair": [376526888], "shirt": 398634295}},
 "lines": [{"id": "l1", "role": "narrator", "text": "[excited] Why does every group project have that ONE person?",
            "emoji": "😭"}],
 "shots": [
  {"name": "kid", "seconds": "auto", "pad": 0.3,
   "actors": {"kid": {"at": [0, 3, 0], "facing": [0, 0, 1],
                      "poses": [[0, "idle"], ["l1:one", "arms_out"]], "faces": [[0, "smile"], ["l1:one", "angry"]]}},
   "camera": [{"t": 0, "aim": "kid.head", "distance": 9, "fov": 45},
              {"t": 0.05, "aim": "kid.head", "distance": 5.5, "move": 0.3, "ease": "out"}],
   "say": [{"line": "l1", "at": 0.0}],
   "sfx": [{"sound": "boom", "at": "l1:end+0.05"}]}
 ],
 "music": {"track": "build/library/music/bed.wav", "start": 0.7, "gain_db": -14},
 "texts": [{"text": "{pink:Mom's} old photos..", "style": "header", "from": 0, "to": 11}]
}
```

- **family:** `comedy` (low clause captions with an emoji), `story` (high 1-3 word captions), `music` (headers).
- **set:** a set from `tools/roblox/kit.py` (`docs/SETS.md`), or `baseplate`. Its marks give good places to stand.
- **cast:** each actor a look from `tools/roblox/cast.json` (`{"look": "narrator"}`), or a `stage.py` spec: skin,
  hair (catalog ids that fit R6), face accessories, shirt, pants.
- **lines:** each spoken line: its role in `tools/edit/voices.json`, the text with its audio tags, its caption (or
  none: `"caption": false`; or its own wording), an emoji for the end of its caption.
- **shots,** in order, back to back:
  - `seconds`: a number, or `"auto"`: to the end of its last line plus `pad`.
  - `actors`: who is in the shot, where (`at`, the torso centre: y = 3 standing on a floor at 0), which way they face,
    their pose keys and face keys. Anyone in the cast but not in the shot waits far behind the camera.
  - `walk`: `{"from": [...], "to": [...], "start": t}`: a heel-to-toe walk between two points, then the poses.
  - `camera`: keys, each a view and, after the first, `move` (seconds; 0 cuts) and `ease` (`out`, `inout`, `in`,
    `linear`). A view is one of:
    - `{"aim": "kid.head", "distance": 5.5, "height": -0.3, "fov": 45, "toward": [x, y, z]}`: framed on a point
      (an actor's `head`, `face`, `torso` or `feet`, or `[x, y, z]`), from in front of whoever it aims at;
    - `{"pos": [x, y, z], "look": "girl.face"}`;
    - `{"ots": {"near": "kid", "far": "girl"}}` (over the shoulder, with depth of field);
    - `{"low": {"aim": "kid.head"}}`, `{"top": {"aim": "kid.torso"}}`;
    - with `"dutch": 14`, `"back": 2`, `"orbit": 30` applied after.
  - `say`: the lines said in the shot, each `at` seconds in (or at a time, below). A line can run on past the cut.
  - `sfx`: effects from `tools/edit/sfx.py` (`boom`, `whoosh`, `pop`, `ding`, `error`, `shimmer`, `thud`, `riser`,
    `tick`) or a file; booms and thuds are picture hits that `audio.py` checks a sound lands on.
  - `streak`: true for a swoop, smeared in the edit (`camera.smear`, `fx.streak`).
  - `drift`: how much a held camera drifts (1 by default, 0 for none).
- **music:** a bed looped to length from `start`, ducked under the voice (6 dB by default).
- **texts:** words on screen that aren't captions of a line (headers, labels), in seconds.

## Times

Any key's time is seconds from the shot's start, or anchored to the voice: `"l1:start"`, `"l1:end"`, `"l1:WORD"`
(the word's start, as the transcriber heard it in the processed line; `WORD.end` for its end; `WORD#2` for its second
time), each with `+0.1` or `-0.05` after it. So a face changes on the word, as the references' do, and a boom lands
after the punch however the take came out.

## Captions

Made from the lines in the family's style (`docs/CAPTIONS.md`): the script's own words and capitals, timed by the
transcriber's word times. Comedy captions are a clause each, up to three lines, cut a sentence at a time; story
captions 1-3 words, a new one at punctuation. Each shows 2 frames before its first word and holds until the next.
The read-time check treats them as speech: heard as they're read, they need only their characters at 25 a second.

## When a shoot fails

A playtest can drop out mid-take ("Target is not reachable", seen on S7's 170th frame). The shoot then starts a new
playtest, stages everything again and resumes from the frames on disk, up to four times. `shoot --only <shot>`
reshoots chosen shots; delete a shot's folder to redo it from scratch.
