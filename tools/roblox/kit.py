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


def rug(s: Set, pos, w, d, color=(200, 80, 90)):
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


SETS = {"classroom": classroom, "hallway": hallway, "bedroom": bedroom, "living_room": living_room,
        "street": street, "stage_void": stage_void}
