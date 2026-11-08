"""The set kit: rooms, furniture and streets as code, built in the playtest by `sets.py` (docs/SETS.md).

A set is made of blocks, cylinders, balls and wedges (Roblox parts), signs (a part with text on it) and lights, all
written into one Luau table and built in one go under workspace._Set. Positions are in studs, y up; floors are at
y = 0, so an actor standing on one has its torso centre at y = 3. Every set names its marks: where actors stand
({"pos": [x, 3, z], "look": [x, y, z]}), and where it's good to shoot from.

    import kit
    s = kit.SETS["classroom"]({})
    s.marks["teacher"]          # {"pos": [...], "look": [...]}
    s.luau()                     # the Luau that builds it

Colours are Roblox-bright and saturated, like the references' sets (school blues, red lockers, warm wood); a set
says which lighting preset it wants (`sets.LIGHTING`).
"""

from __future__ import annotations

import json
import math
import random

MATERIALS = ["SmoothPlastic", "Plastic", "Wood", "WoodPlanks", "Marble", "Brick", "Concrete", "Fabric", "Glass",
             "Metal", "Neon", "Granite", "Slate", "Asphalt", "Grass", "Pebble", "Sand", "Cobblestone", "DiamondPlate",
             "Plaster", "CeramicTiles", "Carpet", "Leather", "Cardboard", "RoofShingles", "Rubber", "Foil", "Ice"]
SHAPES = {"block": 0, "cyl": 1, "ball": 2, "wedge": 3, "corner": 4}


class Set:
    def __init__(self, name: str, lighting: str = "interior", hide_baseplate: bool = True):
        self.name = name
        self.lighting = lighting
        self.hide_baseplate = hide_baseplate
        self.parts: list[list] = []
        self.signs: list[dict] = []
        self.lights: list[list] = []
        self.marks: dict[str, dict] = {}
        self.cams: dict[str, dict] = {}
        self.park = (0, 3, -120)
        self.bounds = None   # a room's inside, (x0, x1, y0, y1, z0, z1): set by room()

    # ---- primitives
    def part(self, shape: str, size, pos, color, material="SmoothPlastic", rot=(0, 0, 0), transparency=0.0,
             reflect=0.0, collide=True):
        self.parts.append([SHAPES[shape], *[round(v, 3) for v in size], *[round(v, 3) for v in pos],
                           *[round(v, 2) for v in rot], *[int(c) for c in color], MATERIALS.index(material),
                           round(transparency, 2), round(reflect, 2)])

    def box(self, size, pos, color, material="SmoothPlastic", rot=(0, 0, 0), transparency=0.0, reflect=0.0):
        self.part("block", size, pos, color, material, rot, transparency, reflect)

    def cyl(self, length, radius, pos, color, material="SmoothPlastic", axis="y", transparency=0.0):
        """A cylinder `length` long along `axis`."""
        rot = {"x": (0, 0, 0), "y": (0, 0, 90), "z": (0, 90, 0)}[axis]
        self.part("cyl", (length, radius * 2, radius * 2), pos, color, material, rot, transparency)

    def ball(self, d, pos, color, material="SmoothPlastic"):
        self.part("ball", (d, d, d), pos, color, material)

    def wedge(self, size, pos, color, material="SmoothPlastic", rot=(0, 0, 0)):
        self.part("wedge", size, pos, color, material, rot)

    def sign(self, size, pos, text, face="Front", bg=(255, 255, 255), fg=(30, 30, 40), rot=(0, 0, 0),
             font="GothamBold", scale=0.8, material="SmoothPlastic"):
        """A flat part with text on one face."""
        self.signs.append({"size": list(size), "pos": list(pos), "text": text, "face": face, "bg": list(bg),
                           "fg": list(fg), "rot": list(rot), "font": font, "scale": scale, "mat": material})

    def light(self, pos, color=(255, 244, 228), brightness=1.2, rng=24.0, shadows=False):
        self.lights.append([*[round(v, 2) for v in pos], *color, brightness, rng, 1 if shadows else 0])

    def mark(self, name, pos, look):
        self.marks[name] = {"pos": [round(v, 2) for v in pos], "look": [round(v, 2) for v in look]}

    def cam(self, name, pos, look, fov=55):
        """A good place to shoot the set from (a portrait frame), for previews and establishing shots."""
        self.cams[name] = {"pos": [round(v, 2) for v in pos], "look": [round(v, 2) for v in look], "fov": fov}

    # ---- the Luau that builds it
    def luau(self, offset=(0.0, 0.0, 0.0), append: bool = False) -> str:
        """The Luau that builds the set `offset` studs from where it was designed; with `append`, beside a set
        already built (no new lighting, the first set's folder kept)."""
        from sets import lighting_luau
        ox, oy, oz = offset
        parts = [r[:4] + [round(r[4] + ox, 3), round(r[5] + oy, 3), round(r[6] + oz, 3)] + r[7:] for r in self.parts]
        signs = [dict(g, pos=[g["pos"][0] + ox, g["pos"][1] + oy, g["pos"][2] + oz]) for g in self.signs]
        lights = [[round(r[0] + ox, 2), round(r[1] + oy, 2), round(r[2] + oz, 2)] + r[3:] for r in self.lights]
        data = json.dumps({"p": parts, "s": signs, "l": lights}, separators=(",", ":"))
        mats = "{" + ",".join(f"'{m}'" for m in MATERIALS) + "}"
        return f"""
local HS = game:GetService('HttpService')
local folder
if {str(append).lower()} and workspace:FindFirstChild('_Set') then
  folder = workspace:FindFirstChild('_Set')
else
  local old = workspace:FindFirstChild('_Set') if old then old:Destroy() end
  folder = Instance.new('Folder') folder.Name = '_Set' folder:SetAttribute('SetName', '{self.name}')
end
local D = HS:JSONDecode({json.dumps(data)})
local MATS = {mats}
local shapes = {{[0]='Block', [1]='Cylinder', [2]='Ball'}}
local n = 0
for _, r in ipairs(D.p) do
  local p
  if r[1] == 3 then p = Instance.new('WedgePart')
  elseif r[1] == 4 then p = Instance.new('CornerWedgePart')
  else p = Instance.new('Part') p.Shape = Enum.PartType[shapes[r[1]]] end
  p.Anchored = true
  p.Size = Vector3.new(r[2], r[3], r[4])
  p.CFrame = CFrame.new(r[5], r[6], r[7]) * CFrame.Angles(math.rad(r[8]), math.rad(r[9]), math.rad(r[10]))
  p.Color = Color3.fromRGB(r[11], r[12], r[13])
  local ok = pcall(function() p.Material = Enum.Material[MATS[r[14] + 1]] end)
  if not ok then p.Material = Enum.Material.SmoothPlastic end
  p.Transparency = r[15]
  p.Reflectance = r[16]
  p.TopSurface = Enum.SurfaceType.Smooth p.BottomSurface = Enum.SurfaceType.Smooth
  p.CastShadow = r[15] < 0.5
  p.Parent = folder
  n += 1
end
for _, s in ipairs(D.s) do
  local p = Instance.new('Part')
  p.Anchored = true
  p.Size = Vector3.new(s.size[1], s.size[2], s.size[3])
  p.CFrame = CFrame.new(s.pos[1], s.pos[2], s.pos[3]) * CFrame.Angles(math.rad(s.rot[1]), math.rad(s.rot[2]), math.rad(s.rot[3]))
  p.Color = Color3.fromRGB(s.bg[1], s.bg[2], s.bg[3])
  pcall(function() p.Material = Enum.Material[s.mat] end)
  local g = Instance.new('SurfaceGui')
  g.Face = Enum.NormalId[s.face]
  g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
  g.PixelsPerStud = 50
  g.LightInfluence = 1
  local t = Instance.new('TextLabel')
  t.Size = UDim2.fromScale(1, 1)
  t.BackgroundTransparency = 1
  t.Text = s.text
  t.TextScaled = true
  t.TextWrapped = true
  t.TextColor3 = Color3.fromRGB(s.fg[1], s.fg[2], s.fg[3])
  pcall(function() t.Font = Enum.Font[s.font] end)
  local pad = Instance.new('UIPadding')
  local m = UDim.new((1 - s.scale) / 2, 0)
  pad.PaddingLeft, pad.PaddingRight, pad.PaddingTop, pad.PaddingBottom = m, m, m, m
  pad.Parent = t
  t.Parent = g
  g.Parent = p
  p.Parent = folder
  n += 1
end
for _, l in ipairs(D.l) do
  local a = Instance.new('Part')
  a.Anchored = true a.CanCollide = false a.Transparency = 1 a.Size = Vector3.new(0.2, 0.2, 0.2)
  a.CFrame = CFrame.new(l[1], l[2], l[3])
  local pl = Instance.new('PointLight')
  pl.Color = Color3.fromRGB(l[4], l[5], l[6]) pl.Brightness = l[7] pl.Range = l[8] pl.Shadows = l[9] == 1
  pl.Parent = a
  a.Parent = folder
end
folder.Parent = workspace
{"local base = workspace:FindFirstChild('Baseplate') if base and base:GetAttribute('_SetHidden') == nil then base:SetAttribute('_SetHidden', base.Transparency) base.Transparency = 1 base.CanCollide = false end" if self.hide_baseplate else ""}
{"" if append else lighting_luau(self.lighting)}
out('{self.name}: ' .. n .. ' parts, ' .. #D.l .. ' lights')
"""


# ---------------------------------------------------------------------------------------------------- furniture

WOOD = (170, 118, 72)
DARK_WOOD = (110, 72, 44)
WHITE = (242, 242, 245)
METAL = (150, 155, 165)
BLACK = (30, 30, 34)


