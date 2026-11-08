"""The face library: about 40 expressions drawn from code in one style, black line art with a few coloured accents
(docs/FACES.md).

    python tools/roblox/facekit.py build [OUT_DIR]      # every face as a 512 px PNG (default build/faces/kit) and
                                                       # a contact sheet on skin, then installs them into Studio
    python tools/roblox/facekit.py sheet [OUT_DIR]      # just the sheet

    import facekit
    facekit.NAMES                                       # the expressions
    facekit.draw("smug")                                # a PIL RGBA image

Each face is built from parts (eyes, brows, mouth, extras) so the set holds one line weight and one placement:
features inside the area Roblox's own face uses (x 42-88, y 27-101 of 128), drawn at four times the size and scaled
down so every edge is smooth. A face's name says what it's for; docs/FACES.md lists which face fits which beat.
"""

from __future__ import annotations

import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

S = 512
K = 4  # drawn at K times the size, then scaled down
INK = (22, 18, 18, 255)
WHITE = (255, 255, 255, 255)
TEAR = (90, 170, 255, 235)
SWEAT = (140, 205, 255, 240)
BLUSH = (255, 120, 140, 110)
RED = (232, 52, 52, 255)
MOUTH = (110, 24, 30, 255)
TONGUE = (238, 110, 120, 255)
GOLD = (255, 205, 40, 255)
GREEN = (40, 170, 80, 255)
LW = 17  # line weight at 512 px

EYE_Y, EYE_DX, MOUTH_Y = 200, 66, 322


class Face:
    def __init__(self):
        self.img = Image.new("RGBA", (S * K, S * K), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    # primitives, in 512-px units
    def _p(self, x, y):
        return (x * K, y * K)

    def line(self, pts, w=LW, color=INK):
        """A stroke through points with round caps and joins."""
        pts = [self._p(*p) for p in pts]
        r = w * K / 2
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(1, int(math.dist((x0, y0), (x1, y1)) / (r / 3)))
            for i in range(n + 1):
                u = i / n
                x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
                self.d.ellipse((x - r, y - r, x + r, y + r), fill=color)
        if len(pts) == 1:
            x, y = pts[0]
            self.d.ellipse((x - r, y - r, x + r, y + r), fill=color)

    def curve(self, f, a=0.0, b=1.0, n=60, w=LW, color=INK):
        self.line([f(a + (b - a) * i / n) for i in range(n + 1)], w, color)

    def ellipse(self, cx, cy, rx, ry, fill=INK, outline=None, w=LW):
        box = (K * (cx - rx), K * (cy - ry), K * (cx + rx), K * (cy + ry))
        if outline:
            ow = w * K
            self.d.ellipse((box[0] - ow / 2, box[1] - ow / 2, box[2] + ow / 2, box[3] + ow / 2), fill=outline)
            self.d.ellipse((box[0] + ow / 2, box[1] + ow / 2, box[2] - ow / 2, box[3] - ow / 2), fill=fill)
        else:
            self.d.ellipse(box, fill=fill)

    def poly(self, pts, fill, outline=INK, w=LW):
        P = [self._p(*p) for p in pts]
        self.d.polygon(P, fill=fill)
        if outline:
            self.line(pts + [pts[0]], w, outline)

    def text(self, s, cx, cy, size, fill, outline=INK, w=8):
        f = ImageFont.truetype(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "fonts",
                                            "montserrat", "Montserrat-ExtraBold.ttf"), size * K)
        self.d.text(self._p(cx, cy), s, font=f, fill=fill, anchor="mm", stroke_width=w * K, stroke_fill=outline)

    def done(self) -> Image.Image:
        return self.img.resize((S, S), Image.LANCZOS)


# ---------------------------------------------------------------------------------------------------- eyes


def _both(fn):
    def draw(f: Face, **kw):
        for side in (-1, 1):
            fn(f, 256 + side * EYE_DX, EYE_Y, side, **kw)
    return draw


@_both
def eyes_dot(f, x, y, side, r=15, ry=None):
    f.ellipse(x, y, r, ry or r * 1.25)


@_both
def eyes_oval(f, x, y, side, look=0.0):
    f.ellipse(x + look * 6, y, 13, 26)
    f.ellipse(x + look * 6 - 3, y - 11, 4, 5, fill=WHITE)


