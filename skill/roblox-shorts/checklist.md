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
- **Framing:** heads above the caption block (70% of the height); nobody cut in half at an edge unless meant; the
  subject of the line in frame; no camera inside a wall or a prop.
- **Staging:** no actor inside furniture or another actor; feet on the floor; no one floating; walks don't slide.
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
  of silence before the line.
