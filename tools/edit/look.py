"""Picture helpers: frames are float32 RGB in 0..1 (display-referred sRGB), H x W x 3; layers are straight-alpha RGBA.

Light is averaged and blended in linear light, never in sRGB: motion-blur sub-frames averaged in sRGB come out dark
and muddy at the edges of anything bright.
"""

from __future__ import annotations

import cv2
import numpy as np

LUMA = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def load(path: str) -> np.ndarray:
    im = cv2.imread(path, cv2.IMREAD_COLOR)
    if im is None:
        raise FileNotFoundError(path)
    return cv2.cvtColor(im, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0


def save(path: str, x: np.ndarray):
    cv2.imwrite(path, cv2.cvtColor((np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8), cv2.COLOR_RGB2BGR))


def srgb_to_linear(x: np.ndarray) -> np.ndarray:
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4).astype(np.float32)


def linear_to_srgb(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, 0, None)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055).astype(np.float32)


def load_avg(paths: list[str]) -> np.ndarray:
    """Motion blur: a frame's sub-frames (captured across the shutter) averaged in linear light. On a frame where the
    camera cuts or jumps, pass only the LAST sub-frame: the first ones still show the old framing, and averaged they
    read as a double exposure."""
    acc = None
    for p in paths:
        lin = srgb_to_linear(load(p))
        acc = lin if acc is None else acc + lin
    return linear_to_srgb(acc / len(paths))


def reframe(src: np.ndarray, out_w: int, out_h: int, zoom: float = 1.0, cx: float = 0.5, cy: float = 0.5,
            sharpen: float = 0.18) -> np.ndarray:
    """Crop `src` to the out_w x out_h shape (zoom 1 = as much of the source as that shape allows) about (cx, cy) in
    source fractions, scaled with Lanczos, with a light unsharp mask for the upscale. The crop is a sub-pixel affine
    warp, so a slow digital push doesn't step from pixel to pixel."""
    sh, sw = src.shape[:2]
    aspect = out_w / out_h
    cw = sw / zoom
    ch = cw / aspect
    if ch > sh / zoom:
        ch = sh / zoom
        cw = ch * aspect
    x0 = np.clip(cx * sw - cw / 2, 0, max(0, sw - cw))
    y0 = np.clip(cy * sh - ch / 2, 0, max(0, sh - ch))
    m = np.array([[out_w / cw, 0, -x0 * out_w / cw], [0, out_h / ch, -y0 * out_h / ch]], dtype=np.float64)
    out = cv2.warpAffine(src, m, (out_w, out_h), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)
    if sharpen > 0:
        blur = cv2.GaussianBlur(out, (0, 0), 1.3)
        out = out + (out - blur) * sharpen
    return np.clip(out, 0, 1)


def fit_blurred(src: np.ndarray, out_w: int, out_h: int, blur: float = 40.0, dim: float = 0.55) -> np.ndarray:
    """A wide picture in a tall frame (a landscape capture in a 9:16 short): the whole picture fitted to the width,
    over a zoomed, blurred and darkened copy of itself filling the rest. (Not used in the trailer this kit comes from:
    there the capture was cropped.)"""
    bg = reframe(src, out_w, out_h, sharpen=0)
    bg = cv2.GaussianBlur(bg, (0, 0), blur) * dim
    sh, sw = src.shape[:2]
    h = int(round(out_w * sh / sw))
    fg = cv2.resize(src, (out_w, h), interpolation=cv2.INTER_LANCZOS4)
    y = (out_h - h) // 2
    out = bg.copy()
    out[max(0, y):y + h] = fg[max(0, -y):max(0, -y) + min(h, out_h)]
    return np.clip(out, 0, 1)


def over(base: np.ndarray, rgba: np.ndarray, x: int = 0, y: int = 0) -> np.ndarray:
    """Composite a straight-alpha RGBA layer onto an RGB frame at (x, y), in place; parts off the frame are dropped."""
    h, w = rgba.shape[:2]
    H0, W0 = base.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W0, x + w), min(H0, y + h)
    if x1 <= x0 or y1 <= y0:
        return base
    sub = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    a = sub[..., 3:4]
    base[y0:y1, x0:x1] = base[y0:y1, x0:x1] * (1 - a) + sub[..., :3] * a
    return base


def centre(base: np.ndarray, rgba: np.ndarray, cx: float, cy: float) -> np.ndarray:
    h, w = rgba.shape[:2]
    return over(base, rgba, int(round(cx - w / 2)), int(round(cy - h / 2)))


def vignette(x: np.ndarray, stops: float = 0.3) -> np.ndarray:
    h, w = x.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    s = max(w, h) / 2
    r = np.sqrt(((xx - w / 2) / s) ** 2 + ((yy - h / 2) / s) ** 2)
    v = (2.0 ** (-stops * np.clip(r / 1.15, 0, 1) ** 2.2)).astype(np.float32)
    return x * v[..., None]


def grain(x: np.ndarray, frame: int, strength: float = 0.02, size: float = 0.7) -> np.ndarray:
    """Grain at the delivery size, seeded by the frame number (so any frame renders the same on its own), strongest
    in the mid-tones."""
    rng = np.random.default_rng(1000 + frame)
    h, w = x.shape[:2]
    n = rng.standard_normal((h, w)).astype(np.float32)
    if size > 0:
        n = cv2.GaussianBlur(n, (0, 0), size)
        n /= n.std() + 1e-6
    luma = x @ LUMA
    weight = 0.55 + 1.8 * luma * (1 - luma)
    return np.clip(x + n[..., None] * strength * weight[..., None], 0, 1).astype(np.float32)


def lift_blacks(x: np.ndarray, black: float = 0.028) -> np.ndarray:
    """Blacks lifted a few percent, so dark areas keep their texture after a platform's re-encode crushes them."""
    return (black + (1 - black) * np.clip(x, 0, 1)).astype(np.float32)
