"""Captions in the references' house style, as RGBA layers to put over a 1080 x 1920 frame (docs/CAPTIONS.md).

    import captions
    layer, (x, y) = captions.render("why does every group project have that ONE person? 😭", "comedy")
    look.over(frame, layer, x, y)          # or captions.over(frame, text, style)

Three styles, measured from the reference frames (spike S6):

- `comedy`: low (the block's centre 77.9% down), a clause per caption, white Montserrat SemiBold with a thin black
  outline, CAPS on the stressed words written into the text, one trailing emoji.
- `story`: high (24.8% down), 1-3 words, half again as big, a thicker outline, no emoji.
- `header` (and `label`): the music formats' header near the top; a word in braces takes a colour,
  `"{pink:Mom's} old photos.."`.

Emoji are Noto's 3D set (assets/emoji/noto), placed as pictures after the text; any emoji without a picture there
raises, so a caption never shows a box.
"""

from __future__ import annotations

import functools
import os
import re
import sys

import numpy as np
from PIL import Image, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import typeset as ts  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
FONTS = os.path.join(ROOT, "assets", "fonts", "montserrat")
EMOJI = os.path.join(ROOT, "assets", "emoji", "noto")
W, H = 1080, 1920

COLORS = {"pink": (255, 105, 196), "blue": (90, 180, 255), "yellow": (255, 221, 64), "green": (110, 232, 120),
          "red": (255, 82, 82), "purple": (190, 120, 255), "orange": (255, 160, 60), "white": (255, 255, 255)}

# Measured on full-size reference frames (tests/s6_captions.py): cap height and outline in px at 1080 wide; step:
# baseline to baseline in cap heights; centre: the block's centre (first line's cap top to last line's baseline) as a
# share of the frame's height, or with anchor "top", where the first line's cap top goes; width: the widest line, px;
# tracking: letter spacing in em; emoji: an emoji's height in cap heights.
STYLES = {
    "comedy": dict(face="Montserrat-SemiBold.ttf", cap=43, stroke=4, step=1.465, centre=0.779, width=800,
                   tracking=-0.02, emoji=1.16),
    "story": dict(face="Montserrat-SemiBold.ttf", cap=66, stroke=8, step=1.47, centre=0.248, width=760,
                  tracking=-0.02, emoji=1.12),
    "header": dict(face="Montserrat-SemiBold.ttf", cap=65, stroke=7, step=1.48, centre=0.112, anchor="top",
                   width=900, tracking=-0.02, emoji=1.12),
    "label": dict(face="Montserrat-SemiBold.ttf", cap=50, stroke=6, step=1.48, centre=0.2, anchor="top", width=900,
                  tracking=-0.02, emoji=1.12),
}

_EMOJI_CHARS = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿←-⇿⌀-⏿️‍"
                          "\U000E0020-\U000E007F]")


def face_path(face: str) -> str:
    return face if os.path.isabs(face) else os.path.join(FONTS, face)


@functools.lru_cache(maxsize=32)
def cap_ratio(face: str) -> float:
    """The font's cap height as a share of its size (an 'H' measured at 200 px)."""
    f = ImageFont.truetype(face_path(face), 200)
    box = f.getbbox("H")
    return (box[3] - box[1]) / 200


def size_for(face: str, cap: float) -> int:
    return max(4, int(round(cap / cap_ratio(face))))


def is_emoji(token: str) -> bool:
    return bool(token) and all(_EMOJI_CHARS.match(ch) for ch in token)


def emoji_file(token: str) -> str:
    """The picture for one emoji (a sequence of codepoints): Noto names files by codepoint, without FE0F."""
    cps = [f"{ord(ch):x}" for ch in token if ord(ch) != 0xFE0F]
    path = os.path.join(EMOJI, "emoji_u" + "_".join(cps) + ".png")
    if not os.path.exists(path):
        raise FileNotFoundError(f"no picture for emoji {token!r} ({'_'.join(cps)}); add it to {EMOJI}")
    return path


