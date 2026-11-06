"""A small stdio MCP client for Roblox Studio's built-in MCP server (StudioMCP.exe), and a bridge that keeps one
session open so scripts can call it many times a second (docs/ROBLOX_CAPTURE.md, "The bridge").

    python tools/roblox/studio_mcp.py serve              keep one session open; listen on 127.0.0.1:PORT
    python tools/roblox/studio_mcp.py list               the tools and their input schemas
    python tools/roblox/studio_mcp.py call TOOL [ARGS]   ARGS: inline JSON or @file.json; --code FILE puts a file's
                                                         text in args["code"]; images are saved under --out DIR

With the bridge running, list and call go through it; otherwise each call starts a session of its own (slow: a few
seconds each). Every call but list_roblox_studios needs a studio_id: when ARGS has none, the one open Studio is used,
or the one whose name contains STUDIO_PLACE.

Environment: STUDIO_MCP_EXE (the server; found automatically on Windows), STUDIO_MCP_PORT (47321), STUDIO_PLACE,
STUDIO_ID, DM (the default datamodel_type: Edit).
"""

from __future__ import annotations

import base64
import glob
import itertools
import json
import os
import socket
import subprocess
import sys
import threading
import time

PORT = int(os.environ.get("STUDIO_MCP_PORT", "47321"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOG = os.environ.get("STUDIO_MCP_LOG", os.path.join(ROOT, "build", "studio_mcp.log"))


def find_exe() -> str:
    """STUDIO_MCP_EXE; else beside the Studio the registry names (what Roblox's own mcp.bat does); else the newest
    under %LOCALAPPDATA%\\Roblox\\Versions."""
    env = os.environ.get("STUDIO_MCP_EXE")
    if env:
        return env
    if sys.platform == "win32":
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Roblox\RobloxStudio") as k:
                content, _ = winreg.QueryValueEx(k, "ContentFolder")
            exe = os.path.normpath(os.path.join(content, "..", "StudioMCP.exe"))
            if os.path.exists(exe):
                return exe
        except OSError:
            pass
        found = glob.glob(os.path.join(os.environ.get("LOCALAPPDATA", ""), "Roblox", "Versions", "*", "StudioMCP.exe"))
        if found:
            return max(found, key=os.path.getmtime)
    raise SystemExit("StudioMCP.exe not found: set STUDIO_MCP_EXE to its path (it ships with Roblox Studio)")


class Session:
    def __init__(self, log=None):
        self.log = log or (lambda s: None)
        self.p = subprocess.Popen([find_exe()], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  bufsize=0)
        self.ids = itertools.count(1)
        self.pending: dict = {}
        self.lock = threading.Lock()
        self.wlock = threading.Lock()
        threading.Thread(target=self._read, daemon=True).start()
        threading.Thread(target=self._read_err, daemon=True).start()
        init = self.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                           "clientInfo": {"name": "vid-editing-bridge", "version": "1.0"}}, timeout=60)
        self.server_info = init.get("result", {})
        self.notify("notifications/initialized", {})

    def _send(self, msg):
        data = (json.dumps(msg) + "\n").encode("utf-8")
        with self.wlock:
            self.p.stdin.write(data)
            self.p.stdin.flush()

    def _read(self):
        buf = b""
        while True:
            chunk = self.p.stdout.readline()
            if not chunk:
                break
            buf += chunk
            try:
                msg = json.loads(buf.decode("utf-8"))
            except json.JSONDecodeError:
                continue  # a message split across lines
            buf = b""
            if "method" in msg and "id" in msg:  # a request from the server: answer ping, refuse the rest
                if msg["method"] == "ping":
                    self._send({"jsonrpc": "2.0", "id": msg["id"], "result": {}})
                elif msg["method"] == "roots/list":
                    self._send({"jsonrpc": "2.0", "id": msg["id"], "result": {"roots": []}})
                else:
                    self._send({"jsonrpc": "2.0", "id": msg["id"],
                                "error": {"code": -32601, "message": "not supported by this client"}})
                continue
            if "id" in msg:
                with self.lock:
                    slot = self.pending.get(msg["id"])
                if slot:
                    slot["msg"] = msg
                    slot["ev"].set()
            else:
                self.log("notification: " + json.dumps(msg)[:500])

    def _read_err(self):
        for line in self.p.stderr:
            self.log("stderr: " + line.decode("utf-8", "replace").rstrip())

    def request(self, method, params, timeout=120):
        rid = next(self.ids)
        slot = {"ev": threading.Event(), "msg": None}
        with self.lock:
            self.pending[rid] = slot
        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        ok = slot["ev"].wait(timeout)
        with self.lock:
            self.pending.pop(rid, None)
        if not ok:
            return {"error": {"code": -1, "message": f"timeout after {timeout}s waiting for {method}"}}
        return slot["msg"]

    def notify(self, method, params):
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def alive(self):
        return self.p.poll() is None


