# Verifying a cut

An agent can't watch or listen. Everything it says about a cut has to be one of two things:

- a measurement of the delivered file;
- a look at frames pulled from that file.

This is how, with the tools in `tools/verify/`.

## The timeline file

The tools read one JSON file per cut, the timeline (`tools/verify/timeline.py`). The edit and the mix both work from
it, so a beat is timed once.

```json
{
  "fps": 30,
  "clips":    [{"name": "hook", "frames": 45}, {"name": "reveal", "frames": 60}],
  "texts":    [{"text": "WAIT FOR IT", "start": 10, "frames": 40},
               {"text": "3", "start": 90, "frames": 4, "accent": true}],
  "hits":     [{"frame": 45, "what": "the reveal's first frame"}],
  "silences": [{"start": 1.40, "end": 1.50, "what": "the beat before the reveal"}],
  "cues":     [{"label": "theme", "bus": "music", "scene": "hook", "start": 0.0, "end": 3.5, "bridge": "reveal"}]
}
```

- **Units.** `clips` and `texts` are in frames; `silences` and `cues` in seconds. Clips play back to back; a
  clip's `start` is derived.
- **Texts.** `accent` marks text read at a glance, such as a number slammed on a beat; it's exempt from the read-time
  check. `sub` is a second line on the same card; it counts toward read time. `speech` marks a caption of what the
  voice is saying; it needs only the time to say it.
- **Cues.** `cues.py`'s `Mix.export` writes `cues` and `silences` for you. `bridge` is null, a clip's name, or
  `[clip, frame]`.

## The checks

### qc.py: the file

```
python tools/verify/qc.py OUT.mp4 --timeline cut.json [--lufs -14] [--tp -1.0] [--cps 12]
```

| Check | FAILs when |
|---|---|
| Specs | the timeline's length and the file's differ by more than a frame and a half |
| Loudness, on the MP4 | integrated loudness is more than 1 LU off target, or true peak is over `--tp` |
| Text read time | a text is up for less than 0.5 s plus its characters at `--cps` a second (at least 1.2 s); a caption of the voice (`"speech": true`), heard as it's read, for less than its characters at 35 a second (at least 0.25 s), measured on the references' own story captions (below) |
| Flashes (WCAG 2.3.1) | more than 3 general or red flashes in any second, over the whole frame or any quarter of it (the 2 x 2 blocks of a 4 x 4 grid) |
| Clicks at cuts | never: listed as CHECK. A jump at a cut with a declared hit within 2 frames counts as the hit's onset. Listen for each one that's left. |
| Black and frozen frames | never: listed. Check that each was meant. |

### caption_pace.py: captions against the references

```
python tools/verify/caption_pace.py VIDEO --words TRANSCRIPT.json --band 0.15 0.36 [--list]
```

Finds each caption change in the picture (white fill beside black outline, in a band of rows), pairs each caption
with the words said while it's up, and gives its time on screen and characters a second. On the references' story
captions (2026-11-08):

| Video | Captions | On screen: median, p10, least | Characters a second: median, p90, p95 |
|---|---|---|---|
| 006 | 58 | 0.55, 0.34, (0.03: a detection slip) s | 22.9, 39.4, 45.1 |
| 008 | 135 | 0.73, 0.42, 0.30 s | 20.0, 27.9, 30.0 |
| 009 | 50 | 0.62, 0.37, 0.28 s | 21.3, 38.2, 39.5 |
| 011 | 52 | 0.63, 0.38, 0.25 s | 23.6, 33.6, 34.5 |
| 013 | 49 | 0.65, 0.40, 0.23 s | 22.5, 28.8, 35.0 |

So `qc.py` fails a spoken caption faster than 35 characters a second (the middle of their p95s) or up under 0.25 s
(about their shortest). The rule before this was 25 a second and 0.3 s: a quarter of the references' own captions
would have failed it, and 13 of M4's 57 did, with the voice at the references' pace (ours: median 20.0, p90 29.5).

### audio.py: the sound against the cut

```
python tools/verify/audio.py cut.json OUT.mp4
```

| Check | Result |
|---|---|
| Crossings | Every placed sound running across every cut, each with its reason: a bridge, or a prelap (a sound placed in the next clip that starts just before it). One with neither FAILs. So does a timeline with sound but no cue sheet (the plan re-run after the mix wipes it, and every crossing would pass unchecked). |
| Silences | Each intended silence's peak on the final file. Over -60 dBFS FAILs. |
| Sync | For each hit: does a sound land within 2 frames (a rise over 6 dB, or a level over -14 dB)? CHECK if not. |
| Spectrogram | 30 Hz to 16 kHz with every cut marked and named. A tail past a cut shows as energy past its line. |

### sheets.py: the picture

```
python tools/verify/sheets.py cuts OUT.mp4 --timeline cut.json
python tools/verify/sheets.py contact OUT.mp4 --every 6 --timeline cut.json
python tools/verify/sheets.py frames OUT.mp4 120 121 122
```

