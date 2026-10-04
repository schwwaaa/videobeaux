"""
Filter labels for the Photobooth program, kept free of OpenCV/numpy imports so GUI program
discovery stays fast and works even if OpenCV is missing. tests/unit/test_booth_filters.py
checks this list matches the real registry in booth_filters.py.
"""
from __future__ import annotations

BUILTIN_LABELS = [
    "Classic · Negative",
    "Classic · Black & white",
    "Classic · Thermal",
    "Classic · Pop art",
    "Classic · Sketch",
    "Classic · Pixelate",
    "Classic · Glitch",
    "Classic · Kaleidoscope",
    "Classic · Sepia",
    "Classic · Night vision",
    "Slit-scan · Time warp",
    "Slit-scan · Radial",
    "Slit-scan · Vertical",
    "Slit-scan · Wavy",
    "Time · Ghost trails",
    "Time · RGB time-split",
    "Time · Motion only",
    "Retro TV · VHS",
    "Retro TV · CRT",
    "Retro TV · Weak signal",
    "Print & pixel · Halftone",
    "Print & pixel · Game Boy",
    "Print & pixel · 1-bit Mac",
    "Print & pixel · ASCII",
    "Print & pixel · LED wall",
    "Print & pixel · CGA",
    "Print & pixel · Commodore 64",
    "Print & pixel · PICO-8",
    "Art · Comic",
    "Art · Oil paint",
    "Art · Watercolour",
    "Art · Neon edges",
    "Art · Emboss",
    "Art · Blueprint",
    "Colour · Duotone cyan/magenta",
    "Colour · Duotone orange/teal",
    "Colour · Duotone purple/yellow",
    "Colour · Infrared",
    "Colour · Solarize",
    "Colour · Posterize",
    "Colour · Chromatic aberration",
    "Colour · Lomo",
    "Colour · Hue cycle",
    "Warp · Fisheye",
    "Warp · Pinch",
    "Warp · Swirl",
    "Warp · Wavy mirror",
    "Warp · Tunnel",
    "Warp · Little planet",
    "Face · Big head",
    "Face · Tiny head",
    "Face · Big eyes",
    "Face · Face swap",
]

DEFAULT_LABEL = "Classic · Negative"


def all_labels() -> list[str]:
    """Built-in labels plus any user-dropped filters (only imported when that folder has files)."""
    from videobeaux.utils.booth_filters_dir import user_filter_dir
    d = user_filter_dir()
    if d.is_dir() and any(d.glob("*.py")):
        try:
            from videobeaux.utils.booth_filters import build_filters
            return list(build_filters())
        except BaseException:      # noqa: BLE001 — OpenCV missing or a bad user file: fall back to built-ins
            pass
    return list(BUILTIN_LABELS)