def serve():
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    logf = open(LOG, "a", encoding="utf-8")

    def log(s):
        logf.write(time.strftime("%H:%M:%S ") + s + "\n")
        logf.flush()

    state = {"s": Session(log)}
    log("session up: " + json.dumps(state["s"].server_info)[:300])
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", PORT))
    srv.listen(8)
    print(f"bridge listening on 127.0.0.1:{PORT}", flush=True)

    def handle(conn):
        with conn:
            data = b""
            while not data.endswith(b"\n"):
                chunk = conn.recv(1 << 20)
                if not chunk:
                    break
                data += chunk
            req = json.loads(data.decode("utf-8"))
            if not state["s"].alive():
                log("StudioMCP exited; restarting")
                state["s"] = Session(log)
            t0 = time.time()
            res = state["s"].request(req["method"], req.get("params", {}), timeout=req.get("timeout", 120))
            log(f"{req['method']} {req.get('params', {}).get('name', '')} {time.time() - t0:.1f}s")
            conn.sendall((json.dumps(res) + "\n").encode("utf-8"))

    while True:
        conn, _ = srv.accept()
        threading.Thread(target=handle, args=(conn,), daemon=True).start()


def via_server(method, params, timeout):
    try:
        conn = socket.create_connection(("127.0.0.1", PORT), timeout=3)
    except OSError:
        return None
    with conn:
        conn.settimeout(timeout + 30)
        conn.sendall((json.dumps({"method": method, "params": params, "timeout": timeout}) + "\n").encode("utf-8"))
        data = b""
        while not data.endswith(b"\n"):
            chunk = conn.recv(1 << 22)
            if not chunk:
                break
            data += chunk
    return json.loads(data.decode("utf-8"))


def rpc(method, params, timeout=120):
    res = via_server(method, params, timeout)
    if res is None:
        s = Session(lambda m: sys.stderr.write(m + "\n"))
        try:
            res = s.request(method, params, timeout)
        finally:
            s.p.kill()
    return res


def studios(timeout=60) -> list[dict]:
    """The open Studios: [{"id": ..., "name": "Place name (placeId: N)"}]."""
    res = rpc("tools/call", {"name": "list_roblox_studios", "arguments": {}}, timeout)
    for item in res.get("result", {}).get("content", []):
        if item.get("type") == "text":
            try:
                return json.loads(item["text"]).get("studios", [])
            except (json.JSONDecodeError, AttributeError):
                pass
    return []


def pick_studio() -> str:
    """STUDIO_ID; else the one open Studio; else the one whose name contains STUDIO_PLACE."""
    if os.environ.get("STUDIO_ID"):
        return os.environ["STUDIO_ID"]
    found = studios()
    want = os.environ.get("STUDIO_PLACE", "")
    match = [s for s in found if want and want.lower() in s.get("name", "").lower()] if want else found
    if len(match) == 1:
        return match[0]["id"]
    names = "; ".join(f"{s.get('name')} = {s.get('id')}" for s in found) or "none open"
    raise SystemExit(f"which Studio? set STUDIO_PLACE or STUDIO_ID ({names})")


def show(res, out_dir):
    if res.get("error"):
        print("ERROR: " + json.dumps(res["error"]))
        return 1
    result = res.get("result", {})
    n = 0
    for item in result.get("content", []):
        if item.get("type") == "text":
            print(item["text"])
        elif item.get("type") == "image":
            os.makedirs(out_dir, exist_ok=True)
            n += 1
            ext = ".png" if "png" in item.get("mimeType", "png") else ".jpg"
            path = os.path.join(out_dir, time.strftime("cap_%H%M%S") + f"_{n}{ext}")
            with open(path, "wb") as f:
                f.write(base64.b64decode(item["data"]))
            print("IMAGE: " + path)
        else:
            print(json.dumps(item)[:2000])
    if "structuredContent" in result and not result.get("content"):
        print(json.dumps(result["structuredContent"], indent=1))
    return 1 if result.get("isError") else 0


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    cmd = args.pop(0)
    timeout, out_dir, code_file, rest = 120.0, os.path.join(ROOT, "build", "captures"), None, []
    while args:
        a = args.pop(0)
        if a == "--timeout":
            timeout = float(args.pop(0))
        elif a == "--out":
            out_dir = args.pop(0)
        elif a == "--code":
            code_file = args.pop(0)
        else:
            rest.append(a)
    if cmd == "serve":
        serve()
        return 0
    if cmd == "list":
        res = rpc("tools/list", {}, timeout)
        for t in res.get("result", {}).get("tools", []):
            print("== " + t["name"])
            print((t.get("description") or "").strip())
            print(json.dumps(t.get("inputSchema", {}), indent=1))
        return 0
    if cmd == "call":
        name = rest[0]
        arguments = {}
        if len(rest) > 1:
            raw = rest[1]
            if raw.startswith("@"):
                with open(raw[1:], encoding="utf-8") as f:
                    raw = f.read()
            arguments = json.loads(raw)
        if code_file:
            with open(code_file, encoding="utf-8") as f:
                arguments["code"] = f.read()
        if name != "list_roblox_studios" and "studio_id" not in arguments:
            arguments["studio_id"] = pick_studio()
        if name in ("execute_luau", "search_game_tree", "inspect_instance") and "datamodel_type" not in arguments:
            arguments["datamodel_type"] = os.environ.get("DM", "Edit")
        return show(rpc("tools/call", {"name": name, "arguments": arguments}, timeout), out_dir)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
