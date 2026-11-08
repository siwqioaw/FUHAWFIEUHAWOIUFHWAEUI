"""Install the roblox-shorts skill for every agent on this machine: a copy of skill/roblox-shorts in each skills
folder that exists (~/.claude/skills, ~/.agents/skills, ~/.codex/skills), with REPO.txt naming this checkout so the
skill can find its tools.

    python tools/install_skill.py            # install or update
    python tools/install_skill.py --remove   # take it out again
"""

from __future__ import annotations

import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "skill", "roblox-shorts")
HOMES = [os.path.join(os.path.expanduser("~"), d, "skills") for d in (".claude", ".agents", ".codex")]


def main() -> int:
    remove = "--remove" in sys.argv
    done = []
    for home in HOMES:
        if not os.path.isdir(os.path.dirname(home)):
            continue  # that agent isn't installed here
        dest = os.path.join(home, "roblox-shorts")
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        if remove:
            done.append(f"removed {dest}")
            continue
        os.makedirs(home, exist_ok=True)
        shutil.copytree(SRC, dest)
        with open(os.path.join(dest, "REPO.txt"), "w", encoding="utf-8") as f:
            f.write(ROOT + "\n")
        done.append(f"installed {dest}")
    print("\n".join(done) or "no agent skills folder found (~/.claude, ~/.agents or ~/.codex)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
