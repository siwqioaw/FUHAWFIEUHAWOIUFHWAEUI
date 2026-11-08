"""Spike S6: our captions beside the references' at full size, and laid over them.

    python tests/s6_captions.py            -> build/s6/compare_<name>.png and the measurements

For each reference frame: the reference's caption cut out and painted over (OpenCV's inpainting), ours drawn on the
same picture in the same place, then three crops side by side at full size: theirs, ours, and ours as a red ghost
over theirs (where the two differ, red or white shows). The measurements are each line's width and cap height in
our layer, against the reference's measured by eye on the full-size crops (docs/CAPTIONS.md).
"""

from __future__ import annotations

import os
import sys

import cv2
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "edit"))
import captions  # noqa: E402
import look  # noqa: E402

OUT = os.path.join(ROOT, "build", "s6")
# name: (video, time, our text, style, crop box (x0, y0, x1, y1), the reference's caption box to paint over)
SAMPLES = {
    "comedy": ("001", 1.2, "why are popular GIRLS so ANNOYING?\U0001F940", "comedy", (100, 1380, 980, 1600),
               (130, 1425, 960, 1575)),
    "story": ("006", 2.0, "until you TOUCH", "story", (220, 340, 860, 600), (310, 375, 740, 570)),
    "header": ("002", 1.0, "{pink:Mom's} old photos..", "header", (60, 150, 1020, 320), (100, 180, 990, 290)),
    "header_caps": ("014", 1.5, "WHEN THE BELL RINGS", "header", (60, 190, 1020, 420), (130, 220, 930, 400)),
}


def ref_frame(video: str, t: float) -> np.ndarray:
    import glob
    src = glob.glob(os.path.join(ROOT, "refs", "r6rants", "videos", video + "*.mp4"))[0]
    dst = os.path.join(OUT, "ref", f"{video}_{t}.png")
    if not os.path.exists(dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        import subprocess
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(t), "-i", src,
                        "-frames:v", "1", dst], check=True)
    return look.load(dst)


def paint_over(img: np.ndarray, box) -> np.ndarray:
    """The reference's caption removed: its white fill and black outline inside `box`, inpainted."""
    u8 = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    x0, y0, x1, y1 = box
    reg = u8[y0:y1, x0:x1]
    white = (reg.min(axis=2) > 215).astype(np.uint8)
    dark = (reg.max(axis=2) < 70).astype(np.uint8)
    near = cv2.dilate(white, np.ones((25, 25), np.uint8))
    mask = np.zeros(u8.shape[:2], np.uint8)
    m = cv2.dilate(((white | (dark & near)) * 255).astype(np.uint8), np.ones((5, 5), np.uint8))
    mask[y0:y1, x0:x1] = m
    bgr = cv2.cvtColor(u8, cv2.COLOR_RGB2BGR)
    fixed = cv2.inpaint(bgr, mask, 7, cv2.INPAINT_TELEA)
    return cv2.cvtColor(fixed, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0


def ghost(ref: np.ndarray, layer: np.ndarray, x: int, y: int) -> np.ndarray:
    """Ours as a red ghost over theirs: our letters' fill tinted red at 60%."""
    out = ref.copy()
    red = layer.copy()
    fill = (layer[..., :3].min(axis=2) > 0.8) & (layer[..., 3] > 0.5)
    red[..., 0], red[..., 1], red[..., 2] = 1.0, 0.1, 0.1
    red[..., 3] = np.where(fill, 0.6, 0.0)
    look.over(out, red, x, y)
    return out


def line_boxes(layer: np.ndarray) -> list[tuple[int, int, int]]:
    """Each text line's (width, fill top, fill bottom) in a caption layer: rows of white fill grouped."""
    fill = (layer[..., :3].min(axis=2) > 0.8) & (layer[..., 3] > 0.5)
    rows = np.nonzero(fill.any(axis=1))[0]
    out, start = [], rows[0]
    for a, b in zip(rows, rows[1:]):
        if b - a > 3:
            sub = fill[start:a + 1]
            cols = np.nonzero(sub.any(axis=0))[0]
            out.append((int(cols.max() - cols.min() + 1), int(start), int(a)))
            start = b
    sub = fill[start:rows[-1] + 1]
    cols = np.nonzero(sub.any(axis=0))[0]
    out.append((int(cols.max() - cols.min() + 1), int(start), int(rows[-1])))
    return out


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    for name, (video, t, text, style, crop, box) in SAMPLES.items():
        ref = ref_frame(video, t)
        clean = paint_over(ref, box)
        layer, (x, y) = captions.render(text, style)
        ours = clean.copy()
        look.over(ours, layer, x, y)
        x0, y0, x1, y1 = crop
        trio = [ref[y0:y1, x0:x1], ours[y0:y1, x0:x1], ghost(ref, layer, x, y)[y0:y1, x0:x1]]
        gap = np.ones((y1 - y0, 12, 3), np.float32) * 0.1
        sheet = np.concatenate([trio[0], gap, trio[1], gap, trio[2]], axis=1)
        look.save(os.path.join(OUT, f"compare_{name}.png"), sheet)
        look.save(os.path.join(OUT, f"ours_{name}.png"), ours)
        boxes = line_boxes(layer)
        st = captions.STYLES[style]
        print(f"{name}: {captions.lines_of(text, style)}; lines {[(w, b - a + 1) for w, a, b in boxes]} px "
              f"(width, fill height); block at x {x}, y {y}; cap {st['cap']} px, outline {st['stroke']} px")
    return 0


if __name__ == "__main__":
    sys.exit(main())
