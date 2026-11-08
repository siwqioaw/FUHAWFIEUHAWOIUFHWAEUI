"""The backlot: sets built in the playtest from code, so a set is the same every time and nothing is saved to the
place (docs/SETS.md).

    import sets
    sets.build("classroom")       # in a running playtest (server side), under workspace._Set
    sets.clear()                  # always, at the end of a session
    sets.marks("classroom")       # named spots: where actors stand, where cameras go

A set is a list of parts and props made by `kit.py`'s builders, plus a lighting preset and named marks. Everything
goes under one folder, `_Set`, which `clear` removes, so the place is left as it was (CLAUDE.md, Roblox Studio rules).
"""

from __future__ import annotations

import json

import studio

LIGHTING = {
    # ClockTime, Brightness, Ambient, OutdoorAmbient, ColorShift_Top, ExposureCompensation, fog, atmosphere density
    "day": dict(ClockTime=14.0, Brightness=2.2, Ambient=(120, 120, 128), OutdoorAmbient=(150, 150, 160),
                ExposureCompensation=0.1, EnvironmentDiffuseScale=0.6, EnvironmentSpecularScale=0.4,
                GlobalShadows=True, atmosphere=dict(Density=0.25, Offset=0.1, Haze=0.6, Glare=0.0,
                                                    Color=(199, 199, 199), Decay=(106, 112, 125))),
    "interior": dict(ClockTime=13.0, Brightness=1.2, Ambient=(96, 98, 108), OutdoorAmbient=(118, 120, 130),
                     ExposureCompensation=-0.25, EnvironmentDiffuseScale=0.7, EnvironmentSpecularScale=0.3,
                     GlobalShadows=True, atmosphere=dict(Density=0.1, Offset=0.0, Haze=0.0, Glare=0.0,
                                                         Color=(199, 199, 199), Decay=(106, 112, 125))),
    "golden": dict(ClockTime=17.6, Brightness=2.0, Ambient=(130, 110, 100), OutdoorAmbient=(170, 140, 120),
                   ExposureCompensation=0.15, EnvironmentDiffuseScale=0.6, EnvironmentSpecularScale=0.4,
                   GlobalShadows=True, atmosphere=dict(Density=0.3, Offset=0.15, Haze=1.2, Glare=0.4,
                                                       Color=(255, 214, 170), Decay=(170, 120, 90))),
    "night": dict(ClockTime=0.5, Brightness=1.0, Ambient=(95, 100, 125), OutdoorAmbient=(90, 95, 120),
                  ExposureCompensation=0.35, EnvironmentDiffuseScale=0.4, EnvironmentSpecularScale=0.3,
                  GlobalShadows=True, atmosphere=dict(Density=0.35, Offset=0.0, Haze=0.4, Glare=0.0,
                                                      Color=(60, 70, 100), Decay=(40, 45, 70))),
    "eerie": dict(ClockTime=19.2, Brightness=0.8, Ambient=(70, 80, 95), OutdoorAmbient=(60, 70, 90),
                  ExposureCompensation=0.1, EnvironmentDiffuseScale=0.3, EnvironmentSpecularScale=0.2,
                  GlobalShadows=True, atmosphere=dict(Density=0.45, Offset=0.2, Haze=2.0, Glare=0.0,
                                                      Color=(120, 135, 150), Decay=(60, 70, 85))),
}


def _c3(rgb) -> str:
    return f"Color3.fromRGB({int(rgb[0])}, {int(rgb[1])}, {int(rgb[2])})"


