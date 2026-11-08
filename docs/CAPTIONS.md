# Captions

`tools/edit/captions.py` draws captions in the references' house style. Spike S6 (2026-11-08) measured the style on
full-size reference frames and matched it; `tests/s6_captions.py` shows ours beside theirs.

```python
import captions
frame = captions.over(frame, "why does every group project have that ONE person? 😭", "comedy")
layer, (x, y) = captions.render("in this world, NOBODY", "story")      # or place the layer yourself
captions.lines_of(text, "comedy")                                      # how it wraps, for the timeline's texts
```

## The styles

All white Montserrat SemiBold with a black outline and no box, letter-spaced -0.02 em, cut in hard on the cut (or a
frame or two before it).

| Style | For | Cap height | Outline | Line to line | Where | Width | Emoji |
|---|---|---|---|---|---|---|---|
| `comedy` | family A: a clause per caption, CAPS on the stressed words | 43 px | 4 px | 1.465 cap heights | the block's centre 77.9% down | up to 800 px | one, at the end, outlined like the letters, 1.16 cap heights tall |
| `story` | family B: 1-3 words, a new one about every 0.6 s, lowercase with CAPS on the loud words | 66 px | 8 px | 1.47 | the block's centre 24.8% down | up to 760 px | none |
| `header` | family C's header: a word in braces takes a colour, `{pink:Mom's} old photos..` | 65 px | 7 px | 1.48 | the first line's cap top 11.2% down | up to 900 px | rarely |
| `label` | family C's label per type, under the header | 50 px | 6 px | 1.48 | as placed | up to 900 px | rarely |

Sizes are at 1080 x 1920; `over` scales them for a smaller frame. Colours for braces: pink, blue, yellow, green, red,
purple, orange, white.

## Pace

Measured with `tools/verify/caption_pace.py` on the references' story captions (006, 008, 009, 011, 013): a new
caption every 0.55-0.73 s (median), up for 0.23-0.30 s at the least; 20-24 characters a second at the median, the
fastest 5% at 30-45. M4's captions, planned: median 0.53 s up, p10 0.39, least 0.27; 19.5 characters a second, p95
30.3. How `make.py` breaks and times them is in `docs/MAKING.md`.

## How it was matched

On four reference frames (001 at 1.2 s, 006 at 2.0 s, 002 at 1.0 s and 014 at 1.5 s, all full size), each glyph's
white fill was found as a white region ringed by the black outline, and measured:

| | Reference | Ours |
|---|---|---|
| comedy: cap height, outline | 43 px, 4 px | 43 px, 4 px |
| comedy: the stems of I and l | 6-7 px | 7 px (SemiBold; Medium is 5, Regular 4) |
| comedy: "why are popular GIRLS so" | 773 px wide, baseline at 1485 | 778 px, 1486 |
| comedy: the second line's baseline | 1548 | 1549 |
| story: cap height, outline | 66 px, 8 px | 66 px, 8 px |
| story: "until you" / "TOUCH" | 383 / 331 px wide, baselines 460 / 557 | 397 / 335 px, 461 / 559 |
| header: first baseline | 260 (002), 295 (014) | 280 |

- The reference's font is a geometric sans like Montserrat; its lowercase runs about 3% narrower than Montserrat's,
  its capitals a little wider. At -0.02 em the comedy line comes out the same width.
- The two references' headers sit 35 px apart from each other, so ours sits between them.
- The references outline their emoji like their letters; ours does too.

`tests/s6_captions.py` writes `build/s6/compare_<style>.png`: the reference's crop, ours on the same picture (the
reference's caption painted out), and ours as a red ghost over theirs.

## Assets

- **Font:** Montserrat (Regular to Black), `assets/fonts/montserrat/`, SIL Open Font License 1.1 (`OFL.txt` beside
  it).
- **Emoji:** 50 of Noto's 3D emoji at 128 px, `assets/emoji/noto/`, by Google (the repository's licence beside them).
  A caption with an emoji that has no picture there raises instead of drawing a box: add the picture
  (`emoji_u<codepoints>.png`, without FE0F) from the same set.
- Not Apple's emoji, which the references use: their licence doesn't allow it.
