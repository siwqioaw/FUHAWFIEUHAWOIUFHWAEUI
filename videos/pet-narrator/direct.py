"""Milestone M5, the one-prompt run: "In this world, your pet narrates your life out loud" (the owner's own example
concept from docs/ROBLOX_SHORTS_PLAN.md), made by following skill/roblox-shorts from that one line.

Family B. Pets narrate their owners' lives; most brag; Max's dog only tells the truth (the mirror, the cartoon);
at the dance Max freezes, so the dog says it for him; the twist re-reads the whole video: the storyteller was the dog.
A speech bubble pops over a pet whenever it speaks: the rule's signature. Custom assets: blocky dogs and cats built
from code (tools/roblox/kit.py, dog and cat).

    python videos/pet-narrator/direct.py
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from shots import Spec, actor, dutch_in, hold, low, ots, pull, push, shot, top, two_shot, wide  # noqa: E402

HOME, LIVING, DANCE = (300.0, 0.0, 0.0), (600.0, 0.0, 0.0), (900.0, 0.0, 0.0)
SOUTH = [0, 0, -1]           # on the north lawn, facing the street
MAXDOG = {"color": [205, 150, 90], "spot": [240, 230, 215], "collar": [220, 50, 60]}


def head(x, z, facing, kind="dog"):
    """The point over a prop pet's head, for its speech bubble."""
    fx, fz = facing[0], facing[2]
    if kind == "dog":
        return [x + fx * 1.3, 2.7, z + fz * 1.3]
    return [x + fx * 0.25, 2.1, z + fz * 0.25]


street_props = [
    {"kind": "dog", "at": [-42, 0, 18], "facing": SOUTH, "color": [185, 185, 190], "spot": [250, 250, 250], "collar": [60, 120, 230]},
    {"kind": "cat", "at": [-24.6, 0, 18], "facing": SOUTH, "color": [230, 150, 70]},
    {"kind": "cat", "at": [9.4, 0, 18], "facing": SOUTH, "color": [90, 90, 100]},
    {"kind": "dog", "at": [25.8, 0, 18], "facing": SOUTH, "color": [60, 55, 55], "spot": [240, 240, 240], "collar": [250, 200, 40]},
    {"kind": "dog", "at": [45.8, 0, 18], "facing": SOUTH, **MAXDOG},
]
s = Spec("pet-narrator", family="story", set="street", set_options={"props": street_props},
         title="In this world, your pet narrates your life out loud", names=["Mia", "Jake"],
         cast={"max": "jock", "lily": "popular_girl", "girl1": "bestie", "ex1": "extra_a", "ex2": "extra_b",
               "ex3": "extra_c"},
         extra_sets=[("home", "bedroom", HOME, {"props": [{"kind": "dog", "at": [2.0, 0, 3.5], "facing": [-1, 0, 0], **MAXDOG}]}),
                     ("living", "living_room", LIVING, {"props": [{"kind": "dog", "at": [-0.2, 0, 4.0], "facing": [-1, 0, -0.4], **MAXDOG}]}),
                     ("dance", "classroom", DANCE, {"board": "SCHOOL DANCE!",
                                                    "props": [{"kind": "dog", "at": [5.4, 0, -5.4], "facing": [-1, 0, -0.35], **MAXDOG}]})])
for ln in json.load(open(os.path.join(HERE, "lines.json"), encoding="utf-8")):
    s.line(ln["id"], ln["role"], ln["text"])


def bubble(over, at, size=210, dur=0.9):   # about a pet's head at 9 studs: the rule's signature has to read
    return ("\U0001F4AC", over, at, {"size": size, "lift": 0.35, "dur": dur})


DOG_A, CAT_A, CAT_B, DOG_B, DOG_MAX = (head(-42, 18, SOUTH), head(-24.6, 18, SOUTH, "cat"), head(9.4, 18, SOUTH, "cat"),
                                       head(25.8, 18, SOUTH), head(45.8, 18, SOUTH))
LIVING_DOG = head(-0.2, 4.0, [-1, 0, -0.4])
DANCE_DOG = head(5.4, -5.4, [-1, 0, -0.35])   # beside Max, not in him (its head was on his mark)

