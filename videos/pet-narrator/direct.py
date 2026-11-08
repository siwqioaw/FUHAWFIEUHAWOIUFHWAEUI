"""Milestone M5, the one-prompt run: "In this world, your pet narrates your life out loud" (the owner's own example
concept from docs/ROBLOX_SHORTS_PLAN.md), made by following skill/roblox-shorts from that one line.

Family B. Pets narrate their owners' lives; most brag; Max's dog only tells the truth (the mirror, the cartoon);
at the dance Max freezes, so the dog says it for him; the twist re-reads the whole video: the storyteller was the dog.
A speech bubble pops over a pet whenever it speaks: the rule's signature. Custom assets: blocky dogs and cats built
from code (tools/roblox/kit.py, dog and cat), a mirror with Max's reflection in it, a cartoon on the TV, the gym
dressed for the dance.

    python videos/pet-narrator/direct.py
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from shots import Spec, actor, push, shot, wide  # noqa: E402

HOME, LIVING, DANCE = (300.0, 0.0, 0.0), (600.0, 0.0, 0.0), (900.0, 0.0, 0.0)
SOUTH = [0, 0, -1]           # on the north lawn, facing the street
MAXDOG = {"color": [205, 150, 90], "spot": [240, 230, 215], "collar": [220, 50, 60]}


def head(x, z, facing, kind="dog"):
    """The point over a prop pet's head, for its speech bubble."""
    fx, fz = facing[0], facing[2]
    if kind == "dog":
        return [x + fx * 1.3, 2.7, z + fz * 1.3]
    return [x + fx * 0.25, 2.1, z + fz * 0.25]


# the living room: Max on the sofa, his dog on the floor by its end (on his old mark both stood in the coffee table)
SOFA = [0.0, 4.5, 8.3]                 # sofa_right's seat: the cushion is 2.5 up, so a sitter stands 1.5 higher
LDOG_AT, LDOG_FACING = [4.6, 0, 6.6], [-0.7, 0, -0.7]   # looking up at him by the sofa's end
LDOG = head(4.6, 6.6, LDOG_FACING)
BEG, BEG_FACING = [2.2, 3, 4.0], [1.49, 0, 1.69]   # by the sofa's end, facing his dog
PLEAD = {"ls": (74, 0, 26), "rs": (74, 0, -26), "neck": (-8, 0, 0)}   # hands together in front: please
SIT = "sit"

# the bedroom: Max at the mirror, his reflection in it (a second Max behind an open frame, his moves mirrored)
MIRROR_AT = [-3.0, 0, -1.2]         # clear of the desk chair (the reflection stood in its back)
MAX_M, REFL = [-3.0, 3, 1.5], [-3.0, 3, -3.9]
WAVE_L = {"ls": (140, 0, -30), "rs": (0, 0, 4), "neck": (0, 0, 6)}    # the wave mirrored: the other hand

# the gym, dressed for the dance
LILY = [-1.0, 3, -6.0]
MAXD = [2.2, 3, -3.2]                  # where Max stops, facing her
TO_LILY = [-0.75, 0, -0.66]
GDOG_AT, GDOG_FACING = [6.0, 0, -3.6], [-1, 0, -0.35]   # a step off his right hand (his arm was in its head)
GDOG = head(6.0, -3.6, GDOG_FACING)
PAIR = [3.5, 4.1, -3.6]                # between his head and the dog's, a little high: the two-shots aim here

PUMP = {"rs": (172, 0, 16), "ls": (6, 0, -4), "neck": (10, 0, 0)}   # a fist up on the pet's side: a two-arm
# cheer put the far hand off the frame's edge (M5's second review: "both cheers read as one arm")

