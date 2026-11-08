# Capturing footage from Roblox Studio

The trailer this kit comes from had no screen recording. Every frame was posed, then captured, one at a time, from a
Studio playtest, through Studio's built-in MCP server. That gives camera moves as exact as a 3D package's, slow
motion for free and no dropped frames, at about 1 s a frame.

What was verified, and where:

- **Verified in that project.** The bridge and the MCP calls, over many hours. A game-specific harness doing the same
  jobs as `harness.luau`, across three cuts.
- **Run in Studio on 2026-11-07** (spikes S1-S3, a scratch Baseplate place): `harness.luau` and `capture.py`,
  including the smoke test (no HUD, cursor or character) and portrait takes ("Resolution"); `stage.py` and
  `faces.py` ("Actors", "Faces"); `pose.py` ("Posing R6"). Run `capture.py smoke` before every session anyway, and
  fix what it shows.

## What you need

- **Studio,** open on the place, signed in, **on a screen of its own that nothing covers** (see "Studio's
  gotchas"), laid out for the most viewport (see "Resolution").
- **The bridge** (`tools/roblox/studio_mcp.py serve`), running in the background. It keeps one session with
  Studio's MCP server (`StudioMCP.exe`, which ships with Studio) open, so a call takes a fraction of a second instead
  of seconds.
  - It finds the server the way Roblox's own `mcp.bat` does: through the registry, then the newest
    `%LOCALAPPDATA%\Roblox\Versions\*\StudioMCP.exe`. `STUDIO_MCP_EXE` overrides it.
- **`STUDIO_PLACE`,** set to part of the place's name, if more than one Studio is open.

```
python tools/roblox/studio_mcp.py serve          # leave running
python tools/roblox/studio_mcp.py list           # the tools and their arguments
python tools/roblox/studio_mcp.py call execute_luau '{"code": "return game.Name"}'
```

## The MCP tools that matter

| Tool | Use |
|---|---|
| `list_roblox_studios` | The open Studios, `{"studios": [{"id", "name"}]}`. Every other call takes the `studio_id`. Ids change when Studio restarts. |
| `execute_luau` | Run Luau in a datamodel (`datamodel_type`: Edit, or during a playtest Server or Client) and get back what it returns. |
| `screen_capture` | The viewport as an image, at the viewport's size. In edit mode it can place the camera (`camera_position`, `look_at_position`). |
| `start_stop_play` | Start (`is_start: true`) or stop a playtest. |
| `get_studio_state` | Edit or play, and which datamodels exist. |
| `get_console_output` | The Output window. |
| `user_keyboard_input`, `user_mouse_input`, `character_navigation` | Drive a playtest's client as a player would. |

`tools/roblox/studio.py` wraps them: `luau`, `server`, `capture`, `play`, `wait_for`, `state`, `console`.

## Studio's gotchas

- **`execute_luau` on the Server has its own module cache.** `require` there gets fresh copies of the game's modules,
  not the running game's. To reach the game's live state, run the code in a Script (`studio.server`). Client code
  shares the game's modules.
- **Answers are cut at about 100 KB.** Summarise in Luau and return the summary.
- **Code that runs more than a few seconds without yielding** comes back "not reachable", though Studio finishes it.
  Run long work in `task.spawn`, leave its result somewhere, and poll for it.
- **`execute_luau` runs without plugin-level capabilities.** Some properties (`Lighting.Technology`, say) can't be
  set from it, or even read ("lacking capability RobloxScript").
- **The capture is the viewport.** `screen_capture` returns the viewport at its own size: 1280 x 841 in that
  project. If Studio's window is minimized the capture fails or comes back blank. See "Resolution".
- **Desktop screenshots of Studio can come back flat grey.** Use `screen_capture`, or PowerShell's `CopyFromScreen`
  for the whole window.
- **A playtest plays as the signed-in account, with the place's API access.** Anything the game saves (a profile,
  settings, currency) is saved for real. In that project the harness set two settings in memory; the game then saved
  its settings for another reason, and changed the owner's real profile. Capture must never change a game's settings
  or saves. If it must, replace the game's save function with one that saves nothing, in memory only.
