from __future__ import annotations
r"""
videobeaux.programs.captburn - module-structured port of captburn v0.1-stable

Entry points expected by cli.py:
  * register_arguments(parser) - declare program-specific flags
  * run(args)                  - execute with combined global+program args

Core kept from captburn v0.1-stable:
  - Styles: popon (static) / painton (\\k word reveal + active-word pop)
  - Fixed ASS style field order (includes Angle)
  - PlayResX/Y = actual video size (pixel-true XY / \\move)
  - Event-level alignment enforced (\\anN)
  - Optional rotation (ASS \\frz) via --rotate
  - Writes sidecar .captburn.ass and .captburn.json next to the selected output

Assumptions from videobeaux.cli:
  - Global args: --input, --output, --force are populated and validated
  - --output is normalized to end with .mp4 by the global CLI

Dependencies:
  - ffmpeg & ffprobe on PATH
  - videobeaux.utils.ffmpeg_operations.run_ffmpeg_with_progress
"""
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import argparse
import json
import re
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress, ffmpeg_has_filter

# =====================
# Helpers
# =====================

def _is_capton(obj: Any) -> bool:
    return isinstance(obj, dict) and "style" in obj and "events" in obj

def _coerce_segments(obj: Any) -> List[Dict[str, Any]]:
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict) and "segments" in obj and isinstance(obj["segments"], list):
        return obj["segments"]
    raise ValueError("Not a transcript JSON (list or {segments:[...]})")

def _which(name: str) -> str:
    exe = shutil.which(name)
    if not exe:
        raise RuntimeError(f"{name} not found. Ensure it is installed and on PATH.")
    return exe

def _ffprobe_dims(video: Path) -> Tuple[int, int]:
    ffprobe = _which("ffprobe")
    cmd = [ffprobe, "-v", "error", "-select_streams", "v:0",
           "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", str(video)]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0 or not p.stdout.strip():
        raise RuntimeError(f"ffprobe failed to read dimensions: {video}")
    w, h = p.stdout.strip().split("x")
    return int(w), int(h)

