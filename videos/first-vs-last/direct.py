"""Milestone M2, a comparison montage (family C, no voice): "First day of school VS Last day of school".

A header per side; three shots a side, the second side outdoing the first; a boom on the turn; "Me:" to close and
loop. 30 fps, as the references' music formats are.

The cuts land on the track's accents, measured (its review found the first cut missed them): "The Plan's Working",
from 22.74 s in, is 120 BPM in 4/4 with its accents 3-3-2 in each 2 s bar, at +0, +0.75 and +1.5 s from 1.28 s.
So the cuts are at 1.28, 2.78, 4.78 (the turn, the boom carrying it), 6.03, 7.28 and 8.78 s (the track's two biggest
hits), and the video is 10.0 s, five bars, so the loop comes round on the beat.

    python videos/first-vs-last/direct.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from shots import Spec, actor, low, push, shot, top, two_shot, wide  # noqa: E402

CLASS = (200.0, 0.0, 0.0)
FPS = 30
CUTS = [0, 38, 83, 143, 181, 218, 263, 300]   # frames: the accents at 1.28, 2.78, 4.78, 6.03, 7.28, 8.78; 10.0 s


def length(i):
    return (CUTS[i + 1] - CUTS[i]) / FPS


s = Spec("first-vs-last", family="music", set="hallway", fps=FPS,
         title="First day of school VS Last day of school",
         cast={"leo": "me", "friend": "jock", "teacher": "teacher", "ex1": "extra_a", "ex3": "extra_c",
               "nar": "narrator"},
         extra_sets=[("class", "classroom", CLASS, {"board": "Welcome, class!"})])
US, TO_BOARD = [0, 0, 1], [0, 0, -1]
POINT_AT = {"rs": (90, 52, 0), "ls": (0, 0, -4), "neck": (0, 28, 0)}   # facing the camera, pointing off to its left
TIRED = {"root": (-6, 0, 0), "neck": (-10, 0, 0), "ls": (4, 0, -2), "rs": (4, 0, 2)}   # the face still seen
ARMS_UP = {"ls": (176, 0, -8), "rs": (176, 0, 8), "neck": (14, 0, 0)}   # a cheer narrow enough for two in a frame

s.add(
    # first day: bright, eager
    shot("hello", {"leo": actor([0, 3, 0], facing=US, poses=[(0, "idle"), (0.1, "wave")], faces=[(0, "grin")])},
         push("leo.head+[-0.9,0.3,0]", 10.0, 8.5, fov=48), seconds=length(0)),   # framed toward the waving hand
    shot("hand_up", {"leo": actor([6, 3, -1.9], facing=TO_BOARD, poses=[(0, "idle"), (0.05, "hand_up")],
                                  faces=[(0, "starstruck")]),   # at his desk (it hides his legs), front row
                     "ex3": actor([6, 3, 5.1], facing=TO_BOARD, faces=[(0, "bored")])},   # the row behind
         [{"t": 0, "pos": [0.4, 6.6, -11.0], "look": [6.0, 5.4, -1.9], "fov": 50},   # from the board's end, at his
          {"t": 0.04, "pos": [0.9, 6.5, -9.8], "look": [6.0, 5.4, -1.9], "fov": 50, "move": 0.3, "ease": "out"}],
         set="class", seconds=length(1)),   # eye height: the hand clears his head
    shot("friends", {"leo": actor([-2.2, 3, 0], facing=[0.2, 0, 1], poses=[(0, "cheer")], faces=[(0, "grin")]),
                     "friend": actor([2.2, 3, 0], facing=[-0.2, 0, 1], poses=[(0, "cheer")], faces=[(0, "laugh")])},
         two_shot("leo", "friend", distance=15.0, fov=56), seconds=length(2)),   # their high five meets, outer arms in
    # last day: everything worse, then absurd
    shot("asleep", {"leo": actor([-3, 3, 5.1], facing=TO_BOARD, poses=[(0, "slump")], faces=[(0, "sleepy")])},
         [{"t": 0, "aim": "leo.head+[0,0.1,0]", "distance": 7.5, "fov": 48, "orbit": 30},   # down the aisle:
          {"t": 0.04, "aim": "leo.head+[0,0.1,0]", "distance": 6.0, "fov": 48, "orbit": 30, "move": 0.4,
           "ease": "out"}], set="class", sfx=[("boom", 0.0)],   # straight on, a front-row chair filled the bottom
         overlays=[("\U0001F4A4", "leo.head", 0.2, {"size": 130, "lift": 1.2, "dur": 1.0})], seconds=length(3)),
    shot("yelled", {"teacher": actor([-2.4, 3, 0.8], facing=[0.2, 0, 1], poses=[(0, POINT_AT)], faces=[(0, "yell")]),
                    "leo": actor([2.3, 3, 0.2], facing=[-0.3, 0, 1], poses=[(0, TIRED)], faces=[(0, "dead")])},
         [{"t": 0, "pos": [-0.25, 4.9, 13.0], "look": [-0.25, 4.3, 0.5], "fov": 52}], set="class",
         seconds=length(4)),   # the point across the frame at him
    shot("freedom", {"leo": actor([0, 3, -12], facing=US, poses=[(0, "cheer")], faces=[(0, "evil")],
                                  walk={"from": [0, 3, -30], "to": [0, 3, -12], "start": 0.0, "freq": 3.4}),
                     "ex3": actor([4.4, 3, -26], facing=[-0.5, 0, 1], poses=[(0, "hands_on_head")],
                                  faces=[(0, "shock")])},   # a run the whole shot long, past her with room
         wide([0, 5.2, -3.5], [0, 4.2, -18], fov=55, push_in=1.5), seconds=length(5)),
    # Me: the channel's own narrator, wrecked on the first day while everyone else cheers
    shot("me", {"nar": actor([0, 3, 0], facing=US, poses=[(0, TIRED)], faces=[(0, "dead")]),
                "ex1": actor([-2.3, 3, -9.0], facing=US, poses=[(0, ARMS_UP)], faces=[(0, "grin")]),
                "friend": actor([2.3, 3, -9.6], facing=US, poses=[(0, ARMS_UP)], faces=[(0, "laugh")])},
         push("nar.face", 7.0, 6.2, fov=60, height=2.5, move=0.3), seconds=length(6)),   # from above: the
    # cheerers stand clear above his head, arms and all (level, their fists poked out of his hair)
)
s.text("{yellow:First} day of school..", 0.0, CUTS[3] / FPS, style="header")
s.text("{red:Last} day of school..", CUTS[3] / FPS, CUTS[6] / FPS, style="header")
s.text("Me:", CUTS[6] / FPS, CUTS[7] / FPS, style="header")
s.music("build/library/music/the_plans_working.mp3", start=0.0, gain_db=-1.0, offset=22.74, duck=False)

if __name__ == "__main__":
    print(s.write(HERE))
