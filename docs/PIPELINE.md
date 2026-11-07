# From an idea to a checked file

Each step writes files that the next step reads, so any step can be rerun alone and nothing depends on a GUI.

| # | Step | Tool | Writes |
|---|---|---|---|
| 0 | Measure the references | `tools/verify/analyze.py` | `build/analysis/` |
| 1 | Write the beat sheet | you | `beats.md` |
| 2 | Write the timeline | you | `cut.json` |
| 3 | Capture the shots | `tools/roblox/capture.py`, `stage.py` | `build/shots/<shot>/f00000.png ...` |
| 4 | Show stills | `render.stills` | `build/stills/` |
| 5 | Write the edit | your `frame_at(r)` | |
| 6 | Render the master | `render.master` | `build/master.mov` |
| 7 | Mix | `cues.Mix` | `build/mix_raw.wav`; `cues` and `silences` in `cut.json` |
| 8 | Master the sound | `tools/edit/master.py` | `build/mix.wav` |
| 9 | Encode | `tools/edit/deliver.py` | `out/<name>.mp4` |
| 10 | Verify | `qc.py`, `audio.py`, `sheets.py` | `build/verify/` |
| 11 | Review | an independent agent, then the owner | notes |
| 12 | Fix, then back to 6, or to 3 for a reshoot | | |

`tests/selftest.py` is a complete small example of steps 5 to 10: an edit function, a cue sheet, the master, the
encode and every check.

## The steps

0. **Measure the references.** Run `analyze.py` over the example videos the owner gives you. Write down what the
   numbers say about the format:
   - how fast they cut, and how soon the first cut comes;
   - how loud they are;
   - how much text they carry.

   Then look at the shot sheets for what the numbers can't say. These measurements are the targets for your own
   cuts.
1. **Write the beat sheet.** Every beat, timed. Say what the viewer sees and hears, and why they keep watching. The
   third trailer cut, the accepted one, started from one, after the owner asked for a well-planned story. Show it to
   the owner before capturing anything.
2. **Write the timeline** (`docs/VERIFY.md`, "The timeline file"). Every moment the picture and the sound share (a
   cut, a slam, a word) is a named number in one place: the edit, the mix and the checks all read it.
3. **Capture the shots** (`docs/ROBLOX_CAPTURE.md`). Before each session, run the smoke test. Before the full take,
   preview a few frames of each shot (`capture.take(..., only=[0, 15, 30])`).
4. **Show stills of the key frames** to the owner before the full render. A reaction to a frame costs a minute; a
   reaction to a finished cut costs a round.
5. **Write the edit.** One module-level `frame_at(r)` that builds frame r from the timeline (`docs/PICTURE.md`).
6. **Render the master** (`render.master`). It's ProRes 422 HQ, 10-bit. Rendered in parallel, 1,600 frames at 1080p
   took 12 to 20 minutes with 12 processes.
7. **Mix** (`docs/AUDIO.md`). Place every sound in a clip, and declare every bridge and every silence.
8. **Master the sound:** -14 LUFS, true peak under -2.4 dBTP in the WAV.
9. **Encode:** `deliver.py build/master.mov build/mix.wav out/<name>.mp4 --size shorts`.
10. **Verify the encoded file.** Run `qc.py`, `audio.py` and `sheets.py cuts` and `contact` on it, and look at
    full-size frames of anything doubtful. Everything must pass, and every CHECK must be explained.
11. **Review.** First an independent agent, with the current files and the checklist (`docs/VERIFY.md`), then the
    owner. Add every new kind of failure to the checklist.

## Making it repeatable

For a series of shorts, give each video a folder and one script that runs all of it. A suggested layout:

```
videos/<slug>/
  beats.md      the beat sheet
  cut.json      the timeline
  shots.py      the shot functions, captured with tools/roblox/capture.py
  edit.py       frame_at(r), and main(), which renders the master
  mix.py        the cue sheet
  make.py       capture (if needed), render, mix, master, encode, verify, in order; stops at the first FAIL
  assets/       sounds, music, fonts, images, each with its license
```

Shared looks belong in `tools/edit/` once two videos use them: a caption style, an intro sting, a colour grade.

## How long things take

The trailer's numbers are the only ones measured so far:

| Step | Time |
|---|---|
| Capture | about 1 s a frame (30 minutes for 60 s at 30 fps; three times that with 3 motion-blur sub-frames). Portrait at 960 x 1707, measured 2026-11-07: 0.94 s a frame, so 28 minutes for 60 s at 30 fps |
| Render | 1,600 frames at 1080p: 12 to 20 minutes, 12 processes |
| Checks | under a minute for a minute of video (the trailer's full set: about 70 s) |
| A review round, fix included | about an hour |
