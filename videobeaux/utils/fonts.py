"""
Fonts for the caption programs and ffmpeg's drawtext.

* `default_font()` — a usable font file. drawtext without `fontfile` needs fontconfig, which the ffmpeg we build deliberately
  doesn't include, so every caller passes an explicit file: the bundled DejaVu Sans, else a system font.
* `font_catalog()` — every font family the app can use: the open-licensed set bundled in assets/fonts/ (same on every machine,
  see tools/fetch-fonts.py) plus the fonts installed on this computer. Each entry names a regular file and, when there is one,
  a bold file. The GUI's font picker is built from `python -m videobeaux.utils.fonts --json`.
* `resolve_font(name_or_path)` — a family name ("Anton", "Arial") or a path to a .ttf/.otf → the file to draw with.
"""
from __future__ import annotations

import json
import os
import sys
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


# ───────────────────────── catalog ─────────────────────────
FONT_EXTS = {".ttf", ".otf", ".ttc"}
_SKIP_FAMILY = ("symbol", "dingbat", "webdings", "wingdings", "emoji", "braille", "bitmap", "lastresort", "marlett", "ornament")
_REGULAR_STYLES = ("regular", "book", "roman", "normal", "medium")
_catalog_cache: list | None = None


def _system_dirs() -> list[Path]:
    home = Path.home()
    if sys.platform == "darwin":
        return [Path("/System/Library/Fonts"), Path("/System/Library/Fonts/Supplemental"), Path("/Library/Fonts"), home / "Library/Fonts"]
    if sys.platform.startswith("win"):
        win = Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts"
        local = Path(os.environ.get("LOCALAPPDATA", str(home / "AppData/Local"))) / "Microsoft/Windows/Fonts"
        return [win, local]
    return [Path("/usr/share/fonts"), Path("/usr/local/share/fonts"), home / ".fonts", home / ".local/share/fonts"]


def _cache_file() -> Path:
    base = Path(os.environ.get("VIDEOBEAUX_CACHE_DIR") or (Path.home() / ".videobeaux"))
    return base / "fonts-cache.json"


def _faces(path: Path):
    """(family, style) for each face in a font file (a .ttc holds several). Unreadable files yield nothing."""
    from PIL import ImageFont
    i = 0
    while i < 32:
        try:
            f = ImageFont.truetype(str(path), 12, index=i)
            fam, style = f.getname()
        except Exception:
            return
        yield i, (fam or "").strip(), (style or "").strip()
        if path.suffix.lower() != ".ttc":
            return
        i += 1


def _scan(dirs: list[Path], bundled: bool) -> dict:
    fams: dict = {}
    for d in dirs:
        if not d.is_dir():
            continue
        for p in sorted(d.rglob("*")):
            if p.suffix.lower() not in FONT_EXTS or p.name.startswith("."):
                continue
            for _idx, fam, style in _faces(p):
                if not fam or fam.startswith(".") or any(k in fam.lower() for k in _SKIP_FAMILY):
                    continue
                st = style.lower()
                if "italic" in st or "oblique" in st:
                    continue
                e = fams.setdefault(fam, {"family": fam, "regular": None, "bold": None, "bundled": bundled})
                if st == "bold":
                    e["bold"] = e["bold"] or str(p)
                elif st in _REGULAR_STYLES or e["regular"] is None:
                    if e["regular"] is None or st in ("regular", "book", "roman"):
                        e["regular"] = str(p)
    for e in fams.values():
        e["regular"] = e["regular"] or e["bold"]
    return {k: v for k, v in fams.items() if v["regular"]}


def font_catalog(refresh: bool = False) -> list[dict]:
    """Bundled families first (A→Z), then the families installed on this computer (A→Z)."""
    global _catalog_cache
    if _catalog_cache is not None and not refresh:
        return _catalog_cache
    dirs = _system_dirs()
    stamp = {str(d): (d.stat().st_mtime if d.is_dir() else 0) for d in dirs}
    stamp["bundled"] = _ASSETS.stat().st_mtime if _ASSETS.is_dir() else 0
    stamp["bundled_n"] = len(list(_ASSETS.glob("*.ttf"))) if _ASSETS.is_dir() else 0
    cf = _cache_file()
    if not refresh:
        try:
            data = json.loads(cf.read_text(encoding="utf-8"))
            if data.get("stamp") == stamp and all(os.path.exists(e["regular"]) for e in data["fonts"][:20]):
                _catalog_cache = data["fonts"]
                return _catalog_cache
        except Exception:
            pass
    bundled = _scan([_ASSETS], True)
    system = {k: v for k, v in _scan(dirs, False).items() if k not in bundled and k.lower() not in {b.lower() for b in bundled}}
    fonts = sorted(bundled.values(), key=lambda e: e["family"].lower()) + sorted(system.values(), key=lambda e: e["family"].lower())
    _catalog_cache = fonts
    try:
        cf.parent.mkdir(parents=True, exist_ok=True)
        cf.write_text(json.dumps({"stamp": stamp, "fonts": fonts}), encoding="utf-8")
    except Exception:
        pass
    return fonts


def resolve_font(name_or_path: str | None, bold: bool = True) -> str | None:
    """A family name or a font-file path → the file to draw with (bold when asked and available). Falls back to DejaVu."""
    if name_or_path:
        p = Path(str(name_or_path)).expanduser()
        if p.suffix.lower() in FONT_EXTS and p.exists():
            return str(p)
        want = str(name_or_path).strip().lower()
        for e in font_catalog():
            if e["family"].lower() == want:
                return (e["bold"] if bold and e["bold"] else e["regular"])
        for e in font_catalog():                      # "Arial Bold" / "Anton Regular" style names
            fam = e["family"].lower()
            if want.startswith(fam + " "):
                rest = want[len(fam):].strip()
                return e["bold"] if "bold" in rest and e["bold"] else e["regular"]
    return default_font(bold)


if __name__ == "__main__":
    if "--json" in sys.argv:
        print(json.dumps(font_catalog(refresh="--refresh" in sys.argv), ensure_ascii=False))
    else:
        for e in font_catalog():
            print(("★ " if e["bundled"] else "  ") + e["family"], "|", e["regular"], "|", e["bold"] or "-")