@_both
def eyes_white(f, x, y, side, rx=34, ry=40, look=(0.0, 0.0), pupil=13, lid=0.0):
    """Open eyes: white with a black outline, a pupil looking `look` (-1..1 each way); `lid` closes them from the
    top (0..1)."""
    f.ellipse(x, y, rx, ry, fill=WHITE, outline=INK, w=LW * 0.75)
    px, py = x + look[0] * (rx - pupil - 6), y + look[1] * (ry - pupil - 6)
    f.ellipse(px, py, pupil, pupil * 1.1)
    f.ellipse(px - pupil * 0.35, py - pupil * 0.4, pupil * 0.3, pupil * 0.3, fill=WHITE)
    if lid > 0:
        top = y - ry
        cut = top + 2 * ry * lid
        f.d.rectangle((K * (x - rx - 12), K * (top - 14), K * (x + rx + 12), K * cut), fill=(0, 0, 0, 0))
        f.line([(x - rx - 2, cut), (x + rx + 2, cut)], LW * 0.9)


@_both
def eyes_happy(f, x, y, side, h=16):
    """Closed, smiling: ^ arcs."""
    f.curve(lambda u: (x - 26 + 52 * u, y + 6 - h * math.sin(math.pi * u)), w=LW * 0.95)


@_both
def eyes_closed(f, x, y, side, droop=8):
    """Closed, relaxed or sad: arcs that sag."""
    f.curve(lambda u: (x - 26 + 52 * u, y - 2 + droop * math.sin(math.pi * u)), w=LW * 0.95)


@_both
def eyes_squeeze(f, x, y, side):
    """Squeezed shut: > <."""
    s = -side
    f.line([(x - 22 * s, y - 18), (x + 18 * s, y), (x - 22 * s, y + 18)], LW * 0.95)


@_both
def eyes_x(f, x, y, side):
    f.line([(x - 20, y - 20), (x + 20, y + 20)], LW * 0.95)
    f.line([(x - 20, y + 20), (x + 20, y - 20)], LW * 0.95)


@_both
def eyes_flat(f, x, y, side, tilt=0.0):
    """Unimpressed: a straight lid line over a half dot."""
    f.ellipse(x, y + 6, 15, 12)
    f.d.rectangle((K * (x - 24), K * (y - 26), K * (x + 24), K * (y + 3 + tilt * side)), fill=(0, 0, 0, 0))
    f.line([(x - 26, y + 1 - tilt * side), (x + 26, y + 1 + tilt * side)], LW * 0.9)


@_both
def eyes_heart(f, x, y, side):
    pts = []
    for i in range(80):
        t = 2 * math.pi * i / 80
        hx = 16 * math.sin(t) ** 3
        hy = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((x + hx * 2.2, y + hy * 2.2))
    f.poly(pts, RED, INK, LW * 0.6)


@_both
def eyes_star(f, x, y, side):
    pts = []
    for i in range(10):
        r = 34 if i % 2 == 0 else 15
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((x + r * math.cos(a), y + r * math.sin(a)))
    f.poly(pts, GOLD, INK, LW * 0.55)


@_both
def eyes_dollar(f, x, y, side):
    f.text("$", x, y, 62, GREEN, INK, 5)


@_both
def eyes_spiral(f, x, y, side):
    f.curve(lambda u: (x + 4 * u * 8 * math.cos(u * 4 * math.pi * side), y + 4 * u * 8 * math.sin(u * 4 * math.pi)),
            n=120, w=LW * 0.7)


@_both
def eyes_shiny(f, x, y, side):
    """Big cute eyes: black with two highlights."""
    f.ellipse(x, y, 25, 32)
    f.ellipse(x - 8, y - 12, 9, 10, fill=WHITE)
    f.ellipse(x + 9, y + 10, 4, 4, fill=WHITE)


@_both
def eyes_narrow(f, x, y, side, slant=10):
    """Scheming: a dark almond with the lid slanted down to the middle."""
    f.poly([(x - 28, y - slant * side * -1), (x + 28, y + slant * side * -1), (x + 22, y + 10), (x - 22, y + 10)],
           INK, None)
    f.line([(x - 30, y - slant * -side), (x + 30, y + slant * -side)], LW * 0.9)


