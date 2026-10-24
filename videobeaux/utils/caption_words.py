"""
Shared helpers for the caption programs (Captburn, Kinetic Captions): read word timings from a Vosk transcript JSON and
find a font file for pixel measurement.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional


def is_capton(obj: Any) -> bool:
    """True for a legacy captburn "capton" file (style + events) rather than a transcript."""
    return isinstance(obj, dict) and "style" in obj and "events" in obj


def coerce_segments(obj: Any) -> List[Dict[str, Any]]:
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict) and "segments" in obj and isinstance(obj["segments"], list):
        return obj["segments"]
    raise ValueError("Not a transcript JSON (list or {segments:[...]})")


def find_font_file(font_name: Optional[str]) -> Optional[str]:
    """
    Best-effort resolution of a font NAME to an actual font FILE, used only
    for PIL-based pixel-width measurement to decide line wrapping — the
    renderer uses the same file. Returns None if nothing usable is found, in
    which case callers fall back to a cruder character-count estimate
    rather than crashing.
    """
    candidates = []
    if font_name:
        if font_name.lower().endswith((".ttf", ".otf", ".ttc")) and Path(font_name).exists():
            return font_name
        candidates += [
            f"/System/Library/Fonts/Supplemental/{font_name} Bold.ttf",
            f"/System/Library/Fonts/Supplemental/{font_name}.ttf",
            f"/Library/Fonts/{font_name} Bold.ttf",
            f"/Library/Fonts/{font_name}.ttf",
            f"C:\\Windows\\Fonts\\{font_name.lower()}.ttf",
            f"C:\\Windows\\Fonts\\{font_name.lower()}bd.ttf",
        ]
    candidates += [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
    ]
    for path in candidates:
        if path and Path(path).exists():
            return path
    return None


def extract_words(seg: Dict[str, Any]) -> List[Dict[str, Any]]:
    words = seg.get("words")
    if isinstance(words, list) and words:
        out: List[Dict[str, Any]] = []
        for w in words:
            txt = (w.get("word") or w.get("text") or str(w)).strip()
            if not txt:
                continue
            out.append({
                "text": txt,
                "start": float(w.get("start", seg.get("start", 0.0))),
                "end": float(w.get("end", seg.get("end", 0.0))),
            })
        return out
    content = (seg.get("content") or seg.get("text") or "").strip()
    tokens = [t for t in re.split(r"\s+", content) if t]
    st = float(seg.get("start", 0.0))
    et = float(seg.get("end", st + max(1.0, len(tokens) * 0.25)))
    dur = max(0.01, et - st)
    out: List[Dict[str, Any]] = []
    if tokens:
        step = dur / len(tokens)
        for i, tok in enumerate(tokens):
            out.append({"text": tok, "start": st + i * step, "end": st + (i + 1) * step})
    return out