- **Team Create saves every edit as you make it.** "Close without saving" keeps nothing out. Anything temporary you
  put in the place in edit mode, you must remove by hand. Playtest changes vanish when the test stops.
- **The PC's screensaver or lock** stops desktop control and screenshots. MCP keeps working.
- **A covered Studio draws nothing.** With Studio maximized behind other windows, `screen_capture` returned an empty
  grey viewport with only the view cube. Moved to a monitor of its own it rendered at once. Focus isn't needed, and a
  window partly covered (the taskbar along the bottom) still renders in full. (2026-11-07)
- **In edit mode, set the camera's Focus with its CFrame.** Studio's editor camera keeps aiming at its focus point: a
  CFrame set alone was re-aimed (the up vector read back tilted) and the capture came from elsewhere. Setting
  `Camera.Focus` to the target, then the CFrame, held.
- **Studio's edit-mode camera applies roll backwards:** a +90 degree roll read back as -90. The playtest's Scriptable
  camera does it exactly. Shoot in a playtest.
- **`screen_capture` leaves out BillboardGuis.** One showed in Studio's window but in no capture, in edit or play.
  SurfaceGuis, particles and shadows are captured. Billboards also stay upright on screen when the camera rolls, so
  they couldn't be used in portrait anyway: put text on a SurfaceGui or add it in the edit.
- **Don't start Studio from an automation tool to bring it forward.** One "open application" call launched a second
  Studio, and the bridge then listed two (one named "None"). Move Studio's window with the window API instead
  (`SetWindowPos` without activation), and close any extra instance.
- **The bridge's link to Studio can drop for a few seconds** ("WebSocket ... Connection reset" in
  `build/studio_mcp.log`); `list_roblox_studios` then returns nothing. Retry after a few seconds.
- **A new scene keeps changing for up to about 45 s, unless the quality level is fixed.** After two actors were staged
  and the camera put on the shot, a held frame changed by itself in steps 2 to 11 s apart: the floor's lighting and
  texture detail, a shadow appearing, then anti-aliasing coming on. The steps shrank (on average 3.8 grey levels, then
  1.3, 1.2, 0.7, 0.4, 0.2, 0.1 and 0.2), the last about 40 s in, and between them only small changes (under 8 grey
  levels, some captures identical). It was Studio's rendering Quality Level climbing: each playtest starts at the
  in-game graphics setting, Automatic here, whatever Studio Settings say, and Automatic can also drop while the PC is
  busy. Since the owner's decision of 2026-11-07, the harness's installer sets the highest level (Level 21) for the
  playtest and `capture.release()` puts back what it found. A held frame then stopped changing within 4 s and stayed
  still for the 71 s measured; `capture.settle` still checks, and ends at its 15 quiet seconds. The frames look the same
  as at the level Automatic reaches (0.05 grey levels apart, no pixel over 8). In the one take shot both ways each frame
  took about 13% longer (median 1.47 s against 1.30), but S4's six takes at Level 21 ran 0.94-1.25 s a frame: the cost
  depends on what's in view. (2026-11-07)

## The harness

`harness.luau`, run in the Client datamodel of a playtest (`capture.install()`), installs a LocalScript. It shows the
world a frame at a time.

**What it holds every frame.** It binds to RenderStep at the last priority, after the game's own camera code, and
holds:

- the camera: Scriptable, at the frame's CFrame and field of view;
- the HUD hidden:
  - the game's ScreenGuis and BillboardGuis moved out of PlayerGui (a game's own code often re-enables its screens
    every frame; moved out, they draw nothing);
  - the core GUI, the top bar, prompts, the chat and the cursor off;
- the local character hidden;
- the lights, ambient and time of day the frame asks for.

**Particles.** On the first frame it freezes every particle emitter and beam. A frame takes about a second, and live
particles would jump between frames.

**Quality.** The installer sets Studio's rendering Quality Level to the highest for the playtest, and
`capture.release()` puts back what it found ("Studio's gotchas").

**A frame** is a JSON object written to the harness's `Frame` attribute. `capture.frame(state)` writes it, waits for
`Applied`, then waits 3 rendered frames.