- `cuts`: the two frames before and the two after every cut, one row per cut. This is where double exposures, flash
  frames, UI slivers and continuity breaks show.
- `contact`: a frame every N, each labelled with its time and its clip.
- `frames`: frames at full size. A tile is too small to judge an overlay: the misplaced one that got a cut rejected
  was a few dozen pixels off.

### analyze.py: reference videos

```
python tools/verify/analyze.py REF1.mp4 REF2.mp4 ... [--truth cut.json]
```

For each video it gives:

- the cuts it detects, the shot lengths and the cuts in each 5 seconds;
- the time of the first cut;
- loudness, flashes, and black or frozen stretches;
- one frame from every shot.

Cut detection is an estimate. Read its accuracy note in the script, and score it on one of your own renders first
(`--truth`).

## What measurement can't judge

Whether it's funny, whether the story reads, whether a sound sounds like what it is (cut 1's generator measured fine
and sounded like an alarm), whether a walk looks stiff. For those:

1. **An independent reviewer.** A fresh agent with no stake in the cut. Give it:
   - the paths of the current MP4 and the reports, with their times;
   - the timeline;
   - full-size frames of anything doubtful;
   - the checklist below.

   Ask for problems, not a grade.
2. **The owner.** Show stills and drafts early. Their reaction to a frame is worth more than any description.

### The reviewer's checklist

The checks have to come back clean first. Then:

- every overlay on every frame it's on, at full size;
- every cut's frames (-2 to +1): no double exposure, no stray frame, nothing at the edges;
- every text: readable on a phone, clear of the platform's buttons, up long enough;
- every crossing in `audio_report.md`: meant?
- every hit: a sound on it?
- every key word of the voice: nothing louder on top of it;
- every voice line: its `report.md` clean (every scripted word heard, pauses cut, the role's pitch and level), and
  the line in the voice of the character who says it;
- continuity: who, where and what, shot to shot;
- every walk and lean: full-size crops of the feet at full stride and as they pass, from a camera at ankle height
  where you can: the planted foot stays put and no planted sole goes into the floor (`pose.walk_check` measures a
  walk, `pose.soles` any pose);
- every camera move: the horizon level unless the shot means to tilt; a smear that never doubles a feature; the
  subject clear of the caption block (`camera.project`);
- every pose, and every snap between poses: no arm through the head or chest (`pose.clearance`,
  `pose.snap_clearance`), and a face the hands don't hide;
- the first frames of every take: nothing in the scene still loading (textures, lights or shadows popping in);
- every still before a shoot (`make.py stills`), at full size: no white wall burned out, no face hidden by a pose or
  cut by the frame, a two-shot wide enough for both, no actor inside furniture;
- every icon overlay: over the right head, on the right word, with its sound;
- every caption, face and pose on its word, not before it (a caption up before its punch is said kills the joke);
- every gesture inside the frame (a cheer in a close-up is a sliver of arm at the edge);
- no jump cut: the same subject from the same side needs a big change of size or angle across a cut, and the same pose;
- one voice per role: no line in another register (the voice report's register check);
- the end: nothing cut off in the last frames (a note, a word), so the loop is clean;
- everyone a shot is about in frame (the portrait frame sees about 4.7 studs either side at 15 studs; the plan
  warns), and no camera inside a wall or a prop (a frame of one flat colour);
- no face cut by an edge of the frame (a half-face at the edge of a group shot: M2's "Me:", M3's chat, M4's
  whisper) or down past 85% of the height, under the Shorts UI (M5's slumped close-up); the plan warns about both,
  with each face where its pose puts it;
- the first two seconds: what is this, and why keep watching?
- and every failure in `docs/LESSONS.md`, and every one found since.

## Trusting the checks

`python tests/selftest.py` builds a 6-second cut with failures planted in it:

- flashes;
- a caption too short to read;
- a sound across a cut;
- a click;
- a noisy silence;
- a hit with nothing on it;
- R6 poses that go wrong (`pose.py`): a lean that isn't planted; a walk 10% too fast, at standing height, or not
  planted; a swing that jumps speed; an overshoot that stalls; an arm through the head or chest, at rest or between
  poses;
- camera moves that overshoot, jump when cut short, ease the wrong way, cut across an orbit or move a pan; a smear
  that isn't 0 at rest or across a cut, or is too wide or too narrow; a streak that doubles, doesn't spread or isn't
  in linear light; a projection turned the wrong way.

It confirms that each check catches its failure and passes the clean parts. It also checks `master.py`'s loudness
meter against ffmpeg's. Run it after changing any tool. When it last ran it passed 106 of 106.

On the third trailer cut, the delivered file measured:

- loudness: -14.2 LUFS, true peak -2.3 dBTP;
- flashes: none;
- sound: no undeclared crossings, every silence silent, every hit with a sound on it.

`qc.py` also fails two of its cards for read time, by 0.5 s each. It counts the cards' small "RULE 2" label lines,
and the trailer's own check didn't. Both are heuristics; this one is the stricter.