def room(s: Set, w, d, h, x0=0.0, z0=0.0, wall=(214, 222, 236), trim=(70, 120, 210), floor=(205, 205, 212),
         floor_mat="Marble", ceiling=(200, 202, 210), walls="nsew", gaps=None):
    """A room centred on (x0, z0): floor top at y 0, walls `h` high on the sides named in `walls` (n = +z, s = -z,
    e = +x, w = -x), a coloured trim along the bottom (as the references' school), a ceiling. `gaps`: {side: [(from,
    to, bottom, top), ...]} openings along a wall (doors, windows), in studs from the wall's left end as seen from
    inside."""
    gaps = gaps or {}
    s.bounds = (x0 - w / 2, x0 + w / 2, 0.0, h, z0 - d / 2, z0 + d / 2)
    s.box((w + 2, 1, d + 2), (x0, -0.5, z0), floor, floor_mat)
    if ceiling:
        s.box((w + 2, 1, d + 2), (x0, h + 0.5, z0), ceiling, "SmoothPlastic")
    t = 1.0
    sides = {"n": ((x0, z0 + d / 2 + t / 2), w, (1, 0)), "s": ((x0, z0 - d / 2 - t / 2), w, (-1, 0)),
             "e": ((x0 + w / 2 + t / 2, z0), d, (0, -1)), "w": ((x0 - w / 2 - t / 2, z0), d, (0, 1))}
    for side in walls:
        (cx, cz), length, (ux, uz) = sides[side]
        # inside, looking at the wall, its left end is at -length/2 along (ux, uz) rotated... keep it simple:
        # segments run along the wall from one end; gaps cut the full height into pieces
        holes = sorted(gaps.get(side, []))
        cuts = [(0.0, 0.0, 0.0, 0.0)] + holes + [(length, length, 0.0, 0.0)]
        along = (1, 0) if side in "ns" else (0, 1)
        start = -length / 2
        for (a0, a1, b0, b1), (c0, c1, _, _) in zip(cuts, cuts[1:]):
            seg0, seg1 = start + a1, start + c0
            if seg1 - seg0 > 0.01:
                _wall(s, side, cx, cz, along, seg0, seg1, 0, h, t, wall)
        for (g0, g1, gb, gt) in holes:
            if gb > 0:
                _wall(s, side, cx, cz, along, start + g0, start + g1, 0, gb, t, wall)
            if gt < h:
                _wall(s, side, cx, cz, along, start + g0, start + g1, gt, h, t, wall)
        # trim along the bottom and a thin band at the top
        _wall(s, side, cx, cz, along, -length / 2, length / 2, 0, 1.2, t + 0.15, trim, skip=holes, doors=True)
        _wall(s, side, cx, cz, along, -length / 2, length / 2, h - 0.6, h, t + 0.1, trim, skip=holes)


def _wall(s, side, cx, cz, along, a, b, y0, y1, t, color, skip=None, doors=False):
    """A wall piece from a to b along the wall, y0 to y1 high; with `skip`, the pieces between the holes."""
    spans = [(a, b)]
    if skip:
        spans = []
        cur = a
        for g0, g1, gb, gt in sorted(skip):
            g0, g1 = -((b - a) / 2) + g0, -((b - a) / 2) + g1
            if doors and gb > 0.5:  # a window: the trim runs under it
                continue
            if y0 >= gt or y1 <= gb:
                continue
            spans.append((cur, g0))
            cur = g1
        spans.append((cur, b))
    for p, q in spans:
        if q - p < 0.01:
            continue
        mid = (p + q) / 2
        x = cx + along[0] * mid
        z = cz + along[1] * mid
        size = (q - p, y1 - y0, t) if side in "ns" else (t, y1 - y0, q - p)
        s.box(size, (x, (y0 + y1) / 2, z), color, "SmoothPlastic")


def window(s: Set, pos, w, h, axis="z", frame=WHITE, glass=(170, 210, 240)):
    """A window in a wall opening: a frame and a pane of glass, the panes crossed by bars. `axis` is the wall's
    normal."""
    x, y, z = pos
    if axis == "z":
        s.box((w, h, 0.3), (x, y, z), glass, "Glass", transparency=0.45, reflect=0.1)
        for dx in (-w / 2, 0, w / 2):
            s.box((0.35, h + 0.35, 0.6), (x + dx, y, z), frame)
        for dy in (-h / 2, 0, h / 2):
            s.box((w + 0.35, 0.35, 0.6), (x, y + dy, z), frame)
    else:
        s.box((0.3, h, w), (x, y, z), glass, "Glass", transparency=0.45, reflect=0.1)
        for dz in (-w / 2, 0, w / 2):
            s.box((0.6, h + 0.35, 0.35), (x, y, z + dz), frame)
        for dy in (-h / 2, 0, h / 2):
            s.box((0.6, 0.35, w + 0.35), (x, y + dy, z), frame)


def door(s: Set, pos, axis="z", color=(150, 95, 60), frame=WHITE, w=4.0, h=7.5, open_=False):
    x, y0, z = pos
    if axis == "z":
        s.box((w, h, 0.4), (x, y0 + h / 2, z), color, "Wood")
        s.box((w + 0.6, 0.4, 0.7), (x, y0 + h + 0.2, z), frame)
        for dx in (-w / 2 - 0.15, w / 2 + 0.15):
            s.box((0.4, h, 0.7), (x + dx, y0 + h / 2, z), frame)
        s.ball(0.35, (x + w / 2 - 0.5, y0 + 3.4, z - 0.3), (220, 190, 80), "Metal")
    else:
        s.box((0.4, h, w), (x, y0 + h / 2, z), color, "Wood")
        s.box((0.7, 0.4, w + 0.6), (x, y0 + h + 0.2, z), frame)
        for dz in (-w / 2 - 0.15, w / 2 + 0.15):
            s.box((0.7, h, 0.4), (x, y0 + h / 2, z + dz), frame)
        s.ball(0.35, (x - 0.3, y0 + 3.4, z + w / 2 - 0.5), (220, 190, 80), "Metal")


def school_desk(s: Set, pos, face=(0, 0, -1), top=(196, 150, 100), legs=(80, 80, 90), chair=(60, 110, 200)):
    """A student desk with its chair behind it (the chair on the side away from `face`, the way the student faces)."""
    x, _, z = pos
    fz = 1 if face[2] >= 0 else -1
    s.box((3.4, 0.25, 2.2), (x, 2.55, z), top, "Wood")
    for dx in (-1.5, 1.5):
        for dz in (-0.9, 0.9):
            s.cyl(2.45, 0.09, (x + dx, 1.22, z + dz), legs, "Metal")
    s.box((3.0, 0.9, 1.6), (x, 2.0, z + 0.1 * fz), (170, 125, 85), "Wood")  # the book box under the top
    cz = z - 2.1 * fz
    s.box((2.2, 0.22, 2.0), (x, 1.6, cz), chair)
    s.box((2.2, 2.0, 0.22), (x, 2.7, cz - 0.95 * fz), chair)
    for dx in (-0.95, 0.95):
        for dz in (-0.8, 0.8):
            s.cyl(1.55, 0.08, (x + dx, 0.78, cz + dz), legs, "Metal")


def teacher_desk(s: Set, pos):
    x, _, z = pos
    s.box((7.0, 0.35, 3.4), (x, 3.1, z), DARK_WOOD, "Wood")
    s.box((7.0, 2.9, 0.3), (x, 1.5, z + 1.55), (120, 80, 50), "Wood")
    for dx in (-3.3, 3.3):
        s.box((0.35, 2.9, 3.2), (x + dx, 1.5, z), (120, 80, 50), "Wood")
    s.box((1.6, 0.25, 1.2), (x - 1.8, 3.4, z), (230, 70, 70))  # a book
    s.box((1.4, 0.25, 1.0), (x - 1.8, 3.65, z), (60, 150, 230))
    s.ball(0.8, (x + 2.2, 3.7, z - 0.4), (230, 40, 40))  # an apple
    s.cyl(0.4, 0.08, (x + 2.2, 4.15, z - 0.4), (90, 60, 30))


def whiteboard(s: Set, pos, w=16, h=6, text="", axis="z", toward=1):
    """A whiteboard on a wall, its writing facing `toward` (+1 or -1) along `axis`."""
    x, y, z = pos
    face = {("z", 1): "Back", ("z", -1): "Front", ("x", 1): "Right", ("x", -1): "Left"}[(axis, toward)]
    if axis == "z":
        s.box((w + 0.6, h + 0.6, 0.3), (x, y, z), (180, 180, 190), "Metal")
        s.sign((w, h, 0.3), (x, y, z + toward * 0.1), text, face=face, bg=(248, 248, 250), fg=(40, 70, 160),
               scale=0.7, font="PermanentMarker")
        s.box((w, 0.3, 0.8), (x, y - h / 2 - 0.3, z + toward * 0.3), (180, 180, 190), "Metal")
    else:
        s.box((0.3, h + 0.6, w + 0.6), (x, y, z), (180, 180, 190), "Metal")
        s.sign((0.3, h, w), (x + toward * 0.1, y, z), text, face=face, bg=(248, 248, 250), fg=(40, 70, 160),
               scale=0.7, font="PermanentMarker")


def lockers(s: Set, x0, z, n, axis="z", side=1, color=(205, 60, 60), h=7.0, w=1.8, depth=1.6):
    """A bank of `n` lockers starting at x0 along x (axis 'z': the bank faces +z*side)."""
    for i in range(n):
        x = x0 + i * (w + 0.05)
        s.box((w, h, depth), (x, h / 2, z), color, "Metal")
        for k in range(3):  # vents
            s.box((w * 0.6, 0.12, 0.05), (x, h - 1.0 - 0.3 * k, z + side * (depth / 2 + 0.02)), (150, 40, 40))
        s.box((0.15, 0.7, 0.12), (x + w * 0.3, h * 0.48, z + side * (depth / 2 + 0.05)), METAL, "Metal")
    s.box(((w + 0.05) * n, 0.3, depth + 0.1), (x0 + (n - 1) * (w + 0.05) / 2, h + 0.15, z), (150, 40, 40), "Metal")


