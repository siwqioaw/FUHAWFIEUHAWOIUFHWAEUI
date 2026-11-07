"""Stage a playtest's server for capture (docs/ROBLOX_CAPTURE.md, "Actors"): stand-in actors for the harness to
pose, and the local player's character parked out of the way.

    import stage
    stage.actors({"kid": {"skin": (255, 204, 153), "hair": [9243992729], "face_acc": [130858694386007],
                          "shirt": 4047884046, "pants": 382538503, "face": faces.url("smile")}})
    stage.park((0, 3, -60))          # the player's own character, anchored out of shot
    stage.clear_actors()

Actors are bodies made from a HumanoidDescription, named _Actor_<name>, root anchored, with their Animate script
removed (the harness poses them at set times) and their name and health bars off. An actor's position (the harness's
cf) is its HumanoidRootPart: for R6, the torso centre, 3 studs above the feet.

- **The rig** is R6 unless `"rig": "R15"`: the channel's characters are R6 (refs/r6rants/SYNTHESIS.md).
- **What they wear:** body colours as (r, g, b); catalog accessories as lists of asset ids (hair, hat, face_acc, neck,
  shoulder, front, back, waist); classic clothing as asset ids (shirt, pants, tshirt). Layered clothing is R15 only.
  Find items with AvatarEditorService:SearchCatalog (it works from edit mode) and log each one in ATTRIBUTION.md.
- **The face:** `face` sets the head's face decal (faces.py); the harness changes it per frame.
- **Nobody's avatar** by default. `user_id` loads a real person's avatar instead: only with that person's
  permission, and never for a video about someone who hasn't agreed to be in it.

Each actor is made in its own call (the bridge cuts commands somewhere past 4 KB), and reports what actually loaded:
an id that fails to load leaves its accessory out without an error, so read the report.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import studio  # noqa: E402

ACCESSORIES = {"hair": "HairAccessory", "hat": "HatAccessory", "face_acc": "FaceAccessory", "neck": "NeckAccessory",
               "shoulder": "ShouldersAccessory", "front": "FrontAccessory", "back": "BackAccessory",
               "waist": "WaistAccessory"}
CLOTHES = {"shirt": "Shirt", "pants": "Pants", "tshirt": "GraphicTShirt"}


def _rgb(c) -> str:
    return f"Color3.fromRGB({int(c[0])}, {int(c[1])}, {int(c[2])})"


def _ids(s: dict) -> list[int]:
    out = []
    for key in ACCESSORIES:
        ids = s.get(key) or []
        out += [int(i) for i in (ids if isinstance(ids, (list, tuple)) else [ids])]
    return out


def _description(s: dict, with_accessories: bool) -> str:
    if s.get("user_id"):
        return f"local d = Players:GetHumanoidDescriptionFromUserId({int(s['user_id'])})"
    skin = s.get("skin", (255, 204, 153))
    torso, arms, legs = s.get("torso", (60, 120, 200)), s.get("arms", skin), s.get("legs", (40, 40, 50))
    lines = ["local d = Instance.new('HumanoidDescription')",
             f"d.HeadColor, d.TorsoColor = {_rgb(skin)}, {_rgb(torso)}",
             f"d.LeftArmColor, d.RightArmColor = {_rgb(arms)}, {_rgb(arms)}",
             f"d.LeftLegColor, d.RightLegColor = {_rgb(legs)}, {_rgb(legs)}"]
    for key, prop in ACCESSORIES.items():
        ids = s.get(key)
        if ids and with_accessories:
            ids = ids if isinstance(ids, (list, tuple)) else [ids]
            lines.append(f"d.{prop} = '{','.join(str(int(i)) for i in ids)}'")
    for key, prop in CLOTHES.items():
        if s.get(key):
            lines.append(f"d.{prop} = {int(s[key])}")
    return "\n\t".join(lines)


def actor(name: str, s: dict) -> str:
    """Make (or remake) one actor, waiting at y = -200 until the harness poses it. Returns its report line.

    Measured on 2026-11-07 (spike S2): an R6 model made from a description has its Head as PrimaryPart, so pivoting
    it placed the head where the root should be (1.5 studs low, feet in the floor). Here the HumanoidRootPart is the
    pivot for every rig: an R6 actor's cf is its torso centre, 3 studs above its feet. And on R6 a description
    silently drops newer accessories (a 2022 hair loaded on R15 and not on R6), so on R6 each accessory is loaded
    and attached with Humanoid:AddAccessory instead. The report gives each accessory's offset from the head and marks
    MISFIT any that sits more than 1.2 studs below it: that 2022 hair attached 2.0 studs low, hidden in the torso,
    while a 2016 hair (Straight Blonde Hair, 376526888) sat 0.3 below, as a long hair should. Cast R6 actors from
    hair that fits; the report is the test."""
    rig = "R15" if s.get("rig") == "R15" else "R6"
    face = json.dumps(s.get("face") or "")
    manual = "{" + ",".join(str(i) for i in _ids(s)) + "}" if rig == "R6" else "{}"
    body = f"""local Players = game:GetService('Players')