def eyes_wink(f: Face):
    eyes_happy_one(f, 256 - EYE_DX, EYE_Y)
    f.ellipse(256 + EYE_DX, EYE_Y, 15, 19)


def eyes_happy_one(f, x, y, h=16):
    f.curve(lambda u: (x - 26 + 52 * u, y + 6 - h * math.sin(math.pi * u)), w=LW * 0.95)


def eyes_derp(f: Face):
    f.ellipse(256 - EYE_DX, EYE_Y, 36, 40, fill=WHITE, outline=INK, w=LW * 0.75)
    f.ellipse(256 - EYE_DX + 14, EYE_Y + 10, 11, 12)
    f.ellipse(256 + EYE_DX, EYE_Y + 6, 22, 24, fill=WHITE, outline=INK, w=LW * 0.75)
    f.ellipse(256 + EYE_DX - 6, EYE_Y - 4, 8, 9)


# ---------------------------------------------------------------------------------------------------- brows


def brows(f: Face, kind: str, y: float = EYE_Y - 62):
    for side in (-1, 1):
        x = 256 + side * EYE_DX
        if kind == "angry":  # down toward the middle
            f.line([(x - 30 * side * -1, y - 8), (x + 22 * side * -1, y + 14)], LW)
        elif kind == "sad":  # up toward the middle
            f.line([(x - 28 * side * -1, y + 12), (x + 24 * side * -1, y - 8)], LW)
        elif kind == "raised":
            f.curve(lambda u, x=x: (x - 28 + 56 * u, y - 10 - 10 * math.sin(math.pi * u)), w=LW * 0.9)
        elif kind == "flat":
            f.line([(x - 26, y + 4), (x + 26, y + 4)], LW * 0.9)
        elif kind == "skeptic":  # one up, one flat
            if side == 1:
                f.curve(lambda u, x=x: (x - 28 + 56 * u, y - 16 - 10 * math.sin(math.pi * u)), w=LW * 0.9)
            else:
                f.line([(x - 26, y + 8), (x + 26, y + 8)], LW * 0.9)


# ---------------------------------------------------------------------------------------------------- mouths


def mouth_smile(f, w=70, h=34, y=MOUTH_Y):
    f.curve(lambda u: (256 - w + 2 * w * u, y + h * math.sin(math.pi * u)))


def mouth_frown(f, w=56, h=24, y=MOUTH_Y + 24):
    f.curve(lambda u: (256 - w + 2 * w * u, y - h * math.sin(math.pi * u)))


def mouth_flat(f, w=46, y=MOUTH_Y + 12, tilt=0.0):
    f.line([(256 - w, y - tilt), (256 + w, y + tilt)])


def mouth_wavy(f, w=60, y=MOUTH_Y + 14, a=8):
    f.curve(lambda u: (256 - w + 2 * w * u, y + a * math.sin(u * 3 * math.pi)), n=80)


def _open(f, pts, teeth=False, tongue=False, fangs=False):
    """An open mouth: its outline filled dark, with top teeth and a tongue if asked."""
    f.poly(pts, MOUTH, None)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    top, bot = min(ys), max(ys)
    if tongue:
        cx = (min(xs) + max(xs)) / 2
        f.ellipse(cx, bot - (bot - top) * 0.18, (max(xs) - min(xs)) * 0.26, (bot - top) * 0.26, fill=TONGUE)
    if teeth:
        layer = Image.new("RGBA", f.img.size, (0, 0, 0, 0))
        dl = ImageDraw.Draw(layer)
        dl.rectangle((K * min(xs), K * top, K * max(xs), K * (top + (bot - top) * 0.3)), fill=WHITE)
        mask = Image.new("L", f.img.size, 0)
        ImageDraw.Draw(mask).polygon([(K * x, K * y) for x, y in pts], fill=255)
        f.img.paste(layer, (0, 0), Image.composite(layer, Image.new("RGBA", f.img.size), mask).split()[3])
        f.d = ImageDraw.Draw(f.img)
    if fangs:
        cx = (min(xs) + max(xs)) / 2
        for dx in (-0.55, -0.2, 0.2, 0.55):
            x = cx + dx * (max(xs) - min(xs)) / 2
            f.poly([(x - 11, top + 2), (x + 11, top + 2), (x, top + 26)], WHITE, None)
    f.line(pts + [pts[0]], LW * 0.95)


