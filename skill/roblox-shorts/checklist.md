# The reviewer's checklist

A fresh reviewer gets `out/<slug>.mp4`, `build/<slug>/cut.json`, `build/<slug>/plan.json`, the voice report and this
list, never the maker's opinion. Every item needs evidence (a frame number, a measurement). Add every new kind of
failure found to this list and to `docs/VERIFY.md`.

## Measured (must pass before review)

- `build/<slug>/verify/qc_report.md`: loudness -14 LUFS +-1, true peak <= -1 dBTP, read time, no clicks at cuts, no
  flashes over the WCAG limit, no unintended black or frozen frames.
- `audio_report.md`: every sound crossing a cut declared; every hit has a sound on it.
- The voice report: every line's checks pass.

## Looked at

- **Every cut** (`verify/cut_*` sheets, frames -2 to +1): no double exposure, no stray frame, nothing popping in.
- **First frames of every shot:** nothing still loading (textures, faces, lights).
- **Faces:** the right face on the right word; never a blank default face; no face hidden by a hand or hair; the
  actor whose line it is looks like they're saying it.
- **Framing:** heads clear of the caption block (a comedy's sits below 66% of the height, a story's above 36%); no face
  cut by an edge of the frame (the plan warns: a back row at a push-in's edges shows only as half-faces) or down past
  85% under the Shorts UI; a close-up aimed at the face where the pose puts it (a slump drops it half a stud); the
  subject of the line in frame; no camera inside a wall or a prop.
- **Staging:** no actor inside furniture, a prop or another actor (the plan's staging warnings, limb by limb: R6s
  side by side need 4 studs, cheering 5; a walk 4 studs' room past anyone); feet on the floor; no one floating; walks don't slide; a
  walk ends facing where the shot needs the face.
- **Every beat in the picture:** each line's action shown, not just said (M4: "switched schools" over a white wall,
  "hid behind the lockers" with no lockers to hide behind, "ate lunch alone" from above, "sat down" in profile).
  Lunch goes in the `cafeteria`, a dance in the `gym` with `{"dance": True}`.
- **The signature escalates:** when the story says louder or more, the sound and the picture get louder and bigger
  (M4's dings measured quieter as the line said "so loud"); the rule shown in the first second, not after it's
  explained.
- **Gestures read:** a raised hand clears the head (an R6 arm straight up reaches only the top of the head, its
  shoulder pivot is that low: `hand_up` leans the body 20 degrees away so the hand clears it by 0.6); a point
  crosses the frame toward its target, not at the camera; a gesture's hand inside the frame (the plan warns, at
  mid-shot); background gestures not behind a
  foreground head (two fists poked out of a narrator's hair like ears).
- **Icons:** over the right head (the one the rule is about), never on a face, and over a subject the camera can see:
  a speaking pet behind its owner puts the bubble on the owner's shirt (M5; the plan warns).
- **Set writing:** none under the captions (posters, boards, scoreboards: `{"signs": False}`).
- **Captions:** the script's words, timed to the voice; CAPS where the script stresses; emoji drawn (comedy only);
  readable on a phone; never over a face.
- **Sound:** the voice clear over the bed; a boom after every punch (comedy); the rule's sound on every instance
  (stories); nothing louder than a key word.
- **Story:** the premise in the first second; one idea per shot; escalation; the twist or last punch lands; it loops.
- **Rules:** teen-safe; original (nothing from the references); no Roblox logo or UI; every asset licensed and logged.

## Failures found so far (and what catches them)

- White walls burned out in interiors (sets' first previews): the interior preset's exposure; look at stills.
- A two-shot too tight for its actors (M3's first stills): `two_shot` distance from their spacing; look at stills.
- A sleeping actor's face hidden by a slumped head: pose the face toward the camera; look at stills.
- A word the transcriber hears as its homophone ("Seen." as "Scene."): the voice check matches homophones.
- Expressive reads outside a role's pitch or pace range: the ranges catch gross mistakes only (`docs/VOICE.md`).
- A name lower-cased at a caption's start ("leo had never" beside "so Leo stopped", M4's plan): `make._names` keeps
  any word the script capitalizes mid-sentence; selftest.
- Story captions ending on "a" or "the", or leaving one word alone ("you hear a | ding.", "a few a | day."):
  `make._story_groups`; selftest.
- A read-time rule stricter than the references (25 characters a second failed 13 of M4's 57 captions with the voice
  at the references' pace): measure theirs with `tools/verify/caption_pace.py` before changing a threshold.
- A Roblox logo on a costume (the teacher's "ROBLOX Jacket" in M3's `grade` shot): read every cast item's name in
  `ATTRIBUTION.md` for "Roblox" and look at each actor in the stills; the teacher now wears a plain sweater.
- A gap hovering round the silence line left uncut (M5's line a, 0.22 s at 38-42 dB under): `voice.quiet_spans`
  fills from the first 30 ms of silence to the last; selftest, with the measured profile.
- A soft first consonant missed by the transcriber ("She aced" heard as "He aced", M5): it hears a copy with 0.5 s
  of silence before the line. When even the raw take is heard wrong, the read is wrong: regenerate the line.
- Actors a shot is about standing outside the narrow portrait frame (M4's gossips by the lockers, the people Leo
  walks past; M5's bragging owners): `make.py plan` warns ("never in frame"); stage in depth, not side by side.
- A camera inside a wall (M4's over-the-shoulder shot from behind an actor against the lockers: a solid blue
  frame): look at every still before the shoot; film from where the near actor stands instead.
- A regenerated line's new takes ignored for the old files of the same name: takes are now named by the take.
- Actors inside each other (M3's presenters 3 studs apart, her elbow through his arm): R6 actors with arms out are
  about 4 studs wide; stand them 4.4 apart.
- Captions and faces before their words (M3: a punch captioned 0.6 s before it was said): `voice.refine_words`.
- Gestures out of frame in close-ups (a cheer, a point): key a face instead, or frame wider.
- A jump cut (M3's `the_chat` into `seen`: 1.17x the size, the head dropping across the cut): change size by 2x or
  more, or the angle, and keep the pose.
- A line in another register (M3: the narrator an octave down, 5-7 dB quieter in the speech band): the voice
  report's register check.
- A click when the Short loops (a note cut 8 ms before the end): the mix fades the bed and the end.
- A check passing on missing data (`audio.py` on a timeline with no cues): it fails that now.
- Captions coming in after a cut by 1-3 frames: they snap to it.
- Booms on static holds, their tails under the next word: a punch-in on the hit, the tail ducked.
- Faces under the story captions (M5's first stills: the street owners' faces 23-32% down, the captions'
  block at 19-31%): the plan warns; aim higher and further back (a face about 40% down at 9.5 studs).
- A camera inside an actor (M5's `didnt`: a dark blur of jeans, the low camera behind Max's legs): the plan
  can't see it; the stills can. Keep anyone out of the line between a low camera and its subject.
- Icons off the frame (M4: 13 of 26 bells set round a head in a close-up): the renderer pulls them inside, clear
  of the captions; set them close to the head in close-ups anyway.
- Flat frames from a camera above a ceiling (M4's overhead `lunch`: `top()` starts 2 studs over its height; the
  classroom's ceiling is at 15): `qc.py` fails a run of one flat colour.
- Two captions on one frame (a rounding slip): selftest.
- People from one place turning up in another (M4: the old school's jock at the new school): cast each place.
- A jump cut on one line (1.6-1.8x, same angle): orbit the second shot 30 degrees or more.
- Cuts off the beat (M2: a 120 BPM track with 3-3-2 accents read as 80 BPM from one autocorrelation peak): find
  the strongest onsets, check the bar (2 s at 120 BPM) and cut on the accents; make a music format whole bars long
  so the loop comes round in phase.
- A shot whose joke needs words (M2's top-down "asleep": hair and shoulders): each 1.5 s shot of a music format
  must read from its picture alone.
- Icons missing in a video's other sets (M5: every speech bubble outside the street, its point never moved by the
  set's offset): fixed in `_offset_shot`; selftest. Look for the rule's signature in every shot that has one.
- A new pose that clips (a sideways wave put the arm 0.33 studs into the head): the selftest measures every pose;
  raise an arm through the front, not out to the side past about 60 degrees.
- A prop in the camera's path (M5's `aced` opened inside the street's parked car, at (12, 0, 7)): look at the
  first frames of every shot, not only the middle still.
- A pet inside its owner (M5: the dance dog's head on Max's mark): place a pet beside its owner's mark, its head
  a stud clear, and look at the shot from behind too.
- Actors waiting for later shots visible in the sky (M5's opening: they waited at z = 400, in front of a camera
  looking north on the open street): they wait under the floor now.
- A rule's signature without its sound (M5's bubbles): every instance gets both, as M4's bells and dings do.
- Captions over set text (a poster's "GAME ON" right above them): keep text on walls out of the captions' band.
- Word starts late after the refinement (M5: 0.09-0.24 s): `refine_words` walks back to the sound's onset.