street_props = [
    {"kind": "dog", "at": [-42, 0, 18], "facing": SOUTH, "color": [185, 185, 190], "spot": [250, 250, 250], "collar": [60, 120, 230]},
    {"kind": "cat", "at": [-24.6, 0, 18], "facing": SOUTH, "color": [230, 150, 70]},
    {"kind": "cat", "at": [9.4, 0, 18], "facing": SOUTH, "color": [90, 90, 100]},
    {"kind": "dog", "at": [25.8, 0, 18], "facing": SOUTH, "color": [60, 55, 55], "spot": [240, 240, 240], "collar": [250, 200, 40]},
    {"kind": "dog", "at": [45.8, 0, 18], "facing": SOUTH, **MAXDOG},
]
s = Spec("pet-narrator", family="story", set="street", set_options={"props": street_props},
         title="In this world, your pet narrates your life out loud", names=["Mia", "Jake"],
         cast={"max": "jock", "refl": "jock", "lily": "popular_girl", "girl1": "bestie", "ex1": "extra_a",
               "ex2": "extra_b", "ex3": "extra_c", "d1": "student_a", "d2": "student_c"},
         extra_sets=[("home", "bedroom", HOME, {"signs": False,   # its GAME ON poster sat under the mirror's captions
                                               "props": [{"kind": "mirror", "at": MIRROR_AT, "facing": [0, 0, 1],
                                                          "open_": True}]}),
                     ("living", "living_room", LIVING, {"tv": "bye bye,\nBUDDY...",   # the cartoon he cried at
                                                        "props": [{"kind": "dog", "at": LDOG_AT, "facing": LDOG_FACING,
                                                                   **MAXDOG}]}),
                     ("dance", "gym", DANCE, {"dance": True, "scoreboard": False,   # the school dance (it was a
                                              # daylit classroom); the scoreboard's writing would sit in the captions
                                              "props": [{"kind": "dog", "at": GDOG_AT, "facing": GDOG_FACING,
                                                         **MAXDOG}]})])
for ln in json.load(open(os.path.join(HERE, "lines.json"), encoding="utf-8")):
    s.line(ln["id"], ln["role"], ln["text"])


def bubble(over, at, size=210, dur=0.9, text=None):   # about a pet's head at 9 studs: the signature has to read
    return ("\U0001F4AC", over, at, {"size": size, "lift": 0.35, "dur": dur, **({"text": text} if text else {})})


DOG_A, CAT_A, CAT_B, DOG_B, DOG_MAX = (head(-42, 18, SOUTH), head(-24.6, 18, SOUTH, "cat"), head(9.4, 18, SOUTH, "cat"),
                                       head(25.8, 18, SOUTH), head(45.8, 18, SOUTH))

