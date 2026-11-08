# Comparison: "[A] VS [B]" (family C, music only)

**Use when** the concept is a before/after or two sides (first day vs last day, Monday vs Friday, mom vs dad).

**Length** 10-12 s; no voice; 30 fps (as the references' music formats). A header per side from frame 0 (`header`
style: `"{yellow:First} day of school.."`), three shots a side, the second side outdoing the first, "Me:" or a
reaction to close.

## Building it

- Music from YouTube's Audio Library (never AI music here: the music is the focus). Find its beat grid and its
  loudest section (`docs/MAKING.md`), start the bed on a beat, and make every shot two (or three) beats long.
- `seconds=2 * BEAT` per shot; a boom on the turn between sides; `texts` for the headers.
- Each shot one tableau with a small camera move: `push`, `low`, `top`, `two_shot`, `dutch_in`.

## Example skeleton (original)

`videos/first-vs-last/direct.py`: eager on the first day (cheering, hand up, friends), wrecked on the last (asleep,
yelled at, sprinting out with an evil grin), then a deadpan "Me:".

## Rubric

A header on frame 0; cuts on the beat; the second side absurdly worse; a closer that loops.
