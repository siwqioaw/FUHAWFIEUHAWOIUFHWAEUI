"""Effects for frames and layers (float32 RGB / straight-alpha RGBA in 0..1, as look.py and typeset.py make them).

Every effect is a pure function of its inputs and a seed: no state carried from one frame to the next, so any frame
renders the same on its own, and render.py can render frames out of order in parallel. Pass the frame number (or the
frame within the shot) as the seed wherever an effect is random.

Most of these were used in the trailer this kit comes from; `pop` and `ease_out_back` are new here.
"""

from __future__ import annotations

import cv2
import numpy as np

import typeset as ts

GLYPHS = "ABCDEFGHJKLMNPQRSTUVWXYZ0123456789"


# --- Timing -------------------------------------------------------------------------------------------------------

def ease(u: float) -> float:
    """Smoothstep: slow in, slow out."""
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def ease_out_cubic(u: float) -> float:
    u = min(1.0, max(0.0, u))
    return 1 - (1 - u) ** 3


def ease_out_back(u: float, overshoot: float = 1.70158) -> float:
    """Past the target and back: a bouncy settle."""
    u = min(1.0, max(0.0, u))
    c = overshoot
    return 1 + (c + 1) * (u - 1) ** 3 + c * (u - 1) ** 2


def lerp_keys(keys: list[tuple[float, float]], x: float) -> float:
    """A value from (time, value) keys, linear between them and held past the ends."""
    xs, ys = zip(*keys)
    return float(np.interp(x, xs, ys))


# --- Layers -------------------------------------------------------------------------------------------------------

def scaled(layer: np.ndarray, s: float, blur_to: float | None = None, n: int = 7) -> np.ndarray:
    """A layer scaled by `s` about its centre, on a canvas big enough for it. With `blur_to`, averaged over the
    scales from s to blur_to (motion blur along the scale change)."""
    h, w = layer.shape[:2]
    big = max(s, blur_to if blur_to is not None else s)
    oh, ow = int(h * big) + 4, int(w * big) + 4
    steps = n if blur_to is not None and abs(blur_to - s) > 0.004 else 1
    acc = np.zeros((oh, ow, 4), np.float32)
    for j in range(steps):
        sj = s if steps == 1 else s + (blur_to - s) * (j + 1) / steps
        m = np.array([[sj, 0, (ow - w * sj) / 2], [0, sj, (oh - h * sj) / 2]], np.float32)
        acc += cv2.warpAffine(layer, m, (ow, oh), flags=cv2.INTER_LINEAR)
    return acc / steps


def slam(layer: np.ndarray, k: int, dur: int = 5, s0: float = 1.36, split0: int = 12) -> np.ndarray | None:
    """A layer slamming in, k frames after it starts: it shrinks from s0 to its size over `dur` frames, blurred along
    its own motion, fades up over two frames, and its RGB split settles. Centre it on the layer's own centre."""
    if k < 0:
        return None

    def scale(j: float) -> float:
        return s0 + (1 - s0) * ease_out_cubic(j / dur)

    acc = scaled(layer, scale(k), scale(k + 1))
    acc[..., 3] *= min(1.0, (k + 1) / 2)
    split = int(round(split0 * (1 - min(1.0, (k + 1) / dur)) ** 2))
    return ts.rgb_split(acc, split) if split else acc


def pop(layer: np.ndarray, k: int, dur: int = 8, s0: float = 0.55, overshoot: float = 1.9) -> np.ndarray | None:
    """A layer popping up, k frames after it starts: it grows from s0 past its size and settles back over `dur`
    frames, fading up over two. A friendlier entrance than a slam."""
    if k < 0:
        return None
    s = s0 + (1 - s0) * ease_out_back(k / dur, overshoot)
    out = scaled(layer, max(0.01, s))
    out[..., 3] *= min(1.0, (k + 1) / 2)
    return out