s.add(
    # -- A: the rule, on strangers' pets
    shot("rule", {"ex1": actor([-44, 3, 18.5], facing=SOUTH, poses=[(0, "arms_crossed")], faces=[(0, "proud")])},
         push([-43, 3.6, 18.3], 13.5, 10.5, fov=50, toward=[0, 0, -1]), say=[("a", 0.0)],
         sfx=[("pop", "a:pet", -10)], overlays=[bubble(DOG_A, "a:pet")], until="a:cats"),
    shot("cats", {"ex2": actor([-26, 3, 18.5], facing=SOUTH, faces=[(0, "smile")])},
         push([-25.3, 3.6, 18.3], 11.5, 9.2, fov=50, toward=[0.35, 0, -1]), sfx=[("pop", "a:cats", -10)],
         overlays=[bubble(CAT_A, "a:cats")],
         until="a:and"),
    shot("love", {"ex1": actor([-44, 3, 18.5], facing=SOUTH, poses=[(0, PUMP)], faces=[(0, "grin")])},
         push([-42.6, 3.6, 18.3], 11.5, 10.0, fov=50, toward=[-0.4, 0, -1]), sfx=[("pop", "a:love", -10)],
         overlays=[bubble(DOG_A, "a:love", 210)], until="a:because"),
    shot("brag", {"ex2": actor([-26, 3, 18.5], facing=SOUTH, poses=[(0, "hands_on_hips")], faces=[(0, "proud")])},
         push([-25.3, 4.0, 18.3], 7.0, 11.5, fov=50, toward=[0, 0, -1]),   # a pull back: its first frames had his
         sfx=[("pop", "a:brag", -10)], overlays=[bubble(CAT_A, "a:brag", 210)], until="a:end+0.04"),   # hair under the captions
    # -- B: the brags, then Max's dog
    shot("aced", {"girl1": actor([8, 3, 18.5], facing=SOUTH, poses=[(0, "arms_crossed")], faces=[(0, "proud")])},
         push([8.7, 3.6, 18.3], 12.5, 10.2, fov=50, toward=[-0.35, 0, -1]), say=[("b", "a:end+0.04")],   # clear of the car
         sfx=[("pop", "b:mia", -10)], overlays=[bubble(CAT_B, "b:mia", text="A+")], until="b:jake's"),   # its own
    # brag in its bubble: the storyteller reports it (the second review heard the storyteller's voice in this cat)
    shot("fastest", {"ex3": actor([24, 3, 18.5], facing=SOUTH, poses=[(0, PUMP)], faces=[(0, "starstruck")])},
         push([24.9, 3.6, 18.3], 12.5, 10.2, fov=50, toward=[-0.3, 0, -1]), sfx=[("pop", "b:jake's", -10)],
         overlays=[bubble(DOG_B, "b:jake's", text="#1")],
         until="b:but"),
    shot("max", {"max": actor([44, 3, 18.5], facing=SOUTH, faces=[(0, "nervous")])},
         push([44.9, 3.6, 18.3], 12.0, 9.2, fov=50, toward=[0, 0, -1]), sfx=[("pop", "b:truth", -10)],
         overlays=[bubble(DOG_MAX, "b:truth")],
         until="b:like"),
    # the mirror: over his shoulder, his reflection waving back; in on the reflection's cringe on "nine"
    shot("mirror", {"max": actor(MAX_M, facing=[0, 0, -1],
                                 poses=[(0, "idle"), ("b:hi", "wave"), ("b:nine", "idle")], faces=[(0, "grin")]),
                    "refl": actor(REFL, facing=[0, 0, 1],
                                  poses=[(0, "idle"), ("b:hi", WAVE_L), ("b:nine", "idle")],
                                  faces=[(0, "grin"), ("b:nine", "cringe")])},
         [{"t": 0, "pos": [-1.7, 5.3, 4.6], "look": [-3.2, 4.4, -3.9], "fov": 45},
          {"t": "b:nine", "pos": [-2.2, 5.0, 2.9], "look": [-3.2, 4.4, -3.9], "fov": 45, "move": 0.3, "ease": "out"}],
         set="home", until="b:or"),
    # the cartoon: over the sofa onto the TV, then his face
    shot("cartoon", {"max": actor(SOFA, facing=[0, 0, -1], poses=[(0, SIT)], faces=[(0, "cry")])},
         [{"t": 0, "pos": [1.6, 7.4, 13.6], "look": [-2.0, 4.4, -2.3], "fov": 50},
          {"t": 0.04, "pos": [1.4, 7.2, 12.8], "look": [-2.0, 4.4, -2.3], "fov": 50, "move": 0.9, "ease": "out"}],
         set="living", until="b:twice"),
    shot("twice", {"max": actor(SOFA, facing=[0, 0, -1], poses=[(0, SIT)], faces=[(0, "sob")])},
         [{"t": 0, "aim": "max.face+[0,0.6,0]", "distance": 3.6, "fov": 45, "orbit": -30}],
         set="living", until="b:max#2"),
    shot("begged", {"max": actor(BEG, facing=BEG_FACING, poses=[(0, PLEAD)], faces=[(0, "pout")])},
         wide([8.6, 5.0, 0.4], [3.15, 3.8, 4.85], fov=52), set="living", until="b:he#2"),
    shot("didnt", {},
         push([LDOG[0], 2.5, LDOG[2]], 5.6, 4.7, fov=50, height=0.0, toward=[-0.7, 0, -0.7]), set="living",
         sfx=[("pop", "b:didn't", -10)], overlays=[bubble(LDOG, "b:didn't", 220)], until="b:end+0.04"),
    # -- C: the dance, the dog speaks up, the reveal
    shot("dance", {"lily": actor(LILY, facing=[0.4, 0, 1], poses=[(0, "laugh")], faces=[(0, "laugh")]),
                   "girl1": actor([-3.2, 3, -8.6], facing=[0.3, 0, 1], poses=[(0, "laugh")], faces=[(0, "grin")]),
                   "ex1": actor([2.6, 3, -9.4], facing=[-0.3, 0, 1], poses=[(0, "cheer")], faces=[(0, "grin")]),
                   "ex3": actor([0.0, 3, -13.0], facing=[0, 0, 1], poses=[(0, "cheer")], faces=[(0, "starstruck")]),
                   "ex2": actor([-5.4, 3, -11.6], facing=[0.3, 0, 1], poses=[(0, "laugh")], faces=[(0, "laugh")])},
         wide([0.0, 8.0, 12.0], [-0.5, 3.8, -8.0], fov=58, push_in=3.0), set="dance", say=[("c", "b:end+0.04")],
         until="c:max"),
    shot("walk", {"max": actor(MAXD, facing=TO_LILY, faces=[(0, "nervous")],
                               walk={"from": [6.4, 3, 3.0], "to": MAXD, "start": 0.0}),
                  "lily": actor(LILY, facing=[0.75, 0, 0.66], faces=[(0, "smile")]),
                  "d1": actor([-8.5, 3, -6.5], facing=[1, 0, 0.2], poses=[(0, "cheer")], faces=[(0, "grin")]),
                  "d2": actor([-6.0, 3, -10.0], facing=[1, 0, 0.3], poses=[(0, "laugh")], faces=[(0, "laugh")])},
         wide([10.6, 5.4, 0.0], [0.4, 4.2, -4.4], fov=52), set="dance", until="c:and#1"),   # two more dancers
    # behind her: after the dance's wide the gym stood empty (the second review)   # from the side: from
    # the front, Lily cut from the dance's wide at 1.3x and 5 degrees round
    shot("froze", {"max": actor(MAXD, facing=TO_LILY, faces=[(0, "blank")], drift=0.0)},
         push("max.head+[0,0.6,0]", 4.6, 3.4, move=0.5), set="dance", drift=0.0, until="c:so"),
    shot("said_it", {"max": actor(MAXD, facing=TO_LILY, faces=[(0, "shock")])},
         [{"t": 0, "aim": PAIR, "distance": 9.9, "fov": 50, "toward": [-0.3, 0, -1]},
          {"t": 0.04, "aim": PAIR, "distance": 9.0, "fov": 50, "toward": [-0.3, 0, -1], "move": 0.6,
           "ease": "out"}], set="dance", sfx=[("pop", "c:dog", -10)],
         overlays=[bubble(GDOG, "c:dog", 210)], until="c:he#1"),
    shot("likes_you", {"lily": actor(LILY, facing=[0.75, 0, 0.66], faces=[(0, "shock"), ("c:september", "love")])},
         [{"t": 0, "pos": [6.4, 3.8, -3.5], "look": [-1.0, 4.3, -6.0], "fov": 45},   # over the dog's head at her
          {"t": 0.04, "pos": [6.0, 3.8, -3.65], "look": [-1.0, 4.3, -6.0], "fov": 45, "move": 1.2, "ease": "out"}],
         set="dance", sfx=[("pop", "c:he#1", -10), ("pop", "c:he's", -12)],
         overlays=[bubble(GDOG, "c:he#1", 200, 0.7), bubble(GDOG, "c:he's", 200, 1.0)], until="c:lily#2"),
    shot("smiled", {"lily": actor(LILY, facing=[0.75, 0, 0.66], faces=[(0, "love")]),
                    "max": actor(MAXD, facing=TO_LILY, faces=[(0, "wide_happy")])},
         [{"t": 0, "pos": [4.6, 5.0, -0.2], "look": [-1.0, 4.4, -6.0], "fov": 45}], set="dance",
         until="c:and#2"),   # over his shoulder: she smiles at him
    shot("honestly", {"max": actor(MAXD, facing=TO_LILY, faces=[(0, "wide_happy")])},
         [{"t": 0, "aim": PAIR, "distance": 9.9, "fov": 50, "toward": [-0.6, 0, -0.8]},
          {"t": 0.04, "aim": PAIR, "distance": 9.0, "fov": 50, "toward": [-0.6, 0, -0.8], "move": 0.6,
           "ease": "out"}], set="dance", sfx=[("pop", "c:honestly", -10)],
         overlays=[bubble(GDOG, "c:honestly", 220, 1.2)], until="c:best"),
    shot("me", {}, push(GDOG[:1] + [2.5] + GDOG[2:], 3.6, 2.9, fov=48, height=0.0, toward=[-0.6, 0, -1], move=0.6),
         set="dance", sfx=[("riser", "c:that's-1.15", -14), ("pop", "c:me", -8)],
         overlays=[("\U0001F4AC", GDOG, "c:me", {"size": 230, "lift": 0.2, "dur": 1.4})], until="c:end+0.35"),
)
s.music("build/library/music/lofi_bed.mp3", start=0.0, gain_db=-16.0, duck_db=-9.0)

if __name__ == "__main__":
    print(s.write(HERE))
