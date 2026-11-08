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

## Fonts and emoji

| Asset | Source | License | Used in |
|---|---|---|---|
| Montserrat, Regular to Black (`assets/fonts/montserrat/`) | github.com/JulietaUla/Montserrat, by The Montserrat Project Authors | SIL Open Font License 1.1 (`OFL.txt` beside it) | every caption, from S6 |
| 50 Noto 3D emoji at 128 px (`assets/emoji/noto/`) | github.com/googlefonts/noto-emoji (`3D/png/128`), by Google | the repository's README: images under the Apache License 2.0, fonts under the SIL OFL 1.1 (its LICENSE file beside them) | caption emoji, from S6 |

## Voices

Generated with ElevenLabs on the owner's paid plan, through the ElevenLabs connector; the output belongs to the owner
(ElevenLabs' Terms of Use, 4(c)(ii)). None is a clone of a real person. Ids are the voices' ElevenLabs ids.

| Voice | Source | License | Used in |
|---|---|---|---|
| Liam (TX3LPaxmHKxFdv7VOQHJ) | ElevenLabs premade voice | ElevenLabs Terms of Use, paid plan (commercial use) | narrator and storyteller, from S5 |
| Adam (pNInz6obpgDQGcFmaJgB) | ElevenLabs premade voice | ElevenLabs Terms of Use, paid plan (commercial use) | deep punch voice, from S5 |
| Yuria (vGfq3y2g8QTWjuUhrNYc) | ElevenLabs Voice Library | ElevenLabs Terms of Use and Voice Library Addendum, paid plan | girl, from S5 |
| Kathie (o9B86nZP8mMLaT5FBEzP) | ElevenLabs Voice Library | ElevenLabs Terms of Use and Voice Library Addendum, paid plan | second girl (cast, not yet used) |
| Lyra (ofWwoMxOYgLntvYlQLiB) | ElevenLabs Voice Library | ElevenLabs Terms of Use and Voice Library Addendum, paid plan | mom (cast, not yet used) |
| Auditioned, not cast: jimmy, James, Max, Ayla, Philip, Damyen | ElevenLabs Voice Library | as above | S5 auditions only (in `build/`, not published) |

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
