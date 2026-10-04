"""
booth_filters — the photobooth filter library (negative, Game Boy, VHS, thermal, halftone, ...).

Ported from the SSTV photo booth's booth_effects.py. Every filter takes a BGR uint8 frame plus
a Ctx (time, faces) and returns a BGR frame. Stateful ones (slit-scans, ghost trails, ...) keep a
short frame history and are re-created for every run, so nothing leaks between jobs.

Adding your own filter — drop a .py file in ~/.videobeaux/filters/ (or the folder named by the
VIDEOBEAUX_USER_FILTERS environment variable) containing:

    from videobeaux.utils.booth_filters import register

    @register("My filters", "Invert red")          # pack, name  → shows up as "My filters · Invert red"
    def invert_red(img, ctx):                      # img: BGR uint8; ctx.t = seconds; ctx.faces = [(x, y, w, h)]
        out = img.copy()
        out[..., 2] = 255 - out[..., 2]
        return out

(Pass faces=True to @register if the filter wants ctx.faces. A class instance with __call__(img, ctx)
and an optional reset() works too. Restart the app so the Filter list picks it up.)
"""
import collections
import datetime
import math

import numpy as np

from videobeaux.utils.booth_filters_dir import user_filter_dir
from videobeaux.utils.cv import require_cv2

cv2 = require_cv2()

_rng = np.random.default_rng()

class Ctx:
    """Per-frame information for effects and stickers."""

    def __init__(self, t=0.0, dt=1 / 30, faces=(), eyes=None):
        self.t = t                  # seconds (monotonic)
        self.dt = dt                # seconds since the previous frame
        self.faces = list(faces)    # smoothed (x, y, w, h) per face
        self.eyes = eyes or []      # per face: [(cx, cy, r), (cx, cy, r)]
        self.message = None         # (unused here; kept for compatibility with booth filters)

    def center(self, img):
        """Centre of the biggest face, else of the frame."""
        if self.faces:
            x, y, w, h = max(self.faces, key=lambda f: f[2])
            return float(x + w / 2), float(y + h / 2)
        return img.shape[1] / 2, img.shape[0] / 2


class Effect:
    def __init__(self, name, fn, faces=False, eyes=False):
        self.name = name
        self.fn = fn
        self.needs_faces = faces or eyes
        self.needs_eyes = eyes

    def __call__(self, img, ctx):
        return self.fn(img, ctx)

    def reset(self):
        r = getattr(self.fn, 'reset', None)
        if r:
            r()


def plain(fn):
    """Adapt a one-argument filter f(img) to the f(img, ctx) interface."""
    return lambda img, ctx: fn(img)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
_grids = {}


def grid(h, w):
    """Cached pixel coordinate grids (xx, yy) as float32."""
    k = (h, w)
    if k not in _grids:
        yy, xx = np.indices((h, w), dtype=np.float32)
        _grids[k] = (xx, yy)
    return _grids[k]


def lut3(colors_by_level):
    """(256, 3) BGR table -> cv2.LUT table for a 3-channel grey image."""
    return np.asarray(colors_by_level, np.uint8).reshape(256, 1, 3)


def gradient_lut(dark_rgb, light_rgb):
    t = np.linspace(0, 1, 256)[:, None]
    dark = np.array(dark_rgb[::-1], float)
    light = np.array(light_rgb[::-1], float)
    return lut3(dark + (light - dark) * t)


def grey3(img):
    return cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY),
                        cv2.COLOR_GRAY2BGR)


def radial_warp(img, cx, cy, R, fn, out=None):
    """Remap the disc of radius R around (cx, cy): a destination pixel at
    relative radius u (0..1) samples the source at radius fn(u)."""
    h, w = img.shape[:2]
    cx, cy, R = float(cx), float(cy), float(R)     # keep maps float32
    x0, x1 = max(0, int(cx - R)), min(w, int(cx + R) + 1)
    y0, y1 = max(0, int(cy - R)), min(h, int(cy + R) + 1)
    if out is None:
        out = img.copy()
    if x1 <= x0 or y1 <= y0 or R < 4:
        return out
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx, dy = xx - cx, yy - cy
    u = np.sqrt(dx * dx + dy * dy) / R
    inside = u < 1
    scale = np.ones_like(u)
    ui = u[inside]
    scale[inside] = fn(ui) / np.maximum(ui, 1e-6)
    out[y0:y1, x0:x1] = cv2.remap(img, cx + dx * scale, cy + dy * scale,
                                  cv2.INTER_LINEAR,
                                  borderMode=cv2.BORDER_REFLECT)
    return out


def bulge(a):
    return lambda u: u * (1 - a * (1 - u) ** 2)      # magnify the middle


def pinch(a):
    return lambda u: u * (1 + a * (1 - u) ** 2)      # shrink the middle


class History:
    """Last N frames, newest last; ago(k) = the frame k steps back."""

    def __init__(self, n):
        self.frames = collections.deque(maxlen=n)

    def push(self, img):
        self.frames.append(img.copy())

    def ago(self, k):
        n = len(self.frames)
        return self.frames[max(0, n - 1 - k)]

    def reset(self):
        self.frames.clear()


# ---------------------------------------------------------------------------
# Classic pack (the original filters, unchanged)
# ---------------------------------------------------------------------------
def make_negative(mode="full"):
    """mode: 'full' inverts every channel; 'brightness only' flips light/dark but keeps the hues."""
    def fn(img):
        if mode == "brightness only":
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            hsv[..., 2] = 255 - hsv[..., 2]
            return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        return 255 - img
    return fn


f_negative = make_negative()


class TimeWarp:
    """Live slit-scan: each horizontal band comes from an older frame."""
    name = 'Slit-scan time warp'

    def __init__(self, bands=64):
        self.frames = collections.deque(maxlen=bands)
        self.bands = bands

    def __call__(self, img):
        self.frames.append(img.copy())
        out = np.empty_like(img)
        h = img.shape[0]
        n = len(self.frames)
        for i in range(self.bands):
            y0, y1 = i * h // self.bands, (i + 1) * h // self.bands
            src = self.frames[max(0, n - 1 - i)]
            out[y0:y1] = src[y0:y1]
        return out

    def reset(self):
        self.frames.clear()


COLORMAPS = {"inferno": cv2.COLORMAP_INFERNO, "jet": cv2.COLORMAP_JET, "turbo": cv2.COLORMAP_TURBO,
             "hot": cv2.COLORMAP_HOT, "magma": cv2.COLORMAP_MAGMA, "plasma": cv2.COLORMAP_PLASMA,
             "viridis": cv2.COLORMAP_VIRIDIS, "rainbow": cv2.COLORMAP_RAINBOW, "ocean": cv2.COLORMAP_OCEAN,
             "bone": cv2.COLORMAP_BONE}