@functools.lru_cache(maxsize=64)
def emoji_layer(token: str, height: int) -> np.ndarray:
    img = Image.open(emoji_file(token)).convert("RGBA")
    img = img.resize((max(1, round(img.width * height / img.height)), height), Image.LANCZOS)
    a = np.asarray(img, dtype=np.float32) / 255.0
    # Pillow gives premultiplied-looking edges on resize; keep straight alpha as the type layers use
    return a


def _tokens(text: str) -> list[tuple[str, str | None]]:
    """(token, colour name or None): words, emoji split off the words they touch, '{colour:words}' marked."""
    out: list[tuple[str, str | None]] = []
    for m in re.finditer(r"\{(\w+):([^}]*)\}|(\S+)", text):
        colour, inner, plain = m.group(1), m.group(2), m.group(3)
        words = inner.split() if inner is not None else [plain]
        for w in words:
            parts = re.findall(f"(?:{_EMOJI_CHARS.pattern})+|[^{_EMOJI_CHARS.pattern[1:-1]}]+", w)
            for p in parts:
                out.append((p, colour))
    return out


def text_layer(text: str, size: int, face: str, color=(255, 255, 255), tracking: float = 0.0,
               stroke: float = 0.0) -> tuple[np.ndarray, int, int]:
    """One run of text with its outline, letter-spaced without losing the font's kerning. Returns (RGBA layer, the
    left padding, the baseline's row in the layer)."""
    from PIL import ImageDraw
    f = ts.font(face, size)
    sw = int(round(stroke))
    asc, desc = f.getmetrics()
    pad = int(size * 0.3) + sw
    xs = [f.getlength(text[: i + 1]) - f.getlength(text[i]) + i * tracking * size for i in range(len(text))]
    width = (xs[-1] + f.getlength(text[-1])) if text else 0.0
    w_px, h_px = int(width) + 2 * pad + 4, asc + desc + 2 * pad
    fill, edge = Image.new("L", (w_px, h_px), 0), Image.new("L", (w_px, h_px), 0)
    df, de = ImageDraw.Draw(fill), ImageDraw.Draw(edge)
    for ch, x in zip(text, xs):
        df.text((pad + x, pad), ch, font=f, fill=255)
        if sw:
            de.text((pad + x, pad), ch, font=f, fill=255, stroke_width=sw, stroke_fill=255)
    out = ts._solid(fill, color)
    if sw:
        out = ts.stack(ts._solid(edge, (0, 0, 0)), out)
    return out, pad, pad + asc


def _advance(text: str, size: int, face: str, tracking: float) -> float:
    f = ts.font(face, size)
    return f.getlength(text) + tracking * size * max(0, len(text) - 1)


def _outlined_emoji(token: str, height: int, stroke: int) -> np.ndarray:
    """An emoji picture with the captions' black outline round it, as the references draw theirs."""
    import cv2
    pic = emoji_layer(token, height)
    if stroke <= 0:
        return pic
    h, w = pic.shape[:2]
    out = np.zeros((h + 2 * stroke, w + 2 * stroke, 4), np.float32)
    a = np.zeros(out.shape[:2], np.float32)
    a[stroke:stroke + h, stroke:stroke + w] = pic[..., 3]
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * stroke + 1, 2 * stroke + 1))
    out[..., 3] = cv2.dilate(a, k)
    out[stroke:stroke + h, stroke:stroke + w] = ts.stack(out[stroke:stroke + h, stroke:stroke + w], pic)
    return out


def _segments(tokens, style: dict, size: int):
    """Each token: (kind, token, layer, advance, left padding, baseline row in the layer)."""
    face = face_path(style["face"])
    f = ts.font(face, size)
    tr = style.get("tracking", 0.0)
    space = f.getlength(" ") + tr * size
    sw = int(round(style["stroke"]))
    segs = []
    for tok, colour in tokens:
        if is_emoji(tok):
            lay = _outlined_emoji(tok, int(round(style["cap"] * style["emoji"])), sw)
            segs.append(("emoji", tok, lay, lay.shape[1] - 2 * sw, sw, 0))
        else:
            c = COLORS.get(colour or "white", (255, 255, 255))
            lay, pad, base = text_layer(tok, size, face, c, tr, style["stroke"])
            segs.append(("text", tok, lay, _advance(tok, size, face, tr), pad, base))
    return segs, space


