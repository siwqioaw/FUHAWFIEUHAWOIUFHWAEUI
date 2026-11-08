# Rant: "Why do [group] do this" (family A)

**Use when** the concept is a type of person everyone knows, with habits to roast (popular girls, little brothers,
group-project slackers, substitute teachers). 4 of 8 of the channel's rants passed 1M views.

**Length** 22-30 s; 65-95 words at 2.9-3.6 a second with pauses as beats; a new framing every 1.6-2.5 s; 10-14
shots. **Captions:** comedy style, a clause each, CAPS on stressed words, one emoji at the end. 60 fps.

## Beat table

| Time | Beat | Picture | Sound |
|---|---|---|---|
| 0.0-0.5 | the premise | the narrator alone, a strong pose snapping to another on the first stressed word; push-in | the first line from frame 1; no music yet |
| 0.5-3.5 | the premise lands | his face swaps on the type's name; a swoop or cut to the type | music enters at about 0.75 s; boom after the line |
| 3.5-10 | example 1 | the type does the thing (their line, in their voice); the narrator's retort, close | boom after the retort |
| 10-17 | example 2 | bigger; a figure of speech shown literally; a deep-voice one-word punch | boom |
| 17-25 | example 3 | the worst one; the narrator's outburst (dutch, furious face) | boom; music may drop for the gag |
| last 1-2 s | the narrator escalates | his fate: dead face, a top-down, a hard cut | final boom, cut mid-boom |

## Shots that work

- `push("me.head", 13, 6)` opening wide on what the rant is about (M3's board, whole, then him); `push(..., 5.6, 4.3,
  move=0.35)` for a retort's slow push; `dutch_in(..., 14)` for the outburst, the body leaning into the lens
  (`lean_in`: hands on the head show only as slivers at a close-up's edges); `low(target)` for the type looking big;
  `two_shot(a, b)` for the setup, 4.4 studs apart or more; `pull("me.face", 3.4, 7, move=0.7)` for a sad reveal (a
  fast pull reads as a whip).
- Faces: smug or side-eye on setups, angry/furious on the stressed word, deadpan on retorts, dead at the end.
- Comedy captions sit low (70-86% of the height): frame faces above 66%, and the "Seen."-type close-up higher still
  so the caption clears the chin. A back row of extras at a push-in's edges shows only as half-faces: keep the class
  either side of the subject's head, inside the frame.

## Sound plan

The comedy bed (pizzicato and marimba, about 104 BPM) from 0.75 s at -15 dB, ducked 5 dB under the voice; a boom
after every punch; pops or whooshes on swoops if the shot needs them.

## Example skeleton (original)

`videos/group-project/direct.py`: "Nah, why does every group project have that ONE person?" The title page, the guy
who left the chat on "Seen.", "So, as WE researched..." / "WE?!", and the same grade for everyone.

## Rubric (score before the shoot)

Premise in the first second; three examples that escalate; a punch every 2-8 s with a boom; at least one deep or
one-word punch; a face change on nearly every line; a literal visual for each figure of speech; a hidden detail in
the set; ends on the narrator, cut hard.
