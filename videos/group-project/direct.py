"""Milestone M3, a rant (family A): "Nah, why does every group project have that ONE person?"

Three examples, a punch with a boom after each (the title page, the guy who left the chat on seen, the "WE" on
presentation day), and the narrator getting the same grade to end on. Written for teens: a roast of a type, never of a
real person. Run it to write short.json:

    python videos/group-project/direct.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from shots import Spec, actor, dutch_in, push, shot, two_shot  # noqa: E402

s = Spec("group-project", family="comedy", set="classroom",
         title="Why does every group project have THAT one person",
         set_options={"board": "GROUP PROJECT\n40 slides\nDue FRIDAY",
                      "no_chair": [[15, 10]],   # he stands at that desk to work: the chair would run through his legs
                      "props": [{"kind": "laptop", "at": [15, 2.675, 10.3], "facing": [0, 0, 1],
                                 "text": "Slide 40 / 40"}]},   # the work, on screen
         cast={"me": "narrator", "girl": "popular_girl", "jock": "jock", "nerd": "nerd", "ex3": "extra_c"})

s.line("l1", "narrator", "[excited] Nah, why does every group project have that ONE person?", emoji="\U0001F62D")
s.line("l2", "girl", "[bubbly] Oh my gosh, you guys, I'll do the title page!", emoji="✨")
s.line("l3", "narrator", "[sarcastic] The title page. For a forty slide project.", emoji="\U0001F480")
s.line("l4", "narrator", "[annoyed] Then there's this guy, who hasn't answered the group chat since September.",
       emoji="\U0001F644")
s.line("l5", "deep", "[deadpan] [deep voice] Seen.", emoji="\U0001F5FF")
s.line("l6", "narrator", "[frustrated] So I do the whole thing myself. Every single slide.", emoji="\U0001F62D")
s.line("l7", "narrator", "[annoyed] And on presentation day?", emoji="\U0001F440")
s.line("l8", "girl", "[confident] So, as WE researched...")
s.line("l9", "narrator", "[shouting] WE?!", emoji="\U0001F621")
s.line("l10", "narrator", "[frustrated] And we all get the same grade.", emoji="\U0001F940")

FRONT = [5, 3, -11]          # the narrator in front of the board, talking to us
GIRL = [-1.5, 3, -10.5]
JOCK = [1.5, 3, 3]           # standing asleep in the middle aisle
BOARD_GIRL, BOARD_ME = [-2.0, 3, -14], [2.4, 3, -14]   # 4.4 apart: at 3, her elbow went through his arm
TOWARD_US = [0, 0, 1]
TO_BOARD = [0, 0, -1]
DESK = [15, 3, 12.5]         # at the back desk by the window, the laptop in front of him
TYPE = {"ls": (60, 0, -4), "rs": (60, 0, 4), "neck": (-12, 0, 0)}   # hands at its keys, his head down to it

extras = {   # the class behind the jock, either side of his head (a back row showed only as half-faces at the edges)
    "ex3": actor([-0.6, 3, 7.4], facing=TO_BOARD, faces=[(0, "deadpan")]),     # 4.2 apart: at 3.6 their arms met
    "nerd": actor([3.6, 3, 7.9], facing=TO_BOARD, faces=[(0, "smile")]),   # a hand to his chin left the frame
}

s.add(
    shot("hook", {"me": actor([0.6, 3, -11.5], facing=TOWARD_US,
                              poses=[(0, "idle"), ("l1:why", "hands_on_head")],
                              faces=[(0, "side_eye"), ("l1:why", "cringe"), ("l1:one", "angry")])},
         [{"t": 0, "aim": "me.head", "distance": 14.0, "fov": 60, "height": -0.3},   # the board whole for "Nah,"
          {"t": "l1:why", "aim": "me.head", "distance": 7.6, "fov": 60, "height": -0.3, "move": 0.35, "ease": "out"}],
         say=[("l1", 0.0)], sfx=[("boom", "l1:end+0.04")], pad=0.18),   # in on "why", to his hands on his head
    shot("title_page", {"girl": actor(GIRL, facing=TOWARD_US, poses=[(0, "idle"), ("l2:title", "cheer")],
                                      faces=[(0, "grin"), ("l2:title", "starstruck")])},
         push("girl.head", 13.0, 11.6), say=[("l2", 0.05)], pad=0.15),   # her cheer's hands inside
    shot("forty", {"me": actor(FRONT, facing=TOWARD_US, poses=[(0, "idle")],
                               faces=[(0, "deadpan"), ("l3:forty", "side_eye")])},
         push("me.head", 5.6, 4.3, move=0.35), say=[("l3", 0.0)], sfx=[("boom", "l3:end+0.04")], pad=0.55),
    shot("the_chat", {**extras, "jock": actor(JOCK, facing=TO_BOARD, poses=[(0, "idle")], faces=[(0, "sleepy")])},
         push("jock.head", 12.0, 7.5, fov=50, height=-0.6, move=0.4), say=[("l4", 0.0)], pad=0.08),
    shot("seen", {"jock": actor(JOCK, facing=TO_BOARD, poses=[(0, "idle")],
                                faces=[(0, "sleepy"), ("l5:start", "deadpan")])},   # eyes open to say it
         push("jock.face+[0,-0.45,0]", 3.4, 2.8, move=0.3), say=[("l5", 0.08)], sfx=[("boom", "l5:end+0.02")],
         pad=0.6),
    shot("alone", {"me": actor(DESK, facing=TO_BOARD, poses=[(0, TYPE)], faces=[(0, "teary")])},
         [{"t": 0, "pos": [15.0, 5.7, 5.4], "look": [15.0, 4.3, 12.5], "fov": 50},   # alone at the back, typing
          {"t": 0.04, "pos": [15.0, 5.5, 6.4], "look": [15.0, 4.3, 12.5], "fov": 50, "move": 1.6, "ease": "out"}],
         say=[("l6", 0.0)], until="l6:every"),
    shot("slides", {"me": actor(DESK, facing=TO_BOARD, poses=[(0, TYPE), ("l6:slide", "slump", 0.3)],
                                faces=[(0, "cry")])},
         [{"t": 0, "pos": [16.0, 7.0, 15.0], "look": [15.0, 3.55, 9.3], "fov": 50},   # over his shoulder: the count
          {"t": 0.04, "pos": [15.8, 6.6, 14.2], "look": [15.0, 3.55, 9.3], "fov": 50, "move": 1.2, "ease": "out"}],
         until="l6:end+0.12"),
    shot("pres_day", {"girl": actor(BOARD_GIRL, facing=TOWARD_US, poses=[(0, "idle")], faces=[(0, "smug")]),
                      "me": actor(BOARD_ME, facing=TOWARD_US, poses=[(0, "idle")], faces=[(0, "side_eye_left")])},
         two_shot("girl", "me", distance=13.5, fov=50), say=[("l7", 0.0)], pad=0.1),
    shot("as_we", {"girl": actor(BOARD_GIRL, facing=TOWARD_US, poses=[(0, "idle")],   # as in the shot before
                                 faces=[(0, "smug"), ("l8:we", "proud")]),
                   "me": actor(BOARD_ME, facing=TOWARD_US, faces=[(0, "side_eye_left")])},
         push("girl.head", 7.0, 5.0), say=[("l8", 0.05)], pad=0.1),
    shot("we", {"me": actor(BOARD_ME, facing=TOWARD_US, poses=[(0, "lean_in")], faces=[(0, "furious")]),   # into
    # the lens (hands on his head showed in the push-in only as two slivers at the edges)
                "girl": actor(BOARD_GIRL, facing=TOWARD_US, faces=[(0, "smug")])},
         dutch_in("me.head", degrees=14, start=7.0, end=3.6, move=0.22), say=[("l9", 0.04)],
         sfx=[("boom", "l9:end+0.02")], pad=0.5),
    shot("grade", {"girl": actor([-2.6, 3, -12.5], facing=TOWARD_US, faces=[(0, "smug"), ("l10:we", "proud")]),
                   "jock": actor([2.6, 3, -12.5], facing=TOWARD_US, faces=[(0, "sleepy")]),   # asleep, an A
                   "me": actor([0.0, 3, -10.6], facing=TOWARD_US, faces=[(0, "side_eye"), ("l10:grade", "furious")])},
         [{"t": 0, "pos": [0.0, 6.5, 4.6], "look": [0.0, 4.6, -11.0], "fov": 60},   # a little high: their heads
          {"t": 0.04, "pos": [0.0, 6.5, 3.8], "look": [0.0, 4.6, -11.0], "fov": 60, "move": 1.0, "ease": "out"}],   # clear
         say=[("l10", 0.05)], pad=0.05,
         overlays=[(None, "girl.head", "l10:we", {"text": "A+", "size": 150, "lift": 1.3, "dur": 1.2}),
                   (None, "jock.head", "l10:same", {"text": "A+", "size": 150, "lift": 1.3, "dur": 1.0}),
                   (None, "me.head", "l10:grade", {"text": "A+", "size": 150, "lift": 1.3, "dur": 0.8})]),
    shot("dead", {"me": actor(BOARD_ME, facing=TOWARD_US, poses=[(0, "slump")], faces=[(0, "dead")])},
         push("me.head", 5.0, 3.8, move=0.5), sfx=[("boom", 0.0)], seconds=1.25),
)
s.music("build/library/music/comedy_bed.mp3", start=0.75, gain_db=-15.0, duck_db=-5.0)

if __name__ == "__main__":
    print(s.write(HERE))
