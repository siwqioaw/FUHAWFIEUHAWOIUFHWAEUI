# Notes for agent sessions

The owner is starting a series of Roblox shorts for kids, and wants an agent to design and run the whole workflow,
from idea to finished file, by itself. This repository is the starting point: tools and lessons from an earlier
project (a horror trailer for a Roblox game, made by an agent; `docs/LESSONS.md`). Use what fits, measure, and
replace what doesn't. The trailer's style doesn't carry over; its methods and checks do.

## Read first

1. `docs/LESSONS.md`: what the owner rejected and why, and the check that catches each failure.
2. `docs/PIPELINE.md`: the steps, and what each costs in time.
3. `docs/VERIFY.md`: the timeline file and every check.
4. `docs/KIDS_SHORTS.md`: what changes for kids' shorts. It's untested advice: check each point.
5. `docs/ROBLOX_CAPTURE.md` before any work in Studio.

## How to work

- **You can't watch or listen, so measure.** Never call a cut done until the checks pass on the encoded file and
  you've looked at the frames around every cut. Look at full-size frames of anything drawn over footage.
- **The delivered file is the one that's checked.** Not the WAV, not the master.
- **Review independently.** After each round, a fresh reviewer gets the current files (with their times), the
  timeline and the checklist in `docs/VERIFY.md`. Give it the work, not your conclusions. Add every new kind of
  failure to the checklist.
- **Show the owner stills and short drafts early.** They judge from renders. When they step away, ask every question
  up front, then run to the end and hand back finished files.
- **Test changes to the tools.** After changing anything in `tools/verify/` or `tools/edit/`, run
  `python tests/selftest.py` and see it pass. A check that stops catching its failure is worse than no check.
- **Record what you learn.** Write it into the docs in the same commit as the change: real numbers and paths, plain
  words.

## Rules

- **Never ask for, see, type, log or commit a password, API key or token.** If an upload needs one, the owner types
  it into their own terminal.
- **Publishing is the owner's decision, every time.** Never upload, post or schedule a video, or change a channel's
  settings. That includes the "made for kids" setting.
- **Kids' safety and privacy:**
  - no child's personal information in a video or a file;
  - a real person's name or avatar only with their permission, and a parent's for a child;
  - nothing frightening, graphic or mean;
  - no flashes over the WCAG limit (`qc.py` checks).
- **Everything used needs a license.** Every sound, music track, font and image needs a license that allows its use.
  Record each in `ATTRIBUTION.md`. Reference videos are for study and measurement only: never reuse their footage,
  music or characters.
- **Never put an AI model's name or identifier in a commit, a file or a code comment.** That's the owner's standing
  rule from the earlier project.
- **Roblox Studio:**
  - a playtest plays as the owner's account, so anything the game saves is saved for real;
  - Team Create saves every edit live;
  - remove anything temporary you add to a place.
- **Don't commit generated media.** `build/` and `out/` are ignored. Keep source (scripts, timelines, beat sheets)
  and licenses in git.

## Commands

```
python tests/selftest.py                                     # every tool, against planted failures
python tools/verify/analyze.py refs/r6rants/videos/*.mp4 --out build/analysis/r6rants   # measure reference videos
python tools/verify/transcribe.py refs/r6rants/videos/*.mp4 --out refs/r6rants/transcripts --device cpu
python tools/verify/study.py refs/r6rants/videos/*.mp4 --out build/study/r6rants --words refs/r6rants/transcripts --analysis build/analysis/r6rants
python tools/verify/sheets.py strip VIDEO --from 10.5 --to 11.0 --step 2 --out DIR   # a cut, or a fast move?
python tools/verify/qc.py out/x.mp4 --timeline cut.json      # the file
python tools/verify/audio.py cut.json out/x.mp4              # the sound against the cut
python tools/verify/sheets.py cuts out/x.mp4 --timeline cut.json
python tools/edit/master.py build/mix_raw.wav build/mix.wav --timeline cut.json
python tools/edit/deliver.py build/master.mov build/mix.wav out/x.mp4 --size shorts
python tools/roblox/studio_mcp.py serve                      # the Studio bridge, in the background
python tools/roblox/capture.py smoke build/capture           # before every capture session
```

The setup is in `README.md`: Python with `requirements.txt`, and ffmpeg on the PATH.