local IS = game:GetService('InsertService')
local old = workspace:FindFirstChild("_Actor_{name}")
if old then old:Destroy() end
local info = ""
local ok, err = pcall(function()
	{_description(s, rig == "R15")}
	local okA, m = pcall(function() return Players:CreateHumanoidModelFromDescriptionAsync(d, Enum.HumanoidRigType.{rig}) end)
	if not (okA and m) then m = Players:CreateHumanoidModelFromDescription(d, Enum.HumanoidRigType.{rig}) end
	m.Name = "_Actor_{name}"
	local hum = m:FindFirstChildOfClass("Humanoid")
	hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	hum.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
	local root = m:FindFirstChild("HumanoidRootPart")
	root.Anchored = true
	m.PrimaryPart = root
	m.WorldPivot = root.CFrame
	local animate = m:FindFirstChild("Animate")
	if animate then animate:Destroy() end
	local head = m:FindFirstChild("Head")
	local dec = head and head:FindFirstChild("face")
	if dec and {face} ~= "" then dec.Texture = {face} end
	m:PivotTo(CFrame.new(0, -200, 0))
	m.Parent = workspace
	local failed = {{}}
	for _, id in {manual} do
		local okL, pack = pcall(function() return IS:LoadAsset(id) end)
		local a = okL and pack:FindFirstChildOfClass("Accessory")
		if a then hum:AddAccessory(a) else table.insert(failed, tostring(id)) end
		if okL then pack:Destroy() end
	end
	task.wait(0.2)
	local acc = {{}}
	for _, c in m:GetChildren() do
		local h = c:IsA("Accessory") and c:FindFirstChild("Handle")
		if h and head then
			local o = head.CFrame:PointToObjectSpace(h.Position)
			table.insert(acc, string.format("%s (%.1f, %.1f, %.1f from the head)%s", c.Name, o.X, o.Y, o.Z,
				o.Y < -1.2 and " MISFIT: below the head, made for another rig" or ""))
		end
	end
	local shirt, pants = m:FindFirstChildOfClass("Shirt"), m:FindFirstChildOfClass("Pants")
	info = string.format("%s; accessories: %s%s; shirt %s; pants %s; face %s", "{rig}",
		#acc > 0 and table.concat(acc, ", ") or "none", #failed > 0 and ("; FAILED to load " .. table.concat(failed, ", ")) or "",
		shirt and shirt.ShirtTemplate or "none", pants and pants.PantsTemplate or "none", dec and dec.Texture or "no face decal")
end)
out("{name}: " .. (if ok then "ready (" .. info .. ")" else "FAILED " .. tostring(err)))"""
    return studio.server(body, wait=25)


def actors(spec: dict[str, dict]) -> str:
    """Make (or remake) several actors, one call each: {name: spec} (the module's docstring). Returns the reports."""
    return "\n".join(actor(name, s) for name, s in spec.items())


def park(pos=(0, 3, -60)) -> str:
    """The local player's character anchored at `pos`: out of shot, and still near enough the shot for a place
    with streaming on to keep the shot's parts loaded on the client (choose `pos` near the shot)."""
    return studio.server(f"""
local p = game:GetService('Players'):GetPlayers()[1]
local ch = p and p.Character
if not ch then out('no character') return end
ch:PivotTo(CFrame.new({pos[0]}, {pos[1]}, {pos[2]}))
for _, d in ch:GetDescendants() do if d:IsA('BasePart') then d.Anchored = true end end
out('parked at ' .. tostring(ch:GetPivot().Position))""")


def clear_actors() -> str:
    return studio.server("""
local n = 0
for _, m in workspace:GetChildren() do
	if string.sub(m.Name, 1, 7) == "_Actor_" then m:Destroy() n += 1 end
end
out(n .. ' actors cleared')""")
