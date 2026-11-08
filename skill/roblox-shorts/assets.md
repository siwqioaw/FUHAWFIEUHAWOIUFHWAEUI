# Custom assets: making or finding what the library lacks

Every asset needs a licence and a line in `ATTRIBUTION.md`. Generated media stays in `build/` (never committed);
code that makes an asset is committed.

## A new face

Add an entry to `FACES` in `tools/roblox/facekit.py`, built from its parts (eyes, brows, mouth, extras), so it keeps
the set's line weight:

```python
"suspicious_grin": _face(_p(eyes_flat, tilt=6), _p(brows, kind="skeptic"), _p(mouth_grin, h=40)),
```

Then `python tests/studio_library.py faces` (draws and installs them into Studio's content folder, no upload) and
`python tools/roblox/facekit.py sheet` to look at it beside the others. A new part (a new eye shape) is a small
function drawing with `Face.line`, `Face.curve`, `Face.ellipse`, `Face.poly`.

## A new look for the cast

1. Find free items on Roblox's public catalog API (no login), made by Roblox, old enough to fit R6 (2011-2019):

```
https://catalog.roblox.com/v1/search/items/details?Keyword=hair&CreatorName=Roblox&MaxPrice=0&Limit=30
https://catalog.roblox.com/v1/search/items/details?Category=3&Subcategory=56&CreatorName=Roblox&Limit=30   # shirts
https://catalog.roblox.com/v1/search/items/details?Category=3&Subcategory=57&CreatorName=Roblox&Limit=30   # pants
```

2. Add the look to `tools/roblox/cast.json` (skin colour, hair, face accessories, shirt, pants).
3. `python tests/studio_library.py cast` builds every look on R6, writes a line-up and a fit report: an accessory more
   than 1.2 studs under the head is MISFIT (made for R15). Use only looks that fit.
4. Log every item in `ATTRIBUTION.md`.
5. Hold the look up against the references' recurring characters (`refs/r6rants/SYNTHESIS.md`): a free catalog
   outfit can be theirs. M2's fourth review found `extra_c` in the black jacket and motorcycle tee their recurring
   kid wears; it's an orange sweater now. Plain body colours (`torso`, `arms`, as the `student_*` looks) are a safe
   way to make a look nobody else has.
6. Two actors can share a look (M5's `refl`, Max's reflection, is the same `jock` look): cast them under two names.

## Sounds

- Simple effects: add a function to `tools/edit/sfx.py` (a few lines of synthesis), listed in `EFFECTS`.
- Anything else (a door, crickets, a crowd): the ElevenLabs connector's sound effects (`creative_generate_in_flow`
  with `node_type: "sfx"`), saved to `build/library/sfx/`, the prompt and date logged in `ATTRIBUTION.md`.
- Never ripped meme clips.

## Music

- **Music-only formats:** YouTube's Audio Library (studio.youtube.com, the owner's channel): a track whose licence needs
  no attribution, downloaded into `build/library/music/`, logged. Find its beat grid (`docs/MAKING.md`).
- **A voiced video's bed:** the Audio Library, or ElevenLabs music through the connector (`node_type: "music"`,
  `instrumental: true`, a 1-3 sentence prompt: genre, mood, instruments, tempo), on the owner's paid plan. Not for a
  music-only video, where the music is the focus.

## Emoji and icons

Noto's 3D emoji (`assets/emoji/noto/`): add a missing one from `github.com/googlefonts/noto-emoji` (`3D/png/128`,
`emoji_u<codepoints>.png`). A caption with an emoji that has no picture raises rather than drawing a box.

## Images in the world

Posters and signs are text on parts (`kit.Set.sign`). A picture on a part needs an uploaded image (the owner's
call, in Studio) or a decal from the Toolbox (checked and logged): prefer text and colour.
