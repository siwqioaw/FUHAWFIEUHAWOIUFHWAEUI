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
python tools/make.py plan    videos/<slug> --keep-shots   # captions timed again, every shot as already shot
python tools/make.py plan    videos/<slug> --check        # every time and warning, nothing written (safe mid-shoot)
```

Everything a run makes goes in `build/<slug>/` (ignored by git); the spec, and the notes that go with it, are the
video's record and are committed.

## The stages

| Stage | Reads | Writes | Fails when |
|---|---|---|---|
| voice | `short.json` lines, `build/<slug>/takes.json` (the agent writes it after generating each line with the ElevenLabs connector: {line id: [take URL or file, ...]}; each download is named by its take, so a regenerated line's new takes are fetched; a link expires after some
hours, and then the copy fetched while it worked is used) | `voice/<id>.wav`, `voice/words.json`, `voice/report.md` | any voice check fails (`docs/VOICE.md`) |
| plan | the spec, `words.json` | `plan.json` (every shot's camera path, actors' pose and face keys, voices, effects, captions), `cut.json` (the timeline every check reads) | a time can't be resolved, a shot has no camera, a caption is up too briefly to read (`qc.py`'s rule, found before the shoot); it warns about an actor a shot lists but never shows, a face under the captions (a story's face above 36% of the height, a comedy's below 66%), a face cut by an edge of the frame, and one below 85% where the Shorts UI covers it (each face where its pose puts it); a gesture whose hand or arm leaves the frame (sampled through the shot); a jump cut (the same face both sides of a cut at under 1.4x the size and 25 degrees round); an icon whose subject is hidden behind a nearer actor (it lands on that actor); actors' bodies or arms inside each other, or any limb inside the set's furniture or props; a camera outside its set's room or inside any part of the set |
| shoot | `plan.json` | `shots/<shot>/f00000.png ...` (960 x 1707), and `_shot.json`: a stamp of the shot's plan | frames are missing after 4 attempts. A shot whose plan has changed since its stamp is shot again; a complete, current one is skipped; and the cut refuses frames shot from another plan. A shot keeps its seed (its hold's drift) by name across plans, so one put in before others leaves theirs current; folders shot before stamps count as current, so delete the ones you restage |
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
  - `walk`: `{"from": [...], "to": [...], "start": t}`: a heel-to-toe walk between two points: the actor waits at
    `from` until `start`, turns to its own facing in 0.3 s on arriving, then takes its poses. Pose keys are
    `(t, pose)` or `(t, pose, snap seconds)`; a pose is a name in `pose.POSES` or a dict of joints (`sit` rests on a
    seat 1 stud up). The plan warns when two actors' bodies or arms meet, or a walk passes through someone.
  - `camera`: keys, each a view and, after the first, `move` (seconds; 0 cuts) and `ease` (`out`, `inout`, `in`,
    `linear`). A view is one of:
    - `{"aim": "kid.head", "distance": 5.5, "height": -0.3, "fov": 45, "toward": [x, y, z]}`: framed on a point
      (an actor's `head`, `face`, `torso` or `feet`, or `[x, y, z]`), from in front of whoever it aims at. A head
      or face is where the actor's pose has it at the key's time: a slump drops the face half a stud and tips it
      forward, a laugh throws it back (M5's first `twice` aimed at the upright face and framed the slumped one on the
      frame's bottom edge). An overlay over a head follows the pose at its time the same way;
    - `{"pos": [x, y, z], "look": "girl.face"}`;
    - `{"ots": {"near": "kid", "far": "girl"}}` (over the shoulder, with depth of field);
    - `{"low": {"aim": "kid.head"}}`, `{"top": {"aim": "kid.torso"}}`;
    - a two-shot: `{"aim": "girl.head", "between": "me", "distance": 11}` (framed between two heads, from the side
      both face);
    - with `"dutch": 14`, `"back": 2`, `"orbit": 30` applied after.
  - `say`: the lines said in the shot, each `at` seconds in (or at a time, below). A line can run on past the cut.
  - `sfx`: effects from `tools/edit/sfx.py` (`boom`, `whoosh`, `pop`, `ding`, `error`, `shimmer`, `thud`, `riser`,
    `tick`) or a file; booms and thuds are picture hits that `audio.py` checks a sound lands on.
  - `streak`: true for a swoop, smeared in the edit (`camera.smear`, `fx.streak`).
  - `drift`: how much a held camera drifts (1 by default, 0 for none).
- **until:** a shot can end on a time instead of a length: `"until": "b:switched"` cuts on that word (stories cut on
  the first word of each clause).
- **set:** a shot staged in one of the video's other sets (`"sets": [{"id": "new_school", "name": "hallway", "at":
  [400, 0, 0], "options": {...}}]`), its coordinates in that set's own frame.
- **overlays:** icons popping over a point in the scene, projected through the shot's camera: `{"icon": "bell", "over":
  "leo.head", "at": "b:ding", "size": 150}` (an emoji name or picture; the rule's signature in a story). Add `"text":
  "99%"` for a line in the `label` style over it, or give only the text: a number over a head, a message in a bubble.
  An icon over a head follows the pose at its time; one that would cover any actor's face is moved beside that
  head (in a close-up the captions' band leaves no room above it).
- **planted:** false for an actor whose feet shouldn't be kept on the floor.
- **music:** a bed looped to length from `start` (`offset` seconds into the track), ducked under the voice (6 dB by
  default, `duck_db`), or not (`"duck": false`, for music formats).
- **texts:** words on screen that aren't captions of a line (headers, labels), in seconds.
- **names:** names that only ever start a sentence ("Mia aced her math test."), so captions keep their capitals; a
  name the script also uses mid-sentence is found without this.

## Times

Any key's time is seconds from the shot's start, or anchored to the voice: `"l1:start"`, `"l1:end"`, `"l1:WORD"`
(the word's start, as the transcriber heard it in the processed line; `WORD.end` for its end; `WORD#2` for its second
time), each with `+0.1` or `-0.05` after it. So a face changes on the word, as the references' do, and a boom lands
after the punch however the take came out.

