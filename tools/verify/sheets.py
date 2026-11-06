"""Stills to look at, pulled from the delivered video (docs/VERIFY.md, "Picture"):

    python tools/verify/sheets.py contact VIDEO.mp4 [--every 6] [--timeline cut.json] [--out DIR]
        dense contact sheets: a frame every N, each labelled with its time (and clip, with a timeline)
    python tools/verify/sheets.py cuts VIDEO.mp4 --timeline cut.json [--out DIR]
        the two frames before and the two after every cut, a row per cut
    python tools/verify/sheets.py frames VIDEO.mp4 FRAME [FRAME ...] [--out DIR]
        single frames at full size, to look at anything a tile left in doubt

Look at the full-size frames before calling anything fine: a contact sheet's tiles are small, and the misplaced
overlay that got a cut rejected was a few dozen pixels.
"""

from __future__ import annotations

import argparse
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import media  # noqa: E402
from timeline import Timeline  # noqa: E402


def tile(paths: list[str], labels: list[str], dest: str, cols: int, tile_w: int) -> str:
    ims = [Image.open(p).convert("RGB") for p in paths]
    tile_h = int(tile_w * ims[0].height / ims[0].width)
    rows = (len(ims) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * tile_w, rows * tile_h), (12, 12, 12))
    d = ImageDraw.Draw(canvas)
    for i, (im, text) in enumerate(zip(ims, labels)):
        x, y = (i % cols) * tile_w, (i // cols) * tile_h
        canvas.paste(im.resize((tile_w, tile_h), Image.LANCZOS), (x, y))
        d.rectangle((x, y, x + 8 + 7 * len(text), y + 16), fill=(0, 0, 0))
        d.text((x + 4, y + 2), text, fill=(255, 220, 0))
    canvas.save(dest, quality=88)
    return dest


def contact(video: str, every: int, tl: Timeline | None, out: str, per_sheet: int = 40) -> list[str]:
    info = media.probe(video)
    v = media.video_stream(info)
    n = int(v.get("nb_frames") or round(float(info["format"]["duration"]) * media.fps_of(info)))
    fps = media.fps_of(info)
    frames = list(range(0, n, every))
    portrait = int(v["height"]) > int(v["width"])
    paths = media.extract_frames(video, frames, os.path.join(out, "_contact"), width=360 if portrait else 640)
    labels = []
    for f in frames:
        lab = f"{f / fps:.2f}s"
        if tl:
            name, off = tl.clip_at(f)
            lab += f" {name}+{off}"
        labels.append(lab)
    cols = 10 if portrait else 8
    sheets = []
    for k in range(0, len(frames), per_sheet):
        chunk = [f for f in frames[k:k + per_sheet] if f in paths]
        dest = os.path.join(out, f"contact_{k // per_sheet:02d}.jpg")
        sheets.append(tile([paths[f] for f in chunk], labels[k:k + len(chunk)], dest, cols, 200 if portrait else 320))
    return sheets


def cuts(video: str, tl: Timeline, out: str, per_sheet: int = 6) -> list[str]:
    rows: list[tuple[int, str]] = []
    for a, b, f in tl.cuts():
        for r, tag in ((f - 2, f"{a} -2"), (f - 1, f"{a} -1"), (f, f"{b} 0"), (f + 1, f"{b} +1")):
            rows.append((r, f"{tag}  {tl.sec(r):.2f}s"))
    info = media.probe(video)
    portrait = int(media.video_stream(info)["height"]) > int(media.video_stream(info)["width"])
    paths = media.extract_frames(video, [r for r, _ in rows], os.path.join(out, "_cuts"),
                                 width=360 if portrait else 640)
    sheets = []
    for k in range(0, len(rows), per_sheet * 4):
        chunk = [(r, lab) for r, lab in rows[k:k + per_sheet * 4] if r in paths]
        dest = os.path.join(out, f"cuts_{k // (per_sheet * 4):02d}.jpg")
        sheets.append(tile([paths[r] for r, _ in chunk], [lab for _, lab in chunk], dest, 4, 240 if portrait else 400))
    return sheets


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=["contact", "cuts", "frames"])
    ap.add_argument("video")
    ap.add_argument("frame", nargs="*", type=int)
    ap.add_argument("--every", type=int, default=6)
    ap.add_argument("--timeline")
    ap.add_argument("--out", default="build/verify")
    args = ap.parse_args()
    tl = Timeline.load(args.timeline) if args.timeline else None
    os.makedirs(args.out, exist_ok=True)
    if args.what == "contact":
        out = contact(args.video, args.every, tl, args.out)
    elif args.what == "cuts":
        if not tl:
            ap.error("cuts needs --timeline")
        out = cuts(args.video, tl, args.out)
    else:
        out = list(media.extract_frames(args.video, args.frame, os.path.join(args.out, "frames")).values())
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
