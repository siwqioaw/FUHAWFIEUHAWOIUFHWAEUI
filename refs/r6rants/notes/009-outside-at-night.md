# 009: DON'T Go Outside at Night (3,068,381 views, published 2026-08-21)

**Format:** in-this-world story (third-person narrator, "In this town, ..." rule premise, horror twist)  **Length:** 30.5 s, 60 fps
**Measured:** 32 raw cuts from `analyze.py`, but 25 real cuts on the strips. The 7 extra detections are an opening
blur-in, camera pushes and swoops, a door swinging open, and a repeat detection 4 frames after a real cut (section 7).
That gives 26 shots: median 1.19 s, mean 1.17 s, all between 0.52 and 2.07 s. First real cut at 0.55 s. 124 words,
4.09 words/s, first word at 0.00 s, 50 captions. -13.8 LUFS, true peak -0.3 dBTP, LRA 1.5 LU.

## In one line
Nobody in this town may go outside at night. Ethan calls it a lie and sneaks out. The street is empty, but every
neighbour stares at him in terror and his mother cries at the window. Then his father charges out with a bat yelling
"you monster", and Ethan understands: the rule exists because at night people can see what he really is, a shadow
creature.

## Why it works
1. **The rule and a monster in the first second** (0.00-1.90). Line 1 states the rule, which is also the title: "In
   this town, nobody is allowed outside at night". Under it, a cold open shows two people fleeing a drip-faced monster
   beneath a blood-red sky. It opens one question (why?), and the last sentence answers it. *heard + seen*
2. **Fair clues that read the wrong way** (11.7-24.2). Neighbours stare "terrified" straight into the lens, his mother
   cries behind the window, his father comes out with a bat. Horror grammar says the danger is behind Ethan; the
   reveal says the danger is Ethan. Every clue reads differently on a second watch. *heard + seen*
3. **Guard down, then up.** A slang sneer ("a goofy-ah lie", 4.9-5.8) and a troll grin on "Nothing happens."
   (8.37-9.03) make a comic false all-clear. Then the captions go lowercase, low-frequency energy rises (10.9-16.0),
   and the video's biggest bass hit lands on "Suddenly" as the front door bursts open (20.0). *seen + measured*
4. **The twist is told three ways in 8 s** (22.5-30.3): in the father's line ("you monster!"), in the picture (black
   particles, then a head turn to a skull face under a red sky at 26.60-26.77), and in the narrator's explanation,
   which reuses the rule's own words. A young viewer can't miss it. *heard + seen*
5. **Colour as a code, and a loop** (0-2.0, 26.45-30.53). A black sky marks Ethan's night; a red sky with a pink cast
   marks "what people see". The red world opens and closes the video. The last shot (a screaming man runs at the camera
   with a monster behind him, red sky) mirrors the first, so the restart reads as the same nightmare. *seen + measured*
6. **Literal illustration, clause by clause.** Every cut falls on the first word of a sentence or phrase (24 of 25
   within 0.1 s of a word onset). Every shot gets a new face showing the narrated feeling ("confused", "crying",
   "freezes"), and a new 2-3-word caption arrives every 0.6 s. *measured + seen*

## 1. Hook (0-3 s)
- **First frame:** f0-f2 are a vertical motion-blur smear (red, black, white). By f3 (0.05 s) it resolves into a
  medium close-up of a monster walking at the camera: a white R6 head with black dripping eye holes and a dripping
  black mouth, a black shirt, a blood-red sky with black streak clouds over a silhouetted town. Caption "in this TOWN",
  centred 24% from the top. f0 is a weak still, but from f3 on the frame works as a thumbnail: one face, red, high
  contrast. *seen (strip `009x/s_open_mom.jpg`)*
- **First line:** "In this town, nobody is allowed outside at night." 0.00-1.90. Strong low-frequency energy runs
  under the first words (0.05-0.70 s, RMS -7 to -10 dBFS, the loudest stretch of the video). *heard + measured.*
  Probably a boom. *guess*
- **0.40-0.55 s:** a fleeing man's blue shoulder enters the left foreground. At 0.55 a hard cut, matched on his run,
  to a three-shot: the man (cyan shirt, screaming face) and a woman (red top, long dark hair, scared face) run at the
  camera with the monster walking behind them. The camera tracks back at their pace. Caption "NOBODY is" (0.52).
- **1.0 s:** same shot. Captions "ALLOWED OUTSIDE" (1.02), then "at NIGHT" (1.63).
- **2.0 s:** cut to a warm, brightly lit bedroom. The mom (red bun, denim jacket) faces Ethan, whose back is to the
  camera. Caption "PARENTS say".
- **2.62-2.98 s:** the camera swoops past Ethan, through a close-up of the mom's stern face (2.87), and past the back
  of her head to land on the bedroom window. It is one continuous move; parallax shows the window holding still while
  her head slides out of frame. *seen (`009x/swoop_mom_window.jpg`)*
- **3.0-4.0 s:** through the window, a thin black long-limbed creature runs across the night street (3.10-3.70), on
  "something comes out after dark". The danger is shown, not only told.
- **Promise:** why can't anyone go out at night? It is half answered at 2.0-4.0 ("something comes out"), then answered
  in full and reversed at 26.36-30.34 ("...because that's when people can see what he really is").