| Key | Meaning |
|---|---|
| `cam` | 12 CFrame components, or `{"pos": [x,y,z], "look": [x,y,z], "roll": degrees}` |
| `fov` | vertical field of view, degrees |
| `dof` | `[focus, radius, near, far]` for depth of field |
| `hud`, `keepGuis`, `me` | show the game's GUIs; leave named ones showing; show the local character |
| `clock`, `ambient`, `lights` | Lighting.ClockTime; Lighting.Ambient; `[[path, on, brightness], ...]` held |
| `actors` | `[{"name", "cf", "anims": [[key, t, w]], "face", "joints", "rootpos", "hidden"}]`: models pivoted to `cf`; each animation held at t seconds; `face` a texture for the head; `joints` and `rootpos` an R6 pose ("Posing R6") |
| `moves`, `attrs` | `[[path, cf], ...]` pivoted; `[[path, name, value], ...]` attributes set for the game's code |
| `t` | the shot's time, left in the attribute `T` for your own code |

`capture.release()` puts it all back.

## A shot

A shot is a function of its time t that returns the frame's state. Everything in it is posed from t:

- the camera's path;
- each actor's place and animation times;
- the lights.

```python
def shot(t):                                      # an R6 actor walks towards the camera ("Posing R6")
    z = -6 + pose.walk_travel(t)
    joints, rootpos = pose.walking(t)
    return {"cam": {"pos": [0, 6, 18 - 1.5 * t], "look": [0, 4, 0]}, "fov": 55,
            "actors": [{"name": "kid", "cf": {"pos": [0, 3, z], "look": [0, 3, z + 10]},
                        "joints": joints, "rootpos": rootpos}]}
capture.take("build/shots/walk_in", shot, seconds=2.5, fps=60)
```

An R15 actor (`"rig": "R15"` in `stage.py`) takes Roblox's own animations instead: `"anims": [["walk", t, 1.0]]`.

How `take` runs:

- **Warmup and settle.** The first frame is applied, the world gets 4 real seconds (animations load), the frame is
  applied again, and then it's captured about once a second until no pixel has changed by more than 8 grey levels
  for 15 seconds (`capture.settle`). For up to about 45 s after a scene is set up, Studio keeps refining it in steps
  2 to 11 s apart ("Studio's gotchas"). Between the steps the picture changes only a little, so two captures that
  nearly agree don't mean it's done (spike S3: the steps landed in a take's first 10 frames as pops).
- **Frame timing.** Each frame is exactly 1/fps after the last, however long the capture took.
- **Motion blur.** `blur=3` captures 3 sub-frames per frame across the shutter.
- **Slow motion.** `speed=0.25` is quarter speed: t advances a quarter as fast, and everything posed from it slows
  with it.
- **Redoing frames.** `only=[...]` recaptures just those frames.
- **Walks.** Match a walk to the distance covered, or the feet slide. A stiff walk was one of cut 1's rejections.
  An R6 walk from `pose.py` moves by `pose.walk_travel(t)` ("Posing R6"); an animation's playback rate has to
  match its speed.

**Anything the harness doesn't hold moves in real time between frames:** the game's own NPCs, tweens, physics, its
own animations. Hold it, drive it from the frame state (`moves`, `attrs`), or keep it out of shot.

## Actors

`stage.py` makes actors on the server (spike S2 ran it in Studio on 2026-11-07):

- **What they are.** Bodies from a HumanoidDescription, named `_Actor_<name>`: **R6** unless the spec says
  `"rig": "R15"`. Two took 2.8 s to make, dressed.
- **How they're set up.** Root anchored, Animate script removed, name and health bars off. The pivot is the
  HumanoidRootPart for every rig, so an actor's `cf` is its torso centre: for R6, **3 studs above its feet**. (An R6
  model made from a description has its Head as PrimaryPart: pivoted as it came, the head went where the root
  should, 1.5 studs low with the feet in the floor.)
