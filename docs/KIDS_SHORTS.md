# Kids' Roblox shorts: what changes

**This page is untested advice.** None of it was tried in the project this kit comes from, which was a horror trailer
for teenagers and up. Treat each point as something to check:

- against the reference videos the owner provides, measured with `tools/verify/analyze.py`;
- against each platform's current rules;
- with the owner.

Replace it with what you learn.

## What carries over

- **Measure.** The method holds: build from code, check by measurement on the delivered file, then have an
  independent reviewer look.
- **The checks don't change:**
  - photosensitive flashes;
  - read time;
  - sound kept inside its scene;
  - silences silent;
  - true peak after the encode;
  - overlays checked at full size.
- **Capture.** The Roblox capture kit: posed frames, exact camera moves, actors posed from code.

## What changes

- **The format.**
  - Vertical: 1080 x 1920, 30 fps (or 60 for fast gameplay).
  - A length under each platform's current limit for its short format. Check the limits: they change.
  - `deliver.py --size shorts`.
- **Capture resolution** is the first technical problem (`docs/ROBLOX_CAPTURE.md`, "Resolution"). Solve it before
  making anything else.
- **The opening.** The first second or two has to say what the video is. The trailer's confusing opening was its
  first rejection, and a short has even less time.
  - Measure it: how soon do the references cut, and what is on screen at 0.5 s?
  - Check it: what does the frame at 1 s say?
- **The look.** Bright, saturated, clean, readable on a small screen. That's the opposite of the trailer's grade:
  drop the lifted blacks and heavy grain if the references don't have them, and keep `look.grain` faint.
- **Captions.**
  - Big, heavy, outlined, centred, and clear of the platform's buttons.
  - Word-by-word highlighting (`typeset.caption(..., highlight=k)`) is common in shorts; check whether the references
    use it.
  - Young viewers read slower: run `qc.py` with a lower `--cps` than the trailer's 12. That number is a guess to
    tune, not a standard.
- **Sound.**
  - -14 LUFS still, but no sudden very loud hits: children watch on tablets at whatever volume was left on.
  - Keep the loudness range modest: `qc.py` prints it, and the references' is in `analyze.py`'s report.
- **Content.**
  - Nothing frightening, graphic or mean: no jump scares.
  - Nothing that teaches unsafe behaviour or encourages buying things.
- **Pace.** Shorts cut fast, but a cut a child can't follow is as bad as a slow one. Match the references' median
  shot length (`analyze.py`), and give every story beat time to land.

## Platform and legal points: the owner decides

- **Made for kids.** Whether to mark a video "made for kids" changes how the platform treats it (comments,
  personalised ads, some features), and in the US it's tied to COPPA. That is the owner's decision. Don't set it or
  advise on it as settled; point them to the platform's own guidance.
- **Real people.**
  - No children's personal information on screen: no real usernames, faces, voices, schools or locations.
  - A real person's avatar or name only with that person's permission, and a parent's for a child.
  - Stand-in actors (`stage.actors` with colours) need no one's permission.
- **Roblox's brand.** Roblox's name, logo and look belong to Roblox. Check Roblox's current guidelines for creators
  using them in videos and thumbnails. Don't make anything look like official Roblox content or Roblox's own
  interface.
- **Other people's work.**
  - Reference videos are for measurement and study only. Never reuse their footage, music, characters or jokes word
    for word.
  - Every sound, piece of music, font and image needs a license that allows it. Record each in `ATTRIBUTION.md`.
- **Synthetic content.** Some platforms require disclosing realistic altered or synthetic media. Check whether
  game footage and generated voices fall under their current rules, and tell the owner.
- **Publishing.** Uploading or posting anything is the owner's call, every time.

## Study the references by measurement

The first job in the new project, before writing any shot:

```
python tools/verify/analyze.py refs/*.mp4 --out build/analysis
```

For each video, `analyze.py` reports:

- its length;
- the shot count and median shot length;
- the time of the first cut;
- the cuts in each 5 seconds (the pace curve);
- loudness and loudness range;
- flashes;
- one frame from every shot.

Then write a short table of what the references have in common, and what they vary. That becomes the spec for the
first video. Score the cut detection on one of your own renders before trusting it (`--truth`).