## 2. Script and story
Script. Captions are the spelling. The transcript agrees word for word, except that it hears "goofy-ah" where the caption
says "GOOFY AHH".

| Time | Speaker | Line (as captioned; / = caption change) |
|---|---|---|
| 0.00 | Narrator | in this TOWN / NOBODY is / ALLOWED OUTSIDE / at NIGHT |
| 2.00 | Narrator | PARENTS say / it's because / SOMETHING comes OUT / AFTER DARK |
| 4.06 | Narrator | but ETHAN thinks / It's all / a GOOFY AHH LIE |
| 6.08 | Narrator | so ONE NIGHT / he SNEAKS outside / to prove / EVERYONE wrong |
| 8.36 | Narrator | NOTHING happens |
| 9.00 | Narrator | he WALKS through / the EMPTY streets |
| 10.32 | Narrator | then he notices / something strange |
| 11.72 | Narrator | everyone inside / is staring / directly at him / TERRIFIED |
| 14.44 | Narrator | ethan keeps walking / until HE REACHES / his OWN HOUSE |
| 16.42 | Narrator | he sees his / MOTHER CRYING / BEHIND the WINDOW |
| 18.26 | Narrator | confused / Ethan steps / toward the door |
| 19.98 | Narrator | SUDDENLY his FATHER / comes RUSHING out / gripping a / BASEBALL BAT |
| 22.50 | Father (whose voice: listener pass) | "don't you DARE" / "hurt my FAMILY" / "YOU MONSTER" |
| 24.44 | Narrator | ETHAN FREEZES |
| 25.18 | Narrator | then he FINALLY / understands |
| 26.36 | Narrator | the reason / he isn't ALLOWED / OUTSIDE at NIGHT / is BECAUSE / that's when PEOPLE / can SEE WHAT / he REALLY IS |

Beat sheet:

| Time | Beat | What the viewer learns or feels | Why they keep watching |
|---|---|---|---|
| 0.0-2.0 | The rule, with a legend | a town rule; people fleeing a monster | "why?", and a scary image |
| 2.0-4.0 | Authority and proof | the parents' reason; a creature crosses the street | the danger is real |
| 4.0-6.1 | The doubter | Ethan sneers "goofy-ah lie" | he's going to break the rule |
| 6.1-8.4 | The rule broken | bed, stairs, door | waiting for the monster |
| 8.4-9.0 | False all-clear | "Nothing happens.", troll grin | a laugh, and the sense it's too early to be safe |
| 9.0-10.3 | Alone | the empty street, a 1.3 s hold | the pause before the turn |
| 10.3-14.4 | Something strange | neighbours staring at him, terrified | the viewer assumes a threat behind him |
| 14.4-18.2 | Home | his mother crying | it gets personal |
| 18.2-20.0 | Approach | confused, he walks to the door | anticipation |
| 20.0-24.4 | Confrontation | father charges with a bat: "you monster!" | the twist, said out loud |
| 24.4-26.4 | Realisation | he freezes; black particles swirl around him | the transformation |
| 26.4-30.5 | Reveal and reason | the monster face; the rule's real reason; father flees a shadow giant | payoff, then the loop |

**Structure:** rule, doubter, the rule broken, mounting strangeness, confrontation, twist. The turn is "Suddenly"
(19.98) and the father's line (22.50-24.16). The visual payoff is the head turn (26.60-26.77). The explanation
(26.36-30.34) closes the question opened at 0.00, in the same words ("allowed outside at night"). There's no
resolution: it ends mid-chase, on an image like the opening one, so it loops.
**Writing voice:** third person, present tense, short declaratives of 2-10 words. Connectives a kid can follow
signpost each step: "But", "So one night", "Then", "Suddenly", "Then he finally understands", "The reason ... is
because". The only jokes are one slang intrusion ("a goofy-ah lie") and one deadpan anticlimax ("Nothing happens.");
the rest is played straight. There's one line of dialogue, the father's, in quotes.

### Suspense: how tension is built and released
- **Build (6.1-20.0):** the sneak-out (6.1-8.4), a false release (8.37), the empty street (9.0-10.3), "something
  strange" (10.3), the witnesses (11.7-14.0), the crying mother (16.4-18.2). Each step adds a clue and none explains
  it. The typography goes quiet: 10.30-13.75 are five lowercase captions in a row ("then he notices / something strange
  / everyone inside / is staring / directly at him"), then "TERRIFIED" alone in caps. The narrator slows from 4.43
  words/s (0-8.4) to 3.79 (8.4-20.0), and the longest pauses fall here: 0.34 s after "strange", 0.42 s after
  "terrified". Low-frequency energy rises from 10.9 to about 16.0. *seen + measured*
- **Release (20.0):** "Suddenly", the door bursts open, the biggest bass hit. It releases the tension into the reveal,
  not into relief. *measured + seen*
- **Scare or comedy?** It scares; it doesn't flip into comedy. The jokes come early, to lower the guard (4.9-6.0,
  8.37-9.03), and never at the end.