def mouth_grin(f, w=78, h=60, teeth=True, tongue=False, y=MOUTH_Y - 6):
    pts = [(256 - w + 2 * w * i / 30, y + 4 * math.sin(math.pi * i / 30)) for i in range(31)]
    pts += [(256 + w - 2 * w * i / 30, y + h * math.sin(math.pi * (1 - i / 30))) for i in range(31)]
    _open(f, pts, teeth=teeth, tongue=tongue)


def mouth_laugh(f):
    mouth_grin(f, w=84, h=86, teeth=True, tongue=True, y=MOUTH_Y - 16)


def mouth_o(f, rx=24, ry=32, y=MOUTH_Y + 8):
    pts = [(256 + rx * math.cos(2 * math.pi * i / 40), y + ry * math.sin(2 * math.pi * i / 40)) for i in range(40)]
    _open(f, pts)


def mouth_yell(f, w=62, h=78, y=MOUTH_Y - 10):
    pts = [(256 - w, y), (256 + w, y), (256 + w * 0.7, y + h), (256 - w * 0.7, y + h)]
    pts = _round(pts)
    _open(f, pts, teeth=True, tongue=True)


def mouth_sad_open(f, w=58, h=46, y=MOUTH_Y + 38):
    pts = [(256 - w + 2 * w * i / 30, y - h * math.sin(math.pi * i / 30)) for i in range(31)]
    pts += [(256 + w - 2 * w * i / 30, y - 6 * math.sin(math.pi * (1 - i / 30))) for i in range(31)]
    _open(f, pts, tongue=True)


def mouth_smirk(f, side=1):
    f.curve(lambda u: (256 - 50 + 100 * u, MOUTH_Y + 18 - side * 22 * u * u + 6 * math.sin(math.pi * u)))


def mouth_grimace(f, w=72, h=42, y=MOUTH_Y):
    pts = _round([(256 - w, y), (256 + w, y), (256 + w, y + h), (256 - w, y + h)], r=0.25)
    f.poly(pts, WHITE, None)
    for i in range(1, 6):
        x = 256 - w + 2 * w * i / 6
        f.line([(x, y + 4), (x, y + h - 4)], LW * 0.45)
    f.line([(256 - w + 6, y + h / 2), (256 + w - 6, y + h / 2)], LW * 0.45)
    f.line(pts + [pts[0]], LW * 0.95)


def mouth_cat(f, y=MOUTH_Y + 6):
    f.curve(lambda u: (256 - 44 + 44 * u, y + 14 * math.sin(math.pi * u)), w=LW * 0.9)
    f.curve(lambda u: (256 + 44 * u, y + 14 * math.sin(math.pi * u)), w=LW * 0.9)


def mouth_small_o(f, y=MOUTH_Y + 14, side=0):
    f.ellipse(256 + side * 24, y, 12, 14, fill=MOUTH, outline=INK, w=LW * 0.75)


def mouth_tongue(f):
    mouth_smile(f, w=64, h=26)
    f.ellipse(256 + 18, MOUTH_Y + 38, 20, 22, fill=TONGUE, outline=INK, w=LW * 0.7)
    f.line([(256 + 18, MOUTH_Y + 28), (256 + 18, MOUTH_Y + 46)], LW * 0.4)


def mouth_evil(f):
    w, h, y = 92, 56, MOUTH_Y - 18
    pts = [(256 - w + 2 * w * i / 30, y - 18 * math.sin(math.pi * i / 30) + 30 * (abs(i - 15) / 15) ** 2)
           for i in range(31)]
    pts += [(256 + w - 2 * w * i / 30, y + 30 * (abs(15 - i) / 15) ** 2 + h * math.sin(math.pi * (1 - i / 30)))
            for i in range(31)]
    _open(f, pts, fangs=True)


def _round(pts, r=0.18, n=6):
    """A polygon with its corners rounded."""
    out = []
    m = len(pts)
    for i in range(m):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % m]
        a = (p1[0] + (p0[0] - p1[0]) * r, p1[1] + (p0[1] - p1[1]) * r)
        b = (p1[0] + (p2[0] - p1[0]) * r, p1[1] + (p2[1] - p1[1]) * r)
        for j in range(n + 1):
            u = j / n
            out.append(((1 - u) ** 2 * a[0] + 2 * (1 - u) * u * p1[0] + u * u * b[0],
                        (1 - u) ** 2 * a[1] + 2 * (1 - u) * u * p1[1] + u * u * b[1]))
    return out


