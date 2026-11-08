# pet-narrator: notes

Milestone M5, the one-prompt run, 2026-11-08. The prompt was the owner's own example concept from the plan:

```
/roblox-shorts In this world, your pet narrates your life out loud
```

Everything after that line followed `skill/roblox-shorts` without questions: concept tests, script, direction, a new
custom asset (the pets), voice, plan, stills, shoot, cut, mix, deliver, review. Times per stage are at the end.

## The premise tests (`writing/concepts.md`)

| Test | Result |
|---|---|
| Shown in 2 s | yes: a pet beside its owner with a speech bubble over its head as the line is said |
| Benefit becomes cost | yes: pets brag about their owners; an honest pet tells everything |
| One loophole | do goldfish count? do pets lie? (the script names goldfish to start the argument) |

Scored 21 of 24 (universal 3, visual 3, quotable 2, escalation 3, twist 3, loop 2, original 3, safe 3). A topic
prompt would have generated ten; a premise this strong goes straight to the tests.

## The pick

- **Logline:** every pet narrates its owner's life out loud; most brag, but Max's dog only tells the truth (the
  mirror practice, crying at a cartoon, twice); at the dance Max freezes in front of Lily, so his dog says it for him.
  The twist re-reads the whole video: the storyteller was the dog ("That's me, by the way.").
- **Quotable:** "That's me, by the way."
- **Hidden detail:** the classroom board says SCHOOL DANCE!; every owner's pet has its own colour and collar.
- **Loop:** the dog's last line leads back into "In this world, every pet narrates..."; we now know who's talking.

## Custom assets made for it

- **Pets:** `kit.dog` and `kit.cat`, blocky R6-scale animals from parts (body, legs, paws, head, snout, nose, bead
  eyes with catchlights, ears, collar, tail), placed by any set's `props` option. Five dogs and cats on the street,
  Max's dog (brown, white muzzle, red collar) in the bedroom, the living room and the dance.
- **The rule's signature:** a speech bubble icon popping over the pet as it speaks (`overlays`).
- **Bed:** a warm, playful lo-fi track made with ElevenLabs music through the connector.

## Decisions

- One storyteller (Liam at 1.2x), three parts generated whole; the pets' brags in the storyteller's voice with
  `[warmly]`, as the references keep characters in the narrator's voice.
- Four places in one shoot: the street (main), Max's bedroom, the living room, the school dance in the classroom.
- The brags name the owners ("Mia aced her math test. Jake's the fastest kid in school."): the first version opened
  line b on "She aced", and both takes read it as "He aced" (heard that way on the raw takes too, the "sh" faint at
  the line's start). Regenerated with names: every check passes, and each brag lands on a name as its bubble pops.
  The spec lists `names=["Mia", "Jake"]` so captions keep their capitals.
- The street's owners stand 18 studs apart, too far for one portrait frame (the plan's framing check: "never in
  frame"), so "And most people love it, | because their pets brag about them all day" is two shots, cut on
  "because": a low angle on the dog's owner cheering, then a pull-back from the cat's proud owner.
- The bubble over Max's dog shows only when it speaks ("He didn't."), not while Max begs.

## What the run found in the tools

M5 is the run the skill was built for, so its failures went back into the tools rather than around them: a pause
the voice chain left at 38-42 dB under (cut now), a soft first consonant (the transcriber hears a padded copy), new
takes downloaded under old names (named by the take now), captions breaking on "a" and "the" (split by phrase now),
and actors out of the narrow frame (the plan warns). Each is in `skill/roblox-shorts/checklist.md` and the selftest.

## Time, stage by stage

Measured on this machine (Windows, Studio on its own monitor, the transcriber on the CPU). The first M5 run was also
the run that found the tools' faults, so the fixes' time (hours) isn't a stage of a normal run and isn't counted.

| Stage | Time | Measured from |
|---|---|---|
| Concept, tests, script | about 4 min after the libraries' commit (03:13 to 03:17) | file times: `lines.json` 03:17 |
| Voice: three lines, two takes each, through the connector | seconds a line | the connector |
| Music bed (ElevenLabs music) | seconds | `lofi_bed.mp3` 03:21 |
| Direction (`direct.py`): 20 shots, four sets, props, bubbles | about 25 min, alongside other work | file times |
| Voice processing and checks | 192 s (6 s from the cache) | `make.py voice` |
| Plan | 8-9 s | `make.py plan` |
| Stills: 20 shots, then 12 restaged, then 3 | 470 + 273 + 96 s | `make.py stills` |
| Shoot: 1794 frames at 60 fps | 3159 s (52.7 min, 1.76 s a frame with staging) | `make.py shoot` |
| Cut, mix, deliver (every check) | 171 + 9 + 129 s | `make.py cut`, `mix`, `deliver` |
| Independent review | about 25 min | the reviewer agent |

So a 30-second story is about two and a half hours from the prompt to a reviewed file: an hour of it the shoot, half
an hour looking at stills and restaging, half an hour of review; the writing is the shortest part.
