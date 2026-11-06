# Lessons from the project this kit comes from

## The project

A 66-second trailer for a co-op horror game on Roblox, made by an agent working alone over three cuts:

- every frame of footage captured from a Roblox Studio playtest, a frame at a time (`docs/ROBLOX_CAPTURE.md`);
- the picture assembled in Python: reframing, grading, type, effects (`docs/PICTURE.md`);
- the sound placed on a cue sheet and mastered in Python (`docs/AUDIO.md`);
- every cut checked by measurement on the delivered MP4, then by an independent reviewer (`docs/VERIFY.md`).

The owner rejected the first two cuts. Almost every reason was a craft error that a check would have caught, so the
checks in this kit exist because of them. The owner's own words after the second cut:

> you have to verify every edit you make and ensure it's good, that's what the red teamer was for but clearly he
> missed it

(The "red teamer" was the independent reviewer agent.)

## What the owner said

| Cut | Rejected | Praised |
|---|---|---|
| 1 | The opening was confusing ("what is happening"). Stand-in bodies instead of the real people who'd agreed to be in it. Stiff walk cycles. A generator that sounded like an alarm. The attack cut to a blur. | The hard cuts from 0:21 on. The 5-4-3-2-1 countdown. |
| 2 | "Random glowing eyes in the middle of the screen": eye dots drawn in post that missed the creature's face. A roar bleeding across a cut into the countdown (0:31-0:33). The story. | The security-camera look. |
| 3 | Accepted. | |

What landed: hard cuts on beats, one strong graphic device used with intent (the countdown, the CCTV look). What
failed: anything ambiguous, anything that looked fake, and sound that didn't respect the cut.

## Failure modes, and the check for each

Every one of these happened. The check column is what catches it now.

| What went wrong | Why | Check |
|---|---|---|
| Eye dots drawn in post landed beside the face, not on it. | A 2D overlay placed from the creature's posed head point, projected into a 3D take that moved: dozens of pixels off. | Don't draw tracked overlays over 3D footage. Light it in the scene, or cut to a full-frame insert. Look at full-size frames from the MP4 at every overlay frame (`sheets.py frames`). |
| A roar ran about 2 s past its cut, under the next scene. | Sounds were placed on a global timeline, so nothing stopped a tail at a cut. | Place every sound in a clip; it's cut off at the clip's end unless it declares a bridge (`tools/edit/cues.py`). `audio.py` lists every sound across every cut and fails what wasn't declared. |
| A beat meant to be silent wasn't. | The master chain's high-pass and limiter ring on for milliseconds after loud low end. | Mute intended silences again after the master (`master.py` does). `audio.py` measures each one on the final file: peak under -60 dBFS. |
| The MP4's true peak went over the limit. | AAC adds true peak to sharp clicks: a mix limited at -2.4 dBTP measured up to -0.3 dBTP in the MP4. | Ceiling -2.4 dBTP on the WAV, the sharpest clicks low-passed above about 5 kHz, and `qc.py` on the MP4. The final trailer measured -2.3 dBTP. (The self-test's mix: -2.4 in the WAV, -1.3 in the MP4.) |
| A card couldn't be read in time. | "THE VOICES AREN'T YOUR FRIENDS." (31 characters) was up for 1.67 s. | `qc.py`: 0.5 s plus the characters at 12 a second, at least 1.2 s; that card needed 3.08 s. |
| A jump cut inside a blurred take showed a double exposure. | Motion blur averages sub-frames across the shutter; the first sub-frames of the frame after a jump still show the old framing. | At a cut or a camera jump, use only the last sub-frame (`look.load_avg` with one path). Check the cut sheets (`sheets.py cuts`). |
| A face blended over a take at partial opacity read as a ghosted double image. | Two pictures mixed instead of one picture chosen. | Cut to the other picture in full frame. |
| Slivers of game UI at the frame's edge in a few frames. | The HUD hiding missed one kind of GUI. | Look along every edge of every cut sheet. The capture's smoke frame must show no UI at all (`capture.py smoke`). |
| Two security feeds contradicted each other about who was where. | Each shot was designed alone. | Keep one continuity table (who, where, which clock, which card) and check each shot against it. |
| The reviewer passed problems that were already fixed and missed new ones. | It was given an older render and report. | Regenerate every report from the final file, and give the reviewer the paths and their times. |
| A voice line's key word was buried under a beep 9 dB over it. | A sound effect placed on the word. | Duck everything under voice (`cues.duck`); measure the level at each key word against what's on top of it; look at the spectrogram. |
| The capture harness changed the owner's real game settings. | Studio playtests run as the signed-in owner with the place's API access. The harness set two settings in memory; the game saved its settings table for another reason, and wrote them to the live profile. | Never change a game's settings, saves or currency during capture. If the game must be told something, do it in memory only, and replace its save path with one that saves nothing (`docs/ROBLOX_CAPTURE.md`). |
| Screenshots of Studio taken through desktop control came back flat grey. | Studio's viewport doesn't show in that screenshot path. | Capture the viewport through Studio's MCP `screen_capture`; for the whole window, PowerShell's `CopyFromScreen` works. |

## How the work went

- **A beat sheet first.** The third cut started from a written beat sheet with every beat timed. The timeline file
  held every moment the picture and the sound share, and both read it: nothing was timed twice.
- **The delivered file is the one that's checked.** The encoder changes true peak and can change frames.
- **An independent reviewer after every round.** A fresh agent, given:
  - the current MP4 and the reports made from it;
  - full-size frames;
  - a checklist that grows with every past failure.

  It found 4 to 8 real issues a round, over 3 rounds. Give it the work, not your conclusions: a reviewer handed your
  view tends to confirm it.
- **Costs, for planning:**
  - capture: about 1 s a frame over the MCP bridge (60 s at 30 fps is 30 minutes; 3 sub-frames for motion blur is
    90);
  - a full master render: 1,600 frames at 1920 x 1080 took 12 to 20 minutes with 12 processes;
  - a review round, fix included: about an hour.
- **Draft renders over descriptions.** The owner judged from renders and asked for more when something was tame;
  descriptions of planned work got little reaction. Show stills early.
- **When the owner steps away,** ask every question the job needs before starting, then run to the end without
  stopping for input, and hand back finished files.

## What doesn't carry over

The horror itself: the dark grade, the 2.39:1 letterbox, the CCTV look, the synthesized score, the creature work and
the game's own code. None of it is in this repository. Only the methods and the checks are.
