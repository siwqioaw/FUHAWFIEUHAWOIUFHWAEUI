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

## On a phone

Most Shorts are heard on a phone's speaker, which plays little below 200-300 Hz. Measure the punches there too: the
level from 300 Hz to 8 kHz in the 0.3 s after a hit against the 0.3 s before. M2's turn rose under 3 dB there with
a pure sub-bass boom (-46 dB of its energy above 300 Hz: silent on a phone, and its sub pumped the limiter, pulling
the music's mids down under it); the other cuts rose 9-10. The boom now carries a low-mid body (a glide from 180 to
110 Hz driven into harmonics) and a knock at 0.8-4 kHz over a lower sub (`sfx.boom`, `sub=0.45`). A sound that must
read on a phone needs its own energy above 300 Hz.

Its peak still sets how loud the file can be. Over a loud music bed (M2's track at -1 dB, no voice), the boom's cue
3 dB up rose 7.7 dB on the phone band in the mix, but its peak needed 8 dB of limiting to reach -14 LUFS; the master
takes 6 at most, backed off, and the file came out at -15.9 LUFS and failed, the boom squashed to +5.0 dB. At +2 dB:
-15.1 LUFS, still out. At +1 dB: -14.3 LUFS and +3.4 dB on the phone band, kept. Neither a lighter sub (+1 dB of
mids for the same peak at most) nor dipping the bed under the boom (the boom's own peak is the limit) bought more.
Check the delivered loudness after raising any hit.

## What a measurement can't tell you

Whether a sound reads as what it is. In cut 1 a generator sound measured fine and sounded like an alarm, and only the
owner could hear that.

- Use sounds recorded or designed as the thing they stand for, and name the files for what they are.
- Ask the owner to listen early: a 10-second test clip of the key sounds costs little.

## Sources

Every sound needs a license that allows its use in the video: your own recordings or synthesis, a library's terms,
or a royalty-free license. Keep a record of each source and its license beside the project. A platform's content ID
match on borrowed music can mute or demonetise a video.
