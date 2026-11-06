"""Stage a playtest's server for capture (docs/ROBLOX_CAPTURE.md, "Actors"): stand-in actors for the harness to
pose, and the local player's character parked out of the way.

    import stage
    stage.actors({"kid": {"skin": (255, 204, 153), "torso": (40, 120, 220), "legs": (30, 30, 40)}})
    stage.park((0, 3, -60))          # the player's own character, anchored out of shot
    stage.clear_actors()

Actors are R15 bodies made from a HumanoidDescription, named _Actor_<name>, anchored, with their Animate script
removed (the harness plays their animations at set times) and their name and health bars off. By default they are
plain bodies in the colours given: no one's avatar. `user_id` loads a real person's avatar instead: only with that
person's permission, and never for a video about someone who hasn't agreed to be in it.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import studio  # noqa: E402


def _rgb(c) -> str:
    return f"Color3.fromRGB({int(c[0])}, {int(c[1])}, {int(c[2])})"


def actors(spec: dict[str, dict]) -> str:
    """Make (or remake) actors: {name: {skin, torso, arms, legs} colours as (r, g, b), or user_id}. They wait at
    y = -200 until the harness poses them."""
    blocks = []
    for name, s in spec.items():
        if s.get("user_id"):
            desc = f"local d = Players:GetHumanoidDescriptionFromUserId({int(s['user_id'])})"
        else:
            skin = s.get("skin", (255, 204, 153))
            torso = s.get("torso", (60, 120, 200))
            arms = s.get("arms", skin)
            legs = s.get("legs", (40, 40, 50))
            desc = (f"local d = Instance.new('HumanoidDescription')\n"
                    f"d.HeadColor, d.TorsoColor = {_rgb(skin)}, {_rgb(torso)}\n"
                    f"d.LeftArmColor, d.RightArmColor = {_rgb(arms)}, {_rgb(arms)}\n"
                    f"d.LeftLegColor, d.RightLegColor = {_rgb(legs)}, {_rgb(legs)}")
        blocks.append(f"""
do
	local old = workspace:FindFirstChild("_Actor_{name}")
	if old then old:Destroy() end
	local ok, err = pcall(function()
		{desc}
		local m = Players:CreateHumanoidModelFromDescription(d, Enum.HumanoidRigType.R15)
		m.Name = "_Actor_{name}"
		local hum = m:FindFirstChildOfClass("Humanoid")
		hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
		hum.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
		m.HumanoidRootPart.Anchored = true
		local animate = m:FindFirstChild("Animate")
		if animate then animate:Destroy() end
		m:PivotTo(CFrame.new(0, -200, 0))
		m.Parent = workspace
	end)
	table.insert(report, "{name}: " .. (if ok then "ready" else tostring(err)))
end""")
    body = "local Players = game:GetService('Players')\nlocal report = {}\n" + "\n".join(blocks)
    return studio.server(body + "\nout(table.concat(report, '; '))", wait=5 + 3 * len(spec))


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
