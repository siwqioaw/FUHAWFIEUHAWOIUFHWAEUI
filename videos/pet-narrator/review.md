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

## Before round 2 (2026-11-08)

The restaged video was delivered once and looked at cut by cut before its second review, and three new problems
showed: in `said_it` and `honestly` the dog that speaks stood behind Max, so its bubble came out of his shirt (the
round-1 bubbles were never drawn outside the street, so no one had seen it); the bedroom's "GAME ON" poster sat
under the mirror's captions once that shot turned 30 degrees. Max now steps aside when the dog speaks (the dog shows
beside him, facing the lens), the bedroom's writing is off, and the plan warns about an icon over a hidden subject.
Before that the plan's new checks had restaged `mirror` (the wave cut off; then a jump cut from the street's Max),
`smiled` (a jump cut into `honestly`) and the dance's dancers (a hand cut off, two too close).

## Round 2 (2026-11-08, on `out/pet-narrator.mp4` of 10:47)

A second fresh reviewer: 2 must-fix, 5 should-fix, 7 nits. Every measured check passed (-14.6 LUFS, -2.4 dBTP, every
line on its start, the bed 23.7 dB under the voice). Evidence in `build/review2/pet-narrator/`.

| # | Finding | Severity | Cause | Fix |
|---|---|---|---|---|
| 1 | Max and his dog inside the coffee table for four shots, the dog's head resting on it | must | the staging check compared actors only with each other | the plan checks every limb against the set's parts (selftest); Max on the sofa, his dog on the floor by its end |
| 2 | The reveal's bubbles come out of Max's sleeve | must | the hidden-subject check shrank actors' boxes 12% a side | no shrink (selftest); the dog a step off his right hand, the two-shots framed on both |
| 3 | The dog's own words ("He likes you...") have no bubble | should | they played over Lily's close-up | over the dog's head at her, a bubble on each "He" |
| 4 | Beats said but not shown: no mirror (he waved at the lens); the TV behind the camera on "cried at a cartoon"; the dance a daylit classroom | should | the props didn't exist | a mirror with his reflection in it (a second Max behind an open frame, shot over his shoulder); a cartoon on the TV, over the sofa; the gym dressed for the dance |
| 5 | Story captions over the hair in medium shots and every close-up | should | the check looked at the face only | the plan warns when a head's top reaches above 28% (selftest); those shots framed lower |
| 6 | Two cheers with a hand off the frame shipped | should | | one fist up on the pet's side; proud owners with arms crossed, framed a little wider |
| 7 | The loudest sound, the last pop at 0 dB, lands inside the quotable line; no riser into the twist | should | | the pop at -8 dB; a riser into "That's me" |
| nits | the dog's nose cut and collar under the UI in `me`; a poster on Lily's head; Max's head at the edge in `smiled`; "love it," 0.11 s late; the room empty after the dance and a dancer hidden; the storyteller's voice out of other pets; 118 words | nit | | `me` reframed; the dance in the gym with five dancers in depth; `smiled` over Max's shoulder; the caption rules re-timed "love it,"; the voices and the length kept (the script's) |

Planned again in full: 18 of 20 shots shot again.
