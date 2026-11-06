"""Type as straight-alpha RGBA layers (float32, 0..1, H x W x 4), to composite with look.over / look.centre.

Fonts are files passed by path. Keep each font's license beside it: most free faces are under the SIL Open Font
License, which allows bundling them with the license. With no path, Pillow's own face is used: fine for tests, not for
a deliverable.

Captions over game footage sit on busy, bright pictures, often under a platform's own buttons: a heavy face, a thick
dark outline (`stroke`, in em) and a soft shadow keep them readable. Check them on the delivered file at phone size.
"""

from __future__ import annotations

import functools
from typing import Iterable

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


@functools.lru_cache(maxsize=64)
def font(face: str | None, size: int):
    if face is None:
        return ImageFont.load_default(size)
    return ImageFont.truetype(face, size)


def _solid(mask: Image.Image, color) -> np.ndarray:
    a = np.asarray(mask, dtype=np.float32) / 255.0
    rgb = np.empty(a.shape + (3,), dtype=np.float32)
    rgb[...] = np.array(color[:3], dtype=np.float32) / 255.0
    return np.dstack([rgb, a])


def stack(below: np.ndarray, above: np.ndarray) -> np.ndarray:
    """Straight-alpha 'over' of two same-size RGBA layers."""
    a1, a0 = above[..., 3:4], below[..., 3:4]
    a = a1 + a0 * (1 - a1)
    rgb = np.where(a > 1e-6, (above[..., :3] * a1 + below[..., :3] * a0 * (1 - a1)) / np.maximum(a, 1e-6), 0)
    return np.dstack([rgb, a]).astype(np.float32)


def paste(dst: np.ndarray, src: np.ndarray, x: int, y: int) -> np.ndarray:
    """`src` over the RGBA layer `dst` at (x, y), in place; parts off `dst` are dropped."""
    h, w = src.shape[:2]
    H, W = dst.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 > x0 and y1 > y0:
        dst[y0:y1, x0:x1] = stack(dst[y0:y1, x0:x1], src[y0 - y:y1 - y, x0 - x:x1 - x])
    return dst


def _effects(out: np.ndarray, size: int, shadow: float, glow: float, glow_color) -> np.ndarray:
    a = out[..., 3]
    h, w = a.shape
    if glow > 0:
        g = np.clip(cv2.GaussianBlur(a, (0, 0), size * 0.18) * glow, 0, 1)
        rgb = np.empty((h, w, 3), np.float32)
        rgb[...] = np.array(glow_color[:3], np.float32) / 255.0
        out = stack(np.dstack([rgb, g]), out)
    if shadow > 0:
        sh = np.clip(cv2.GaussianBlur(a, (0, 0), size * 0.12) * 1.6, 0, 1) * shadow
        out = stack(np.dstack([np.zeros((h, w, 3), np.float32), sh]), out)
    return out


def line(text: str, size: int, color=(255, 255, 255), face: str | None = None, tracking: float = 0.0,
         stroke: float = 0.0, stroke_color=(0, 0, 0), shadow: float = 0.55, glow: float = 0.0) -> np.ndarray:
    """One line of text: letter-spacing `tracking` (em), an outline `stroke` (em) in `stroke_color`, a soft dark
    shadow under it, an optional glow in its own colour. The text's box keeps the font's line height, so lines made
    at one size share a baseline (trim with crop_x, not crop_alpha, to keep it)."""
    f = font(face, size)
    sw = int(round(stroke * size))
    asc, desc = f.getmetrics()
    pad = int(size * 0.6) + sw
    if tracking:
        widths = [f.getlength(ch) for ch in text]
        tw = sum(widths) + tracking * size * max(0, len(text) - 1)
    else:
        widths, tw = [], f.getlength(text)
    W, H = int(tw) + 4 + pad * 2, asc + desc + pad * 2
    fill, edge = Image.new("L", (W, H), 0), Image.new("L", (W, H), 0)
    df, de = ImageDraw.Draw(fill), ImageDraw.Draw(edge)

    def draw(x: float, s: str):
        df.text((x, pad), s, font=f, fill=255)
        if sw:
            de.text((x, pad), s, font=f, fill=255, stroke_width=sw, stroke_fill=255)

    if tracking:
        x = float(pad)
        for ch, cw in zip(text, widths):
            draw(x, ch)
            x += cw + tracking * size
    else:
        draw(pad, text)  # whole, so the font's kerning applies
    out = _solid(fill, color)
    if sw:
        out = stack(_solid(edge, stroke_color), out)
    return _effects(out, size, shadow, glow, color)


def wrap(words: list[str], size: int, max_width: float, face: str | None = None) -> list[list[int]]:
    """Word indices per line, greedily filled to `max_width` pixels."""
    f = font(face, size)
    space = f.getlength(" ")
    rows: list[list[int]] = []
    cur: list[int] = []
    width = 0.0
    for i, w in enumerate(words):
        ww = f.getlength(w)
        if cur and width + space + ww > max_width:
            rows.append(cur)
            cur, width = [], 0.0
        width += (space if cur else 0.0) + ww
        cur.append(i)
    if cur:
        rows.append(cur)
    return rows


