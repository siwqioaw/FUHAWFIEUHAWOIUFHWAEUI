# The library: everything you can put in a shot

All of it is code in the repository; a video's `direct.py` names it.

## Sets (`tools/roblox/kit.py`; `building.md` to make more)

| Set | Lighting | Marks (where actors stand) | Cameras |
|---|---|---|---|
| `classroom` | interior | teacher, board, desk1a-desk3d, seat1a-seat3d, door, aisle | back_wide, front_wide, students |
| `hallway` | interior | centre, near, far, lockers_left, lockers_right | down_hall, up_hall, lockers |
| `bedroom` | interior | bed, desk_chair, centre, door | from_door, bed_side, desk |
| `living_room` | interior | sofa_left, sofa_right, kitchen, centre, front_door | tv_side, wide, kitchen |
| `street` | day; `{"night": True}` for night (lamps on, windows lit, black sky) | sidewalk_a, sidewalk_b, road, lawn, porch | street, along, houses |
| `stage_void` | interior | centre, left, right (a one-colour cyclorama, `{"color": [r, g, b]}`) | front |

- Options: the classroom's whiteboard text (`{"board": "..."}`), the hallway's locker colour (`{"lockers": [r, g,
  b]}`), the bedroom's walls, blanket and rug, the living room's sofa colour, the street's car colour.
- Coordinates: studs, y up, floors at y = 0; a standing actor's `at` has y = 3. The classroom is 44 x 36 (the board
  at z = -18, students face -z, desks at x -12, -3, 6, 15 and z -4, 3, 10; aisles at x -7.5, 1.5, 10.5). The hallway
  is 18 wide and 80 long along z (lockers at x = +-8.2; stand at x = +-6).
- Several places in one video: `Spec(..., extra_sets=[("new_school", "hallway", (400, 0, 0), {...})])`, then
  `shot(..., set="new_school")` with that set's own coordinates.

## Cast (`tools/roblox/cast.json`)

`narrator` (our recurring narrator: blue hair, black glasses, teal shirt), `me` (a story's hero), `popular_girl`,
`bestie`, `little_brother`, `mom`, `dad`, `teacher`, `rich_kid`, `jock`, `nerd`, `extra_a`, `extra_b`, `extra_c`. All
free Roblox catalog items checked on R6 (`assets.md` to add more). In a spec: `cast={"me": "narrator", ...}`.

## Faces (`tools/roblox/facekit.py`: 43, one line weight)

| Mood | Faces |
|---|---|
| everyday | smile, grin, laugh, blank, deadpan, bored, wink, tongue, proud, whistle, sleepy, oval |
| surprise, fear | shock, gasp, scared, nervous, wide_happy |
| anger | angry, yell, furious (with a vein), pout, grimace |
| sadness | sad, cry, sob, teary, sad_smile |
| attitude | smug, side_eye, side_eye_left, sus, scheming, evil, disgust, confused, cringe |
| big feelings | love, starstruck, money, cute, dizzy, dead, derp |

Comedy changes faces on the word; stories give each shot one face. `facekit.py sheet` draws them all.

## Poses (`tools/roblox/pose.py`)

idle, arms_out, hands_on_head, point, point_left, arms_crossed, hands_on_hips, laugh, facepalm, cheer, slump, think,
lean_in. Keys snap in 5 frames with a little overshoot and then drift; `walk={"from", "to", "start"}` walks
heel to toe at a steady speed.

## Camera (`tools/shots.py`)

`push` (the opener), `pull` (a reveal), `swoop` (speaker to listener, `streak=True` to blur it), `dutch_in` (panic),
`low` (power, a desk in the foreground), `top` (absurd, lonely), `ots` (an exchange, depth of field), `two_shot`,
`hold`, `wide` (from a fixed point). Faces stay above 70% of the frame, clear of the captions.

## Sound

- Effects from code (`tools/edit/sfx.py`): boom (the punch, 47 Hz), whoosh, pop, ding, error, shimmer, thud, riser,
  tick. More from the ElevenLabs connector's sound effects (`assets.md`).
- Voices (`tools/edit/voices.json`): narrator (Liam), girl (Yuria), girl_bratty (Kathie), deep (Adam), story (Liam at
  1.2x), mom (Lyra).
- Music beds: `build/library/music/` (made or downloaded per `assets.md`; never committed). Comedy: pizzicato and
  marimba about 104 BPM; stories: one bed per mood; music formats: an Audio Library track cut on its beat.

## Captions and on-screen text (`tools/edit/captions.py`)

`comedy`, `story`, `header`, `label`; emoji from `assets/emoji/noto/` (63 pictures). Overlays: an icon popping over
a point (`overlays=[("bell", "leo.head", "b:ding")]`): bell, heart, money, skull, fire, eyes, warning, or any emoji.
