# Faces

`tools/roblox/facekit.py` draws the 43-face library from code: black line art in one weight (17 px at 512), with a
few coloured accents (blue tears and sweat, pink blush, red hearts and an anger vein, gold stars, green dollar signs).
Each face is built from parts (eyes, brows, mouth, extras), drawn at four times the size and scaled down, so every
edge is smooth and every face matches.

```
python tools/roblox/facekit.py build build/faces/kit --install    # draw, sheet, and install into Studio
python tools/roblox/facekit.py sheet                              # the contact sheet on skin
```

Faces render from Studio's content folder (`tools/roblox/faces.py`): nothing is uploaded, and a face changes on any
frame (`make.py` keys them to words). The selftest checks every face draws on the front of the head.

| Mood | Faces |
|---|---|
| everyday | smile, grin, laugh, blank, deadpan, bored, wink, tongue, proud, whistle, sleepy, oval |
| surprise, fear | shock, gasp, scared, nervous, wide_happy |
| anger | angry, yell, furious, pout, grimace |
| sadness | sad, cry, sob, teary, sad_smile |
| attitude | smug, side_eye, side_eye_left, sus, scheming, evil, disgust, confused, cringe |
| big feelings | love, starstruck, money, cute, dizzy, dead, derp |

The references draw faces that change on almost every line; ours are our own designs (the owner's decision), not
copies of theirs or of Roblox's classic faces. Adding one: `skill/roblox-shorts/assets.md`.
