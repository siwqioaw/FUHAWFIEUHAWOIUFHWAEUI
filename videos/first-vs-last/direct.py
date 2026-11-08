"""Milestone M2, a comparison montage (family C, no voice): "First day of school VS Last day of school".

A header per side; three shots a side, each two beats of the track (80 BPM: 1.5 s), the second side outdoing the
first; a boom on the turn; a deadpan "Me" to close and loop. 30 fps, as the references' music formats are.

    python videos/first-vs-last/direct.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from shots import Spec, actor, dutch_in, hold, low, pull, push, shot, swoop, top, two_shot, wide  # noqa: E402

CLASS = (200.0, 0.0, 0.0)
BEAT = 0.75                      # "The Plan's Working", 80 BPM; the bed starts on a beat
s = Spec("first-vs-last", family="music", set="hallway", fps=30,
         title="First day of school VS Last day of school",
         cast={"leo": "me", "friend": "jock", "teacher": "teacher", "ex1": "extra_a", "ex2": "extra_b"},
         extra_sets=[("class", "classroom", CLASS, {"board": "Welcome, class!"})])
US = [0, 0, 1]

s.add(
    # first day: bright, eager
    shot("hello", {"leo": actor([0, 3, 0], facing=US, poses=[(0, "idle"), (0.1, "cheer")], faces=[(0, "grin")]),
                   "ex1": actor([-2.4, 3, -5], facing=[0.3, 0, 1], poses=[(0, "cheer")], faces=[(0, "smile")])},
         push("leo.head", 9.5, 6.0, fov=48), seconds=2 * BEAT),
    shot("hand_up", {"leo": actor([1.5, 3, 3], facing=[0, 0, -1], poses=[(0, "point")], faces=[(0, "starstruck")]),
                     "teacher": actor([-9, 3, -14.5], facing=US, faces=[(0, "smile")])},
         low("leo.head", distance=5.0, eye=2.4), set="class", seconds=2 * BEAT),
    shot("friends", {"leo": actor([-1.3, 3, 0], facing=US, poses=[(0, "hands_on_hips")], faces=[(0, "grin")]),
                     "friend": actor([1.3, 3, 0], facing=US, poses=[(0, "cheer")], faces=[(0, "laugh")])},
         two_shot("leo", "friend", distance=9.0, fov=50), seconds=2 * BEAT),
    # last day: everything worse, then absurd
    shot("asleep", {"leo": actor([1.5, 3, 3], facing=[0, 0, -1], poses=[(0, "slump")], faces=[(0, "sleepy")])},
         top("leo.torso", height=10.0), set="class", sfx=[("boom", 0.0)], seconds=2 * BEAT),
    shot("yelled", {"teacher": actor([-1.0, 3, 0.5], facing=[0.55, 0, 1], poses=[(0, "point")], faces=[(0, "yell")]),
                    "leo": actor([2.6, 3, 0.9], facing=[-0.45, 0, 1], poses=[(0, "slump")], faces=[(0, "dead")])},
         two_shot("teacher", "leo", distance=9.0, fov=50), set="class", seconds=2 * BEAT),   # turned to us: faces read
    shot("freedom", {"leo": actor([0, 3, -20], facing=US, poses=[(0, "cheer")], faces=[(0, "evil")],
                                  walk={"from": [0, 3, -24], "to": [0, 3, -16], "start": 0.0, "freq": 2.4}),
                     "ex2": actor([2.2, 3, -27], facing=[0, 0, 1], poses=[(0, "hands_on_head")], faces=[(0, "shock")])},
         dutch_in("leo.head", degrees=-14, start=10.0, end=6.5, move=0.4), seconds=2 * BEAT),
    shot("me", {"leo": actor([0, 3, 0], facing=US, poses=[(0, "arms_crossed")], faces=[(0, "deadpan")])},
         push("leo.head", 6.0, 4.4, move=0.3), seconds=2 * BEAT),
)
s.text("{yellow:First} day of school..", 0.0, 3 * 2 * BEAT, style="header")
s.text("{red:Last} day of school..", 3 * 2 * BEAT, 6 * 2 * BEAT, style="header")
s.text("Me:", 6 * 2 * BEAT, 7 * 2 * BEAT, style="header")
s.music("build/library/music/the_plans_working.mp3", start=0.0, gain_db=-1.0, offset=22.74, duck=False)

if __name__ == "__main__":
    print(s.write(HERE))