def _rows(segs, space: float, style: dict) -> list[list]:
    """Segments wrapped into rows no wider than the style's width. An emoji never starts a row: one that won't fit
    takes the word before it down to the next row (hung on the end it drew "and on presentation day? 👀" to x = 961,
    under the Shorts buttons: M3's third review)."""
    gap = style["cap"] * 0.12
    rows: list[list] = []
    cur, wcur = [], 0.0
    for s in segs:
        sep = (gap if s[0] == "emoji" else space) if cur else 0.0
        if cur and wcur + sep + s[3] > style["width"]:
            if s[0] != "emoji":
                rows.append(cur)
                cur, wcur, sep = [], 0.0, 0.0
            elif len(cur) > 1 and cur[-1][0][0] != "emoji":
                last, lsep = cur.pop()
                rows.append(cur)
                cur, wcur = [(last, 0.0)], last[3]
        cur.append((s, sep))
        wcur += sep + s[3]
    if cur:
        rows.append(cur)
    return rows


def render(text: str, style: str | dict = "comedy", width: int | None = None) -> tuple[np.ndarray, tuple[int, int]]:
    """The caption as an RGBA layer and where its top-left goes on a 1080 x 1920 frame: lines wrapped to the style's
    width and centred (emoji included), the block placed as the style says."""
    st = dict(STYLES[style]) if isinstance(style, str) else dict(style)
    if width:
        st["width"] = width
    size = size_for(st["face"], st["cap"])
    segs, space = _segments(_tokens(text), st, size)
    rows = _rows(segs, space, st)
    sw = int(round(st["stroke"]))
    step = int(round(st["cap"] * st["step"]))
    margin = int(size * 0.3) + sw + 4
    above = st["cap"] + margin + int(size * 0.3)  # room over the first baseline: ascenders, outline
    below = int(size * 0.35) + margin  # room under the last baseline: descenders, outline, emoji
    widths = [sum(sep + s[3] for s, sep in r) for r in rows]
    bw = int(max(widths) + 2 * margin) if widths else 1
    bh = above + step * (len(rows) - 1) + below
    out = np.zeros((bh, bw, 4), np.float32)
    for k, (row, rw) in enumerate(zip(rows, widths)):
        x = margin + (bw - 2 * margin - rw) / 2
        base = above + k * step
        for s, sep in row:
            x += sep
            kind, tok, lay, adv, pad, lbase = s
            if kind == "text":
                ts.paste(out, lay, int(round(x - pad)), int(round(base - lbase)))
            else:  # an emoji's bottom sits a sixth of a cap height under the baseline
                ts.paste(out, lay, int(round(x - pad)), int(round(base + st["cap"] * 0.16 - (lay.shape[0] - pad))))
            x += adv
    first_cap_top = above - st["cap"]
    last_base = above + (len(rows) - 1) * step
    if st.get("anchor") == "top":
        y = st["centre"] * H - first_cap_top
    else:
        y = st["centre"] * H - (first_cap_top + last_base) / 2
    return out, (int(round(W / 2 - bw / 2)), int(round(y)))


def over(frame: np.ndarray, text: str, style: str | dict = "comedy", scale: float | None = None) -> np.ndarray:
    """`frame` (float RGB 0..1, any size with the 9:16 shape) with the caption on it."""
    import look
    h, w = frame.shape[:2]
    layer, (x, y) = render(text, style)
    k = scale if scale is not None else w / W
    if abs(k - 1) > 1e-6:
        import cv2
        layer = cv2.resize(layer, (max(1, int(layer.shape[1] * k)), max(1, int(layer.shape[0] * k))),
                           interpolation=cv2.INTER_AREA)
        x, y = int(round(x * k)), int(round(y * k))
    out = frame.copy()
    look.over(out, layer, x, y)
    return out


def lines_of(text: str, style: str | dict = "comedy") -> list[str]:
    """The caption's lines as `render` wraps them (for checks and the timeline's texts)."""
    st = dict(STYLES[style]) if isinstance(style, str) else dict(style)
    segs, space = _segments(_tokens(text), st, size_for(st["face"], st["cap"]))
    return [" ".join(s[1] for s, _ in r) for r in _rows(segs, space, st)]
