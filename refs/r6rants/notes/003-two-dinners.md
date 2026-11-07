# 003: He Ordered 2 Dinners Every Night (6,386,754 views, published 2026-05-18)

**Format:** story (third-person narrated tearjerker: a mystery, its answer, a kindness arc, a death twist, a letter
payoff)  **Length:** 36.62 s, 60 fps, 1080x1920
**Measured:** `analyze.py` reports 44 cuts, but the sheets show 27 real cuts. The other 17 are camera moves and snappy
poses (see "Checks against 001"). So 28 shots: median 1.21 s, mean 1.31 s, range 0.50-2.80 s, first cut at 0.87 s.
153 words at 4.21 words/s, first word at 0.00 s, no pause longer than 0.34 s. -14.3 LUFS, true peak +0.8 dBTP, LRA 2.2 LU.
Evidence is in `build/study/r6rants/003x/`:
- `s_*.jpg`: frame strips around every raw cut.
- `framestats.png` and `.csv`: per-frame difference, HSV saturation and warmth (mean R minus mean B). Computed on a
  108x192 downscale with the caption band left out.
- `music_side.png`, `music_sustained.png` and `zoomspec.png`: the side (L-R) channel, the time-median-filtered
  spectrum, and zoomed spectrograms.
- `faces_a.jpg`, `grid_a.jpg`, `grid_b.jpg`, `crops_*.jpg`: faces and details at full size.

## In one line
A pizza delivery driver wonders why an old man orders two of everything every night and eats alone. It's for his dead
wife. The driver starts eating with him; the old man dies in his sleep and leaves him a thank-you letter.

## Why it works
1. **An odd fact made visual in 8 s.** The title and first line state it ("ordering the EXACT same meal EVERY night",
   0.00-3.80). Three matched inserts show it: TWO soups (4.00), TWO drinks (4.67), TWO slices of PIE (5.37), all on the
   same table, same angle and same push-in. Then he eats alone with both meals (7.47). The question (for whom?) is
   obvious, and the story says it aloud by 10.2 s: "the driver FINALLY asked why". *heard + seen*
2. **Plant the answer, then reveal it with the camera.** The empty chair fills the foreground of the "he ALWAYS ate
   ALONE" shot (7.47), with the camera behind it. At 12.25 he points and the camera swings down to the chair
   (12.35-12.55). At 13.93 the reverse angle shows his wife sitting in it. The camera reaches the chair 1.4 s before he
   explains it ("my WIFE used to SIT there", 13.92). *seen + heard*
3. **Two turns, not one.** The hook is answered by 18.3 s, halfway through. Then a new arc (kindness, 18.5-24.5) builds a
   routine ("EVERY night after WORK", 22.02-24.46), so breaking it ("then one evening / nobody answered the door", 24.58)
   lands as the twist. The letter (29.2-36.3) explains the opening fact: he was "waiting for someone again, instead of
   waiting to die". *heard*
4. **Picture and sound carry the feeling; the voice never stops.** The narration runs at 4.21 words/s and never pauses
   longer than 0.34 s. *measured* The feeling comes from five other things instead:
   - a color script: warm, saturated interiors at saturation 109-181, a gray graveyard at 27, a faded flashback;
   - a quick desaturation on the driver's death reaction (28.27-28.37);
   - two red pulses on the heaviest words, "colder" (17.93-18.27) and "die" (36.17-36.50);
   - a music bed that adds a layer at the empty chair (about 12.6 s) and changes chord for the letter (about 32 s);
   - three knocks at the twist (24.69-25.15).
5. **Mirror shots show change without words.** The old man alone at the grave (15.30) is repeated with the driver beside
   him holding the rose (23.70), in the same composition. Eating alone with two meals (7.47) becomes laughing over dinner
   together (20.97-22.87). The letter holds a photo of that dinner (32.63). *seen*
6. **One shot per caption phrase.** There are 26 caption phrases and 28 shots. *measured*
   - 20 of the 27 cuts start a phrase, 0.01-0.19 s (median about 0.1 s) after its first word.
   - The other 7 cut in the middle of a phrase, on the word they illustrate: "an old man" 0.87, "driver" 19.10, "stayed to
     eat" 20.97, "passed" 28.27.

## 1. Hook (0-3 s)
- **First frame:** a radial zoom blur. The driver is small in the middle of a green field, with red and yellow streaks
  around him and the pizza shop as a blurred band. The caption "a delivery driver noticed an / OLD MAN" is already on
  screen and sharp, so it sits above the blur. It is weak as a still. The first sharp frame (0.20) shows the driver in
  medium shot by his red scooter. *seen*
- **First line:** "A delivery driver noticed an old man ordering the exact same meal every night.", 0.00-3.80. *heard*
- **0.00-0.20:** a fast push-in from extreme wide to medium shot while the blur clears.
- **0.25-0.50:** the driver thrusts a pizza box at the lens, with an open grin. The "Builder Brothers PIZZA" logo fills
  the lower half of the frame. *seen*
