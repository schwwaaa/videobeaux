#!/usr/bin/env python3
r"""
CAPTBURN — vintage titler‑style caption burner

Single‑file Python CLI that:
  1) Ingests a video (or a folder of videos) and a JSON transcription
  2) Builds an ASS subtitle file in one of three styles: pop‑on, paint‑on, roll‑up
  3) Lets you customize font, size, colors, outline, shadow, box bg, XY or motion, margins, etc.
  4) Writes a companion "capton" JSON (events + styles) to allow fast re‑burns
  5) Burns captions into the video with ffmpeg (libass)

Tested on macOS (Apple Silicon + Intel) with Homebrew ffmpeg built with libass.

Usage examples (quick):
  # Single video + loose JSON transcript
  python captburn.py -i media/motivation.mp4 -t media/motivation.json \
    --style popon --font "DM Sans" --font-size 42 --primary "#FFFFFF" \
    --outline "#000000" --outline-width 3 --back "#000000" --back-opacity 0.5 \
    --align 2 --margin-v 80

  # Paint‑on (word‑reveal) using word timings
  python captburn.py -i media/clip.mp4 -t media/clip.json --style painton \
    --font "IBM Plex Sans" --font-size 40 --align 2

  # Roll‑up style (2 line window)
  python captburn.py -i media/clip.mp4 -t media/clip.json --style rollup --rollup-lines 2

  # Batch a directory (auto‑match clipname.json next to video)
  python captburn.py --in-dir media/in --out-dir media/out --style popon --align 2

  # Re-burn from a previously saved capton JSON (skips re-parse)
  python captburn.py -i media/clip.mp4 --capton media/clip.captburn.json

Notes:
  • Input transcript JSON shapes supported:
      A) Segments with word timings: [{"content": "...", "start": 0.0, "end": 1.2, "words": [{"word":"foo","start":0.00,"end":0.23}, ...]}]
      B) Simpler segments: [{"text":"...","start":...,"end":...}] or {"content":..., ...}
  • Paint‑on uses ASS karaoke (\k) per-word; pop‑on uses sentence/segment blocks; roll‑up slides a N‑line window.
  • Colors accept #RRGGBB and optional alpha via --back-opacity, --primary-alpha, etc.
"""

from __future__ import annotations
import argparse
import json
import math
import os
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# -----------------------------
# Helpers: colors, times, paths
# -----------------------------

def ensure_ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise RuntimeError("ffmpeg not found. On macOS: brew install ffmpeg || brew install ffmpeg --with-libass (if older brew). Ensure libass is enabled.")
    return exe


