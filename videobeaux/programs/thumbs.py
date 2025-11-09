#!/usr/bin/env python3
# videobeaux/programs/thumbs.py
# Thumbnail / Contact Sheet generator for videobeaux.
#
# Supports:
#   - Interval sampling (--fps)
#   - Scene-based sampling (--scene)
#   - Timestamp overlays (--timestamps)
#   - Custom fonts, colors, margins, padding
#   - Frame sequences (--outdir)
#   - Contact sheets (--outputfile)
#
# Example:
#   videobeaux -P thumbs -i ./media/bbb.mov --outputfile ./out/bbb_contact.jpg --fps 0.5 --tile 5x4 -F

from __future__ import annotations
import argparse
from pathlib import Path
from typing import List

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

DEFAULT_EXT = "jpg"

# ------------------------------
# Helper functions
# ------------------------------
def _parse_tile(tile: str | None) -> tuple[int, int]:
    if not tile:
        return (6, 4)
    try:
        parts = tile.lower().replace("x", " ").split()
        c, r = int(parts[0]), int(parts[1])
        return (max(1, c), max(1, r))
    except Exception:
        raise SystemExit("❌ Invalid --tile format. Use like 6x4 (columns x rows).")

def _scale_expr(scale: str | None) -> str:
    if not scale:
        return "320:-1"
    if ":" not in scale:
        raise SystemExit("❌ Invalid --scale format. Use WIDTH:HEIGHT (e.g., 320:-1 or 360:360).")
    return scale

def _escape_text(s: str) -> str:
    return s.replace(":", r"\:").replace("'", r"\'")

def _sanitize_color(c: str) -> str:
    """Accepts '#RRGGBB', '0xRRGGBB', or named colors like 'black'."""
    c = (c or "").strip()
    if not c:
        return "black"
    if c.startswith("#"):
        hx = c[1:]
        if len(hx) == 3:
            hx = "".join(ch * 2 for ch in hx)
        return "0x" + hx.lower()
    if c.lower().startswith("0x"):
        return c.lower()
    return c  # Named colors

def _drawtext_chain(timestamps: bool, fontfile: str | None) -> list[str]:
    chain: list[str] = []
    if timestamps:
        dt = "drawtext=text='%{pts\\:hms}':x=10:y=h-th-10:fontsize=20:fontcolor=white"
        if fontfile:
            dt += f":fontfile='{_escape_text(fontfile)}'"
        chain.append(dt)
    return chain

def _ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

# ------------------------------
# Argument registration
# ------------------------------
def register_arguments(parser: argparse.ArgumentParser):
    parser.description = (
        "Generate thumbnails and/or a tiled contact sheet from a video. "
        "Supports interval or scene-based selection, timestamps, custom fonts, and layout styling."
    )

    # Sampling
    parser.add_argument("--fps", type=float, default=0.5, help="Frames per second to sample (e.g., 0.5 = one every 2s).")
    parser.add_argument("--scene", action="store_true", help="Use scene-based selection instead of fixed intervals.")
    parser.add_argument("--scene-threshold", type=float, default=0.4, help="Scene detection sensitivity (lower = more cuts).")

    # Appearance
    parser.add_argument("--tile", type=str, default="6x4", help="Contact sheet grid 'COLUMNSxROWS' (e.g., 6x4).")
    parser.add_argument("--scale", type=str, default="320:-1", help="Per-thumb scale (e.g., 320:-1).")
    parser.add_argument("--timestamps", action="store_true", help="Overlay timestamps on thumbnails.")
    parser.add_argument("--label", action="store_true", help="Add a footer label with filename.")
    parser.add_argument("--fontfile", type=str, help="Custom font path for drawtext.")
    parser.add_argument("--bg", type=str, default="#000000", help="Background color ('black', '#111111', or '0x111111').")
    parser.add_argument("--margin", type=int, default=12, help="Outer margin (pixels).")
    parser.add_argument("--padding", type=int, default=6, help="Padding between tiles (pixels).")

    # Outputs
    parser.add_argument("--outdir", type=str, help="Directory to export frame sequence.")
    parser.add_argument("--outputfile", type=str, help="Output contact sheet path (e.g., ./out/sheet.jpg).")
    parser.add_argument("--image-format", choices=["jpg", "png"], default=None, help="Output format if --outputfile has no extension.")
    parser.add_argument("--jpeg-quality", type=int, default=3, help="JPEG quality (2=high, 3=good, 5=ok).")

