"""Lazy OpenCV import.

Program modules are imported by GUI discovery, so cv2 must never be imported at
module top level — call require_cv2() inside run() instead. That way a missing
or broken OpenCV install only affects the programs that actually need it.
"""
from __future__ import annotations


def require_cv2():
    try:
        import cv2
        return cv2
    except ImportError:
        raise SystemExit(
            "❌ This program needs OpenCV, which isn't installed.\n"
            "   Install it with:  pip install \"opencv-python-headless>=4.10,<5\""
        )


def hex_to_rgb(text: str, default=(0, 255, 136)):
    """'#RRGGBB' / '#RGB' -> (r, g, b); `default` if unparseable."""
    s = (text or "").strip().lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    try:
        return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
    except (ValueError, IndexError):
        return default