- **0.87:** cut to the old man's front door swinging open (0.87-1.15) as the camera pushes through the doorway. He waves
  with a closed-eye grin (1.2-2.2). *seen*
- **1.87:** the caption changes to "ordering the EXACT same meal / EVERY night" while the picture is still on him.
  *measured*
- **2.23:** cut to a close-up of the driver: wide eyes, flat mouth. The camera pulls back to medium shot by 2.50. His face
  swaps to a raised brow and small frown at 2.42, and his hand comes to his chin at 2.63. He holds that thinking pose
  until 4.0. *seen*
- **3.0:** the thinking driver by his scooter: his curiosity is the viewer's. *seen*
- **Promise:** something is strange about this order. *heard*
  - Sharpened at 3.94-8.34: two of everything, and he eats alone.
  - Asked at 8.68-10.24.
  - Answered at 13.92-18.26: his wife used to sit there, and she died three years ago.

## 2. Script and story
Script. The captions are the spelling; the transcript agrees word for word (153 words).

| Time | Speaker | Line (as captioned) |
|---|---|---|
| 0.00 | Narrator | a delivery driver noticed an / OLD MAN |
| 1.66 | Narrator | ordering the EXACT same meal / EVERY night |
| 3.94 | Narrator | TWO soups / TWO drinks / TWO slices of PIE |
| 6.38 | Narrator | but the STRANGE part was / he ALWAYS ate ALONE... |
| 8.68 | Narrator | one night the driver FINALLY / asked why |
| 10.52 | Narrator | the old man SMILED sadly- / and pointed at the EMPTY / chair across from him |
| 13.92 | Old man (no change of voice measured, see 8) | my WIFE used to SIT there |
| 15.18 | Old man | she passed away THREE years / ago... / but eating ALONE feels / colder...💔 |
| 18.54 | Narrator | the next DAY the driver / brought him a free / homemade DESSERT and / stayed to EAT with him |
| 22.02 | Narrator | AFTER that / he SAT with the old man / EVERY night after WORK |
| 24.58 | Narrator | then one evening / nobody answered the door |
| 26.48 | Narrator | a neighbor quietly told him / the old man had passed away / in his sleep |
| 29.18 | Narrator | a week later the DRIVER / received a letter / the old man had written / BEFORE he died |
| 32.52 | The letter, read aloud | thank you for making me FEEL / like I was WAITING / for someone AGAIN / instead of WAITING to die... |

The letter prop on screen (32.63-35.43) reads: "Thank you for making / me feel like I was / waiting for someone
again...", then a photo of the dinner shot (shot 17), then "instead of waiting to 💀". *seen*

Beat sheet:

| Time | Beat | What the viewer learns or feels | Why they keep watching |
|---|---|---|---|
| 0.0-3.8 | Setup: a driver notices a regular's odd order | two characters, a job, a house | "exact same meal every night": what's odd? |
| 3.9-6.1 | The detail: two of everything | the clue (food for two) | each insert adds an item: a rule of three |
| 6.4-8.3 | The contradiction: he eats alone | the mystery, stated | "but the STRANGE part was", plus the driver peeking through the window |
| 8.7-10.2 | The question, asked in the story | the viewer's own question | the answer is due |
| 10.5-13.7 | Sad smile, point, the empty chair | the answer starts in the picture | the camera reveals the chair |
| 13.9-18.3 | "My wife used to sit there... colder" | grief; the hook is answered at 50% | the wife in the chair, the grave, the red pulse |
| 18.5-21.9 | The driver brings dessert and stays | warmth; a new arc begins | the door opens on a smiling face |
| 22.0-24.5 | Montage: every night after work | a routine is built | four shared moments in 2.7 s, ending at the grave together |
| 24.6-26.3 | The routine breaks: nobody answers | dread | three knocks, a worried face |
| 26.5-29.2 | The neighbor: he died in his sleep | the twist: shock, grief | crying close-up, color drains |
| 29.2-32.3 | A week later, a letter he wrote before he died | anticipation | a new object: what does it say? |
| 32.5-36.3 | The letter | catharsis; the opening fact explained | text on screen, a photo of their dinner, red pulse, hard cut |

Emotional track (how picture and sound carry each beat):