# ---------------------------------------------------------------------------------------------------- extras


def tears(f, streams=True):
    for side in (-1, 1):
        x = 256 + side * EYE_DX
        if streams:
            f.line([(x + side * 4, EYE_Y + 22), (x + side * 8, EYE_Y + 90), (x + side * 4, EYE_Y + 150)], LW * 1.3,
                   TEAR)
        else:
            drop(f, x + side * 30, EYE_Y + 42, 13, TEAR)


def drop(f, x, y, r, color):
    pts = [(x + r * math.cos(a), y + r * math.sin(a)) for a in (i * math.pi / 20 for i in range(21))]
    pts += [(x, y - r * 2.6)]
    f.poly(pts, color, INK, LW * 0.45)


def sweat(f):
    drop(f, 352, 112, 15, SWEAT)


def blush(f):
    for side in (-1, 1):
        f.ellipse(256 + side * 100, EYE_Y + 66, 30, 15, fill=BLUSH)


def vein(f):
    x, y = 340, 98
    for a in (0, 90, 180, 270):
        r = math.radians(a + 45)
        f.curve(lambda u, r=r: (x + math.cos(r) * (8 + 14 * u) + math.cos(r + 1.4) * 8 * math.sin(math.pi * u),
                                y + math.sin(r) * (8 + 14 * u) + math.sin(r + 1.4) * 8 * math.sin(math.pi * u)),
                w=LW * 0.7, color=RED)


# ---------------------------------------------------------------------------------------------------- the set


def _face(*parts):
    def make() -> Image.Image:
        f = Face()
        for p in parts:
            p(f)
        return f.done()
    return make


def _p(fn, **kw):
    return lambda f: fn(f, **kw)


