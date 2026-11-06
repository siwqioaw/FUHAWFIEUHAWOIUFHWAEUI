"""Stills to look at, pulled from the delivered video (docs/VERIFY.md, "Picture"):

    python tools/verify/sheets.py contact VIDEO.mp4 [--every 6] [--timeline cut.json] [--out DIR]
        dense contact sheets: a frame every N, each labelled with its time (and clip, with a timeline)
    python tools/verify/sheets.py cuts VIDEO.mp4 --timeline cut.json [--out DIR]
        the two frames before and the two after every cut, a row per cut
    python tools/verify/sheets.py frames VIDEO.mp4 FRAME [FRAME ...] [--out DIR]
        single frames at full size, to look at anything a tile left in doubt
    python tools/verify/sheets.py strip VIDEO.mp4 [FRAME ...] [--from S --to S --step N] [--name NAME] [--out DIR]
        a run of frames side by side, each labelled with its number and time: to tell a cut from a fast camera
        move or snappy animation, or to see how a move eases

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


def strip(video: str, frames: list[int], out: str, name: str = "strip.jpg") -> str:
    """The given frames side by side, 8 to a row (4 for landscape), labelled with frame number and time."""
    info = media.probe(video)
    fps = media.fps_of(info)
    portrait = int(media.video_stream(info)["height"]) > int(media.video_stream(info)["width"])
    paths = media.extract_frames(video, frames, os.path.join(out, "_strip"), width=360 if portrait else 640)
    ok = [f for f in frames if f in paths]
    return tile([paths[f] for f in ok], [f"f{f} {f / fps:.2f}s" for f in ok], os.path.join(out, name),
                8 if portrait else 4, 225 if portrait else 400)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=["contact", "cuts", "frames", "strip"])
    ap.add_argument("video")
    ap.add_argument("frame", nargs="*", type=int)
    ap.add_argument("--every", type=int, default=6)
    ap.add_argument("--timeline")
    ap.add_argument("--out", default="build/verify")
    ap.add_argument("--from", dest="t0", type=float, help="strip: first second")
    ap.add_argument("--to", dest="t1", type=float, help="strip: last second")
    ap.add_argument("--step", type=int, default=2, help="strip: every Nth frame between --from and --to")
    ap.add_argument("--name", default="strip.jpg", help="strip: the sheet's file name")
    args = ap.parse_args()
    if args.what == "strip":
        frames = list(args.frame)
        if args.t0 is not None and args.t1 is not None:
            fps = media.fps_of(media.probe(args.video))
            frames += list(range(int(round(args.t0 * fps)), int(round(args.t1 * fps)) + 1, max(1, args.step)))
        if not frames:
            ap.error("strip needs frame numbers, or --from and --to")
        os.makedirs(args.out, exist_ok=True)
        print(strip(args.video, sorted(set(frames)), args.out, args.name))
        return 0
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
