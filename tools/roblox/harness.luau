-- Capture harness (play client). Run this file in the Client datamodel of a running playtest (capture.install()
-- does): it installs a LocalScript that shows the world a frame at a time for capture.py.
--
-- Every rendered frame (BindToRenderStep at the last priority, so after the game's own camera code), it holds:
--   the camera: Scriptable, at the frame's CFrame and field of view;
--   the HUD hidden: the game's ScreenGuis moved into a folder outside PlayerGui (a game's own code often re-enables
--     its screens every frame; moved out, they draw nothing), the core GUI, top bar and mouse cursor off;
--   the local character hidden (LocalTransparencyModifier), unless the frame says otherwise;
--   the lights, ambient and time of day the frame asks for (a game's lighting code would undo them otherwise).
-- On the frame that asks (capture.py's first), every particle emitter and beam is frozen: a frame takes about a
-- second to capture, so live particles would jump from frame to frame.
--
-- A frame is one JSON object written to the harness's Frame attribute. Once applied, Applied is set to its id, or to
-- -1 with Err set to the error.
--   id       set by capture.py
--   cam      12 CFrame components, or {pos = {x, y, z}, look = {x, y, z}, roll = degrees}
--   fov      vertical field of view in degrees (default 70)
--   dof      {focus, radius, near, far} for a depth-of-field effect; absent for none
--   hud      true to show the game's screens (default hidden)
--   keepGuis names of the game's own ScreenGuis or BillboardGuis to leave showing (a scoreboard you want in shot)
--   me       true to show the local character (default hidden)
--   freeze   true to freeze every particle emitter and beam now
--   clock    Lighting.ClockTime, held
--   ambient  {r, g, b} in 0..1: Lighting.Ambient, held
--   lights   {{path, on, brightness}}: lights held on or off, e.g. "Workspace.Lamps.Lamp1.PointLight"
--   actors   {{name, cf, anims = {{key, t, w, priority}}, face, hidden, optional}}: the model _Actor_<name> (stage.py
--            makes them) or <name> in Workspace, pivoted to cf; each animation held at t seconds with weight w. key
--            is a name below (walk, run, idle, ...), a number, or "rbxassetid://N". face: a texture for the head's
--            face decal (faces.py), set when it changes
--   moves    {{path, cf}}: any model or part pivoted to cf
--   attrs    {{path, name, value}}: attributes set, for the game's own code to read
--   t        the shot's time in seconds, left in the attribute T for your own code
-- Setting the attribute Release to true puts everything back: camera, HUD, lights, particles; then the harness ends.
local pg = game:GetService("Players").LocalPlayer:WaitForChild("PlayerGui")
local old = pg:FindFirstChild("_CaptureHarness")
if old then
	old:SetAttribute("Release", true)
	task.wait(0.1)
	old:Destroy()
end
local ls = Instance.new("LocalScript")
ls.Name = "_CaptureHarness"
ls.Source = [==[
local HttpService = game:GetService("HttpService")
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local StarterGui = game:GetService("StarterGui")
local UserInputService = game:GetService("UserInputService")
local lp = Players.LocalPlayer
local cam = workspace.CurrentCamera

pcall(function()
	RunService:UnbindFromRenderStep("_CaptureHarness")
end)
for _, c in cam:GetChildren() do
	if c.Name == "_CaptureDof" then
		c:Destroy()
	end
end
local dof = Instance.new("DepthOfFieldEffect")
dof.Name = "_CaptureDof"
dof.Enabled = false
dof.Parent = cam
local held = ReplicatedStorage:FindFirstChild("_CaptureHeld") or Instance.new("Folder")
held.Name = "_CaptureHeld"
held.Parent = ReplicatedStorage

local camCF = cam.CFrame
local fov = 70
local showHud, showMe = false, false
local keep = {} -- names of the game's GUIs to leave showing
local clock, ambient = nil, nil
local wasLighting = { ClockTime = Lighting.ClockTime, Ambient = Lighting.Ambient }
local heldLights = {} -- light -> {on, b}
local wasLights = {} -- light -> {Enabled, Brightness}
local frozen = {} -- emitter or beam -> its TimeScale or TextureSpeed
local tracks = {} -- model -> {id -> AnimationTrack}

local ANIMS = { -- Roblox's own R15 animations (they load in any experience)
	walk = "rbxassetid://913402848",
	run = "rbxassetid://913376220",
	idle = "rbxassetid://507766388",
	toolnone = "rbxassetid://507768375",
	wave = "rbxassetid://507770239",
	laugh = "rbxassetid://507770818",
	point = "rbxassetid://507770453",
	cheer = "rbxassetid://507770677",
}
local MOVEMENT = { walk = true, run = true, idle = true }

local function find(path)
	local node = game
	for part in string.gmatch(path, "[^%.]+") do
		node = node and node:FindFirstChild(part)
	end
	return node
end

local function cframe(c)
	if c.pos then
		local cf =
			CFrame.lookAt(Vector3.new(c.pos[1], c.pos[2], c.pos[3]), Vector3.new(c.look[1], c.look[2], c.look[3]))
		if c.roll then
			cf *= CFrame.Angles(0, 0, math.rad(c.roll))
		end
		return cf
	end
	return CFrame.new(c[1], c[2], c[3], c[4], c[5], c[6], c[7], c[8], c[9], c[10], c[11], c[12])
end

local function setHidden(model, hidden)
	local m = if hidden then 1 else 0
	for _, d in model:GetDescendants() do
		if d:IsA("BasePart") or d:IsA("Decal") then
			d.LocalTransparencyModifier = m
		end
	end
end

local function freeze()
	for _, d in workspace:GetDescendants() do
		if frozen[d] == nil then
			if d:IsA("ParticleEmitter") then
				frozen[d] = d.TimeScale
				d.TimeScale = 0
			elseif d:IsA("Beam") then
				frozen[d] = d.TextureSpeed
				d.TextureSpeed = 0
			end
		end
	end
end

local function poseActor(a)
	local m = workspace:FindFirstChild("_Actor_" .. a.name) or workspace:FindFirstChild(a.name)
	if not m then
		if a.optional then
			return
		end
		error("no actor " .. a.name)
	end
	if a.cf then
		m:PivotTo(cframe(a.cf))
	end
	setHidden(m, a.hidden == true)
	if a.face then
		local head = m:FindFirstChild("Head")
		local decal = head and head:FindFirstChild("face")
		if not decal then
			error("no face decal on " .. a.name)
		end
		if decal.Texture ~= a.face then
			decal.Texture = a.face
		end
	end
	local ctl = m:FindFirstChildOfClass("Humanoid") or m:FindFirstChildOfClass("AnimationController")
	if not ctl then
		return
	end
	local animator = ctl:FindFirstChildOfClass("Animator")
	if not animator then
		animator = Instance.new("Animator")
		animator.Parent = ctl
	end
	tracks[m] = tracks[m] or {}
	local mine, used = tracks[m], {}
	for _, an in a.anims or {} do
		local key, t, w, pri = an[1], an[2] or 0, an[3] or 1, an[4]
		local id = ANIMS[key] or (if type(key) == "number" then "rbxassetid://" .. tostring(key) else key)
		local tr = mine[id]
		if not tr then
			local anim = Instance.new("Animation")
			anim.AnimationId = id
			tr = animator:LoadAnimation(anim)
			tr.Priority = if pri
				then Enum.AnimationPriority[pri]
				elseif MOVEMENT[key] then Enum.AnimationPriority.Movement
				else Enum.AnimationPriority.Action
			mine[id] = tr
		end
		if not tr.IsPlaying then
			tr:Play(0, w, 0)
		end
		tr:AdjustSpeed(0)
		tr:AdjustWeight(w, 0)
		-- Length is 0 until the animation has loaded: capture.py's warmup applies the first frame again after it.
		tr.TimePosition = t % math.max(tr.Length, 1e-3)
		used[id] = true
	end
	for id, tr in mine do
		if not used[id] and tr.IsPlaying then
			tr:Stop(0)
		end
	end
end

local function holdLights(list)
	local want = {}
	for _, item in list or {} do
		local light = find(item[1])
		if not (light and light:IsA("Light")) then
			error("no light " .. tostring(item[1]))
		end
		want[light] = { on = item[2] ~= false, b = item[3] }
		if wasLights[light] == nil then
			wasLights[light] = { Enabled = light.Enabled, Brightness = light.Brightness }
		end
	end
	for light in heldLights do
		if not want[light] then
			light.Enabled, light.Brightness = wasLights[light].Enabled, wasLights[light].Brightness
		end
	end
	heldLights = want
end

local function apply(f)
	if f.cam then
		camCF = cframe(f.cam)
	end
	fov = f.fov or fov
	showHud, showMe = f.hud == true, f.me == true
	keep = {}
	for _, name in f.keepGuis or {} do
		keep[name] = true
	end
	for _, g in held:GetChildren() do
		if keep[g.Name] then
			g.Parent = lp.PlayerGui
		end
	end
	clock = f.clock
	ambient = if f.ambient then Color3.new(f.ambient[1], f.ambient[2], f.ambient[3]) else nil
	if f.dof then
		dof.FocusDistance, dof.InFocusRadius, dof.NearIntensity, dof.FarIntensity =
			f.dof[1], f.dof[2], f.dof[3], f.dof[4]
		dof.Enabled = true
	else
		dof.Enabled = false
	end
	holdLights(f.lights)
	for _, a in f.actors or {} do
		poseActor(a)
	end
	for _, mv in f.moves or {} do
		local node = find(mv[1])
		if not (node and node:IsA("PVInstance")) then
			error("nothing to move at " .. tostring(mv[1]))
		end
		node:PivotTo(cframe(mv[2]))
	end
	for _, at in f.attrs or {} do
		local node = find(at[1])
		if not node then
			error("no instance " .. tostring(at[1]))
		end
		node:SetAttribute(at[2], at[3])
	end
	script:SetAttribute("T", f.t)
	if f.freeze then
		freeze()
	end
end

local function hud(off)
	pcall(function()
		StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.All, not off)
	end)
	pcall(function()
		StarterGui:SetCore("TopbarEnabled", not off)
	end)
	pcall(function()
		game:GetService("ProximityPromptService").Enabled = not off
	end)
	pcall(function()
		game:GetService("TextChatService").ChatWindowConfiguration.Enabled = not off
		game:GetService("TextChatService").ChatInputBarConfiguration.Enabled = not off
	end)
	UserInputService.MouseIconEnabled = not off
end
hud(true)

RunService:BindToRenderStep("_CaptureHarness", Enum.RenderPriority.Last.Value, function()
	cam.CameraType = Enum.CameraType.Scriptable
	cam.CFrame = camCF
	cam.FieldOfView = fov
	if showHud then
		for _, g in held:GetChildren() do
			g.Parent = lp.PlayerGui
		end
	else
		-- Screens and billboards (name tags, prompts); SurfaceGuis stay, being part of the world more often than not.
		for _, g in lp.PlayerGui:GetChildren() do
			if (g:IsA("ScreenGui") or g:IsA("BillboardGui")) and not keep[g.Name] then
				g.Parent = held
			end
		end
	end
	if lp.Character then
		setHidden(lp.Character, not showMe)
	end
	for light, rec in heldLights do
		light.Enabled = rec.on
		if rec.b then
			light.Brightness = rec.b
		end
	end
	if clock then
		Lighting.ClockTime = clock
	end
	if ambient then
		Lighting.Ambient = ambient
	end
end)

local function release()
	pcall(function()
		RunService:UnbindFromRenderStep("_CaptureHarness")
	end)
	for _, g in held:GetChildren() do
		g.Parent = lp.PlayerGui
	end
	hud(false)
	if lp.Character then
		setHidden(lp.Character, false)
	end
	for light, was in wasLights do
		light.Enabled, light.Brightness = was.Enabled, was.Brightness
	end
	for d, v in frozen do
		if d.Parent then
			if d:IsA("ParticleEmitter") then
				d.TimeScale = v
			else
				d.TextureSpeed = v
			end
		end
	end
	Lighting.ClockTime, Lighting.Ambient = wasLighting.ClockTime, wasLighting.Ambient
	for _, mine in tracks do
		for _, tr in mine do
			tr:Stop(0)
		end
	end
	dof:Destroy()
	cam.CameraType = Enum.CameraType.Custom
	script:SetAttribute("Released", true)
end

script:GetAttributeChangedSignal("Frame"):Connect(function()
	local raw = script:GetAttribute("Frame")
	local ok, err = pcall(function()
		local f = HttpService:JSONDecode(raw)
		apply(f)
		script:SetAttribute("Applied", f.id)
	end)
	script:SetAttribute("Err", if ok then "" else tostring(err))
	if not ok then
		script:SetAttribute("Applied", -1)
	end
end)
script:GetAttributeChangedSignal("Release"):Connect(function()
	if script:GetAttribute("Release") == true then
		release()
	end
end)
script:SetAttribute("Ready", true)
]==]
ls.Parent = pg
local t0 = os.clock()
while not ls:GetAttribute("Ready") and os.clock() - t0 < 5 do
	task.wait(0.05)
end
return "harness " .. tostring(ls:GetAttribute("Ready"))