| Time | Feeling | Picture | Color | Sound | Caption |
|---|---|---|---|---|---|
| 0-3.8 | light curiosity | grin, wave, puzzled close-up | noon sun, saturation 110-155 | sparse music | caps on EXACT, EVERY |
| 3.9-8.3 | intrigue | matched inserts, peeking, eating alone | outdoor inserts (warmth +2 to +5), then a warm interior (+78 to +97) | same | "ALONE..." |
| 8.7-13.9 | expectancy, then sorrow | the question, sad smile, point, the chair | warm | a new music layer at about 12.6 s | "sadly-" (a dash) |
| 13.9-18.3 | grief | the wife in memory, the grave, him alone | faded flashback; grave at saturation 27; red pulse on "colder" | fuller music | the only emoji, 💔; "..." |
| 18.5-24.5 | warmth | the door opens on a smile, laughing meals, the couch, the grave together | warm and saturated (109-181) | same | caps return: DAY, DESSERT, EAT, AFTER, SAT, EVERY, WORK |
| 24.6-29.2 | dread, shock, grief | the driver knocking (from behind), worried close-up, the neighbor, crying close-up | daylight; desaturates at 28.27-28.37 | three knocks | no caps at all for four captions |
| 29.2-32.5 | quiet suspense | mailbox, reading | neutral daylight | new bass note and chord from about 32 s | DRIVER, BEFORE |
| 32.6-36.6 | catharsis | the letter from his point of view, with the photo; the crying face | red pulse on "die" | music side channel about +3 dB above the start | FEEL, WAITING, AGAIN, WAITING, "die..." |

**Structure.** Five parts:
1. Mystery (0-10.2).
2. Answer (10.5-18.3).
3. Kindness arc and routine (18.5-24.5).
4. Twist (24.6-29.2).
5. Payoff object (29.2-36.6).

The answer lands at 38-50% of the runtime, the twist at 67%, and the payoff fills the last 20%.

**How the twist is set up.** *seen + heard*
- Death is already in the story: the wife, and the grave at 15.30.
- The montage ends at the grave with both of them (23.70), one shot before the routine breaks.
- The routine line ("EVERY night after WORK") comes right before "then one evening", so the broken routine reads as bad
  news.
- His death is never shown. It is told by a neighbor seen only from behind, and felt in the driver's crying close-up.
- The death section's four captions drop all caps.

**Payoff.** The letter is an object the viewer reads with the driver, from his point of view. That shot (32.63-35.43) is
the longest in the video, 2.80 s. Its photo is a still of the happiest moment: the dinner at shot 17's table, framed a
little wider. Its last line explains
the title's odd fact: he set two places because he was "waiting". *seen + heard*

**Ending.** *measured + seen*
- The last word, "die", starts at 36.14.
- A red pulse runs 36.17-36.50.
- The audio is cut hard at 36.58: the level falls from -25 to -58 dBFS within 40 ms.
- The picture ends at 36.62 on the crying driver.

There is no narrative loop. On replay, the first image (the same driver, grinning) contrasts with the last (crying).

**Writing voice.**
- Third person, past tense.
- 13 plain declarative sentences of 6-18 words (mean 11.8). No slang, no jokes.
- Time markers open the acts: "One night", "The next day", "After that", "Then one evening", "A week later".
- The old man's two lines and the letter are first person.
- The last line repeats a word: "waiting for someone again, instead of waiting to die".
- The only humor is incidental and visual: meme photos on the shop signs, fast food standing in for the "homemade
  dessert", the 💀 in the letter, a face in a window (section 4).

## 3. Cast

| Character | Role | Avatar | Faces (time) | How the look says who they are |
|---|---|---|---|---|
| Driver | protagonist: carries the kindness and the grief | R6. Classic bright-yellow head and arms; red short-sleeved collared work shirt over a black V; dark navy pants; red cap. Props: pizza box, red scooter with a delivery box, paper bag, red rose, envelope, letter | open grin (0.00); wide eyes, flat mouth (2.23); raised brow, small frown (2.42, mid-shot); one eye squinted, peeking (6.43); dot eyes and "o" mouth (8.70); closed-eye smile (19.10); laughing (20.97); closed-eye grin (22.07); wide eyes, open smile (22.87); closed eyes, sad brows (23.70); dot eyes, wavy mouth (25.40); blank white eyes, open wavy mouth, shocked (26.57); big glossy blue eyes, tear, frown (28.27, again at 35.43); round eyes, tiny "o" (29.37); eyes up, reading (30.97) | yellow "noob" skin plus a uniform: an ordinary working guy whose job reads without words |
| Old man | the mystery | R6. Pale skin; bald with white side hair; full white beard and mustache (3D accessory); dark pants. Two plaid shirts: a navy-blue long-sleeved one (0.87-2.23, 10.63-12.07, 16.83-18.60) and a near-black short-sleeved one (7.47, 12.07-13.93, 15.30, 18.60-24.63). They swap within the same scene, a continuity slip that clearly didn't matter | closed-eye grin, waving (0.87); sad, with worried brows and small flat mouth (7.47, 15.30); sad smile, worried brows over a toothy grin (10.63), "smiled sadly" taken literally; worried, wavy mouth (12.07); sad, downcast eyes (16.83); "O" surprise (18.70, mid-shot); laughing (20.97, 22.07); smiling (22.87, 23.70) | bald, white beard, plaid: a grandfather at a glance |
| Wife | memory | R6. Brown skin; cream head wrap with loose white strands; black rectangular glasses; white blouse with green dots | big toothy grin, squinting (13.93-15.30) | joyful, the opposite of his face; she eats the same soup and drink |
| Neighbor | messenger | R6. Long white hair; green striped cardigan; magenta pants; back to camera | never shown | anonymous: she is the news, not a person |