def lighting_luau(name: str) -> str:
    """Luau that sets the lighting preset, keeping what it found in attributes on the _Set folder to put back."""
    p = LIGHTING[name]
    atm = p["atmosphere"]
    props = {k: v for k, v in p.items() if k != "atmosphere"}
    lines = ["local L = game:GetService('Lighting')", "local saved = {}"]
    for k, v in props.items():
        lines.append(f"saved['{k}'] = L.{k}")
        val = _c3(v) if isinstance(v, tuple) else (str(v).lower() if isinstance(v, bool) else repr(v))
        lines.append(f"L.{k} = {val}")
    lines += [
        "for k, v in pairs(saved) do",
        "  if typeof(v) == 'Color3' then folder:SetAttribute('L_' .. k, string.format('%d,%d,%d', v.R*255+0.5, v.G*255+0.5, v.B*255+0.5))",
        "  else folder:SetAttribute('L_' .. k, v) end",
        "end",
        "local atm = L:FindFirstChildOfClass('Atmosphere')",
        "if atm then folder:SetAttribute('HadAtmosphere', true) atm.Parent = folder atm.Name = '_SavedAtmosphere' end",
        "local a = Instance.new('Atmosphere')",
        "a.Name = '_SetAtmosphere'",
        f"a.Density, a.Offset, a.Haze, a.Glare = {atm['Density']}, {atm['Offset']}, {atm['Haze']}, {atm['Glare']}",
        f"a.Color, a.Decay = {_c3(atm['Color'])}, {_c3(atm['Decay'])}",
        "a.Parent = L",
        "local cc = Instance.new('ColorCorrectionEffect')",
        "cc.Name = '_SetColor'",
        f"cc.Contrast, cc.Saturation, cc.Brightness = {p.get('contrast', 0.08)}, {p.get('saturation', 0.12)}, 0",
        "cc.Parent = L",
    ]
    return "\n".join(lines)


RESTORE = """
local L = game:GetService('Lighting')
local folder = workspace:FindFirstChild('_Set')
if folder then
  for k, v in pairs(folder:GetAttributes()) do
    if string.sub(k, 1, 2) == 'L_' then
      local prop = string.sub(k, 3)
      if typeof(v) == 'string' and string.find(v, ',') then
        local r, g, b = string.match(v, '(%d+),(%d+),(%d+)')
        pcall(function() L[prop] = Color3.fromRGB(tonumber(r), tonumber(g), tonumber(b)) end)
      else
        pcall(function() L[prop] = v end)
      end
    end
  end
  local mine = L:FindFirstChild('_SetAtmosphere')
  if mine then mine:Destroy() end
  local cc = L:FindFirstChild('_SetColor')
  if cc then cc:Destroy() end
  local saved = folder:FindFirstChild('_SavedAtmosphere')
  if saved then saved.Name = 'Atmosphere' saved.Parent = L end
  folder:Destroy()
end
local base = workspace:FindFirstChild('Baseplate')
if base and base:GetAttribute('_SetHidden') then base.Transparency = base:GetAttribute('_SetHidden') base.CanCollide = true base:SetAttribute('_SetHidden', nil) end
out('set cleared')
"""


def _registry() -> dict:
    import kit
    return kit.SETS


def _shift(m: dict, offset) -> dict:
    return {k: {kk: ([a + b for a, b in zip(vv, offset)] if kk in ("pos", "look") else vv) for kk, vv in v.items()}
            for k, v in m.items()}


def marks(name: str, options: dict | None = None, offset=(0.0, 0.0, 0.0)) -> dict:
    """The set's named spots: {name: {"pos": [x, y, z], "look": [x, y, z]}} for actors (y = 3: a standing actor's
    torso centre) and cameras."""
    if name == "baseplate":
        return _shift({"centre": {"pos": [0, 3, 0], "look": [0, 3, 10]}}, offset)
    return _shift(_registry()[name](options or {}).marks, offset)


def park_point(name: str) -> tuple:
    """Where the player's own character waits: out of every shot, near enough to keep the set streamed in."""
    if name == "baseplate":
        return (0, 3, -60)
    return tuple(_registry()[name]({}).park)


def build(name: str, options: dict | None = None, offset=(0.0, 0.0, 0.0), append: bool = False) -> str:
    """Build a set in the running playtest (server side). 'baseplate' builds nothing but the lighting. With an
    offset and `append`, another set beside the first, for a video that moves between places."""
    if name == "baseplate":
        body = "local folder = Instance.new('Folder') folder.Name = '_Set' folder.Parent = workspace\n" + \
            lighting_luau((options or {}).get("lighting", "day")) + "\nout('baseplate set')"
        return studio.server(body, wait=2)
    s = _registry()[name](options or {})
    return studio.server(s.luau(offset, append), wait=3, timeout=300)


def clear() -> str:
    return studio.server(RESTORE, wait=1)


def describe(name: str) -> str:
    """The set's marks as JSON, for a spec's author."""
    return json.dumps(marks(name), indent=1)
