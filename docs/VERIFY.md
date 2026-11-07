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
  check. `sub` is a second line on the same card; it counts toward read time.
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
| Text read time | a text is up for less than 0.5 s plus its characters at `--cps` a second (at least 1.2 s) |
| Flashes (WCAG 2.3.1) | more than 3 general or red flashes in any second, over the whole frame or any quarter of it (the 2 x 2 blocks of a 4 x 4 grid) |
| Clicks at cuts | never: listed as CHECK. A jump at a cut with a declared hit within 2 frames counts as the hit's onset. Listen for each one that's left. |
| Black and frozen frames | never: listed. Check that each was meant. |

### audio.py: the sound against the cut

```
python tools/verify/audio.py cut.json OUT.mp4
```

| Check | Result |
|---|---|
| Crossings | Every placed sound running across every cut, each with its reason: a bridge, or a prelap (a sound placed in the next clip that starts just before it). One with neither FAILs. |
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
- continuity: who, where and what, shot to shot;
- every walk and lean: full-size crops of the feet at full stride and as they pass, from a camera at ankle height
  where you can: the planted foot stays put and no planted sole goes into the floor (`pose.walk_check` measures a
  walk, `pose.soles` any pose);
- every pose, and every snap between poses: no arm through the head or chest (`pose.clearance`,
  `pose.snap_clearance`), and a face the hands don't hide;
- the first frames of every take: nothing in the scene still loading (textures, lights or shadows popping in);
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
  poses.

It confirms that each check catches its failure and passes the clean parts. It also checks `master.py`'s loudness
meter against ffmpeg's. Run it after changing any tool. When it last ran it passed 46 of 46.

On the third trailer cut, the delivered file measured:

- loudness: -14.2 LUFS, true peak -2.3 dBTP;
- flashes: none;
- sound: no undeclared crossings, every silence silent, every hit with a sound on it.

`qc.py` also fails two of its cards for read time, by 0.5 s each. It counts the cards' small "RULE 2" label lines,
and the trailer's own check didn't. Both are heuristics; this one is the stricter.