def make_thermal(colormap="inferno", equalize=True):
    cmap = COLORMAPS.get(colormap, cv2.COLORMAP_INFERNO)

    def fn(img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return cv2.applyColorMap(cv2.equalizeHist(gray) if equalize else gray, cmap)
    return fn


f_thermal = make_thermal()


POP_PALETTES = np.array([
    [(60, 20, 120), (40, 170, 255), (200, 255, 255)],
    [(90, 20, 20), (200, 70, 255), (130, 255, 190)],
    [(20, 80, 20), (0, 215, 255), (255, 200, 210)],
    [(120, 40, 0), (70, 70, 255), (150, 255, 255)],
], np.uint8)


def make_popart(layout="2x2 panels", palette=0, low=90, high=170):
    """layout '2x2 panels' = four colourways (Warhol); 'single' uses one palette over the whole frame."""
    def fn(img):
        h, w = img.shape[:2]
        if layout == "single":
            small = cv2.resize(img, (max(2, w // 2), max(2, h // 2)), interpolation=cv2.INTER_AREA)
            gray = cv2.equalizeHist(cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), (5, 5), 0))
            lvl = np.digitize(gray, [low, high])
            return cv2.resize(POP_PALETTES[int(palette) % 4][lvl], (w, h), interpolation=cv2.INTER_NEAREST)
        small = cv2.resize(img, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
        gray = cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), (5, 5), 0)
        gray = cv2.equalizeHist(gray)
        lvl = np.digitize(gray, [low, high])
        out = np.empty_like(img)
        for t, (ty, tx) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))):
            out[ty * h // 2:(ty + 1) * h // 2,
                tx * w // 2:(tx + 1) * w // 2] = POP_PALETTES[t][lvl]
        return out
    return fn


f_popart = make_popart()


def f_sketch(img):
    gray = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (5, 5), 0)
    blur = cv2.GaussianBlur(255 - gray, (21, 21), 0)
    sk = cv2.divide(gray, 255 - blur, scale=256)
    return cv2.cvtColor(sk, cv2.COLOR_GRAY2BGR)


