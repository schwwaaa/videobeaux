#!/usr/bin/env python3
# videobeaux/programs/watermark.py
#
# Overlay a static/animated image (PNG/JPG/GIF) onto a video — covers both
# "watermark" use (opacity, spin, timed fade-in/out, GIF looping) and precise
# image-overlay use (9-point placement grid, custom pixel/expression position,
# exact pixel sizing). Merged from what used to be two near-duplicate
# programs, watermark.py and overlay_img_pro.py.
# - Robust GIF handling (looping, -ignore_loop, optional -stream_loop)
# - 9 placement presets + custom X/Y, with margin
# - Sizing: scale factor relative to intrinsic width (iw*scale), or exact
#   --width/--height pixel dimensions when you need precise control
# - Opacity via colorchannelmixer (alpha)
# - Optional spin (continuous rotation over time)
# - Timed enable window (start/end seconds)
# - Safe stream mapping and mp4-friendly output
#
# Example:
# videobeaux -P watermark \
#   -i ./media/bbb.mov -o ./out/bbb_wm_windowed.mp4 \
#   --watermark ./media/badge.gif --placement bottom-right --margin 24 \
#   --scale 0.25 --opacity 0.7 --spin 12.0 --start 1.0 --end 7.0 \
#   --wm-loop -1 -F
#
# Notes:
# - spin is degrees per second (float). angle(t) = spin_deg_per_sec * t * pi/180
# - wm-loop behaves like ffmpeg -stream_loop for the watermark input:
#     -1 = infinite, 0 = no extra loops, N>0 loop N times after first play
# - We ALWAYS pass -ignore_loop 0 for GIF so decoder honors intrinsic timing.
# - For non-GIF stills, ffmpeg holds the frame; for sequences/GIF we add -stream_loop as requested.
# - --width/--height take priority over --scale when either is set.

from __future__ import annotations
import argparse
from pathlib import Path
from typing import Tuple

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

GUI_METADATA = {
    'args': {
        'placement': {
            'type': 'select', 'default': 'bottom-right',
            'choices': [
                'top-left', 'top-center', 'top-right',
                'center-left', 'center', 'center-right',
                'bottom-left', 'bottom-center', 'bottom-right',
                'custom',
            ],
            'help': "Where to position the overlay. Choose 'custom' to use X/Y Position below for exact pixel/expression control.",
        },
        'x_pos': {'help': "Horizontal position (pixels or an ffmpeg expression). Only used when Placement is 'custom'."},
        'y_pos': {'help': "Vertical position (pixels or an ffmpeg expression). Only used when Placement is 'custom'."},
        'width': {'help': "Exact overlay width in pixels. Overrides --scale when set."},
        'height': {'help': "Exact overlay height in pixels (or -1 to preserve aspect ratio). Overrides --scale when set."},
    }
}


# 9-point placement grid + margin, using ffmpeg overlay filter variables
# (W/H = main video size, w/h = the overlay's own size after scaling).
def _placement_xy(placement: str, margin: int) -> Tuple[str, str]:
    m = int(margin)
    table = {
        "top-left":      (f"{m}", f"{m}"),
        "top-center":    ("(W-w)/2", f"{m}"),
        "top-right":     (f"W-w-{m}", f"{m}"),
        "center-left":   (f"{m}", "(H-h)/2"),
        "center":        ("(W-w)/2", "(H-h)/2"),
        "center-right":  (f"W-w-{m}", "(H-h)/2"),
        "bottom-left":   (f"{m}", f"H-h-{m}"),
        "bottom-center": ("(W-w)/2", f"H-h-{m}"),
        "bottom-right":  (f"W-w-{m}", f"H-h-{m}"),
    }
    return table.get(placement.lower().strip(), (f"W-w-{m}", f"H-h-{m}"))


def _sanitize_scale(scale: float) -> float:
    try:
        s = float(scale)
    except Exception:
        raise SystemExit("❌ --scale must be a number (e.g., 0.25).")
    if s <= 0:
        raise SystemExit("❌ --scale must be > 0.")
    return s


def _sanitize_opacity(opacity: float) -> float:
    try:
        a = float(opacity)
    except Exception:
        raise SystemExit("❌ --opacity must be a number between 0.0 and 1.0.")
    if not (0.0 <= a <= 1.0):
        raise SystemExit("❌ --opacity must be between 0.0 and 1.0.")
    return a


def _gif_input_flags(wm_path: Path, wm_loop: int, ignore_loop_flag: bool) -> list[str]:
    """
    Build input flags for GIF/animated watermark.
    We default to respecting GIF's intrinsic loop: -ignore_loop 0
    Then optionally add -stream_loop <N> to extend looping.
    """
    flags: list[str] = []
    if wm_path.suffix.lower() == ".gif":
        # If user asked to ignore the gif's intrinsic loop, set -ignore_loop 1
        if ignore_loop_flag:
            flags += ["-ignore_loop", "1"]
        else:
            flags += ["-ignore_loop", "0"]

        # -stream_loop <N>: -1 infinite, 0 none, N>0 N extra loops after first play.
        # Only add when user provides a value different from None and not 0.
        # (If 0, we omit; if -1 or >0, we set it.)
        if wm_loop is not None and wm_loop != 0:
            flags += ["-stream_loop", str(int(wm_loop))]
    return flags


