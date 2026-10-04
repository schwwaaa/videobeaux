"""Shared building blocks for the video-feedback programs (Feedback Loop, Key Feedback)."""
from __future__ import annotations

import numpy as np

KEY_MODES = ["none", "luma", "color", "luma AND color", "luma OR color"]


def transform_feedback(cv2, fb, zoom_pct=0.0, rotate_deg=0.0, shift_x=0.0, shift_y=0.0, hue_shift_deg=0.0):
    """One pass around the loop: zoom / rotate / shift the previous output, then rotate its hues."""
    H, W = fb.shape[:2]
    m = cv2.getRotationMatrix2D((W / 2.0, H / 2.0), rotate_deg, 1.0 + zoom_pct / 100.0)
    m[0, 2] += shift_x
    m[1, 2] += shift_y
    fb = cv2.warpAffine(fb, m, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if abs(hue_shift_deg) > 0.01:
        hsv = cv2.cvtColor(fb, cv2.COLOR_RGB2HSV)
        hsv[..., 0] = (hsv[..., 0].astype(np.int16) + int(round(hue_shift_deg / 2.0))) % 180
        fb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    return fb


def luma01(frame_rgb: np.ndarray) -> np.ndarray:
    f = frame_rgb.astype(np.float32) / 255.0
    return 0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2]


def luma_band(luma: np.ndarray, low: float, high: float, soft: float) -> np.ndarray:
    """1 where luma is inside [low, high], fading over `soft` at each edge (0 = hard)."""
    soft = max(float(soft), 1e-4)
    up = np.clip((luma - (low - soft / 2.0)) / soft, 0.0, 1.0)
    down = np.clip(((high + soft / 2.0) - luma) / soft, 0.0, 1.0)
    return np.minimum(up, down)


def color_match(cv2, frame_rgb: np.ndarray, rgb, similarity: float, soft: float) -> np.ndarray:
    """1 where the chroma is close to `rgb` (brightness ignored, like a chroma key), fading over `soft`."""
    ycc = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2YCrCb).astype(np.float32)
    ref = cv2.cvtColor(np.uint8([[list(rgb)]]), cv2.COLOR_RGB2YCrCb).astype(np.float32)[0, 0]
    d = np.hypot(ycc[..., 1] - ref[1], ycc[..., 2] - ref[2]) / 255.0           # 0 = same chroma
    thr = max(similarity, 1e-4) * 0.5
    soft = max(soft, 1e-4) * 0.5
    return np.clip(1.0 - (d - thr) / soft, 0.0, 1.0)


def build_key(cv2, frame_rgb, mode, *, low, high, soft, color_rgb, similarity, color_soft, invert) -> np.ndarray:
    """Float matte 0..1 (H, W) for one of KEY_MODES."""
    if mode == "none":
        k = np.ones(frame_rgb.shape[:2], np.float32)
        return 1.0 - k if invert else k
    parts = {}
    if "luma" in mode:
        parts["luma"] = luma_band(luma01(frame_rgb), low, high, soft)
    if "color" in mode:
        parts["color"] = color_match(cv2, frame_rgb, color_rgb, similarity, color_soft)
    if mode == "luma AND color":
        k = np.minimum(parts["luma"], parts["color"])
    elif mode == "luma OR color":
        k = np.maximum(parts["luma"], parts["color"])
    else:
        k = parts.get("luma", parts.get("color"))
    return (1.0 - k) if invert else k


def combine(frame: np.ndarray, fb: np.ndarray, insert: np.ndarray, mode: str) -> np.ndarray:
    """Join the live frame to the feedback, only where `insert` (0..1) lets it in. Returns float32 0..255."""
    f, b = frame.astype(np.float32), fb.astype(np.float32)
    if mode == "screen":
        blended = 255.0 - (255.0 - f) * (255.0 - b) / 255.0
    elif mode == "lighten":
        blended = np.maximum(f, b)
    elif mode == "add":
        blended = f + b
    else:                                        # over
        blended = f
    a = insert[..., None]
    return b * (1.0 - a) + blended * a
