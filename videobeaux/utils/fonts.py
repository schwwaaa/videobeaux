"""
A font file for ffmpeg's drawtext (and PIL). drawtext without `fontfile` needs fontconfig, which the ffmpeg we build
deliberately doesn't include — so every caller passes an explicit file: the bundled DejaVu Sans, else a system font.
"""
from __future__ import annotations

import os
from pathlib import Path

_ASSETS = Path(__file__).resolve().parents[1] / "assets" / "fonts"
_SYSTEM = [
    "/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial.ttf",
    "C:\\Windows\\Fonts\\arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def default_font(bold: bool = False) -> str | None:
    """Path of a usable font file, or None if the machine has none (should not happen: DejaVu ships in assets/)."""
    names = ["DejaVuSans-Bold.ttf", "DejaVuSans.ttf"] if bold else ["DejaVuSans.ttf", "DejaVuSans-Bold.ttf"]
    for n in names:
        p = _ASSETS / n
        if p.exists():
            return str(p)
    for p in _SYSTEM:
        if os.path.exists(p):
            return p
    return None


def drawtext_escape_path(path: str) -> str:
    """Escape a font path for use inside a drawtext filter option."""
    return path.replace("\\", "/").replace(":", r"\:").replace("'", r"\'")
