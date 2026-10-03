"""Named color palettes + helpers shared by the dithering programs."""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np

PALETTES: dict[str, list[str]] = {
    "bw":             ["000000", "FFFFFF"],
    "gameboy":        ["0F380F", "306230", "8BAC0F", "9BBC0F"],
    "cga_pink":       ["000000", "55FFFF", "FF55FF", "FFFFFF"],
    "cga_green":      ["000000", "55FF55", "FF5555", "FFFF55"],
    "ega16":          ["000000", "0000AA", "00AA00", "00AAAA", "AA0000", "AA00AA", "AA5500", "AAAAAA",
                       "555555", "5555FF", "55FF55", "55FFFF", "FF5555", "FF55FF", "FFFF55", "FFFFFF"],
    "c64":            ["000000", "FFFFFF", "880000", "AAFFEE", "CC44CC", "00CC55", "0000AA", "EEEE77",
                       "DD8855", "664400", "FF7777", "333333", "777777", "AAFF66", "0088FF", "BBBBBB"],
    "pico8":          ["000000", "1D2B53", "7E2553", "008751", "AB5236", "5F574F", "C2C3C7", "FFF1E8",
                       "FF004D", "FFA300", "FFEC27", "00E436", "29ADFF", "83769C", "FF77A8", "FFCCAA"],
    "amber":          ["000000", "331A00", "804D00", "FFB000"],
    "green_phosphor": ["000000", "003300", "008800", "33FF33"],
    "sepia":          ["1A0F08", "5C3A21", "A67C52", "E8D5B0"],
    "virtualboy":     ["000000", "550000", "AA0000", "FF0000"],
}

PALETTE_CHOICES = list(PALETTES) + ["custom"]

_HEX = re.compile(r"^#?([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$")


def parse_hex_list(text: str) -> list[str]:
    """'#ff0000, 00ff00 ,#00f' -> ['FF0000', '00FF00', '0000FF']. Raises ValueError on junk."""
    out = []
    for tok in re.split(r"[,\s]+", (text or "").strip()):
        if not tok:
            continue
        m = _HEX.match(tok)
        if not m:
            raise ValueError(f"'{tok}' is not a hex color (use #RRGGBB or #RGB)")
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        out.append(h.upper())
    return out


def resolve_palette(name: str, custom: str | None = None) -> list[str]:
    if name == "custom":
        colors = parse_hex_list(custom or "")
        if len(colors) < 2:
            raise ValueError("Custom palette needs at least 2 colors, e.g. '#000000, #ff6847, #ffffff'")
        return colors
    if name not in PALETTES:
        raise ValueError(f"Unknown palette '{name}'. Choices: {', '.join(PALETTE_CHOICES)}")
    return PALETTES[name]


def to_array(hexes: list[str]) -> np.ndarray:
    return np.array([[int(h[i:i + 2], 16) for i in (0, 2, 4)] for h in hexes], dtype=np.uint8)


def write_palette_png(hexes: list[str], path) -> Path:
    """
    A 16x16 image holding the palette (paletteuse requires exactly 256 pixels).
    Colors repeat cyclically to fill it — duplicates don't change which palette
    entry is nearest, so a 2-color palette still yields exactly 2 colors.
    """
    from PIL import Image
    path = Path(path)
    colors = to_array(hexes)
    full = colors[np.arange(256) % len(colors)].reshape(16, 16, 3)
    Image.fromarray(full).save(path)
    return path
