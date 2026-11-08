# Building: new sets and props

Sets are code (`tools/roblox/kit.py`): built in the playtest every shoot, removed after, never saved into the place.
A new location is a new function in `kit.py` registered in `SETS`.

## A set in five steps

```python
def library(opt: dict) -> Set:
    s = Set("library", opt.get("lighting", "interior"))
    room(s, 40, 32, 14, wall=(236, 226, 206), trim=(120, 80, 50), floor=(150, 105, 70), floor_mat="WoodPlanks",
         gaps={"n": [(8, 18, 4.5, 11)]})                 # a wall opening: (from, to, bottom, top) along the wall
    window(s, (-7, 7.75, 16.5), 10.0, 6.5, axis="z")
    for x in (-14, -7, 7, 14):                           # shelves down both sides
        bookshelf(s, (x, 0, -14.6), w=6, seed=int(x))
    for x in (-8, 8):                                    # reading tables (sitting: kit.lunch_table's heights)
        table(s, (x, 0, 2), w=8, d=3.4, h=2.6, color=(170, 120, 80))
    for x in (-10, 0, 10):
        ceiling_light(s, (x, 13.6, 0), length=10, axis="x")   # brightness 0.6, range 20: the classroom's level
    s.mark("shelves", (0, 3, -11), (0, 3, -20))          # where an actor stands, and what they face
    s.cam("wide", (16, 9, 13), (-3, 4, -6), 60)           # a good establishing angle
    s.park = (0, 3, -90)                                  # where the player's own character waits, out of shot
    return s

SETS["library"] = library
```

The kit's own `gym` and `cafeteria` are fuller worked examples: a dressing option (`{"dance": True}`), furniture
sized for sitting, a menu drawn in pictures, optional trays.

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
   first sets' previews did). Keep practical lights near the classroom's: brightness 0.45-0.6, range 20-30 studs,
   and no light over the whole room (the gym's first preview, at 0.9 over 40 studs with one such light, was white).
5. **Marks and cameras,** then look at it: `python tests/studio_library.py sets library` shoots every camera to
   `build/library/sets/`. Look at each still at full size: walls closed, nothing floating or sunk, text facing out,
   no burned-out white.

## Rules

- `room()` records the room's inside; the plan then warns about a camera above its ceiling or behind a wall, and
  about any camera inside a part of any set. An exterior without `room()` gets the part check only.
- Furniture people sit on: the seat 1 stud up, a table's top 2.6 with its underside at least 2.0 (a seated R6's
  legs), as `lunch_table`: pose `sit` rests on it. Higher seats (the classroom's 1.7) make a sitting body rise.
- Anything an actor hides behind, sits at or uses in one scene, make a prop in `PROPS` (`lockers`, `tray`), so a
  video places it where its scene needs it, not where every scene sees it.
- Pictures before words on set dressing (the cafeteria's menu draws a slice, an apple, a carton): writing at head
  height sits under a story's captions. Every set takes `{"signs": False}`.

- Roblox-bright and saturated, like the references: school blues, red lockers, warm wood, marble floors.
- No Roblox logo, no copy of Roblox UI, no real brands on signs.
- Put one hidden detail in every set that matters to the video (a whiteboard joke, a poster, an odd extra).
- Free Toolbox models are allowed (the owner's decision) when a builder can't make the thing: check the model for
  scripts first, log it in `ATTRIBUTION.md`, and remove it after the shoot.
