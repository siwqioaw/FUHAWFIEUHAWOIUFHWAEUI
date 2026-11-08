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
CAFE = (600.0, 0.0, 0.0)     # the new school's cafeteria
BLUE = [60, 110, 210]

s = Spec("ding", family="story", set="hallway", title="In this world, you hear a DING when someone talks about you",
         cast={"leo": "me", "her": "bestie", "pg": "popular_girl", "ex1": "extra_a", "ex2": "extra_b",
               "ex3": "extra_c", "jock": "jock", "nerd": "nerd", "sa": "student_a", "sb": "student_b",
               "sc": "student_c"},
         set_options={"signs": False},   # no writing in the sets: every one sat under the captions
         extra_sets=[("new_school", "hallway", NEW, {"lockers": BLUE, "signs": False,   # a bank to hide behind
                                                     "props": [{"kind": "lockers", "at": [-3.0, 0, 6.6],
                                                                "facing": [0, 0, 1], "n": 3, "color": BLUE}]}),
                     ("class", "classroom", CLASS, {"board": "", "signs": False}),
                     ("lunch", "cafeteria", CAFE, {"props": [{"kind": "tray", "at": [-12.0, 2.6, -6.2]}]})])
for ln in json.load(open(os.path.join(HERE, "lines.json"), encoding="utf-8")):
    s.line(ln["id"], ln["role"], ln["text"])

EX1, PG, EX2 = [-2.4, 3, 6.0], [0.6, 3, 10.0], [3.0, 3, 8.5]   # the rule's first instance: inside the frame,
PG_TO, EX2_TO = [0.85, 0, -0.53], [-0.85, 0, 0.53]   # the gossips turned to each other (side by side at 3.4, both
#                                                    leaning in, their arms met)
US = [0, 0, 1]
L, R = [1, 0, 0], [-1, 0, 0]      # facing +x (from the left lockers) and -x (from the right)
BELL = {"size": 150}


def bell(over, at, size=150, lift=1.5, dur=0.7):
    return ("bell", over, at, {"size": size, "lift": lift, "dur": dur})


SIT = {"lh": (90, 0, 0), "rh": (90, 0, 0), "ls": (12, 0, -3), "rs": (12, 0, 3), "rootpos": (0, -0.5, 0)}
SIT_SLUMP = {**SIT, "root": (-9, 0, 0), "neck": (-28, 0, 0), "ls": (8, 0, -2), "rs": (8, 0, 2)}
SIT_WHISPER = {**SIT, "root": (-10, -24, 0), "neck": (8, -22, 0), "ls": (20, 0, -8), "rs": (20, 0, 8)}  # to her right
PEEK = {"root": (-6, 0, 14), "neck": (4, 0, 10), "ls": (26, 0, -10), "rs": (10, 0, 8)}   # leaning out to his left
SEAT = -7.65                 # the far bench of the cafeteria's first table (kit.cafeteria, mark "seat_far")