def register_arguments(parser: argparse.ArgumentParser):
    parser.description = (
        "Burn a watermark or general-purpose image overlay (PNG/JPG/GIF) into a video: "
        "9-point placement grid or a custom pixel/expression position, scale or exact "
        "pixel sizing, opacity, optional spin, and a timed enable window."
    )
    parser.add_argument("--watermark", required=True, help="Path to watermark/overlay image (PNG/JPG/GIF).")
    parser.add_argument("--placement", default="bottom-right",
                        choices=[
                            "top-left", "top-center", "top-right",
                            "center-left", "center", "center-right",
                            "bottom-left", "bottom-center", "bottom-right",
                            "custom",
                        ],
                        help="Where to position the overlay. Use 'custom' with --x_pos/--y_pos for exact control.")
    parser.add_argument("--margin", type=int, default=24, help="Margin (px) from edges for placement.")
    parser.add_argument("--x_pos", required=False, type=str, default=None,
                        help="Horizontal position, in pixels or an ffmpeg expression. Only used when --placement custom.")
    parser.add_argument("--y_pos", required=False, type=str, default=None,
                        help="Vertical position, in pixels or an ffmpeg expression. Only used when --placement custom.")
    parser.add_argument("--scale", type=float, default=0.25,
                        help="Scale factor relative to watermark intrinsic width (iw*scale). Ignored if --width/--height is set.")
    parser.add_argument("--width", required=False, type=str, default=None,
                        help="Exact overlay width in pixels. Overrides --scale when set.")
    parser.add_argument("--height", required=False, type=str, default=None,
                        help="Exact overlay height in pixels (or -1 to preserve aspect ratio). Overrides --scale when set.")
    parser.add_argument("--opacity", type=float, default=0.8,
                        help="Watermark opacity (0.0–1.0).")
    parser.add_argument("--spin", type=float, default=0.0,
                        help="Watermark spin in degrees per second (0 = no rotation).")
    parser.add_argument("--start", type=float, default=0.0, help="Enable overlay starting at t seconds.")
    parser.add_argument("--end", type=float, default=0.0,
                        help="Disable overlay after t seconds (0 = until end).")

    # GIF/animated controls
    parser.add_argument("--wm-loop", type=int, default=0,
                        help="Additional loops for watermark input (-1=infinite, 0=none, N>0 times).")
    parser.add_argument("--ignore-loop", action="store_true",
                        help="For GIF watermark: ignore intrinsic loop (use frames once).")

    # Video encode controls (kept from your args)
    parser.add_argument("--video-crf", type=int, default=18, help="CRF for libx264.")
    parser.add_argument("--video-preset", type=str, default="fast", help="x264 preset.")

    # NOTE: -i/--input, -o/--output, -F/--force are provided by the top-level CLI.


def run(args: argparse.Namespace):
    in_path = Path(args.input)
    if not in_path.exists():
        raise SystemExit(f"❌ Input not found: {in_path}")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    wm_path = Path(args.watermark)
    if not wm_path.exists():
        raise SystemExit(f"❌ Watermark not found: {wm_path}")

    # Validate numerics
    opacity = _sanitize_opacity(args.opacity)

    # Placement math
    if args.placement == "custom":
        if not args.x_pos or not args.y_pos:
            raise SystemExit("❌ --placement custom requires both --x_pos and --y_pos.")
        x_expr, y_expr = args.x_pos, args.y_pos
    else:
        x_expr, y_expr = _placement_xy(args.placement, args.margin)

    # Enable expression
    if args.end and args.end > 0:
        enable_expr = f"between(t,{float(args.start)},{float(args.end)})"
    else:
        enable_expr = f"gte(t,{float(args.start)})"

    # Build the watermark processing chain
    # 1) size: exact --width/--height when given, else scale relative to its
    #    own intrinsic width (iw*scale)
    # 2) convert to RGBA, then apply alpha multiplier via colorchannelmixer
    # 3) optional rotation with 'rotate' (angle in radians)
    if args.width or args.height:
        w_expr = args.width if args.width else "-1"
        h_expr = args.height if args.height else "-1"
        size_filter = f"scale={w_expr}:{h_expr}"
    else:
        scale = _sanitize_scale(args.scale)
        size_filter = f"scale=iw*{scale}:-1"
    wm_chain_parts = [size_filter, "format=rgba", f"colorchannelmixer=aa={opacity}"]

    spin = float(args.spin or 0.0)
    if spin != 0.0:
        # angle(t) = spin_deg_per_sec * t * pi/180
        # Use ffmpeg expr: (spin*pi/180)*t
        wm_chain_parts.append(f"rotate={(spin)}*PI/180*t:fillcolor=0x00000000")

    wm_chain = ",".join(wm_chain_parts)

    # Overlay (+ enable)
    overlay = f"overlay={x_expr}:{y_expr}:enable='{enable_expr}'"

    # Assemble filter_complex with named pads
    # [1:v]wm_chain[wm];[0:v][wm]overlay=... (alpha premult handled by format=rgba)
    filter_complex = f"[1:v]{wm_chain}[wm];[0:v][wm]{overlay}[vout]"

    # Inputs (include GIF flags when appropriate)
    input_flags: list[str] = ["-i", str(in_path)]
    gif_flags = _gif_input_flags(wm_path, int(args.wm_loop), bool(args.ignore_loop))
    input_flags += gif_flags + ["-i", str(wm_path)]

    # Safe mapping: map main video/audio from #0, output yuv420p mp4 with x264
    command = [
        "ffmpeg",
        *input_flags,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "0:a:0?",
        "-c:v", "libx264",
        "-crf", str(int(args.video_crf)),
        "-preset", str(args.video_preset),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(out_path),
    ]

    if getattr(args, "force", False):
        command = command[:1] + ["-y"] + command[1:]

    # Run
    run_ffmpeg_with_progress(command, args.input, out_path)
