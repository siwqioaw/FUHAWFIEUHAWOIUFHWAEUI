# Sound

The sound is built in Python from files on disk:

1. **Place.** `tools/edit/cues.py` places each sound on the cut, through a cue sheet that keeps sounds inside their
   scenes.
2. **Master.** `tools/edit/master.py` sets the loudness and keeps the peaks under the limit.
3. **Check.** `tools/verify/audio.py` and `qc.py` measure the result on the delivered file.

## The cue sheet

Every sound is placed **in a clip**, at a time into it:

```python
from cues import Mix, load, duck
mix = Mix(Timeline.load("cut.json"))                         # buses: voice, music, sfx, ambience
mix.place("sfx", load("pop.wav"), "hook", at=0.40, gain_db=-4, label="pop")
mix.place("music", load("theme.wav"), "hook", until="ending", label="theme")      # a bridge, declared
mix.place("voice", load("line3.wav"), "reveal", at=-0.20, prelap=0.25, label="line 3")   # starts before its picture
mix.silence(4.0, 4.25, "the beat before the reveal")
out = mix.render({"voice": 0, "music": -10, "sfx": -3})
mix.write("build/mix_raw.wav", out)
mix.export("cut.json")                                       # the placements, for audio.py
```

- **Cut off at the clip's end.** A sound stops at the end of its clip, with a 30 ms fade, unless `until` says how far
  it may run: a later clip's name, or `(clip, frame)`. A sound can't bleed into the next scene unless you said so.
  That was the roar that got cut 2 rejected.
- **Starting before its clip.** A sound that starts before its clip (a prelap: the next scene's sound arriving a
  beat early) must say how far back it may start (`prelap`), or `place` raises.
- **Silences.** `silence` marks a span meant to be silent. The render mutes it, and so does `master.py` after the
  master chain.
- **Checked.** `export` writes every placement into the timeline file. `audio.py` lists every sound across every cut,
  and fails one that is neither a bridge nor a prelap.

## Under the voice

- **Duck.** Music and effects come down under speech: `duck(music, voice, sr, depth_db=-9)` eases the music down
  wherever the voice is above -45 dBFS, in 40 ms, and back over 350 ms.
- **Key words.** A word the story hangs on must be the loudest thing at that moment. In the trailer a beep placed on a
  key word sat 9 dB over it.
- **Measuring it.** Read the voice stem's level at the word against everything else's (the stems are the buses before
  the mix), and look at the spectrogram.

## Mastering

```
python tools/edit/master.py build/mix_raw.wav build/mix.wav --timeline cut.json
```

- **The chain, in order:**
  1. A high-pass at 22 Hz.
  2. Gain to -14 LUFS integrated (ITU-R BS.1770; the meter agrees with ffmpeg's to 0.05 LU in the self-test).
  3. A look-ahead true-peak limiter at a -2.4 dBTP ceiling.
  4. The silences muted again.
- **When it can't reach the target.** If -14 LUFS would take more than 6 dB of limiting, the gain backs off and the
  file comes out quieter than the target. Fix that in the mix: a too-loud transient over a quiet bed.
- **Why -2.4 dBTP.** The AAC encoder adds true peak to sharp clicks: up to 3 dB in the trailer, and 1.1 dB in the
  self-test. The fix there was two parts:
  - the ceiling at -2.4;
  - the two sharpest sounds (a contactor and a kick) low-passed above about 5 kHz.

  `qc.py` measures the MP4, and that is the number that counts.
- **The target.** -14 LUFS is the figure usually given for YouTube's loudness normalisation, and the trailer used it.
  Check each platform's current behaviour: a louder file gets turned down, and a quieter one mostly stays quiet.

## Sync

Each hit in the timeline (a cut, a slam, a pop) should have a sound landing on it. `audio.py` checks for a rise of
over 6 dB, or a level over -14 dB, within 2 frames of each, and marks CHECK where there's none. A sound placed with
`frames=True` at the hit's frame lands exactly on it.

## What a measurement can't tell you

Whether a sound reads as what it is. In cut 1 a generator sound measured fine and sounded like an alarm, and only the
owner could hear that.

- Use sounds recorded or designed as the thing they stand for, and name the files for what they are.
- Ask the owner to listen early: a 10-second test clip of the key sounds costs little.

## Sources

Every sound needs a license that allows its use in the video: your own recordings or synthesis, a library's terms,
or a royalty-free license. Keep a record of each source and its license beside the project. A platform's content ID
match on borrowed music can mute or demonetise a video.
