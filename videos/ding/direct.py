"""Milestone M4, an "In this world" story (family B): every time someone talks about you behind your back, you hear a
ding.

The rule shown on strangers in the first seconds; a false high (Leo has never heard one); the rule's cost (a new
school full of dings, so he shuts everyone out); the twist from the rule itself (it never said it had to be bad); the
loudest ding last, from her. One storyteller, no silence, high 1-3 word captions, one bed, a ding for every ding.

    python videos/ding/direct.py
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from shots import Spec, actor, dutch_in, hold, low, ots, pull, push, shot, swoop, top, two_shot, wide  # noqa: E402

NEW = (400.0, 0.0, 0.0)      # the new school: the same hallway with blue lockers
CLASS = (200.0, 0.0, 0.0)    # a classroom

s = Spec("ding", family="story", set="hallway", title="In this world, you hear a DING when someone talks about you",
         cast={"leo": "me", "her": "bestie", "pg": "popular_girl", "ex1": "extra_a", "ex2": "extra_b",
               "ex3": "extra_c", "jock": "jock", "nerd": "nerd", "sa": "student_a", "sb": "student_b",
               "sc": "student_c"},
         extra_sets=[("new_school", "hallway", NEW, {"lockers": [60, 110, 210]}),
                     ("class", "classroom", CLASS, {"board": "Welcome back!"})])
for ln in json.load(open(os.path.join(HERE, "lines.json"), encoding="utf-8")):
    s.line(ln["id"], ln["role"], ln["text"])

EX1, PG, EX2 = [-2.4, 3, 6.0], [0.6, 3, 9.9], [3.2, 3, 7.7]   # the rule's first instance: inside the frame,
#                                                              the gossips side by side as the camera sees them
US = [0, 0, 1]
L, R = [1, 0, 0], [-1, 0, 0]      # facing +x (from the left lockers) and -x (from the right)
BELL = {"size": 150}


def bell(over, at, size=150, lift=1.5, dur=0.7):
    return ("bell", over, at, {"size": size, "lift": lift, "dur": dur})


s.add(
    # -- A: the rule, shown on strangers; Leo has never heard a ding
    shot("world", {"ex1": actor(EX1, facing=[0.25, 0, -1], faces=[(0, "smile")]),
                   "pg": actor(PG, facing=[-0.55, 0, -0.85], poses=[(0, "lean_in")], faces=[(0, "scheming")]),
                   "ex2": actor(EX2, facing=[-0.75, 0, -0.65], poses=[(0, "lean_in")], faces=[(0, "side_eye_left")])},
         wide([0.0, 6.0, -5], [0, 4.2, 8], fov=58, push_in=2.0), say=[("a", 0.0)], until="a:talks"),
    shot("whisper", {"pg": actor(PG, facing=[-0.55, 0, -0.85], poses=[(0, "lean_in")], faces=[(0, "scheming")]),
                     "ex2": actor(EX2, facing=[-0.75, 0, -0.65], poses=[(0, "lean_in")], faces=[(0, "side_eye_left")])},
         two_shot("pg", "ex2", distance=7.5, fov=50), until="a:you#2"),
    shot("ding", {"ex1": actor(EX1, facing=[0.25, 0, -1], faces=[(0, "smile"), ("a:ding", "shock")])},
         push("ex1.head", 7.0, 4.8), sfx=[("ding", "a:ding")], overlays=[bell("ex1.head", "a:ding")], until="a:most"),
    shot("few", {"ex2": actor([2.6, 3, -5.5], facing=[-0.4, 0, 1], faces=[(0, "nervous")]),
                 "jock": actor([-2.8, 3, -8.5], facing=[0.4, 0, 1], faces=[(0, "side_eye")]),
                 "ex3": actor([0.6, 3, -13], facing=US, faces=[(0, "confused")])},
         wide([0, 7.5, 6], [0, 4, -9], fov=55, push_in=2.0),
         sfx=[("ding", "a:people", -5), ("ding", "a:few", -5), ("ding", "a:day", -5)],
         overlays=[bell("ex2.head", "a:people", 110), bell("jock.head", "a:few", 110), bell("ex3.head", "a:day", 100)],
         until="a:leo"),
    shot("leo", {"leo": actor([0, 3, 0], facing=US, poses=[(0, "hands_on_hips")], faces=[(0, "grin")])},
         push("leo.head", 8.5, 5.0), until="a:not"),
    shot("liked", {"leo": actor([0, 3, 0], facing=US, poses=[(0, "laugh")], faces=[(0, "laugh")]),
                   "ex3": actor([-2.3, 3, -2.2], facing=[0.4, 0, 1], poses=[(0, "laugh")], faces=[(0, "laugh")]),
                   "jock": actor([2.3, 3, -2.2], facing=[-0.4, 0, 1], poses=[(0, "cheer")], faces=[(0, "grin")])},
         two_shot("ex3", "jock", distance=11.0, fov=52), until="a:end+0.04"),
    # -- B: a new school, and the dings start
    shot("switch", {"leo": actor([0, 3, -30], facing=US, faces=[(0, "nervous")],
                                 walk={"from": [0, 3, -32], "to": [0, 3, -25], "start": 0.0})},
         wide([2.5, 5.5, -16], [0, 4, -28], fov=50), set="new_school", say=[("b", "a:end+0.04")], until="b:and"),
    shot("first", {"leo": actor([0, 3, -24], facing=US, faces=[(0, "nervous"), ("b:ding", "shock")])},
         push("leo.head", 7.0, 4.6), set="new_school", sfx=[("ding", "b:ding")],
         overlays=[bell("leo.head", "b:ding")], until="b:then#2"),
    shot("twenty", {"leo": actor([0, 3, -24], facing=US, poses=[(0, "idle"), ("b:twenty", "hands_on_head")],
                                 faces=[(0, "shock"), ("b:twenty", "scared")])},
         [{"t": 0, "aim": "leo.head", "distance": 7.0, "fov": 48, "orbit": 35},
          {"t": 0.05, "aim": "leo.head", "distance": 4.4, "fov": 48, "orbit": 35, "dutch": -12, "move": 0.3,
           "ease": "inout"}], set="new_school",
         sfx=[("ding", "b:two", -3), ("ding", "b:more", -3)] + [("ding", f"b:twenty+{k * 0.07:.2f}", -7) for k in range(6)],
         overlays=[bell("leo.head+[0.9,0.1,0]", "b:two", 110), bell("leo.head+[-0.9,0.3,0]", "b:more", 110)]
         + [bell(f"leo.head+[{dx},{dy},0]", f"b:twenty+{k * 0.07:.2f}", 95)
            for k, (dx, dy) in enumerate([(1.4, 0.6), (-1.4, 0.9), (0.4, 1.4), (-0.6, -0.2), (1.1, -0.4), (-1.2, -0.5)])],
         until="b:every#1"),
    shot("past", {"leo": actor([0, 3, -12], facing=US, faces=[(0, "nervous")],
                               walk={"from": [0, 3, -14], "to": [0, 3, -5], "start": 0.0}),
                  "sa": actor([-2.6, 3, -7], facing=[0.7, 0, 0.7], faces=[(0, "side_eye")]),
                  "sb": actor([2.8, 3, -9.5], facing=[-0.7, 0, 0.7], faces=[(0, "side_eye_left")]),
                  "nerd": actor([-2.9, 3, -11.5], facing=[0.7, 0, 0.7], faces=[(0, "sus")])},
         wide([0, 6.0, 4], [0, 3.8, -10], fov=55), set="new_school", until="b:ding#2"),
    shot("dingding", {"leo": actor([0, 3, -5], facing=US, poses=[(0, "hands_on_head")], faces=[(0, "scared")])},
         push("leo.face", 4.5, 3.0, move=0.4), set="new_school",
         sfx=[("ding", "b:ding#2"), ("ding", "b:ding#3"), ("ding", "b:ding#4")],
         overlays=[bell("leo.head+[1.0,0.2,0]", "b:ding#2", 120), bell("leo.head+[-1.0,0.4,0]", "b:ding#3", 120),
                   bell("leo.head+[0,0.6,0]", "b:ding#4", 130)],
         until="b:so"),
    shot("stopped", {"leo": actor([-6.0, 3, 2], facing=L, poses=[(0, "slump")], faces=[(0, "sad")])},
         push("leo.head", 6.5, 4.8, move=0.5), set="new_school", until="b:he#3"),
    shot("lunch", {"leo": actor([1.5, 3, 3], facing=[0, 0, -1], poses=[(0, "slump")], faces=[(0, "sad")])},
         top("leo.torso", height=9.0, fov=60), set="class", until="b:he#4"),
    shot("home", {"leo": actor([0, 3, 10], facing=[0, 0, 1], faces=[(0, "sad")],
                                walk={"from": [0, 3, 6], "to": [0, 3, 14], "start": 0.0})},
         wide([0, 5.0, -2], [0, 3.5, 14], fov=50), set="new_school", until="b:end+0.04"),
    # -- C: the twist
    shot("month", {"leo": actor([1.5, 3, 3], facing=[0, 0, -1], poses=[(0, "slump")], faces=[(0, "sad")])},
         push("leo.head", 9.0, 7.0, height=1.0, move=0.9), set="class", say=[("c", "b:end+0.04")],
         until="c:until"),
    shot("loud", {"leo": actor([0, 3, 0], facing=US, poses=[(0, "hands_on_head")], faces=[(0, "scared"), ("c:loud", "furious")])},
         dutch_in("leo.head", degrees=14, start=6.5, end=3.8, move=0.35), set="new_school",
         sfx=[("ding", f"c:dings+{k * 0.18:.2f}", -6) for k in range(9)],
         overlays=[bell(f"leo.head+[{dx},{dy},0]", f"c:dings+{k * 0.18:.2f}", 100)
                   for k, (dx, dy) in enumerate([(1.2, 0.4), (-1.2, 0.6), (0.3, 1.3), (-0.4, -0.3), (1.3, -0.5),
                                                 (-1.3, -0.6), (0.9, 1.0), (-0.9, 1.1), (0.0, 0.2)])],
         until="c:so#2"),
    shot("hid", {"leo": actor([-6.0, 3, 4], facing=L, poses=[(0, "lean_in")], faces=[(0, "nervous")]),
                 "her": actor([5.0, 3, 8.5], facing=[-1, 0, -0.3], faces=[(0, "smile")]),
                 "sc": actor([5.6, 3, 10.6], facing=[-1, 0, -0.6], faces=[(0, "grin")])},
         low("leo.head", distance=4.5, eye=2.2), set="new_school", until="c:the#3"),
    shot("quote", {"leo": actor([-6.0, 3, 4], facing=[1, 0, 0.5], poses=[(0, "lean_in")], faces=[(0, "nervous")]),
                   "her": actor([5.0, 3, 8.5], facing=[-1, 0, -0.3], poses=[(0, "idle"), ("c:funny", "laugh")],
                                faces=[(0, "laugh"), ("c:why", "cute")]),
                   "sc": actor([5.6, 3, 10.6], facing=[-1, 0, -0.6], faces=[(0, "grin")])},
         two_shot("her", "sc", distance=7.5, fov=50), set="new_school", until="c:the#4"),
    shot("rule", {"leo": actor([-6.0, 3, 4], facing=L, poses=[(0, "idle")],
                               faces=[(0, "teary"), ("c:bad", "wide_happy")])},
         pull("leo.face", 2.6, 6.5, move=0.5), set="new_school", sfx=[("shimmer", "c:never", -2)], until="c:the#5"),
    shot("sat", {"leo": actor([2.9, 3, -4], facing=US, faces=[(0, "grin")],
                              walk={"from": [6.5, 3, -4], "to": [2.9, 3, -4], "start": 0.0}),
                 "her": actor([0.4, 3, -4], facing=US, faces=[(0, "cute")]),
                 "sc": actor([-2.4, 3, -4.6], facing=US, faces=[(0, "grin")])},
         two_shot("her", "leo", distance=10.5, fov=52), set="class", until="c:the#6"),
    shot("her", {"her": actor([0.4, 3, -4], facing=US, faces=[(0, "cute"), ("c:ding", "love")])},
         [{"t": 0, "aim": "her.head", "distance": 7.0, "fov": 45, "height": -0.3, "orbit": -30},
          {"t": 0.04, "aim": "her.head", "distance": 4.6, "fov": 45, "height": -0.3, "orbit": -30, "move": 0.35,
           "ease": "out"}], set="class", sfx=[("riser", "c:the#6", -10), ("ding", "c:ding", 3)],
         overlays=[bell("her.head", "c:ding", 210, lift=1.7, dur=2.5)], until="c:end+0.3"),
)
s.music("build/library/music/story_bed.mp3", start=0.0, gain_db=-15.0, duck_db=-4.0)

if __name__ == "__main__":
    print(s.write(HERE))
