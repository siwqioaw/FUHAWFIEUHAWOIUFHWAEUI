# What the 16 have in common

The cross-video findings from the per-video notes (`notes/`), measurements (`measurements/`) and transcripts
(`transcripts/`). Claims cite videos by number; *seen*, *measured* and *heard* as in `../NOTES_TEMPLATE.md`. What
needs a listener was answered by the listener pass (`listener/`, summarised and checked in "Sound, as heard").

## The set at a glance

| # | format | views | s | fps | words | words/s | 1st word | raw cuts | real cuts (+ swoops) | a new framing every | LUFS | LRA | TP | beat BPM (conf) | voice dBFS | bed dBFS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 001 | rant | 9.9M | 28.2 | 60 | 90 | 3.26 | 0.0 | 31 | 16 (+2) | 1.6 s | -13.1 | 4.0 | 0.2 | 90.9 (5.1) | -17.8 | -9.7 |
| 002 | comparison | 9.6M | 11.5 | 60 | lyrics | | | 9 | 8 (+1) | 1.2 s | -8.5 | 1.2 | 0.3 | 139.5 (8.5) | | -16.5 |
| 003 | mini-drama | 6.4M | 36.6 | 60 | 153 | 4.21 | 0.0 | 44 | 27 | 1.3 s | -14.3 | 2.2 | 0.8 | 71.4 (4.1) | -17.7 | -19.4 |
| 004 | rant | 6.2M | 25.9 | 60 | 92 | 3.60 | 0.0 | 29 | 11 (+4) | 1.6 s | -12.1 | 3.2 | 0.3 | 80.0 (9.4) | -16.6 | -10.5 |
| 005 | rant | 5.6M | 31.3 | 60 | 95 | 3.06 | 0.0 | 19 | 11 (+2) | 2.2 s | -13.3 | 4.9 | 0.3 | 74.1 (2.5) | -18.3 | -14.6 |
| 006 | in this world | 4.3M | 34.4 | 60 | 159 | 4.66 | 0.0 | 35 | 23 | 1.4 s | -14.1 | 3.4 | -0.1 | 105.3 (3.9) | -18.2 | -10.2 |
| 007 | owned | 4.0M | 23.4 | 60 | 73 | 3.18 | 0.0 | 28 | 13 (+1) | 1.7 s | -12.0 | 2.0 | 0.1 | 88.2 (5.5) | -16.4 | -8.4 |
| 008 | in this town | 3.3M | 99.8 | 60 | 421 | 4.24 | 0.0 | 100 | 81 (+9 jump-ins) | 1.1 s | -14.4 | 3.7 | 0.1 | 96.8 (3.4) | -18.7 | -24.1 |
| 009 | night story | 3.1M | 30.5 | 60 | 124 | 4.09 | 0.0 | 32 | 25 | 1.2 s | -13.8 | 1.5 | -0.3 | 176.5 (3.8) | -17.3 | -19.2 |
| 010 | owned | 2.6M | 20.5 | 60 | 66 | 3.31 | 0.0 | 24 | 12 | 1.6 s | -12.0 | 3.6 | 0.1 | 88.2 (6.8) | -16.6 | -9.3 |
| 011 | in this world | 2.1M | 32.7 | 60 | 141 | 4.34 | 0.0 | 30 | 20 (+3) | 1.4 s | -13.7 | 1.9 | -0.1 | 77.9 (3.9) | -18.2 | |
| 012 | long story | 1.6M | 157.0 | 60 | 637 | 4.06 | 0.0 | 187 | 152 | 1.0 s | -14.0 | 2.4 | 0.1 | 74.1 (3.0) | -17.4 | -21.9 |
| 013 | in this world | 1.3M | 31.9 | 60 | 141 | 4.46 | 0.0 | 38 | 19 (+7) | 1.2 s | -12.9 | 1.7 | -0.4 | 117.6 (2.7) | -16.9 | -16.2 |
| 014 | types list | 1.1M | 11.6 | 30 | lyrics | | | 9 | 5 | 1.9 s | -6.2 | 0.7 | 1.5 | 105.3 (5.6) | | -9.1 |
| 015 | types list | 1.1M | 10.8 | 30 | lyrics | | | 5 | 5 (+1) | 1.5 s | -6.3 | 0.7 | 1.8 | 105.3 (5.8) | | -9.1 |
| 016 | rant | 1.0M | 29.4 | 60 | 84 | 2.94 | 0.0 | 23 | 11 | 2.5 s | -12.3 | 2.6 | 0.0 | 77.9 (4.6) | -15.7 | -18.5 |