def _sec(ts: float) -> str:
    if ts < 0:
        ts = 0.0
    h = int(ts // 3600)
    m = int((ts % 3600) // 60)
    s = int(ts % 60)
    cs = int(round((ts - int(ts)) * 100))
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"

def _find_font_file(font_name: Optional[str]) -> Optional[str]:
    """
    Best-effort resolution of a font NAME to an actual font FILE, used only
    for PIL-based pixel-width measurement to decide line wrapping — the
    actual burn-in still goes through libass's own system font matching by
    name, unaffected by this. Returns None if nothing usable is found, in
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


def _wrap_words_pixel(words: List[str], font_path: str, font_size: int, max_width_px: int) -> List[List[str]]:
    """Greedy word-wrap using real rendered pixel width. Returns a list of
    lines, each a list of the word strings it contains."""
    font = ImageFont.truetype(font_path, font_size)
    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    space_w = draw.textbbox((0, 0), " ", font=font)[2]

    lines: List[List[str]] = []
    current: List[str] = []
    current_w = 0
    for w in words:
        ww = draw.textbbox((0, 0), w, font=font)[2]
        gap = space_w if current else 0
        if current and current_w + gap + ww > max_width_px:
            lines.append(current)
            current, current_w, gap = [], 0, 0
        current.append(w)
        current_w += gap + ww
    if current:
        lines.append(current)
    return lines or [[]]


def _fit_font_size(
    word_groups: List[List[Dict[str, Any]]],
    font_path: Optional[str],
    requested_size: int,
    max_width_px: int,
    max_lines: int = 2,
    min_size: int = 24,
    step: int = 4,
) -> int:
    """
    Largest font size <= requested_size (down to min_size) at which every
    caption burst wraps into at most max_lines lines at max_width_px —
    mirrors the reference script's per-caption auto-shrink loop, but
    computed once across the whole transcript and applied as a single
    consistent size, since ASS styles are global rather than per-event.
    Returns requested_size unchanged if no font file could be resolved for
    measurement (nothing to fit against).
    """
    if not font_path:
        return requested_size

    size = requested_size
    while size > min_size:
        fits = True
        for group in word_groups:
            words = [w["text"] for w in group]
            if not words:
                continue
            if len(_wrap_words_pixel(words, font_path, size, max_width_px)) > max_lines:
                fits = False
                break
        if fits:
            return size
        size -= step
    return max(size, min_size)


def _group_words_fixed(
    segments: List[Dict[str, Any]],
    words_per_caption: int,
    uppercase: bool,
) -> List[List[Dict[str, Any]]]:
    """
    Flattens every segment's words into one continuous stream and re-chunks
    it into fixed-size bursts, ignoring the original sentence boundaries —
    matching the reference script's group_words(): short, punchy multi-word
    bursts on screen at a time rather than a whole (possibly long) sentence,
    which is what actually gives short-form caption tools their rhythm and
    keeps the fitted font size comfortably large instead of collapsing to
    fit a long run-on line.
    """
    all_words: List[Dict[str, Any]] = []
    for seg in segments:
        all_words.extend(_extract_words(seg))
    if uppercase:
        all_words = [{**w, "text": w["text"].upper()} for w in all_words]

    groups: List[List[Dict[str, Any]]] = []
    for i in range(0, len(all_words), max(1, words_per_caption)):
        chunk = all_words[i:i + words_per_caption]
        if chunk:
            groups.append(chunk)
    return groups


def _hex_to_ass_bgr(hex_rgb: str, alpha: float = 0.0) -> str:
    hx = hex_rgb.strip()
    if hx.startswith('#'):
        hx = hx[1:]
    if len(hx) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", hx):
        raise ValueError(f"Invalid hex color: {hex_rgb}")
    r = int(hx[0:2], 16)
    g = int(hx[2:4], 16)
    b = int(hx[4:6], 16)
    a = int(round(alpha * 255))
    return f"&H{a:02X}{b:02X}{g:02X}{r:02X}"

# =====================
# Data classes
# =====================

@dataclass
class Style:
    name: str = "CaptBurn"
    fontname: str = "Arial"
    fontsize: int = 42
    primary: str = "#FFFFFF"
    # "Already spoken" color for painton's \k karaoke sweep — words switch
    # from highlight -> primary is backwards from how it reads; see
    # to_ass_style_line()'s comment for the actual ASS semantics.
    highlight: str = "#FFE500"
    outline: str = "#000000"
    outline_width: float = 3.0
    shadow: float = 0.0
    back: str = "#000000"
    back_opacity: float = 0.0
    bold: bool = False
    italic: bool = False
    scale_x: int = 100
    scale_y: int = 100
    spacing: float = 0.0
    margin_l: int = 60
    margin_r: int = 60
    margin_v: int = 40
    align: int = 2
    border_style: int = 1

    def to_ass_style_line(self) -> str:
        primary_ass = _hex_to_ass_bgr(self.primary, 0.0)
        highlight_ass = _hex_to_ass_bgr(self.highlight, 0.0)
        outline_ass = _hex_to_ass_bgr(self.outline, 0.0)
        back_ass = _hex_to_ass_bgr(self.back, self.back_opacity)
        bold = -1 if self.bold else 0
        italic = -1 if self.italic else 0
        # SecondaryColour is what ASS's \k karaoke effect actually uses:
        # a word renders in SecondaryColour until the karaoke timer reaches
        # it, then switches to PrimaryColour and stays there (a progressive
        # "sweep" highlight, not a single word flashing then reverting).
        # This was previously hardcoded to opaque white, identical to the
        # usual primary — meaning \k's timing data existed but was
        # completely invisible. Swapping in a real highlight color here is
        # what actually makes painton's word-reveal visible at all.
        # Angle slot (0) appears after Spacing; order must match Format
        return (
            f"Style: {self.name},{self.fontname},{self.fontsize},"
            f"{highlight_ass},{primary_ass},{outline_ass},{back_ass},"
            f"{bold},{italic},0,0,100,100,{self.spacing},0,"
            f"{self.border_style},{self.outline_width},{self.shadow},{self.align},"
            f"{self.margin_l},{self.margin_r},{self.margin_v},1"
        )

@dataclass
class Event:
    start: float
    end: float
    text: str
    pos: Optional[Tuple[int, int]] = None
    move: Optional[Tuple[int, int, int, int, int, int]] = None

    def to_ass_dialogue(self, style_name: str, rotate: Optional[float] = None, align: Optional[int] = None) -> str:
        start_s = _sec(self.start)
        end_s = _sec(self.end)
        tags: List[str] = []
        if align is not None:
            tags.append(f"\\an{align}")
        if self.pos:
            x, y = self.pos
            tags.append(f"\\pos({x},{y})")
        if self.move:
            x1, y1, x2, y2, t1, t2 = self.move
            tags.append(f"\\move({x1},{y1},{x2},{y2},{t1},{t2})")
        if rotate is not None:
            tags.append(f"\\frz{rotate}")
        prefix = "{" + "".join(tags) + "}" if tags else ""
        safe_text = self.text.replace("\n", "\\N")
        return f"Dialogue: 0,{start_s},{end_s},{style_name},,0,0,0,,{prefix}{safe_text}\n"

@dataclass
class Caption:
    version: str
    style: Style
    events: List[Event]

    def to_json(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "style": asdict(self.style),
            "events": [
                {
                    "start": e.start,
                    "end": e.end,
                    "text": e.text,
                    **({"pos": list(e.pos)} if e.pos else {}),
                    **({"move": list(e.move)} if e.move else {}),
                }
                for e in self.events
            ],
        }

# =====================
# Transcript -> events
# =====================

def _load_transcript(path: Path) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "segments" in data:
        data = data["segments"]
    if not isinstance(data, list):
        raise ValueError("Transcript JSON must be an array or have a 'segments' key.")
    return data

def _extract_words(seg: Dict[str, Any]) -> List[Dict[str, Any]]:
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

def _events_popon(
    groups: List[List[Dict[str, Any]]],
    font_path: Optional[str] = None,
    font_size: int = 42,
    max_width_px: Optional[int] = None,
    text_color_ass: Optional[str] = None,
) -> List[Event]:
    # popon has no \k tags, so it never advances past SecondaryColour on its
    # own — and the style's PrimaryColour slot is dedicated to painton's
    # highlight color (see Style.to_ass_style_line()), which would leave
    # popon's static text rendering entirely in the highlight color instead
    # of the intended plain text color. An explicit \1c override corrects
    # that for these non-karaoke events.
    color_prefix = f"{{\\1c{text_color_ass}}}" if text_color_ass else ""
    evs: List[Event] = []
    for group in groups:
        if not group:
            continue
        text = " ".join(w["text"] for w in group)
        st = group[0]["start"]
        et = group[-1]["end"]

        if font_path and max_width_px:
            wrapped = _wrap_words_pixel([w["text"] for w in group], font_path, font_size, max_width_px)
            text = "\\N".join(" ".join(line) for line in wrapped)

        evs.append(Event(start=st, end=et, text=color_prefix + text))
    return evs

def _events_painton(
    groups: List[List[Dict[str, Any]]],
    font_path: Optional[str] = None,
    font_size: int = 42,
    max_width_px: Optional[int] = None,
    max_line_chars: int = 42,
) -> List[Event]:
    r"""
    Paint-on (word-reveal) via ASS karaoke \k timing: each caption burst
    (a small fixed-size group of words, not a whole sentence — see
    _group_words_fixed) is wrapped into lines that actually fit the video
    width (real pixel measurement when a font file could be resolved, else
    a character-count estimate as a fallback), with every word tagged with
    its own \k duration so the style's highlight color sweeps across in
    sync with when it's spoken. All lines of one burst are combined into a
    SINGLE event (joined with \N) so the whole burst stays visible together
    while the highlight sweeps through it, rather than each wrapped line
    flashing on and off independently.

    Each word also renders ~18% larger for its own full spoken duration —
    matching the reference script's per-word emphasis, which is a binary
    per-frame state (word is either "active size" or "normal size" for its
    whole duration, no tweening at all). The first attempt at this used a
    slow ~90ms \t() tween to grow and shrink the word, which is NOT what
    the reference does — animating a run's size over many frames makes
    libass continuously reflow the words around it, which read as the
    whole line jittering. The fix isn't to avoid sizing the word at all;
    it's to snap it near-instantly (a few ms, effectively one frame) to its
    enlarged size at word-start and hold it there for the word's entire
    duration, snapping back just as fast at word-end — a hard cut, exactly
    like the reference's discrete state, not a continuous animation. A
    neighboring word can still nudge a pixel or two at the exact instant an
    adjacent word's size snaps (ASS reflows the shared line either way),
    but it now happens once, synchronized with the same instant the \k
    color already changes — not as an independent multi-frame wobble.
    """
    evs: List[Event] = []

    def word_piece(w: Dict[str, Any], ev_start: float) -> str:
        wdur = max(0.01, w["end"] - w["start"])
        k = int(round(wdur * 100))
        t1 = max(0, int(round((w["start"] - ev_start) * 1000)))
        t_end = max(t1 + 2, int(round((w["end"] - ev_start) * 1000)))
        ramp = max(1, min(30, (t_end - t1) // 3))
        # \fscy (vertical) only — \fscx changes the word's rendered width,
        # and because this style is center-aligned, ANY word's width
        # change makes ASS recenter the WHOLE line around its new total
        # width, shoving every other word sideways. Confirmed directly:
        # swapping which word was "big" shifted an untouched neighboring
        # word ~15-20px sideways. \fscy doesn't change advance width, so
        # centering is untouched — the trade-off is the pop is a pure
        # vertical grow rather than a uniform size increase.
        grow = f"\\t({t1},{t1 + ramp},\\fscy118)"
        shrink = f"\\t({max(t1 + ramp, t_end - ramp)},{t_end},\\fscy100)"
        return f"{{\\k{k}{grow}{shrink}}}{w['text']} "

    for group in groups:
        if not group:
            continue
        ev_start = group[0]["start"]
        ev_end = group[-1]["end"]

        if font_path and max_width_px:
            wrapped = _wrap_words_pixel([w["text"] for w in group], font_path, font_size, max_width_px)
            line_lengths = [len(line) for line in wrapped if line]
        else:
            line_lengths = None

        if line_lengths:
            idx = 0
            line_texts: List[str] = []
            for n in line_lengths:
                line_words = group[idx: idx + n]
                idx += n
                if not line_words:
                    continue
                pieces = [word_piece(w, ev_start) for w in line_words]
                line_texts.append("".join(pieces).strip())
            if line_texts:
                evs.append(Event(start=ev_start, end=ev_end, text="\\N".join(line_texts)))
        else:
            # Fallback: character-count heuristic (no font file could be
            # resolved for measurement) — still combined into one event.
            line_len = 0
            buf: List[str] = []
            line_texts = []

            def flush_line():
                nonlocal buf, line_len
                if buf:
                    line_texts.append("".join(buf).strip())
                buf = []
                line_len = 0

            for w in group:
                token = w["text"]
                piece = word_piece(w, ev_start)
                if line_len + len(token) > max_line_chars and buf:
                    flush_line()
                buf.append(piece)
                line_len += len(token) + 1
            flush_line()
            if line_texts:
                evs.append(Event(start=ev_start, end=ev_end, text="\\N".join(line_texts)))
    return evs

# =====================
# ASS build + encode
# =====================

def _build_ass(style: Style, events: List[Event], playres_x: int, playres_y: int, rotate: Optional[float]) -> str:
    header = (
        "[Script Info]\n"
        "; Script generated by captburn (module)\n"
        "ScriptType: v4.00+\n"
        "WrapStyle: 2\n"
        "ScaledBorderAndShadow: yes\n"
        f"PlayResX: {playres_x}\n"
        f"PlayResY: {playres_y}\n\n"
        "[V4+ Styles]\n"
        "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
        "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,"
        "Alignment,MarginL,MarginR,MarginV,Encoding\n"
        f"{style.to_ass_style_line()}\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    lines = [header]
    for ev in events:
        lines.append(ev.to_ass_dialogue(style.name, rotate=rotate, align=style.align))
    return "".join(lines)

# =====================
# Public API expected by videobeaux/cli.py
# =====================

GUI_METADATA = {
    'args': {
        'primary': {'type': 'color'},
        'highlight': {'type': 'color'},
        'outline': {'type': 'color'},
        'back': {'type': 'color'},
    }
}

def register_arguments(parser: argparse.ArgumentParser):
    parser.description = "Generate ASS captions from transcript JSON and burn into video (popon/painton)."

    # transcript / caption (support both spellings)
    parser.add_argument("-t", "--trans-json", type=str, help="Transcript JSON (default: <input>.json)")
    parser.add_argument("--caption", dest="caption", type=str, help="Existing caption/capton JSON to re-burn")

    # styles/modes
    parser.add_argument("--style", choices=["popon", "painton"], default="popon")

    # typography
    parser.add_argument("--font", default="Arial")
    parser.add_argument("--font-size", type=int, default=42)
    parser.add_argument("--words-per-caption", type=int, default=4,
                        help="Words shown per caption burst for popon/painton (default: 4) — short, "
                             "punchy multi-word groups like short-form caption tools use, instead of "
                             "displaying a whole (possibly long) transcript sentence at once.")
    parser.add_argument("--no-uppercase", action="store_true",
                        help="Keep the transcript's original case instead of forcing UPPERCASE "
                             "(short-form caption tools default to uppercase).")
    parser.add_argument("--no-bold", action="store_true",
                        help="Use the font's regular weight instead of bold (short-form caption "
                             "tools default to bold).")
    parser.add_argument("--italic", action="store_true")
    parser.add_argument("--primary", default="#FFFFFF")
    parser.add_argument("--highlight", default="#FFE500",
                        help="Active-word highlight color for painton's \\k karaoke sweep.")
    parser.add_argument("--outline", default="#000000")
    parser.add_argument("--outline-width", type=float, default=None,
                        help="Outline/stroke width in px. Default: auto-scaled to the fitted font "
                             "size (~11%%), matching short-form caption tools' bold outline.")
    parser.add_argument("--shadow", type=float, default=0.0)
    parser.add_argument("--back", default="#000000")
    parser.add_argument("--back-opacity", type=float, default=0.0)
    parser.add_argument("--scale-x", type=int, default=100)
    parser.add_argument("--scale-y", type=int, default=100)
    parser.add_argument("--spacing", type=float, default=0.0)
    parser.add_argument("--rotate", type=float, help="Rotation degrees (ASS \\frz)")

    # placement / motion
    parser.add_argument("--margin-l", type=int, default=None, help="Left margin (px)")
    parser.add_argument("--margin-r", type=int, default=None, help="Right margin (px)")
    parser.add_argument("--margin-v", type=int, default=None, help="Vertical margin (px)")
    parser.add_argument("--align", type=int, default=2, help="ASS alignment 1..9")
    parser.add_argument("--border-style", type=int, default=1, help="1=outline, 3=opaque box")
    parser.add_argument("--x", type=int, help="Override X position (pixels)")
    parser.add_argument("--y", type=int, help="Override Y position (pixels)")
    parser.add_argument("--move", type=str, help="ASS move x1,y1,x2,y2,t1ms,t2ms")

    # encoding
    parser.add_argument("--vcodec", default="libx264")
    parser.add_argument("--crf", type=int, default=18)
    parser.add_argument("--preset", default="medium")

def _build_style_and_events(args, segments: List[Dict[str, Any]], w: int, h: int) -> Tuple[Style, List[Event]]:
    """
    Shared by both of run()'s transcript-flow branches (fresh --trans-json
    and a --caption that turns out to be a transcript, not a capton). Resolves
    a font file for pixel measurement, fits a font size that actually keeps
    lines within the video width, builds events with that fit applied, and
    constructs the matching Style.
    """
    uppercase = not bool(getattr(args, "no_uppercase", False))
    bold = not bool(getattr(args, "no_bold", False))
    words_per_caption = int(getattr(args, "words_per_caption", 4))

    font_path = _find_font_file(args.font)
    max_width_px = int(w * 0.9)  # small safety margin vs. libass's own metrics

    groups = _group_words_fixed(segments, words_per_caption, uppercase)
    fitted_size = _fit_font_size(groups, font_path, int(args.font_size), max_width_px, max_lines=2)
    if font_path is None:
        print("⚠️ Could not locate a font file for pixel-accurate caption wrapping — falling back to a rougher estimate.")
    elif fitted_size != int(args.font_size):
        print(f"ℹ️  Shrunk caption font {args.font_size} → {fitted_size}px to keep lines within the frame.")

    primary_ass = _hex_to_ass_bgr(args.primary, 0.0)

    if args.style == "popon":
        events = _events_popon(groups, font_path=font_path, font_size=fitted_size, max_width_px=max_width_px, text_color_ass=primary_ass)
    else:
        events = _events_painton(groups, font_path=font_path, font_size=fitted_size, max_width_px=max_width_px)

    outline_width = args.outline_width
    if outline_width is None:
        # Proportional to the fitted size rather than a fixed px value, so
        # the bold-outline look holds whether the auto-shrink kept the
        # requested size or knocked it down.
        outline_width = max(2.0, fitted_size * 0.11)

    margin_v = args.margin_v
    if margin_v is None:
        # Anchor the caption block's vertical CENTER around ~67% of the
        # frame height (matching the reference script's fixed anchor)
        # instead of sitting flush against the bottom edge. ASS's MarginV
        # for an2 (bottom-center) is measured up from the bottom edge, so
        # back-solve for it assuming a representative ~1.5-line block at
        # the fitted size.
        line_height = fitted_size * 1.28
        margin_v = max(20, int(h * 0.33 - line_height * 0.75))

    style = Style(
        fontname=args.font,
        fontsize=fitted_size,
        primary=args.primary,
        highlight=getattr(args, "highlight", "#FFE500"),
        outline=args.outline,
        outline_width=float(outline_width),
        shadow=float(args.shadow),
        back=args.back,
        back_opacity=float(args.back_opacity),
        bold=bold,
        italic=bool(args.italic),
        scale_x=int(args.scale_x),
        scale_y=int(args.scale_y),
        spacing=float(args.spacing),
        margin_l=(args.margin_l if args.margin_l is not None else 60),
        margin_r=(args.margin_r if args.margin_r is not None else 60),
        margin_v=int(margin_v),
        align=int(args.align),
        border_style=int(args.border_style),
    )
    return style, events


def run(args) -> None:
    # 1) Resolve IO paths from global CLI
    in_video = Path(args.input)
    out_video = Path(args.output)
    out_video.parent.mkdir(parents=True, exist_ok=True)

    # 2) Probe dimensions for PlayRes
    try:
        w, h = _ffprobe_dims(in_video)
        print(f"📐 Video dimensions: {w}x{h}")
    except Exception as e:
        print("⚠️ ffprobe failed, using fallback 1920x1080:", e)
        w, h = (1920, 1080)

    # 3) Build events and style
    trans_json: Optional[Path] = Path(args.trans_json) if getattr(args, "trans_json", None) else None
    caption_in: Optional[Path] = Path(args.caption) if getattr(args, "caption", None) else None

    events: List[Event] = []
    style: Style

    if caption_in and caption_in.exists():
        with open(caption_in, "r", encoding="utf-8") as f:
            capraw = json.load(f)

        if _is_capton(capraw):
            # True capton JSON (style + events)
            style = Style(**capraw.get("style", {}))
            for ed in capraw.get("events", []):
                pos = tuple(ed["pos"]) if "pos" in ed else None
                move = tuple(ed["move"]) if "move" in ed else None
                events.append(Event(
                    start=float(ed["start"]),
                    end=float(ed["end"]),
                    text=str(ed["text"]),
                    pos=pos,
                    move=move
                ))
        else:
            # Not a capton -> treat as transcript (list or {segments:[...]})
            try:
                segments = _coerce_segments(capraw)
            except Exception:
                # Fall back to trans_json or default <input>.json if this file isn't a transcript either
                segments = None

            if segments is None:
                if not trans_json:
                    candidate = in_video.with_suffix(".json")
                    if candidate.exists():
                        trans_json = candidate
                    else:
                        raise FileNotFoundError(
                            "Provided --caption is neither a capton nor a transcript; "
                            "and no <input>.json transcript was found."
                        )
                segments = _load_transcript(trans_json)

            style, events = _build_style_and_events(args, segments, w, h)
    else:
        # Transcript flow (no --caption)
        if not trans_json:
            candidate = in_video.with_suffix(".json")
            if candidate.exists():
                trans_json = candidate
            else:
                raise FileNotFoundError("No transcript JSON provided and <input>.json not found.")
        segments = _load_transcript(trans_json)

        style, events = _build_style_and_events(args, segments, w, h)

    # Optional overrides applied to all events
    if getattr(args, "x", None) is not None and getattr(args, "y", None) is not None:
        for e in events:
            e.pos = (int(args.x), int(args.y))
    if getattr(args, "move", None):
        try:
            x1, y1, x2, y2, t1, t2 = [int(v) for v in args.move.split(",")]
        except Exception:
            raise ValueError("--move must be 'x1,y1,x2,y2,t1ms,t2ms'")
        for e in events:
            e.move = (x1, y1, x2, y2, t1, t2)

    # 4) Write sidecars next to the chosen output (always)
    ass_path = out_video.with_suffix(".captburn.ass")
    caption_path = out_video.with_suffix(".captburn.json")

    ass_text = _build_ass(style, events, w, h, rotate=getattr(args, "rotate", None))
    ass_path.write_text(ass_text, encoding="utf-8")

    cap = Caption(version="1.0.2", style=style, events=events)
    with open(caption_path, "w", encoding="utf-8") as f:
        json.dump(cap.to_json(), f, ensure_ascii=False, indent=2)

    print(f"📝 ASS  → {ass_path}")
    print(f"🧾 Caption JSON → {caption_path}")

    # 5) Encode via ffmpeg (delegated to platform helper)
    if not ffmpeg_has_filter("ass"):
        raise SystemExit(
            "❌ This ffmpeg build has no 'ass' filter (needs libass), which burning ASS "
            "captions requires. The caption files were still written (see above). Install or "
            "point PATH at an ffmpeg built with --enable-libass — or use Kinetic Captions, "
            "which renders captions itself and doesn't need libass. On macOS: `brew install ffmpeg-full` (keg-only — the GUI picks it up automatically; for the CLI run with PATH=/opt/homebrew/opt/ffmpeg-full/bin:$PATH)."
        )
    vf = f"ass={ass_path.as_posix()}"
    cmd = [
        "ffmpeg",
        "-i", str(in_video),
        "-vf", vf,
        "-c:v", args.vcodec,
        "-crf", str(args.crf),
        "-preset", args.preset,
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(out_video),
    ]

    command = (cmd[:1] + ["-y"] + cmd[1:]) if getattr(args, "force", False) else cmd
    run_ffmpeg_with_progress(command, str(in_video), str(out_video))

    print(f"✅ Burned → {out_video}")