def make_pixelate(block=16):
    def fn(img):
        h, w = img.shape[:2]
        b = max(1, int(block))
        small = cv2.resize(img, (max(1, w // b), max(1, h // b)), interpolation=cv2.INTER_AREA)
        return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
    return fn


f_pixelate = make_pixelate()


def seed(n):
    """Make the random filters repeatable (0/None = fresh randomness each run)."""
    global _rng
    _rng = np.random.default_rng(n if n else None)


def make_glitch(intensity=0.5, tears=4, rgb_shift=9, scanlines=True):
    def fn(img):
        out = img.copy()
        h = img.shape[0]
        hi = max(2, int(rgb_shift * (0.4 + intensity)))
        d = int(_rng.integers(max(1, hi // 2), hi + 1))
        out[..., 0] = np.roll(img[..., 0], d, axis=1)
        out[..., 2] = np.roll(img[..., 2], -d, axis=1)
        reach = max(8, int(60 * (0.3 + intensity)))
        for _ in range(int(tears)):
            y0 = int(_rng.integers(0, max(1, h - 10)))
            y1 = min(h, y0 + int(_rng.integers(4, 12 + int(40 * intensity))))
            out[y0:y1] = np.roll(out[y0:y1], int(_rng.integers(-reach, reach)), axis=1)
        if scanlines:
            out[::3] = (out[::3] * 0.7).astype(np.uint8)
        return out
    return fn


f_glitch = make_glitch()


def f_kaleido(img):
    out = img.copy()
    h, w = img.shape[:2]
    out[:, w // 2:] = cv2.flip(out[:, :w // 2], 1)
    out[h // 2:] = cv2.flip(out[:h // 2], 0)
    return out


SEPIA = np.array([[0.272, 0.534, 0.131],
                  [0.349, 0.686, 0.168],
                  [0.393, 0.769, 0.189]])


TONES = {            # (dark RGB, light RGB) gradients for the non-sepia tones
    "cyanotype": ((5, 20, 60), (205, 232, 255)),
    "rose":      ((40, 8, 28), (255, 222, 232)),
    "forest":    ((8, 28, 14), (212, 238, 190)),
    "gold":      ((30, 18, 0), (255, 226, 140)),
}


def make_sepia(tone="sepia"):
    """tone: sepia (warm brown), cyanotype (blue print), rose, forest, gold."""
    if tone in TONES:
        lut = gradient_lut(*TONES[tone])
        return lambda img: cv2.LUT(cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR), lut)
    return lambda img: cv2.transform(img, SEPIA).clip(0, 255).astype(np.uint8)


f_sepia = make_sepia()


_vignette = None


def f_night(img):
    global _vignette
    h, w = img.shape[:2]
    if _vignette is None or _vignette.shape != (h, w):
        yy, xx = np.mgrid[0:h, 0:w]
        r = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2))
        _vignette = np.clip(1.25 - 0.6 * r ** 2, 0, 1).astype(np.float32)
    g = cv2.equalizeHist(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)).astype(np.float32)
    g = (g + _rng.normal(0, 18, g.shape)) * _vignette
    g = g.clip(0, 255)
    return np.stack([g * 0.25, g, g * 0.35], -1).astype(np.uint8)


# ---------------------------------------------------------------------------
# Slit-scan pack
# ---------------------------------------------------------------------------
class DelayMap:
    """Generic slit-scan: every pixel belongs to a band; band b shows the
    frame delay(b, t) steps ago. Bands are precomputed as flat index lists."""

    def __init__(self, frames, bands, band_fn, delay_fn=None):
        self.hist = History(frames)
        self.n = bands
        self.band_fn = band_fn          # (h, w) -> band per pixel, 0..bands-1
        self.delay_fn = delay_fn        # (band numbers, t) -> frames back
        self._idx = None
        self._key = None

    def _bands(self, h, w):
        if self._key != (h, w):
            band = self.band_fn(h, w).ravel()
            order = np.argsort(band, kind='stable')
            counts = np.bincount(band, minlength=self.n)
            self._idx = np.split(order, np.cumsum(counts)[:-1])
            self._key = (h, w)
        return self._idx

    def __call__(self, img, ctx):
        self.hist.push(img)
        h, w = img.shape[:2]
        idx = self._bands(h, w)
        delays = (np.arange(self.n) if self.delay_fn is None
                  else self.delay_fn(np.arange(self.n), ctx.t))
        out = np.empty_like(img).reshape(-1, 3)
        for b, ids in enumerate(idx):
            if len(ids):
                out[ids] = self.hist.ago(int(delays[b])).reshape(-1, 3)[ids]
        return out.reshape(img.shape)

    def reset(self):
        self.hist.reset()


def bands_radial(n):
    def fn(h, w):
        xx, yy = grid(h, w)
        r = np.hypot(xx - w / 2, yy - h / 2) / np.hypot(w / 2, h / 2)
        return np.minimum((r * n).astype(np.int64), n - 1)
    return fn


def bands_columns(n):
    def fn(h, w):
        xx, _ = grid(h, w)
        return np.minimum((xx * n / w).astype(np.int64), n - 1)
    return fn


def bands_rows(n):
    def fn(h, w):
        _, yy = grid(h, w)
        return np.minimum((yy * n / h).astype(np.int64), n - 1)
    return fn


def wavy_delays(bands, frames):
    def fn(b, t):
        return ((frames - 1) * (0.5 + 0.5 * np.sin(b / bands * 2 * math.pi * 1.5
                                                    + t * 3))).astype(int)
    return fn


# ---------------------------------------------------------------------------
# Time pack
# ---------------------------------------------------------------------------
class Ghost:
    """Long exposure: a slowly fading average, so moving things smear."""

    def __init__(self, keep=0.85):
        self.keep = keep
        self.acc = None

    def __call__(self, img, ctx):
        f = img.astype(np.float32)
        if self.acc is None or self.acc.shape != f.shape:
            self.acc = f
        else:
            cv2.addWeighted(self.acc, self.keep, f, 1 - self.keep, 0,
                            dst=self.acc)
        return self.acc.astype(np.uint8)

    def reset(self):
        self.acc = None


class RGBSplit:
    """Red = now, green and blue = frames ago (defaults ≈ 0.3 s and 0.6 s at 30 fps)."""

    def __init__(self, delay_green=9, delay_blue=18):
        self.dg, self.db = int(delay_green), int(delay_blue)
        self.hist = History(max(self.dg, self.db) + 2)

    def __call__(self, img, ctx):
        self.hist.push(img)
        out = img.copy()
        out[..., 1] = self.hist.ago(self.dg)[..., 1]
        out[..., 0] = self.hist.ago(self.db)[..., 0]
        return out

    def reset(self):
        self.hist.reset()


class MotionOnly:
    """Only what moves shows; the still background fades to black."""

    def __init__(self):
        self.bg = None

    def __call__(self, img, ctx):
        f = img.astype(np.float32)
        if self.bg is None or self.bg.shape != f.shape:
            self.bg = f.copy()
        diff = cv2.absdiff(img, self.bg.astype(np.uint8)).max(axis=2)
        cv2.accumulateWeighted(f, self.bg, 0.04)
        mask = (diff > 22).astype(np.uint8) * 255
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        mask = cv2.dilate(mask, np.ones((7, 7), np.uint8))
        a = cv2.GaussianBlur(mask, (15, 15), 0).astype(np.float32)[..., None] / 255
        return (f * a).astype(np.uint8)

    def reset(self):
        self.bg = None


# ---------------------------------------------------------------------------
# Retro TV pack
# ---------------------------------------------------------------------------
def make_vhs(osd=True, label="PLAY", show_date=True, noise=7.0, tracking=True):
    def fn(img, ctx):
        h, w = img.shape[:2]
        ycc = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        y = cv2.blur(ycc[..., 0], (3, 1)).astype(np.float32)
        y += _rng.normal(0, noise, y.shape)
        chroma = cv2.resize(ycc[..., 1:], (max(1, w // 8), h), interpolation=cv2.INTER_AREA)
        chroma = cv2.resize(chroma, (w, h), interpolation=cv2.INTER_LINEAR)
        chroma = np.roll(chroma, 5, axis=1)
        out = np.dstack([y.clip(0, 255).astype(np.uint8), chroma])
        out = cv2.cvtColor(out, cv2.COLOR_YCrCb2BGR)
        if tracking:                                    # rolling tracking band
            band = int((ctx.t * 70) % (h + 80)) - 40
            for yy in range(max(0, band), min(h, band + 24)):
                out[yy] = np.roll(out[yy], int(_rng.integers(-18, 18)), axis=0)
                out[yy] = np.clip(out[yy].astype(np.int16)
                                  + _rng.integers(0, 90, (w, 1)), 0, 255)
        # head-switching noise along the bottom
        out[-10:] = np.roll(out[-10:], 14, axis=1)
        out[-10:] = np.clip(out[-10:].astype(np.int16)
                            + _rng.integers(-40, 40, out[-10:].shape), 0, 255)
        if osd:                                         # on-screen display, scaled to the frame
            s = max(0.5, h / 512.0)
            white, font = (235, 235, 235), cv2.FONT_HERSHEY_SIMPLEX
            now = datetime.datetime.now()
            m = int(28 * s)
            pts = np.array([[m, int(26 * s)], [m, int(50 * s)], [int(46 * s), int(38 * s)]], np.int32)
            for dx, col in ((2, (0, 0, 0)), (0, white)):
                cv2.fillPoly(out, [pts + dx], col)
                cv2.putText(out, label, (int(56 * s) + dx, int(50 * s) + dx), font, 1.0 * s, col,
                            max(1, int(2 * s)), cv2.LINE_AA)
                if show_date:
                    cv2.putText(out, now.strftime('%b %d %Y').upper(), (m + dx, h - int(58 * s) + dx),
                                font, 0.9 * s, col, max(1, int(2 * s)), cv2.LINE_AA)
                    cv2.putText(out, now.strftime('%I:%M:%S %p'), (m + dx, h - int(26 * s) + dx),
                                font, 0.9 * s, col, max(1, int(2 * s)), cv2.LINE_AA)
        return out
    return fn


f_vhs = make_vhs()


class CRT:
    """Curved glass, scanlines, RGB shadow mask, bloom and vignette."""

    def __init__(self, k=0.10, scanlines=0.45, mask=0.28, glow=0.3):
        self.k = k
        self.scan = scanlines
        self.mask_strength = mask
        self.glow = glow
        self._key = None

    def _prep(self, h, w):
        xx, yy = grid(h, w)
        nx, ny = (xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)
        f = 1 + self.k * (nx * nx + ny * ny)
        self.mx = (nx * f * 1.02) * (w / 2) + w / 2
        self.my = (ny * f * 1.02) * (h / 2) + h / 2
        mult = np.ones((h, w, 3), np.float32)
        mult[1::3] *= 1 - self.scan                           # scanlines
        col = np.arange(w) % 3
        for c in range(3):                                    # shadow mask:
            mult[:, col != 2 - c, c] *= 1 - self.mask_strength    # R, G, B stripes
        r = np.hypot(nx, ny)
        mult *= np.clip(1.25 - 0.45 * r ** 2, 0, 1)[..., None]
        self.mult = mult
        self._key = (h, w)

    def __call__(self, img, ctx):
        h, w = img.shape[:2]
        if self._key != (h, w):
            self._prep(h, w)
        warped = cv2.remap(img, self.mx, self.my, cv2.INTER_LINEAR,
                           borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        f = warped.astype(np.float32) * self.mult
        glow = cv2.resize(cv2.resize(warped, (w // 4, h // 4),
                                     interpolation=cv2.INTER_AREA), (w, h))
        glow = cv2.GaussianBlur(glow, (0, 0), 3).astype(np.float32)
        return np.clip(f * 1.25 + glow * self.glow, 0, 255).astype(np.uint8)


def make_weak_signal(noise=14.0, streaks=5, bursts=0.35, skew=0.035, speckle=0.02):
    """What SSTV looks like at the edge of reception."""
    def fn(img, ctx):
        h, w = img.shape[:2]
        xx, yy = grid(h, w)
        out = cv2.remap(img, xx + (yy - h / 2) * skew, yy, cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_WRAP)
        out[..., 2] = np.roll(out[..., 2], 3, axis=1)     # colour misregistration
        out[..., 0] = np.roll(out[..., 0], -2, axis=1)
        f = out.astype(np.int16) + _rng.normal(0, noise, out.shape).astype(np.int16)
        spk = _rng.random((h, w)) < speckle
        f[spk] = _rng.integers(0, 256, (int(spk.sum()), 3))
        for _ in range(int(streaks)):                       # streaks
            y0 = int(_rng.integers(0, max(1, h - 2)))
            x0 = int(_rng.integers(0, max(1, w - 40)))
            x1 = min(w, x0 + int(_rng.integers(40, max(41, w))))
            f[y0:y0 + 2, x0:x1] = _rng.integers(120, 256, 3)
        if _rng.random() < bursts:                          # a burst of static
            y0 = int(_rng.integers(0, max(1, h - 20)))
            n = int(_rng.integers(6, 20))
            f[y0:y0 + n] = _rng.integers(0, 256, (min(n, h - y0), w, 3))
        return f.clip(0, 255).astype(np.uint8)
    return fn


f_weak_signal = make_weak_signal()


# ---------------------------------------------------------------------------
# Print & pixel pack
# ---------------------------------------------------------------------------
class Halftone:
    """Newspaper dots: dot size per 8x8 cell follows the darkness."""

    def __init__(self, cell=8, levels=16):
        self.cell = cell
        self.levels = levels
        big = cell * 8
        masks = []
        for k in range(levels):
            m = np.zeros((big, big), np.uint8)
            r = big * 0.72 * math.sqrt(k / (levels - 1))
            if r > 0:
                cv2.circle(m, (big // 2, big // 2), int(r), 255, -1, cv2.LINE_AA)
            masks.append(cv2.resize(m, (cell, cell),
                                    interpolation=cv2.INTER_AREA) / 255.0)
        self.masks = np.array(masks, np.float32)
        self.paper = np.array([228, 238, 242], np.float32)
        self.ink = np.array([45, 35, 30], np.float32)

    def __call__(self, img, ctx):
        h, w = img.shape[:2]
        c = self.cell
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        small = cv2.resize(gray, (w // c, h // c), interpolation=cv2.INTER_AREA)
        dark = 1 - cv2.equalizeHist(small) / 255.0
        lvl = np.clip((dark * (self.levels - 1)).round().astype(int), 0,
                      self.levels - 1)
        cov = self.masks[lvl].transpose(0, 2, 1, 3).reshape(lvl.shape[0] * c,
                                                             lvl.shape[1] * c)
        cov = cv2.resize(cov, (w, h), interpolation=cv2.INTER_NEAREST)[..., None]
        return (self.paper * (1 - cov) + self.ink * cov).astype(np.uint8)


def bayer(n):
    m = np.array([[0]])
    while m.shape[0] < n:
        m = np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])
    return (m + 0.5) / m.size


GAMEBOY = np.array([(15, 56, 15), (48, 98, 48), (139, 172, 15),
                    (155, 188, 15)], np.uint8)[:, ::-1]   # RGB -> BGR


def f_gameboy(img):
    h, w = img.shape[:2]
    small = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (w // 4, h // 4),
                       interpolation=cv2.INTER_AREA)
    small = cv2.equalizeHist(small) / 255.0 * 3
    th = np.tile(bayer(4), (small.shape[0] // 4 + 1, small.shape[1] // 4 + 1))
    lvl = np.clip(np.floor(small + th[:small.shape[0], :small.shape[1]]),
                  0, 3).astype(int)
    return cv2.resize(GAMEBOY[lvl], (w, h), interpolation=cv2.INTER_NEAREST)


def f_onebit(img):
    h, w = img.shape[:2]
    small = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (w // 2, h // 2),
                       interpolation=cv2.INTER_AREA)
    small = cv2.equalizeHist(small) / 255.0
    th = np.tile(bayer(8), (small.shape[0] // 8 + 1, small.shape[1] // 8 + 1))
    bw = (small > th[:small.shape[0], :small.shape[1]]).astype(np.uint8) * 255
    return cv2.cvtColor(cv2.resize(bw, (w, h), interpolation=cv2.INTER_NEAREST),
                        cv2.COLOR_GRAY2BGR)


class Ascii:
    """The picture rebuilt from characters, each tinted with its cell colour."""
    RAMP = ' .,:;i1tfLCG08@'

    def __init__(self, cw=10, ch=16):
        self.cw, self.ch = cw, ch
        tiles = []
        for c in self.RAMP:
            t = np.zeros((ch, cw), np.uint8)
            cv2.putText(t, c, (1, ch - 4), cv2.FONT_HERSHEY_PLAIN, 0.95, 255, 1,
                        cv2.LINE_AA)
            tiles.append(t / 255.0)
        self.tiles = np.array(tiles, np.float32)

    def __call__(self, img, ctx):
        h, w = img.shape[:2]
        cols, rows = w // self.cw, h // self.ch
        small = cv2.resize(img, (cols, rows), interpolation=cv2.INTER_AREA)
        gray = cv2.equalizeHist(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY))
        lvl = (gray / 256.0 * len(self.RAMP)).astype(int)
        cov = self.tiles[lvl].transpose(0, 2, 1, 3).reshape(rows * self.ch,
                                                            cols * self.cw)
        hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
        hsv[..., 2] = 255
        hsv[..., 1] = np.minimum(255, hsv[..., 1].astype(int) * 3 // 2)
        col = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        col = cv2.resize(col, (cols * self.cw, rows * self.ch),
                         interpolation=cv2.INTER_NEAREST).astype(np.float32)
        out = np.zeros_like(img)
        out[:rows * self.ch, :cols * self.cw] = (col * cov[..., None]).astype(np.uint8)
        return out


# ---------------------------------------------------------------------------
# Art pack (heavy ones work at half size)
# ---------------------------------------------------------------------------
def _half(img):
    h, w = img.shape[:2]
    return cv2.resize(img, (w // 2, h // 2), interpolation=cv2.INTER_AREA)


def _full(small, img):
    return cv2.resize(small, (img.shape[1], img.shape[0]),
                      interpolation=cv2.INTER_LINEAR)


def f_comic(img):
    small = _half(img)
    col = cv2.bilateralFilter(small, 9, 60, 60)
    col = cv2.bilateralFilter(col, 9, 60, 60)
    col = (col // 40) * 40 + 20
    hsv = cv2.cvtColor(col.astype(np.uint8), cv2.COLOR_BGR2HSV)
    hsv[..., 1] = np.minimum(255, hsv[..., 1].astype(int) * 13 // 10)
    col = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    gray = cv2.medianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), 7)
    edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                  cv2.THRESH_BINARY, 11, 7)
    edges = cv2.erode(edges, np.ones((2, 2), np.uint8))
    out = cv2.bitwise_and(col, col, mask=edges)
    return _full(out, img)


EMBOSS = np.array([[-2, -1, 0], [-1, 1, 1], [0, 1, 2]], np.float32)


def make_oil(brush=40, levels=24, relief=0.35):
    def fn(img):
        small = _half(img)
        paint = cv2.edgePreservingFilter(small, flags=cv2.RECURS_FILTER,
                                         sigma_s=float(brush), sigma_r=0.35)
        paint = cv2.medianBlur(paint, 5)
        lv = max(2, int(levels))
        paint = (paint // lv) * lv + lv // 2
        gray = cv2.cvtColor(paint.astype(np.uint8), cv2.COLOR_BGR2GRAY)
        rel = cv2.filter2D(gray.astype(np.float32), -1, EMBOSS) - gray
        out = paint.astype(np.float32) + relief * rel[..., None]
        return _full(np.clip(out, 0, 255).astype(np.uint8), img)
    return fn


f_oil = make_oil()


_paper = {}


def f_watercolour(img):
    small = _half(img)
    wc = cv2.stylization(small, sigma_s=60, sigma_r=0.55)
    h, w = small.shape[:2]
    if (h, w) not in _paper:
        n = np.random.default_rng(1).normal(0, 1, (h, w)).astype(np.float32)
        n = cv2.GaussianBlur(n, (0, 0), 1.5)
        _paper[(h, w)] = (0.93 + 0.07 * n / (np.abs(n).max() + 1e-6))[..., None]
    out = wc.astype(np.float32) * _paper[(h, w)] * 0.92 + 20
    return _full(np.clip(out, 0, 255).astype(np.uint8), img)


def f_neon(img, ctx):
    h, w = img.shape[:2]
    gray = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (5, 5), 0)
    edges = cv2.dilate(cv2.Canny(gray, 40, 110), np.ones((2, 2), np.uint8))
    xx, yy = grid(h, w)
    hue = ((xx / w * 180 + yy / h * 60 + ctx.t * 40) % 180).astype(np.uint8)
    col = cv2.cvtColor(np.dstack([hue, np.full_like(hue, 255),
                                  edges]), cv2.COLOR_HSV2BGR)
    small = cv2.resize(col, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
    glow = _full(cv2.GaussianBlur(small, (0, 0), 4), img).astype(np.float32)
    return np.clip(col * 1.0 + glow * 2.5, 0, 255).astype(np.uint8)


def make_emboss(strength=1.0, angle=135.0, keep_color=False):
    a = np.deg2rad(angle)
    sx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], np.float32)
    sy = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], np.float32)
    kernel = (np.cos(a) * sx + np.sin(a) * sy) * float(strength)

    def fn(img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
        relief = cv2.filter2D(gray, -1, kernel)
        if keep_color:
            return np.clip(img.astype(np.float32) + relief[..., None], 0, 255).astype(np.uint8)
        return cv2.cvtColor(np.clip(gray + relief, 0, 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    return fn


f_emboss = make_emboss()


# ---------------------------------------------------------------------------
# Colour pack
# ---------------------------------------------------------------------------
def duotone(dark_rgb, light_rgb):
    lut = gradient_lut(dark_rgb, light_rgb)

    def fn(img):
        g = cv2.equalizeHist(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
        return cv2.LUT(cv2.cvtColor(g, cv2.COLOR_GRAY2BGR), lut)
    return fn


def make_infrared(saturation=1.5):
    """False-colour infrared film look: greens turn red/pink."""
    def fn(img):
        f = img.astype(np.float32)
        b, g, r = f[..., 0], f[..., 1], f[..., 2]
        out = np.dstack([b * 0.9 + g * 0.2, r * 0.75, g * 1.25 + r * 0.25])
        out = np.clip(out, 0, 255).astype(np.uint8)
        hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV)
        hsv[..., 1] = np.minimum(255, hsv[..., 1].astype(np.float32) * saturation).astype(np.uint8)
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    return fn


f_infrared = make_infrared()


def make_solarize(threshold=128):
    t = float(min(254, max(1, threshold)))
    v = np.arange(256, dtype=np.float32)
    lut = np.where(v < t, v * 255.0 / t, (255.0 - v) * 255.0 / (255.0 - t)).clip(0, 255).astype(np.uint8)
    return lambda img: cv2.LUT(img, lut)


f_solarize = make_solarize()


def make_posterize(levels=4, smooth=True):
    n = max(2, int(levels))
    lut = (np.round(np.arange(256) / 255.0 * (n - 1)) * (255.0 / (n - 1))).astype(np.uint8)

    def fn(img):
        return cv2.LUT(cv2.GaussianBlur(img, (3, 3), 0) if smooth else img, lut)
    return fn


f_posterize = make_posterize()


class Chromatic:
    """Radial RGB split like a cheap lens: red grows, blue shrinks."""

    def __init__(self, amount=0.03):
        self.a = amount
        self._key = None

    def __call__(self, img, ctx):
        h, w = img.shape[:2]
        if self._key != (h, w):
            xx, yy = grid(h, w)
            cx, cy = w / 2, h / 2
            self.maps = [(cx + (xx - cx) * s, cy + (yy - cy) * s)
                         for s in (1 + self.a, 1 - self.a)]
            self._key = (h, w)
        out = img.copy()
        out[..., 2] = cv2.remap(img[..., 2], *self.maps[1], cv2.INTER_LINEAR,
                                borderMode=cv2.BORDER_REFLECT)
        out[..., 0] = cv2.remap(img[..., 0], *self.maps[0], cv2.INTER_LINEAR,
                                borderMode=cv2.BORDER_REFLECT)
        return out


# ---------------------------------------------------------------------------
# Warp pack (centred on the biggest face when there is one)
# ---------------------------------------------------------------------------
def f_fisheye(img, ctx):
    cx, cy = ctx.center(img)
    return radial_warp(img, cx, cy, 0.55 * min(img.shape[:2]) + 60, bulge(0.6))


def f_pinch(img, ctx):
    cx, cy = ctx.center(img)
    return radial_warp(img, cx, cy, 0.5 * min(img.shape[:2]) + 40, pinch(0.7))


def f_swirl(img, ctx):
    h, w = img.shape[:2]
    cx, cy = ctx.center(img)
    R = 0.55 * min(h, w)
    xx, yy = grid(h, w)
    dx, dy = xx - cx, yy - cy
    u = np.sqrt(dx * dx + dy * dy) / R
    ang = 2.6 * np.clip(1 - u, 0, 1) ** 2 * (0.7 + 0.3 * math.sin(ctx.t * 0.8))
    c, s = np.cos(ang), np.sin(ang)
    return cv2.remap(img, cx + dx * c - dy * s, cy + dx * s + dy * c,
                     cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def f_wavy(img, ctx):
    h, w = img.shape[:2]
    xx, yy = grid(h, w)
    mx = xx + 16 * np.sin(2 * math.pi * yy / 150 + ctx.t * 2)
    my = yy + 10 * np.sin(2 * math.pi * xx / 220 + ctx.t * 1.3)
    return cv2.remap(img, mx.astype(np.float32), my.astype(np.float32),
                     cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


class Tunnel:
    """The picture wrapped around the inside of a tunnel, flying forward."""

    def __init__(self, speed=90.0, around=3, deep=4):
        self.speed, self.around, self.deep = speed, around, deep
        self._key = None

    def __call__(self, img, ctx):
        h, w = img.shape[:2]
        cx, cy = w / 2, h / 2
        if self._key != (h, w):
            xx, yy = grid(h, w)
            dx, dy = xx - cx, yy - cy
            r = np.sqrt(dx * dx + dy * dy)
            # the picture tiles `around` times around the wall ...
            self.u = ((np.arctan2(dy, dx) / (2 * math.pi) + 0.5) * self.around * w).astype(np.float32)
            rmin, rmax = 6.0, math.hypot(w, h) / 2
            # ... and `deep` times down it: log-polar, so equal steps in
            # log(radius) are equal steps along the tunnel
            self.depth = (h * self.deep * (1 - np.log(np.maximum(r, rmin) / rmin)
                                           / math.log(rmax / rmin))).astype(np.float32)
            self.fog = np.clip(r / (0.35 * min(h, w)), 0.15, 1)[..., None].astype(np.float32)
            self._key = (h, w)
        v = (self.depth + ctx.t * self.speed) % h
        out = cv2.remap(img, self.u, v.astype(np.float32), cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_WRAP)
        return (out * self.fog).astype(np.uint8)


class LittlePlanet:
    """Bottom of the picture becomes a tiny round world, sky all around."""

    def __init__(self, curve=0.8, spin=0.0):
        self.curve, self.spin = curve, spin
        self._key = None

    def __call__(self, img, ctx):
        h, w = img.shape[:2]
        if self._key != (h, w):
            xx, yy = grid(h, w)
            dx, dy = xx - w / 2, yy - h / 2
            r = np.sqrt(dx * dx + dy * dy)
            rmax = 0.5 * math.hypot(w, h)
            self.mx = ((np.arctan2(dx, dy) / (2 * math.pi) + 0.5) * 2 * w).astype(np.float32)
            self.my = np.clip(h * (1 - (r / rmax) ** self.curve), 0, h - 1).astype(np.float32)
            self._key = (h, w)
        src = np.hstack([img, cv2.flip(img, 1)])     # seamless all the way round
        mx = self.mx + np.float32(self.spin * ctx.t / 360.0 * 2 * w) if self.spin else self.mx
        return cv2.remap(src, mx, self.my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)


# ---------------------------------------------------------------------------
# Face pack
# ---------------------------------------------------------------------------
def _face_warp(fn, size):
    def run(img, ctx):
        out = img.copy()
        for x, y, w, h in sorted(ctx.faces, key=lambda f: -f[2]):
            src = out.copy()
            radial_warp(src, x + w / 2, y + h * 0.5, size * w, fn, out=out)
        return out
    return run


def make_face_warp(effect="big head", strength=1.0, size=1.0):
    """effect: big head / tiny head / big eyes. strength scales the distortion, size the area it covers."""
    if effect == "big eyes":
        a, r = min(0.95, 0.75 * strength), 0.27 * size

        def fn(img, ctx):
            out = img.copy()
            for eyes, (x, y, w, h) in zip(ctx.eyes, ctx.faces):
                for ex, ey, er in eyes:
                    src = out.copy()
                    radial_warp(src, ex, ey, r * w, bulge(a), out=out)
            return out
        return fn
    if effect == "tiny head":
        return _face_warp(pinch(min(0.95, 0.75 * strength)), 1.0 * size)
    return _face_warp(bulge(min(0.95, 0.5 * strength)), 1.05 * size)


f_big_eyes = make_face_warp("big eyes")


def _paste_face(dst, src_img, sbox, dbox, softness=0.06):
    """Put the face in sbox (from src_img) over dbox in dst, colour-matched,
    with a soft oval edge."""
    sx, sy, sw, sh = [int(v) for v in sbox]
    dx, dy, dw, dh = [int(v) for v in dbox]
    H, W = dst.shape[:2]
    if min(sw, sh, dw, dh) < 8:
        return
    face = src_img[max(0, sy):sy + sh, max(0, sx):sx + sw]
    if face.size == 0:
        return
    face = cv2.resize(face, (dw, dh), interpolation=cv2.INTER_LINEAR).astype(np.float32)
    x0, y0 = max(0, dx), max(0, dy)
    x1, y1 = min(W, dx + dw), min(H, dy + dh)
    if x1 <= x0 or y1 <= y0:
        return
    face = face[y0 - dy:y1 - dy, x0 - dx:x1 - dx]
    roi = dst[y0:y1, x0:x1].astype(np.float32)
    # match the destination's skin tone
    fm, fs = face.reshape(-1, 3).mean(0), face.reshape(-1, 3).std(0) + 1
    rm, rs = roi.reshape(-1, 3).mean(0), roi.reshape(-1, 3).std(0) + 1
    face = (face - fm) * (rs / fs) + rm
    mask = np.zeros((dh, dw), np.float32)
    cv2.ellipse(mask, (dw // 2, dh // 2), (int(dw * 0.42), int(dh * 0.5)),
                0, 0, 360, 1.0, -1)
    mask = cv2.GaussianBlur(mask, (0, 0), dw * softness + 1)
    mask = mask[y0 - dy:y1 - dy, x0 - dx:x1 - dx][..., None]
    dst[y0:y1, x0:x1] = np.clip(roi * (1 - mask) + face * mask, 0,
                                255).astype(np.uint8)


def make_face_swap(softness=0.06):
    def fn(img, ctx):
        if len(ctx.faces) < 2:
            ctx.message = 'Face swap needs 2 faces'
            return img
        a, b = sorted(ctx.faces, key=lambda f: -f[2])[:2]
        out = img.copy()
        _paste_face(out, img, a, b, softness)
        _paste_face(out, img, b, a, softness)
        return out
    return fn


f_face_swap = make_face_swap()


# ---------------------------------------------------------------------------
# Extra filters added for videobeaux (not in the original booth)
# ---------------------------------------------------------------------------
_clahe = None


def make_bw(contrast=2.5, grain=0.0):
    """High-contrast black & white (local contrast boost, so faces and texture pop)."""
    clahe = cv2.createCLAHE(clipLimit=max(0.1, float(contrast)), tileGridSize=(8, 8))

    def fn(img):
        g = clahe.apply(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
        if grain > 0:
            g = np.clip(g.astype(np.float32) + _rng.normal(0, 40 * grain, g.shape), 0, 255).astype(np.uint8)
        return cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
    return fn


f_bw = make_bw()


def make_blueprint(sensitivity=0.5, line_rgb=(235, 245, 255), paper_rgb=(10, 70, 150), grid_lines=False):
    line, paper = tuple(line_rgb[::-1]), tuple(paper_rgb[::-1])
    lo = int(110 - 90 * min(1.0, max(0.0, sensitivity)))

    def fn(img):
        gray = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (5, 5), 0)
        edges = cv2.dilate(cv2.Canny(gray, lo, int(lo * 2.5)), np.ones((2, 2), np.uint8))
        out = np.empty_like(img)
        out[:] = paper
        if grid_lines:
            step = max(8, img.shape[0] // 18)
            faint = tuple(int(0.8 * c + 0.2 * l) for c, l in zip(paper, line))
            out[::step] = faint
            out[:, ::step] = faint
        out[edges > 0] = line
        return out
    return fn


f_blueprint = make_blueprint()


def make_hue_cycle(speed=60.0):
    """Rotate every colour round the wheel, `speed` degrees per second."""
    def fn(img, ctx):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hsv[..., 0] = (hsv[..., 0].astype(np.int32) + int(ctx.t * speed / 2)) % 180
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    return fn


f_hue_cycle = make_hue_cycle()


_lomo_cache = {}


def make_lomo(vignette=0.65, saturation=1.0, contrast=1.0):
    """Cross-processed toy-camera look: punchy curves, colour cast, dark corners."""
    cache = {}
    x = np.arange(256) / 255.0

    def curve(k, lift=0.0, gain=1.0):
        c = 1 / (1 + np.exp(-k * contrast * (x - 0.5)))
        c = (c - c.min()) / (c.max() - c.min())
        return np.clip((c * gain + lift) * 255, 0, 255).astype(np.uint8)
    lut = np.dstack([curve(7, 0.06, 0.92), curve(6, 0.0, 1.0), curve(5, -0.02, 1.05)]).reshape(256, 1, 3)

    def fn(img):
        h, w = img.shape[:2]
        out = cv2.LUT(img, lut)
        if saturation != 1.0:
            hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV)
            hsv[..., 1] = np.clip(hsv[..., 1].astype(np.float32) * saturation, 0, 255).astype(np.uint8)
            out = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        if (h, w) not in cache:
            yy, xx = np.mgrid[0:h, 0:w]
            r = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2))
            cache[(h, w)] = np.clip(1.15 - vignette * r ** 2, 0.25, 1)[..., None].astype(np.float32)
        return (out * cache[(h, w)]).astype(np.uint8)
    return fn


f_lomo = make_lomo()


def palette_filter(colors_rgb, block=3, spread=56):
    """Quantise to a fixed retro palette with an ordered dither, at chunky `block`-px pixels."""
    pal = np.array(colors_rgb, np.float32)[:, ::-1]        # RGB -> BGR
    th = bayer(4)

    def fn(img):
        h, w = img.shape[:2]
        sh, sw = max(1, h // block), max(1, w // block)
        small = cv2.resize(img, (sw, sh), interpolation=cv2.INTER_AREA).astype(np.float32)
        lo, hi = np.percentile(small, (2, 98))              # auto-levels: dim footage still uses the whole palette
        small = (small - lo) * (255.0 / max(hi - lo, 1.0))
        t = np.tile(th, (sh // 4 + 1, sw // 4 + 1))[:sh, :sw, None]
        small = small + (t - 0.5) * spread
        d = ((small[:, :, None, :] - pal[None, None, :, :]) ** 2).sum(-1)
        idx = d.argmin(-1)
        return cv2.resize(pal[idx].astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)
    return fn


CGA = [(0, 0, 0), (85, 255, 255), (255, 85, 255), (255, 255, 255)]
C64 = [(0, 0, 0), (255, 255, 255), (104, 55, 43), (112, 164, 178), (111, 61, 134), (88, 141, 67),
       (53, 40, 121), (184, 199, 111), (111, 79, 37), (67, 57, 0), (154, 103, 89), (68, 68, 68),
       (108, 108, 108), (154, 210, 132), (108, 94, 181), (149, 149, 149)]
PICO8 = [(0, 0, 0), (29, 43, 83), (126, 37, 83), (0, 135, 81), (171, 82, 54), (95, 87, 79),
         (194, 195, 199), (255, 241, 232), (255, 0, 77), (255, 163, 0), (255, 236, 39),
         (0, 228, 54), (41, 173, 255), (131, 118, 156), (255, 119, 168), (255, 204, 170)]


class LEDWall:
    """A wall of round coloured LEDs."""

    def __init__(self, cell=10, brightness=1.15, dot=1.0):
        self.cell, self.brightness = int(cell), brightness
        m = np.zeros((self.cell * 4, self.cell * 4), np.uint8)
        cv2.circle(m, (self.cell * 2, self.cell * 2), int(self.cell * 1.7 * dot), 255, -1, cv2.LINE_AA)
        self.dot = (cv2.resize(m, (self.cell, self.cell), interpolation=cv2.INTER_AREA) / 255.0).astype(np.float32)

    def __call__(self, img, ctx):
        h, w = img.shape[:2]
        c = self.cell
        small = cv2.resize(img, (max(1, w // c), max(1, h // c)), interpolation=cv2.INTER_AREA)
        big = cv2.resize(small, (small.shape[1] * c, small.shape[0] * c), interpolation=cv2.INTER_NEAREST)
        mask = np.tile(self.dot, (small.shape[0], small.shape[1]))[..., None]
        out = np.zeros_like(img)
        out[:big.shape[0], :big.shape[1]] = np.clip(big * mask * self.brightness, 0, 255).astype(np.uint8)
        return out


# ---------------------------------------------------------------------------
def make_packs():
    """[(pack name, [Effect, ...]), ...] in display order."""
    E = Effect
    tw = TimeWarp()
    return [
        ('Classic', [
            E('Negative', plain(f_negative)),
            E('Black & white', plain(f_bw)),
            E('Thermal', plain(f_thermal)),
            E('Pop art', plain(f_popart)),
            E('Sketch', plain(f_sketch)),
            E('Pixelate', plain(f_pixelate)),
            E('Glitch', plain(f_glitch)),
            E('Kaleidoscope', plain(f_kaleido)),
            E('Sepia', plain(f_sepia)),
            E('Night vision', plain(f_night)),
        ]),
        ('Slit-scan', [
            E('Time warp', _Reset(lambda img, ctx: tw(img), tw)),
            E('Radial', DelayMap(48, 48, bands_radial(48))),
            E('Vertical', DelayMap(64, 64, bands_columns(64))),
            E('Wavy', DelayMap(48, 96, bands_rows(96), wavy_delays(96, 48))),
        ]),
        ('Time', [
            E('Ghost trails', Ghost()),
            E('RGB time-split', RGBSplit()),
            E('Motion only', MotionOnly()),
        ]),
        ('Retro TV', [
            E('VHS', f_vhs),
            E('CRT', CRT()),
            E('Weak signal', f_weak_signal),
        ]),
        ('Print & pixel', [
            E('Halftone', Halftone()),
            E('Game Boy', plain(f_gameboy)),
            E('1-bit Mac', plain(f_onebit)),
            E('ASCII', Ascii()),
            E('LED wall', LEDWall()),
            E('CGA', plain(palette_filter(CGA))),
            E('Commodore 64', plain(palette_filter(C64))),
            E('PICO-8', plain(palette_filter(PICO8))),
        ]),
        ('Art', [
            E('Comic', plain(f_comic)),
            E('Oil paint', plain(f_oil)),
            E('Watercolour', plain(f_watercolour)),
            E('Neon edges', f_neon),
            E('Emboss', plain(f_emboss)),
            E('Blueprint', plain(f_blueprint)),
        ]),
        ('Colour', [
            E('Duotone cyan/magenta', plain(duotone((110, 0, 120), (0, 235, 255)))),
            E('Duotone orange/teal', plain(duotone((0, 60, 75), (255, 165, 45)))),
            E('Duotone purple/yellow', plain(duotone((55, 15, 105), (255, 228, 70)))),
            E('Infrared', plain(f_infrared)),
            E('Solarize', plain(f_solarize)),
            E('Posterize', plain(f_posterize)),
            E('Chromatic aberration', Chromatic()),
            E('Lomo', plain(f_lomo)),
            E('Hue cycle', f_hue_cycle),
        ]),
        ('Warp', [
            E('Fisheye', f_fisheye, faces=True),
            E('Pinch', f_pinch, faces=True),
            E('Swirl', f_swirl, faces=True),
            E('Wavy mirror', f_wavy),
            E('Tunnel', Tunnel()),
            E('Little planet', LittlePlanet()),
        ]),
        ('Face', [
            E('Big head', _face_warp(bulge(0.5), 1.05), faces=True),
            E('Tiny head', _face_warp(pinch(0.75), 1.0), faces=True),
            E('Big eyes', f_big_eyes, eyes=True),
            E('Face swap', f_face_swap, faces=True),
        ]),
    ]


class _Reset:
    """Callable wrapper that forwards reset() to a stateful object."""

    def __init__(self, fn, obj):
        self.fn, self.obj = fn, obj

    def __call__(self, img, ctx):
        return self.fn(img, ctx)

    def reset(self):
        self.obj.reset()


# ---------------------------------------------------------------------------
# Registry: every filter by its "Pack · Name" label, plus user-dropped filters
# ---------------------------------------------------------------------------
_USER = []          # [(pack, Effect)] filled by register()


def register(pack, name, faces=False, eyes=False):
    """Decorator for user filters — see the module docstring."""
    def deco(fn):
        _USER.append((pack, Effect(name, fn, faces=faces, eyes=eyes)))
        return fn
    return deco


def load_user_filters():
    """Import every *.py in the user filter folder (once); a broken file is skipped with a warning."""
    import importlib.util
    import sys
    d = user_filter_dir()
    if not d.is_dir() or getattr(load_user_filters, "_done", False):
        return
    load_user_filters._done = True
    for path in sorted(d.glob("*.py")):
        try:
            spec = importlib.util.spec_from_file_location(f"vb_user_filter_{path.stem}", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        except Exception as e:      # noqa: BLE001 — never let a user file break the app
            print(f"⚠️  Skipped user filter {path.name}: {e}", file=sys.stderr)


def build_filters():
    """Fresh {label: Effect} for every built-in and user filter (new instances → no shared state)."""
    load_user_filters()
    out = {}
    for pack, effects in make_packs() + _group(_USER):
        for e in effects:
            out[f"{pack} · {e.name}"] = e
    return out


def _group(pairs):
    packs = {}
    for pack, e in pairs:
        packs.setdefault(pack, []).append(e)
    return list(packs.items())