def caption(text: str, size: int, max_width: int, face: str | None = None, color=(255, 255, 255),
            highlight: int | Iterable[int] | None = None, highlight_color=(255, 214, 0), stroke: float = 0.12,
            stroke_color=(0, 0, 0), shadow: float = 0.6, leading: float = 1.08, align: str = "center") -> np.ndarray:
    """A caption block: `text` wrapped to `max_width` pixels, each line aligned (center, left or right), every word
    outlined. The words numbered in `highlight` (0-based) are drawn in `highlight_color`: the word being said, for
    word-by-word captions. (Not used in the trailer this kit comes from: there each card was one line.)"""
    words = text.split()
    hl = {highlight} if isinstance(highlight, int) else set(highlight or ())
    f = font(face, size)
    sw = int(round(stroke * size))
    asc, desc = f.getmetrics()
    pad = int(size * 0.3) + sw
    space = f.getlength(" ")
    rows = []
    for row in wrap(words, size, max_width - 2 * sw, face):
        widths = [f.getlength(words[i]) for i in row]
        W, H = int(sum(widths) + space * (len(row) - 1)) + 4 + 2 * pad, asc + desc + 2 * pad
        edge = Image.new("L", (W, H), 0)
        de = ImageDraw.Draw(edge)
        fills: dict[tuple, Image.Image] = {}
        x = float(pad)
        for i, ww in zip(row, widths):
            c = tuple(highlight_color if i in hl else color)
            img = fills.setdefault(c, Image.new("L", (W, H), 0))
            ImageDraw.Draw(img).text((x, pad), words[i], font=f, fill=255)
            if sw:
                de.text((x, pad), words[i], font=f, fill=255, stroke_width=sw, stroke_fill=255)
            x += ww + space
        layer = _solid(edge, stroke_color) if sw else np.zeros((H, W, 4), np.float32)
        for c, img in fills.items():
            layer = stack(layer, _solid(img, c))
        rows.append(layer)
    if not rows:
        return np.zeros((1, 1, 4), np.float32)
    step = int(round((asc + desc) * leading))
    width = max(r.shape[1] for r in rows)
    out = np.zeros((step * (len(rows) - 1) + rows[-1].shape[0], width, 4), np.float32)
    for k, r in enumerate(rows):
        x = {"left": 0, "right": width - r.shape[1]}.get(align, (width - r.shape[1]) // 2)
        paste(out, r, x, k * step)
    return _effects(out, size, shadow, 0.0, color)


def crop_alpha(layer: np.ndarray) -> np.ndarray:
    ys, xs = np.nonzero(layer[..., 3] > 0.004)
    if len(ys) == 0:
        return layer[:1, :1]
    return layer[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def crop_x(layer: np.ndarray) -> np.ndarray:
    """Trimmed at the sides only: lines of a list keep the font's own line box, so their baselines stay in step."""
    xs = np.nonzero((layer[..., 3] > 0.004).any(axis=0))[0]
    if len(xs) == 0:
        return layer[:, :1]
    return layer[:, xs.min():xs.max() + 1]


def rgb_split(layer: np.ndarray, px: int) -> np.ndarray:
    """A chromatic split: a red copy shifted right, a cyan one left, the layer itself on top."""
    if px == 0:
        return layer
    h, w = layer.shape[:2]
    out = np.zeros((h, w + 2 * px, 4), dtype=np.float32)
    a = layer[..., 3]
    red = np.zeros_like(out)
    red[:, 2 * px:, 0] = 1.0
    red[:, 2 * px:, 3] = a * 0.7
    cyan = np.zeros_like(out)
    cyan[:, :w, 1] = 0.85
    cyan[:, :w, 2] = 1.0
    cyan[:, :w, 3] = a * 0.7
    core = np.zeros_like(out)
    core[:, px:px + w] = layer
    return stack(stack(cyan, red), core)


def with_caret(layer: np.ndarray | None, size: int, color, on: bool = True, gap: float = 0.14,
               width: float = 0.56, height: float = 0.74) -> np.ndarray:
    """A text layer with a block cursor after it (drawn: most faces have no block glyph). With no text, the cursor
    alone, `height` em tall. Blink it by passing on = (frame // 12) % 2 == 0."""
    cw, gp = max(2, int(size * width)), int(size * gap)
    if layer is None or layer.shape[0] < 3:
        out = np.zeros((int(size * height), cw, 4), dtype=np.float32)
        if on:
            out[..., :3] = np.array(color, dtype=np.float32) / 255.0
            out[..., 3] = 0.95
        return out
    h, w = layer.shape[:2]
    out = np.zeros((h, w + gp + cw, 4), dtype=np.float32)
    out[:, :w] = layer
    if on:
        out[:, w + gp:, :3] = np.array(color, dtype=np.float32) / 255.0
        out[:, w + gp:, 3] = 0.95
    return out
