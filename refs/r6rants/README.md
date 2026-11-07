# Reference set: @r6rants, 16 Shorts over 1M views

The owner's study set for the Roblox shorts skill: every Short from the channel @r6rants with more than a million
views when it was collected (16 of 51, 2026-11-06). `index.md` lists them with views, dates and links.

**These are someone else's work.** They're here to be measured and studied, so that original videos can be made with
the same craft. Never reuse their footage, sound, characters, jokes or scripts, and never commit the videos.

| Folder | What | In git |
|---|---|---|
| `videos/` | the 16 MP4s, from the owner's zip (`r6rants-top-shorts.zip`) | no (ignored) |
| `transcripts/` | words with times, from `tools/verify/transcribe.py` (speech-to-text run on this PC) | yes |
| `measurements/` | `analyze.py` numbers per video, and `summary.md` | yes |
| `notes/` | one study note per video, written to `refs/NOTES_TEMPLATE.md` | yes |
| `listener/` | what a listener hears, per video, from `docs/prompts/listener-pass.md` (filed 2026-11-07; checked in `SYNTHESIS.md`) | yes |
| `SYNTHESIS.md` | what the 16 have in common, and the targets that follow | yes |

The sheets the notes cite (`build/analysis/r6rants/`, `build/study/r6rants/`) are generated and not committed.
Remake them with:

```
python tools/verify/analyze.py refs/r6rants/videos/*.mp4 --out build/analysis/r6rants
python tools/verify/transcribe.py refs/r6rants/videos/*.mp4 --out refs/r6rants/transcripts --device cpu
python tools/verify/study.py refs/r6rants/videos/*.mp4 --out build/study/r6rants --words refs/r6rants/transcripts --analysis build/analysis/r6rants
```

(In PowerShell, pass the files as `(Get-ChildItem refs\r6rants\videos\*.mp4).FullName`.)