s.add(
    # -- A: the rule, shown on strangers; Leo has never heard a ding
    shot("world", {"ex1": actor(EX1, facing=[0.25, 0, -1], faces=[(0, "smile"), ("a:every", "confused")]),
                   "pg": actor(PG, facing=PG_TO, poses=[(0, "lean_in")], faces=[(0, "scheming")]),
                   "ex2": actor(EX2, facing=EX2_TO, poses=[(0, "lean_in")], faces=[(0, "side_eye_left")])},
         wide([0.0, 6.0, -5], [0, 4.2, 8], fov=58, push_in=2.0), say=[("a", 0.0)], until="a:talks",
         sfx=[("ding", "a:every", -3)], overlays=[bell("ex1.head", "a:every", 130)]),   # shown before it's told
    shot("whisper", {"pg": actor(PG, facing=PG_TO, poses=[(0, "lean_in")], faces=[(0, "scheming")]),
                     "ex2": actor(EX2, facing=EX2_TO, poses=[(0, "lean_in")], faces=[(0, "side_eye_left")])},
         two_shot("pg", "ex2", distance=7.0, fov=50), until="a:you#2"),
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
                   "ex3": actor([-1.9, 3, -2.6], facing=[0.4, 0, 1], poses=[(0, "laugh")], faces=[(0, "laugh")]),
                   "jock": actor([2.2, 3, -4.6], facing=[-0.4, 0, 1], poses=[(0, "cheer")], faces=[(0, "grin")])},
         two_shot("ex3", "jock", distance=11.0, fov=52), until="a:end+0.04"),   # staggered: side by side they met
    # -- B: a new school, and the dings start
    shot("switch", {"leo": actor([-4.6, 3, -26], facing=[0.3, 0, 1], faces=[(0, "nervous")],
                                 walk={"from": [-4.6, 3, -32.5], "to": [-4.6, 3, -26], "start": 0.0})},
         wide([2.0, 5.0, -16.5], [-4.2, 4.0, -29.0], fov=55), set="new_school", say=[("b", "a:end+0.04")],
         until="b:and"),   # walking in along the new school's blue lockers
    shot("first", {"leo": actor([0, 3, -24], facing=US, faces=[(0, "nervous"), ("b:ding", "shock")])},
         push("leo.head", 7.0, 4.6), set="new_school", sfx=[("ding", "b:ding")],
         overlays=[bell("leo.head", "b:ding")], until="b:then#2"),
    shot("twenty", {"leo": actor([0, 3, -24], facing=US, poses=[(0, "idle"), ("b:twenty", "hands_on_head")],
                                 faces=[(0, "shock"), ("b:twenty", "scared")])},
         [{"t": 0, "aim": "leo.head", "distance": 7.5, "fov": 50, "height": -1.6},   # low and frontal: the hands on
          {"t": 0.05, "aim": "leo.head", "distance": 5.4, "fov": 50, "height": -1.6, "dutch": -12, "move": 0.3,
           "ease": "inout"}], set="new_school",   # his head frame his face (at 35 degrees round, one covered it)
         sfx=[("ding", "b:two", -1), ("ding", "b:more", -1)] + [("ding", f"b:twenty+{k * 0.07:.2f}", -3) for k in range(6)],
         overlays=[bell("leo.head+[0.9,0.1,0]", "b:two", 110), bell("leo.head+[-0.9,0.3,0]", "b:more", 110)]
         + [bell(f"leo.head+[{dx},{dy},0]", f"b:twenty+{k * 0.07:.2f}", 95)
            for k, (dx, dy) in enumerate([(1.4, 0.6), (-1.4, 0.9), (0.4, 1.4), (-0.6, -0.2), (1.1, -0.4), (-1.2, -0.5)])],
         until="b:every#1"),
    shot("past", {"leo": actor([0, 3, -12], facing=US, faces=[(0, "nervous")],
                               walk={"from": [0, 3, -14], "to": [0, 3, -5], "start": 0.0}),
                  "sa": actor([-4.3, 3, -8.0], facing=[0.7, 0, 0.7], faces=[(0, "side_eye")]),     # 4.3 off his
                  "sb": actor([4.3, 3, -6.5], facing=[-0.7, 0, 0.7], faces=[(0, "side_eye_left")]),  # path: at 2.7
                  "nerd": actor([4.5, 3, -12.8], facing=[-0.7, 0, 0.7], faces=[(0, "sus")])},       # he went through
         wide([0, 6.5, 9.0], [0, 3.8, -10], fov=62), set="new_school", until="b:ding#2"),
    shot("dingding", {"leo": actor([0, 3, -5], facing=US, poses=[(0, "hands_on_head")], faces=[(0, "scared")])},
         push("leo.face", 4.5, 3.0, move=0.4), set="new_school",
         sfx=[("ding", "b:ding#2", 1), ("ding", "b:ding#3", 1), ("ding", "b:ding#4", 1)],
         overlays=[bell("leo.head+[1.0,0.2,0]", "b:ding#2", 120), bell("leo.head+[-1.0,0.4,0]", "b:ding#3", 120),
                   bell("leo.head+[0,0.6,0]", "b:ding#4", 130)],
         until="b:so"),
    shot("stopped", {"leo": actor([-6.0, 3, 2], facing=L, poses=[(0, "slump")], faces=[(0, "sad")])},
         push("leo.head", 6.5, 4.8, move=0.5), set="new_school", until="b:he#3"),
    shot("lunch", {"leo": actor([-12.0, 3, SEAT], facing=[0, 0, 1], poses=[(0, SIT_SLUMP)], faces=[(0, "sad")]),
                   "sa": actor([-9.1, 3, -10.9], facing=[1, 0, 0], poses=[(0, "laugh")], faces=[(0, "laugh")]),
                   "sb": actor([-6.9, 3, -10.9], facing=[-1, 0, 0], poses=[(0, "cheer")], faces=[(0, "grin")])},
         [{"t": 0, "pos": [-10.5, 4.4, 1.6], "look": [-10.5, 3.9, -8.6], "fov": 56}], set="lunch",
         until="b:he#4"),
    shot("home", {"leo": actor([2.5, 3, 18], facing=[0, 0, 1], faces=[(0, "sad")],
                                walk={"from": [2.5, 3, 10], "to": [2.5, 3, 18], "start": 0.0})},
         wide([2.5, 5.0, 2.5], [2.5, 3.5, 18], fov=50), set="new_school", until="b:end+0.04"),
    # -- C: the twist
    shot("month", {"leo": actor([1.5, 3, 3], facing=[0, 0, -1], poses=[(0, "slump")], faces=[(0, "sad")])},
         push("leo.head", 9.0, 7.0, height=1.0, move=0.9), set="class", say=[("c", "b:end+0.04")],
         until="c:until"),
    shot("loud", {"leo": actor([2.5, 3, -4], facing=US, poses=[(0, "hands_on_head")],
                               faces=[(0, "scared"), ("c:loud", "furious")])},
         [{"t": 0, "aim": "leo.head", "distance": 9.0, "fov": 55, "height": -2.2, "orbit": 30},
          {"t": 0.04, "aim": "leo.head", "distance": 6.4, "fov": 55, "height": -2.2, "orbit": 30, "dutch": 14,
           "move": 0.4, "ease": "out"}], set="new_school",
         sfx=[("ding", f"c:dings+{k * 0.18:.2f}", 2) for k in range(9)],
         overlays=[bell(f"leo.head+[{dx},{dy},0]", f"c:dings+{k * 0.18:.2f}", 100)
                   for k, (dx, dy) in enumerate([(1.2, 0.4), (-1.2, 0.6), (0.3, 1.3), (-0.4, -0.3), (1.3, -0.5),
                                                 (-1.3, -0.6), (0.9, 1.0), (-0.9, 1.1), (0.0, 0.2)])],
         until="c:so#2"),
    shot("hid", {"leo": actor([-1.2, 3, 4.6], facing=[0.35, 0, 1], poses=[(0, PEEK)], faces=[(0, "nervous")])},
         [{"t": 0, "pos": [0.6, 4.6, 11.0], "look": [-0.45, 4.4, 4.8], "fov": 45}], set="new_school",
         until="c:the#3"),   # from the girls' side: the bank hides him but his head round its end
    shot("quote", {"her": actor([5.0, 3, 8.5], facing=[-1, 0, -0.3], poses=[(0, "idle"), ("c:funny", "laugh")],
                                faces=[(0, "laugh"), ("c:why", "cute")]),
                   "sc": actor([6.6, 3, 11.6], facing=[-1, 0, -0.6], faces=[(0, "grin")])},   # clear of her arm
         [{"t": 0, "pos": [1.0, 4.6, 6.2], "look": [5.8, 4.3, 10.0], "fov": 55}], set="new_school",
         until="c:the#4"),   # from the bank's end, where he listens (the two-shot put the camera inside the bank)
    shot("rule", {"leo": actor([-1.2, 3, 4.6], facing=[0.35, 0, 1], poses=[(0, "idle")],
                               faces=[(0, "teary"), ("c:bad", "wide_happy")])},
         [{"t": 0, "aim": "leo.face", "distance": 2.8, "fov": 45, "toward": [0.85, 0, 0.5]},
          {"t": 0.04, "aim": "leo.face", "distance": 5.5, "fov": 45, "toward": [0.85, 0, 0.5], "move": 0.5,
           "ease": "out"}], set="new_school",
         sfx=[("shimmer", "c:bad", -9)], until="c:the#5"),   # the shimmer after the quotable line, not over it
    shot("sat", {"leo": actor([-7.6, 3, SEAT], facing=[0, 0, 1], poses=[(0, "idle"), (0.95, SIT, 0.35)],
                              faces=[(0, "nervous"), ("c:down", "grin")],
                              walk={"from": [-3.8, 3, SEAT], "to": [-7.6, 3, SEAT], "start": 0.0}),
                 "her": actor([-12.0, 3, SEAT], facing=[0, 0, 1], poses=[(0, SIT)], faces=[(0, "cute")])},
         [{"t": 0, "pos": [-5.6, 4.3, 2.0], "look": [-9.6, 3.6, SEAT], "fov": 56}], set="lunch",
         until="c:the#6"),
    shot("her", {"leo": actor([-7.6, 3, SEAT], facing=[0, 0, 1], poses=[(0, SIT)],
                              faces=[(0, "grin"), ("c:ding", "starstruck")]),
                 "her": actor([-12.0, 3, SEAT], facing=[0, 0, 1], poses=[(0, SIT), ("c:loudest", SIT_WHISPER, 0.25)],
                              faces=[(0, "cute"), ("c:loudest", "love")])},   # whispering to someone off to her right
         [{"t": 0, "pos": [-10.2, 4.0, 3.2], "look": [-10.2, 4.0, SEAT], "fov": 60},
          {"t": 0.04, "pos": [-10.2, 4.0, 2.4], "look": [-10.2, 4.0, SEAT], "fov": 60, "move": 1.6, "ease": "out"}],
         set="lunch", sfx=[("riser", "c:the#6", -10), ("ding", "c:ding", 5)],
         overlays=[bell("leo.head", "c:ding", 210, lift=1.7, dur=1.6)], until="c:end+0.12"),   # his bell: from her
)
s.music("build/library/music/story_bed.mp3", start=0.0, gain_db=-16.0, duck_db=-9.0)   # under the soft lines

if __name__ == "__main__":
    print(s.write(HERE))