- **What they wear.** Body colours; classic clothing by asset id (`shirt`, `pants`, `tshirt`); catalog accessories
  by asset id (`hair`, `hat`, `face_acc`, `neck`, `shoulder`, `front`, `back`, `waist`). On R6 every accessory is
  loaded with InsertService and attached with `Humanoid:AddAccessory`, because a description silently drops newer
  accessories on R6. The report lists each accessory's offset from the head and marks **MISFIT** any more than
  1.2 studs below it.
  - Fits R6: Straight Blonde Hair (376526888, 2016), 0.3 below the head centre as a long hair should; Pal Hair
    (63690008), 0.2 above it; Black Glasses (130858694386007, a free community item), 0.6 in front of the face.
  - Doesn't: Short and Sleek - Black (9243992729, 2022), 2.0 below the head, hidden in the torso. It fits R15.
  - Find items from edit mode with `AvatarEditorService:SearchCatalog` (free Roblox-made hair, shirts and pants come
    up first with `MaxPrice = 0`). Skip anything with the Roblox logo or another brand on it. Log every item a video
    uses in `ATTRIBUTION.md`.
- **Nobody's avatar.** By default, plain bodies dressed from the catalog. `user_id` loads a real person's avatar,
  only with that person's permission. In the trailer project the owner wanted their friends in it, and the friends had
  agreed.

`stage.park(pos)` anchors the player's own character out of shot. Choose a spot near the shot: with streaming on, the
client only has the parts near its character.

The harness knows Roblox's own R15 animations by name: `walk` (913402848), `run` (913376220), `idle` (507766388),
`toolnone`, `wave`, `laugh`, `point` and `cheer`. Any other animation is `"rbxassetid://N"`, which the place's owner
must be able to use. They don't drive R6 bodies: pose those with `pose.py` ("Posing R6").

## Faces

An R6 head wears its face as a Decal named `face`. Each actor in a frame can carry `"face": <texture>`, and the
harness sets the decal when it changes, so a face changes on exactly the frame the edit wants (spike S2: four
swaps across two frames, all landed).

**No upload needed for capture.** Studio reads `rbxasset://` textures from its own content folder, in edit mode and
in playtests. `tools/roblox/faces.py` installs PNGs there (`faces.install(folder)`, then `faces.url(name)`), so drawn
faces render in captures without ever going to Roblox. What to know:

- **Find the folder from the running Studio,** not the registry: on 2026-11-07 the registry's ContentFolder still
  named the version before an update, and faces installed there never showed. `faces.content_dir()` asks Windows for
  the running RobloxStudioBeta.exe.
- **A Studio update starts a new version folder** without our faces: run `faces.install()` at the start of every
  session (or the face renders blank).
- **Preload before a take:** `capture.preload([urls])` on the client (3 faces in 0.03-0.08 s), so a swap never shows a
  frame of blank texture.
- **The image:** square, transparent background, black line art; features in the middle, as in Roblox's default face
  (`content/textures/face.png`: 128 x 128, features within x 42-88, y 27-101). At 512 x 512 a face stays crisp in a
  close-up that fills the frame with the head. `faces.py test` draws a three-face test set (smile, shock, angry).

## Posing R6

`tools/roblox/pose.py` works out each frame's R6 joints in Python, and the harness applies them (spike S3, run in
Studio on 2026-11-07). Nothing is uploaded, a take is exact, and any frame can be redone. `tests/studio_pose.py` is
the spike itself: the check against Roblox, the takes and their measurements.

```python
import faces, pose
keys = [(0.0, "idle"), (0.35, "arms_out"), (0.85, "hands_on_head"), (1.35, "laugh", 2 / 60)]
def shot(t):
    joints, rootpos = pose.at(keys, t)
    return {"cam": {"pos": [0, 3.6, 12], "look": [0, 3, 0]}, "fov": 55,
            "actors": [{"name": "kid", "cf": {"pos": [0, 3, 0], "look": [0, 3, 10]}, "face": faces.url("shock"),
                        "joints": joints, "rootpos": rootpos}]}
```

