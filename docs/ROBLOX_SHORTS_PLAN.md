# Plan: Roblox Shorts from one prompt

The goal, in the owner's words: give the agent one concept and get back a finished Short, with the agent in charge of
writing, building, animating, camera, editing and sound. The study set is 16 Shorts from @r6rants that passed a
million views (`refs/r6rants/`). This page is the plan for getting there; the reference findings are in
`refs/r6rants/SYNTHESIS.md`.

## Done looks like

The owner types `/roblox-shorts <concept>` (for example *"In this world, your pet narrates your life out loud"*).
Without further input the agent hands back:

- `out/<slug>.mp4`: 1080 x 1920, every check in `docs/VERIFY.md` passing on the delivered file;
- `videos/<slug>/`: the brief, script, beat sheet, cast, shot list, timeline, edit and mix code, stills, review;
- a title, description and hashtags to paste;
- the independent reviewer's report, and what was fixed.

Uploading stays the owner's job, every time.

**The quality bar** is the reference set, measured: hook inside the first second, a real cut or camera swoop every
1.0-1.6 s, a face change on almost every line, captions to the measured spec, loudness within 1 LU of -14 LUFS with a
low loudness range, and a loop ending. Then an independent reviewer, then the owner.

## What the references say, in short

`refs/r6rants/SYNTHESIS.md` has the detail. The 16 videos fall into three families that share one look and differ in
almost everything else, so the skill needs a playbook for each:

| Family | Formats | Length | What makes it |
|---|---|---|---|
| A. Narrator comedy | "Why do [group] do this" rants, "If [type] OWNED Roblox" | 20-31 s | an on-screen narrator from frame 1; three examples or one escalating incident; a punch every 2-8 s with a bass boom after it; faces swapped mid-shot on the word; low captions with CAPS and an emoji |
| B. Narrated stories | "In this world, [rule]", mini-dramas, night legends | 30-36 s (up to 157 s) | the rule as title and first line, shown on strangers by 4-6 s; a false high, "But", a twist from the rule at about 85%; continuous narration at 4.2-4.7 words a second; one face per shot; 1-3 word captions high in frame; flashes, grade and light changes carrying the rule |
| C. Music only | "X VS Y" comparisons, "types of" lists | about 11 s | a header from frame 0; three items per side or four beats per type; cut on the beat; a reaction or "Me:" to close |

Shared by all: drawn 2D faces on R6 avatars that change on almost every line (no lip sync), snappy pose-to-pose
animation, an in-engine camera that moves at the start of nearly every shot, every figure of speech shown literally,
lists of three, plants that pay off, endings that loop, gags and comment prompts in the set, one caption font, and a
dense, loud mix.

