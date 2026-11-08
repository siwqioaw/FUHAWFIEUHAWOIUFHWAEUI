"""The libraries in Studio: every set from each of its cameras, and the whole cast in a line-up, as stills to look at
(docs/SETS.md, docs/FACES.md).

    python tests/studio_library.py sets [classroom hallway ...]     # build/library/sets/<set>_<cam>.png
    python tests/studio_library.py cast                             # build/library/cast/*.png and the fit report
    python tests/studio_library.py faces                            # draw the face kit and install it into Studio

Needs Studio open in the capture layout with the bridge running (docs/ROBLOX_CAPTURE.md). It plays, builds, shoots
and always cleans up: the set, the actors and the playtest.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for sub in ("roblox", "edit"):
    sys.path.insert(0, os.path.join(ROOT, "tools", sub))

import capture  # noqa: E402
import faces  # noqa: E402
import kit  # noqa: E402
import pose  # noqa: E402
import sets  # noqa: E402
import stage  # noqa: E402
import studio  # noqa: E402

OUT = os.path.join(ROOT, "build", "library")


def _still(path: str, state: dict, warmup: float = 2.0) -> str:
    d = os.path.join(OUT, "_take")
    shutil.rmtree(d, ignore_errors=True)
    capture.take(d, lambda t: state, seconds=1 / 60, fps=60, only=[0], warmup=warmup, portrait=True,
                 log=lambda m: None)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    shutil.move(os.path.join(d, "f00000.png"), path)
    return path


def _session(body) -> None:
    try:
        print(studio.play(True))
        studio.wait_for("Client", timeout=120)
        print(stage.park((0, 3, -150)))
        print(capture.install().strip()[-30:])
        body()
    finally:
        for step in (capture.release, stage.clear_actors, sets.clear, lambda: studio.play(False)):
            try:
                print(step())
            except Exception as e:  # noqa: BLE001
                print("cleanup step failed:", e)
        time.sleep(1)


def shoot_sets(names: list[str]) -> None:
    def body():
        for name in names:
            t0 = time.time()
            for opt_name, opt in (("", {}),) + ((("night", {"night": True}),) if name == "street" else ()):
                print(sets.build(name, opt))
                s = kit.SETS[name](opt)
                for cam, v in s.cams.items():
                    p = _still(os.path.join(OUT, "sets", f"{name}{'_' + opt_name if opt_name else ''}_{cam}.png"),
                               {"cam": {"pos": v["pos"], "look": v["look"]}, "fov": v["fov"], "actors": []})
                    print("  ", os.path.relpath(p, ROOT))
                print(sets.clear())
            print(f"{name}: {time.time() - t0:.0f} s")
    _session(body)


def shoot_cast() -> None:
    lib = json.load(open(os.path.join(ROOT, "tools", "roblox", "cast.json"), encoding="utf-8"))["looks"]
    names = list(lib)
    specs = {n: {k: v for k, v in lib[n].items() if k != "about"} for n in names}
    report = []

    def body():
        print(sets.build("stage_void", {"color": [150, 195, 255]}))
        for n, spec in specs.items():
            line = stage.actor(n, spec)
            report.append(line)
            print(line)
        faces_cycle = ["smile", "grin", "smug", "shock", "angry", "cute", "side_eye", "laugh", "scared", "evil",
                       "love", "cry", "deadpan", "money"]
        print(capture.preload([faces.url(f) for f in faces_cycle]))
        groups = [names[i:i + 4] for i in range(0, len(names), 4)]
        for g, group in enumerate(groups):
            actors = []
            for i, n in enumerate(names):
                if n in group:
                    k = group.index(n)
                    x = (k - (len(group) - 1) / 2) * 3.4
                    joints, rootpos = pose.at([(0.0, ["idle", "hands_on_hips", "point", "arms_crossed"][k % 4])],
                                              0.5, drift_amount=0.0, seed=k)
                    actors.append({"name": n, "cf": {"pos": [x, 3, 0], "look": [x, 3, 10]},
                                   "face": faces.url(faces_cycle[(g * 4 + k) % len(faces_cycle)]),
                                   "joints": joints, "rootpos": rootpos})
                else:
                    actors.append({"name": n, "cf": {"pos": [0 + 4 * i, 3, 400], "look": [4 * i, 3, 410]}})
            _still(os.path.join(OUT, "cast", f"lineup_{g + 1}.png"),
                   {"cam": {"pos": [0, 4.2, 13.5], "look": [0, 3.6, 0]}, "fov": 50, "actors": actors})
            print("lineup", g + 1, group)
    _session(body)
    with open(os.path.join(OUT, "cast", "fit_report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print("MISFIT" if any("MISFIT" in r or "FAILED" in r for r in report) else "every look fits R6")


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sets"
    if cmd == "faces":
        import facekit
        out = os.path.join(ROOT, "build", "faces", "kit")
        facekit.build(out)
        print(f"installed {len(faces.install(out))} faces into {faces.content_dir()}")
    elif cmd == "sets":
        shoot_sets(sys.argv[2:] or list(kit.SETS))
    elif cmd == "cast":
        shoot_cast()
    return 0


if __name__ == "__main__":
    sys.exit(main())