- **Poses are data.** `pose.POSES` has 13: idle, arms_out, hands_on_head, point, point_left, arms_crossed,
  hands_on_hips, laugh, facepalm, cheer, slump, think, lean_in. Each names only the joints it moves, as angles in
  degrees (the signs are in `pose.py`'s docstring). A key can also give a dict.
  - **Angle order:** every joint turns by z, then x, then y about its parent's axes, so y aims: an arm held forward
    swings towards the character's left with y > 0. The root's angles lean, turn and roll the whole body.
  - **Pointing:** `point` is straight ahead, so an actor facing the camera points into the lens. For a point across
    the frame, turn the actor.
  - **Width:** `arms_out` is about 5.6 studs from hand to hand. A 9:16 frame 12 studs away at 55 degrees is 7 studs
    wide.
  - **Hands at the head:** `pose.clearance` measures how far an arm goes into the head (or its lower half into the
    torso). A straight R6 arm can't put its hand on the face without its forearm cutting into the head, so
    `facepalm` and `think` hold the hand just before the face and chin, and `hands_on_head` puts the hands beside
    the top of the head. The first `hands_on_head` sank them 0.34 studs into it, and the hair drew over them.
  - **Between poses:** a snap can clip where neither pose does. `pose.snap_clearance(a, b)` measures every frame of
    one. 50 of the 156 snaps between the 13 poses go more than 0.05 studs in on some frame, the worst into and out
    of `arms_crossed` (0.23-0.28 into the chest: the arms swing inward before they swing forward). Where it shows,
    key a pose in between (arms forward first). The take's snaps stay within 0.09, its overshoot grazing the top of
    the head under the hair.
- **Snaps.** Each key snaps from wherever the body was to its pose in 5 frames at 60 fps, or in the key's third
  value, in seconds (2/60 for a hard hit).
  - **The ease:** each angle moves straight from its value to the next, so a path follows the numbers: an arm going
    from x = -10 to 176 rises through the front, never round the back. A raise seen from the front passes the lens
    on its first frame, as a real one does; for another path, key a pose in between.
  - **The overshoot:** a joint goes two thirds of the way on the first frame, about 7% past the pose on the third,
    and settles on the fifth. A joint with a long way to go eases more gently, so that it goes at most 6 degrees
    past (`pose.CAP`).
  - **Against the references:** they snap in about 5 frames, their hardest hits in 1-2, and don't all ease out the
    same way (`refs/r6rants/SYNTHESIS.md`, "Animation"). Every joint moves at once here; in 001 the head leads and
    the hands land last, which the pose library should add.
- **Faces.** The takes change a face on the first frame the body moves, a frame after its key.
- **Drift.** `pose.at` adds slow swings under 2 degrees (head, body, arms) so a held pose stays alive.
  `drift_amount=0` for none; a different `seed` per actor keeps two actors out of step.
- **Planted.** The R6 root joint is at the torso's centre, a stud above the hips: a lean there swings the legs, and
  `laugh` would move the feet 0.63 studs. `pose.at` leans and turns the body about the hips and keeps each leg as
  posed (`pose.plant`).
  - **Leans:** the soles stay where they were, drift and all.
  - **Turns:** the feet turn with the body about the hips' centre, so each slides about 0.2 studs (0.48 at its
    corners) over a 25 degree turn. For a big turn, step instead.
  - **Rolls:** a roll tilts the hips, which would push one foot into the floor, so the body rises until no sole is
    under the floor and the other foot lifts (0.28 studs for 8 degrees).
- **Walks.** `pose.walking(t)` walks at 1.5 cycles a second: 3 steps, or 180 a minute.
  - **Legs:** they reach 30 degrees each way, or 31 as each foot reaches past its stride and comes back onto it. The
    arms swing against them.
  - **Feet:** an R6 leg is a straight block hinged at the top, so a planted foot rolls over its heel while the leg is
    ahead and over its toe once it's behind. Each foot moves with the floor for 60% of the cycle (its stance; under
    half is refused). It comes down from about 0.07 studs up over the first 2 frames of that, as the body settles
    onto it, and both feet are down for a
    moment at each change of step. `pose.walk_steps` gives the frames a foot lands on, for footsteps (frames 2, 22,
    42... at 60 fps).
  - **Height:** the body sits as high as the feet in their stance put it. That is highest while a foot balances on
    an edge (0.06 studs up) and lowest as a sole lies flat, so it bobs twice a step. That's the opposite of a
    person's walk, which rides highest as the legs pass, but with straight block legs any other height would sink
    a planted foot or lift it.
  - **Moving it:** move the actor by `pose.walk_travel(t)`, a steady 5.33 studs a second (`pose.walk_speed()`), and
    track it with the camera at the same speed. The planted feet stay still and the walker stays put in frame.
  - **The passing foot:** with no knees, it skims the floor, up to 0.025 studs into it.