### What the title promises, and how it pays off
"DON'T Go Outside at Night" is a warning to the viewer, and the first line restates it as the town's rule. It
promises that whoever breaks the rule will meet whatever is out there. The payoff flips that: the rule-breaker *is*
what is out there. The last sentence repeats the rule with its real reason ("The reason he isn't allowed outside at
night is because that's when people can see what he really is"). The title, the first line and the last line say the
same words, and by the end they mean something new. *heard*

### How frightening it gets, and how it stays in bounds
- **The most intense moments:** the drip-faced monster in close-up from frame 3 (0.05-0.55); the father bursting out
  with a bat on the biggest hit (20.0); the skull face revealed by a head turn (26.60-28.20); a black giant with
  glowing eyes and fangs reaching over the screaming father (28.95-30.53). No scary image stays on screen longer than
  2.1 s. *seen*
- **Bounds:** no blood, no gore, and no blow lands. The bat is raised and pointed, never swung at Ethan. The next time
  we see the father, the bat lies on the ground and his shirt hem is torn (28.2): the harm is implied by a costume
  change, not shown. The chase ends before any contact. Faces are cartoon line art. The night stays brightly lit, so
  nothing jumps out of darkness. Two early jokes keep the register light. The scare is an idea (you were the monster),
  not gore. *seen*
- **My read:** spooky, about PG. The shadow giant could frighten a young child. *guess*

## 3. Cast

| Character | Role | Avatar | Faces (time) | How the look says who they are |
|---|---|---|---|---|
| Ethan | the doubter, then the monster | R6 with bevelled blocky parts and C-shaped claw hands (not stock R6 block hands); light-gray skin everywhere (RGB about 164-170); plain bright-green torso with a ridge at the hem; mid-gray legs; no hair, no accessories | skeptical (4.03-6.10), sneaky squint (6.62-7.40), nervous (7.62-8.37), troll grin (8.37-9.03), worried (10.33-11.73), puzzled (13.77-14.45), uneasy (14.45-15.22), puzzled again (18.17-18.80), scared (24.73-25.22), scribbled skull (26.60-28.20); shadow giant (28.95-30.53) | a blank everykid: the faces do all the acting, and the monster face lands on a clean, hairless head. The green shirt is the one saturated colour on a black street |
| Mom | warns, then cries | R6; red-orange messy bun; denim jacket over a gray-white striped top; maroon trousers; black shoes | stern frown (2.00-2.98); back of head (4.03-6.10); crying with blue tear streams (16.43-16.80); head dropped, face hidden (16.80-18.17) | the Roblox "mom" look; authority, then grief |
| Father | the confrontation | R6; light-gray skin; bald; beard drawn into the face; plain red torso; gray legs; wooden baseball bat | angry (20.00-24.45); shocked, shirt hem now torn (28.20-28.95); screaming (28.95-30.53) | the protective dad; his red shirt matches the danger palette |
| Drip-face monster | the legend (cold open) | R6; white head, black dripping eye holes and mouth; black torso; white arms; dark-gray legs | constant (0.05-2.00) | the town's nightmare |
| Fleeing man and woman | the legend's victims | R6, white skin; man in plain cyan; woman with long dark wavy hair and a red top | man screaming (round eyes, pinprick pupils, furrowed brow, mouth wide with teeth and tongue); woman scared (round eyes, wavy open mouth) (0.55-2.00) | generic townsfolk |
| The creature | "something comes out" | thin black stick-limbed figure with tiny white eyes, about 12% of the frame height | glimpse, 3.10-3.70 | a shape, not a face. Possibly the shadow giant seen from far away *guess* |
| Two neighbours | witnesses | yellow house: brown "bacon hair"-style hair, black leather jacket, teal top with a badge, a small bee pet floating beside him. Blue house: black ROBLOX-logo tee, black-and-red cap with the R logo | screaming (11.73-12.90); terrified, ring eyes (12.90-13.77) | classic Roblox avatars as recognisable extras |
| Shadow Ethan | the true form | very tall, thin, hunched black humanoid with long arms, long-fingered hands and smoky edges; glowing white round eyes and a jagged fanged grin | 28.95-30.53 | the "something", finally seen |

## 4. World, set and light
- **Ethan's house, inside** (2.00-7.40): a bedroom with orange walls, a gray ceiling, a peach floor, a bed with a
  pale-green blanket and a black night window; a staircase with wooden steps; a white front door with a yellow knob,
  blue floor inside. Built from primitives, low detail. *seen*
- **The suburb at night** (7.40-26.45): Ethan's red house with a white garage door; white paths; saturated green
  lawns; gray sidewalks; dark asphalt with a yellow double centre line; round dark-green trees; power lines;
  mailboxes; neighbouring houses in yellow, blue, tan and red. A blocky Roblox town map in smooth plastic and flat
  colours. *seen*
- **The neighbours' windows** (11.73-13.77): close views of a yellow wall and a blue wall, each window opening onto a
  lit interior.
- **The red world** (0-2.0, 26.45-30.53): the same town under a blood-red skybox with black streak clouds (and a blimp
  prop), with the light turned pink.

**Night lighting**, the main point of study here:
- **The night is only in the sky.** The sky is pure black (RGB 0,0,0 at 11.0 and 18.5), with no moon or stars.
  Characters are exposed as if by day: Ethan's skin measures 164 in the bedroom (5.0) and 170 on the night street
  (11.0); the father's is 178 outside his door at night (23.3). The light is neutral white (R-G 0 to +1), with no blue
  moonlight tint. *measured*
- **Light sources:** one soft directional key from above, and soft contact shadows on the ground whose direction
  changes as the camera moves around. There are no visible sources: no street lamps, no moon. *seen.* Likely Future
  lighting at day settings with a black skybox, or a night clock time with ambient raised. *guess*
- **Depth:** the road falls from luma 58 near the camera to 36 in the distance, and distant trees and houses sink
  toward black. No fog is visible. *measured + seen*
- **How dark it actually is:** per-shot mean luma (0-255) is 46-111 for night exteriors and 60-123 for interiors. In
  the night shots that show sky, 25-35% of the frame is near-black: that is the sky band the captions sit on. The night
  is barely darker than the day scenes overall. *measured*
- **Through the bedroom window** (3.0-4.0) the street is dimmer: grass at luma 77, road 57, sky RGB 17,10,9. *measured*
- **Interiors:** high-key and warm. Orange walls (RGB about 106,29,1 in shadow to 169,55,0 in light), gray ceiling,
  soft light from above. *measured + seen*
- **The red world:** the sky is a pure red hue (R 23-113, G and B near 0) with black streaks. A pink cast falls on
  every white (R-G +9 to +14 on skin and sidewalk); the grass stays saturated green; the distance sinks to dark
  red-brown. The cast starts exactly at the cut at 26.45 and lasts to the end, including the doorway shot at 28.2,
  where no sky is visible. Before 26.45 the same surfaces measure neutral. *measured*
- **Glow:** only the shadow giant's eyes and teeth glow (RGB 254,252,251, with a halo). The bloom is on emissive parts
  only; white sidewalks don't bloom. *measured + seen*
- **Grade:** no vignette (the ground reads 163, 166 and 167 at left, centre and right at 23.3), no visible grain.
  Clothes are at full saturation (green 1,158,2; red 162,1,2; cyan 3,146,198). *measured*
- **Readability:** faces are black line art on light-gray heads. Characters sit at luma 160-200 against a black sky
  (0) and a 37-58 road. The dark never hides anyone. *measured*

## 5. Camera: the shot list

| # | Time | Length | Size | Angle | Move | Subject | Why this shot |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.55 | MCU | eye, slightly low | 3-frame blur-in, then tracks back as he walks | drip-faced monster, red sky | a shock image from frame 3; the legend |
| 2 | 0.55 | 1.45 | MWS three-shot | waist height | tracks back at their running pace | man and woman flee at the camera, monster behind | states the danger: people run from it |
| 3 | 2.00 | 2.03 | MWS OTS two-shot, then CU, then the window | eye | slow push; swoop 2.62-2.98 past Ethan and the mom's face to the window; slow push on the window | mom warns Ethan; the creature crosses the street (3.10-3.70) | the parents' reason, then the proof |
| 4 | 4.03 | 2.07 | MWS to MCU | slightly high, OTS behind the mom (her hair and sleeve in the foreground) | continuous slow push-in | Ethan, arms crossed, skeptical | the doubter |
| 5 | 6.10 | 0.52 | WS | eye | static | Ethan on his bed, black window behind | "one night" |
| 6 | 6.62 | 0.78 | MWS | high, down the stairs | static | Ethan tiptoes down | sneaking |
| 7 | 7.40 | 0.97 | MS | eye, from outside | static, slight push | the door opens toward the camera (7.6); Ethan peeks out, nervous | crossing the threshold |
| 8 | 8.37 | 0.67 | WS to MS | eye | push-in, accelerating at 8.68-8.78 | Ethan on the lawn, troll grin | the anticlimax gag |
| 9 | 9.03 | 1.30 | MS to WS | low, road level, from behind | static; he walks away | Ethan alone on the centre line | the empty street, loneliness |
| 10 | 10.33 | 1.40 | MCU to MS | eye | pulls back (10.33-11.0), then tracks with him | Ethan walking toward the camera, worried | "he notices something strange" |
| 11 | 11.73 | 1.17 | MS (the window in WS) | eye, dutch about 5° | slow push | neighbour screaming in a yellow house's window | first witness |
| 12 | 12.90 | 0.87 | WS to MCU | eye, the dutch increasing | eased push-in, 12.90-13.45 | neighbour in a Roblox cap, terrified | second witness, closer |
| 13 | 13.77 | 0.68 | MWS, profile | low, road level | static | Ethan stops, puzzled | his reaction |
| 14 | 14.45 | 0.77 | MS | eye | tracks back | Ethan walks on, uneasy | he keeps going |
| 15 | 15.22 | 1.22 | MS, 3/4 rear | eye | follows him, then pans to reveal his house; he stops at 16.0 | Ethan reaches home | arrival |
| 16 | 16.43 | 1.73 | MCU | eye, framed by an orange sill | slow push | mom crying, then her head drops (16.8) | the clue gets personal |
| 17 | 18.17 | 0.63 | MS | eye | static | Ethan, confused | reaction; the caption names it |
| 18 | 18.80 | 1.20 | MS from behind | eye | follows him up the path | Ethan walks to the front door | anticipation |
| 19 | 20.00 | 1.50 | MWS to MS | eye | door bursts open (20.00-20.10); tracks back as the dad charges | dad with the bat raised | the jolt, on the biggest hit |
| 20 | 21.50 | 1.03 | MS | side, then high 3/4 rear | fast orbit up and around (21.50-21.80), then tracks | dad running, bat on his shoulder | energy and threat |
| 21 | 22.53 | 1.92 | MWS, full figure | eye, frontal | fast orbit of about 45° (22.53-22.82), then static | dad points at the lens, bat on his shoulder; his line | the twist line, aimed at Ethan (the lens) |
| 22 | 24.45 | 0.77 | OTS to MS | eye | swoop past the dad's shoulder (24.45-24.80) | Ethan frozen, scared | "Ethan freezes" |
| 23 | 25.22 | 1.23 | MWS | top-down | slow descend and push | Ethan in swirling black scribble particles | realisation; the transformation |
| 24 | 26.45 | 1.75 | MS to MCU | eye | slow push, faster at 27.4-28.1 | red sky; his head turns to show the monster face | the visual reveal |
| 25 | 28.20 | 0.75 | MWS, full figure | eye | static | dad backing away; bat on the ground; shirt torn | implied attack, the aftermath |
| 26 | 28.95 | 1.58 | WS to MS | eye (the dad's chest) | tracks back while the dad gains on the camera | dad flees, screaming; the shadow giant reaches over him | the true form; mirrors the opening chase |

Habits:
- **Almost every shot moves.** Slow push-ins (shots 3, 4, 8, 11, 12, 16, 23, 24); track-backs ahead of characters
  walking or running at the camera (1, 2, 10, 14, 19, 26); follows from behind (15, 18). Static holds are short
  (5, 6, 7, 9, 13, 17, 25).
- **Four fast eased moves of 0.3-0.4 s** change the framing inside a shot instead of cutting: 2.62-2.98, 21.50-21.80,
  22.53-22.82, 24.45-24.80. There is also a 0.5 s push at 12.90-13.45.
- **Angles carry meaning:** eye level for most shots. Low, at road level, for the lonely walk (9, 13). High down the
  stairs (6). Dutch on the witnesses (11, 12). Straight down for the moment he understands (23). Witnesses and the
  father look into the lens, so their fear and anger point at Ethan and at the viewer.
- **Composition:** wide lens with strong road perspective; the yellow lines lead into the dark. Subjects sit in the
  middle third, with heads at about 30-55% from the top, just under the caption block (20-28%). Caption and face read
  as one glance.

## 6. Animation and acting
- **Bodies:** stiff R6 walk and run cycles (legs and arms swinging as blocks). A crouched tiptoe on the stairs
  (6.62-7.40). Runners pump their arms with high knees (0.55-2.00, 28.95-30.53). Strong held poses carry the lines:
  arms crossed (4.03-6.10); the bat on the shoulder with the other hand pointing (22.7-24.45); a stiff "freeze" with
  arms slightly out (24.73-25.22); backing away with hands raised (28.2-28.95).
- **Snappy moments:** the door swings fully open in about 0.1 s (20.00-20.10) while the bat comes up; the bat goes from
  hanging to the shoulder in about 0.15 s (22.58-22.72). *seen on frame strips*
- **The reveal is a head turn, not a face swap.** At 26.45-26.60 the back of Ethan's blank head faces the camera. At
  26.60-26.77 (about 10 frames) the head turns round, showing the skull face from the side, then from the front. The
  body doesn't move, so it reads as the head swivelling on a still body. Whether the body faced front throughout can't
  be told from plain-coloured R6 parts. The face lands about 0.1 s before the word "isn't". *seen (`009x/s_2645.jpg`)*
- **Faces are 2D textures with no lip sync.** The father shouts his line (22.50-24.16) over a fixed gritted-teeth face.
- **One face per shot, changed at the cut.** No shot swaps its face texture mid-shot. The only mid-shot changes are
  heads moving: the mom drops her head into her arms (16.80), Ethan turns back to the camera (24.73), and the reveal
  turn (26.60). Two designs are reused: Ethan's puzzled face (13.77 and 18.17), and the scream face (the fleeing man at
  0.55, the father at 28.95).

Face log (*seen*, on 0.1 s strips and full frames):

| Time | Who | Face | When it appears |
|---|---|---|---|
| 0.05-2.00 | drip-face monster | black dripping eye holes, dripping black mouth | first sharp frame (f3) |
| 0.55-2.00 | fleeing man | round eyes with pinprick pupils, furrowed brow, mouth wide with teeth and tongue | at the cut |
| 0.55-2.00 | fleeing woman | round eyes, wavy open mouth | at the cut |
| 2.00-2.98 | Mom | stern: furrowed brows over round eyes, small down-turned mouth | at the cut; close-up at 2.87 |
| 4.03-6.10 | Ethan | skeptical: half-lidded eyes, one brow cocked, crooked "pfft" mouth | at the cut, on "But Ethan thinks" |
| 6.62-7.40 | Ethan | sneaky: eyes narrowed to lines, small smirk | at the cut |
| 7.62-8.37 | Ethan | nervous: round eyes glancing sideways, a sweat drop, flat mouth | as he appears in the doorway |
| 8.37-9.03 | Ethan | troll grin: huge toothy grin, squinting eyes | at the cut, on "Nothing" |
| 10.33-11.73 | Ethan | worried: small ring eyes, sweat drops, small frown | at the cut, on "Then he notices" |
| 11.73-12.90 | yellow-house neighbour | screaming: mouth wide, brows raised | at the cut |
| 12.90-13.77 | blue-house neighbour | ring eyes, wobbly open mouth | at the cut |
| 13.77-14.45 | Ethan | puzzled: one ring eye under a raised brow, the other narrowed, small open frown | at the cut, on "terrified" |
| 14.45-15.22 | Ethan | uneasy: big dark-ringed eyes, wobbly grimace | at the cut |
| 16.43-16.80 | Mom | crying: eyes squeezed shut, blue tear streams, gritted teeth | at the cut; her head drops and hides the face from 16.80 |
| 18.17-18.80 | Ethan | the puzzled face again | at the cut, on "Confused" |
| 20.00-24.45 | Father | angry: thick slanted brows, gritted teeth, beard | at the cut; held through his line |
| 24.73-25.22 | Ethan | scared: raised brows, round eyes, open mouth with teeth | his head turns back to the camera |
| 26.77-28.20 | Ethan | monster: scribbled skull, ring eyes in black sockets, skull nose, wide stitched toothy grin with drips | the head turn, 26.60-26.77 |
| 28.20-28.95 | Father | shocked: dot eyes, open mouth | at the cut |
| 28.95-30.53 | Father | the scream face from the cold open | at the cut |
| 28.95-30.53 | Shadow Ethan | glowing white round eyes, glowing fanged grin | at the cut |

- **Effects in the scene:** black scribble particles swirl outward on the ground around Ethan and over him, and dark
  veins appear on his green shirt (25.22-26.45). Wisps stay around his feet until 28.2. They look in-engine: they lie
  in perspective on the ground and cover parts of the body. *seen*. Also: glowing eyes and teeth on the shadow giant;
  the dropped bat prop and the torn shirt hem (28.2), which imply an attack off screen.
- **Can't tell from stills:** how smooth the in-betweens are; whether the walks and runs are keyframed or recorded
  loops; how the shadow giant moves (its arm reaches forward 29.0-30.4); the easing curve of the head turn.

## 7. Edit and graphics
- **Pace:** 25 real cuts. Real cuts per 5 s: 3 5 5 4 4 4 0 (`analyze.py`'s raw count: 6 6 6 4 6 4 0). The rhythm is
  steady: no shot under 0.5 s, none over 2.1 s. Every cut lands on the first word of a sentence or phrase: 24 of 25
  are within 0.1 s of a word onset (the exception, 15.22, is at +0.12 s). 22 of the 25 coincide with a caption change.
  On 20 of those the caption changes 1-2 frames before the picture; on 2, on the same frame. The other 3 don't sit on a
  caption change: at 4.03 the caption changes 4 frames after the cut, and at 12.90 and 28.95 the caption runs across
  the cut. *measured*
- **`analyze.py` against the strips** (`009x/cuts_a.jpg` to `cuts_d.jpg`, `dense_*.jpg`, `s_*.jpg`):

| Detected | Real? | What it is |
|---|---|---|
| 0.017 | no | the 3-frame blur-in (f0-f2) |
| 3.067 | no | the end of the swoop from the mom to the window (2.62-2.98): one continuous move |
| 4.10 | no | 4 frames after the real cut at 4.033; nothing in the picture changes except the caption (f246) |
| 8.733 | no | the push-in speeding up (8.68-8.78) |
| 10.40 | no | a fast pull-back right after the real cut at 10.333 |
| 20.30 | no | the door swinging open, the bat coming up, the camera pushing in (20.00-20.35) |
| 24.85 | no | the end of the over-the-shoulder swoop (24.45-24.80) |
| the other 25 | yes | hard cuts |

  It missed two 0.3 s orbits (21.50-21.80 and 22.53-22.82).
- **Captions** (seen at full size: `009x/caption_zoom.png`, `frames/f00060.png`, `f01400.png`):
  - 50 captions of 1-4 words (2.5 on average). Each stays on screen 0.28-1.15 s (about 0.6 s typical; the longest is
    "a GOOFY AHH LIE"). They change on the word, within about 0.15 s of the transcript's onsets. They cut in and out with no
    pop or scale animation (checked frame by frame at 0.52 and 2.80).
  - Font: a geometric sans close to Montserrat Medium (single-storey g, double-storey a, straight-tailed y). White
    fill, black outline of about 3-4 px at 1080 px width, no shadow, no box.
  - Size: cap height about 60 px (5.6% of the frame width), line pitch 96 px. The block is 33-51% of the frame width,
    two lines at most.
  - Position: centred horizontally. The block's centre is fixed at 24.0% from the top: one line sits at 22-26%, two
    lines span 20-28% (measured on 10 frames). That puts the caption in the upper third, on the sky or a wall, just
    above the faces, and clear of the Shorts interface at the bottom.
  - Case: sentence starts are usually lowercase ("in this TOWN", "so ONE NIGHT", even "ethan keeps walking"), but "It's
    all" and "Ethan steps" are capitalised, so it isn't strict. 51 of 124 words (41%) are in caps, spread over 34 of
    the 50 captions (counted on the transcript's 124 words; "GOOFY AHH" is one word to the transcript, so the share is approximate).
  Caps mark the loud or key words and drop out during the quiet stretches (10.30-13.75, 16.42-16.78,
    18.15-19.98).
  - No emoji, no "...", no question or exclamation marks. Straight double quotes appear only around the father's line.
- **Other graphics:** none (no stickers, emoji, arrows, zoom punches, shakes, flashes, freezes or transitions), apart
  from the 3-frame blur-in at 0.00-0.05. Roblox doesn't render directional motion blur, so the blur is probably an
  editor effect. *guess.* Everything frightening happens inside the scene: the sky, the particles, the glow, the torn
  shirt.

## 8. Sound

> Answered by the listener pass: `../listener/009.json`. Checked against measurement, and set beside the other videos, in `../SYNTHESIS.md` ("Sound, as heard"). It is a good lead on what each sound is and approximate on times.

- **Voice:** one narrator, in the third person; the father's line may be the same voice (listener pass). 4.09 words/s
  over the spoken span. By section: 4.43 words/s at 0-8.36 (setup), 3.79 at 8.36-19.98 (the walk), 4.04 at 19.98-24.44,
  4.24 at 24.44-30.34. There are ten pauses of 0.15 s or more, all at sentence ends. The longest is 0.42 s (14.02-14.44,
  after "terrified"), then 0.34 (after "strange"), 0.30 (after "lie"), and 0.28 (after "window", "monster!" and
  "understands"). There is no real silence anywhere. *measured from the transcript*
- **Music:** a continuous bed. The gaps between words hold -14 to -17 dBFS RMS with tonal peaks (for example 111, 137,
  189, 271 and 543 Hz at 14.05-14.40). `audio.md` estimates a steady beat at 176.5 BPM (confidence 3.75); that could be
  an 88 BPM half-time, or the rhythm of the speech. *measured.* The genre is for the listener pass.
- **Low end** (20-120 Hz, relative to its own peak at 20.1 s): -3 to -6 dB at 0.0-0.7, under the first words (RMS -7
  to -10 dBFS, the loudest stretch of the video; probably a boom, *guess*). Then -30 to -43 dB, essentially no bass,
  until 10.9. From
  10.9 ("something strange") to about 16.0 it sits at -14 to -29 dB, peaking at 13.7-14.0 on the cut for "terrified":
  a drone or a bass line enters with the strangeness. After 16.2 it is back to -30 to -43, until 0 to -8 dB at
  20.0-20.3. *measured*
- **The "Suddenly" hit:** after -13 dBFS at 19.80, the level dips to -18 to -20 dBFS for about 0.1 s (19.90-19.99),
  then jumps to -7 to -10 dBFS (20.05-20.20) with energy across the whole spectrum, while the door bursts open
  (20.00-20.10). It's the bright column on `audio.png`. *measured*
- **Onsets outside the words** (`audio.md`):
  - 14.17, 24.28 and 26.12 fall in the pauses after "terrified", "you monster!" and "understands": probably short
    stings after key lines. *guess*
  - 11.67, 16.35 and 18.20 (the strongest, at 2.7) fall 0.05-0.07 s before the next word, on cuts. They may be the
    next word's start (the transcript's times can lag) or a whoosh on the cut. *measured; what they are: listener pass*
- **Ending:** loud and bright to the last moment (30.30-30.48: -10 to -12 dBFS RMS, spectral centroid about 1.0-1.1
  kHz). The audio stops at 30.50 with no fade, which suits the loop. *measured*
- **Mix:** -13.8 LUFS integrated, true peak -0.3 dBTP, LRA 1.5 LU: flat and heavily compressed. Words measure -17.3
  dBFS median and gaps -19.2 dBFS, so the bed sits only about 2 dB under the voice. Apart from the two low hits under
  words (0.0-0.7, 20.0-20.3), no effect stands out of the bed the way 001's gap hits did. Loudest 0.5 s windows:
  0.0-0.5 (-13 dBFS), 20.0-20.5 (-15), 29.5-30.5 (-16, -15),
  23.0-24.0 (-16, the father's shout). *measured*
- **For the listener pass:**
  - Is the narrator human or TTS, and which voice? Does the father's line use the same voice, pitched or processed?
    Does the delivery drop or slow down in the walk (8.4-20)?
  - What is the music (horror ambient, phonk, piano, music box)? Does it change at 10.9 ("something strange"), at 20.0
    ("Suddenly") and at 26.45 (the cut to red)? Is the tempo about 88 or 176 BPM?
  - What are these sounds: the opening boom (0.0-0.7); the hit at 20.0-20.3 (a door slam, a bass boom, or both); the
    sounds at 14.17, 24.28 and 26.12; whatever is at 11.67, 16.35 and 18.20; the bright sound at 30.30-30.50 (a scream
    or a screech)?
  - Is there a door creak (7.6), footsteps, a whoosh on the swoops (2.6-3.0, 21.5, 24.45), a sound for the window
    creature (3.1-3.7), a comic sting on the troll grin (8.37), night ambience (crickets, wind)?
  - Does the music drop out anywhere, for example in the 0.1 s dip at 19.90?
  - Does the last sound flow into the opening boom when the video loops?

## 9. Retention devices

| Time | Device | How |
|---|---|---|
| 0.00 | pattern break | a 3-frame blur lands on a drip-faced monster under a red sky, over loud low end |
| 0.00-1.90 | open loop | the rule "nobody is allowed outside at night": why? |
| 0.55 | escalation | people run toward the camera, fleeing it |
| 2.62-3.70 | the promise shown | a swoop to the window; a creature crosses the street |
| 4.1-6.0 | conflict | the doubter: "a goofy-ah lie" |
| 6.1-8.4 | anticipation | the sneak-out: bed, stairs, door |
| 8.37 | false all-clear | troll grin, "Nothing happens." |
| 10.3-14.4 | mystery and misdirection | "something strange"; terrified witnesses stare into the lens; low end rises |
| 16.4-18.2 | escalation | his own mother crying |
| 20.0 | jolt | "Suddenly": the door bursts open on the biggest hit |
| 22.5-24.2 | reveal, spoken | "YOU MONSTER" |
| 25.2-26.4 | transformation | top-down shot, black particles swirling |
| 26.60-26.77 | reveal, seen | red sky; his head turns to a skull face |
| 26.4-30.3 | payoff and callback | the last sentence repeats the rule and gives its real reason |
| 28.95-30.53 | climax, then loop | a shadow giant chases the father at the camera; it ends on loud sound and restarts on the opening chase |

## 10. Packaging
Title: "DON'T Go Outside at Night": an imperative warning with one word in caps, no emoji, no hashtags. It is the
first line's rule turned on the viewer. 12 of the 16 titles in the set carry emoji or #hashtags; this one, like 002,
003 and 008, carries neither. The first frame (f0-f2) is a motion-blur smear,
weak as a still. From f3 on, the drip-faced monster close-up with "in this TOWN" is a strong image: one face, red and
black, high contrast.

## 11. Principles to reuse / things not to copy
**Reuse:**
- Make a rule of the world the first line, make the title that rule as a warning, and end on the same words with
  their real reason.
- Show the danger in the first second, as a cold open of the legend, and once more as a glimpse early on.
- Build a fair twist from three escalating clues that read as "danger near him" and later as "danger is him"
  (strangers' fear, family's tears, family's weapon). Deliver it three ways: a line, a transformation, an
  explanation.
- Put one or two jokes early (a sneer, an anticlimax) to lower the guard, and none at the end.
- Make night a black sky over characters lit like day: readability first. Give the twist its own sky colour, and use
  that colour in both the cold open and the ending so the loop matches.
- Give every shot a new face that shows the narrated feeling; black line-art faces on light-gray heads read in any
  light.
- Keep captions to 2-3 words in the upper third, just above the faces. Use caps for loud words and lowercase for the
  quiet build. Cut on each new sentence, with the caption one or two frames ahead of the picture.
- Suspense camera: track back ahead of approaching characters; shoot from road level for loneliness; tilt the frame
  on witnesses; go top-down for the moment of understanding; push in on reveals; reframe inside a scene with 0.3 s
  orbits.
- Sound: loud low end (a boom) on frame 1, low end that rises when the strangeness starts, a 0.1 s dip before the biggest hit (on
  "Suddenly"), short stings in the pauses after key lines, and loud sound with no fade at the very end.
- Kid bounds: imply harm (a dropped bat, a torn shirt), show no contact and no blood, keep each scary image under
  about 2 s, and end on a chase rather than a catch.

**Don't copy:**
- This story: the town rule, Ethan sneaking out, the crying mother, the father with the bat, "you monster", and the
  script itself, including "a goofy-ah lie".
- The characters' looks: the bald gray kid in a green shirt, the red-bun mom in denim, the bearded dad in red.
- The monster designs: the drip-faced cold-open monster, the scribbled skull grin, the glowing-fanged shadow giant,
  the stick creature.
- The town map and its blimp.
- The channel's "In this town / In this world" wording. Use the shape of a rule premise, in your own words.
- Real brand merch as set dressing (the ROBLOX-logo tee), unless it's a deliberate choice.

## Checks against 001's patterns

| 001's pattern | Here | Where |
|---|---|---|
| `analyze.py` over-counts, in clusters right after real cuts | Holds: 32 raw, 25 real, and 5 of the 7 false detections fall 0.07-0.40 s after a real cut. The causes differ, though: camera moves (4: two swoop ends, a push, a pull-back), a door swinging open (1), a repeat detection with only a caption change (1) and an editor blur-in (1), not snappy poses. | section 7 |
| It misses fast swoops | Holds, and it also goes wrong the other way: it missed 2 orbits (21.50, 22.53) and reported 2 swoops as cuts at their ends (3.067, 24.85). | `009x/s_2030_2150.jpg`, `s_2253.jpg`, `s_open_mom.jpg`, `s_2445.jpg` |
| Faces are 2D textures with no lip sync | Holds. | father's line, 22.50-24.16 |
| Faces swap mid-shot, on the word | Doesn't hold: one face per shot, changed at the cut, with no mid-shot texture swaps. The reveal is a head turn (26.60-26.77). | face log |
| Captions: Montserrat-like font, white with a thin black outline, selective caps, emoji, low in the frame (79%) | Font, outline and selective caps hold. Position, size, chunking and emoji don't: centred at 24% from the top, cap height about 60 px, 2-3 words every 0.6 s, no emoji, no "...". | section 7 |
| Bass hits in the gaps after punchlines, louder than the voice | Doesn't hold. The two big low hits both fall under words (0.0-0.7, 20.0-20.3), the bed sits about 2 dB under the voice, and the pauses carry only soft stings (14.17, 24.28, 26.12). | section 8 |
| 3.26 words/s; the longest gaps (0.44 s) sit next to punchlines | Faster: 4.09 words/s, with a similar longest gap (0.42 s). Here the gaps cluster in the suspense stretch, after "strange" and "terrified", and the narrator slows to 3.79 words/s there. | section 8 |
| The ending line loops into the first | Holds, in both words and picture: "allowed outside at night" in the first and last sentences, and a red-sky chase at both ends. | sections 2, 9 |
