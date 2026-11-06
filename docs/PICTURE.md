# Picture

Frames are float32 RGB arrays in 0..1 (display-referred sRGB), H x W x 3, and layers are straight-alpha RGBA. The
modules in `tools/edit/`:

| Module | What's in it |
|---|---|
| `look.py` | loading and saving frames, linear-light conversion, motion-blur averaging, reframing, compositing, vignette, grain, lifted blacks |
| `typeset.py` | text as layers: tracking, outline, shadow, glow; word-wrapped captions with a highlighted word; trimming; RGB split; a blinking caret |
| `fx.py` | easing; slam, pop and decoding text; shake, chroma split, zoom blur, whip smear, tear, datamosh, vignette pulse |
| `render.py` | the master: frames rendered in parallel worker processes, written as ProRes 422 HQ |

## A cut is a function of the frame number

The edit is one module-level function, `frame_at(r)`, that builds frame r from the timeline: which clip, which take,
which frame of it, what goes on top.

- **Nothing carried over.** It carries no state from one frame to the next, and every random effect takes the frame
  number as its seed.
- **Why it matters.**
  - `render.master` renders frames out of order across processes;
  - `render.stills` can render any single frame to check it;
  - a fix to one shot re-renders only that shot.

## Light is mixed in linear light

Averaging and blending in sRGB darkens and muddies the edges of anything bright.

- **Motion blur.** `look.load_avg` averages a frame's motion-blur sub-frames in linear light.
- **Composites.** Do the same for any cross-fade or composite that mixes light.

## Motion blur

The capture can take several sub-frames per frame, spread across a shutter (half the frame is a film camera's 180
degrees). The edit averages them.

- **At a cut or a camera jump**, use only the frame's **last** sub-frame. The first ones still show the old framing,
  and averaged, the jump reads as a double exposure.
- **Check it** in `sheets.py cuts`.

## Never draw a tracked overlay over 3D footage

The rejected "glowing eyes" were dots drawn in post at a projected head position, and they missed the face by dozens
of pixels. Instead:

- **Put it in the scene.** In Studio: a light, a part, a billboard, and capture it with the shot. It then moves with
  the world by construction.
- **Or cut to it** as a full-frame insert.
- **Never blend a face or a picture over a take at partial opacity.** It reads as a ghosted double image. Choose one
  picture and cut.
- **Text and stickers that don't track anything** (captions, a title, a counter) are fine drawn in post.

## Reframing

- **One picture into another frame.** `look.reframe(src, out_w, out_h, zoom, cx, cy)` crops to the output's shape
  about a point.
  - It's a sub-pixel affine warp, so a slow digital push glides rather than stepping a pixel at a time.
  - It scales with Lanczos and applies a light unsharp mask.
  - An upscale of more than about 1.5x goes visibly soft: capture at the size you deliver if you can
    (`docs/ROBLOX_CAPTURE.md`, "Resolution").
- **A wide picture in a tall frame.** `look.fit_blurred(src, 1080, 1920)` fits the whole picture to the width over a
  blurred, darkened copy of itself. It's the common way to put a landscape clip in a vertical short. The trailer didn't
  use it.

## Type

- **Read time.** `qc.py` checks it: 0.5 s plus the characters at 12 a second, at least 1.2 s. Lower `--cps` for a
  young audience.
- **Over busy footage.** Use a heavy face, an outline (`stroke`, about 0.12 em) and a soft shadow.
  `typeset.caption(text, size, max_width, highlight=k)` wraps a caption and colours word k: for word-by-word captions,
  step k with the voice.
- **Keep text clear of the platform's own buttons and captions.** On vertical video the right side and the bottom
  are covered. Check each platform's current safe area, and look at the frame at phone size.
- **Fonts are files.** Keep each font's license beside it. Most free faces are under the SIL Open Font License, which
  allows bundling them.

## Effects

`fx.py`'s effects are all pure functions of their input and a seed.

- **What the trailer liked.** Hard cuts on beats, and one strong device used with intent. The owner praised the
  countdown and the hard cuts, and rejected a cut to a blur.
- **Use effects on purpose.** Every effect should mark a beat.
- **Easing.** `fx.ease` is smoothstep, `ease_out_cubic` settles, and `ease_out_back` overshoots and settles (for
  pops).
- **Camera shake** (`fx.shake`) moves the picture only. Shake the frame, then put the text on.

## Photosensitivity

WCAG 2.3.1:

- **The limit.** No more than 3 flashes in any second over a quarter of the frame. A flash is a pair of opposite
  changes in luminance of 10% or more where the darker state is under 80%; saturated red counts on its own.
- **Flash frames count.** A white flash frame on a hit counts, so a run of them on fast beats fails.
- **Checked.** `qc.py` checks the whole frame and every quarter of it.

## For the platform's re-encode

Platforms re-encode what they're given, and dark areas band and crush first.

- **Lift the blacks.** `look.lift_blacks` lifts them about 3%.
- **Add grain.** `look.grain` adds fine grain at the delivery size. It hides banding and survives the re-encode
  better than smooth gradients.
- **Deliver clean.** Give the platform a clean, high-bitrate file at its native size (`tools/edit/deliver.py`).