def ceiling_light(s: Set, pos, length=10.0, axis="x", glow=(236, 236, 230), brightness=0.6, rng=20.0):
    x, y, z = pos
    size = (length, 0.3, 1.4) if axis == "x" else (1.4, 0.3, length)
    s.box((size[0] + 0.4, 0.4, size[2] + 0.4), (x, y + 0.1, z), (120, 125, 135), "Metal")
    s.box(size, (x, y - 0.1, z), glow, "Neon")
    s.light((x, y - 1.2, z), glow, brightness, rng)


def poster(s: Set, pos, size, color, text="", axis="z", face="Back", fg=(255, 255, 255)):
    x, y, z = pos
    sz = (size[0], size[1], 0.1) if axis == "z" else (0.1, size[1], size[0])
    if text:
        s.sign(sz, pos, text, face=face, bg=color, fg=fg, scale=0.75)
    else:
        s.box(sz, pos, color)


def clock(s: Set, pos, axis="z"):
    x, y, z = pos
    s.cyl(0.3, 1.1, pos, WHITE, axis=axis)
    s.cyl(0.32, 0.9, pos, (250, 250, 250), axis=axis)
    s.box((0.1, 0.7, 0.1) if axis == "z" else (0.1, 0.7, 0.1), (x, y + 0.3, z - 0.2 if axis == "z" else z), BLACK)


def plant(s: Set, pos, pot=(200, 110, 70)):
    x, y, z = pos
    s.cyl(1.4, 0.8, (x, y + 0.7, z), pot)
    for dx, dy, dz, d in ((0, 2.3, 0, 1.8), (0.6, 1.9, 0.3, 1.3), (-0.5, 2.0, -0.3, 1.4), (0.1, 2.9, 0.2, 1.1)):
        s.ball(d, (x + dx, y + dy, z + dz), (60, 160, 70), "Grass")


def bookshelf(s: Set, pos, axis="z", w=6.0, h=7.0, seed=1):
    x, _, z = pos
    rng = random.Random(seed)
    s.box((w, h, 1.5) if axis == "z" else (1.5, h, w), (x, h / 2, z), DARK_WOOD, "Wood")
    for k in range(4):
        y = 0.6 + k * 1.7
        cx = -w / 2 + 0.4
        while cx < w / 2 - 0.6:
            bw = rng.uniform(0.25, 0.5)
            bh = rng.uniform(1.0, 1.4)
            col = rng.choice([(220, 60, 60), (60, 120, 220), (240, 200, 60), (80, 180, 90), (160, 90, 200),
                              (240, 140, 50)])
            if axis == "z":
                s.box((bw, bh, 1.0), (x + cx + bw / 2, y + bh / 2, z - 0.15), col)
            else:
                s.box((1.0, bh, bw), (x - 0.15, y + bh / 2, z + cx + bw / 2), col)
            cx += bw + 0.05


def bed(s: Set, pos, face=(0, 0, 1), blanket=(90, 140, 230), length=8.0, width=5.0):
    """A bed with its head against the wall behind `pos`, pointing along `face` (+z or -z)."""
    x, _, z = pos
    f = 1 if face[2] >= 0 else -1
    s.box((width, 1.4, length), (x, 0.9, z + f * length / 2), DARK_WOOD, "Wood")
    s.box((width - 0.2, 0.9, length - 0.3), (x, 2.0, z + f * length / 2), WHITE, "Fabric")
    s.box((width, 0.4, length * 0.62), (x, 2.55, z + f * length * 0.66), blanket, "Fabric")
    s.box((width * 0.8, 0.6, 1.4), (x, 2.75, z + f * 1.1), (250, 250, 250), "Fabric")
    s.box((width + 0.4, 4.0, 0.5), (x, 2.0, z - f * 0.1), DARK_WOOD, "Wood")


def sofa(s: Set, pos, face=(0, 0, 1), color=(110, 120, 200), w=8.0):
    x, _, z = pos
    f = 1 if face[2] >= 0 else -1
    s.box((w, 1.6, 3.2), (x, 1.2, z), color, "Fabric")
    s.box((w, 2.6, 0.9), (x, 2.4, z - f * 1.3), color, "Fabric")
    for dx in (-w / 2 + 0.45, w / 2 - 0.45):
        s.box((0.9, 2.2, 3.2), (x + dx, 1.5, z), color, "Fabric")
    for dx in (-w / 4, w / 4):
        s.box((w / 2 - 1.1, 0.5, 2.4), (x + dx, 2.25, z + f * 0.2), tuple(min(255, c + 25) for c in color), "Fabric")


def tv(s: Set, pos, face=(0, 0, -1), w=7.0):
    x, _, z = pos
    f = 1 if face[2] >= 0 else -1
    s.box((w + 1.5, 2.2, 2.2), (x, 1.1, z), DARK_WOOD, "Wood")
    s.box((w, w * 0.56, 0.3), (x, 2.2 + w * 0.28 + 0.4, z), BLACK)
    s.box((w - 0.4, w * 0.56 - 0.4, 0.1), (x, 2.2 + w * 0.28 + 0.4, z + f * 0.17), (40, 60, 110), "Glass")


def table(s: Set, pos, w=5.0, d=3.0, h=2.6, color=WOOD):
    x, _, z = pos
    s.box((w, 0.3, d), (x, h, z), color, "Wood")
    for dx in (-w / 2 + 0.3, w / 2 - 0.3):
        for dz in (-d / 2 + 0.3, d / 2 - 0.3):
            s.box((0.3, h - 0.15, 0.3), (x + dx, (h - 0.15) / 2, z + dz), color, "Wood")


def rug(s: Set, pos, w=6.0, d=4.0, color=(200, 80, 90)):
    x, _, z = pos
    s.box((w, 0.08, d), (x, 0.04, z), color, "Fabric")
    s.box((w - 1.0, 0.09, d - 1.0), (x, 0.045, z), tuple(min(255, c + 30) for c in color), "Fabric")


def lamp(s: Set, pos, shade=(250, 230, 180)):
    x, _, z = pos
    s.cyl(0.3, 0.6, (x, 0.15, z), METAL, "Metal")
    s.cyl(5.0, 0.12, (x, 2.6, z), METAL, "Metal")
    s.cyl(1.2, 0.8, (x, 5.4, z), shade, "Fabric")
    s.light((x, 5.0, z), (255, 225, 170), 1.2, 16)


