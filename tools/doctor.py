"""Is this machine ready to make a Short? Checks everything the pipeline needs and says how to fix what's missing.

    python tools/doctor.py
"""

from __future__ import annotations

import importlib
import os
import shutil
import socket
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "roblox"))

rows: list[tuple[bool, str, str]] = []


def check(ok: bool, what: str, fix: str = "") -> None:
    rows.append((ok, what, fix))


def main() -> int:
    check(sys.version_info >= (3, 10), f"Python {sys.version.split()[0]} (3.10 or newer)", "install Python 3.11")
    for mod, pkg in (("numpy", "numpy"), ("scipy", "scipy"), ("cv2", "opencv-python"), ("PIL", "Pillow"),
                     ("soundfile", "soundfile"), ("faster_whisper", "faster-whisper"), ("requests", "requests")):
        try:
            importlib.import_module(mod)
            check(True, f"Python package {pkg}")
        except ImportError:
            check(False, f"Python package {pkg}", "pip install -r requirements.txt")
    for exe in ("ffmpeg", "ffprobe"):
        check(bool(shutil.which(exe)), f"{exe} on the PATH", "install FFmpeg (a full build) and add it to the PATH")
    fonts = os.path.join(ROOT, "assets", "fonts", "montserrat", "Montserrat-SemiBold.ttf")
    check(os.path.exists(fonts), "caption font (Montserrat)", "git checkout assets/")
    emoji = os.path.join(ROOT, "assets", "emoji", "noto")
    check(os.path.isdir(emoji) and len(os.listdir(emoji)) > 40, "caption emoji (Noto)", "git checkout assets/")
    running = False
    if sys.platform == "win32":
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq RobloxStudioBeta.exe"], capture_output=True,
                             text=True).stdout
        running = "RobloxStudioBeta.exe" in out
    check(running, "Roblox Studio running", "open Studio on a Baseplate place, uncovered on its own monitor "
          "(docs/ROBLOX_CAPTURE.md)")
    try:
        with socket.create_connection(("127.0.0.1", 47321), timeout=1):
            check(True, "the Studio bridge (port 47321)")
    except OSError:
        check(False, "the Studio bridge (port 47321)", "python tools/roblox/studio_mcp.py serve  (in the background)")
    try:
        import faces
        d = os.path.join(faces.content_dir(), "textures", faces.SET)
        n = len([f for f in os.listdir(d) if f.endswith(".png")]) if os.path.isdir(d) else 0
        check(n >= 40, f"faces installed in Studio ({n})", "python tests/studio_library.py faces")
    except SystemExit:
        check(False, "faces installed in Studio", "install Roblox Studio first")
    lib = os.path.join(ROOT, "build", "library", "music")
    beds = [f for f in os.listdir(lib)] if os.path.isdir(lib) else []
    check(bool(beds), f"music beds in build/library/music ({len(beds)})",
          "make or download them (skill/roblox-shorts/assets.md, Music)")
    skill = os.path.join(os.path.expanduser("~"), ".claude", "skills", "roblox-shorts", "SKILL.md")
    check(os.path.exists(skill), "the skill installed for Claude Code", "python tools/install_skill.py")
    rows.append((True, "voices: the ElevenLabs connector in the agent session (checked when the skill runs)", ""))
    width = max(len(w) for _, w, _ in rows)
    bad = 0
    for ok, what, fix in rows:
        bad += not ok
        print(f"  {'ok ' if ok else 'NO '} {what.ljust(width)}" + ("" if ok else f"   -> {fix}"))
    print(f"\n{'Ready.' if not bad else f'{bad} thing(s) to fix first.'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
