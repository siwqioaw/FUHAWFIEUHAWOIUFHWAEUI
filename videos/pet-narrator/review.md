# pet-narrator: review

## Round 1 (2026-11-08, on `out/pet-narrator.mp4` of 06:59)

A fresh reviewer agent got the delivered file, its timeline and plan, the script and direction, the voice report, the
automated reports and the checklists. Its evidence is in `build/review/pet-narrator/`. Every finding was checked;
its measured word onsets were used to test the timing fix.

| # | Finding | Severity | Cause | Fix |
|---|---|---|---|---|
| 1 | 4 of 11 speech bubbles never drawn: every one outside the street, the reveal's included | must | an overlay's point wasn't moved by its set's offset | `_offset_shot` moves it; selftest |
| 2 | `aced` opens inside a red prop | must | the camera's push started inside the street's parked car (12, 0, 7) | the camera swung south-west |
| 3 | Max's dog inside Max at the dance; from behind, its face out of his backside | must | the dog's head on Max's mark | the dog at his right, its head 0.6 studs clear |
| 4 | Jump cuts: `honestly` into `me` (1.15x, one angle); `cartoon` into `twice` (one angle, the head dropping) | must | direction | `honestly` a medium shot of Max and the dog, `me` close from 30 degrees round; `cartoon` a three-quarter medium, `twice` close from the other side |
| 5 | No bubble has a sound; the one pop has no bubble | should | direction | a pop on every bubble; the last bubble on "me", with its pop |
| 6 | The storyteller's soft phrases 5-10 dB under the rest, the bed only 5-7 dB under them | should | the read (soft tags) | the bed ducked 9 dB, not 4, and 1 dB lower; the read kept |
| 7 | Clause starts timed late by the refinement ("cats" 0.13 s, "Like" 0.13, "And honestly" 0.24) | should | voicing starts after a soft or unvoiced consonant | `refine_words` walks back from the voicing to the sound's onset: "cats", "because", "Like" and "And" now within 0.015 s of the reviewer's onsets |
| 8 | "Dogs," said over the cat shot | should | the cut on "dogs" | the cut on "cats" |
| 9 | Two extras floating in the sky in the first frames | should | actors not in a shot waited at z = 400, "behind the camera", which on the open street was in front of it | they wait 200 studs under the floor |
| 10 | Captions over set text: the bedroom's "GAME ON" poster, the "SCHOOL DANCE" board | should | direction | Max moved clear of the poster; the board kept in the dance's wide (it sets the place) |
| 11 | `mirror` into `cartoon` reads as a jump cut (front close-ups, 1.3x) | should | direction | `cartoon` a three-quarter medium |
| nits | captions change 2 frames before cuts (by design); the speaking dog half out of frame in `love`; the point on "hi" off frame; the dog reads as a box in `begged`; the hero named at 36% and the twist at 96% (the format asks 25% and about 85%); "FRESH ERA" printed on a catalog jacket | nit | | `love` aimed at the dog; a wave on "hi"; the rest kept: the structure is the script's |

Fine, by the reviewer's measure: the specs, loudness (-14.6 LUFS, -2.4 dBTP), no flashes, flat, black or frozen
frames, every line at its planned start, every scripted word heard, every caption the script's words with names
capitalized at the references' pace (median 0.57 s on screen, 20.8 characters a second), the cringe on "nine" and the
love face on "September", the street's bubbles on the right pets, a clean loop, every asset licensed, teen-safe.

Planned again in full and shot again.
