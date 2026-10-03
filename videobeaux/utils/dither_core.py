"""Pure-numpy ordered / noise dithering (no ffmpeg, no OpenCV — unit-testable)."""
from __future__ import annotations

from functools import lru_cache

import numpy as np

METHODS = ["bayer2", "bayer4", "bayer8", "bayer16", "clustered", "blue_noise", "ign", "white_noise"]


@lru_cache(maxsize=None)
def bayer_matrix(n: int) -> np.ndarray:
    """n x n Bayer matrix (n a power of two) holding each rank 0..n*n-1 exactly once."""
    if n == 1:
        return np.zeros((1, 1), dtype=np.int64)
    m = bayer_matrix(n // 2)
    return np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])


@lru_cache(maxsize=None)
def clustered_dot_matrix(n: int = 8) -> np.ndarray:
    """Round clustered-dot (halftone-style) threshold matrix, ranks 0..n*n-1."""
    c = (n - 1) / 2.0
    ys, xs = np.mgrid[0:n, 0:n]
    d = np.hypot(xs - c, ys - c)
    ang = np.arctan2(ys - c, xs - c)
    order = np.lexsort((ang.ravel(), d.ravel()))  # nearest the center first, angle breaks ties
    ranks = np.empty(n * n, dtype=np.int64)
    ranks[order] = np.arange(n * n)
    return ranks.reshape(n, n)


@lru_cache(maxsize=None)
def blue_noise_tile(n: int = 64, seed: int = 7) -> np.ndarray:
    """
    Approximate blue noise: white noise high-passed in the frequency domain,
    then rank-transformed so every threshold value appears exactly once.
    Instant to build, no precomputed asset.
    """
    rng = np.random.default_rng(seed)
    white = rng.random((n, n))
    f = np.fft.fft2(white)
    fy = np.fft.fftfreq(n)[:, None]
    fx = np.fft.fftfreq(n)[None, :]
    radius = np.hypot(fx, fy)
    f *= radius / (radius.max() + 1e-9)       # attenuate low frequencies
    noise = np.fft.ifft2(f).real
    order = np.argsort(noise.ravel(), kind="stable")
    ranks = np.empty(n * n, dtype=np.int64)
    ranks[order] = np.arange(n * n)
    return ranks.reshape(n, n)


def threshold_map(method: str, h: int, w: int, frame_index: int = 0, animate: bool = False) -> np.ndarray:
    """(h, w) float32 thresholds in [0, 1)."""
    if method.startswith("bayer"):
        t = bayer_matrix(int(method[5:]))
    elif method == "clustered":
        t = clustered_dot_matrix(8)
    elif method == "blue_noise":
        t = blue_noise_tile(64)
    elif method == "ign":
        # interleaved gradient noise (Jimenez) — cheap, blue-noise-like
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        if animate:
            xs = xs + 5.588238 * frame_index
        return np.mod(52.9829189 * np.mod(0.06711056 * xs + 0.00583715 * ys, 1.0), 1.0).astype(np.float32)
    elif method == "white_noise":
        rng = np.random.default_rng(frame_index if animate else 0)
        return rng.random((h, w), dtype=np.float32)
    else:
        raise ValueError(f"Unknown dither method '{method}'. Choices: {', '.join(METHODS)}")

    n = t.shape[0]
    norm = (t.astype(np.float32) + 0.5) / (n * n)
    if animate:
        norm = np.roll(norm, (frame_index * 3 % n, frame_index * 5 % t.shape[1]), axis=(0, 1))
    reps = (h // n + 1, w // t.shape[1] + 1)
    return np.tile(norm, reps)[:h, :w]


def palette_spread(palette: np.ndarray) -> float:
    """Typical gap between palette colors, as a fraction of one full-range channel."""
    p = palette.astype(np.float32)
    d = np.sqrt(((p[:, None, :] - p[None, :, :]) ** 2).sum(-1))
    np.fill_diagonal(d, np.inf)
    return float(d.min(axis=1).mean() / (255.0 * np.sqrt(3.0)))


_LUT_CACHE: dict[bytes, np.ndarray] = {}


def _palette_lut(palette: np.ndarray) -> np.ndarray:
    """32x32x32 lookup (5 bits per channel) -> nearest palette index. Built once per palette."""
    key = palette.tobytes()
    lut = _LUT_CACHE.get(key)
    if lut is None:
        g = (np.arange(32, dtype=np.float32) * 8.0 + 4.0)
        grid = np.stack(np.meshgrid(g, g, g, indexing="ij"), axis=-1).reshape(-1, 3)   # r,g,b order
        d = ((grid[:, None, :] - palette.astype(np.float32)[None, :, :]) ** 2).sum(-1)
        lut = d.argmin(-1).astype(np.uint8)
        _LUT_CACHE[key] = lut
    return lut


def quantize_to_palette(x: np.ndarray, palette: np.ndarray) -> np.ndarray:
    """Nearest palette color per pixel; x is (H, W, 3) values 0..255 (float or uint8)."""
    q = np.clip(x, 0, 255).astype(np.uint8) >> 3
    idx = (q[..., 0].astype(np.int32) << 10) | (q[..., 1].astype(np.int32) << 5) | q[..., 2]
    return palette[_palette_lut(palette)[idx]]


def dither_frame(
    frame: np.ndarray,
    *,
    method: str,
    palette: np.ndarray | None = None,
    levels: int = 2,
    strength: float = 1.0,
    pixel_size: int = 1,
    frame_index: int = 0,
    animate: bool = False,
) -> np.ndarray:
    """
    Ordered/noise dither an (H, W, 3) uint8 frame. With `palette` (N, 3) the
    result only contains palette colors; otherwise each channel is posterized to
    `levels` steps. pixel_size > 1 dithers at reduced resolution and scales up.
    """
    H, W, _ = frame.shape
    p = max(1, int(pixel_size))
    if p > 1:
        h, w = max(1, H // p), max(1, W // p)
        small = frame[:h * p, :w * p].reshape(h, p, w, p, 3).mean(axis=(1, 3))
    else:
        h, w, small = H, W, frame.astype(np.float32)

    thr = threshold_map(method, h, w, frame_index, animate)
    if palette is not None:
        spread = palette_spread(palette) * 255.0
    else:
        spread = 255.0 / max(1, levels - 1)
    x = small.astype(np.float32) + ((thr - 0.5) * spread * strength)[:, :, None]

    if palette is not None:
        out = quantize_to_palette(np.clip(x, 0, 255), palette)
    else:
        steps = max(1, levels - 1)
        out = (np.round(np.clip(x, 0, 255) / 255.0 * steps) / steps * 255.0).astype(np.uint8)

    if p > 1:
        out = np.repeat(np.repeat(out, p, axis=0), p, axis=1)
        out = np.pad(out, ((0, H - out.shape[0]), (0, W - out.shape[1]), (0, 0)), mode="edge")
    return out
