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
from shots import Spec, actor, dutch_in, hold, low, pull, push, shot, two_shot  # noqa: E402

s = Spec("group-project", family="comedy", set="classroom",
         title="Why does every group project have THAT one person",
         set_options={"board": "GROUP PROJECT\n40 slides\nDue FRIDAY"},
         cast={"me": "narrator", "girl": "popular_girl", "jock": "jock", "teacher": "teacher",
               "nerd": "nerd", "ex3": "extra_c"})

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
TEACH = [-9, 3, -14.5]
BOARD_GIRL, BOARD_ME = [-2.0, 3, -14], [2.4, 3, -14]   # 4.4 apart: at 3, her elbow went through his arm
TOWARD_US = [0, 0, 1]
TO_BOARD = [0, 0, -1]

extras = {   # the class behind the jock, either side of his head (a back row showed only as half-faces at the edges)
    "ex3": actor([-0.3, 3, 7.4], facing=TO_BOARD, faces=[(0, "deadpan")]),
    "nerd": actor([3.3, 3, 7.4], facing=TO_BOARD, faces=[(0, "smile")], poses=[(0, "think")]),
}

s.add(
    shot("hook", {"me": actor([0.6, 3, -11.5], facing=TOWARD_US,
                              poses=[(0, "idle"), ("l1:why", "hands_on_head")],
                              faces=[(0, "smug"), ("l1:one", "angry")])},
         push("me.head", 13.0, 6.2, move=0.35), say=[("l1", 0.0)], pad=0.18),
    shot("title_page", {"girl": actor(GIRL, facing=TOWARD_US, poses=[(0, "idle"), ("l2:title", "cheer")],
                                      faces=[(0, "grin"), ("l2:title", "starstruck")])},
         push("girl.head", 11.0, 9.4), say=[("l2", 0.05)], pad=0.15),
    shot("forty", {"me": actor(FRONT, facing=TOWARD_US, poses=[(0, "idle")],
                               faces=[(0, "deadpan"), ("l3:forty", "side_eye")])},
         push("me.head", 5.6, 4.3, move=0.35), say=[("l3", 0.0)], sfx=[("boom", "l3:end+0.04")], pad=0.55),
    shot("the_chat", {**extras, "jock": actor(JOCK, facing=TO_BOARD, poses=[(0, "idle")], faces=[(0, "sleepy")])},
         push("jock.head", 12.0, 7.5, fov=50, height=-0.6, move=0.4), say=[("l4", 0.0)], pad=0.08),
    shot("seen", {"jock": actor(JOCK, facing=TO_BOARD, poses=[(0, "idle")], faces=[(0, "sleepy")])},
         push("jock.face+[0,-0.45,0]", 3.4, 2.8, move=0.3), say=[("l5", 0.08)], sfx=[("boom", "l5:end+0.02")],
         pad=0.6),
    shot("alone", {"me": actor([10.5, 3, -4], facing=[-1, 0, 0], poses=[(0, "facepalm"), ("l6:every", "slump")],
                               faces=[(0, "teary"), ("l6:every", "cry")])},
         pull("me.face", 3.4, 7.0, move=0.7), say=[("l6", 0.0)], pad=0.12),
    shot("pres_day", {"girl": actor(BOARD_GIRL, facing=TOWARD_US, poses=[(0, "idle")], faces=[(0, "smug")]),
                      "me": actor(BOARD_ME, facing=TOWARD_US, poses=[(0, "idle")], faces=[(0, "side_eye_left")])},
         two_shot("girl", "me", distance=13.5, fov=50), say=[("l7", 0.0)], pad=0.1),
    shot("as_we", {"girl": actor(BOARD_GIRL, facing=TOWARD_US, poses=[(0, "hands_on_hips")],
                                 faces=[(0, "smug"), ("l8:we", "proud")]),
                   "me": actor(BOARD_ME, facing=TOWARD_US, faces=[(0, "side_eye_left")])},
         push("girl.head", 7.0, 5.0), say=[("l8", 0.05)], pad=0.1),
    shot("we", {"me": actor(BOARD_ME, facing=TOWARD_US, poses=[(0, "hands_on_head")], faces=[(0, "furious")]),
                "girl": actor(BOARD_GIRL, facing=TOWARD_US, faces=[(0, "smug")])},
         dutch_in("me.head", degrees=14, start=7.0, end=3.6, move=0.22), say=[("l9", 0.04)],
         sfx=[("boom", "l9:end+0.02")], pad=0.5),
    shot("grade", {"teacher": actor(TEACH, facing=TOWARD_US, poses=[(0, "idle")],
                                    faces=[(0, "smile"), ("l10:same", "grin")])},
         push("teacher.head", 8.0, 5.4), say=[("l10", 0.05)], pad=0.05),
    shot("dead", {"me": actor(BOARD_ME, facing=TOWARD_US, poses=[(0, "slump")], faces=[(0, "dead")])},
         push("me.head", 5.0, 3.8, move=0.5), sfx=[("boom", 0.0)], seconds=1.25),
)
s.music("build/library/music/comedy_bed.mp3", start=0.75, gain_db=-15.0, duck_db=-5.0)

if __name__ == "__main__":
    print(s.write(HERE))