## Captions

Made from the lines in the family's style (`docs/CAPTIONS.md`): the script's own words and capitals, timed by the
transcriber's word times, each starting in lower case unless its first word is stressed, "I" or a name (a word the
script capitalizes mid-sentence, so "so Leo stopped" keeps "Leo had never" capitalized); an emoji only in comedy.

- **Comedy** captions are a clause each, up to three lines: a sentence breaks at its commas when both sides have two
  words or more, so a punch isn't up before it's said (M3's "I'll do the title page!" was up 1.3 s early).
- **Story** captions are 1-3 words, each phrase (up to a punctuation mark) split the way that reads best
  (`_story_groups`): not ending on "a", "the", "to" and the like, no word left alone, none up too briefly to read.
  "you hear a | ding." becomes "you hear | a ding."; "most people hear | a few a | day." becomes "most people | hear
  a few | a day.". Four words only where a phrase is said too fast to split.
- Each shows 2 frames before its first word and holds until the next. One said too fast to read takes up to 0.12 s
  from a neighbour with time to spare (`_balance`): first by hiding later, then by showing earlier, but never more
  than 2 frames before its words (M4's "then he" came up 7 frames early, over the shot before). One due up to 4
  frames after a cut comes in on the cut only while its word is within 3 frames of it, one 2 before a cut waits for
  it, and each keeps its time on screen (`_snap_to_cuts`). A line's first caption waits until the line is heard:
  the first 10 ms within 18 dB of the take's loudest (`_audible_onset`; M3's "WE?!" opened on a soft glide and was
  captioned 13 frames before the shout). The render and `cut.json` count a caption's frames by one rule
  (`_caption_frames`).

The read-time check treats them as speech: heard as they're read, they need only their characters at 35 a second, and
0.25 s at the least, the references' own pace (`docs/VERIFY.md`, `caption_pace.py`).

## Hits

A boom or a thud is a picture hit as well as a sound: one that doesn't land on a cut punches the picture in 7% on its
frame, easing back over 0.3 s (`_punch`; `"punch": false` in the spec turns it off), and its long tail is pulled down
12 dB under a line that starts while it rings (`_duck_tail`). The bed fades out over the last 0.35 s and the mix over
its last 15 ms, so the Short loops without a click.

## When a shoot fails

A playtest can drop out mid-take ("Target is not reachable", seen on S7's 170th frame). The shoot then starts a new
playtest, stages everything again and resumes from the frames on disk, up to four times. `shoot --only <shot>`
reshoots chosen shots; delete a shot's folder to redo it from scratch.
