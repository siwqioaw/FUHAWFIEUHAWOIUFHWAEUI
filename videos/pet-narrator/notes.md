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