def decode(text: str, k: int, seed: int, settle: int = 14, spread: int = 10) -> str:
    """A line resolving out of noise: each character cycles random glyphs, then settles at a frame of its own (within
    `spread` of `settle`). Spaces stay spaces."""
    rng = np.random.default_rng(seed)
    at = rng.integers(settle - spread // 2, settle + spread // 2 + 1, len(text))
    out = []
    for i, ch in enumerate(text):
        if ch == " " or k >= at[i]:
            out.append(ch)
        elif k < at[i] - spread:
            out.append(" ")
        else:
            out.append(GLYPHS[(i * 7 + k * 13 + seed) % len(GLYPHS)])
    return "".join(out)


# --- Frames -------------------------------------------------------------------------------------------------------

def shake(img: np.ndarray, amount: float, seed: int) -> np.ndarray:
    """A camera hit in post: a few pixels of translation, a fraction of a degree and a slight push in (so the edges
    never show). Picture only: shake the frame, then put the text on."""
    if amount <= 0:
        return img
    h, w = img.shape[:2]
    rng = np.random.default_rng(seed)
    k = w / 1920
    dx, dy = rng.normal(0, 14 * amount * k), rng.normal(0, 9 * amount * k)
    m = cv2.getRotationMatrix2D((w / 2, h / 2), rng.normal(0, 0.35 * amount), 1.0 + 0.012 * amount)
    m[0, 2] += dx
    m[1, 2] += dy
    return cv2.warpAffine(img, m, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def chroma(img: np.ndarray, amount: float) -> np.ndarray:
    """A radial chromatic split, red scaled out and blue in about the centre, for the frame of a hit."""
    if amount <= 0:
        return img
    h, w = img.shape[:2]
    out = img.copy()
    for c, s in ((0, 1 + 0.004 * amount), (2, 1 - 0.004 * amount)):
        m = cv2.getRotationMatrix2D((w / 2, h / 2), 0, s)
        out[..., c] = cv2.warpAffine(img[..., c], m, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return out


def zoom_blur(img: np.ndarray, cx: float, cy: float, amount: float, n: int = 10) -> np.ndarray:
    """A radial blur about (cx, cy) in pixels: the frame averaged with itself scaled up to 1 + amount (a punch-in,
    a rush)."""
    if amount <= 0.001:
        return img
    h, w = img.shape[:2]
    acc = np.zeros_like(img)
    for j in range(n):
        s = 1 + amount * j / (n - 1)
        m = np.array([[s, 0, cx - s * cx], [0, s, cy - s * cy]], np.float32)
        acc += cv2.warpAffine(img, m, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return acc / n


def whip(img: np.ndarray, dx: float) -> np.ndarray:
    """A whip pan's smear: the frame averaged along a horizontal sweep of dx pixels. Cut on the smear's peak."""
    n = max(1, int(abs(dx)))
    if n < 2:
        return img
    k = np.full((1, n), 1.0 / n, np.float32)
    return cv2.filter2D(img, -1, k, borderType=cv2.BORDER_REFLECT)


def tear(img: np.ndarray, amount: float, seed: int, bands: int = 9) -> np.ndarray:
    """Bands of rows slid sideways, each band's channels parted: a digital tear."""
    rng = np.random.default_rng(seed)
    out = img.copy()
    h = img.shape[0]
    for _ in range(int(bands * (0.4 + amount))):
        y0 = int(rng.uniform(0, h))
        bh = int(rng.uniform(3, 18 + 110 * amount))
        dx = int(rng.normal(0, 30 + 240 * amount))
        band = np.roll(img[y0:y0 + bh], dx, axis=1)
        if amount > 0.3:
            band = band.copy()
            band[..., 0] = np.roll(band[..., 0], int(8 * amount), axis=1)
            band[..., 2] = np.roll(band[..., 2], -int(8 * amount), axis=1)
        out[y0:y0 + bh] = band
    return out


def datamosh(a: np.ndarray, b: np.ndarray, k: float, seed: int, block: int = 24) -> np.ndarray:
    """A datamosh from a into b (k from 0 to 1): a's picture dragged along a blocky motion field that grows with k,
    blocks of b breaking through more and more."""
    h, w = a.shape[:2]
    bh, bw = h // block + 1, w // block + 1
    rng = np.random.default_rng(seed)
    vx = cv2.resize(rng.standard_normal((4, 7)).astype(np.float32), (bw, bh), interpolation=cv2.INTER_CUBIC)
    vy = cv2.resize(rng.standard_normal((4, 7)).astype(np.float32), (bw, bh), interpolation=cv2.INTER_CUBIC)
    amp = 140.0 * k * k * w / 1920
    vx = cv2.resize(vx * amp, (w, h), interpolation=cv2.INTER_NEAREST)
    vy = cv2.resize(vy * amp * 0.35, (w, h), interpolation=cv2.INTER_NEAREST)
    xx, yy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    smear = cv2.remap(a, xx - vx, yy - vy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    pick = rng.random((bh, bw)).astype(np.float32) < k
    pick = cv2.resize(pick.astype(np.float32), (w, h), interpolation=cv2.INTER_NEAREST)[..., None]
    return smear * (1 - pick) + b * pick


def vignette_pulse(img: np.ndarray, amount: float) -> np.ndarray:
    """The frame's edges pulled down toward black (a squeeze on a beat)."""
    h, w = img.shape[:2]
    xx, yy = np.meshgrid(np.linspace(-1, 1, w, dtype=np.float32), np.linspace(-1, 1, h, dtype=np.float32))
    v = np.clip(1 - amount * (xx * xx * 0.6 + yy * yy) ** 1.2, 0, 1)
    return img * v[..., None]
