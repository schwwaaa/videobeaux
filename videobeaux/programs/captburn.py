from __future__ import annotations
r"""
videobeaux.programs.captburn - module-structured port of captburn v0.1-stable

Entry points expected by cli.py:
  * register_arguments(parser) - declare program-specific flags
  * run(args)                  - execute with combined global+program args

Core kept from captburn v0.1-stable:
  - Styles: popon / painton (\\k word reveal) / rollup
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

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

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
        outline_ass = _hex_to_ass_bgr(self.outline, 0.0)
        back_ass = _hex_to_ass_bgr(self.back, self.back_opacity)
        bold = -1 if self.bold else 0
        italic = -1 if self.italic else 0
        # Angle slot (0) appears after Spacing; order must match Format
        return (
            f"Style: {self.name},{self.fontname},{self.fontsize},"
            f"{primary_ass},&H00FFFFFF,{outline_ass},{back_ass},"
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

def _events_popon(segments: List[Dict[str, Any]]) -> List[Event]:
    evs: List[Event] = []
    for seg in segments:
        text = (seg.get("content") or seg.get("text") or "").strip()
        if not text:
            ws = _extract_words(seg)
            text = " ".join(w["text"] for w in ws)
        st = float(seg.get("start", (_extract_words(seg) or [{"start": 0.0}])[0]["start"]))
        ws2 = _extract_words(seg)
        et = float(seg.get("end", (ws2 or [{"end": st + 2.0}])[-1]["end"]))
        evs.append(Event(start=st, end=et, text=text))
    return evs

def _events_painton(segments: List[Dict[str, Any]], max_line_chars: int = 42) -> List[Event]:
    r"""Paint-on (word-reveal) via ASS karaoke. We pack words into reasonable lines, but reveal per word with \k."""
    evs: List[Event] = []
    for seg in segments:
        words = _extract_words(seg)
        if not words:
            continue
        st = words[0]["start"]
        et = words[-1]["end"]
        line_len = 0
        line_start = st
        buf: List[str] = []

        def flush_line(end_time: float):
            nonlocal buf, line_start
            if not buf:
                return
            text = "".join(buf).strip()
            evs.append(Event(start=line_start, end=end_time, text=text))
            buf = []

        for i, w in enumerate(words):
            wdur = max(0.01, w["end"] - w["start"])  # seconds
            k = int(round(wdur * 100))               # centiseconds for \k
            token = w["text"]
            piece = f"{{\k{k}}}{token} "
            if line_len + len(token) > max_line_chars and buf:
                flush_line(words[i - 1]["end"])      # end previous line
                line_start = w["start"]
                line_len = 0
            buf.append(piece)
            line_len += len(token) + 1
        flush_line(et)
    return evs

def _events_rollup(segments: List[Dict[str, Any]], lines: int = 2, words_per_line: int = 6) -> List[Event]:
    ws_all: List[Dict[str, Any]] = []
    for seg in segments:
        ws_all.extend(_extract_words(seg))
    evs: List[Event] = []
    if not ws_all:
        return evs
    window_tokens: List[str] = []
    window_start = ws_all[0]["start"]
    last_end = window_start
    for i, w in enumerate(ws_all):
        window_tokens.append(w["text"])
        last_end = w["end"]
        if len(window_tokens) % words_per_line == 0:
            window_tokens.append("\n")
        # assemble last N lines
        text_lines: List[str] = []
        cur: List[str] = []
        for tok in window_tokens:
            if tok == "\n":
                text_lines.append(" ".join(cur))
                cur = []
            else:
                cur.append(tok)
        if cur:
            text_lines.append(" ".join(cur))
        text = "\\N".join(text_lines[-lines:])
        start_t = window_start
        end_t = max(last_end, start_t + 0.25)
        evs.append(Event(start=start_t, end=end_t, text=text))
        window_start = w["start"]
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

def register_arguments(parser: argparse.ArgumentParser):
    parser.description = "Generate ASS captions from transcript JSON and burn into video (popon/painton/rollup)."

    # transcript / caption (support both spellings)
    parser.add_argument("-t", "--trans-json", type=str, help="Transcript JSON (default: <input>.json)")
    parser.add_argument("--caption", dest="caption", type=str, help="Existing caption/capton JSON to re-burn")

    # styles/modes
    parser.add_argument("--style", choices=["popon", "painton", "rollup"], default="popon")
    parser.add_argument("--rollup-lines", type=int, default=2)
    parser.add_argument("--words-per-line", type=int, default=6)

    # typography
    parser.add_argument("--font", default="Arial")
    parser.add_argument("--font-size", type=int, default=42)
    parser.add_argument("--bold", action="store_true")
    parser.add_argument("--italic", action="store_true")
    parser.add_argument("--primary", default="#FFFFFF")
    parser.add_argument("--outline", default="#000000")
    parser.add_argument("--outline-width", type=float, default=3.0)
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

            # Build events from transcript
            if args.style == "popon":
                events = _events_popon(segments)
            elif args.style == "painton":
                events = _events_painton(segments)
            else:
                events = _events_rollup(segments, lines=args.rollup_lines, words_per_line=args.words_per_line)

            # Construct style from CLI
            style = Style(
                fontname=args.font,
                fontsize=int(args.font_size),
                primary=args.primary,
                outline=args.outline,
                outline_width=float(args.outline_width),
                shadow=float(args.shadow),
                back=args.back,
                back_opacity=float(args.back_opacity),
                bold=bool(args.bold),
                italic=bool(args.italic),
                scale_x=int(args.scale_x),
                scale_y=int(args.scale_y),
                spacing=float(args.spacing),
                margin_l=(args.margin_l if args.margin_l is not None else 60),
                margin_r=(args.margin_r if args.margin_r is not None else 60),
                margin_v=(args.margin_v if args.margin_v is not None else 40),
                align=int(args.align),
                border_style=int(args.border_style),
            )
    else:
        # Transcript flow (no --caption)
        if not trans_json:
            candidate = in_video.with_suffix(".json")
            if candidate.exists():
                trans_json = candidate
            else:
                raise FileNotFoundError("No transcript JSON provided and <input>.json not found.")
        segments = _load_transcript(trans_json)

        if args.style == "popon":
            events = _events_popon(segments)
        elif args.style == "painton":
            events = _events_painton(segments)
        else:
            events = _events_rollup(segments, lines=args.rollup_lines, words_per_line=args.words_per_line)

        style = Style(
            fontname=args.font,
            fontsize=int(args.font_size),
            primary=args.primary,
            outline=args.outline,
            outline_width=float(args.outline_width),
            shadow=float(args.shadow),
            back=args.back,
            back_opacity=float(args.back_opacity),
            bold=bool(args.bold),
            italic=bool(args.italic),
            scale_x=int(args.scale_x),
            scale_y=int(args.scale_y),
            spacing=float(args.spacing),
            margin_l=(args.margin_l if args.margin_l is not None else 60),
            margin_r=(args.margin_r if args.margin_r is not None else 60),
            margin_v=(args.margin_v if args.margin_v is not None else 40),
            align=int(args.align),
            border_style=int(args.border_style),
        )

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