# ------------------------------
# Main execution
# ------------------------------
def run(args: argparse.Namespace):
    in_path = Path(args.input)
    if not in_path.exists():
        raise SystemExit(f"❌ Input not found: {in_path}")

    contactsheet_path: Path | None = None
    if getattr(args, "outputfile", None):
        contactsheet_path = Path(args.outputfile)
    if contactsheet_path and contactsheet_path.suffix == "":
        ext = args.image_format or DEFAULT_EXT
        contactsheet_path = contactsheet_path.with_suffix(f".{ext}")

    outdir_path: Path | None = None
    if getattr(args, "outdir", None):
        outdir_path = Path(args.outdir)

    if not contactsheet_path and not outdir_path:
        raise SystemExit("❌ Provide at least one output: --outputfile or --outdir.")

    scale = _scale_expr(args.scale)
    draw_chain = _drawtext_chain(args.timestamps, args.fontfile)

    # -------------- Frame Sequence --------------
    if outdir_path:
        outdir_path.mkdir(parents=True, exist_ok=True)
        seq_filters: list[str] = []
        if args.scene:
            seq_filters.append(f"select='gt(scene,{args.scene_threshold})'")
        else:
            seq_filters.append(f"fps={max(0.001, float(args.fps))}")
        seq_filters.append(f"scale={scale}")
        seq_filters.extend(draw_chain)
        seq_vf = ",".join(seq_filters)
        pattern = str(outdir_path / "frame_%06d.jpg")
        cmd = [
            "ffmpeg",
            "-i", str(in_path),
            "-vf", seq_vf,
            "-q:v", str(max(1, min(31, int(args.jpeg_quality)))),
            pattern
        ]
        if getattr(args, "force", False):
            cmd = cmd[:1] + ["-y"] + cmd[1:]
        run_ffmpeg_with_progress(cmd, args.input, outdir_path / "frame_%06d.jpg")

    # -------------- Contact Sheet --------------
    if contactsheet_path:
        _ensure_parent(contactsheet_path)
        cols, rows = _parse_tile(args.tile)
        bg_color = _sanitize_color(args.bg)

        filters: list[str] = []
        if args.scene:
            filters.append(f"select='gt(scene,{args.scene_threshold})'")
        else:
            filters.append(f"fps={max(0.001, float(args.fps))}")
        filters.append(f"scale={scale}")
        filters.extend(draw_chain)
        filters.append(f"tile={cols}x{rows}:{int(args.margin)}:{int(args.padding)}:{bg_color}")

        if args.label:
            label_txt = _escape_text(in_path.name)
            label = f"drawtext=text='{label_txt}':x=10:y=h-th-10:fontsize=22:fontcolor=white"
            if args.fontfile:
                label += f":fontfile='{_escape_text(args.fontfile)}'"
            filters.append(label)

        full_chain = ",".join(filters)
        is_png = contactsheet_path.suffix.lower() == ".png"

        cmd = ["ffmpeg", "-i", str(in_path), "-vf", full_chain, "-frames:v", "1"]
        if not is_png:
            cmd += ["-q:v", str(max(1, min(31, int(args.jpeg_quality))))]
        cmd += [str(contactsheet_path)]
        if getattr(args, "force", False):
            cmd = cmd[:1] + ["-y"] + cmd[1:]
        run_ffmpeg_with_progress(cmd, args.input, contactsheet_path)