## 4. World, set and light
- **Pizza shop lot** (0-0.87, 2.23-6.43). Mid detail.
  - An open grass field with a white-and-red fast-food building on a gray brick base.
  - A red "Subscribe" sign on its roof, styled like YouTube's button (4.00-6.43).
  - Signs carrying circular photos of real people's faces (meme images), visible 0.25-6.43.
  - A red delivery scooter.
  - For the inserts, a plain wooden folding table on the grass, used as a product stage (4.00-6.43).
- **Old man's house, outside** (0.87-2.23, 24.63-28.27). High detail.
  - White clapboard siding, red window and door trim, a porch lamp, white wooden steps, shrubs.
  - An upstairs window holds a decal of a white grinning face (26.57-28.27): a hidden horror-meme gag.
- **Old man's house, inside** (6.43-13.93, 16.83-24.0). Dense, cozy, high detail; probably a furnished house kit (guess).
  - Dining room: warm yellow-orange walls, floral curtains, wood trim, framed pictures.
  - Living room: dark green walls, a framed painting of a house, a CRT TV, a wood stove with an orange glow, tulip ceiling
    lamps, a plank ceiling.
  - An armchair by the front door.
  - A blue-walled room with a white stove (the pie shot).
  - A couch room with green walls and cream curtains.
- **Graveyard** (15.30-16.83, 23.70-24.63).
  - A dark gray tombstone in the foreground, a bare blocky tree, a brick wall with pillars, other stones.
  - Gray-green ground, an overcast sky, fog at the horizon.
  - The red rose is the only saturated color.
- **Driver's home** (29.37-36.62): a beige wall, a blocky brown door frame, gray steps, a white mailbox, grass, a red
  stepped roof edge. The simplest set in the video.
- **Light and grade** (per-shot means; *measured*):
  - Interiors are warm and saturated: saturation 109-181, warmth +31 to +97. Light comes from tulip lamps and the stove
    glow off yellow and green walls, with soft shadows.
  - Exteriors are noon daylight with crisp shadows: the pizza lot at saturation 120-155 and warmth +2 to +19, the
    driver's home at 105-113 and +22 to +30.
  - The graveyard is near-gray: saturation 27 with the old man alone, 68 with the red-shirted driver; warmth +9 and +21.
  - The flashback is faded. The same floral window measures saturation 180 in the present (shot 7) and 111 in the
    flashback (shot 12). Its black level (2nd percentile of brightness) is 22, against 8-11 in present-day interiors. The
    framing differs, so treat this as indicative.
- **Time of day** is always daylight, including "then one evening" (24.58). The video makes no attempt at evening light.
  *seen*

## 5. Camera: the shot list
Sizes: EWS/WS/MWS/MS/MCU/CU are extreme wide to close-up; OTS is over the shoulder; POV is point of view.

