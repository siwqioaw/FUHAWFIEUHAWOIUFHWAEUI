"""Face textures for R6 actors, rendered from Studio's own content folder (docs/ROBLOX_CAPTURE.md, "Faces").

An R6 head wears its face as a Decal named "face". The harness sets that decal's texture per frame (an actor's
"face" key), so a face changes on any frame we choose, with no lip sync, as in the references. A texture can be:

- a file in Studio's content folder, `rbxasset://textures/<set>/<name>.png`: drawn here, installed by install(),
  never uploaded. It renders in edit mode and in playtests on this machine only, which is all a capture needs. A
  Studio update makes a new version folder without it: install() again (take() can't tell, but the face would come
  out as Studio's blank texture).
- an uploaded image, `rbxassetid://N`, for a face that must also show outside this machine.

    import faces
    urls = faces.install("build/faces/test")            # every PNG in the folder -> {name: url}
    faces.url("smile")                                   # rbxasset://textures/vidfaces/smile.png

    python tools/roblox/faces.py test [OUT_DIR]          # draw the three-face test set and install it

A face image is square with a transparent background, the features inside the middle of the frame: Roblox's default
face (`content/textures/face.png`, 128 x 128) keeps them within x 42-88 and y 27-101.
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys

SET = "vidfaces"


def content_dir() -> str:
    """The running Studio's content folder: beside the running RobloxStudioBeta.exe; else the newest version folder
    that has one. Not the registry's ContentFolder: on 2026-11-07 it still named the version before an update, so faces
    installed there never showed."""
    if sys.platform == "win32":
        try:
            exe = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-Process RobloxStudioBeta -ErrorAction SilentlyContinue | Select-Object -First 1).Path"],
                capture_output=True, text=True, timeout=30).stdout.strip()
            if exe and os.path.isdir(os.path.join(os.path.dirname(exe), "content")):
                return os.path.join(os.path.dirname(exe), "content")
        except (OSError, subprocess.SubprocessError):
            pass
    found = [os.path.dirname(p) for p in
             glob.glob(os.path.join(os.environ.get("LOCALAPPDATA", ""), "Roblox", "Versions", "*", "RobloxStudioBeta.exe"))]
    found = [os.path.join(d, "content") for d in found if os.path.isdir(os.path.join(d, "content"))]
    if not found:
        raise SystemExit("Studio's content folder not found: is Studio installed?")
    return max(found, key=lambda d: os.path.getmtime(os.path.dirname(d)))


def url(name: str, face_set: str = SET) -> str:
    return f"rbxasset://textures/{face_set}/{name}.png"


def install(src_dir: str, face_set: str = SET) -> dict[str, str]:
    """Copy every PNG in src_dir into Studio's content/textures/<face_set>/ (replacing what's there). Returns
    {name: url}. Only adds files under its own folder; remove() takes them out again."""
    dest = os.path.join(content_dir(), "textures", face_set)
    os.makedirs(dest, exist_ok=True)
    out = {}
    for path in sorted(glob.glob(os.path.join(src_dir, "*.png"))):
        name = os.path.splitext(os.path.basename(path))[0]
        shutil.copyfile(path, os.path.join(dest, name + ".png"))
        out[name] = url(name, face_set)
    return out


def remove(face_set: str = SET) -> None:
    shutil.rmtree(os.path.join(content_dir(), "textures", face_set), ignore_errors=True)


def test_set(out_dir: str, size: int = 512) -> list[str]:
    """Three simple faces in black line art (smile, shock, angry), for testing swaps before the real set exists."""
    from PIL import Image, ImageDraw

    os.makedirs(out_dir, exist_ok=True)
    s = size / 512
    w = int(round(16 * s))

    def canvas():
        im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        return im, ImageDraw.Draw(im)

    def p(*xy):
        return [v * s for v in xy]

    paths = []
    im, d = canvas()  # smile: closed happy eyes, a wide open grin
    for cx in (190, 322):
        d.arc(p(cx - 42, 170, cx + 42, 250), 200, 340, fill="black", width=w)
    d.chord(p(170, 270, 342, 400), 0, 180, fill=(40, 10, 10, 255), outline="black", width=w)
    d.rectangle(p(190, 343, 322, 362), fill="white")  # teeth under the chord's flat top edge (y = 335)
    paths.append(os.path.join(out_dir, "smile.png"))
    im.save(paths[-1])

    im, d = canvas()  # shock: big round white eyes, small pupils, a small "o"
    for cx in (190, 322):
        d.ellipse(p(cx - 52, 150, cx + 52, 254), fill="white", outline="black", width=w)
        d.ellipse(p(cx - 13, 189, cx + 13, 215), fill="black")
    d.ellipse(p(232, 300, 280, 366), fill=(40, 10, 10, 255), outline="black", width=w)
    paths.append(os.path.join(out_dir, "shock.png"))
    im.save(paths[-1])

    im, d = canvas()  # angry: slanted brows, narrowed eyes, gritted teeth
    d.line(p(140, 160, 236, 196), fill="black", width=int(round(22 * s)))
    d.line(p(276, 196, 372, 160), fill="black", width=int(round(22 * s)))
    for cx in (190, 322):
        d.ellipse(p(cx - 30, 212, cx + 30, 252), fill="black")
    d.rectangle(p(186, 300, 326, 360), fill="white", outline="black", width=w)
    for x in (221, 256, 291):
        d.line(p(x, 300, x, 360), fill="black", width=int(round(8 * s)))
    d.line(p(186, 330, 326, 330), fill="black", width=int(round(8 * s)))
    paths.append(os.path.join(out_dir, "angry.png"))
    im.save(paths[-1])
    return paths


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "test":
        out = sys.argv[2] if len(sys.argv) > 2 else os.path.join("build", "faces", "test")
        test_set(out)
        for name, u in install(out).items():
            print(f"{name}: {u}")
        print("installed in", os.path.join(content_dir(), "textures", SET))
    else:
        print(__doc__)
