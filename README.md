# vid-editing

Tools and lessons for making videos from Roblox footage entirely in code, and for checking them by measurement: an
agent can't watch or listen, so every claim about a cut is measured on the delivered file.

They come from one project: a 66-second trailer for a Roblox horror game, made by an agent over three cuts, of which
the owner rejected the first two (`docs/LESSONS.md` says why). The horror style stayed behind. What's here:

- the methods and checks that would have caught each rejection;
- the Roblox Studio capture kit;
- a starting point for the next project, vertical shorts for kids.

## Start here

| Read | For |
|---|---|
| [`docs/LESSONS.md`](docs/LESSONS.md) | What went wrong in the trailer, and the check that catches each failure now |
| [`docs/PIPELINE.md`](docs/PIPELINE.md) | The steps from an idea to a checked file |
| [`docs/VERIFY.md`](docs/VERIFY.md) | The timeline file, every check, the reviewer's checklist |
| [`docs/AUDIO.md`](docs/AUDIO.md), [`docs/PICTURE.md`](docs/PICTURE.md) | The rules for sound and picture, and why |
| [`docs/ROBLOX_CAPTURE.md`](docs/ROBLOX_CAPTURE.md) | Capturing posed frames from Roblox Studio through its MCP server |
| [`docs/KIDS_SHORTS.md`](docs/KIDS_SHORTS.md) | What changes for kids' shorts: untested advice, to check |
| [`docs/ROBLOX_SHORTS_PLAN.md`](docs/ROBLOX_SHORTS_PLAN.md) | The plan for one-prompt Roblox Shorts, and the decisions it needs |
| [`refs/r6rants/`](refs/r6rants/) | The first reference set: 16 Shorts over 1M views, studied one by one, and what they share |

## Layout

| Folder | What |
|---|---|
| `tools/verify/` | `qc.py` (the file: loudness, flashes, read time, clicks, black), `audio.py` (sound across cuts, silences, sync, spectrogram), `sheets.py` (cut and contact sheets, frame strips), `analyze.py` (reference videos), `study.py` (reference study sheets: hook, contact sheets with the words, a map of the sound), `transcribe.py` (words with times, speech-to-text on this PC), `speech.py` (pitch, pace, pauses and level of speech; every scripted word heard), `timeline.py`, `media.py` |
| `refs/` | reference sets: transcripts, measurements and study notes (the videos themselves are ignored); `NOTES_TEMPLATE.md` |
| `tools/edit/` | `cues.py` (the cue sheet), `master.py` (loudness and true peak), `look.py`, `typeset.py`, `fx.py`, `render.py` (the parallel master render), `deliver.py` (the encode), `voice.py` (voice lines: breaths cut, sped up, levelled, words timed and checked) and `voices.json` (the voice cast) |
| `tools/roblox/` | `studio_mcp.py` (the MCP client and bridge), `studio.py`, `harness.luau`, `capture.py`, `stage.py`, `faces.py`, `pose.py` (R6 posing), `camera.py` (views and moves) |
| `tests/` | `selftest.py`: a test cut with planted failures that every check must catch; `studio_pose.py` and `studio_camera.py`: the posing and camera checks and takes in Studio (spikes S3, S4) |
| `build/`, `out/` | generated, not committed |

## What's been tested

| Part | State |
|---|---|
| The checks (`tools/verify/`) | `tests/selftest.py` passes 68 of 68. On the trailer's delivered file they agree with that project's own checks, except that the read-time check is stricter (`docs/VERIFY.md`, "Trusting the checks"). |
| Mastering, render, encode (`tools/edit/`) | Run by the self-test; the loudness meter agrees with ffmpeg's to 0.05 LU. |
| Type and effects | Run by the self-test; captions looked at in its contact sheet. Mostly ported from the trailer, where they were used. |
| The Studio bridge (`studio_mcp.py`) | Ported from the trailer, where it ran for hours; only the server lookup is new. |
| The capture harness and capture loop | Run in Studio on 2026-11-07: smoke test clean, portrait takes of 15 and 30 frames at 960 x 1707 (`docs/ROBLOX_CAPTURE.md`, "Resolution"). |
| Actors (`stage.py`) and faces (`faces.py`) | Run in Studio on 2026-11-07 (spike S2): dressed R6 actors from catalog items, faces drawn here and swapped per frame from Studio's content folder (`docs/ROBLOX_CAPTURE.md`, "Actors" and "Faces"). |
| R6 posing (`pose.py`) | Run in Studio on 2026-11-07 (spike S3): snaps, drift, planted leans and a heel-to-toe walk at 60 fps; every predicted sole corner matched Roblox's within 0.00001 studs (`tests/studio_pose.py check`; `docs/ROBLOX_CAPTURE.md`, "Posing R6"). |
| Camera (`camera.py`) | Run in Studio on 2026-11-07 (spike S4): push, pull, swoop, dutch, low angle, over the shoulder with depth of field and top-down, each strip measured (`docs/ROBLOX_CAPTURE.md`, "Camera"). |
| Voice (`voice.py`, `speech.py`) | Run on 2026-11-08 (spike S5): 14 audition takes in 11 ElevenLabs voices through the connector, measured against the references; the cast in `voices.json`; three test lines with every check passing (`docs/VOICE.md`). |
| Kids' shorts advice | Untested. |

## Setup

- Python 3.11 or later with `pip install -r requirements.txt`. Tested with Python 3.13.12, numpy 2.5.4, scipy
  1.18.1, OpenCV 5.0.0, Pillow 13.0.0 and soundfile 0.14.0.
- ffmpeg and ffprobe on the PATH. Tested with 8.1.1.
- For capture: Windows with Roblox Studio (`StudioMCP.exe` ships with it).

```
python tests/selftest.py
```