| # | Time | Length | Size | Angle | Move | Subject | Why this shot |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.87 | EWS to MS | eye | push-in with radial blur (clear by 0.20), then hold; box thrust at the lens 0.25-0.50 | driver, pizza box, scooter, shop | who he is, and his job |
| 2 | 0.87 | 1.37 | MWS through a doorway | eye, from the porch | door swings open (0.87-1.15) as the camera pushes in | old man waving, closed-eye grin | the second character: friendly, at home |
| 3 | 2.23 | 1.77 | CU to MS | eye | pull-back 2.23-2.50, then hold | driver puzzled; brow up 2.42; hand to chin 2.63 | his curiosity is ours |
| 4 | 4.00 | 0.67 | MWS insert | slightly high | push-in about 0.25 s, easing out | two soup bowls on a table on the grass | "TWO soups" |
| 5 | 4.67 | 0.70 | same | same | same | two striped drinks | "TWO drinks" |
| 6 | 5.37 | 1.07 | same | same | same | two pie slices | "TWO slices of PIE" |
| 7 | 6.43 | 1.03 | MCU through a window, from inside | eye | pull-back through floral curtains | driver peeking, one eye squinted | snooping: the mystery |
| 8 | 7.47 | 1.23 | MS | high, from behind the empty chair | slow drift | old man alone with two meals | the contradiction; plants the chair |
| 9 | 8.70 | 1.93 | MS, OTS of the old man | eye | slow drift | driver at the door, "o" mouth | the question |
| 10 | 10.63 | 1.43 | OTS to MCU | eye | truck that slides the driver's head out (10.63-11.0) | old man, sad smile | the answer starts on his face |
| 11 | 12.07 | 1.87 | MS, then low WS | side, then low near the floor | point (12.25-12.35), then a swing down to the chair (12.35-12.55) | old man, the empty chair | the camera does the reveal |
| 12 | 13.93 | 1.37 | MS, OTS from his seat | eye | slow drift | the wife in the chair, grinning; faded grade | who sat there |
| 13 | 15.30 | 1.53 | MS | low, stone in the foreground | slow arc | old man with a rose at the grave | she is dead |
| 14 | 16.83 | 1.77 | OTS to MS | eye | truck off the driver's head (16.95-17.30), then hold; red pulse 17.93-18.27 | old man, sad | the grief line |
| 15 | 18.60 | 0.50 | MCU, three-quarter back | eye | static | old man in an armchair turns to the door ("O" at 18.70) | someone is there |
| 16 | 19.10 | 1.87 | MWS from inside | eye | door swings open 19.10-19.25, then hold | driver with a paper bag, closed-eye smile | the kindness |
| 17 | 20.97 | 1.10 | MS two-shot | eye, table height | slight drift | both laughing over a burger, fries and onion rings | together |
| 18 | 22.07 | 0.80 | OTS of the old man | eye | slight drift | driver grinning across a whole lattice pie | together, again |
| 19 | 22.87 | 0.83 | MWS frontal two-shot | eye, seated | push, then pull-back 23.00-23.15 | both on a couch, smiling | a routine |
| 20 | 23.70 | 0.93 | MS two-shot, stone in the foreground | low | orbit right | both at the grave; the rose is now in the driver's hand | mirrors shot 13; foreshadows |
| 21 | 24.63 | 0.77 | MS from behind | eye | static | driver knocking, window above | the routine breaks |
| 22 | 25.40 | 1.17 | CU to MCU | slightly low | pull-back 25.40-25.55 | driver worried, still knocking | dread |
| 23 | 26.57 | 1.70 | WS of the house | eye | slow drift | the neighbor (back to camera) tells the driver on the porch | the news, kept at a distance |
| 24 | 28.27 | 1.10 | CU to MCU | low | pull-back, and desaturation 28.27-28.37 | driver crying | grief |
| 25 | 29.37 | 1.60 | MS | eye | blurred swoop out 29.37-29.47 | driver at a mailbox with an envelope | a time jump, a new object |
| 26 | 30.97 | 1.67 | MWS, three-quarter | eye | slight push | driver reading | the letter |
| 27 | 32.63 | 2.80 | POV insert | high, looking down | static | the letter in his hands, with a photo of the shot-17 dinner | the payoff text |
| 28 | 35.43 | 1.18 | MWS to MS | eye | push-in until about 36.0, then hold; red pulse 36.17-36.50 | driver crying with the letter | the last line lands |

**Camera habits:**
- **Most shots (about 18 of 28) start with a move** that lands within 0.15-0.5 s:
  - push-ins (shots 1, 4-6, 28);
  - pull-backs from a close-up on a reaction (3, 22, 24);
  - trucks that slide the listener's head out of an over-the-shoulder shot (10, 14);
  - a swing to a planted object (11);
  - orbits at the grave (13, 20);
  - a door swinging open as the reveal (2, 16).
- **Holds drift slightly.** Only the letter point-of-view shot (27) is still.
- **Over-the-shoulder framing** for every exchange and for the memory (shots 9, 10, 12, 14, 18).
- **Mirror compositions** repeat a place and angle with one thing changed (13 and 20; 8 against 17-18).
- **Low angles** for grief (13, 20, 24).
- **Heads sit below the caption band** (23-29% from the top). In tight close-ups the caption overlaps the cap (3, 22,
  24). In shots 11 and 27 the caption moves up to 15-20% to clear the face and the letter.

## 6. Animation and acting
- **Held poses.** Big poses are reached in about 8-9 frames (the wave at 1.15-1.30, the point at 12.17-12.30). A two-stage
  move takes about 16 frames (arms cross, then hand to chin, 2.37-2.63). That is softer than 001's 4-6 frames.
  *measured on strips*
- **Gestures carry the lines:**
  - box thrust at the lens (0.25);
  - wave (1.2-2.2);
  - hand on chin (2.63-4.0);
  - peeking through the window (6.43);
  - slumped at the table (7.47);
  - point (12.25);
  - rose held to the chest (15.30, 23.70);
  - head turns to the door (18.75-19.05);
  - bag held out (19.10-20.97);
  - knocking (24.65-24.85; the arm stays up through 26.5);
  - the neighbor's arm gesture (26.6-28.2);
  - envelope (29.4);
  - letter held out in both hands (30.97-36.62).