- **Checks.**
  - `pose.soles(joints, rootpos)` gives each sole's corners as the harness poses them.
  - `pose.walk_check()` gives a walk's planted feet's worst slip, sink and lift, all about 0, and the passing foot's
    scrape, 0.025.
  - `pose.clearance(joints)` gives how far an arm goes into the head (an upright cylinder 1.2 studs across, about
    its rounded mesh) or its lower half into the torso. At rest every pose stays within 0.1 studs: `think`'s hand
    touches the chin at 0.095. `pose.snap_clearance(a, b)` gives the worst over a snap's frames.
  - `python tests/studio_pose.py check` poses an actor in a playtest and compares every sole corner with Roblox's.
    All were within 0.00001 studs: five walk frames, two leans, a turned lean, a roll, a drifting idle and a
    `rootpos` alone.
  - `tests/selftest.py` checks all of these against planted failures: a lean that isn't planted; a walk 10% too
    fast, at standing height, or not planted; a swing that jumps speed; an overshoot that stalls; an arm through the
    head or chest, at rest or between poses.
- **How the harness poses.**
  - **Each joint:** it sets the Motor6D's C0 to its resting position (plus `rootpos`, for the root), then the frame's
    angles, then its resting rotation, and sets it again every rendered frame.
  - **Held poses:** a pose holds until a frame sets it again. A frame that leaves an actor's joints out, or names
    only some, leaves the rest as they were (`pose.py` gives all six). `rootpos` without a root, or without joints,
    moves the body with the root at rest. A joint that errors part-way through a frame leaves the joints before it
    posed until the next frame or release.
  - **Release:** it puts the joints back, and refuses any frame after.
  - **Other animation:** `stage.py` removes the Animate script, so nothing else moves its actors' joints. On a game's
    own animated model the pose would add to whatever its Animator plays.

**Spike S3** (2026-11-07), in portrait at 60 fps, 1.3-1.4 s a frame with two posed actors (median 1.34, slowest 1.6):

- **Acting**, 2.4 s: five keys and four face swaps. Every snap moved for 5 frames, then only the drift moved. The
  mean difference between frames, at 180 px wide, in grey levels:
  - arms_out 5.5, 3.8, 1.3, 0.6, 0.6;
  - hands_on_head 5.8, 6.2, 2.9, 0.4, 0.9;
  - laugh 8.1, 4.9, 2.3, 0.3, 0.7;
  - point 5.2, 3.9, 1.4, 0.7, 0.7;
  - between snaps, never more than 0.16, the first frames included.

  The hands stay clear of the face, and the hair no longer draws over them.
- **Walk**, 1.5 s, side on with the camera tracking: the walker stays put in frame. Her hair's back edge doesn't
  move, its front edge moves at most 2 px between frames, and its top bobs within 12 px (at 1080 wide). The first
  walk, which followed the planted foot's speed, lurched back about 23 px at every step (measured in review).
- **Feet**, 1.0 s, the camera at ankle height: the soles roll from heel to toe and the planted ones stay on the floor.
  The camera can't show the passing foot's 0.025 studs under the floor, which the floor hides. The first walk sank
  the edge of each sole 0.25 studs into the floor at full stride: it kept only the sole's centre on the floor.

The acting take began after a 61 s settle; the walk and feet takes, shot after it, settled in 16 s. Shot after a
3 s warmup, the first acting take changed by 2.0-2.5 grey levels at frames 5, 7 and 9: the scene still settling.

## Camera

`tools/roblox/camera.py` builds a shot's camera from views and moves (spike S4, run in Studio on 2026-11-07).
`tests/studio_camera.py` is the spike itself: seven takes and their measurements.

