# ding: review

## Round 1 (2026-11-08, on `out/ding.mp4` of 05:30)

A fresh reviewer agent got the delivered file, its timeline and plan, the script and direction, the voice report, the
automated reports and the checklists. Its evidence is in `build/review/ding/`. Every finding was checked.

| # | Finding | Severity | Cause | Fix |
|---|---|---|---|---|
| 1 | 13 of the 26 bells never appear on screen and 4 are cut off at an edge ("then twenty", the three "Ding"s, "so loud") | must | bells set 1-1.4 studs round the head plus a 1.5-stud lift, in close-ups 3-4 studs away: projected off the frame | the renderer pulls an icon inside the frame, clear of the captions' band (`_overlay`'s `keep`); selftest |
| 2 | Six flat white frames at 17.73-17.82 s | must | the overhead camera started at 17 studs, above the classroom's 15-stud ceiling (`top()` starts 2 over its height); `qc.py` only looked for black | `lunch` shot from 11; `qc.py` fails a run of frames of one flat colour that isn't black; selftest |
| 3 | "Leo sat down": nobody sits | should | no sitting pose | not fixed: an R6 sit needs leg angles checked in Studio and a staging at the desks; he walks up to her desk. In the backlog |
| 4 | Two captions on one frame, five times | should | the new caption-frame rule rounded a length, not the end | both ends rounded as times; selftest with a chain the old rule overlapped |
| 5 | The second "Ding": its sound and bell 0.17 s before the narrator says it | should | the plan kept the word times from before they were refined | `plan --keep-shots` now keeps only what the frames show (timing, cameras, actors) and times bells, effects and captions from the current words |
| 6 | The first bell at 3.0 s, not in the first second | should | the rule is said from the first word; the format puts its first instance at 4-6 s | kept: the references show it by 4-6 s |
| 7 | Jump cuts: `first` into `twenty` (1.64x on one line), `sat` into `her` (1.8x) | should | direction | both orbited off the line (35 and -30 degrees) |
| 8 | The old school's people at the new school (the jock, the gossips) | should | casting | three new students (`student_a/b/c`, plain sweaters) at the new school |
| 9 | The gossips 1.84 studs apart, arms through each other; the friends in `liked` 2.6 apart and cut off | should | direction | 3.4 apart; the friends staggered behind Leo, inside the frame |
| 10 | A cheer out of frame in `rule` | should | direction | the joy on his face only |
| 11 | "Everyone just liked him" heard as "Everyone disliked him" in a whole-file transcription | should | the read under the bed | kept: the clip and the voice file transcribe right and the caption reads "everyone just liked him"; regenerating the line would mean reshooting the whole video |
| 12 | The last bell over the speaker, not the hearer; gone 12 frames before the end | should | direction | kept over her ("came from her"); it now lasts to the end |
| nits | early captions by 0.1-0.14 s; captions over the board's text in `her`; "hid behind the lockers" stands in front of them; "switched schools" shows a plain wall; a story question (if kind talk dings, why did Leo hear none at the old school?) | nit | | the story question is a real hole in the script: for the owner to weigh; the rest kept |

Fine, by the reviewer's measure: the specs, loudness (-14.2 LUFS, -2.3 dBTP), no flashes or clicks, the dings within
10 ms of their places, the music under the voice, the captions' words at the references' pace (median 0.62 s on
screen, 20.8 characters a second), every face change on its word, the bells in `ding`, `few`, `first` and `her`, the
twist at 84%, a clean loop, no logo, every asset licensed, teen-appropriate.

Eleven shots restaged and shot again within their timing (`plan --keep-shots --replan ...`).