- **Faces are 2D textures with no lip sync.** His own line, "eating alone feels colder", plays over a fixed face
  (16.83-18.26).
- **Faces change with the shot, not mid-shot.** There are about 27 face states across the cast, but only 2 swaps happen
  mid-shot (driver at 2.42, old man at 18.70). *seen*
- **A special face for the peaks.** The crying face (big glossy eyes and a tear) is kept for the two grief peaks (28.27
  and 35.43). *seen*
- **No walks and no particles.** The tear is painted on the face. *seen*
- **About 17% of frames repeat** during motion: about 50 unique frames/s inside a 60 fps file. *measured* That suggests a
  screen capture of playback rather than a frame-by-frame render. *guess*
- **Can't tell from stills:** idle motion such as breathing, and the easing inside the 0.1-0.25 s moves.

## 7. Edit and graphics
- **Pace.** 27 real cuts. Per 5 s: 4 4 3 4 5 4 2 1 (raw `analyze.py`: 11 6 7 4 8 5 2 1). Shots run 0.50-2.80 s. The edit
  slows for the payoff: the last 6.6 s hold only 3 shots, including the longest one (the letter, 2.80 s).
- **Cuts and captions move together.** Of 25 caption changes: *measured*
  - 20 come with a cut, on it or up to 4 frames ahead of it, usually 2 (as in 001).
  - 5 come mid-shot to keep up with the voice (1.87, 20.20, 22.57, 27.68, 34.63).
- **Captions:**
  - Phrase by phrase: 26 captions of 2-10 words (median 5.5), one or two lines.
  - White fill, thin black outline, no box. A geometric sans close to Montserrat Medium/SemiBold (double-story a,
    single-story g, straight y), the same as 001.
  - Line height on the 1920-px frame: 43 px for lines without descenders, 53-54 px with descenders.
  - The longest line spans 65-87% of the width.
  - Position: the block's top sits at 22.7% from the top and its bottom at 28.3-28.8%; single lines sit at 24.4-27.1%.
    The block lifts to 14.6-20.2% in shot 11 and to a 15.4% top in shot 27.
  - Captions swap in one frame, with no entrance animation.
  - Sentence case that starts lowercase, with stressed words in caps. No caps at all in the four death-section captions
    (24.60-29.37).
  - One emoji in the whole video: 💔 after "colder..." (16.83-18.57).
  - A trailing "..." on the sad lines, and a dash on "sadly-".
  *measured + seen*
- **Effects added on the picture:**
  - A radial zoom blur on the first shot (0.00-0.20), under the caption.
  - A blurred swoop for the time jump (29.37-29.47).
  - Red pulses: the frame's green channel dips and recovers over about 0.33 s, on "colder" (17.93-18.27, G 67 to 56 and
    back) and on "die" (36.17-36.50, G 134 to 74 and back). The captions stay pure white (255, 255, 255), so the tint sits
    under the text. It could be done in Roblox (a tweened ColorCorrection) or on the video track; I can't tell which.
  - A desaturation on the crying close-up: the shirt goes from RGB (209, 0, 23) to (166, 53, 73) within 0.1 s
    (28.27-28.37).
  - Nothing else: no shakes, flashes, stickers, zoom punches, freezes or other transitions.
  *measured + seen*
- **Other text is all in the world:**
  - The letter prop: a Comic Sans-like handwriting font, the photo, and the 💀 (Apple-style emoji).
  - The Subscribe sign.
  - "Builder Brothers PIZZA" on the box.

## 8. Sound

> Answered by the listener pass: `../listener/003.json`. Checked against measurement, and set beside the other videos, in `../SYNTHESIS.md` ("Sound, as heard"). It is a good lead on what each sound is and approximate on times.

- **Voice.** As far as measurement can tell, one narrator reads everything, including the old man's lines and the letter.
  *measured, rough* The voice's harmonic spacing (cepstrum, 200-4000 Hz) has a median of about 170 Hz on the narration
  and 164-171 Hz on the old man's lines, so his voice isn't pitched down. The letter measures about 211 Hz. That puts the
  voice in a high-male or female range.
- **Pace.** *measured*
  - 4.21 words/s overall; individual lines run 3.6-5.5 words/s.
  - The slowest lines are the grief line "She passed away... colder" (3.57), the list (3.64) and the hook (3.68).
  - The fastest are hand-off lines at 5.0-5.45: "My wife used to sit there", "The next day...", "A neighbor...", "A week
    later...".
  - Gaps between lines are 0.00-0.34 s. The longest come after "he always ate alone." (0.34 s at 8.34), "asked why."
    (0.28, 10.24), "feels colder." (0.28, 18.26), "pie." (0.24, 6.14) and "before he died." (0.20, 32.32). The only
    breaths fall at the end of the mystery, the question and the grief, and just before the letter.
