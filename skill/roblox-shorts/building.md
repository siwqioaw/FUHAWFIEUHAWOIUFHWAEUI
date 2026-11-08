# Building: new sets and props

Sets are code (`tools/roblox/kit.py`): built in the playtest every shoot, removed after, never saved into the place.
A new location is a new function in `kit.py` registered in `SETS`.

## A set in five steps

```python
def cafeteria(opt: dict) -> Set:
    s = Set("cafeteria", opt.get("lighting", "interior"))
    room(s, 50, 40, 15, wall=(230, 222, 200), trim=(200, 90, 60), floor=(200, 200, 205), floor_mat="CeramicTiles",
         gaps={"n": [(10, 20, 4.5, 11)]})               # a wall opening: (from, to, bottom, top) along the wall
    window(s, (-10, 7.75, 20.5), 10.0, 6.5, axis="z")
    for x in (-12, 0, 12):                               # long tables with benches
        table(s, (x, 0, -4), w=10, d=3.4, h=2.6, color=(170, 120, 80))
        s.box((10, 0.4, 1.2), (x, 1.6, -6.2), (90, 120, 200)); s.box((10, 0.4, 1.2), (x, 1.6, -1.8), (90, 120, 200))
    counter(s, (0, 0, -18), w=20)
    s.sign((8, 2, 0.2), (0, 11, -19.4), "LUNCH", face="Back", bg=(200, 90, 60), fg=(255, 255, 255))
    for x in (-12, 12):
        ceiling_light(s, (x, 14.6, 0), length=10, axis="x")
    s.mark("table_a", (-12, 3, -7.5), (-12, 3, 0))      # where an actor stands, and what they face
    s.cam("wide", (18, 9, 16), (-4, 4, -6), 60)           # a good establishing angle
    s.park = (0, 3, -90)                                  # where the player's own character waits, out of shot
    return s

SETS["cafeteria"] = cafeteria
```

1. **The shell:** `room(s, w, d, h, ...)` makes the floor (top at y 0), four walls with openings (`gaps`), a coloured
   trim and a ceiling. Exteriors skip it (`street`): grass, asphalt, sidewalks.
2. **The furniture:** the builders (`school_desk`, `teacher_desk`, `whiteboard`, `lockers`, `bookshelf`, `bed`,
   `sofa`, `tv`, `table`, `rug`, `lamp`, `counter`, `fridge`, `plant`, `clock`, `poster`, `door`, `window`,
   `ceiling_light`, `tree`, `pine`, `streetlamp`, `house`, `car`, `fence`) or raw parts: `s.box`, `s.cyl`, `s.ball`,
   `s.wedge`, with a colour and a material (`MATERIALS`).
3. **Text in the world:** `s.sign(size, pos, text, face=...)`: whiteboards, posters, notices, the hidden detail. The
   face is the side the text shows on: "Back" faces +z, "Front" -z, "Right" +x, "Left" -x.
4. **Light:** the set's preset (`sets.LIGHTING`: day, interior, golden, night, eerie) and `s.light` / `ceiling_light`
   for practical lights. Interiors at Ambient about 100 and exposure -0.25 keep white walls from burning out (the
   first sets' previews did).
5. **Marks and cameras,** then look at it: `python tests/studio_library.py sets cafeteria` shoots every camera to
   `build/library/sets/`. Look at each still at full size: walls closed, nothing floating or sunk, text facing out,
   no burned-out white.

## Rules

- Roblox-bright and saturated, like the references: school blues, red lockers, warm wood, marble floors.
- No Roblox logo, no copy of Roblox UI, no real brands on signs.
- Put one hidden detail in every set that matters to the video (a whiteboard joke, a poster, an odd extra).
- Free Toolbox models are allowed (the owner's decision) when a builder can't make the thing: check the model for
  scripts first, log it in `ATTRIBUTION.md`, and remove it after the shoot.
