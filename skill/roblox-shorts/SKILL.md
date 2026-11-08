---
name: roblox-shorts
description: Makes a finished vertical Roblox animated Short (1080x1920 MP4, every check passing) from one concept line, in the style of the r6rants study set: it picks the format, writes the script, casts and builds the set in Roblox Studio, animates R6 actors with drawn faces, shoots the camera moves, voices the lines through the ElevenLabs connector, captions, mixes, masters and verifies. Use when asked to make, write, script, plan or produce a Roblox Short, Reel or TikTok, an "In this world" story, a "Why do X do this" rant, an "If X owned Roblox" parody, an "X VS Y" comparison or a "types of" list, or to come up with concepts for one.
---

# Roblox Shorts from one prompt

`/roblox-shorts <concept>` hands back `out/<slug>.mp4` and its record in `videos/<slug>/`. Work in the vid-editing
repository (its path is in `REPO.txt` beside this file); read its `CLAUDE.md` first: its rules bind every run.

**Never ask the owner anything mid-run unless a rule below makes you.** Make the calls a director would, record them
in `videos/<slug>/notes.md`, and hand back finished files. Publishing is always the owner's job: never upload, post,
schedule or change a channel setting.

## The run

| # | Step | Do | Writes | Guide |
|---|---|---|---|---|
| 0 | Concept | If the prompt is a topic, not a premise, generate 10 concepts, score them, take the best. Pick the format. | `notes.md`: the 10, the scores, the pick | `writing/concepts.md`, `formats/` |
| 1 | Script | Write it to the format's beat table and word budget: a hook in the first second, one quotable 2-4 word line, punches every 2-8 s (comedy) or a twist at about 85% (stories), a hidden detail in the set, a loop ending. Check originality against `refs/r6rants/transcripts/`. | `notes.md` | `writing/craft.md` |
| 2 | Direct | Choose the set(s), cast, and every shot: actors, poses and faces keyed to words, a camera move per shot, effects. Write `direct.py` with `tools/shots.py`. | `videos/<slug>/direct.py`, `lines.json` | `library.md`, `formats/` |
| 3 | Voice | Generate each line with the ElevenLabs connector (one flow per video, 2 takes for lines that carry a joke), fetch the takes, `make.py voice`. Fix any FAIL by regenerating that line (a word heard wrong on the raw take too is the read, not the processing: reword it if a sound at the line's start is weak). | `build/<slug>/takes.json`; the voice report | `docs/VOICE.md` |
| 4 | Plan | `python videos/<slug>/direct.py`, then `python tools/make.py plan videos/<slug>`. Read the shot times (a new framing every 1.0-2.5 s), the captions as they'll break, and every warning: someone never in frame, a face under the captions (or a story's hair), cut by an edge at the shot's start, middle or end, or under the Shorts UI, a gesture whose hand leaves the frame, a jump cut, an icon over a subject hidden behind someone, two actors' arms or bodies inside each other, an actor inside furniture or a pet, or a walk through someone (staging), a camera inside a prop or outside the room. Fix each before the stills (a warning on purpose, like a high five's contact, can stay). It fails a caption up too briefly to read. | `plan.json`, `cut.json` | `docs/MAKING.md` |
| 5 | Stills | `make.py stills` (`--only` for a few; `--frames 0 -1` for each shot's first and last frames, where a move starts and ends): look at every still at full size, with a caption drawn over it in the video's style. Fix staging (someone hidden or out of the narrow frame, a face cut off or under the captions, a frame of one flat colour: the camera inside a wall, a logo on a costume, a prop filling the foreground, a gesture that doesn't read, set writing under the captions, each line's action not in the picture) before the shoot. The checks can't see a prop between the camera and the subject, or a head behind a head: only the stills show those. | `build/<slug>/stills/` | `checklist.md` |
| 6 | Shoot | `make.py shoot` (runs in the background; resumes on failure; shoots again only the shots whose plan changed since, so restage in `direct.py`, plan with `--keep-shots --replan <shots>`, and shoot). Needs Studio open in the capture layout and `python tools/roblox/studio_mcp.py serve`. | frames | `docs/ROBLOX_CAPTURE.md` |
| 7 | Cut, mix, deliver | `make.py cut`, `mix`, `deliver`: every check on the delivered file must pass. | `out/<slug>.mp4`, `build/<slug>/verify/` | `docs/VERIFY.md` |
| 8 | Review | A fresh reviewer agent gets the file, the timeline and `checklist.md` (not your opinion of it), briefed from `review_brief.md`. Fix what it finds (`plan --keep-shots --replan <shots>` restages shots without moving the rest); add any new kind of failure to the checklist. | `videos/<slug>/review.md` | `review_brief.md`, `checklist.md` |
| 9 | Package | Title, description, hashtags (`writing/packaging.md`); credits for every licensed asset in `ATTRIBUTION.md`. | `videos/<slug>/package.md` | |

Times measured on the first videos (M5's in `videos/pet-narrator/notes.md`): voice processing 2-4 min (the
transcriber on the CPU; seconds when cached), stills 8 min for 20 shots, the shoot 1.4-1.8 s a frame at 60 fps (a
30 s story about 53 min; music formats at 30 fps, half), cut, mix and deliver 5 min, a review 25 min: about two and a
half hours from the prompt to a reviewed file. Load the transcriber (3 GB) only while Studio isn't shooting, and
expect a shoot to slow to 2-3 s a frame while reviewers or renders share the CPU.

## The house rules (from the owner, all binding)

- **Teens, not kids.** Roast types (the popular girl, the little brother), never real people. Spooky but safe: harm
  implied, never shown, no gore, any scary image under about 2 s. Nothing graphic, sexual or hateful, nothing that
  encourages unsafe behaviour. No kid-coded words in titles. No child's personal information anywhere.
- **Original.** Never reuse the references' footage, music, characters, catchphrases (the "BRO" opener, the sunglasses
  narrator, the beanie kid) or jokes. Our narrator has blue hair and black glasses (`tools/roblox/cast.json`). No
  Roblox logo anywhere, clothes included (an item named "ROBLOX ..." usually carries one).
- **Licensed.** Every sound, track, font, image and catalog item has a licence and a line in `ATTRIBUTION.md`.
  Voices only from ElevenLabs on the owner's paid plan; never a clone of a real person. Music: YouTube Audio Library,
  or ElevenLabs music for a voiced video's bed (not for a music-only video, where the music is the focus).
- **Secrets.** Never ask for, see, type, log or commit a key, a password or a token. Signed download links stay in
  `build/` (ignored by git) and never in a file you commit or a message.
- **Studio.** A playtest plays as the owner's account; everything the pipeline adds lives in the playtest and is
  cleaned up (`sets.clear`, `stage.clear_actors`). Never `open_application` on Studio (it opens a second copy).
- **No AI model names** in commits, files or code comments.
- **Measure, then look.** Every check passing on the delivered file, every still looked at full size, every cut's
  frames looked at, before calling anything done.

## Where things are

- `library.md`: everything you can put in a shot: sets and their marks, the cast, the 43 faces, poses, camera moves,
  effects, voices, caption styles, music.
- `formats/`: one playbook per format, with its beat table, word budget, shot rhythm, sound plan, an original example
  skeleton and a scoring rubric.
- `writing/`: concepts (generators, premise tests, scoring), a bank of tested premises mapped to the library, craft
  (jokes, twists, escalation, the teen voice), packaging (titles, descriptions, hashtags).
- `building.md`: new sets and props with `tools/roblox/kit.py` (the buildings), lighting, marks, previews.
- `assets.md`: new faces, catalog items for new looks, sounds, music, emoji: how to make or find each, licensed.
- `checklist.md`: what the reviewer checks, every failure found so far; `review_brief.md`: the brief to give it.
- Worked examples: `videos/group-project/direct.py` (a rant), `videos/ding/direct.py` (a story across three sets),
  `videos/first-vs-last/direct.py` (a music comparison), `videos/pet-narrator/direct.py` (the one-prompt run: a
  story across four sets, pets made from code as props, a speech bubble as the rule's signature).