def sec_to_ass(ts: float) -> str:
    if ts < 0:
        ts = 0.0
    h = int(ts // 3600)
    m = int((ts % 3600) // 60)
    s = int(ts % 60)
    cs = int(round((ts - math.floor(ts)) * 100))  # centiseconds
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def hex_to_ass_bgr(hex_rgb: str, alpha: float = 0.0) -> str:
    r"""Convert #RRGGBB to ASS &HAABBGGRR format. alpha in [0..1], 0=opaque, 1=fully transparent.
    ASS alpha byte is 0x00 opaque .. 0xFF transparent.
    """
    hx = hex_rgb.strip()
    if hx.startswith("#"):
        hx = hx[1:]
    if len(hx) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", hx):
        raise ValueError(f"Invalid hex color: {hex_rgb}")
    r = int(hx[0:2], 16)
    g = int(hx[2:4], 16)
    b = int(hx[4:6], 16)
    a = int(round(alpha * 255))
    return f"&H{a:02X}{b:02X}{g:02X}{r:02X}"


def safe_stem(p: Path) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", p.stem)

def ensure_ffprobe() -> str:
    exe = shutil.which("ffprobe")
    if not exe:
        raise RuntimeError("ffprobe not found. Install ffmpeg/ffprobe.")
    return exe

def get_video_dimensions(video: Path) -> Tuple[int, int]:
    ffprobe = ensure_ffprobe()
    cmd = [ffprobe, "-v", "error", "-select_streams", "v:0",
           "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", str(video)]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeError(f"ffprobe failed to get dimensions for {video}")
    w_str, h_str = proc.stdout.strip().split("x")
    return int(w_str), int(h_str)



# -----------------------------
# Data structures
# -----------------------------

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
    back_opacity: float = 0.0  # 0..1
    bold: bool = False
    italic: bool = False
    scale_x: int = 100
    scale_y: int = 100
    spacing: float = 0.0
    margin_l: int = 60
    margin_r: int = 60
    margin_v: int = 40
    align: int = 2  # ASS 1..9
    border_style: int = 1  # 1=outline+shadow, 3=opaque box

    def to_ass_style_line(self) -> str:
        primary_ass = hex_to_ass_bgr(self.primary, 0.0)
        outline_ass = hex_to_ass_bgr(self.outline, 0.0)
        back_ass = hex_to_ass_bgr(self.back, self.back_opacity)
        bold = -1 if self.bold else 0
        italic = -1 if self.italic else 0
        # Angle (0) is between Spacing and BorderStyle
        return (
            f"Style: {self.name},{self.fontname},{self.fontsize},"
            f"{primary_ass},&H00FFFFFF,{outline_ass},{back_ass},"
            f"{bold},{italic},0,0,100,100,{self.spacing},0,"
            f"{self.border_style},{self.outline_width},{self.shadow},{self.align},"
            f"{self.margin_l},{self.margin_r},{self.margin_v},1"
        )


from typing import Optional

@dataclass
class Event:
    start: float
    end: float
    text: str  # Plain line or with ASS overrides (e.g., \k tags)
    pos: Optional[Tuple[int, int]] = None
    move: Optional[Tuple[int, int, int, int, int, int]] = None  # x1,y1,x2,y2,t1ms,t2ms

    def to_ass_dialogue(self, style_name: str, rotate: Optional[float] = None, align: Optional[int] = None) -> str:
        start_s = sec_to_ass(self.start)
        end_s = sec_to_ass(self.end)
        tags = []
        if align is not None:
            tags.append(f"\\an{align}")            # force alignment at event level
        if self.pos:
            x, y = self.pos
            tags.append(f"\\pos({x},{y})")
        if self.move:
            x1, y1, x2, y2, t1, t2 = self.move
            tags.append(f"\\move({x1},{y1},{x2},{y2},{t1},{t2})")
        if rotate is not None:
            tags.append(f"\\frz{rotate}")          # rotation in degrees
        prefix = "{" + "".join(tags) + "}" if tags else ""
        safe_text = self.text.replace("\n", "\\N")
        # keep margins in the Style row (0,0,0 here means "use style margins")
        return f"Dialogue: 0,{start_s},{end_s},{style_name},,0,0,0,,{prefix}{safe_text}\n"



@dataclass
class Capton:
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

    @staticmethod
    def from_json(d: Dict[str, Any]) -> "Capton":
        style = Style(**d["style"])
        events = []
        for ed in d["events"]:
            pos = tuple(ed["pos"]) if "pos" in ed else None
            move = tuple(ed["move"]) if "move" in ed else None
            events.append(Event(start=ed["start"], end=ed["end"], text=ed["text"], pos=pos, move=move))
        return Capton(version=d.get("version", "1.0"), style=style, events=events)


# -----------------------------
# Transcript parsing → events
# -----------------------------

def load_transcript(path: Path) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Normalize to list of segments; if a dict with "segments", unwrap
    if isinstance(data, dict) and "segments" in data:
        data = data["segments"]
    if not isinstance(data, list):
        raise ValueError("Transcript JSON must be a list or contain a 'segments' list.")
    return data


def extract_words(seg: Dict[str, Any]) -> List[Dict[str, Any]]:
    words = seg.get("words")
    if isinstance(words, list) and words:
        return [
            {
                "text": (w.get("word") or w.get("text") or str(w)).strip(),
                "start": float(w.get("start", seg.get("start", 0.0))),
                "end": float(w.get("end", seg.get("end", 0.0))),
            }
            for w in words
            if (w.get("word") or w.get("text"))
        ]
    # Fallback: split content/text by spaces, spread across seg start/end
    content = (seg.get("content") or seg.get("text") or "").strip()
    tokens = [t for t in re.split(r"\s+", content) if t]
    st = float(seg.get("start", 0.0))
    et = float(seg.get("end", st + max(1.0, len(tokens) * 0.25)))
    dur = max(0.01, et - st)
    words = []
    if tokens:
        step = dur / len(tokens)
        for i, tok in enumerate(tokens):
            words.append({"text": tok, "start": st + i * step, "end": st + (i + 1) * step})
    return words


def build_events_popon(segments: List[Dict[str, Any]]) -> List[Event]:
    events: List[Event] = []
    for seg in segments:
        text = (seg.get("content") or seg.get("text") or "").strip()
        if not text:
            # If no segment text, fallback to joining words
            ws = extract_words(seg)
            text = " ".join(w["text"] for w in ws)
        st = float(seg.get("start", ws[0]["start"] if (ws := extract_words(seg)) else 0.0))
        et = float(seg.get("end", ws[-1]["end"] if (ws := ws) else st + 2.0))
        events.append(Event(start=st, end=et, text=text))
    return events


def build_events_painton(segments: List[Dict[str, Any]], max_line_chars: int = 42) -> List[Event]:
    r"""Paint‑on (word‑reveal) via ASS karaoke. We pack words into reasonable lines, but reveal per word with \k.
    \k expects centiseconds per token.
    """
    evs: List[Event] = []
    for seg in segments:
        words = extract_words(seg)
        if not words:
            continue
        st = words[0]["start"]
        et = words[-1]["end"]
        # Build karaoke line with {\kNN} before each word
        parts = []
        line_len = 0
        line_start = st
        acc_duration_cs = 0
        buf = []

        def flush_line(end_time: float):
            nonlocal buf, acc_duration_cs, line_start
            if not buf:
                return
            text = "".join(buf).strip()
            evs.append(Event(start=line_start, end=end_time, text=text))
            buf = []
            acc_duration_cs = 0

        for i, w in enumerate(words):
            wdur = max(0.01, w["end"] - w["start"])  # seconds
            k = int(round(wdur * 100))
            token = w["text"]
            piece = f"{{\\k{k}}}{token} "
            if line_len + len(token) > max_line_chars and buf:
                # line break
                flush_line(words[i - 1]["end"])
                line_start = w["start"]
                line_len = 0
            buf.append(piece)
            line_len += len(token) + 1
        flush_line(et)
    return evs


def build_events_rollup(segments: List[Dict[str, Any]], lines: int = 2, words_per_line: int = 6) -> List[Event]:
    r"""Roll‑up style: sliding window of N lines. We emit events as the window advances word‑by‑word."""
    ws_all: List[Dict[str, Any]] = []
    for seg in segments:
        ws_all.extend(extract_words(seg))
    evs: List[Event] = []
    if not ws_all:
        return evs
    # Build rolling text buffer
    window_tokens: List[str] = []
    window_start = ws_all[0]["start"]
    last_end = window_start
    line_break_every = words_per_line
    for i, w in enumerate(ws_all):
        window_tokens.append(w["text"])
        last_end = w["end"]
        # Insert line breaks at intervals
        if len(window_tokens) % words_per_line == 0:
            window_tokens.append("\n")
        # Determine current visible text: last (lines) lines from tokens
        # Build text maintaining line breaks
        text_lines: List[str] = []
        cur_line: List[str] = []
        for tok in window_tokens:
            if tok == "\n":
                text_lines.append(" ".join(cur_line))
                cur_line = []
            else:
                cur_line.append(tok)
        if cur_line:
            text_lines.append(" ".join(cur_line))
        text = "\\N".join(text_lines[-lines:])
        # Emit/update event chunk per word (short lifetime until next word)
        # We give each chunk a small duration; the next word will create the next chunk.
        start_t = window_start
        end_t = max(last_end, start_t + 0.25)
        evs.append(Event(start=start_t, end=end_t, text=text))
        window_start = w["start"]  # next chunk starts at this word for smoother progress
    return evs


# -----------------------------
# ASS document building
# -----------------------------

from typing import Optional, List

def build_ass(style: Style, events: List[Event], playres_x: int, playres_y: int, rotate: Optional[float] = None) -> str:
    header = (
        "[Script Info]\n"
        "; Script generated by captburn\n"
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
        # pass rotate + align to each event; do NOT reference args here
        lines.append(ev.to_ass_dialogue(style.name, rotate=rotate, align=style.align))
    return "".join(lines)


# -----------------------------
# Burn with ffmpeg
# -----------------------------

def burn_subs(ffmpeg: str, in_video: Path, ass_file: Path, out_path: Path, video_codec: str = "libx264", crf: int = 18, preset: str = "medium") -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Prefer -vf ass=; fall back to subtitles=
    vf = f"ass={ass_file.as_posix()}"
    cmd = [
        ffmpeg, "-hide_banner", "-y",
        "-i", str(in_video),
        "-vf", vf,
        "-c:v", video_codec, "-crf", str(crf), "-preset", preset, "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(out_path),
    ]
    print("🎛️ Using filter:", "-vf", vf)
    print("🔨", "Executing:", shlex.join(cmd))
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(proc.stdout)
    if proc.returncode != 0:
        # try subtitles= as a fallback
        vf2 = f"subtitles={ass_file.as_posix()}"
        cmd2 = cmd.copy()
        cmd2[cmd2.index("-vf") + 1] = vf2
        print("⚠️ ffmpeg attempt failed with code", proc.returncode, "— retrying with", vf2)
        print("🔨", "Executing:", shlex.join(cmd2))
        proc2 = subprocess.run(cmd2, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        print(proc2.stdout)
        if proc2.returncode != 0:
            raise RuntimeError(f"ffmpeg failed with exit code {proc2.returncode}")


# -----------------------------
# Capton I/O
# -----------------------------

def write_capton(path: Path, capton: Capton) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(capton.to_json(), f, ensure_ascii=False, indent=2)


def read_capton(path: Path) -> Capton:
    with open(path, "r", encoding="utf-8") as f:
        return Capton.from_json(json.load(f))


# -----------------------------
# Pipeline drivers
# -----------------------------

def make_events(style_name: str, segs: List[Dict[str, Any]], style_choice: str, rollup_lines: int, words_per_line: int) -> List[Event]:
    if style_choice == "popon":
        return build_events_popon(segs)
    elif style_choice == "painton":
        return build_events_painton(segs)
    elif style_choice == "rollup":
        return build_events_rollup(segs, lines=rollup_lines, words_per_line=words_per_line)
    else:
        raise ValueError("Unknown style: " + style_choice)


def apply_overrides(events: List[Event], pos: Optional[Tuple[int, int]], move: Optional[Tuple[int, int, int, int, int, int]]):
    if pos:
        for e in events:
            e.pos = pos
    if move:
        for e in events:
            e.move = move


def process_one(in_video: Path, transcript_json: Optional[Path], out_dir: Path, style_choice: str, style: Style,
                align: int, pos: Optional[Tuple[int, int]], move: Optional[Tuple[int, int, int, int, int, int]],
                rollup_lines: int, words_per_line: int, capton_in: Optional[Path],
                rotate: Optional[float]) -> Tuple[Path, Path, Path]:
    ffmpeg = ensure_ffmpeg()
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = safe_stem(in_video)
    ass_path = out_dir / f"{stem}.captburn.ass"
    capton_path = out_dir / f"{stem}.captburn.json"
    out_video = out_dir / f"{stem}.captburn.mp4"

    style.align = align

    if capton_in and capton_in.exists():
        capton = read_capton(capton_in)
        style = capton.style
        events = capton.events
        print("♻️  Loaded events from capton JSON.")
    else:
        if not transcript_json:
            # auto-resolve transcript path: same name .json next to input
            candidate = in_video.with_suffix(".json")
            if candidate.exists():
                transcript_json = candidate
            else:
                raise FileNotFoundError("No transcript JSON provided and <video>.json not found.")
        segs = load_transcript(transcript_json)
        events = make_events(style.name, segs, style_choice, rollup_lines, words_per_line)

    apply_overrides(events, pos, move)

    # Dimensions for PlayRes (so x/y == real pixels)
    try:
        w, h = get_video_dimensions(in_video)
        print(f"📐 Video dimensions: {w}x{h}")
    except Exception as e:
        print("⚠️ Could not probe video size; using 1920x1080 fallback:", e)
        w, h = (1920, 1080)

    ass_text = build_ass(style, events, w, h, rotate=rotate)
    ass_path.write_text(ass_text, encoding="utf-8")


    capton = Capton(version="1.0.0", style=style, events=events)
    write_capton(capton_path, capton)

    print(f"📝 Wrote ASS → {ass_path}")
    print(f"🧾 Wrote capton JSON → {capton_path}")

    burn_subs(ffmpeg, in_video, ass_path, out_video)
    print(f"✅ Burned → {out_video}")

    return ass_path, capton_path, out_video


def find_videos(indir: Path) -> List[Path]:
    exts = {".mp4", ".mov", ".mkv", ".m4v", ".avi", ".webm"}
    vids: List[Path] = []
    for p in sorted(indir.glob("**/*")):
        if p.suffix.lower() in exts:
            vids.append(p)
    return vids


# -----------------------------
# CLI
# -----------------------------

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="captburn", description="Vintage titler‑style caption burner")

    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("-i", "--input", type=Path, help="Input video file")
    src.add_argument("--in-dir", type=Path, help="Process all videos in this directory (recursive)")

    ap.add_argument("-t", "--trans-json", type=Path, help="Transcript JSON (if omitted, tries <video>.json)")
    ap.add_argument("--capton", type=Path, help="Use existing capton JSON (skips transcript parse)")
    ap.add_argument("--out-dir", type=Path, default=Path("out"), help="Output directory")

    ap.add_argument("--style", choices=["popon", "painton", "rollup"], default="popon", help="Caption style")
    ap.add_argument("--rollup-lines", type=int, default=2, help="Roll‑up: visible line window")
    ap.add_argument("--words-per-line", type=int, default=6, help="Roll‑up: words per line before wrap")

    # Styling
    ap.add_argument("--font", default="Arial", help="Font family name")
    ap.add_argument("--font-size", type=int, default=42, help="Font size")
    ap.add_argument("--bold", action="store_true")
    ap.add_argument("--italic", action="store_true")
    ap.add_argument("--primary", default="#FFFFFF", help="Text color #RRGGBB")
    ap.add_argument("--primary-alpha", type=float, default=0.0, help="0..1 (0=opaque)")
    ap.add_argument("--outline", default="#000000", help="Outline color #RRGGBB")
    ap.add_argument("--outline-width", type=float, default=3.0)
    ap.add_argument("--shadow", type=float, default=0.0)
    ap.add_argument("--back", default="#000000", help="Box background color #RRGGBB")
    ap.add_argument("--back-opacity", type=float, default=0.0, help="0..1 (0=transparent)")
    ap.add_argument("--scale-x", type=int, default=100)
    ap.add_argument("--scale-y", type=int, default=100)
    ap.add_argument("--spacing", type=float, default=0.0, help="Character spacing")
    ap.add_argument("--margin-l", type=int, default=60)
    ap.add_argument("--margin-r", type=int, default=60)
    ap.add_argument("--margin-v", type=int, default=40)
    ap.add_argument("--align", type=int, default=2, help="ASS alignment 1..9 (2 = bottom-center)")
    ap.add_argument("--border-style", type=int, default=1, help="1=outline, 3=opaque box")
    ap.add_argument("--rotate", type=float, help="Rotation degrees (ASS \\frz)")

    # Position / Motion overrides
    ap.add_argument("--x", type=int, help="Override X position (pixels)")
    ap.add_argument("--y", type=int, help="Override Y position (pixels)")
    ap.add_argument("--move", type=str, help="ASS move: x1,y1,x2,y2,t1ms,t2ms")

    # Encoding
    ap.add_argument("--vcodec", default="libx264")
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--preset", default="medium")

    return ap.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    out_dir: Path = args.out_dir

    style = Style(
        name="CaptBurn",
        fontname=args.font,
        fontsize=args.font_size,
        primary=args.primary,
        outline=args.outline,
        outline_width=args.outline_width,
        shadow=args.shadow,
        back=args.back,
        back_opacity=args.back_opacity,
        bold=bool(args.bold),
        italic=bool(args.italic),
        scale_x=args.scale_x,
        scale_y=args.scale_y,
        spacing=args.spacing,
        margin_l=args.margin_l,
        margin_r=args.margin_r,
        margin_v=args.margin_v,
        align=args.align,
        border_style=args.border_style,
    )

    pos = (args.x, args.y) if (args.x is not None and args.y is not None) else None
    move = None
    if args.move:
        try:
            x1, y1, x2, y2, t1, t2 = [int(v) for v in args.move.split(",")]
            move = (x1, y1, x2, y2, t1, t2)
        except Exception:
            raise ValueError("--move must be 'x1,y1,x2,y2,t1ms,t2ms'")

    try:
        if args.input:
            process_one(
                in_video=args.input,
                transcript_json=args.trans_json,
                out_dir=out_dir,
                style_choice=args.style,
                style=style,
                align=args.align,
                pos=pos,
                move=move,
                rollup_lines=args.rollup_lines,
                words_per_line=args.words_per_line,
                capton_in=args.capton,
                rotate=args.rotate,
            )
        else:
            vids = find_videos(args.in_dir)
            if not vids:
                print("No videos found in", args.in_dir)
                return 2
            for v in vids:
                # Try to find transcript JSON with same stem in same dir
                tjson = None
                stem = v.with_suffix(".json")
                if stem.exists():
                    tjson = stem
                process_one(
                    in_video=v,
                    transcript_json=tjson or args.trans_json,
                    out_dir=out_dir,
                    style_choice=args.style,
                    style=style,
                    align=args.align,
                    pos=pos,
                    move=move,
                    rollup_lines=args.rollup_lines,
                    words_per_line=args.words_per_line,
                    capton_in=args.capton,
                )
    except Exception as e:
        print("❌", type(e).__name__, str(e))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
