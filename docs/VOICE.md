# Voice

Every spoken line is a take from ElevenLabs, made through the ElevenLabs connector, then cut, sped up, levelled and
checked here before the mix places it. Spike S5 (2026-11-08) chose the cast and built the chain.

## Making a line

1. **Write it with its delivery.** The model reads audio tags in square brackets: `[excited]`, `[sarcastic]`,
   `[deadpan]`, `[bubbly]`, `[urgent]`, `[whispers]`, `[shouting]`, `[laughs]`, `[deep voice]`. A tag holds until the
   next one. Capitals stress a word (`that ONE person`). It has no speed setting: pace comes from the processing
   below, and pauses from `[pause]` or an ellipsis. Write numbers as words.
2. **Generate it** with the connector, one flow per video, so every take stays on one canvas:
   - `creative_create_flow` once, then `creative_generate_speech` per line with `model_id` and the role's `voice_id`
     from `tools/edit/voices.json`. Ask for 2 takes of a line that carries a joke; 1 is enough for the rest.
   - `creative_get_generations` with the generation ids gives each take's `full_res_url` (an MP3).
   - `python tools/edit/voice.py fetch URL build/<video>/raw/<line>.mp3` downloads it.
   - Never call a generation again to retry it: each call is charged. Read the earlier one back instead.
3. **List the lines** in a `lines.json` (`tests/s5_lines.json` is the example): each line's id, role, text and its
   `take` or `takes`.
4. **Process and check:** `python tools/edit/voice.py make lines.json --out build/<video>/voice`. It writes
   `<id>.wav` (48 kHz mono), `words.json` (each line's words with their times, as the transcriber hears the processed
   file) and `report.md`. With several takes, it keeps the best one: the fewest failed checks, then the clearest
   words, then the widest pitch (the liveliest read).
5. **Listen-equivalent:** `python tools/edit/voice.py reel lines.json --out build/<video>/voice` puts every line in
   one file with a card per line, for the owner.

## The chain

| Step | What it does | Why |
|---|---|---|
| Trim | cuts the silence before the first sound and after the last, leaving 12 ms and 60 ms | the references' first word is on frame 1 |
| Tighten | cuts every pause and breath between words down to `keep` (0.07 s; 0.05 for stories), keeping 60% of it after the word before | the references cut their breaths; stories have no silence at all |
| Tempo | speeds the line up without changing its pitch (ffmpeg's `atempo`, an overlap-add method that stays natural on speech): 1.12x for the narrator, 1.10x for girls, 1.0x for the deep voice, 1.2x for stories | the references are sped up 1.1-1.15x (comedy) and about 1.2x (stories) |
| Level | sets the active speech level (K-weighted, over the 20 ms frames within 25 dB of the loudest) to -18 dB, peaks limited to -1 dBTP | every line at one level, so the mix sets the voice once |

A pause counts as cut when it is silence (32 dB under the loudest frames) or breath (unvoiced, 14 dB under them, and
dark: a spectral centroid under 3.5 kHz, where an "s" is bright).

## The checks (`report.md`)

Each one fails a line that must be regenerated or reprocessed:

- every scripted word heard by the transcriber, in order (tags dropped, "40" taken for "forty");
- the sound starts within 50 ms of the file's start and ends within 150 ms of its end;
- no pause longer than the role's `max_pause` (0.2 s; 0.15 for stories);
- the median pitch inside the role's range: wide enough for any mood (a sarcastic retort read 149 Hz), narrow enough
  to catch a take in the wrong voice;
- for stories, 4.0-5.4 words a second;
- the speech level within 0.6 dB of the cast's, true peak under -1 dBTP.

## The cast (`tools/edit/voices.json`)

Chosen by auditioning 14 takes in 11 voices and measuring each against the references (`speech.py refs`, below). The
owner can swap any role there; the processing and checks follow the role, not the voice.

| Role | Voice | Measured | The references |
|---|---|---|---|
| narrator (family A) | Liam (premade) | 221 Hz, 10.9 semitones of spread, 3.6 words a second after 1.12x | narrators 191-247 Hz; listener: "energetic young male, sped up" |
| girl | Yuria (Voice Library) | 327 Hz | girls' lines about 320 Hz |
| girl_bratty | Kathie (Voice Library) | 383 Hz | a second, sassier girl |
| deep | Adam (premade) | 81 Hz, deadpan | deep punches 79-123 Hz |
| story (family B) | Liam, at 1.2x | 187 Hz, 5.0 words a second in one sentence | storytellers 173-233 Hz; 4.1-4.7 words a second over whole stories |
| mom | Lyra (Voice Library) | 432 Hz when bubbly; untested as a mom | moms are mostly read by the narrator |

Rejected on measurement: Ayla (456 Hz) and Lyra (431 Hz) as the teen girl, both above the references' girls; the
other narrators (jimmy and James, 259 Hz; Max, 235 Hz) passed but sat further from the references' narrators than
Liam. Their takes are in `build/s5/audition/`.

## The references' voices, measured

`python tools/verify/speech.py refs refs/r6rants/videos/*.mp4` (pitch by YIN over the words the transcripts found):

| Video | Family | Median pitch | 10th-90th percentile | Words a second (in runs of speech) |
|---|---|---|---|---|
| 001 | comedy | 214 Hz | 150-351 | 3.26 (3.42) |
| 004 | comedy | 242 Hz | 87-354 | 3.60 (3.68) |
| 005 | comedy | 191 Hz | 106-272 | 3.06 (3.47) |
| 007 | comedy | 247 Hz | 157-469 | 3.18 (3.42) |
| 010 | comedy | 234 Hz | 169-394 | 3.31 (3.31) |
| 016 | comedy | 211 Hz | 110-468 | 2.94 (3.14) |
| 003 | story | 86 Hz | 81-116 | 4.21 (4.21) |
| 006 | story | 191 Hz | 67-245 | 4.66 (4.66) |
| 008 | story | 233 Hz | 121-424 | 4.24 (4.24) |
| 009 | story | 177 Hz | 87-242 | 4.09 (4.14) |
| 011 | story | 195 Hz | 108-296 | 4.34 (4.34) |
| 012 | story | 173 Hz | 86-254 | 4.06 (4.09) |
| 013 | story | 202 Hz | 65-368 | 4.46 (4.52) |

The wide percentiles are the cast: one video's narrator, girl and deep voice together. 003's 86 Hz is its warm
baritone storyteller. The transcriber puts most words back to back, so its gaps can't measure pauses; `voice.py`
measures pauses from the level instead.

## Cost and time

- About 1 credit a character on the newest model (a 60-character line: 60 credits, about 1.2 US cents), and about 5
  s to generate.
- Processing and transcribing: about 4 s a line on the CPU (the transcriber falls back from the GPU when its CUDA
  libraries are missing, as here).

## Licence

- Generated on the owner's paid ElevenLabs plan, which allows commercial use; the output belongs to the owner
  (ElevenLabs' Terms of Use, 4(c)(ii)).
- Voice Library voices (Yuria, Kathie, Lyra) are shared by their owners under ElevenLabs' Voice Library Addendum;
  premade voices (Liam, Adam) under its Terms of Use.
- Never a clone of a real person's voice (`CLAUDE.md`). Every voice used is listed in `ATTRIBUTION.md`.