- **Music.** It plays from the first sample to the hard end. *measured*
  - A steady pulse at about 71 BPM (`study.py`, confidence 4.1). The side channel shows onsets about every 0.42 s through
    the first 12 s: eighth notes at that tempo.
  - A bass and chord loop repeats every 6.5 s (chroma self-similarity 0.82 at 6.50 s). The bass holds about 87 Hz for
    4.9 s, then about 107 Hz for 1.5 s.
  - It is thin until about 12.6 s. Then a new layer enters as he points at the empty chair: the side channel's 150-400 Hz
    band jumps from about -50 to about -35 dBFS.
  - From about 32 s (under "before he died" and the letter) there is a new bass note and chord: the chroma moves from
    F/E/A to C#/D#.
  - There may be a texture change after the knocks (about 25.3 s), but it is less clear.
  - Overall, the side channel rises from -31.5 dBFS (0-11 s) to -29.3 (11-24 s) to -27.3 (24-36.6 s), while the mid
    stays flat at -15 to -19. The bed grows under a steady voice.
  - It sounds like a slow, sad piano with strings or a pad entering at 12.6 s. *guess*
- **Effects.** *measured*
  - Three knocks show as low thumps at 24.69, 24.92 and 25.15 s: the 30-180 Hz band rises 10-11 dB over its 1-second
    median, with a broadband click on the first. They sit under "then one evening," on the shot of him knocking.
  - `audio.md`'s three onsets outside words are not effects. The one at 5.17 is the "t" of "two" (5.22). The ones at 18.35
    and 18.45 are music notes in the gap after "colder"; there is no low thump there.
  - A broadband onset at 36.19, with 2-10 kHz energy until the end, falls inside the red pulse. It may be an effect or the
    tail of "die".
  - No bass booms in gaps (unlike 001).
- **Mix.** *measured*
  - -14.3 LUFS integrated; true peak +0.8 dBTP, over full scale like 001's +0.2; LRA 2.2 LU, flatter than 001's 4.0.
  - Only 9% of the runtime falls outside words. Those slivers read -18.6 dBFS against -17.1 under words, so the bed sits
    close under the voice. A listener should judge the balance.
  - Stereo: L/R correlation 0.87, side 11.5 dB under mid.
  - The audio ends on a hard cut at 36.58.
- **For the listener pass:**
  1. Human or TTS, male or female, and roughly what age? Is it one voice for the narrator, the old man (13.92) and the
     letter (32.52), or does it change?
  2. The music: which instruments, is it a known track, and are the changes at about 12.6, 25.3 and 32 s real?
  3. Are there three knocks at 24.69-25.15? Is there a knock or door sound at 18.3-18.6 (the old man turns to the door at
     18.70), or at the door openings (0.87, 19.10)?
  4. Is there a whoosh on the opening blur (0.00) or the swoop (29.37)?
  5. Is anything heard on the red pulses (17.93, 36.17), such as a heartbeat or a swell?
  6. Is there wind or ambience at the grave (15.30, 23.70)?
  7. Does the music stop with the hard cut at 36.58?

## 9. Retention devices

| Time | Device | How |
|---|---|---|
| 0.00 | movement in the first frame | zoom-blur push-in; the box thrust at the lens at 0.25 |
| 0.00 | premise as an odd fact | "noticed an OLD MAN / ordering the EXACT same meal EVERY night" |
| 4.00-6.43 | matched list of three | three inserts, same framing and push-in, the props swapped on each "TWO" |
| 6.43 | open loop | "but the STRANGE part was", plus the driver peeking through the window |
| 7.47 | contradiction | two meals, one man; the empty chair in the foreground |
| 8.70 | the viewer's question, voiced | "the driver FINALLY asked why" |
| 12.35 | reveal by camera | the swing down to the empty chair |
| 13.93 | the answer as a picture | the wife in the chair, in the faded flashback grade |
| 15.30 | escalation | the grave |
| 17.93 | accent | red pulse on "colder", plus 💔 |
| 18.60 | new loop | the old man turns to the door; it opens on the driver |
| 20.97-24.63 | compressed montage | four shared moments, each in its own place, 0.8-1.1 s each |
| 23.70 | mirror and foreshadowing | the grave again, now together |
| 24.58 | pattern break | "then one evening" right after "EVERY night", plus three knocks |
| 26.57-28.27 | twist | the neighbor's news, the crying close-up, color drains |
| 29.37 | time jump and a new object | "a week later", a blur swoop, the letter |
| 32.63 | payoff in text | the letter seen from his point of view, with a photo callback |
| 36.14-36.62 | final accent, hard end | "die...", a red pulse, the audio cut hard |

## 10. Packaging
- **Title:** "He Ordered 2 Dinners Every Night". *seen*
  - A past-tense statement of the odd fact, with the numeral "2". Title Case, no emoji, no hashtags, no question mark.
    Compare 001's question with emoji.
  - It boils the first two lines down to one fact the narration never says in those words, which opens the question:
    for whom?
