"""Drive Roblox Studio from Python through its built-in MCP server (docs/ROBLOX_CAPTURE.md).

    import studio
    studio.luau("return game.Name")                          # edit mode
    studio.play(True); studio.wait_for("Client")              # start a playtest, wait for its client
    studio.luau("return workspace.CurrentCamera.CFrame", dm="Client")
    studio.server("out(#game.Players:GetPlayers())")          # inside the playtest's server, with the game's modules
    studio.capture("build/shot.png")                          # the viewport as it is
    studio.play(False)

Start the bridge first (`python tools/roblox/studio_mcp.py serve`, in the background) or every call opens a session
of its own, which takes seconds. Pick the Studio with STUDIO_PLACE (part of its name) when more than one is open.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import studio_mcp  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
_sid: str | None = None


def studio_id() -> str:
    global _sid
    if _sid is None:
        _sid = studio_mcp.pick_studio()
    return _sid


def tool(name: str, args: dict, timeout: float = 120) -> dict:
    res = studio_mcp.rpc("tools/call", {"name": name, "arguments": {"studio_id": studio_id(), **args}}, timeout)
    if res.get("error"):
        raise RuntimeError(f"{name}: {res['error']}")
    return res.get("result", {})


def _text(result: dict) -> str:
    return "\n".join(c.get("text", "") for c in result.get("content", []) if c.get("type") == "text")


def luau(code: str, dm: str = "Edit", timeout: float = 120) -> str:
    """Run Luau in a datamodel (Edit, or during a playtest Server or Client) and return what it returns, as text.

    It runs without the plugin-level capabilities, and its answer is cut at about 100 KB: summarise in Luau. Code that
    runs for more than a few seconds without yielding comes back "not reachable" though Studio finishes it: run long
    work in task.spawn and poll for its result. On the Server, `require` here gets fresh copies of modules, not the
    running game's: use server() to reach the game's own state."""
    result = tool("execute_luau", {"datamodel_type": dm, "code": code}, timeout)
    text = _text(result)
    if result.get("isError"):
        raise RuntimeError(text[:2000])
    return text


def server(body: str, wait: float = 1.0, timeout: float = 120) -> str:
    """Run `body` (Luau statements; call out(text) to return a result) inside the running game's server, as a Script
    in ServerScriptService, so it shares the game's module instances."""
    source = ("local function out(t) script:SetAttribute('Out', tostring(t)) end\n" + body +
              "\nscript:SetAttribute('Done', true)")
    code = (
        "local s = Instance.new('Script')\n"
        "s.Name = '_CaptureServerTask'\n"
        f"s.Source = {json.dumps(source)}\n"
        "s.Parent = game:GetService('ServerScriptService')\n"
        "local t0 = os.clock()\n"
        f"while not s:GetAttribute('Done') and os.clock() - t0 < {max(wait, 1.0) + 10} do task.wait(0.05) end\n"
        "local o = s:GetAttribute('Out') s:Destroy() return tostring(o)"
    )
    return luau(code, dm="Server", timeout=timeout)


def capture(path: str, retries: int = 3, camera: list | None = None, look_at: list | None = None) -> str:
    """The viewport, saved to `path` (at the viewport's own size: size Studio's window for the pixels you need).
    In edit mode, `camera` and `look_at` (world positions) place the view for the capture."""
    args: dict = {"capture_id": f"cap_{int(time.time() * 1000)}"}
    if camera is not None:
        args["camera_position"], args["look_at_position"] = camera, look_at
    for attempt in range(retries):
        for item in tool("screen_capture", args, 90).get("content", []):
            if item.get("type") == "image":
                os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
                with open(path, "wb") as f:
                    f.write(base64.b64decode(item["data"]))
                return path
        time.sleep(0.5 * (attempt + 1))
    raise RuntimeError("no image in the capture: is Studio's window minimized?")


def play(on: bool = True) -> str:
    """Start or stop a playtest. It plays as the signed-in account, with the place's API access: anything the game
    saves (a profile, settings) is saved for real."""
    return _text(tool("start_stop_play", {"is_start": on}, 120))


def state() -> str:
    return _text(tool("get_studio_state", {}, 60))


def wait_for(dm: str = "Client", timeout: float = 60) -> None:
    """Wait until a playtest's datamodel answers."""
    t0 = time.time()
    while True:
        try:
            if luau("return 'ok'", dm=dm, timeout=15).strip().endswith("ok"):
                return
        except RuntimeError:
            pass
        if time.time() - t0 > timeout:
            raise RuntimeError(f"the {dm} datamodel didn't answer in {timeout:.0f} s")
        time.sleep(1.0)


def console() -> str:
    return _text(tool("get_console_output", {}, 60))


def read(name: str) -> str:
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return f.read()