```python
import camera
mcu = camera.aim((0, 4.5, 0), toward=(0, 0, 1), distance=5.5, fov=45)   # a medium close-up on a head
path = camera.moves([(0.0, camera.back(mcu, 4)), (0.1, mcu, 0.25)])     # push in from 4 studs back
def shot(t):
    return dict(camera.state(camera.hold(path(t), t)), actors=[...])
```

- **Views** are dicts the harness takes: pos, look, roll, fov (of the finished 9:16 frame), dof, and an up vector
  for a camera looking straight up or down.
  - `aim` frames a point from a direction and a distance; `back` moves along the line of sight, keeping the focus on
    the subject; `orbit` swings round what the camera looks at.
  - `dutch` sets the roll: + tilts the picture clockwise (14.3 degrees measured for 14).
  - `low` puts the camera at desk height, looking up; `top` straight above, the frame's top towards a direction.
  - `ots` puts it behind and beside a near actor's shoulder, looking at the far actor's face (or `lift` studs below
    it, to raise the face clear of the captions), with depth of field that keeps the face sharp.
  - `project` says where a point lands in the frame: check that faces sit above about 70% of the frame's height,
    where captions go.
- **Moves** (`camera.moves`) take keys as poses do: each moves from wherever the camera was over its seconds (0
  cuts) with an ease, the camera swinging round its aim, so a move between two orbit views goes round the circle.
  - "out": fastest first, about a fifth of the way on the first of 12 frames: 007's pull-back shrinks the face to
    two thirds on its first step, ours to 0.61.
  - "inout": speeding up and slowing down, as 002's swoop into a dutch angle and 007's whip-pan.
  - "in": speeding up all the way, to cut on the move. "linear": steady, as 006's pull-backs, which run and stop.
  - A move cut short by the next carries on from where it was, but not at its speed: the camera pauses unless the
    next move is "out".
- **Holds** drift slightly (`camera.hold`) across the frame: about 0.02 studs for every 5 studs back, the aim a
  little more, the roll a tenth of a degree. Give each shot its own seed.
- **Swoops:** the references' are mostly sharp (001 with speed lines, 004); 003's time-jump swoop is blurred. To
  blur one, capture it a frame at a time and streak it in the edit: `fx.streak(frame, camera.smear(path, t))`, as
  wide as the picture slides sideways while a 180 degree shutter is open, with a tapered weight in linear light.
  - Three sub-frames a frame (`capture.take(blur=3)`) showed three separate copies of each face, at three times the
    capture; `fx.whip`'s flat weight doubled the pupils at its ends.
  - `smear` is sideways only and gives 0 at a cut. A move that keeps its aim (an orbit) gives 0 too: the subject
    stays put, though the background slides.
- **Portrait framing:** a 9:16 frame is narrow, about 2.3 studs wide 5 studs away at 45 degrees. Over the shoulder,
  the near head sits cut by the frame's edge: 1.3 studs to the side, 2.8 behind and 0.6 up, at 50 degrees.

**Spike S4** (2026-11-07): seven takes at 60 fps in portrait, at Quality Level 21, 0.88-1.81 s a frame (each take's
median; top-down, full of floor, the slowest). What each move did:

| Take | Measured | Against the references |
|---|---|---|
| Push-in, 0.25 s, "out" | fastest on its first frames, settled after 15 | openings move in 0.2-0.3 s (006) |
| Pull-back from an extreme close-up, 0.2 s, "out" | the face's size frame to frame: 0.61, 0.76, 0.83, 0.88, 0.92 ... 1.00 | 007 at 3.73: about 0.66 on the first step (tracked in review) |
| Swoop, speaker to listener, 0.15 s, "inout", streaked | a smear of up to 169 px; one streak per eye | 001's and 004's are sharp; 003's is blurred |
| Swoop that rolls to a dutch angle, 0.35 s, "inout" | the floor's edge at -14.3 degrees at the end | 002 at 0.2: speeds up and slows down over about 0.4 s |
| Low angle from just above the desk | the camera 2.5 up, looking up 12.4 degrees; the desk's front edge 83% down | 004 keeps the desk large in the foreground (seen in review) |
| Over the shoulder | depth of field: the near head 94% softer, the near shoulder 91%, the far face 1% | 003 shoots every exchange this way |
| Top-down | framed by its up vector | 005 and 009 use top-down shots |

