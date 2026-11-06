# Attribution

Every third-party asset used in a video, or kept in this repository, gets an entry here: what it is, where it came
from, its license, and where it's used.

| Asset | Source | License | Used in |
|---|---|---|---|
| (none yet) | | | |

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