- **First frame:** a blur, weak as a still. The sharp frames from 0.2 to 0.87 (the driver presenting a pizza box, under
  the caption with "OLD MAN") do the cover's job. In the feed, the caption gives the premise within the first second.

## 11. Principles to reuse / things not to copy
**Reuse:**
- **Premise:** a logline title about one odd repeated behaviour, a first line that states it, then the oddity made
  visible as a matched three-insert list.
- **Plant and reveal:** put the answer's object (an empty seat) in an early shot's foreground. Reveal it later with a
  camera move, and fill it in a reverse-angle flashback.
- **Structure:**
  - Answer the hook at about half time.
  - Open a second arc that builds a routine, then break the routine for the twist.
  - End on an object (a letter, message or photo) whose last line reuses a key word to explain the premise.
- **Mirror shots:** the same place and angle with one difference, to show change without words.
- **Color script by location:**
  - a warm, saturated home;
  - a gray, foggy grief location with one red accent;
  - a faded flashback with lifted blacks;
  - a quick desaturation on the shock reaction;
  - a short red pulse under the captions on the heaviest word of a key line.
- **Sound:** music in layers that enter at story turns, under continuous narration. One real-world sound for the twist
  (knocks).
- **Edit:** one shot per caption phrase. Cut about 0.1 s after the phrase's first word, with the caption 2 frames ahead.
- **Reactions:** cut to a close-up and pull back to medium close-up in about 0.2 s. Keep one special face (tears) for
  the peaks.
- **Captions:** in the top quarter for this format. Drop caps and emoji in the saddest stretch.
- **Transitions:** a blur swoop for a time jump.
- **Set dressing:** gags for rewatchers (signs, a face in a window), and an in-world Subscribe sign instead of an
  overlay.

**Don't copy:**
- **This story:** the two dinners, the dead wife, the delivery driver, and the letter's line "waiting for someone again,
  instead of waiting to die". The plot is close to widely shared "lonely old man" feel-good stories (guess), so write a
  new premise rather than a variation.
- **The characters' looks:** the yellow-skinned pizza driver in a red cap and shirt, the bald bearded old man in plaid,
  the wife with the head wrap and glasses, the white-haired neighbor.
- **Other people's marks:** "Builder Brothers PIZZA" (the Roblox game Work at a Pizza Place; the logo is seen, naming the
  game is my identification), the "M" fries box, and the photos of real people on the signs.
- **The letter's 💀 joke and the window face.**

## Checks against 001
1. **The cut list is inflated: holds.** 44 raw cuts, 27 real. *seen on strips*
   - The false cuts are camera moves: insert push-ins (4.12, 4.22, 4.75, 4.80), the door swing (0.92), a truck (11.00,
     11.05), a camera move (7.52, 7.70), the tail of a swing (12.72), the grave orbit (23.78, 23.90, 23.97) and pull-backs
     (2.63 with a pose, 25.58).
   - Two more are poses: the wave (1.32) and the point (12.20).
   - Every false cut falls in the first 0.65 s after a real cut, where the landing moves and poses happen. 12 of the 17
     fall within 0.3 s; the other five are 1.32, 2.63, 11.00, 11.05 and 12.72. No real cut was missed.
   - Fast moves never flagged at all: the pull-back at 2.30-2.50, the swing at 12.35-12.55 (flagged only at its edges),
     the truck at 16.95-17.30, the couch pull-back at 23.00-23.15.
2. **2D faces, no lip sync: holds. Swap timing doesn't.** No mouth moves on any line. But faces change with the shot, one
   face per shot, with only 2 mid-shot swaps. In 001 they changed on the word, often mid-shot.
3. **Captions: the style holds; position and emoji don't.** Same white, outlined geometric sans, phrase by phrase, with
   selective caps and captions 0-4 frames ahead of cuts. But the block sits at 23-29% from the top (about 79% in 001),
   and there is one emoji in 26 captions (nearly every line in 001).
4. **Bass hits after punchlines: absent.** There are no low booms in gaps. The only low thumps are the knocks heard in
   the scene (24.69-25.15); accents are visual (red pulses) instead.
5. **"The edit adds nothing" (001): contradicted.** This video lays a zoom blur, a blur swoop, red pulses and a
   desaturation over the footage. I can't tell whether they come from the editor or from in-engine color tweens. It also
   grades each location differently.
6. **Other differences from 001:**
   - The narrator is off screen, third person, past tense (001: on screen, first person).
   - Faster speech, 4.21 against 3.26 words/s, with no pause over 0.34 s.
   - Slower music (about 71 against 91 BPM) that changes in sections.
   - A title with no emoji.
   - No narrative loop.
   - Poses reached in 8-16 frames instead of 4-6.