- **Faces clear of the captions:** every take ends with the kid's face 30-63% down the frame; in the extreme close-up
  the eyes sit 23% down and the mouth 47%.
- **What the difference between frames can't do:** it rises and falls with what's in view as much as with the camera
  (the swoop's dip is the empty gap between the actors passing), and it can't separate the camera from the actors'
  animation. Track a feature instead: a face's size, the floor's tiles.

## Resolution

The capture is the viewport, at whatever size Studio's viewport is. A vertical short needs 1080 x 1920, and the
monitors here are 1920 x 1080. Cropping 9:16 straight out of a landscape viewport leaves under half the width.

**What works (spike S1, measured on 2026-11-07): roll the camera 90 degrees.** `capture.take(..., portrait=True)` and
`capture.py smoke --portrait`:

1. each frame's camera is rolled +90 degrees (the harness applies `CFrame.Angles(0, 0, roll)`), and its field of view
   set so the finished 9:16 frame has the vertical field of view the shot asked for (`capture.portrait_fov`);
2. the capture is turned 90 degrees anticlockwise and cropped to 9:16 about its centre (`capture.upright`), saved at
   its own pixels: the edit scales it to 1080 x 1920 once, with `look.reframe`.

The frame's width comes from the viewport's **height**, and its height from the viewport's **width**, so the layout
matters:

| Studio's layout on a 1920 x 1080 monitor | Viewport | Portrait frame | To 1080 wide |
|---|---|---|---|
| Default panels and ribbon, edit mode | 928 x 841 | 522 x 928 | 2.07x |
| Default panels and ribbon, in a playtest | 1280 x 841 | 720 x 1280 | 1.50x |
| Side panels closed | 1914 x 841 | 841 x 1495 | 1.28x |
| ... and the ribbon collapsed (double-click the Home tab) | 1914 x 900 | 900 x 1600 | 1.20x |
| ... and View > Full Screen (F11) | 1914 x 923 | 923 x 1641 | 1.17x |
| ... and Window > Script > Command Bar off | **1914 x 960** | **960 x 1707** | **1.125x** |

At the last layout the frames are sharp at delivery size: on a test chart, SurfaceGui text of 20 px read cleanly
after the 1.125x scale, and an R6 dummy's face and the baseplate's studs stayed crisp. The capture-layout checklist, in that order: Studio maximized
on a monitor of its own; Explorer, Properties, Toolbox and Output closed (Window menu brings them back); ribbon
collapsed; Full Screen on; Command Bar off. `take` prints the frame size it will get, and warns when it's short of
1080 wide.

**Speed, measured:** 0.47 s a capture in edit mode at 928 x 841; 0.52 s a frame applied and captured in a playtest at
1280 x 841; **0.94 s a frame at 1914 x 960 with the portrait turn and crop**, on an empty baseplate. So about 28 minutes
of capture for a minute of video at 30 fps, 56 at 60. With two posed, dressed actors on set (S3): about 1.3 s a frame at
the Automatic quality level (median 1.27-1.37 over five takes, slowest 1.8). At the highest level the harness now sets:
1.47 s for a take full of floor and feet, 0.94-1.25 s for S4's six (each take's median): so 30-45 minutes for a minute
at 30 fps, 60-90 at 60. Heavy work on the same PC slows it: frames took 4-6 s while a video decode ran.

**Not needed, but possible, for true 1080 x 1920:** capture each frame as two tiles (the camera turned up and down
about the same point, so no parallax) and stitch them with a homography. It doubles the capture time.
Untested alternatives: a portrait monitor (about 1080 x 1750 of viewport without a roll), and Studio's device emulator.

## Smoke test, before every capture session

```
python tools/roblox/capture.py smoke build/capture
```

It installs the harness, freezes the particles and captures the current view. Look at `build/capture/smoke.png`. It
must show:

- no HUD, no cursor and no character;
- nothing at the edges.

Then call `capture.release()`, or stop the playtest.
