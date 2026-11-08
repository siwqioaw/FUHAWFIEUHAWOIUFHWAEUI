# "In this world, [rule]" (family B)

**Use when** the concept is a rule of the world that is visible in 2 s, whose benefit becomes its cost, with one
loophole to argue about. 4 of 9 passed 1M views; the longest still spread.

**Length** 30-36 s; 140-160 words at 4.2-4.7 a second, no silence; a new framing every 1.0-1.4 s (cut on the first
word of a clause); 20-28 shots. **Captions:** story style, high, 1-3 words. One storyteller (`story` role) reads
everything, characters' lines included. 60 fps.

## Beat table (as a share of the length)

| Share | Beat | How |
|---|---|---|
| 0-13% | the rule | the first sentence, the title; shown at once on strangers with the rule's visual signature (an icon, a flash, a colour) |
| 13-24% | the price or the dread | the catch, shown on an extra |
| 20-25% | the hero | named; with the person who matters |
| about 41% | the rule fires on the hero | the signature, louder |
| 41-68% | a false high, or the cost piling up | |
| 58-68% | the reversal | "But", "Then", "Until" |
| about 85% | the twist | the rule, one step deeper, re-reads what we've seen; one fast sentence; the biggest sound after it |
| last 0.3 s | the end | the rule's visual on the last word; stop |

## Shots that work

- `shot(..., until="b:WORD")`: each shot ends on the word that starts the next clause.
- `swoop(a, b)` to whoever is named, landing on the name; `pull("hero.face", ...)` for realisations; `ots(near, far)`
  for overhearing; `dutch_in` or a low angle for panic; `wide(...)` + `walk` for passing time. Loneliness: alone at a
  long cafeteria table (`sit`), not `top(...)`: from above, R6s are hair and shoulders (M2 and M4's reviews).
- Overlays (`overlays=[("bell", "leo.head", "b:ding")]`) for the rule's signature, with a matching effect: over the
  one the rule acts on (the person talked about, the pet that speaks), and that one in the picture, not behind
  someone (M5's dog stood behind its owner and its bubble came out of his shirt; the plan warns now). In a
  close-up the icon goes beside the head, not on it.
- Show the rule in the first second, before the narrator explains it (M4's first bell came at 3 s); every line's
  action in the picture (the new school's own lockers, hiding behind a bank of `lockers`, sitting down).
- Several places: `extra_sets=[("new_school", "hallway", (400, 0, 0), {...})]` and `set="new_school"` per shot.

## Sound plan

One bed for the whole story (`story_bed`: wistful synthwave) at -16 dB ducked 9 dB (at 4 the sad, soft lines sat
only 6 dB over it); a sound for each state of the rule (a ding, a shimmer, a thud), louder as the story says louder
(M4's dings measured quieter as the line said "so loud": set the gains to climb); a riser into the twist; nothing on
the quotable line itself (the shimmer after it); the last sound on the last word, the loudest.

## Example skeleton (original)

`videos/ding/direct.py`: "In this world, every time someone talks about you behind your back, you hear a ding." Leo
has never heard one; a new school is all dings; he shuts everyone out; he overhears them: "The new kid is SO funny.
Why won't he sit with us?"; the rule never said it had to be bad; the loudest ding comes from her.

## Rubric

The rule shown in 2 s; benefit becomes cost; one loophole; the hero named by 25%; the twist from the rule at about 85%;
no silence; the last image is the rule's visual; teen-safe.
