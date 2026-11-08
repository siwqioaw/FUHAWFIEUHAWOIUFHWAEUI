# Voice

Every spoken line is a take from ElevenLabs, made through the ElevenLabs connector, then cut, sped up, levelled and
checked here before the mix places it. Spike S5 (2026-11-08) chose the cast and built the chain.

## Making a line

1. **Write it with its delivery.** The model reads audio tags in square brackets: `[excited]`, `[sarcastic]`,
   `[deadpan]`, `[bubbly]`, `[urgent]`, `[whispers]`, `[shouting]`, `[laughs]`, `[deep voice]`. A tag holds until the
   next one. Capitals stress a word (`that ONE person`). It has no speed setting: pace comes from the processing
   below. A deliberate pause is the edit's: split the line in two and leave the gap in the shot's timing, since the
   processing cuts pauses inside a line. Write numbers as words.
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
| Tighten | cuts every silence between words down to `keep` (0.07 s; 0.05 for stories), keeping 60% of it after the word before; a breath only when it is an island between two silences | the references cut their breaths; stories have no silence at all |
| Tempo | speeds the line up without changing its pitch (ffmpeg's `atempo`, an overlap-add method that stays natural on speech): 1.12x for the narrator, 1.10x for girls, 1.0x for the deep voice, 1.2x for stories | the references are sped up 1.1-1.15x (comedy) and about 1.2x (stories) |
| Level | sets the active speech level (K-weighted, over the 20 ms frames within 25 dB of the loudest) to -18 dB, peaks limited to -1 dBTP | every line at one level, so the mix sets the voice once |

Silence is 40 dB under the loudest frames. A breath is cut only as an island: 0.12 s or more of unvoiced sound,
18 dB under the loudest frames, with silence on both sides. A creaky tail joined to its word, or an "h" joined to the
next, is sound and stays. The first version also cut quiet unvoiced frames as breath, and an independent review found
it taking 50-150 ms off the ends of words in 12 of 35 cuts; on the same 16 takes the chain now makes 5 cuts, every one
44 dB or more under the speech.

A gap can also hover round the 40 dB line: M5's sentence breaks sat at 38-42 dB under, a faint breath or room tone
that split the silence into pieces too short to cut, and line a kept a 0.22 s pause against the stories' 0.15. So in
a stretch more than 32 dB under the loudest frames (what the pause check counts), everything from its first 30 ms of
silence to its last is silence too. A creaky decay's one-frame dips start nothing, so the S5 cases still pass
(`tests/selftest.py` has both, the gap built from M5's measured profile). Processed takes are cached by take and
settings, with `PROCESS_VERSION` in the key: bump it when the chain changes.

## Word times

The transcriber's word times anchor everything keyed to a word: captions, faces, poses, effects, cuts. It starts a
word straight after the one before, though, over any pause, held vowel or scoff between them: M3's review found
"for a forty slide project" captioned 0.6 s before "For" was said (a scoff and a pause after "page."), and "every"
0.33 s early. `voice.refine_words` moves the start of a word that opens a phrase (after a comma or a sentence's end,
by the script's punctuation) to its own voiced stretch: from the voicing of the word before or a gap, past a sound
and a pause, or, when the word holds no voicing at all, to the next voiced stretch. Inside a quick phrase it leaves
words alone: there the voicing measure misses reduced syllables ("the" in "Jake's the fastest" would have moved
half a second). On M3's lines it moves "for" to 8.06 s (the reviewer measured about 8.00) and "every" to 17.36
(17.30). It runs on every take, after the cache. For a video already shot, `python tools/edit/voice.py refine
build/<slug>/voice` re-times its `words.json` against its own lines (the audio untouched), then `make.py plan
--keep-shots` times the captions again without moving a shot.

## The checks (`report.md`)

Each one fails a line that must be regenerated or reprocessed:

- every scripted word heard by the transcriber, in order (tags dropped, "40" taken for "forty", "21" for
  "twenty-one"). It hears a copy with 0.5 s of silence before the line, its times moved back: from time 0 it missed
  a soft first consonant (M5's "She aced her math test" came back "He aced" on both takes, though the 70 ms "sh" is
  there, at 4.8-5.3 kHz). When even the raw take is heard that way, the read is wrong: regenerate the line;
- its median pitch inside the role's register: within -7 to +9 semitones of the voice's own pitch (`center` in
  `voices.json`, its audition). A shout can rise a long way and still be him; an octave down sounds like someone else
  (M3's review: two narrator lines read at 99-105 Hz against his 212-224, heard as another, quieter voice). The
  tag decides it: on the narrator (Liam), [suspicious], [defeated], [curious] and [deadpan] each read 97-113 Hz,
  twice; [annoyed], [frustrated] and [excited] 212-279 Hz, [sarcastic] 157 Hz, [shouting] 329 Hz;
- no word heard that isn't in the script (a tag read aloud, a repeated phrase);
- the sound starts within 50 ms of the file's start and ends within 150 ms of its end;
- no pause longer than the role's `max_pause` (0.2 s; 0.15 for stories);
- the median pitch inside the role's range. The ranges are wide, for any mood (a sarcastic retort read 149 Hz), so
  they catch a gross mistake (a man's voice on a girl's line) but not the choice between two voices: the voice id
  in `voices.json` decides that. Under 0.12 s of voicing (a whisper, a one-word deep punch) the pitch is noted as
  unmeasured, not failed;
- for stories, 4.0-5.4 words a second;
- the speech level within 0.6 dB of the cast's, true peak at most -1 dBTP (the level is measured again after the
  limiter; a take with no speech raises).

## The cast (`tools/edit/voices.json`)

Chosen by auditioning 14 takes in 11 voices and measuring each against the references (`speech.py refs`, below);
the numbers here are from the chain as it stands after the review. The
owner can swap any role there; the processing and checks follow the role, not the voice.

| Role | Voice | Measured | The references |
|---|---|---|---|
| narrator (family A) | Liam (premade) | 214 Hz, 3.5 words a second after 1.12x | narrators 191-247 Hz; listener: "energetic young male, sped up" |
| girl | Yuria (Voice Library) | 339 Hz | girls' lines about 320 Hz |
| girl_bratty | Kathie (Voice Library) | 364 Hz | a second, sassier girl |
| deep | Adam (premade) | 82 Hz, deadpan | deep punches 79-123 Hz |
| story (family B) | Liam, at 1.2x | 183 Hz, 4.8 words a second in one sentence | storytellers 173-233 Hz; 4.1-4.7 words a second over whole stories |
| mom | Lyra (Voice Library) | 419 Hz when bubbly; untested as a mom | moms are mostly read by the narrator |

Rejected on measurement: Ayla (433 Hz) and Lyra (419 Hz) as the teen girl, both above the references' girls; the
other narrators (jimmy 255 Hz, James 252 Hz, Max 228 Hz) passed but sat further from the references' narrators than
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
- Processing and transcribing: about 18 s a take on the CPU (the transcriber falls back from the GPU when its CUDA
  libraries are missing, as here); three lines with three takes took 1 min 46 s. The first run downloads the
  transcription model (about 3 GB). It needs about 3 GB of free memory to load: run the voice stage while Studio
  isn't shooting (twice it ran out of memory during a shoot). It is loaded only when a take isn't cached, so
  re-timing words or re-checking cached takes takes seconds (M5's three lines: 6 s).

## Licence

- Generated on the owner's paid ElevenLabs plan, which allows commercial use; the output belongs to the owner
  (ElevenLabs' Terms of Use, 4(c)(ii)).
- Voice Library voices (Yuria, Kathie, Lyra) are shared by their owners under ElevenLabs' Voice Library Addendum;
  premade voices (Liam, Adam) under its Terms of Use.
- Never a clone of a real person's voice (`CLAUDE.md`). Every voice used is listed in `ATTRIBUTION.md`.
