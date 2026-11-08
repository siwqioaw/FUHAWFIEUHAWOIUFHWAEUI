# Sets: the backlot in code

`tools/roblox/kit.py` builds every location from code inside the playtest, and `sets.clear()` removes it after the
shoot: nothing is saved into the place (CLAUDE.md's Studio rules). `tools/roblox/sets.py` builds a set, its lighting
preset and any extra sets at offsets; `make.py` calls it for every shoot.

| Set | Size | What's in it | Lighting |
|---|---|---|---|
| `classroom` | 44 x 36 x 15 | 12 desks with chairs in 3 rows, the teacher's desk, a whiteboard (text by option), 3 windows, a door, posters, a clock, a bookshelf, a plant, 6 ceiling lights | interior |
| `hallway` | 18 x 80 x 15 | red lockers in banks on both sides (colour by option), 6 doors, a window at the end, a marble floor, blue trim, 6 ceiling lights, 2 posters | interior |
| `bedroom` | 28 x 24 x 13 | bed, desk with a computer, chair, rug, lamp, bookshelf, posters, window, door | interior |
| `living_room` | 40 x 30 x 14 | sofa, TV, coffee table, rug, lamp, plant, kitchen counter, fridge, 2 windows, front door | interior |
| `street` | 140 x 200 | road with lines, sidewalks, 8 houses with roofs, fences, trees, 4 streetlamps, a parked car; `{"night": True}` lights lamps and windows under a black sky | day / night |
| `stage_void` | 120 x 120 | one-colour floor and back wall (a cyclorama) | interior |

## Props

Any set takes props in its options, placed for the whole video: `{"props": [{"kind": "dog", "at": [x, 0, z],
"facing": [x, 0, z], "color": [r, g, b]}]}` (`kit.PROPS`). Made from parts like everything else:

| Prop | What | Options |
|---|---|---|
| `dog`, `cat` | blocky R6-scale pets: a dog standing (body, legs, paws, head, snout, bead eyes with catchlights, floppy ears, collar, tail), a cat sitting (pointed ears, green eyes, long tail); M5's narrator and the street's bragging pets | facing, color, spot, collar (dog), size |
| `balloons` | three party balloons on strings, tied to a weight | colors, height |
| `cake` | a two-tier birthday cake, candles lit | frosting, sponge, candles; `at` y is the table top |
| `smoothie` | a tall cup with a lid and a straw | color; `at` y is the surface |
| `ice_pack` | a soft blue ice pack | color; `at` y is the surface |
| `wall_phone` | an old wall phone with a handset and a coiled cord | facing; `at` is its centre on the wall |
| `plant`, `lamp`, `table`, `rug`, `car`, `tree`, `pine`, `bookshelf`, `sofa`, `tv` | the furniture builders | their own |

The pets are looked at in M5's stills. The party props, smoothie, ice pack and wall phone are checked by the selftest
(each builds) and previewed with `python tests/studio_library.py props`.

## Measured on the first previews (2026-11-08)

- Build time: 0.5-1 s for a set of 100-300 parts; the street and the classroom about 300 parts each.
- The first interior preset (Brightness 1.6, Ambient 140, exposure +0.2) burned white walls and ceilings to pure
  white. Now Brightness 1.2, Ambient 96-108, exposure -0.25, and a colour correction (+0.08 contrast, +0.12
  saturation) added with the set and removed with it: walls keep their tint and the colours are as saturated as the
  references'.
- A whiteboard's text sat behind its own frame and didn't show; signs now sit a tenth of a stud in front, facing the
  room.

Making a new set, the furniture builders, marks and camera marks: `skill/roblox-shorts/building.md`. Previews of
every camera: `python tests/studio_library.py sets [names]`.