FACES = {
    # everyday
    "smile": _face(eyes_dot, mouth_smile),
    "grin": _face(eyes_happy, mouth_grin),
    "laugh": _face(eyes_squeeze, mouth_laugh, _p(tears, streams=False)),
    "blank": _face(eyes_dot, _p(mouth_flat, w=40)),
    "deadpan": _face(eyes_flat, _p(mouth_flat, w=44)),
    "bored": _face(_p(eyes_white, lid=0.55, look=(0, 0.4)), _p(mouth_flat, w=36, tilt=6)),
    "wink": _face(eyes_wink, mouth_smile),
    "tongue": _face(eyes_happy, mouth_tongue),
    "proud": _face(eyes_happy, _p(brows, kind="raised"), _p(mouth_smile, w=80, h=40)),
    "whistle": _face(eyes_closed, _p(brows, kind="raised"), _p(mouth_small_o, side=1)),
    "sleepy": _face(_p(eyes_closed, droop=10), _p(mouth_small_o, y=MOUTH_Y + 20)),
    # surprise and fear
    "shock": _face(_p(eyes_white, pupil=9), _p(brows, kind="raised"), mouth_o),
    "gasp": _face(_p(eyes_white, pupil=9, rx=38, ry=44), _p(brows, kind="raised"), _p(mouth_o, rx=30, ry=42)),
    "scared": _face(_p(eyes_white, pupil=8, look=(0, 0.2)), _p(brows, kind="sad"), mouth_wavy, sweat),
    "nervous": _face(eyes_dot, _p(brows, kind="sad"), _p(mouth_wavy, a=6), sweat),
    "wide_happy": _face(_p(eyes_white, pupil=14), _p(brows, kind="raised"), _p(mouth_grin, h=70)),
    # anger
    "angry": _face(eyes_dot, _p(brows, kind="angry"), _p(mouth_frown, h=20)),
    "yell": _face(_p(eyes_dot, r=13), _p(brows, kind="angry"), mouth_yell),
    "furious": _face(_p(eyes_white, pupil=7), _p(brows, kind="angry"), mouth_grimace, vein),
    "pout": _face(eyes_dot, _p(brows, kind="angry"), _p(mouth_small_o, y=MOUTH_Y + 18), blush),
    "grimace": _face(eyes_squeeze, mouth_grimace),
    # sadness
    "sad": _face(eyes_dot, _p(brows, kind="sad"), mouth_frown),
    "cry": _face(eyes_closed, _p(brows, kind="sad"), _p(mouth_wavy, a=7, y=MOUTH_Y + 26), tears),
    "sob": _face(eyes_squeeze, _p(brows, kind="sad"), mouth_sad_open, tears),
    "teary": _face(_p(eyes_shiny), _p(brows, kind="sad"), _p(mouth_wavy, a=5, w=40), _p(tears, streams=False)),
    "sad_smile": _face(eyes_closed, _p(brows, kind="sad"), _p(mouth_smile, w=50, h=20)),
    # attitude
    "smug": _face(_p(eyes_white, lid=0.5, look=(0.5, 0.3)), _p(brows, kind="skeptic"), _p(mouth_smirk, side=1)),
    "side_eye": _face(_p(eyes_white, lid=0.45, look=(1.0, 0.2)), _p(mouth_flat, w=34, tilt=-4)),
    "side_eye_left": _face(_p(eyes_white, lid=0.45, look=(-1.0, 0.2)), _p(mouth_flat, w=34, tilt=4)),
    "sus": _face(_p(eyes_flat, tilt=6), _p(brows, kind="skeptic"), _p(mouth_flat, w=30)),
    "scheming": _face(eyes_narrow, _p(brows, kind="angry"), _p(mouth_smirk, side=1)),
    "evil": _face(eyes_narrow, _p(brows, kind="angry"), mouth_evil),
    "disgust": _face(_p(eyes_flat, tilt=4), _p(brows, kind="angry"), _p(mouth_wavy, w=50, a=9, y=MOUTH_Y + 22)),
    "confused": _face(eyes_dot, _p(brows, kind="skeptic"), _p(mouth_wavy, w=40, a=6)),
    "cringe": _face(eyes_squeeze, _p(brows, kind="sad"), mouth_grimace, sweat),
    # big feelings
    "love": _face(eyes_heart, _p(mouth_smile, w=60, h=30), blush),
    "starstruck": _face(eyes_star, _p(mouth_grin, h=64)),
    "money": _face(eyes_dollar, mouth_grin),
    "cute": _face(eyes_shiny, mouth_cat, blush),
    "dizzy": _face(eyes_spiral, _p(mouth_wavy, a=8)),
    "dead": _face(eyes_x, _p(mouth_flat, w=40)),
    "derp": _face(eyes_derp, mouth_tongue),
    "oval": _face(eyes_oval, _p(mouth_smile, w=48, h=22)),
}
NAMES = sorted(FACES)


def draw(name: str) -> Image.Image:
    return FACES[name]()


def build(out_dir: str) -> list[str]:
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for name in NAMES:
        p = os.path.join(out_dir, name + ".png")
        draw(name).save(p)
        paths.append(p)
    return paths


def sheet(out_dir: str, cols: int = 7, cell: int = 220) -> str:
    """Every face on a skin-coloured square with its name, to look at."""
    rows = math.ceil(len(NAMES) / cols)
    img = Image.new("RGB", (cols * cell, rows * (cell + 34)), (40, 42, 50))
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "fonts",
                                           "montserrat", "Montserrat-SemiBold.ttf"), 22)
    for i, name in enumerate(NAMES):
        x, y = (i % cols) * cell, (i // cols) * (cell + 34)
        tile = Image.new("RGBA", (cell - 12, cell - 12), (255, 214, 170, 255))
        face = draw(name).resize((cell - 12, cell - 12), Image.LANCZOS)
        tile.alpha_composite(face)
        img.paste(tile.convert("RGB"), (x + 6, y + 6))
        d.text((x + cell / 2, y + cell + 12), name, font=font, fill=(235, 235, 240), anchor="mm")
    dest = os.path.join(out_dir, "sheet.png")
    img.save(dest)
    return dest


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join("build", "faces", "kit")
    if cmd == "sheet":
        os.makedirs(out, exist_ok=True)
        print(sheet(out))
        return 0
    paths = build(out)
    print(f"{len(paths)} faces in {out}; sheet {sheet(out)}")
    if "--install" in sys.argv:
        import faces
        print(f"installed {len(faces.install(out))} into Studio's content folder")
    return 0


if __name__ == "__main__":
    sys.exit(main())