def counter(s: Set, pos, w=10.0, axis="x"):
    x, _, z = pos
    s.box((w, 3.0, 2.4), (x, 1.5, z), WHITE)
    s.box((w + 0.2, 0.3, 2.6), (x, 3.15, z), (60, 60, 70), "Granite")
    for k in range(int(w // 2.5)):
        s.box((0.15, 0.6, 0.12), (x - w / 2 + 1.25 + k * 2.5, 2.4, z - 1.25), METAL, "Metal")
    s.box((2.0, 0.2, 1.4), (x + w / 4, 3.31, z), (180, 185, 195), "Metal")  # the sink


def fridge(s: Set, pos):
    x, _, z = pos
    s.box((3.4, 8.0, 3.0), (x, 4.0, z), (235, 238, 242), "Metal")
    s.box((3.42, 0.08, 3.02), (x, 5.4, z), (180, 185, 195))
    s.box((0.2, 1.6, 0.2), (x + 1.3, 6.4, z - 1.55), METAL, "Metal")
    s.box((0.2, 2.0, 0.2), (x + 1.3, 3.6, z - 1.55), METAL, "Metal")


def tree(s: Set, pos, h=12.0, seed=1):
    x, _, z = pos
    rng = random.Random(seed)
    s.cyl(h * 0.55, 0.7, (x, h * 0.27, z), (110, 75, 50), "Wood")
    for _ in range(5):
        d = rng.uniform(5, 7.5)
        s.ball(d, (x + rng.uniform(-2, 2), h * 0.62 + rng.uniform(-1, 2.5), z + rng.uniform(-2, 2)),
               rng.choice([(70, 160, 70), (60, 145, 65), (85, 175, 80)]), "Grass")


def pine(s: Set, pos, h=14.0):
    x, _, z = pos
    s.cyl(3.0, 0.6, (x, 1.5, z), (100, 70, 45), "Wood")
    for k in range(4):
        w = 7.5 - 1.6 * k
        y = 3.0 + k * 2.6
        for rot in (0, 45):
            s.box((w, 2.8, w), (x, y + 1.4, z), (50, 120, 70), "Grass", rot=(0, rot, 0))


def streetlamp(s: Set, pos, on=False):
    x, _, z = pos
    s.cyl(12.0, 0.25, (x, 6.0, z), (60, 60, 70), "Metal")
    s.box((2.6, 0.3, 0.6), (x + 1.1, 12.0, z), (60, 60, 70), "Metal")
    s.box((1.2, 0.4, 0.8), (x + 2.1, 11.8, z), (255, 240, 200) if on else (220, 220, 210), "Neon" if on else "Glass")
    if on:
        s.light((x + 2.1, 10.8, z), (255, 214, 150), 2.2, 34, shadows=True)


def house(s: Set, pos, w=24.0, d=18.0, h=12.0, wall=(235, 220, 190), roof=(170, 70, 60), door_color=(60, 110, 190),
          face=-1, windows_lit=False):
    """A house facade with depth: walls, a pitched roof, a door and four windows, facing -z (face=-1) or +z."""
    x, _, z = pos
    s.box((w, h, d), (x, h / 2, z), wall, "Plaster")
    s.wedge((w + 1, 5, d / 2 + 0.6), (x, h + 2.5, z - face * d / 4), roof, "RoofShingles", rot=(0, 0 if face < 0 else 180, 0))
    s.wedge((w + 1, 5, d / 2 + 0.6), (x, h + 2.5, z + face * d / 4), roof, "RoofShingles", rot=(0, 180 if face < 0 else 0, 0))
    fz = z + face * (d / 2 + 0.05)
    s.box((4.0, 7.5, 0.3), (x, 3.75, fz), door_color, "Wood")
    s.box((5.0, 0.5, 1.2), (x, 7.8, fz + face * 0.4), WHITE)
    glass = (255, 215, 140) if windows_lit else (160, 200, 235)
    for dx in (-w / 3, w / 3):
        for y in (4.5,):
            s.box((5.0, 4.0, 0.3), (x + dx, y, fz), glass, "Neon" if windows_lit else "Glass")
            s.box((5.6, 0.4, 0.6), (x + dx, y - 2.2, fz + face * 0.2), WHITE)
    s.box((w, 0.6, 1.2), (x, h - 0.3, fz + face * 0.4), WHITE)


def car(s: Set, pos, color=(220, 60, 60), axis="x"):
    x, _, z = pos
    long_ = (11.0, 2.4, 5.0) if axis == "x" else (5.0, 2.4, 11.0)
    s.box(long_, (x, 1.9, z), color, "Metal", reflect=0.05)
    cab = (6.0, 2.0, 4.6) if axis == "x" else (4.6, 2.0, 6.0)
    s.box(cab, (x, 4.1, z), (170, 205, 235), "Glass", transparency=0.25)
    s.box((cab[0] + 0.2, 0.3, cab[2] + 0.2), (x, 5.2, z), color, "Metal")
    for dx in (-3.5, 3.5):
        for dz in (-2.5, 2.5):
            px, pz = (x + dx, z + dz) if axis == "x" else (x + dz, z + dx)
            s.cyl(1.0, 1.0, (px, 1.0, pz), BLACK, "Rubber", axis="z" if axis == "x" else "x")


def fence(s: Set, x0, x1, z, color=(250, 250, 250)):
    n = int((x1 - x0) // 2)
    for k in range(n + 1):
        s.box((0.4, 3.2, 0.4), (x0 + k * 2, 1.6, z), color, "Wood")
    for y in (1.0, 2.4):
        s.box((x1 - x0, 0.35, 0.2), ((x0 + x1) / 2, y, z), color, "Wood")


def _yaw(facing) -> float:
    """The yaw in degrees that turns a prop's front (+z) toward `facing`."""
    return math.degrees(math.atan2(facing[0], facing[2]))


def _rot(dx, dz, yaw_deg):
    a = math.radians(yaw_deg)
    return dx * math.cos(a) + dz * math.sin(a), -dx * math.sin(a) + dz * math.cos(a)


def dog(s: Set, pos, facing=(0, 0, 1), color=(205, 150, 90), spot=(240, 230, 215), collar=(220, 50, 60), size=1.0):
    """A blocky dog standing on the floor at pos (x, _, z), facing `facing`: body, legs, head with a snout, floppy
    ears, a tail, black bead eyes and a nose, a collar. About 3 studs long, its head 2.6 up at size 1."""
    x, _, z = pos
    yaw = _yaw(facing)
    k = size

    def at(dx, dy, dz):
        rx, rz = _rot(dx * k, dz * k, yaw)
        return (x + rx, dy * k, z + rz)

    def box(size_, d, color_, mat="SmoothPlastic"):
        s.box(tuple(v * k for v in size_), at(*d), color_, mat, rot=(0, yaw, 0))

    box((1.3, 1.0, 2.2), (0, 1.25, 0), color, "Fabric")                     # body
    box((1.0, 0.5, 1.2), (0, 0.85, 0.15), spot, "Fabric")                   # belly
    for dx in (-0.45, 0.45):
        for dz in (-0.75, 0.75):
            box((0.38, 0.8, 0.38), (dx, 0.4, dz), color, "Fabric")         # legs
            box((0.42, 0.18, 0.5), (dx, 0.09, dz + 0.06), spot, "Fabric")   # paws
    box((1.15, 1.0, 1.0), (0, 2.05, 1.3), color, "Fabric")                  # head
    box((0.7, 0.5, 0.55), (0, 1.8, 1.95), spot, "Fabric")                   # snout
    box((0.28, 0.2, 0.12), (0, 1.97, 2.25), (25, 20, 20))                   # nose
    for dx in (-0.3, 0.3):
        box((0.16, 0.2, 0.08), (dx, 2.25, 1.82), (20, 20, 20))              # eyes
        box((0.06, 0.07, 0.04), (dx - 0.03, 2.3, 1.87), (255, 255, 255))    # catchlights
    for dx in (-0.62, 0.62):
        box((0.2, 0.75, 0.55), (dx, 2.0, 1.2), tuple(int(c * 0.75) for c in color), "Fabric")   # ears
    box((1.2, 0.18, 1.05), (0, 1.62, 1.25), collar)                          # collar
    s.box((0.22 * k, 0.22 * k, 0.9 * k), at(0, 1.75, -1.35), color, "Fabric", rot=(-35, yaw, 0))   # tail


def cat(s: Set, pos, facing=(0, 0, 1), color=(110, 110, 120), size=1.0):
    """A blocky sitting cat: a slimmer body, pointed ears, a long tail, green eyes."""
    x, _, z = pos
    yaw = _yaw(facing)
    k = size

    def at(dx, dy, dz):
        rx, rz = _rot(dx * k, dz * k, yaw)
        return (x + rx, dy * k, z + rz)

    def box(size_, d, color_, rot=(0, 0, 0)):
        s.box(tuple(v * k for v in size_), at(*d), color_, "Fabric", rot=(rot[0], yaw + rot[1], rot[2]))

    box((0.9, 1.2, 1.1), (0, 0.6, 0), color)                   # sitting body
    box((0.85, 0.75, 0.75), (0, 1.55, 0.25), color)            # head
    for dx in (-0.25, 0.25):
        s.wedge((0.25 * k, 0.35 * k, 0.2 * k), at(dx, 2.08, 0.25), color, "Fabric", rot=(0, yaw, 0))   # ears
        box((0.14, 0.16, 0.06), (dx, 1.62, 0.64), (60, 180, 80))                                      # eyes
    box((0.12, 0.08, 0.06), (0, 1.48, 0.65), (240, 140, 150))  # nose
    box((0.18, 0.18, 1.2), (0.35, 0.12, -0.5), color, rot=(0, 25, 0))   # tail


def balloons(s: Set, pos, colors=((235, 70, 90), (70, 150, 235), (250, 200, 60)), height=6.5):
    """A bunch of party balloons tied at pos (x, _, z): three balls on thin strings, a little apart."""
    x, _, z = pos
    for k, (dx, dz, c) in enumerate(zip((-0.7, 0.6, 0.0), (0.2, -0.3, 0.6), colors)):
        top = height + 0.6 * k
        s.ball(1.5, (x + dx, top, z + dz), c)
        s.box((0.05, top - 0.75, 0.05), (x + dx / 2, (top - 0.75) / 2, z + dz / 2), (240, 240, 240))
    s.box((0.4, 0.3, 0.4), (x, 0.15, z), (90, 90, 100))        # the weight


def cake(s: Set, pos, frosting=(250, 225, 235), sponge=(235, 190, 120), candles=3):
    """A two-tier birthday cake to stand on a table top (pos y is the surface), candles lit with a small light."""
    x, y, z = pos
    s.cyl(0.9, 1.4, (x, y + 0.45, z), sponge)
    s.cyl(0.15, 1.45, (x, y + 0.92, z), frosting)
    s.cyl(0.7, 1.0, (x, y + 1.35, z), sponge)
    s.cyl(0.12, 1.05, (x, y + 1.72, z), frosting)
    for k in range(candles):
        dx = (k - (candles - 1) / 2) * 0.5
        s.cyl(0.5, 0.06, (x + dx, y + 2.03, z), (120, 180, 240))
        s.ball(0.16, (x + dx, y + 2.35, z), (255, 200, 80), "Neon")
    s.light((x, y + 2.6, z), (255, 190, 120), 0.8, 8)


def smoothie(s: Set, pos, color=(240, 120, 160)):
    """A tall smoothie cup with a lid and a straw, to stand on a surface (pos y is the surface)."""
    x, y, z = pos
    s.cyl(1.0, 0.32, (x, y + 0.5, z), color, transparency=0.1)
    s.cyl(0.08, 0.35, (x, y + 1.04, z), (245, 245, 245))
    s.box((0.07, 0.8, 0.07), (x + 0.1, y + 1.4, z), (60, 160, 230), rot=(0, 0, -12))


def ice_pack(s: Set, pos, color=(150, 205, 245)):
    """A soft-looking ice pack lying on a surface (pos y is the surface)."""
    x, y, z = pos
    s.box((1.1, 0.22, 0.75), (x, y + 0.11, z), color, "Fabric")
    s.box((0.9, 0.05, 0.55), (x, y + 0.24, z), (210, 235, 250), "Fabric")


def wall_phone(s: Set, pos, facing=(0, 0, 1), color=(70, 70, 80)):
    """An old wall phone: a base on the wall at pos (x, y, z: its centre), a handset on its hook, a coiled cord."""
    x, y, z = pos
    yaw = _yaw(facing)

    def at(dx, dy, dz):
        rx, rz = _rot(dx, dz, yaw)
        return (x + rx, y + dy, z + rz)

    s.box((0.9, 1.5, 0.3), at(0, 0, 0), color, rot=(0, yaw, 0))
    s.box((0.35, 1.3, 0.3), at(-0.15, 0.05, 0.3), (40, 40, 48), rot=(0, yaw, 0))      # the handset
    s.box((0.3, 0.3, 0.05), at(0.25, 0.3, 0.17), (200, 200, 210), rot=(0, yaw, 0))     # the keypad
    for k in range(6):                                                                 # the cord's coils
        s.cyl(0.08, 0.08, at(-0.15, -0.75 - 0.12 * k, 0.32), (40, 40, 48), axis="x")


def locker_bank(s: Set, pos, facing=(0, 0, 1), n: int = 3, color=(205, 60, 60), h: float = 7.0):
    """A free-standing bank of `n` lockers on the floor at pos, their doors facing `facing` (+-x or +-z), a plain
    steel back: something to hide behind and listen ("he hid behind the lockers")."""
    x, _, z = pos
    ax = "x" if abs(facing[0]) > abs(facing[2]) else "z"
    f = 1 if (facing[0] if ax == "x" else facing[2]) > 0 else -1
    w, depth = 1.8, 1.6
    span = n * (w + 0.05)
    for i in range(n):
        o = -span / 2 + (i + 0.5) * (w + 0.05)
        cx, cz = (x, z + o) if ax == "x" else (x + o, z)
        size = (depth, h, w) if ax == "x" else (w, h, depth)
        s.box(size, (cx, h / 2, cz), color, "Metal")
        for k in range(3):   # vents, and the handle
            vy = h - 1.0 - 0.3 * k
            if ax == "x":
                s.box((0.05, 0.12, w * 0.6), (cx + f * (depth / 2 + 0.02), vy, cz), tuple(int(c * 0.72) for c in color))
            else:
                s.box((w * 0.6, 0.12, 0.05), (cx, vy, cz + f * (depth / 2 + 0.02)), tuple(int(c * 0.72) for c in color))
        if ax == "x":
            s.box((0.12, 0.7, 0.15), (cx + f * (depth / 2 + 0.05), h * 0.48, cz + w * 0.3), METAL, "Metal")
        else:
            s.box((0.15, 0.7, 0.12), (cx + w * 0.3, h * 0.48, cz + f * (depth / 2 + 0.05)), METAL, "Metal")
    top = (depth + 0.1, 0.3, span) if ax == "x" else (span, 0.3, depth + 0.1)
    s.box(top, (x, h + 0.15, z), tuple(int(c * 0.72) for c in color), "Metal")


PROPS = {"dog": dog, "cat": cat, "plant": plant, "lamp": lamp, "table": table, "rug": rug, "car": car, "tree": tree,
         "pine": pine, "bookshelf": bookshelf, "sofa": sofa, "tv": tv,
         "balloons": balloons, "cake": cake, "smoothie": smoothie, "ice_pack": ice_pack, "wall_phone": wall_phone,
         "lockers": locker_bank}


def props(s: Set, items: list) -> None:
    """Props placed by a set's options: [{"kind": "dog", "at": [x, 0, z], "facing": [..], ...}, ...]."""
    for it in items or []:
        kw = {k: (tuple(v) if isinstance(v, list) else v) for k, v in it.items() if k not in ("kind", "at")}
        PROPS[it["kind"]](s, tuple(it["at"]), **kw)


# ---------------------------------------------------------------------------------------------------- the sets


def classroom(opt: dict) -> Set:
    """A bright classroom, 44 x 36: four rows of three desks facing the whiteboard at -z, the teacher's desk in
    front, windows down the +x wall, the door at the back of the -x wall, posters, a clock, lights."""
    s = Set("classroom", opt.get("lighting", "interior"))
    W, D, H = 44.0, 36.0, 15.0
    room(s, W, D, H, wall=(206, 216, 234), trim=(64, 110, 205), floor=(196, 198, 206), floor_mat="Marble",
         gaps={"e": [(6, 14, 4.5, 11.5), (16, 24, 4.5, 11.5), (26, 34, 4.5, 11.5)], "w": [(28, 32.5, 0, 7.8)]})
    for zc in (-12, -2, 8):  # windows in the +x wall's openings
        window(s, (W / 2 + 0.5, 8.0, -zc), 8.0, 7.0, axis="x")
    door(s, (-W / 2 - 0.3, 0, D / 2 - 6.25), axis="x")
    whiteboard(s, (0, 8.5, -D / 2 + 0.2), w=18, h=6.5, text=opt.get("board", "Group project due FRIDAY"),
               axis="z", toward=1)
    teacher_desk(s, (-9, 0, -D / 2 + 6))
    for r, z in enumerate((-4, 3, 10)):
        for c, x in enumerate((-12, -3, 6, 15)):
            school_desk(s, (x, 0, z), face=(0, 0, -1), chair=[(60, 110, 200), (220, 90, 70), (70, 170, 110)][(r + c) % 3])
    for i, (x, col, txt) in enumerate(((-17, (240, 180, 60), "READ!"), (14, (90, 190, 120), "Be kind"))):
        poster(s, (x, 9.5, -D / 2 + 0.6), (5, 4), col, txt, axis="z", face="Back")
    poster(s, (-W / 2 + 0.6, 9.0, -6), (6, 4.5), (230, 90, 120), "MATH IS FUN?", axis="x", face="Right")
    clock(s, (12, 12.0, -D / 2 + 0.6), axis="z")
    bookshelf(s, (W / 2 - 1.2, 0, 13), axis="x", w=7)
    plant(s, (-W / 2 + 2.5, 0, -D / 2 + 2.5))
    for x in (-11, 0, 11):
        for z in (-8, 6):
            ceiling_light(s, (x, H - 0.4, z), length=8, axis="x")
    s.mark("teacher", (-9, 3, -D / 2 + 9), (-9, 3, 0))
    s.mark("board", (3, 3, -D / 2 + 4), (3, 3, 10))
    for r, z in enumerate((-4, 3, 10)):
        for c, x in enumerate((-12, -3, 6, 15)):
            s.mark(f"desk{r + 1}{'abcd'[c]}", (x, 3, z - 2.1 + 2.1), (x, 3, z - 10))
            s.mark(f"seat{r + 1}{'abcd'[c]}", (x, 2.2, z + 2.1), (x, 2.2, z - 10))
    s.mark("door", (-W / 2 + 3, 3, D / 2 - 6.25), (0, 3, D / 2 - 6.25))
    s.mark("aisle", (1.5, 3, 4), (1.5, 3, -10))
    s.cam("back_wide", (14, 9, 16), (-2, 4, -10), 60)
    s.cam("front_wide", (-6, 7, -15), (6, 3.5, 10), 60)
    s.cam("students", (10, 5, -10), (-4, 3.5, 6), 50)
    s.park = (0, 3, -80)
    return s


def hallway(opt: dict) -> Set:
    """A school hallway 18 wide and 80 long along z: red lockers both sides, doors between banks, blue trim, a
    marble floor and a row of ceiling lights, windows at the far end (as the references' corridor)."""
    s = Set("hallway", opt.get("lighting", "interior"))
    W, L, H = 18.0, 80.0, 15.0
    room(s, W, L, H, wall=(208, 216, 232), trim=(60, 108, 205), floor=(212, 212, 220), floor_mat="Marble",
         gaps={"n": [(4, 14, 4.5, 11.5)]})
    window(s, (0, 8.0, L / 2 + 0.5), 10.0, 7.0, axis="z")
    for side, x in ((1, -W / 2 + 0.8), (-1, W / 2 - 0.8)):
        for z0 in (-36, -18, 0, 18):
            for i in range(7):
                z = z0 + i * 1.85
                s.box((1.6, 7.0, 1.8), (x, 3.5, z), opt.get("lockers", (205, 60, 60)), "Metal")
                s.box((0.05, 0.12, 1.08), (x + side * 0.82, 6.2, z), (150, 40, 40))
                s.box((0.05, 0.12, 1.08), (x + side * 0.82, 5.9, z), (150, 40, 40))
                s.box((0.12, 0.7, 0.15), (x + side * 0.85, 3.4, z + 0.5), METAL, "Metal")
            s.box((1.7, 0.3, 7 * 1.85), (x, 7.15, z0 + 3 * 1.85), (150, 40, 40), "Metal")
        for zd in (-23, -5, 31):
            door(s, (x - side * 0.2, 0, zd), axis="x", color=(130, 85, 55))
    for z in range(-34, 36, 12):
        ceiling_light(s, (0, H - 0.4, z), length=9, axis="z", brightness=0.8)
    poster(s, (-W / 2 + 0.6, 9.5, 12.5), (5, 3.5), (250, 200, 60), "SPIRIT WEEK", axis="x", face="Right",
           fg=(40, 40, 60))
    poster(s, (W / 2 - 0.6, 9.5, -12.5), (5, 3.5), (90, 160, 240), "NO RUNNING", axis="x", face="Left")
    s.mark("centre", (0, 3, 0), (0, 3, -10))
    s.mark("near", (0, 3, -20), (0, 3, 10))
    s.mark("far", (0, 3, 20), (0, 3, -10))
    s.mark("lockers_left", (-W / 2 + 3.2, 3, 4), (W / 2, 3, 4))
    s.mark("lockers_right", (W / 2 - 3.2, 3, -4), (-W / 2, 3, -4))
    s.cam("down_hall", (0, 6, -30), (0, 5, 10), 60)
    s.cam("up_hall", (2, 6, 30), (-1, 5, -10), 60)
    s.cam("lockers", (4, 5, -2), (-9, 4, 6), 55)
    s.park = (0, 3, -120)
    return s


def bedroom(opt: dict) -> Set:
    """A teen's bedroom, 28 x 24: the bed against the +z wall, a desk with a computer by the window in the -x wall,
    posters, a rug, a lamp, a bookshelf, the door in the +x wall."""
    s = Set("bedroom", opt.get("lighting", "interior"))
    W, D, H = 28.0, 24.0, 13.0
    room(s, W, D, H, wall=opt.get("walls", (180, 200, 240)), trim=(255, 255, 255), floor=(160, 115, 80),
         floor_mat="WoodPlanks", gaps={"w": [(8, 16, 4.5, 10.5)], "e": [(14, 18.5, 0, 7.8)]})
    window(s, (-W / 2 - 0.5, 7.5, 0), 8.0, 6.0, axis="x")
    door(s, (W / 2 + 0.3, 0, D / 2 - 7.75), axis="x")
    bed(s, (4, 0, D / 2 - 0.6), face=(0, 0, -1), blanket=opt.get("blanket", (90, 140, 230)))
    table(s, (-W / 2 + 3.2, 0, -5), w=3.6, d=7.0, h=3.2, color=WHITE)
    s.box((0.4, 2.6, 3.6), (-W / 2 + 2.2, 4.9, -5), BLACK)  # monitor
    s.box((0.1, 2.2, 3.2), (-W / 2 + 2.45, 4.9, -5), (70, 110, 220), "Neon")
    s.box((1.2, 0.15, 2.6), (-W / 2 + 3.6, 3.45, -5), (40, 40, 45))  # keyboard
    s.box((2.4, 0.3, 2.4), (-W / 2 + 6.2, 2.0, -5), (40, 40, 45))  # chair seat
    s.box((0.3, 3.0, 2.4), (-W / 2 + 7.3, 3.6, -5), (40, 40, 45))
    s.cyl(1.9, 0.15, (-W / 2 + 6.2, 1.0, -5), METAL, "Metal")
    rug(s, (2, 0, 0), 10, 8, opt.get("rug", (120, 90, 200)))
    lamp(s, (-W / 2 + 2.0, 0, D / 2 - 2.0))
    bookshelf(s, (W / 2 - 1.2, 0, -4), axis="x", w=6, seed=3)
    for x, col, txt in ((-2, (230, 80, 120), "GAME ON"), (10, (60, 180, 220), "")):
        poster(s, (x, 8.5, D / 2 - 0.6), (4.5, 6), col, txt, axis="z", face="Front")
    s.light((0, H - 1.5, 0), (255, 240, 220), 1.0, 30)
    s.mark("bed", (4, 3, D / 2 - 7), (4, 3, 0))
    s.mark("desk_chair", (-W / 2 + 6.2, 3, -5), (-W / 2, 3, -5))
    s.mark("centre", (2, 3, 0), (2, 3, -10))
    s.mark("door", (W / 2 - 3, 3, D / 2 - 7.75), (0, 3, D / 2 - 7.75))
    s.cam("from_door", (11, 7, -9), (-2, 3.5, 6), 60)
    s.cam("bed_side", (-8, 6, 6), (6, 3, 10), 55)
    s.cam("desk", (-4, 5.5, -1), (-14, 4, -6), 55)
    s.park = (0, 3, -70)
    return s


def living_room(opt: dict) -> Set:
    """A family living room with a kitchen behind it, 40 x 30: the sofa facing the TV, a rug, a coffee table, a lamp,
    a plant, the kitchen counter and fridge along the -z wall, a window and the front door."""
    s = Set("living_room", opt.get("lighting", "interior"))
    W, D, H = 40.0, 30.0, 14.0
    room(s, W, D, H, wall=(238, 226, 205), trim=(150, 105, 70), floor=(175, 125, 85), floor_mat="WoodPlanks",
         gaps={"n": [(6, 14, 4.5, 11), (26, 34, 4.5, 11)], "e": [(4, 8.5, 0, 7.8)]})
    for x in (-10, 10):
        window(s, (x, 7.75, D / 2 + 0.5), 8.0, 6.5, axis="z")
    door(s, (W / 2 + 0.3, 0, -D / 2 + 6.25), axis="x", color=(170, 40, 40))
    sofa(s, (-2, 0, 8), face=(0, 0, -1), color=opt.get("sofa", (95, 120, 190)))
    tv(s, (-2, 0, -2.5), face=(0, 0, 1))
    rug(s, (-2, 0, 3), 14, 9, (190, 70, 80))
    table(s, (-2, 0, 3.5), w=5, d=2.6, h=1.6, color=DARK_WOOD)
    lamp(s, (6.5, 0, 9.5))
    plant(s, (-11, 0, 11))
    counter(s, (-6, 0, -D / 2 + 1.5), w=16)
    fridge(s, (6, 0, -D / 2 + 1.8))
    for x, col in ((-14, (240, 200, 120)), (-10, (160, 200, 230))):
        poster(s, (x, 8.5, -D / 2 + 0.6), (3, 2.4), col, "", axis="z")
    s.light((-2, H - 1.5, 3), (255, 240, 220), 1.0, 34)
    s.light((-4, H - 1.5, -10), (255, 245, 230), 0.8, 26)
    s.mark("sofa_left", (-4, 2.2, 8.4), (-4, 2.2, -2))
    s.mark("sofa_right", (0, 2.2, 8.4), (0, 2.2, -2))
    s.mark("kitchen", (-6, 3, -D / 2 + 5), (-6, 3, 0))
    s.mark("centre", (-2, 3, 0.5), (-2, 3, 10))
    s.mark("front_door", (W / 2 - 3, 3, -D / 2 + 6.25), (0, 3, -D / 2 + 6.25))
    s.cam("tv_side", (-2, 6, -1), (-2, 3, 12), 60)
    s.cam("wide", (14, 8, 10), (-6, 3.5, -4), 60)
    s.cam("kitchen", (4, 6, 2), (-8, 4, -12), 55)
    s.park = (0, 3, -80)
    return s


def street(opt: dict) -> Set:
    """A suburban street along x: the road with its lines, sidewalks, houses both sides with lawns and fences,
    trees, streetlamps (lit at night), a parked car. opt["night"] = True lights it for night."""
    night = bool(opt.get("night"))
    s = Set("street", opt.get("lighting", "night" if night else "day"), hide_baseplate=True)
    L = 140.0
    s.box((L, 1, 200), (0, -0.5, 0), (90, 160, 80), "Grass")
    s.box((L, 0.1, 20), (0, 0.05, 0), (60, 62, 68), "Asphalt")
    for x in range(-66, 70, 10):
        s.box((5, 0.12, 0.5), (x, 0.11, 0), (240, 230, 120))
    for z in (-12.5, 12.5):
        s.box((L, 0.5, 5), (0, 0.25, z), (190, 190, 195), "Concrete")
    colours = [(235, 220, 190), (190, 215, 235), (240, 200, 200), (210, 230, 200), (240, 235, 210)]
    roofs = [(170, 70, 60), (80, 90, 110), (120, 80, 60), (90, 110, 80)]
    for i, x in enumerate(range(-52, 60, 34)):
        house(s, (x, 0, 36), wall=colours[i % 5], roof=roofs[i % 4], face=-1, windows_lit=night)
        house(s, (x + 17, 0, -36), wall=colours[(i + 2) % 5], roof=roofs[(i + 1) % 4], face=1, windows_lit=night)
        fence(s, x - 13, x - 4, 22)
        fence(s, x + 4, x + 13, 22)
        tree(s, (x + 17, 0, 19), seed=i)
        tree(s, (x - 1, 0, -19), seed=i + 10)
    for x in (-50, -10, 30, 70):
        streetlamp(s, (x, 0, 15.5), on=night)
    car(s, (12, 0, 7), color=opt.get("car", (220, 60, 60)))
    s.mark("sidewalk_a", (-6, 3.5, -12.5), (10, 3.5, -12.5))
    s.mark("sidewalk_b", (6, 3.5, -12.5), (-10, 3.5, -12.5))
    s.mark("road", (0, 3, -3), (0, 3, 10))
    s.mark("lawn", (-35, 3, 26), (-35, 3, 0))
    s.mark("porch", (-52, 3, 25), (-52, 3, 0))
    s.cam("street", (0, 6, -14), (10, 5, 30), 60)
    s.cam("along", (-40, 5, -6), (30, 4, 4), 50)
    s.cam("houses", (-10, 8, -16), (-30, 8, 36), 60)
    s.park = (0, 3, -110)
    return s


def stage_void(opt: dict) -> Set:
    """A plain coloured cyclorama: a floor and a back wall in one colour, for comparisons and lists (family C)."""
    s = Set("stage_void", opt.get("lighting", "interior"))
    c = tuple(opt.get("color", (140, 190, 255)))
    s.box((120, 1, 120), (0, -0.5, 0), c)
    s.box((120, 60, 1), (0, 30, -30), c)
    s.light((0, 20, 20), (255, 255, 255), 1.0, 60)
    s.mark("centre", (0, 3, 0), (0, 3, 10))
    s.mark("left", (-4, 3, 0), (-4, 3, 10))
    s.mark("right", (4, 3, 0), (4, 3, 10))
    s.cam("front", (0, 4.5, 14), (0, 4, 0), 50)
    s.park = (0, 3, -60)
    return s


def hoop(s: Set, x_wall: float, z: float = 0.0, toward: int = -1, rim=(240, 100, 30)):
    """A basketball hoop on the end wall at x_wall, facing `toward` (+1 faces +x): a brace, a backboard with its
    target square, an orange rim 10 studs up (twice an R6's height, as a real one is twice a teen's) and a net."""
    f = toward
    s.box((2.2, 0.5, 0.5), (x_wall + f * 1.1, 13.0, z), METAL, "Metal")
    bx = x_wall + f * 2.35
    s.box((0.3, 4.0, 6.5), (bx, 13.4, z), (245, 245, 248))
    face = bx + f * 0.17
    for dy in (-0.9, 0.9):
        s.box((0.06, 0.14, 2.4), (face, 12.3 + dy, z), (220, 50, 50))
    for dz in (-1.13, 1.13):
        s.box((0.06, 1.8, 0.14), (face, 12.3, z + dz), (220, 50, 50))
    cx = bx + f * 1.25
    for k in range(10):
        a = 2 * math.pi * k / 10
        s.box((0.62, 0.12, 0.2), (cx + 0.95 * math.cos(a), 11.4, z + 0.95 * math.sin(a)), rim, "Metal",
              rot=(0, -math.degrees(a) + 90, 0))
    s.box((0.9, 0.12, 0.2), (bx + f * 0.45, 11.4, z), rim, "Metal")
    s.cyl(1.5, 0.85, (cx, 10.6, z), (250, 250, 250), "Fabric", transparency=0.45)


def bleachers(s: Set, x: float, z_front: float, z_back: float, w: float = 40.0, tiers: int = 5, rise: float = 1.25,
              colors=((198, 148, 94), (178, 130, 82))):
    """Wooden bleachers along a wall: `tiers` steps rising from z_front to the wall at z_back (z_back > z_front)."""
    step = (z_back - z_front) / tiers
    for k in range(tiers):
        z0 = z_front + step * k
        h = rise * (k + 1)
        s.box((w, h, z_back - z0), (x, h / 2, (z0 + z_back) / 2), colors[k % 2], "WoodPlanks")
        s.box((w, 0.12, 0.25), (x, h + 0.02, z0 + 0.15), (240, 240, 240))   # a white nosing on each step
    s.box((w, 0.25, 0.25), (x, rise * tiers + 2.6, z_back - 0.3), METAL, "Metal")   # the rail at the top
    for dx in (-w / 2, 0.0, w / 2):
        s.box((0.25, 2.6, 0.25), (x + dx, rise * tiers + 1.3, z_back - 0.3), METAL, "Metal")


def gym(opt: dict) -> Set:
    """A school gym, 64 x 44 x 26: a honey wood court with its lines and blue paint, a hoop at each end, wooden
    bleachers along the +z wall, blue and gold banners, high windows, a scoreboard over the doors' wall, stacked
    mats and a ball rack. {"dance": True} dresses it for the school dance: balloons along the walls, streamers under
    the ceiling, a mirror ball, coloured lights and a DJ table with speakers. {"scoreboard": False} leaves it off."""
    s = Set("gym", opt.get("lighting", "interior"))
    W, D, H = 64.0, 44.0, 26.0
    BLUE, GOLD = (40, 85, 200), (250, 190, 50)
    room(s, W, D, H, wall=(206, 212, 224), trim=BLUE, floor=(196, 140, 82), floor_mat="WoodPlanks",
         gaps={"n": [(10, 20, 17, 23), (27, 37, 17, 23), (44, 54, 17, 23)], "s": [(4, 14, 0, 9)]})
    for xc in (-17, 0, 17):
        window(s, (xc, 20.0, D / 2 + 0.5), 10.0, 6.0, axis="z")
    for xc in (-25.6, -20.4):
        door(s, (xc, 0, -D / 2 - 0.3), axis="z", color=(60, 95, 180), w=4.8, h=8.6)
    # the court: blue paint, then white lines a hair above it
    L, C = 0.05, (250, 250, 250)
    for sx in (-1, 1):
        s.box((12, 0.04, 10), (sx * 22, 0.02, 0), BLUE)
        s.box((0.35, L, 10.35), (sx * 16, L / 2, 0), C)
        for dz in (-5, 5):
            s.box((12, L, 0.35), (sx * 22, L / 2, dz), C)
    for dz in (-15, 15):
        s.box((56.35, L, 0.35), (0, L / 2, dz), C)
    for dx in (-28, 28):
        s.box((0.35, L, 30.35), (dx, L / 2, 0), C)
    s.box((0.35, L, 30), (0, L / 2, 0), C)
    s.cyl(0.06, 4.6, (0, 0.03, 0), C, axis="y")
    s.cyl(0.07, 4.25, (0, 0.035, 0), BLUE, axis="y")
    s.cyl(0.08, 1.2, (0, 0.04, 0), GOLD, axis="y")
    hoop(s, -W / 2, 0, toward=1)
    hoop(s, W / 2, 0, toward=-1)
    bleachers(s, 0, 8.0, D / 2, w=40, tiers=5)
    for xc in (-24, -12, 12, 24):   # banners: under the high windows over the bleachers, and either side of the
        for zw, y in ((D / 2 - 0.3, 13.0), (-D / 2 + 0.3, 15.5)):   # scoreboard (not over the doors)
            if zw < 0 and xc < -10:
                continue
            s.box((4.5, 6.0, 0.2), (xc, y, zw), BLUE)
            s.box((4.5, 0.8, 0.24), (xc, y - 2.2, zw), GOLD)
    if opt.get("scoreboard", True):
        s.box((14.6, 6.0, 0.6), (0, 19.0, -D / 2 + 0.4), (24, 24, 28))
        s.sign((6.6, 5.0, 0.1), (-3.5, 19.0, -D / 2 + 0.75), "HOME\n24", face="Back", bg=(24, 24, 28),
               fg=(255, 90, 60), font="Arcade", scale=0.85)
        s.sign((6.6, 5.0, 0.1), (3.5, 19.0, -D / 2 + 0.75), "GUEST\n18", face="Back", bg=(24, 24, 28),
               fg=(255, 200, 60), font="Arcade", scale=0.85)
    for k, dy in enumerate((0.35, 1.05, 1.75)):   # mats stacked in the corner
        s.box((6.0, 0.7, 4.0), (-27.5 + 0.15 * k, dy, 17.5 - 0.1 * k), BLUE if k % 2 == 0 else (70, 120, 220),
              "Fabric")
    s.box((5.2, 0.25, 1.4), (27, 1.4, -18.5), METAL, "Metal")   # the ball rack
    s.box((5.2, 0.25, 1.4), (27, 2.9, -18.5), METAL, "Metal")
    for dx in (-2.5, 2.5):
        s.box((0.25, 3.2, 1.4), (27 + dx, 1.6, -18.5), METAL, "Metal")
    for row, y in ((0, 2.1), (1, 3.6)):
        for k in range(4):
            s.ball(1.1, (25.35 + k * 1.1, y, -18.5), (225, 110, 40))
    for x in (-20, 0, 20):   # the first preview, at 0.9 and 40 studs with a light over the whole room, burned out
        for z in (-10, 10):
            ceiling_light(s, (x, H - 0.4, z), length=10, axis="x", brightness=0.45, rng=30)
    if opt.get("dance"):
        party = ((255, 90, 190), (60, 210, 255), (170, 100, 255), (255, 200, 70))
        for k, (x, z) in enumerate(((-30.5, -19.5), (-14, -19.5), (14, -19.5), (28, -19.5), (-28, 6), (28, 6),
                                    (-21, 7.2), (21, 7.2))):
            balloons(s, (x, 0, z), colors=(party[k % 4], party[(k + 1) % 4], party[(k + 2) % 4]), height=7.5)
        for k in range(28):   # streamers hanging under the ceiling, in rows across the room
            x = -27 + (k % 7) * 9
            z = -15 + (k // 7) * 10
            s.box((0.1, 4.5, 1.1), (x, H - 3.0, z), party[k % 4], "Fabric")
        s.part("ball", (3.2, 3.2, 3.2), (0, 18.0, 0), (225, 228, 240), "Foil", reflect=0.6)
        s.box((0.1, H - 19.6, 0.1), (0, (19.6 + H) / 2, 0), BLACK)
        for k, (x, z) in enumerate(((-16, -8), (16, -8), (-16, 8), (16, 8), (0, -14), (0, 12))):
            s.light((x, 7.0, z), party[k % 4], 1.1, 18)
        table(s, (0, 0, -16.5), w=8.0, d=3.0, h=3.0, color=(36, 36, 42))   # the DJ's table
        s.box((2.0, 0.25, 1.4), (0, 3.3, -16.5), (60, 60, 66))
        s.box((1.8, 1.2, 0.08), (0, 3.95, -17.1), (90, 200, 255), "Neon")
        for dx in (-6.0, 6.0):   # speakers
            s.box((2.4, 5.0, 2.2), (dx, 2.5, -17.0), (30, 30, 34))
            s.cyl(0.15, 0.85, (dx, 1.8, -15.85), (70, 70, 78), axis="z")
            s.cyl(0.15, 0.45, (dx, 3.9, -15.85), (70, 70, 78), axis="z")
    s.mark("centre", (0, 3, 2), (0, 3, -10))
    s.mark("left_court", (-16, 3, 0), (-30, 3, 0))
    s.mark("right_court", (16, 3, 0), (30, 3, 0))
    s.mark("bleachers", (-4, 5.5, 12.2), (-4, 5.5, 0))          # on the second step, facing the court
    s.mark("bleachers_high", (4, 8.0, 17.8), (4, 8.0, 0))      # on the fourth
    s.mark("door", (-23, 3, -17), (-23, 3, 0))
    s.mark("dj", (0, 3, -19.0), (0, 3, 0))
    s.cam("wide", (26, 12, -16), (-2, 4, 6), 60)
    s.cam("court", (0, 6, -14), (0, 4.5, 12), 60)
    s.cam("hoop", (14, 4.5, 4), (31, 11, 0), 55)
    s.cam("bleachers", (0, 6, 1), (0, 6, 18), 55)
    s.park = (0, 3, -150)
    return s


def lunch_table(s: Set, pos, length: float = 14.0, top=(220, 80, 80)):
    """A long cafeteria table along x with a bench down each side, in the table's colour, on steel legs, sized for
    R6 bodies sitting (pose "sit"): the benches 1 stud up, the top 2.6, its underside clear of a seated R6's legs
    (2.0). A sitter's mark is on a bench's centre line, 2.65 from the table's, facing the table."""
    x, _, z = pos
    s.box((length, 0.3, 3.6), (x, 2.45, z), top)
    s.box((length - 0.4, 0.12, 3.3), (x, 2.24, z), (150, 152, 160), "Metal")
    for dx in (-length / 2 + 1.2, length / 2 - 1.2):
        s.box((0.4, 2.2, 0.4), (x + dx, 1.1, z), METAL, "Metal")
        s.box((0.4, 0.25, 6.6), (x + dx, 0.13, z), METAL, "Metal")
        for dz in (-2.65, 2.65):
            s.box((0.35, 0.7, 0.35), (x + dx, 0.35, z + dz), METAL, "Metal")
    for dz in (-2.65, 2.65):
        s.box((length, 0.3, 1.3), (x, 0.85, z + dz), top)


def tray(s: Set, pos, color=(240, 140, 60)):
    """A lunch tray with a slice of pizza, a carton of milk and an apple. `pos` y is the table top."""
    x, y, z = pos
    s.box((1.7, 0.12, 1.15), (x, y + 0.06, z), color)
    s.wedge((0.12, 0.75, 0.9), (x - 0.35, y + 0.19, z), (245, 190, 80), rot=(0, 0, 90))
    s.box((0.35, 0.6, 0.35), (x + 0.45, y + 0.42, z - 0.2), (250, 250, 250))
    s.box((0.36, 0.18, 0.36), (x + 0.45, y + 0.42, z - 0.2), (60, 120, 220))
    s.ball(0.42, (x + 0.45, y + 0.33, z + 0.3), (215, 40, 45))


PROPS["tray"] = tray


def cafeteria(opt: dict) -> Set:
    """A school cafeteria, 52 x 40 x 15: six long tables with benches in two columns, the lunch counter along the
    -z wall with the food in steel pans behind a glass guard, a chalkboard menu drawn in pictures, two vending
    machines on the +x wall, trash cans, a bulletin board, windows in the +z wall, double doors in the -x wall. Six
    lunch trays on the tables, or none with {"trays": False} (M4's lunch alone: only his)."""
    s = Set("cafeteria", opt.get("lighting", "interior"))
    W, D, H = 52.0, 40.0, 15.0
    room(s, W, D, H, wall=(198, 232, 212), trim=(235, 125, 55), floor=(238, 232, 220), floor_mat="CeramicTiles",
         gaps={"n": [(8, 16, 4.5, 11.5), (22, 30, 4.5, 11.5), (36, 44, 4.5, 11.5)], "w": [(26, 35, 0, 8.6)]})
    for xc in (-14, 0, 14):
        window(s, (xc, 8.0, D / 2 + 0.5), 8.0, 7.0, axis="z")
    for zc in (8.25, 12.75):
        door(s, (-W / 2 - 0.3, 0, zc), axis="x", color=(205, 95, 60), w=4.3, h=8.2)
    tops = [(220, 80, 80), (70, 140, 230), (250, 195, 60)]
    for r, z in enumerate((-5, 3.5, 12)):
        for c, x in enumerate((-12, 10)):
            lunch_table(s, (x, 0, z), 14.0, tops[(r + c) % 3])
    for k, (x, z) in enumerate(((-15, -6.2), (-9, -3.8), (13, -6.2), (-12, 4.7), (7, 2.3), (12, 13.2))
                               if opt.get("trays", True) else ()):   # {"trays": False}: set your own (prop "tray")
        tray(s, (x, 2.6, z), ((240, 140, 60), (70, 190, 180))[k % 2])
    # the serving line along the -z wall
    cz = -14.5
    s.box((24, 3.0, 3.0), (2, 1.5, cz), (190, 195, 205), "Metal")
    s.box((24.2, 0.25, 3.2), (2, 3.12, cz), (165, 170, 180), "Metal")
    s.box((24, 0.2, 1.4), (2, 2.4, cz + 2.2), METAL, "Metal")
    for dx in (-11, -3.5, 3.5, 11):
        s.box((0.2, 0.6, 1.2), (2 + dx, 2.0, cz + 2.0), METAL, "Metal")
    foods = [(240, 175, 70), (95, 170, 75), (250, 220, 90), (246, 242, 232), (200, 85, 60), (235, 185, 120)]
    for k, col in enumerate(foods):
        px = 2 - 10 + k * 4
        s.box((3.4, 0.3, 2.0), (px, 3.35, cz), (212, 214, 220), "Metal")
        s.box((3.0, 0.22, 1.6), (px, 3.45, cz), col)
    s.box((24, 0.15, 2.0), (2, 5.6, cz), (205, 232, 246), "Glass", transparency=0.5)
    for dx in (-11.8, 0, 11.8):
        s.box((0.15, 2.3, 0.15), (2 + dx, 4.4, cz - 0.6), METAL, "Metal")
    s.box((24, 3.2, 1.6), (2, 1.6, -D / 2 + 0.8), (205, 208, 215), "Metal")   # the kitchen counter behind
    s.box((24.2, 0.25, 1.8), (2, 3.3, -D / 2 + 0.8), (150, 155, 165), "Metal")
    # the menu, drawn in chalk pictures: a slice, an apple, a carton, a cookie
    s.box((13.0, 5.6, 0.25), (2, 9.6, -D / 2 + 0.4), (120, 80, 50), "Wood")
    s.box((12.2, 4.8, 0.3), (2, 9.6, -D / 2 + 0.45), (40, 72, 58))
    zf = -D / 2 + 0.65
    s.wedge((0.1, 1.8, 2.0), (-2.2, 9.7, zf), (245, 190, 80), rot=(0, 90, 0))
    s.ball(1.6, (0.9, 9.7, zf), (215, 50, 50))
    s.box((1.1, 1.8, 0.1), (3.6, 9.7, zf), (250, 250, 250))
    s.box((1.12, 0.5, 0.12), (3.6, 9.9, zf), (60, 120, 220))
    s.cyl(0.1, 0.85, (6.3, 9.7, zf), (190, 140, 80), axis="z")
    # vending machines on the +x wall
    for zc, col in ((-6.0, (205, 40, 50)), (-1.6, (40, 95, 205))):
        x = W / 2 - 1.7
        s.box((3.2, 8.0, 3.8), (x, 4.0, zc), col)
        s.box((0.1, 4.8, 2.6), (x - 1.95, 5.0, zc - 0.3), (200, 235, 255), "Glass", transparency=0.35)
        for row in range(4):
            for k in range(3):
                s.box((0.3, 0.6, 0.55), (x - 1.75, 3.2 + row * 1.15, zc - 1.2 + k * 0.85),
                      ((250, 200, 60), (90, 200, 90), (240, 120, 60), (230, 230, 240))[(row + k) % 4])
        s.box((0.12, 0.8, 2.6), (x - 1.66, 1.4, zc - 0.3), (25, 25, 30))
        s.box((0.12, 1.4, 0.5), (x - 1.66, 5.2, zc + 1.35), (60, 60, 66))
    for x, z in ((-22.5, 16.5), (22.5, 16.5), (-22.5, -12.5)):   # trash cans
        s.cyl(2.6, 1.1, (x, 1.3, z), (110, 118, 130))
        s.cyl(0.25, 1.2, (x, 2.72, z), (40, 40, 46))
    s.box((0.3, 5.0, 9.0), (-W / 2 + 0.35, 8.0, -6.0), (190, 150, 100), "Wood")   # a bulletin board
    for k, (dy, dz, col) in enumerate(((1.1, -2.6, (250, 230, 120)), (-0.8, -2.2, (140, 200, 250)),
                                      (0.9, 0.6, (250, 160, 190)), (-1.0, 1.4, (170, 230, 160)),
                                      (0.6, 3.2, (250, 250, 250)))):
        s.box((0.1, 1.6, 1.9), (-W / 2 + 0.55, 8.0 + dy, -6.0 + dz), col)
    clock(s, (W / 2 - 0.6, 11.5, 6.0), axis="x")
    for x in (-14, 0, 14):
        for z in (-8, 6):
            ceiling_light(s, (x, H - 0.4, z), length=9, axis="x")
    s.mark("centre", (0, 3, 4), (0, 3, -10))
    s.mark("line", (2, 3, -10.6), (2, 3, -20))
    s.mark("server", (2, 3, -17.6), (2, 3, 0))
    s.mark("seat_far", (-12, 3, -7.65), (-12, 3, 0))     # on table 1's far bench, facing the table: pose "sit"
    s.mark("seat_near", (-12, 3, -2.35), (-12, 3, -12))   # its near bench
    s.mark("seat2_far", (10, 3, -7.65), (10, 3, 0))
    s.mark("vending", (22.0, 3, -3.8), (26, 3, -3.8))
    s.mark("door", (-22, 3, 10.5), (0, 3, 10.5))
    s.cam("wide", (20, 11, 17), (-6, 3, -6), 60)
    s.cam("line", (9, 5.5, -6), (0, 4.5, -17), 55)
    s.cam("tables", (-12, 5, 4), (-12, 4, -10), 55)
    s.park = (0, 3, -110)
    return s


def boxes(s: Set, offset=(0.0, 0.0, 0.0)) -> list:
    """Every part's box as the world has it (rotation taken into the bounds): [(x0, x1, y0, y1, z0, z1), ...], signs
    included. For checking where a camera is."""
    from pose import angles
    out = []
    rows = [(r[1:4], r[4:7], r[7:10]) for r in s.parts] + [(g["size"], g["pos"], g["rot"]) for g in s.signs]
    for size, pos, rot in rows:
        m = angles(*rot)
        half = [abs(m[i][0]) * size[0] / 2 + abs(m[i][1]) * size[1] / 2 + abs(m[i][2]) * size[2] / 2 for i in range(3)]
        c = [pos[i] + offset[i] for i in range(3)]
        out.append((c[0] - half[0], c[0] + half[0], c[1] - half[1], c[1] + half[1], c[2] - half[2], c[2] + half[2]))
    return out


def _with_props(fn):
    def build(opt: dict) -> Set:
        st = fn(opt)
        props(st, opt.get("props"))
        if opt.get("signs") is False:   # no writing anywhere: posters, boards and scoreboards blank (M4's and M5's
            for g in st.signs:          # reviews: set text under the captions)
                g["text"] = ""
        return st
    build.__doc__ = fn.__doc__
    return build


SETS = {name: _with_props(fn) for name, fn in {
    "classroom": classroom, "hallway": hallway, "bedroom": bedroom, "living_room": living_room, "street": street,
    "gym": gym, "cafeteria": cafeteria, "stage_void": stage_void}.items()}
