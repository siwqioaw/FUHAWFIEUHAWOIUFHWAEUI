"""Master a mix (docs/AUDIO.md, "Mastering"): a high-pass for the rumble nobody hears, gain to the loudness target,
a true-peak limiter under a ceiling that leaves room for the AAC encode, then the intended silences muted again (the
high-pass and the limiter ring on for a few milliseconds after loud low end).

    python tools/edit/master.py MIX.wav OUT.wav [--lufs -14] [--ceiling -2.4] [--timeline cut.json]

The ceiling is -2.4 dBTP, not -1: AAC at 320 kb/s added 0.5 to 3 dB of true peak to sharp clicks in the project this
comes from, so a WAV limited to -1 came out over the limit in the MP4. Low-pass the sharpest transients (clicks, hard
kicks) above about 5 kHz as well, and measure the delivered file (tools/verify/qc.py): that number is the one that
counts.

`lufs` and `true_peak_db` follow ITU-R BS.1770 (tests/selftest.py checks them against ffmpeg's ebur128).
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import soundfile as sf
from scipy import ndimage
from scipy import signal as sps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cues import mute_silences  # noqa: E402


def _db(g):
    return 10 ** (np.asarray(g) / 20)


def _to_db(g, floor=1e-12):
    return 20 * np.log10(np.maximum(g, floor))


def k_weighting(sr: int) -> np.ndarray:
    """BS.1770's K-weighting (a high shelf, then a high-pass) as second-order sections, for any sample rate."""
    f0, g, q = 1681.974450955533, 3.999843853973347, 0.7071752369554196
    k = np.tan(np.pi * f0 / sr)
    vh = 10 ** (g / 20)
    vb = vh ** 0.4996667741545416
    a0 = 1 + k / q + k * k
    shelf = [(vh + vb * k / q + k * k) / a0, 2 * (k * k - vh) / a0, (vh - vb * k / q + k * k) / a0,
             1.0, 2 * (k * k - 1) / a0, (1 - k / q + k * k) / a0]
    f0, q = 38.13547087602444, 0.5003270373238773
    k = np.tan(np.pi * f0 / sr)
    a0 = 1 + k / q + k * k
    hp = [1.0, -2.0, 1.0, 1.0, 2 * (k * k - 1) / a0, (1 - k / q + k * k) / a0]
    return np.array([shelf, hp])


def lufs(x: np.ndarray, sr: int) -> float:
    """Integrated loudness: 400 ms blocks every 100 ms, gated at -70 LUFS and at 10 LU under the gated mean."""
    x = np.asarray(x, dtype=float)
    if x.ndim == 1:
        x = x[:, None]
    if not len(x):
        return -120.0
    power = (sps.sosfilt(k_weighting(sr), x, axis=0) ** 2).sum(axis=1)
    block, hop = int(0.4 * sr), int(0.1 * sr)
    if len(power) <= block:
        z = np.array([power.mean()])
    else:
        c = np.concatenate([[0.0], np.cumsum(power)])
        starts = np.arange(0, len(power) - block + 1, hop)
        z = (c[starts + block] - c[starts]) / block
    loud = -0.691 + 10 * np.log10(np.maximum(z, 1e-20))
    z = z[loud > -70]
    if not len(z):
        return -120.0
    rel = -0.691 + 10 * np.log10(z.mean()) - 10
    z2 = z[(-0.691 + 10 * np.log10(np.maximum(z, 1e-20))) > rel]
    return float(-0.691 + 10 * np.log10(z2.mean() if len(z2) else z.mean()))


def _peak_curve(x: np.ndarray) -> np.ndarray:
    """Per-sample peak including inter-sample overs (4x oversampled), linked across channels."""
    up = np.abs(sps.resample_poly(x, 4, 1, axis=0))
    if up.ndim == 2:
        up = up.max(axis=1)
    n = len(x)
    up = np.pad(up, (0, max(0, 4 * n - len(up))))[: 4 * n]
    return up.reshape(n, 4).max(axis=1)


def true_peak_db(x: np.ndarray) -> float:
    return float(_to_db(_peak_curve(x).max())) if len(x) else -120.0


def limiter(x: np.ndarray, sr: int, ceiling_db: float = -2.4, lookahead: float = 0.004,
            release: float = 0.08) -> np.ndarray:
    """A look-ahead true-peak limiter with linked channels: the gain each sample needs is held over the look-ahead and
    smoothed, so it is already down when the peak arrives; it recovers at 20 dB per `release` seconds."""
    need = np.minimum(1.0, _db(ceiling_db) / np.maximum(_peak_curve(x), 1e-12))
    if need.min() >= 1.0:
        return x
    look = max(1, int(lookahead * sr))
    held = ndimage.minimum_filter1d(need, size=2 * look + 1, mode="nearest")
    smooth = ndimage.uniform_filter1d(held, size=look + 1, mode="nearest")
    gdb = _to_db(np.minimum(smooth, need))
    rate = 20.0 / max(1, int(release * sr))
    idx = np.arange(len(gdb)) * rate
    g = _db(np.minimum.accumulate(gdb - idx) + idx)
    return x * (g[:, None] if x.ndim == 2 else g)


def master(x: np.ndarray, sr: int, target_lufs: float = -14.0, ceiling_db: float = -2.4, max_limit_db: float = 6.0,
           highpass_hz: float = 22.0, silences: list | None = None) -> np.ndarray:
    """If reaching the target would take more than `max_limit_db` of limiting, the gain backs off instead (the mix
    comes out quieter than the target, and transients keep their shape): fix that in the mix, not here."""
    y = sps.sosfilt(sps.butter(2, highpass_hz, "highpass", fs=sr, output="sos"), x, axis=0) if highpass_hz else x
    y = y * _db(target_lufs - lufs(y, sr))
    over = true_peak_db(y) - ceiling_db
    if over > max_limit_db:
        y = y * _db(-(over - max_limit_db))
    if true_peak_db(y) > ceiling_db:
        y = limiter(y, sr, ceiling_db - 0.05)
    return mute_silences(y, sr, silences or [])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mix")
    ap.add_argument("out")
    ap.add_argument("--lufs", type=float, default=-14.0)
    ap.add_argument("--ceiling", type=float, default=-2.4, help="true-peak ceiling of the WAV (dBTP)")
    ap.add_argument("--timeline", help="a timeline whose silences are muted again after the chain")
    args = ap.parse_args()
    x, sr = sf.read(args.mix, always_2d=True, dtype="float64")
    sil = json.load(open(args.timeline, encoding="utf-8")).get("silences", []) if args.timeline else []
    y = master(x, sr, args.lufs, args.ceiling, silences=sil)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    sf.write(args.out, y, sr, subtype="PCM_24")
    print(f"{args.out}: {lufs(y, sr):.1f} LUFS, true peak {true_peak_db(y):.1f} dBTP (in: {lufs(x, sr):.1f} LUFS)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