s.add(
    # -- A: the rule, on strangers' pets
    shot("rule", {"ex1": actor([-44, 3, 18.5], facing=SOUTH, poses=[(0, "hands_on_hips")], faces=[(0, "proud")])},
         push([-43, 3.6, 18.3], 12.5, 9.5, fov=50, toward=[0, 0, -1]), say=[("a", 0.0)],
         sfx=[("pop", "a:pet", -10)], overlays=[bubble(DOG_A, "a:pet")], until="a:cats"),
    shot("cats", {"ex2": actor([-26, 3, 18.5], facing=SOUTH, faces=[(0, "smile")])},
         push([-25.3, 3.6, 18.3], 11.5, 9.2, fov=50, toward=[0.35, 0, -1]), sfx=[("pop", "a:cats", -10)],
         overlays=[bubble(CAT_A, "a:cats")],
         until="a:and"),
    shot("love", {"ex1": actor([-44, 3, 18.5], facing=SOUTH, poses=[(0, "cheer")], faces=[(0, "grin")])},
         push([-42.6, 3.7, 18.3], 10.5, 9.0, fov=50, toward=[-0.4, 0, -1]), sfx=[("pop", "a:love", -10)],
         overlays=[bubble(DOG_A, "a:love", 210)], until="a:because"),
    shot("brag", {"ex2": actor([-26, 3, 18.5], facing=SOUTH, poses=[(0, "hands_on_hips")], faces=[(0, "proud")])},
         pull([-25.3, 3.6, 18.3], 7.0, 9.5, fov=50, toward=[0, 0, -1]),
         sfx=[("pop", "a:brag", -10)], overlays=[bubble(CAT_A, "a:brag", 210)], until="a:end+0.04"),
    # -- B: the brags, then Max's dog
    shot("aced", {"girl1": actor([8, 3, 18.5], facing=SOUTH, poses=[(0, "hands_on_hips")], faces=[(0, "proud")])},
         push([8.7, 3.6, 18.3], 11.5, 9.2, fov=50, toward=[-0.35, 0, -1]), say=[("b", "a:end+0.04")],   # clear of the car
         sfx=[("pop", "b:mia", -10)], overlays=[bubble(CAT_B, "b:mia")], until="b:jake's"),
    shot("fastest", {"ex3": actor([24, 3, 18.5], facing=SOUTH, poses=[(0, "cheer")], faces=[(0, "starstruck")])},
         push([24.9, 3.6, 18.3], 11.5, 9.2, fov=50, toward=[-0.3, 0, -1]), sfx=[("pop", "b:jake's", -10)],
         overlays=[bubble(DOG_B, "b:jake's")],
         until="b:but"),
    shot("max", {"max": actor([44, 3, 18.5], facing=SOUTH, faces=[(0, "nervous")])},
         push([44.9, 3.6, 18.3], 12.0, 9.2, fov=50, toward=[0, 0, -1]), sfx=[("pop", "b:truth", -10)],
         overlays=[bubble(DOG_MAX, "b:truth")],
         until="b:like"),
    shot("mirror", {"max": actor([-6.5, 3, 1.5], facing=[0, 0, -1], poses=[(0, "idle"), ("b:hi", "wave")],
                                 faces=[(0, "grin"), ("b:nine", "cringe")])},
         push("max.head", 5.2, 4.2, move=0.4), set="home", until="b:or"),
    shot("cartoon", {"max": actor([-2, 3, 3], facing=[0, 0, -1], poses=[(0, "idle")], faces=[(0, "cry")])},
         [{"t": 0, "aim": "max.head+[0,0.2,0]", "distance": 7.5, "fov": 48, "height": -0.3, "orbit": 40},
          {"t": 0.04, "aim": "max.head+[0,0.2,0]", "distance": 6.6, "fov": 48, "height": -0.3, "orbit": 40,
           "move": 0.4, "ease": "out"}], set="living", until="b:twice"),
    shot("twice", {"max": actor([-2, 3, 3], facing=[0, 0, -1], poses=[(0, "slump")], faces=[(0, "sob")])},
         [{"t": 0, "aim": "max.face+[0,0.25,0]", "distance": 2.8, "fov": 45, "height": -0.2, "orbit": -35}],
         set="living", until="b:max#2"),
    shot("begged", {"max": actor([-2, 3, 3], facing=[1, 0, 0.4], poses=[(0, "hands_on_head")], faces=[(0, "pout")])},
         wide([2.4, 3.6, 6.8], [-1.6, 4.0, 3.2], fov=52), set="living", until="b:he#2"),
    shot("didnt", {},
         push([LIVING_DOG[0], 2.5, LIVING_DOG[2]], 5.6, 4.7, fov=50, height=0.0, toward=[-1, 0, -0.4]), set="living",
         sfx=[("pop", "b:didn't", -10)], overlays=[bubble(LIVING_DOG, "b:didn't", 220)], until="b:end+0.04"),
    # -- C: the dance, the dog speaks up, the reveal
    shot("dance", {"lily": actor([0, 3, -8], facing=[0, 0, 1], poses=[(0, "laugh")], faces=[(0, "laugh")]),
                   "ex1": actor([-5, 3, -6], facing=[0.3, 0, 1], poses=[(0, "cheer")], faces=[(0, "grin")]),
                   "ex2": actor([1.5, 3, -11], facing=[-0.3, 0, 1], poses=[(0, "laugh")], faces=[(0, "laugh")]),
                   "ex3": actor([-3, 3, -11], facing=[0, 0, 1], poses=[(0, "cheer")], faces=[(0, "starstruck")]),
                   "girl1": actor([-7, 3, -9], facing=[0.3, 0, 1], poses=[(0, "laugh")], faces=[(0, "grin")])},
         wide([7.5, 7.0, 6.0], [-1.5, 3.8, -8], fov=58, push_in=3.0), set="dance", say=[("c", "b:end+0.04")],
         until="c:max"),
    shot("walk", {"max": actor([2.4, 3, -6.6], facing=[-1, 0, -0.6], faces=[(0, "nervous")],
                               walk={"from": [6.8, 3, -1.2], "to": [2.6, 3, -6.4], "start": 0.0}),
                  "lily": actor([0, 3, -8], facing=[1, 0, 0.6], faces=[(0, "smile")])},
         wide([6.5, 5.0, 3.5], [1.2, 3.8, -7], fov=50), set="dance", until="c:and#1"),
    shot("froze", {"max": actor([2.6, 3, -6.4], facing=[-1, 0, -0.6], faces=[(0, "blank")], drift=0.0)},
         push("max.head", 4.6, 3.4, move=0.5), set="dance", drift=0.0, until="c:so"),
    shot("said_it", {"max": actor([2.6, 3, -6.4], facing=[-1, 0, -0.3], faces=[(0, "shock")])},
         push([3.4, 3.75, -6.2], 9.5, 8.0, fov=50, toward=[-1, 0, -0.1]), set="dance", sfx=[("pop", "c:dog", -10)],
         overlays=[bubble(DANCE_DOG, "c:dog", 210)], until="c:he#1"),
    shot("likes_you", {"lily": actor([0, 3, -8], facing=[1, 0, 0.6], faces=[(0, "shock"), ("c:september", "love")])},
         push("lily.head+[0,0.3,0]", 6.0, 4.6), set="dance", until="c:lily#2"),
    shot("smiled", {"lily": actor([0, 3, -8], facing=[0.5, 0, 1], poses=[(0, "idle")], faces=[(0, "love")]),
                    "max": actor([2.4, 3, -6.8], facing=[-0.5, 0, 1], faces=[(0, "wide_happy")])},
         wide([1.2, 5.2, 1.0], [1.2, 5.4, -7.4], fov=50), set="dance", until="c:and#2"),
    shot("honestly", {"max": actor([2.6, 3, -6.4], facing=[-1, 0, -0.3], faces=[(0, "wide_happy")])},
         push([3.4, 3.8, -6.2], 9.0, 7.5, fov=50, toward=[-1, 0, -0.1]), set="dance", sfx=[("pop", "c:honestly", -10)],
         overlays=[bubble(DANCE_DOG, "c:honestly", 220, 1.2)], until="c:best"),
    shot("me", {}, push(DANCE_DOG[:1] + [2.5] + DANCE_DOG[2:], 3.6, 2.7, fov=48, height=0.0, toward=[-0.6, 0, -1],
                        move=0.6), set="dance", sfx=[("pop", "c:me")],
         overlays=[("\U0001F4AC", DANCE_DOG, "c:me", {"size": 230, "lift": 0.2, "dur": 1.4})], until="c:end+0.35"),
)
s.music("build/library/music/lofi_bed.mp3", start=0.0, gain_db=-16.0, duck_db=-9.0)

if __name__ == "__main__":
    print(s.write(HERE))
