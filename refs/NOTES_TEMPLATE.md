# How to study one reference short

One note per video, in `refs/<set>/notes/<NNN>-<slug>.md`. The goal is a production spec: someone who has never seen
the video could rebuild its *craft* (not its jokes, characters or footage) from the note alone. Every claim cites a
time. Say how you know: **seen** (on a sheet or frame), **measured** (a number from a tool), **heard** (a transcript or
a model that can hear) or **guess**. Never present a guess as seen.

## Inputs, per video

| What | Where | Made by |
|---|---|---|
| Cuts, shot lengths, pace, loudness, flashes; one frame from every shot | `build/analysis/<set>/<name>/analysis.md`, `shots_00.jpg` | `tools/verify/analyze.py` |
| Words with times, speech rate, pauses | `refs/<set>/transcripts/<name>.md` (and `.json`) | `tools/verify/transcribe.py` |
| The first 3 s every 0.25 s; the whole video every 0.5 s (1 s past 40 s), each labelled with its words | `build/study/<set>/<name>/hook.jpg`, `contact_NN.jpg` | `tools/verify/study.py` |
| The sound: spectrogram, loudness, words, cuts, onsets outside speech | `build/study/<set>/<name>/audio.png`, `audio.md` | `tools/verify/study.py` |
| Any single frame at full size | `python tools/verify/sheets.py frames VIDEO FRAME --out DIR` | `tools/verify/sheets.py` |
| What a listener hears (voices, music, effects) | `refs/<set>/listener/<NNN>.json`, when the owner has run it | the owner, through a model that can hear |

The transcript mishears some words; the burned-in captions are the better source for the exact script. Read both.

## The note

```markdown
# NNN: <title> (<views>, published <date>)

**Format:** <rant | owned-roblox | in-this-world | story | skit | ...>  **Length:** x s
**Measured:** n shots, median shot x s, first cut x s, n words, x words/s, x LUFS, true peak x dBTP

## In one line
<what the video is, as a viewer would describe it to a friend>

## Why it works
The 3 to 6 mechanisms that most plausibly earned the views, each tied to a time.

## 1. Hook (0-3 s)
- The first frame, as a thumbnail: who, where, framing, text on screen.
- The first line, word for word, and when it starts.
- What changes at 0.5, 1, 2 and 3 s.
- The promise or question it opens, and when it's answered.

## 2. Script and story
- The full script with speakers and times (from captions and transcript).
- A beat sheet: | time | beat | what the viewer learns or feels | why they keep watching |
- The structure, the turn, the payoff, the ending (and whether it loops into the start).
- Voice of the writing: point of view, tense, sentence length, slang, how jokes are built.

## 3. Cast
| Character | Role | Avatar (rig, body colours, clothes, hair, accessories) | Face(s) and when they change | How the look says who they are |

## 4. World, set and light
- Each location: what it is, how detailed, the key props, the build style.
- Light: time of day, key/fill, colour temperature, shadows, fog, bloom, grade. Saturation and contrast.

## 5. Camera: the shot list
| # | Time | Length | Size (ECU/CU/MCU/MS/WS/EWS) | Angle (eye/high/low/OTS/POV/top) | Move | Subject | Why this shot |
Then the camera's habits across the video.

## 6. Animation and acting
How bodies and faces perform: poses, gestures, walks, head moves on speech, face swaps, timing, exaggeration.
Mark what can't be told from stills.

## 7. Edit and graphics
- Pace: cuts per 5 s, where cuts land (on words, on beats, on sound hits).
- Captions: font (or the nearest you can name), weight, size as % of frame width, colours, outline, shadow,
  position (% from the top), words per caption, highlight, entrance animation, case, emoji.
- Other text, stickers, images, arrows, zoom punches, shakes, flashes, freezes, speed ramps, transitions.

## 8. Sound
- Voice(s): who speaks, narrator or dialogue, pace (words/s), pauses and what they're for.
- Music: there or not, where it changes, estimated tempo, its job.
- Effects: onsets outside speech (`audio.md`), where they land, what they likely are (mark guesses).
- Mix: voice against the bed (dB), loudness.
- Questions only a listener can answer, for the listener pass.

## 9. Retention devices
| time | device (open loop, pattern break, escalation, reveal, callback, loop) | how |

## 10. Packaging
Title formula, emoji, hashtags; whether the first frame works as the thumbnail.

## 11. Principles to reuse / things not to copy
What carries over to an original video, and what is this creator's own (jokes, characters, catchphrases).
```
