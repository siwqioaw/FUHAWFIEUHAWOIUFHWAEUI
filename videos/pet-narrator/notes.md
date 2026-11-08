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
