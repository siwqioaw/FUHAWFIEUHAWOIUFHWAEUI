# Capturing footage from Roblox Studio

The trailer this kit comes from had no screen recording. Every frame was posed, then captured, one at a time, from a
Studio playtest, through Studio's built-in MCP server. That gives camera moves as exact as a 3D package's, slow
motion for free and no dropped frames, at about 1 s a frame.

What was verified, and where:

- **Verified in that project.** The bridge and the MCP calls, over many hours. A game-specific harness doing the same
  jobs as `harness.luau`, across three cuts.
- **Run in Studio on 2026-11-07** (spike S1, a scratch Baseplate place): `harness.luau` and `capture.py`, including
  the smoke test (no HUD, cursor or character) and portrait takes of 15 and 30 frames. See "Resolution".
- **Not yet run:** `stage.py`. Run `capture.py smoke` before every session anyway, and fix what it shows.

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
  set from it.
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

**A frame** is a JSON object written to the harness's `Frame` attribute. `capture.frame(state)` writes it, waits for
`Applied`, then waits 3 rendered frames.

| Key | Meaning |
|---|---|
| `cam` | 12 CFrame components, or `{"pos": [x,y,z], "look": [x,y,z], "roll": degrees}` |
| `fov` | vertical field of view, degrees |
| `dof` | `[focus, radius, near, far]` for depth of field |
| `hud`, `keepGuis`, `me` | show the game's GUIs; leave named ones showing; show the local character |
| `clock`, `ambient`, `lights` | Lighting.ClockTime; Lighting.Ambient; `[[path, on, brightness], ...]` held |
| `actors` | `[{"name", "cf", "anims": [[key, t, w]], "hidden"}]`: models posed, each animation held at t seconds |
| `moves`, `attrs` | `[[path, cf], ...]` pivoted; `[[path, name, value], ...]` attributes set for the game's code |
| `t` | the shot's time, left in the attribute `T` for your own code |

`capture.release()` puts it all back.

## A shot

A shot is a function of its time t that returns the frame's state. Everything in it is posed from t:

- the camera's path;
- each actor's place and animation times;
- the lights.

```python
def shot(t):
    return {"cam": {"pos": [0, 6, 18 - 1.5 * t], "look": [0, 4, 0]}, "fov": 55,
            "actors": [{"name": "kid", "cf": {"pos": [0, 3, 8 - 4 * t], "look": [0, 3, -10]},
                        "anims": [["walk", t, 1.0]]}]}
capture.take("build/shots/walk_in", shot, seconds=2.5, fps=30)
```

How `take` runs:

- **Warmup.** The first frame is applied, then the world gets 4 real seconds (animations and textures load, lights
  settle), and then it's applied again.
- **Frame timing.** Each frame is exactly 1/fps after the last, however long the capture took.
- **Motion blur.** `blur=3` captures 3 sub-frames per frame across the shutter.
- **Slow motion.** `speed=0.25` is quarter speed: t advances a quarter as fast, and everything posed from it slows
  with it.
- **Redoing frames.** `only=[...]` recaptures just those frames.
- **Walks.** Match a walk's playback rate to the distance covered, or the feet slide. A stiff walk was one of cut 1's
  rejections.

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
  - Fits R6: Straight Blonde Hair (376526888, 2016), 0.3 below the head centre as a long hair should; Black Glasses
    (130858694386007, a free community item), 0.6 in front of the face.
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
must be able to use. They don't drive R6 bodies: R6 posing is spike S3.

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
1280 x 841; **0.94 s a frame at 1914 x 960 with the portrait turn and crop**. So about 28 minutes of capture for a
minute of video at 30 fps, 56 at 60.

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
