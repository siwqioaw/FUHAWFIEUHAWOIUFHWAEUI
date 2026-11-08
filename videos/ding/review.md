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

## Round 2 (2026-11-08, on `out/ding.mp4` of 07:51)

A second fresh reviewer, the same brief. Evidence in `build/review2/ding/`. Two must-fix problems that every check had
passed, and the first review's kept nits came back as should-fix: the picture didn't show what the lines said.

| # | Finding | Severity | Cause | Fix |
|---|---|---|---|---|
| 1 | In every close-up the bells sat on foreheads (3.32 s on ex1's eyebrows; 11.17 s on Leo's with no caption up; the last one on her heart-eye) | must | the captions' band pushed each icon down to 33% of the height, onto the face | an icon that would cover a face moves beside that head (`_clear_of_faces`, every actor's head as posed); selftest |
| 2 | Leo's arm through two students' as he walks past them in `past` | must | they stood 2.6-2.8 studs from his path; R6s need 4 | 4.3-4.5 off his path, the camera wider; a staging check in the plan (bodies and arms over every pose, walks every half stud); selftest |
| 3 | The dings get quieter as the story says louder (single -17 dB, "twenty" -19.5, "so loud" -22.7 to -24.9) | should | gains set by ear for the burst, not measured | the signature escalates: twenty -3, dingding +1, loud +2 each, the last +5 |
| 4 | The rule isn't shown in the first 2 s (the first bell at 3.02) | should | the first bell waited for "ding" | a bell and a ding over the boy being talked about on "every" (0.54 s), before it's explained |
| 5 | The whisper two-shot cuts both gossips at the edges | should | they stood side by side, 3.4 apart (arms met) | turned to each other, 2.8 apart, a tighter two-shot |
| 6 | The last bell over the wrong head | should | the bell marked the speaker; the rule marks the one talked about | the last shot in the cafeteria: she whispers to her right, the loudest bell over Leo |
| 7 | Four beats not in the picture: "switched schools" a white wall; "hid behind the lockers" in front of them; "ate lunch alone" from above; "Leo sat down" in profile, his face never seen | should | the portrait frame showed only the hallway's centre; no prop to hide behind; no cafeteria; walks ended facing their way | Leo walks along the new school's blue lockers; a free-standing bank of lockers (`lockers` prop) he peeks round; lunch alone at a table in a new `cafeteria` set, the others laughing in the line; the next day he walks in, turns and sits with them (a `sit` pose; a walk now ends turned to the actor's facing) |
| 8 | Set text under the captions: "WELCOME BACK!", "Be kind", "CK!", a yellow poster | should | the sets' signs at caption height | `{"signs": False}` on every set (a new option) |
| 9 | A jump cut from `month` to `loud`: the same size and front angle | should | direction | `loud` from low and 30 degrees round, wider, with a dutch |
| 10 | The shimmer 3-7 dB over the quotable line in 1-4 kHz | should | the shimmer on "never" | after the line, on "bad", 7 dB down |
| nits | "then he" up 7 frames early, over the shot before; `twenty`'s arms over his face edge; her raised arm over sc's mouth; an orange prop in `her`'s first frames; the sad lines 6.3 dB over the bed; 0.56 s held after the last word; "morning," alone; the bells not in `ATTRIBUTION.md`'s emoji row | nit | | a caption never shows more than 2 frames before its words, and one that waits for a cut keeps its time (selftests); `twenty` low and frontal; sc moved clear; the bed 1 dB lower and ducked 9 dB, not 4; the hold 0.12 s; the bell logged. "morning," kept: "and on the first | morning, | ding." reads with the ding |

Fine, by the reviewer's measure: every check on the file (-14.2 LUFS, -2.2 dBTP, 10 of 10 hits), 26 bells each on
its ding within 2 frames, faces and poses on their words, all 53 captions the script's words at the references' pace
(median 0.59 s, 20 characters a second), never over eyes or mouths, the voice's pauses and register, no camera inside
anything, teen-suitable and original.

Fourteen shots restaged and shot again within their timing (`plan --keep-shots --replan ...`), seven kept.