Real cuts and swoops are counted by eye on frame strips (each note's section 7). "A new framing every" counts both.
Voice dBFS is the median level while words are said; bed dBFS the median in gaps 0.15 s or more from any word.
The transcripts put every voiced video's first word at 0.00 s; one note (007) measured the second word starting 0.7 s in.

**What the raw numbers get wrong.** `analyze.py` counted 1.3 to 2.5 times the real cuts: snappy poses, fast camera
moves, caption swaps on still shots, outfit strobes, a body passing the lens and smoke puffs all read as cuts. It
also misses camera swoops and, rarely, a hard cut between two shots of the same palette (008). Count by eye.

## The channel in one paragraph

@r6rants makes Roblox skits and stories acted by R6 avatars whose drawn 2D faces change on almost every line, in
bright, detailed sets (a school, a house, a town, woods), animated pose to pose with snaps of 4-6 frames, shot with an
in-engine camera that pushes, swoops and pulls on nearly every shot, captioned in one house font, and mixed hot and
dense. Three families share that look and differ in almost everything else: who talks, how fast, where the captions
sit, what the sound does and how the edit behaves. Over 2026 the channel moved from narrator comedy with emoji titles
(March-April, the four biggest rants) through music-only lists (August-September) to narrated "In this world"
stories with hashtags (September-November). Comedy holds the top view counts; stories are the newest work.

## Three families, eight formats

| Family | Format | Videos | Length | Words (words/s) | Who talks | Captions | Signature |
|---|---|---|---|---|---|---|---|
| A. Narrator comedy | rant: "Why do [group] do this" | 001, 004, 005, 016 | 26-31 s | 84-95 (2.9-3.6) | the recurring narrator, on screen and in the scenes | low (about 77-79%), a clause per caption, CAPS on stressed words, a trailing emoji | the "BRO" opener; three examples or one escalating incident; a retort or punch every 2-8 s; one boom after each punch |
| | owned: "If [type] OWNED Roblox" | 007, 010 | 20-23 s | 66-73 (3.2-3.3) | the narrator, second person ("you log in") | as the rant; in-world notices quoted in lowercase | the rules arrive as notices built in the world; a refrain closes each gag; a rise then a fast fall |
| B. Narrated stories | "In this world / town, [rule]" | 006, 008, 011, 013 | 32-100 s | 141-421 (4.2-4.7) | an off-screen storyteller | high (block about 22-29% from the top), 1-3 words, bigger, no emoji | the rule as title and first line, demonstrated on strangers by 4-6 s; a twist built from the rule at about 85% |
| | mini-drama | 003 | 37 s | 153 (4.2) | storyteller | high, 1-3 words | an odd habit shown in three inserts; plant and reveal; two turns; a letter |
| | night legend | 009, 012 | 31 s, 157 s | 124, 637 (4.1) | storyteller (012 in first person) | high (009) or lower and bigger (012: about 70%, 80 px) | a rule as a warning; fair clues that read the wrong way; light as story state |
| C. Music only | comparison: "X VS Y" | 002 | 11.5 s | none | nobody | a header at the top, the names in colour | three "photos" per side; a music switch at the turn; the second side absurdly outdoes the first |
| | types list: "When [moment]" / "My [group]" | 014, 015 | 11 s | none | nobody | a header and a coloured label per type | four beats per type; "Me:" or a bookend to finish |

## Rules every video follows

1. **The premise is readable in the first second.** Voiced videos speak from frame 1; music videos put a header on
   frame 0. The first spoken line is the premise and usually the title: "Bro, why are popular girls so annoying?"
   (001), "In this town, nobody is allowed outside at night" (009), "In this town, every secret you say out loud turns
   into a gray mouse" (008).
2. **Something moves at once.** A push-in, swoop or snap pose starts within 0.5 s in all 16; the first new framing
   comes by 0.5-1.2 s.
3. **One idea per shot.** A new framing every 1.0-1.4 s in the stories, 1.6-2.5 s in the comedy, 3-4 beats in the
   music formats. Stories cut on the first word of each clause (011: all 20 cuts within 0.09 s of one); comedy cuts on
   new examples and joins action to reaction with a swoop; music formats cut on the downbeat.
4. **Faces do the acting.** Drawn 2D faces, no lip sync. Comedy swaps them mid-shot on the word (about 25 changes in
   001's 28 s); stories give each shot one face chosen for its sentence. Traits are drawn into every face of a
   character (the pet's glasses, 004). Tricks: a two-face flap for shouted lines (008), the head's colour ramped to red
   before the angry face (016), a blank face on a frozen pose (010), a smirk swap that exposes fake crying (016), swaps
   hidden behind a turn or a passing body (007).
5. **Every figure of speech is shown literally:** "basically a ghost", a player walks through him (007); "like a crime
   documentary", a top-down crime scene (005); "throwing hands", the brother flies out of a window (016); "the class is
   completely silent", a tumbleweed (001, again in 007).
6. **Lists of three, escalating:** three examples (001, 004), three photos per parent (002), three types and "Me"
   (014), three clues (009), three popups (007), three inserts (003), three tries with a counter (008: 10, 20, 30 steps).
7. **Plants pay off, and the ending answers the opening.** Every rule in 008 is a setup; 012's password pays off three
   times, flipped each time; 013's catch becomes the twist. Most end on a loop: "Bro, we know" into "Bro, why..."
   (001), the opening hallway (005), the red sky (009), the same tray shot, now happy (015), 012's last shot matching
   its first.
8. **The set rewards rewatching:** meme whiteboards (001, 004), a hidden screaming-face extra in three places (010),
   comment prompts written into the set ("answer in the comments! 6+7=?", 004; "COMMENT IF YOU SEE THIS", 016) and a
   subscribe sign (007, 015).
9. **The sound is dense:** -12 to -14.4 LUFS with a voice, -6 to -8.5 without; loudness range under 5 LU. (We'll match
   the density at -14 LUFS, without their over-full-scale peaks.)

## Family A: narrator comedy

**The opening is a template** (001, 004, 005, 007, 010, 016 all use it):

| Time | Picture | Sound |
|---|---|---|
| 0.0-0.5 | the narrator alone in a wide shot, hands up by his head; caption "BRO"; push-in, arms snap out | "Bro," on frame 1 |
| 0.5-1.1 | a 0.2 s swoop (with white anime speed lines, 001 and 005) or a cut lands on the subject beside him; he points | the premise line; the music may start on this landing (007) |
| 2.0-2.5 | the two-shot holds | the premise ends; a sub-bass boom fills the gap; the next cut lands 0.3-0.7 s into it |

**The body:** three behaviours each closed by a retort to the subject (004), one situation in three acts (rule,
build to a reveal, anticlimax, 005), one incident escalating every 2-3 s (016), or, for "owned", a rule, its
enforcement at a cost, an invasion of your space (010), each closed by the same refrain ("Bro, I just got here!").
A punch lands every 2-8 s. Action and reaction are joined by a 0.05-0.16 s swoop; hard cuts start new examples.

**The ending escalates the narrator:** the roast "Bro, we know" (001), a red-glowing demon behind the pet (004), he
vanishes on "I'm vanishing" (005), the "LOL LOSER" notice (007), the brother thrown out of a window (016).

- **The narrator** is the channel's mascot: brown swept hair, purple round sunglasses (on when he talks to camera, off
  when he acts in a scene, so every reaction face is drawn without them), black jacket over a purple motorbike tee.
  Gen-Z register ("bro", "lil bro", "it's not that serious", "goofy-ah"); short verdict lines ("My phone? Gone.").
- **Pauses are comic beats** (005 has six; 016 up to 0.56 s), and 0.2-0.3 s dead stops come right before reveals (007).
- **The boom:** one sub-bass sample after the punches in 001, 004 and 005 (measured at about 48 Hz in 004/005),
  louder than the voice; the next cut lands inside it.
- **"Owned" notices are props in the world**, not edit graphics: dark panels that rise out of the ground, grow in the
  sky or fly in from a speck in 6 frames, with the camera tilting or whip-panning to meet them (007, 010). Their
  layout (title, rule, one button) echoes Roblox's own kick prompt: ours must be our own design.

## Family B: narrated stories

**The "In this world" template** (006, 008, 011, 013; timings as a share of the length, from 011 and 013):

| Share | Beat | How |
|---|---|---|
| 0-13% | the rule | title and first sentence: "In this world, [rule]", key noun in caps; demonstrated at once on anonymous extras, showing the rule's visual signature (a colour burst, a flash-vision, a fade, a mouse) |
| 13-24% | the price, or dread | the catch stated in the next sentence and shown on an extra (013); the range of bad outcomes in 3.5 s (011) |
| 20-25% | the hero | named (Liam, David, Jake), with the person who matters |
| about 41% | the rule fires on the hero | with the flash |
| 41-68% | a false high | a happy vision, the comic middle (guilt-free targets, 013), or hope and acceptance as a false ending (006) |
| 58-68% | the reversal | opened with "But", right after the happiest beat |
| about 85% | the twist | the rule, or its catch one step deeper, fires on someone unexpected or re-reads a scene already seen; told in one fast sentence; the biggest boom right after |
| last 0.2-0.3 s | the end | the last image is the rule's own visual on the last word (a fade, the colour, the named object); the video stops within 0.3 s of the last word |

For longer stories (008 at 100 s, 012 at 157 s) the same engine repeats: each act answers one question and opens the
next, a big question closes every 15-20 s and a beat lands every 2-4 s, the tone changes every 10-15 s, and a
try-fail ladder with a visible counter breaks into the hero's own vulnerability (008). 003 and 009 run the same
engine with an odd habit or a warning in place of the rule.

- **The storyteller** is off screen, third person (012: second person, then first), a plain storybook register with a
  little slang early to lower the guard (009); continuous at 4.1-4.7 words a second, no pause over about 0.35-0.46 s,
  except one deliberate pause right before the fatal moment (013: 0.40 s).
- **The camera points at whoever is named:** 0.15-0.32 s swoops from the speaker to the person named, landing on the
  naming word (013: 7 of 7); close-ups that pull back to the pose; one held axis with a slow push for a confession,
  the loudest passage (008); jump-ins on the same axis instead of zoom punches (008, 012).
- **The edit carries the rule and the feeling:**
  - a warm white flash of about 0.3 s, red to orange to white, as the sign that the rule fired, with the cut hidden at
    the white peak (011, 013); a hard cut instead of a flash for the final shock (011);
  - grade changes that *are* the rule: grey drains to about 25% of normal saturation in 5-18 frames, and colour bursts
    through 2-3 near-white frames to about twice normal (006);
  - a colour script by place (warm home, grey graveyard, faded flashback, 003) and light as a story state (012: warm
    lantern = trust, blue-black = danger at mean luma 20/255, moonlit violet = truth, foggy lavender dawn = the
    changed, bright day = denial), switched on the word that names it;
  - a red pulse under the heaviest word (003); a red sky for "what people see" (009); spin-blur and blur swoops for
    time jumps (003, 006).
- **Sound:** music in layers that enter at story turns (003); bass thuds on drains and shimmers on bursts (006); bass
  hits in the 0.16-0.26 s breaths between sentences (011); a bed switch at the crisis (008); the bed about 4.5 dB
  under the voice (012); one real-world sound for the twist (three knocks, 003); a 0.1 s dip before the biggest hit
  (009); an end sting.
- **Kid bounds for scary stories** (009, 012): harm implied, never shown (a dropped bat, mud not blood); victims alive;
  each scary image under about 2 s; drawn cartoon faces for the scares; end on a chase or a plea, not a catch; a heart
  under the fear (protecting a little sister, 012).

## Family C: music only

- **Comparison (002):** a header per side ("Mom's old photos.." / "Dad's old photos", the name in colour), three live
  "photo" tableaux per side with a small camera move each, a hard music switch at the turn, the second side absurdly
  outdoing the first, a reaction shot to close. 11.5 s; a shot every 3 beats at 139.5 BPM.
- **Types list (014, 015):** a header for a shared moment, a coloured label per type, each type one shot of exactly
  four beats (about 2.3 s at 105 BPM), and "Me:" as the last type or a bookend that repeats the first shot with a new
  face. About 11 s.
- **The recurring beanie kid** (black "PRO" beanie, blond hair, black jacket, red motorbike tee) is this family's "me",
  as the sunglasses narrator is family A's.

## The look

**Avatars.** R6 bodies throughout. Big, detailed UGC hair; catalog clothes with graphics; one accessory that names the
character (sunglasses, beanie, glasses, a slipper as a threat prop). Skin mostly light beige or tan, sometimes classic
yellow (010's mom, 003's driver). In night stories each hero gets one very saturated hair colour so they read in the
dark (012). Extras are jokes: noob-style characters with red top hats and grins, a screaming-face extra, a cat guest.

**Faces.** Drawn cartoon faces in black line art (anime and meme styles: toothy grins, squeezed-shut laughs, dollar
eyes, pinpoint-pupil screams, troll grins, tears, blushes, "^ ^" eyes, skull grins for scares). About 25 a video in the
comedy, one per shot in the stories. Black line art on light skin reads in any light (009). This is the most
important art asset to build.

**Sets.** A school (hallway with red lockers, classrooms with yellow one-piece desks and whiteboards, a cafeteria),
house interiors (living room, kitchen, bedroom), suburban streets, a town map, woods, a wedding venue, a hospital, a
graveyard, and Roblox's default Baseplate as "inside the game" (007). Realistic detail with clear shapes; small
readable signs (ROOM 102, PRINCIPAL).

**Light.** Bright, even, saturated daylight; warm interiors against cooler hallways; soft shadows, high ambient, low
contrast. Night is a black or coloured sky over characters lit like day (009: skin measured 164 indoors and 170 on the
night street). Stories add grade and light changes as story signals (above).

## Camera grammar (all families)

- **Every shot moves at its start:** a 0.2-0.3 s push-in or pull-back (007's eases out, 006's run steadily and
  stop), then a hold with slight drift (006).
- **Measured frame by frame (spike S4):** the difference between whole frames can't tell the camera from the animation
  in the shot, so track a feature (a face's size, the floor's tiles). 007's pull-back at 3.73 eases out: its first step
  shrinks the face to about 0.71. Its whip-pan at 4.50 speeds up and slows down (the floor slides 2.5, 8, 13, 19, 25,
  33, 44, 60 px a frame, then three frames too fast to track, then 60, 43, 31, 23, 17, 11, 6). 002's swoop that rolls to
  a dutch angle speeds up and slows down over about 0.4 s. 006's pull-backs run steadily, the picture shrinking
  0.93-0.95 a frame for 12-13 frames, then stop. Swoops between framings: 001's at 0.48 is sharp, with speed lines,
  fastest at its end as it lands the two-shot; 004's at 12.80 is sharp; 003's time-jump swoop is blurred.
- **Swoops of 0.05-0.32 s** join framings inside a scene: action to reaction (004), speaker to the person named
  (013), into a two-shot with speed lines (001, 005).
- **ECU, then a fast pull-back** (0.1-0.25 s) to show the situation (007, 011).
- **Low angles at desk height**, over-the-shoulder for "me receiving it", a point of view or a camera behind the hero
  for "you" lines (007), whip-pans to the object named (011, 016), tilt reveals (002), top-down for understanding or a
  crime scene (005, 009), road level for loneliness, dutch tilts on witnesses, tracking back ahead of runners (009).
- **Mirror shots** show change without words: the same place and angle with one difference (003, 006, 011).
- Subjects stay centred, clear of the caption block.

## Animation

- **Pose to pose, snappy:** big poses reached in 4-6 frames at 60 fps, held with drift; anticipation (the head drops,
  then snaps up into a grin, 014). Stock-style cycles for dances, runs and walks.
- **Snaps, frame by frame (spike S3; `sheets.py strip --step 1` over each):**
  - 001, 17.37-17.45: head down to a yell over 5 frames, 4 different pictures (one frame repeats). The head
    leads and the hands land on the last frame.
  - 004, 20.07-20.15: an arm from the desk to straight up over 5 frames, 4 different pictures in steps of
    similar size, the biggest the last, under a push-in.
  - 008, 12.72-12.75: both arms jump to a new pose in one frame, on the caption change, and settle over 2.
  - So most snaps take about 5 frames at 60 fps and the hardest hits 1-2. They don't all ease out, and in 001
    the body moves in overlapping parts, the head first and the hands last.
- **Frame rate:** 14 of the 16 are 60 fps files, and while something moves they show 48-57 different pictures a
  second; the rest repeat the frame before, as a real-time capture that drops frames does. 014 and 015 are 30 fps
  files that change on every frame.
- **Game logic as gags:** spawning as an empty frame and a pop-in (007, 010), a freeze as a blank face on a locked
  mid-stride pose (010), an outfit swap hidden behind a spin and revealed with a glow (007).
- **Effects in the scene:** money rain, hearts, a gold aura with rays, blue square particles (laughing, running), smoke
  puffs, a tumbleweed, a floating "z", 3D notice panels that fly in. (007's outfit strobe at 7.5 a second fails the
  flash check: ours stay under 3.)

## Captions and text

One house font in every video: a geometric sans close to Montserrat Medium or SemiBold, white, a thin black outline
(about 3 px at 1080), no box, cut in hard.

| Family | Where (block centre) | Size (cap height at 1080 wide) | Length | Case | Emoji |
|---|---|---|---|---|---|
| A. comedy | about 77-79% from the top | 42-45 px (about 4% of the width) | a clause, 1-3 lines, up to about 800 px wide | sentence case, stressed words in CAPS; "..." on setups; quotes for dialogue; notices in lowercase quotes | one trailing emoji on most lines (🥀 most, then 😭 🙏 💀 ☠️ ✨) |
| B. stories | about 22-29% from the top (012: about 70%) | about 1.5-1.7x larger (012: about 80 px) | 1-3 words (008 up to 6), a new one every 0.6 s | lowercase with caps on the loud words; caps grow with the stakes (013) | none (one in all of 003) |
| C. music | header about 12% from the top, labels under it | about 70 px | a header plus a 1-4 word label | header in caps or title case; labels in a colour per type | none |

Captions change on the cut or lead it by 1-2 frames.

## Packaging

| Period | Titles | Examples |
|---|---|---|
| March-April | a question or "If ... OWNED Roblox", a key word in caps, 😭🙏 or 💀🙏, no hashtags | "Why Do POPULAR Girls Do This!?😭🙏", "If A Gold Digger OWNED Roblox😭🙏" |
| August-September | plain, the header as the title | "Mom VS Dad", "When The Bell Rings #roblox #entertainment #rblx" |
| September-November | the rule as the title, the key noun in caps, the three hashtags | "In This World, People Can't See Colors Until They Touch Their SOULMATE #roblox #entertainment #rblx", "The Lantern 🎃" |

## What we won't copy, even as style

- **Their characters and catchphrases:** the sunglasses narrator, the beanie kid, the "BRO" opener as staged, their
  scripts and jokes (each note's section 11 lists them). We build our own recurring cast and our own opener.
- **Things that are someone else's:** photos of real people as posters and billboards (003, 005, 007, 015); other
  companies' characters (a hedgehog-like runner in 014, c00lkidd and a Miku-style avatar in 004); brand logos (a
  pizza chain from a Roblox game, an "M" fries box, the ROBLOX logo on a tee, "R$" on banknotes, a "BLOXY" can).
- **Anything close to Roblox's own interface:** the notice panels' title, rule and OK-button layout echoes Roblox's
  kick prompt (007, 010); ours get their own shape, colour and font.
- **Their mastering:** true peaks over 0 dBTP and the music formats at -6 LUFS. We deliver -14 LUFS with the repo's
  true-peak ceiling.
- **Flashes over the WCAG limit** (007's strobe).

## Sound, as heard (the listener pass)

A model that can hear answered each note's open questions (`listener/NNN.json`, one per video, filed 2026-11-07 from
`docs/prompts/listener-pass.md`). Its answers about *what* a sound is are leads we can't get any other way; its exact
times are approximate, and it is sometimes wrong. What could be measured was checked:

| Claim | Check (pitch by YIN on the mid channel, 16 kHz; speech rates from `transcripts/`) | Result |
|---|---|---|
| Girls' lines are a different, higher voice (001, 004) | median pitch 320 Hz on the girls' lines against 196-208 Hz (001) and 195-291 Hz (004) for the narrator | confirmed |
| A deep voice delivers one-word punches (016 "GONE", "You mad?") | 79 Hz and 123 Hz against the narrator's 174-211 Hz | confirmed for 016 |
| The same deep voice says 001's "BRAD IS ASLEEP" | 198 Hz: the narrator's own pitch | not confirmed (001's other "deep" lines sit under booms and can't be measured) |
| The stories slow the voice to normal speed for the twist (011, 013) | after the twist point 5.2 words/s against 4.2 before (011), 6.1 against 4.3 (013) | contradicted: the twist line is faster |
| Songs: 002 is "Bang Bang Bang" (BBpanzu feat. Starxrayne & JamsDX); 014 and 015 are "Come On!" (Kyle Exum) | the lyrics in our transcripts; 139.5 and 105.3 BPM measured; 014 and 015 already looked like one track | consistent |
| The punch boom sits at about 50 Hz | 48 Hz measured on 004 and 005 | consistent |
| Comedy music enters about 0.7 s in and is muted for gags | the stereo side channel (L-R) | can't tell: stereo effects and reverb fill the side channel |

**Voices.**
- **Comedy** is voiced by a small cast of text-to-speech voices, not one narrator:
  - an energetic young male narrator, sped up about 1.1-1.15x with the breaths cut;
  - a higher teen girl's voice for girls' lines (about 320 Hz);
  - at least in 016, a deep, slowed voice for one-word punches ("GONE", "You mad?").

  The listener names them as stock voices of one TTS service (the deep one "Adam"): a plausible lead, not verified.
  Voices switch mid-sentence for a punch; quoted characters often keep the narrator's voice.
- **Stories:** one storyteller voice reads everything, characters' lines included, at about 1.2x with every breath
  removed (006, 009, 011, 013 have no silence at all). 008's narrator sounds like an expressive performance (the voice
  cracks on the confession); 012 uses one teen-boy voice for every character, told apart only by delivery.

**Music.**
- **Comedy:** one stock comedy loop (pizzicato strings, marimba, light percussion, about 104 BPM) under 001, 004, 007,
  010 and 016 (005: a similar loop at about 100). It is silent under "BRO" and enters around 0.7-0.9 s. Then it's
  switched on purpose:
  - killed for the silent-class gag, leaving crickets (001, about 21.7 s);
  - muted for the four-part name (005, about 6-13 s);
  - swapped for a horror drone at the dark ending (004);
  - interrupted by a boss-fight choir for the brother's entrance (016).
- **Stories:** one bed per video under continuous narration:
  - a wistful synthwave loop at about 130 BPM, shared by 006 and 013;
  - dark synthwave at about 92 (011);
  - a slowed, detuned A-minor horror pad at about 88, shared by 009 and 012;
  - lo-fi guitar and pads at about 98 (003);
  - in 008, a new score per act: pizzicato, then minor piano with wind, then warm major strings.

  A genre switch can itself be the punchline: 006 drops into an R&B slow jam on "instantly" as the best friend
  touches him.
- **Music formats:** commercial songs, cut to their bars: 002 cuts on the "bang"s of the chorus drop; 014 and 015 cut
  each type on the downbeat after "Now, come on!". (We won't use commercial songs: see the plan's music rules.)

**Effects.**

| Family | The palette |
|---|---|
| A. comedy | a sub-bass "vine boom" after nearly every punch (4-6 a video); a cash-register cha-ching for money; an achievement ding and an error tone for in-world notices; pops and whooshes on cuts; giggles, snores, crickets, a glass smash, a door creak, a crowd "oooh", meme voice clips, a scream cut off mid-peak |
| B. stories | a sound for each state of the rule (sparkle chimes on colour bursts and dull thuds on drains, 006; shimmer whooshes on visions, 011); heartbreak "crack" stings on the emotional peaks (003); a doorbell, then unanswered knocks (003); footsteps, crying, a door slam, a roar (009); cha-chings as a reward that turns tragic (013); and 012 uses none at all |
| C. music | none added: the song carries it (014 adds a school bell) |

**Mix and endings.**
- The voice sits 12-15 dB over the bed in every voiced video. Comedy carries 37-50% of its energy under 80 Hz (the
  booms); stories carry 55-84% in the speech band.
- Endings are hard by design: a cut mid-boom (001, 010), mid-scream (004), or mid-word ("emergency bu—", 011;
  "taught—", 013), so the viewer finishes it on the replay.

**Still open:** the stock loops' titles; which TTS service and voices, for certain; exact music on and off times.

## Targets for the skill

| | Family A comedy | Family B story | Family C music |
|---|---|---|---|
| Length | 20-31 s | 30-36 s (longer only for a big story) | 10-12 s |
| Words | 65-95 at 2.9-3.6 a second, pauses as beats | 140-160 at 4.2-4.7 a second, no pauses but one | none |
| First word / text | frame 1 | frame 1 | the header on frame 0 |
| New framing | every 1.6-2.5 s | every 1.0-1.4 s | every 3-4 beats |
| Faces | a change on nearly every line, mid-shot | one per shot, for its sentence | one or two per character |
| Captions | low, a clause, CAPS, one emoji | high, 1-3 words, no emoji | header and coloured labels |
| Voices | a cast of 3 TTS voices: narrator, a girl, a deep punch voice; sped up 1.1-1.15x, breaths cut | one storyteller voice for everyone, about 1.2x, no silence | none |
| Sound | a stock comedy loop at about 104 BPM, silent under the opener and switched off for gags; a sub-bass boom after each punch; literal effects for every action | one bed per video (synthwave, a horror pad, lo-fi), a new layer or score at turns; a sound for each state of the rule; stings on emotional peaks | one track, cut on its bars and drops |
| Ending | the narrator escalates; loop into the opener | the rule's visual on the last word; stop within 0.3 s | a reaction or "Me:"; loop |
| Loudness | -14 LUFS integrated, LRA under 5 LU, true peak under the repo's ceiling | same | same |
