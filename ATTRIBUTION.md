# Attribution

Every third-party asset used in a video, or kept in this repository, gets an entry here: what it is, where it came
from, its license, and where it's used.

| Asset | Source | License | Used in |
|---|---|---|---|
| Pal Hair (hair, 63690008) | Roblox Marketplace, by Roblox | Roblox Marketplace avatar item, worn by an actor in Studio; Roblox's Terms of Use (decision 4 in `docs/ROBLOX_SHORTS_PLAN.md`) | S2-S3 test renders (in `build/`, not published); fits R6 |
| Straight Blonde Hair (hair, 376526888) | Roblox Marketplace, by Roblox | Roblox Marketplace avatar item, worn by an actor in Studio; Roblox's Terms of Use (decision 4 in `docs/ROBLOX_SHORTS_PLAN.md`) | S2-S3 test renders (in `build/`, not published); fits R6 |
| Short and Sleek - Black (hair, 9243992729) | Roblox Marketplace, by Roblox | Roblox Marketplace avatar item, worn by an actor in Studio; Roblox's Terms of Use (decision 4 in `docs/ROBLOX_SHORTS_PLAN.md`) | S2 test render (in `build/`, not published); doesn't fit R6 |
| Black Glasses (face accessory, 130858694386007) | Roblox Marketplace, by JTF Community (a group), free | Roblox Marketplace avatar item, worn by an actor in Studio; Roblox's Terms of Use (decision 4 in `docs/ROBLOX_SHORTS_PLAN.md`) | S2-S3 test renders (in `build/`, not published) |
| Guitar Tee with Black Jacket (shirt, 4047884046) | Roblox Marketplace, by Roblox | Roblox Marketplace avatar item, worn by an actor in Studio; Roblox's Terms of Use (decision 4 in `docs/ROBLOX_SHORTS_PLAN.md`) | S2-S3 test renders (in `build/`, not published) |
| Black Jeans with Sneakers (pants, 382538503) | Roblox Marketplace, by Roblox | Roblox Marketplace avatar item, worn by an actor in Studio; Roblox's Terms of Use (decision 4 in `docs/ROBLOX_SHORTS_PLAN.md`) | S2-S3 test renders (in `build/`, not published) |
| Pastel Starburst Top with Gray Jacket (shirt, 398634295) | Roblox Marketplace, by Roblox | Roblox Marketplace avatar item, worn by an actor in Studio; Roblox's Terms of Use (decision 4 in `docs/ROBLOX_SHORTS_PLAN.md`) | S2-S3 test renders (in `build/`, not published) |
| Roblox Studio's Baseplate template: its floor texture and sky | Roblox, built into Studio | Roblox content in Roblox Studio, under Roblox's Terms of Use | S1-S3 test renders (in `build/`, not published) |
| Beautiful You Jeans (pants, 398634487) | Roblox Marketplace, by Roblox | Roblox Marketplace avatar item, worn by an actor in Studio; Roblox's Terms of Use (decision 4 in `docs/ROBLOX_SHORTS_PLAN.md`) | S2-S3 test renders (in `build/`, not published) |

## Software the tools use

Installed separately, each under its own license; none of it is included here:

- Python packages: numpy, SciPy, OpenCV, Pillow, soundfile (`requirements.txt`);
- FFmpeg;
- Roblox Studio and its MCP server (`StudioMCP.exe`).

The harness's default animations (`tools/roblox/harness.luau`) are Roblox's own R15 animations, referenced by asset
id and not included.

## Standards the checks implement

- WCAG 2.3.1, "Three Flashes or Below Threshold": `tools/verify/qc.py`.
- ITU-R BS.1770, loudness and true peak: `tools/edit/master.py`.
