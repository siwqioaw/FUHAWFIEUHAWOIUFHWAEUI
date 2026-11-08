# Comparison: "[A] VS [B]" (family C, music only)

**Use when** the concept is a before/after or two sides (first day vs last day, Monday vs Friday, mom vs dad).

**Length** 10-12 s; no voice; 30 fps (as the references' music formats). A header per side from frame 0 (`header`
style: `"{yellow:First} day of school.."`), three shots a side, the second side outdoing the first, "Me:" or a
reaction to close.

## Building it

- Music from YouTube's Audio Library (never AI music here: the music is the focus). Find its beat grid and its
  loudest section (`docs/MAKING.md`), start the bed on a beat, and cut on its accents, measured from the strongest
  onsets and their autocorrelation (M2's first cut read a 120 BPM 3-3-2 track as 80 BPM and missed every accent).
  Put the biggest cuts on the biggest hits, and make the length whole phrases, not only whole bars (M2's five bars
  over four-bar chords loop on the beat but not the phrase).
- Fixed shot lengths in frames (`CUTS`), a boom on the turn between sides; `texts` for the headers.
- Each shot one tableau that reads at a glance, with a small camera move: `push`, `low`, `two_shot`, `dutch_in`.
  Not `top` (from above, R6s are hair and shoulders). A raised hand needs `hand_up` (it leans away: an R6 arm
  straight up only reaches the top of the head); a point turned across the frame at its target; a seated look at a
  desk (the desk hides the legs) or a cafeteria bench (`sit`); people behind the punchline's face stood where they
  show above or beside it, not behind it (two fists out of a narrator's hair read as ears).

## Example skeleton (original)

`videos/first-vs-last/direct.py`: eager on the first day (a wave, a hand up in class, a high five), wrecked on the
last (asleep at his desk, yelled at, sprinting out with an evil grin), then "Me:": the channel's narrator, wrecked
on the first day while everyone behind him cheers.

## Rubric

A header on frame 0; cuts on the beat; the second side absurdly worse; a closer that loops.