The listener pass adds the sound: comedy is voiced by a small TTS cast (an energetic narrator, a higher girl's voice,
a deep voice for one-word punches), sped up 1.1-1.15x with the breaths cut, over one stock comedy loop that is switched
off for gags, with a sub-bass boom after each punch. Stories use one storyteller voice at about 1.2x with no silence
at all, over one bed per video, with a sound for each state of the rule (`refs/r6rants/SYNTHESIS.md`, "Sound, as
heard").

## What the research changes

`docs/research/roblox-shorts-landscape.md` (the deep-research report, 2026-11-06) covers the whole channel and the
rules around it. What it changes here:

- **Which formats to make first.** Across all 51 of the channel's Shorts, the hit rate follows how universal the
  subject is: "If X OWNED Roblox" 2 of 2 at 1M or more, "Why do X do this" rants 4 of 8, "In this world" stories 4 of
  9, emotional stories 1 of 4, relationship drama 0 of 5. The rants were dropped after April despite that; the
  narrated stories now run 30-157 s and still spread (157 s reached 2.1M in two days).
- **Premise tests for stories.** Can the rule be shown on screen in 2 s? Does its benefit become its cost? Is there one
  loophole for commenters to argue about? Rules that need explaining flop ("a photo of your wife appears in your
  pocket", 83K).
- **What viewers do in the comments,** and what to write for it: they quote a 2-4 word punchline ("BRO, WE KNOW",
  2.1K likes), hunt background Easter eggs (the "67 kid"), rewrite the joke, ask for part 2, and argue about the
  premise. They complained about an end tag. So: one quotable line and one hidden detail per Short; no end tags.
- **How the channel itself is made:** the creator writes and supplies the voiceover, and freelancers animate 35-50 s
  pieces in Moon Animator after an unpaid 15-20 s test. Our pipeline automates the freelancer's job; the script and
  the voice stay the core.
- **YouTube's money rules bite on music.** A Short over 60 s with any Content ID claim is blocked worldwide; one
  licensed track halves a Short's share of the Shorts revenue pool; AI music that is the focus of a video must be
  disclosed. So no commercial songs, and no AI music for the music-only formats.
- **"Inauthentic content"** (YouTube Partner Program) names "templated storylines" and "characters put in the same
  situation over and over again with the same outcome". Automating the mechanics is fine; the premise, cast, set and
  outcome must vary, and the production records should be kept (each `videos/<slug>/` folder is that record).
- **AI disclosure:** fully animated videos and stock AI narration are exempt; cloning a real person's voice is not.
- **Faces:** Roblox moved all classic faces to Dynamic Heads in 2026 (R6 itself stays). Face packs carry their own,
  often restrictive, licences. Our own drawn set is safer and becomes a brand asset.
- **Roblox's name and look:** no logo anywhere; "Roblox" only as a descriptive word; a "not affiliated with Roblox"
  line; no merchandise with R6 characters (Roblox's current terms need a licence for "commercial content" with its
  classic avatars; its 2022 creator guidance allows ad-funded YouTube videos).
- **Made for kids:** animated characters are one of the FTC's factors, and "made for kids" switches comments off,
  which this niche lives on. The audience is mostly teens. Writing for teens and setting the channel deliberately is
  the owner's legal call.
- **Capture:** Roblox's own capture guide gives Editor Quality 21 and **Test > Device** for a custom viewport size,
  which is spike S1's option (b); OBS at 60 fps and 20 Mbps or more is the fallback for real-time capture.

## The pipeline

Every stage writes files the next one reads, so any stage can be rerun alone (the repo's existing rule).

| # | Stage | Role | Writes | Built on |
|---|---|---|---|---|
| 0 | Pick the format | showrunner | `brief.md` | format playbooks (`skill/roblox-shorts/formats/`) |
| 1 | Write | copywriter | `script.md`: lines, speakers, on-screen text, title | writing playbooks, rubric, originality check |
| 2 | Direct | director | `beats.md`, `shots.json`: every shot's set, cast, faces, poses, camera move, length | camera grammar, set and cast libraries |
| 3 | Voice | voice director | `voice/*.wav`, `words.json` | the chosen voice tool; `tools/verify/transcribe.py` for word times |
| 4 | Time | editor | `cut.json`: every shot, line, caption, face change and hit in frames | `tools/verify/timeline.py` |
| 5 | Build and dress | set builder | the shot's set in the backlot place, lights | backlot place, lighting presets, Studio MCP |
| 6 | Stage and animate | animator | per-frame state: actors' poses and faces, props | R6 pose library, easing, `tools/roblox/harness.luau` |
| 7 | Shoot | camera | `build/shots/<shot>/f00000.png ...` | `tools/roblox/capture.py` (posed frames) |
| 8 | Cut | editor | `build/master.mov` | `frame_at(r)`, `tools/edit/typeset.py` captions, `render.py` |
| 9 | Mix and master | sound | `build/mix.wav` | `tools/edit/cues.py`, `master.py`; licensed music and effects |
| 10 | Deliver and verify | QC | `out/<slug>.mp4`, `build/verify/` | `deliver.py`, `qc.py`, `audio.py`, `sheets.py`, a style check against the references |
| 11 | Review | independent agent, then owner | `review.md` | the checklist in `docs/VERIFY.md`, grown with every failure |
| 12 | Package | showrunner | `package.md`: title, description, hashtags | title formulas from the set |

## Decisions, and why

1. **Shoot posed frames, not a screen recording.** The kit already captures one exact frame at a time through
   Studio's MCP server: exact camera moves, no dropped frames, unattended, about 1 s a frame. A 30 s Short is 15 min
   at 30 fps or 30 min at 60. A screen recording is faster but drops frames, needs the window visible and big, and
   can't be checked frame by frame.
2. **Our own R6 animation, as data.** An R6 body has six joints. A pose is six rotations and a root offset; an
   animation is poses on frames with easing. The harness applies the frame's pose each frame, so nothing needs
   uploading as an animation asset, and the snappy pose-to-pose style of the references (big poses reached in 4-6
   frames at 60 fps, then held with a little drift) is easy to write and to check.
3. **Faces are textures, swapped on the word.** The references never lip-sync: a face changes on almost every line.
   A face library (about 30 expressions) is the single most important art asset in the project.
4. **A backlot.** One Studio place with standing sets (classroom, hallway, bedroom, living room, kitchen, street by
   day and night, ...), each with named camera and actor marks and a lighting preset. Most references reuse a few
   locations; building each set once well is what makes one-prompt videos possible.
5. **Captions and graphics in Python**, on top of the captured frames (`typeset.py`): tracked overlays over 3D
   footage are banned by `docs/LESSONS.md`, but captions and headers track nothing.
6. **Everything source in git, no media.** Scripts, timelines, libraries (JSON and Luau), notes, measurements and
   licences are committed; frames, renders and the reference videos are not.

## Phase 1: spikes for the riskiest unknowns

Each spike has a test it must pass. None depends on the others except S7.

| Spike | Question | Passes when |
|---|---|---|
| S1 Portrait capture | How to get 1080 x 1920 out of Studio on a 1920 x 1080 monitor? Try (a) rolling the camera 90 degrees and turning the landscape capture upright, (b) Studio's device emulator in portrait, (c) a portrait or virtual display. | a frame at least 1000 px wide of real pixels, no UI, under 1.5 s a frame. **Passed 2026-11-07 with (a)**, one number short: 960 x 1707 real pixels (sharp after the 1.125x scale), no UI, 0.94 s a frame; Studio needs its own uncovered screen and the capture layout (`docs/ROBLOX_CAPTURE.md`, "Resolution") |
| S2 R6 actors | Can `stage.py` make R6 actors with catalog hair, clothes and accessories, and swap a face texture per frame? | a still of two dressed R6 actors, each face changed between two frames. **Passed 2026-11-07:** two dressed R6 actors, every face changed between two frames, faces drawn here and rendered from Studio's content folder (no upload). Newer hair doesn't fit R6: the cast library needs hair checked on R6 (`stage.py` flags misfits) |
| S3 Snappy animation | Can the harness pose R6 joints per frame with ease-out snaps and held drift, plus a walk cycle? | frame strips that match the reference strips' timing (4-6 frame snaps). **Passed 2026-11-07:** `pose.py` poses R6 from Python: snaps of 5 frames at 60 fps, as long as most of the references' (which also hit in 1-2 frames, and don't all ease out: 001 moves the head before the hands, 004's biggest step is its last); held poses drift; leans and a heel-to-toe walk keep the planted soles still and on the floor, checked against Roblox's own positions to 0.00001 studs; no pose at rest puts an arm through the head (some snaps between poses still clip, and are measured); a new scene needs up to about 45 s to settle before a take (`docs/ROBLOX_CAPTURE.md`, "Posing R6") |
| S4 Camera grammar | Push-in, 0.15 s swoop, dutch roll, desk-height low angle, over-the-shoulder with depth of field. | a strip of each move |
| S5 Voice | Which voice tool, which voices? Three lines in two voices. | owner approves by ear; word times from `transcribe.py` |
| S6 Captions | Reproduce the caption and header spec. | side by side with a reference frame at full size, no visible difference in style |
| S7 End to end | Two shots, one line, two face changes, captions, a hit, mastered. | `qc.py` and `audio.py` pass on the delivered file |

## Phase 2: libraries

| Library | First version | Notes |
|---|---|---|
| Backlot sets | school hallway, classroom, living room, bedroom, suburban street (day, night) | marks for actors and cameras; lighting preset per set |
| Lighting presets | day interior, day exterior, golden hour, night exterior (black sky, faces lit like day), eerie, and story states (warm trust, blue-black danger, foggy dawn) | measured against reference frames: `refs/r6rants/notes/012-the-lantern.md` section 4 has numbers |
| Cast archetypes | narrator kid, popular girl, mom, dad, little brother, teacher, teacher's pet, rich kid, extras | each a HumanoidDescription spec: body colours, catalog hair, clothes, accessories, default face |
| Faces | about 40 drawn faces in black line art: smug, grin, laugh, cry, shocked, side-eye, yell, pout, blank, sleepy, love, scared, confused, derp, cute, evil grin, disgust, sad smile, dollar eyes, scheming, skull grin ...; open and closed pairs for shouting flaps; per-character variants that keep a trait (glasses) | the most important art asset; source is an owner decision (below) |
| Recurring cast | our own narrator and our own "me" kid, as the channel has its sunglasses narrator and beanie kid | a recurring cast builds a channel; never their designs |
| Notice panels | our own in-world panel design (shape, colour, font, icon) for "owned"-style rules | not Roblox's kick-prompt layout |
| Poses | about 40 R6 poses, walk and run cycles, gestures | point, shrug, facepalm, hands on head, arms crossed, hands on hips, laugh lean, cry, sit variants, sleep on desk, cute pose ... |
| Camera moves | about 12 parametric moves | push, pull, swoop, whip, orbit, tilt reveal, dutch, handheld drift |
| Effects and props | particle bursts (laugh, hearts, tears, anger), tumbleweed, floating "z" | in the scene, captured with the shot |
| Voices | a cast per family: comedy narrator, a teen girl, a deep punch voice; one storyteller for stories; delivered at 1.1-1.2x with the breaths cut | a paid plan with a commercial licence; never a clone of a real person |
| Sound effects | tagged by job: a sub-bass boom for punches, a cha-ching, a notice ding and an error tone, pops and whooshes for cuts, a shimmer and a dull thud for a rule's two states, a heartbreak sting, footsteps, doors, crickets | made in Python where it's simple (the boom, whooshes, pops, dings), otherwise CC0 or a paid library; no ripped meme clips |
| Music beds | comedy: a bouncy pizzicato and marimba loop around 100-104 BPM; stories: synthwave, lo-fi, a dark pad, one per mood; music formats: a track with clear bars and a drop | YouTube Audio Library or a library with channel safelisting; no commercial songs; every file in `ATTRIBUTION.md` |
| Captions | three measured styles as `typeset.py` styles: comedy (low, a clause, CAPS, an emoji), story (high, 1-3 words), music (header and coloured labels) | an open-licence font close to Montserrat (Montserrat itself is SIL OFL); emoji from an open emoji set, not Apple's |
| Edit effects | warm white flash with the cut at its peak, grade drain and burst, red word pulse, speed lines on swoops, blur swoop for time jumps | `tools/edit/fx.py` and `look.py`; every flash checked by `qc.py` |

## Phase 3: the writing system

- **Format playbooks**, one per format in the set: rant, "If X owned Roblox" parody, "In this world" story,
  mini-drama, night legend, comparison, types list. Each: when to use it, a structure with timings (the beat tables
  in `SYNTHESIS.md` are the first drafts), a word budget (comedy 2.9-3.6 words a second, stories 4.2-4.7), beat and
  punch rhythm, face-change density, framing rate, caption style, sound plan, an original example skeleton, and a
  scoring rubric.
- **Concept to format:** the agent picks the format from the concept, or the owner names it.
- **Every script carries** one quotable 2-4 word punchline, one hidden detail in the set, a loop or a hard cut at the
  end, and no end tag; a story premise must pass the three premise tests (above).
- **Originality check:** compare the script against every reference transcript; no shared jokes, premises or lines.
- **Variety ledger:** every made video's premise, format, cast, sets and outcome go in one table; a new script that
  repeats an earlier outcome with the same cast in the same situation is rewritten before anything is built.

## Phase 4: the skill

- The skill's source in this repo, `skill/roblox-shorts/` (`SKILL.md`, the playbooks, the libraries), installed by a
  copy script into `~/.claude/skills`, `~/.agents/skills` and `~/.codex/skills`, as the owner's other skills are.
  It runs the repo's tools, so it works from this checkout.
- One folder per video, `videos/<slug>/`, and `make.py` to run every stage after writing, stopping at the first FAIL.
- Two modes: one-shot (the default: run to the end, then hand back) and checkpoint (show stills before the shoot).

## Milestones

| | Milestone | Done when |
|---|---|---|
| M0 | Reference study | done 2026-11-07: 16 notes, `SYNTHESIS.md`, the listener pass (checked) and the research report filed |
| M1 | Spikes | S1-S7 pass; a 6-second test file |
| M2 | First Short: a comparison montage | no voice, about 11 s: proves sets, cast, faces, poses, camera, capture, music, header text |
| M3 | A rant | voice, captions and acting, 25-30 s |
| M4 | An "In this world" story | 30-35 s, a twist, an emotional beat |
| M5 | One prompt to file | the skill runs alone end to end; time per video measured |
| M6 | Scale | more sets and archetypes; the owner's channel analytics feed back into the playbooks |

## Owner decisions

**Decided on 2026-11-07,** each as the research recommended:

1. **Voice: ElevenLabs, on a paid plan** (paid plans carry a commercial licence; free-tier audio never does), for a
   small cast of stock voices. The owner subscribes and keeps the API key in an environment variable set in their own
   terminal; the agent never sees it. Never a clone of a real person's voice.
2. **Audience: teens, not made for kids.** The content rules are in `CLAUDE.md` ("Audience, safety and privacy");
   `docs/KIDS_SHORTS.md` defers to them. The owner sets the channel's "made for kids" setting.
3. **Faces: our own drawn set** (classic faces have moved to Dynamic Heads, and face packs restrict use). Spike S2
   found that captures need no upload: Studio renders them from its own content folder (`tools/roblox/faces.py`).
   Uploading stays optional, for faces that must show outside this machine.
4. **Assets: free Toolbox models and catalog items**, each checked for scripts before use and logged in
   `ATTRIBUTION.md`; music from YouTube's Audio Library.

**Decided later that day: capture at Studio's highest rendering quality.** At Automatic a new scene kept refining for up
to about 45 s and could drop quality mid-take; the harness now sets the highest level for each playtest and puts the
setting back afterwards. Frames look the same and take about 13% longer (`docs/ROBLOX_CAPTURE.md`, "Studio's gotchas").

**Still open** (none blocks the spikes):

5. **Frame rate:** 60 fps like most of the set, or 30 like 014 and 015? Measured: 0.94 s a captured frame, so a 35 s
   story takes about 16 minutes to shoot at 30 fps and 33 at 60; with two posed actors at the highest quality (about
   1.5 s a frame) about 26 and 51. The 14 files at 60 fps really move at 60 (48-57 different pictures a second while
   something moves), and a snap lasts about 5 frames at 60, 2-3 at 30.
6. ~~**Portrait capture:** if the camera-roll trick fails, a rotated monitor or a virtual display?~~ Not needed: the
   roll works (S1). Studio needs the left monitor to itself while it shoots.
7. **Where it lives:** keep building on the `roblox-shorts-skill` branch of `vid-editing` and merge, or split into a
   new repository later?
8. **The channel's main model:** narrated comedy and stories in English, or wordless music gags that travel across
   languages, or both? [Both families can come from one pipeline; the first milestones prove both.]

## Risks

- **YouTube's "inauthentic content" rule** (formerly "repetitious content") demonetises mass-produced, templated
  videos, naming "templated storylines" and the same situation with the same outcome. In January 2026 YouTube removed
  16 such channels with 4.7B views between them. Every video must be a genuinely new story with real craft, not a
  template with words swapped: the variety ledger enforces it.
- **Music and Content ID:** any claim blocks a Short over 60 s worldwide, and licensed music cuts the revenue share.
- **Copying:** never reuse the references' scripts, jokes, characters or music (`refs/r6rants/README.md`).
- **Roblox's brand:** nothing that looks like official Roblox content or interface, which matters most for the
  "If X owned Roblox" format.
- **Licences:** faces, hair and clothing items, fonts, emoji, music and effects each need one (`ATTRIBUTION.md`).
- **Kids:** whether a video is "made for kids" is the owner's call; real people's names, avatars or voices only with
  permission.
- **Technical:** shoot time, portrait resolution, Studio stability over long sessions, and stiff animation (one of
  the trailer's rejections).

## Where the knowledge lives

- `refs/<set>/`: notes, transcripts, measurements and listener reports for each reference set.
- `docs/`: method and rules; `docs/prompts/`: the listener-pass and deep-research prompts; `docs/research/`: reports.
- `skill/roblox-shorts/`: the skill, its playbooks and libraries, once Phase 2 starts.
- Git history on the `roblox-shorts-skill` branch, pushed to the private GitHub repository.
