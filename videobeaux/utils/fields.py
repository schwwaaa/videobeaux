"""
Coordinate / field engine shared by Topobeaux, Shape Synth and Stackadelic.

Coordinates: the frame height spans y in [-1, 1] and x keeps the aspect ratio, so circles stay round.
A *shape field* is a scalar image that is <= 1 inside the shape and grows outward, 0 at the shape's centre line;
`inside(field, edge)` turns it into a 0..1 matte with a soft edge.
"""
from __future__ import annotations

import numpy as np

SHAPES = ["circle", "ring", "diamond", "square", "cross", "stripes", "checker", "vortex"]
COMBINE = ["A", "B", "min", "max", "sum", "difference", "xor"]

_cache: dict = {}


def ramps(h: int, w: int, rotate_deg: float = 0.0, cx: float = 0.0, cy: float = 0.0):
    """
    (x, y) float32 images: x in [-w/h, w/h], y in [-1, 1], centred on (cx, cy) in those units, then rotated by
    `rotate_deg` about that centre. x grows to the right, y grows downward.
    """
    key = (h, w)
    if key not in _cache:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        _cache[key] = ((xx / max(w - 1, 1) * 2.0 - 1.0) * (w / h), yy / max(h - 1, 1) * 2.0 - 1.0)
        if len(_cache) > 6:
            _cache.pop(next(iter(_cache)))
    x, y = _cache[key]
    x, y = x - cx, y - cy
    if rotate_deg:
        a = np.deg2rad(rotate_deg)
        c, s = np.cos(a), np.sin(a)
        x, y = c * x - s * y, s * x + c * y
    return x.astype(np.float32), y.astype(np.float32)


def soft(x: np.ndarray, lo: float, hi: float, edge: float = 0.0) -> np.ndarray:
    """1 where lo <= x <= hi, fading to 0 over `edge` across each end (edge 0 = hard step)."""
    edge = max(float(edge), 1e-6)
    up = np.clip((x - (lo - edge / 2.0)) / edge, 0.0, 1.0)
    dn = np.clip(((hi + edge / 2.0) - x) / edge, 0.0, 1.0)
    return np.minimum(up, dn)


def inside(field: np.ndarray, edge: float = 0.05) -> np.ndarray:
    """Matte (0..1) of a shape field: 1 where field <= 1, soft over `edge` in field units."""
    return np.clip((1.0 - field) / max(float(edge), 1e-6) + 0.5, 0.0, 1.0).astype(np.float32)


def fold(x: np.ndarray, n: float) -> np.ndarray:
    """
    Frequency doubler: repeat a 0-at-centre distance profile outward as bands (50% duty, `n` per unit), so a
    circle becomes concentric rings, a square nested squares. n <= 1 leaves the profile unchanged.
    """
    if n <= 1.0001:
        return x
    t = np.mod(np.clip(x, 0.0, None) * n, 2.0)
    return (2.0 * (1.0 - np.abs(t - 1.0))).astype(np.float32)


def curve(x: np.ndarray, k: float) -> np.ndarray:
    """Exp (k > 0) / log (k < 0) shaper on 0..1; k = 0 is linear."""
    if abs(k) < 1e-3:
        return x
    xc = np.clip(x, 0.0, None)
    if k > 0:
        return ((np.exp(k * xc) - 1.0) / (np.exp(k) - 1.0)).astype(np.float32)
    k = -k
    return (np.log1p(k * xc) / np.log1p(k)).astype(np.float32)


def shape_field(name: str, x: np.ndarray, y: np.ndarray, *, size: float = 0.5, fold_n: float = 1.0,
                curve_k: float = 0.0, thickness: float = 0.3) -> np.ndarray:
    """
    Scalar field for a shape recipe at half-size `size` (in coordinate units). <= 1 inside, 0 on the centre line.
    `fold_n` folds the field (repeats rings / diamonds / squares outward, or adds spiral arms to the vortex);
    `curve_k` bends the profile (exp/log); `thickness` is the ring's half width as a fraction of `size`.
    """
    size = max(float(size), 1e-3)
    ax, ay = np.abs(x), np.abs(y)
    if name == "circle":
        f = np.hypot(x, y) / size
    elif name == "ring":
        f = np.abs(np.hypot(x, y) - size) / max(thickness * size, 1e-3)
        return curve(f, curve_k)
    elif name == "diamond":
        f = (ax + ay) / size
    elif name == "square":
        f = np.maximum(ax, ay) / size
    elif name == "cross":
        f = np.minimum(ax, ay) / (size * 0.5)               # bars of width `size` through the centre along both axes
        return curve(f.astype(np.float32), curve_k)
    elif name == "stripes":
        f = 2.0 * np.abs(np.mod(x / size + 1.0, 2.0) - 1.0)  # vertical bars, 50% duty, period 2·size
        return curve(f.astype(np.float32), curve_k)
    elif name == "checker":
        parity = (np.floor(x / size) + np.floor(y / size)) % 2
        return np.where(parity == 0, 0.0, 2.0).astype(np.float32)
    elif name == "vortex":
        arms = max(1, int(round(fold_n)))
        t = np.hypot(x, y) / size + arms * np.arctan2(y, x) / (2.0 * np.pi)
        f = np.abs(np.mod(t, 1.0) - 0.5) * 4.0               # spiral arms, 50% duty
        return curve(f.astype(np.float32), curve_k)
    else:
        raise ValueError(f"unknown shape {name!r}")
    f = f.astype(np.float32)
    if fold_n > 1.0001:
        f = fold(f, fold_n)
    return curve(f, curve_k)


def combine(a: np.ndarray, b: np.ndarray, mode: str) -> np.ndarray:
    """Combine two 0..1 mattes."""
    if mode == "A":
        return a
    if mode == "B":
        return b
    if mode == "min":
        return np.minimum(a, b)
    if mode == "max":
        return np.maximum(a, b)
    if mode == "sum":
        return np.clip(a + b, 0.0, 1.0)
    if mode == "difference":
        return np.abs(a - b)
    if mode == "xor":
        return np.clip(a + b - 2.0 * a * b, 0.0, 1.0)
    raise ValueError(f"unknown combine mode {mode!r}")
