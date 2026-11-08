# The reviewer's brief

Step 8 of the run: a fresh agent reviews the delivered file. Give it this brief with the blanks filled, and nothing
of your own opinion of the video: no "I think the bubbles work", no list of what you already fixed. Run it in the
background while you do something else; it takes 20-30 minutes. Don't re-plan or re-deliver the video while it works:
it reads `plan.json` and `cut.json`, and a newer one than the file confuses it.

Every first review of the first four videos found real must-fix problems that every automated check had passed
(bells off the frame, cuts off the beat, a camera inside a car, an actor's elbow through another's arm), and the
second rounds found lines not shown in the picture and a speaker hidden behind its owner. A later round gets the
earlier reviews too (`videos/<slug>/review.md`), to check the fixes hold and look past them. Fix what it
finds, write `videos/<slug>/review.md` (each finding, its cause, its fix or why it stays), and add every new kind of
failure to `checklist.md`.

```
You are an independent reviewer of a finished vertical YouTube Short (1080x1920, <FPS> fps, about <LENGTH> s) made
by an automated pipeline in the repository <REPO>, for a teen audience (13-17; the channel is set as not made for
kids). It's <ONE PARAGRAPH: the format, the premise, who acts it out where, the voice, the captions, the rule's
signature or the jokes, the music>. Review the delivered file against the checklist and report every failure with
evidence. You can't watch or listen, so measure, and look at still frames (the Read tool shows you a PNG/JPG).

Do not change any file outside a folder you create, build/review/<slug>/. Don't run Roblox Studio, don't regenerate
audio, don't re-run the pipeline's stages (make.py), don't commit, don't upload anything.

The files (made today; the video at about <TIME>):
- The delivered file: out/<slug>.mp4
- Its timeline: build/<slug>/cut.json (clips in frames, played back to back; "texts" the captions; "cues" the
  sounds placed; "hits")
- The plan it was rendered from: build/<slug>/plan.json
- The script and direction: videos/<slug>/short.json, videos/<slug>/direct.py, videos/<slug>/notes.md
- The voice report and word times: build/<slug>/voice/report.md, build/<slug>/voice/words.json
- The automated reports already run on the delivered file: build/<slug>/verify/
- The checklists: skill/roblox-shorts/checklist.md, docs/VERIFY.md ("the checklist"), docs/LESSONS.md,
  skill/roblox-shorts/formats/<format>.md
- The rules: CLAUDE.md, section "Rules"; ATTRIBUTION.md

How to look and measure:
- A full-size frame at time T: ffmpeg -v error -ss T -i out/<slug>.mp4 -frames:v 1 build/review/<slug>/t_T.png
- The frames around every cut: python tools/verify/sheets.py cuts out/<slug>.mp4 --timeline build/<slug>/cut.json
  --out build/review/<slug>/cuts
- A strip: python tools/verify/sheets.py strip out/<slug>.mp4 --from A --to B --step 2 --out build/review/<slug>/strips
- The checks again: python tools/verify/qc.py out/<slug>.mp4 --timeline build/<slug>/cut.json --out
  build/review/<slug> ; python tools/verify/audio.py build/<slug>/cut.json out/<slug>.mp4 --out build/review/<slug>
- Caption pace: python tools/verify/caption_pace.py out/<slug>.mp4 --words <transcript json> --band <0.15 0.36 for
  stories, 0.70 0.86 for comedy>
- ffprobe/ffmpeg are on the PATH; Python has numpy, PIL, soundfile, opencv, scipy. PYTHONIOENCODING=utf-8 to print.

Check every item in skill/roblox-shorts/checklist.md and docs/VERIFY.md's checklist with evidence, and also: <THE
FORMAT'S OWN QUESTIONS: does the first second state the premise; does every icon appear over the right head, when it
should, on screen, its subject visible; do the cuts land on the music's beats; does the twist land; does it loop>; is
each caption the script's words, in time with the voice (not before it), never over a face; does each face and pose
change land on its word; are the right people in each shot and in frame, with every gesture inside the frame; does
every line's action show in the picture; is any actor inside another or inside furniture; is anything wrong at any
cut (a stray or doubled frame, a jump cut, a camera inside something, a loading texture); is the music under the
voice; is anything a logo, a brand or someone else's content; is it suitable for teens.

Report: first the findings, each marked must-fix, should-fix or nit, with the time or frame, what you saw (and which
frame file shows it), and the checklist item it fails. Then a short list of what you checked and found fine. Keep
the report under 700 words. Report what you see, not what you expect to see.
```
