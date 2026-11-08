# group-project: review

## Round 1 (2026-11-08, on `out/group-project.mp4` of 04:13)

A fresh reviewer agent got the delivered file, its timeline and plan, the script, the voice report, the automated
reports and the checklists. Its evidence is in `build/review/group-project/`. Every finding was checked and stands.

| # | Finding | Severity | Cause | Fix |
|---|---|---|---|---|
| 1 | In `pres_day` the girl's elbow (hands on hips) cuts into the narrator's arm for the whole shot | must | they stood 3 studs apart; R6 actors with arms out are about 4 wide | stand 4.4 apart |
| 2 | Cast items and Roblox's built-ins (the board font, materials, sky) not logged for the videos | must | `ATTRIBUTION.md` listed some items for the spike renders only | rows for every item and built-in, with the videos that use them |
| 3 | Captions, faces and poses come up to 0.6 s before their words ("for a forty slide project" during the scoff after "page") | should | the transcriber starts a word straight after the last one, stretching it over a pause or a breath | word starts moved to where the sound begins (`voice.refine_words`) |
| 4 | Gestures keyed to words happen out of frame in close-ups (the girl's cheer and point, the teacher's cheer behind a desk) | should | direction | gestures only where the frame shows them |
| 5 | A jump cut into `seen`: the same subject, same place, 1.17x the size; the head drops across the cut; an eye under the bangs in "Seen." | should | direction | `seen` a much closer shot from another angle, the pose the same across the cut |
| 6 | Lines 7 and 10 read an octave low (99 and 105 Hz against 212-224) and 5-7 dB quieter in the speech band: they could sound like another narrator | should | the tags ([suspicious], [defeated]) pulled the read down; the role's pitch range was wide enough to pass it | a check that a role keeps its own register across a video's lines; both lines regenerated |
| 7 | A click on every loop: a music note starts 8 ms before the end | should | the bed was cut, not faded | the mix fades the bed out at the end |
| 8 | `audio.py` passed a timeline with no cues (the plan had been re-run after delivery) | should | a check that passes on missing data | `audio.py` fails a timeline with clips but no cues |
| 9 | Captions come in 1-3 frames after a cut; the render and `cut.json` disagree by a frame | nit | show times not snapped to cuts; rounding in two places | captions snap to a cut just before them; one frame rule |
| 10 | Booms land on frames with no picture change, and their tails sit under the next line's first word | nit | a boom after a line, inside a shot | a punch-in on every boom; its tail ducked under the next line |
| 11 | `the_chat` reads as an empty room (the extras out of frame); the hook shows the board only in pieces | nit | direction | the class seated in frame; the hook opens on the whole board |

Fine, by the reviewer's measure: the specs, loudness (-14.2 LUFS, -2.4 dBTP), no flashes, no stray or black frames,
every shot's first frames textured, every line at its planned start, the captions' words, caps and emoji, heads clear
of the captions, every boom on its hit, the music 15-20 dB under the voice, the premise at frame 0, no logo or
reference content, teen-appropriate.

All eleven fixed in the tools or the staging; the whole video shot again from them (the two narrator lines
regenerated: "[curious]" and "[deadpan]" still read an octave down, "[annoyed]" and "[frustrated]" keep his voice).

## Round 2 (2026-11-08, on `out/group-project.mp4` of 07:38)

No must-fix problems. Evidence in `build/review2/group-project/`.

| # | Finding | Severity | Fix |
|---|---|---|---|
| 1 | The presentation two-shot too tight: arms out at both edges, her hand meeting his forearm (the framing check projects heads only) | should | her arms at her sides |
| 2 | Gestures still clipped in close-ups: the hook's arms out, the girl's cheer at the edges | should | the hook's hands on his head; her shot wider |
| 3 | Half-faces at both edges of `the_chat` | should | the front pair moved inside the frame; the back row dropped (at the push-in's edges it could only show as half-faces: the plan's new edge check flagged both) |
| 4 | Captions 2 frames before four cuts, over the shot before | nit | a caption due up to 2 frames before a cut waits for it; selftest |
| 5 | Line 3 lower (157 Hz) than the narrator's others | nit | kept: inside the register check, a sarcastic read |
| 6 | `alone` opens with a whip, not a reveal | nit | a slower pull-back |
| 7 | The hook shows the board in pieces | nit | the narrator centred under it, the shot opening wide on it |
| 8 | "September." left alone as a caption | nit | a long comedy sentence splits at its comma; selftest |
| 9 | "seen." touches the jock's chin | nit | the face framed higher |
| 10 | Crossed arms read as two boxes in `forty` | nit | arms at his sides |

Fine, by the reviewer's measure: every check on the file (-14.2 LUFS, -2.4 dBTP), every line on its planned start to
the sample, the captions' words and pace (14.6 characters a second), faces on their words within 4 frames, every boom
on its punch with its punch-in and its tail ducked, the voice 18-23 dB over the bed, narrator lines within 1.2 dB of
each other, no jump cuts (2.3x and 2.15x where it was 1.17x), a clean loop, teen-safe.

Seven shots restaged and shot again (`plan --keep-shots --replan ...`). Re-planning them with the camera aimed where each pose puts the face moved one: `alone`'s pull-back starts on the facepalm's lowered face.

## Round 3 (2026-11-08, on `out/group-project.mp4` of 10:52)

A third fresh reviewer, with the earlier rounds. No must-fix problems; every measured check passed again. Evidence in
`build/review3/group-project/`.

| # | Finding | Severity | Cause | Fix |
|---|---|---|---|---|
| 1 | Two one-word punches captioned before they're heard: "WE?!" 13 frames early, "seen." 5 | should | the take's soft glide under the music was called the first word; a caption snapped back to a cut | a line's first caption waits for the take to be heard (within 18 dB of its peak); a snap back keeps a caption within 2 frames of its word; selftests |
| 2 | Lines said but not shown: "every single slide" over him crying by the window; "we all get the same grade" over the teacher | should | direction | a new shot over his shoulder onto a laptop reading "Slide 40 / 40" (a new prop); the three of them in a row, an A+ popping over each on its word |
| 3 | Arms cut by the frame: the girl's cheer, the hook's hands on his head, her hands on hips in `as_we` | should | framed for faces | the hook and the title page framed wider (the plan's gesture check passes); `as_we` keeps the pose of the shot before |
| 4 | Nobody visibly says "Seen." | nit | the jock's sleepy face held through his line | his eyes open, deadpan, on his line |
| 5 | The girl's pose jumps across the `pres_day` cut | nit | | as above |
| 6 | No boom after the premise | nit | | a boom after line 1 |
| 7 | The board never whole | nit | the push started at once | the hook holds wide on the whole board for "Nah," and pushes in on "why" |
| 8 | Captions: l2 up whole before its last clause; l8's "..." dropped; "and on presentation day?" to x 961, under the Shorts buttons | nit | | a comedy line breaks at its commas; a word-ending ellipsis stays; an emoji takes its word to the next row (selftests) |
| 9 | `package.md` said 27.3 s; `caption_pace.py` found no captions in the pipeline's words | nit | | 26.9 s; it reads the pipeline's word file now |

Nine shots planned again and shot again: `slides` is new, and the shots after it kept their seeds (their drift), so
`pres_day` and `we` kept their frames. `slides` was shot a second time: from over his shoulder his head hid all of
the screen but "de 0"; it's shot from high over his head now.
