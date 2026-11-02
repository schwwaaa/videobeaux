#!/usr/bin/env python3
# videobeaux/programs/zoom.py
#
# Zoom in on a point: crop a window around it, then scale that window back up to the frame. The output keeps the
# input's size and timing, and the audio is copied as-is.

from __future__ import annotations

import argparse
import subprocess
from typing import Tuple

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

GUI_METADATA = {
    'args': {
        'zoom': {'label': 'Zoom (%)', 'min': 100, 'max': 400, 'good_min': 110, 'good_max': 250,
                 'help': '100 = no zoom. 150 = 1.5× closer, 200 = twice as close.'},
        'focus_x': {'label': 'Focus X (%)', 'min': 0, 'max': 100,
                    'help': 'Horizontal point to zoom toward: 0 = left edge, 50 = centre, 100 = right edge.'},
        'focus_y': {'label': 'Focus Y (%)', 'min': 0, 'max': 100,
                    'help': 'Vertical point to zoom toward: 0 = top, 50 = middle, 100 = bottom.'},
    }
}


def zoom_window(width: int, height: int, zoom_pct: float, focus_x_pct: float, focus_y_pct: float) -> Tuple[int, int, int, int]:
    """
    The crop (w, h, x, y) that, scaled back up to width x height, zooms by zoom_pct around the focus point.
    The window stays inside the frame, so a focus near an edge zooms toward that edge rather than past it.
    Sizes and offsets are even, as yuv420p needs.
    """
    z = zoom_pct / 100.0
    w = max(2, int(width / z) // 2 * 2)
    h = max(2, int(height / z) // 2 * 2)
    x = round(width * focus_x_pct / 100.0 - w / 2)
    y = round(height * focus_y_pct / 100.0 - h / 2)
    x = min(max(x, 0), width - w) // 2 * 2
    y = min(max(y, 0), height - h) // 2 * 2
    return w, h, x, y


def _probe_size(path: str) -> Tuple[int, int]:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", path],
        capture_output=True, text=True, check=True,
    )
    width, height = (int(v) for v in result.stdout.strip().split("x"))
    return width, height


def register_arguments(parser: argparse.ArgumentParser):
    parser.description = (
        "Zoom in by a percentage toward a point you choose. The frame keeps its size: the picture is cropped "
        "around the focus point and scaled back up."
    )
    parser.add_argument("--zoom", type=float, default=150.0,
                        help="Zoom as a percentage: 100 = no zoom, 150 = 1.5x closer, 200 = twice as close. Default: 150.")
    parser.add_argument("--focus_x", type=float, default=50.0,
                        help="Horizontal focus point, 0 (left edge) to 100 (right edge). Default: 50 (centre).")
    parser.add_argument("--focus_y", type=float, default=50.0,
                        help="Vertical focus point, 0 (top edge) to 100 (bottom edge). Default: 50 (middle).")


def run(args):
    if args.zoom < 100:
        raise SystemExit("❌ --zoom is a percentage where 100 = no zoom. Use 100 or more.")
    for name, value in (("--focus_x", args.focus_x), ("--focus_y", args.focus_y)):
        if not 0 <= value <= 100:
            raise SystemExit(f"❌ {name} is a percentage from 0 to 100.")

    width, height = _probe_size(args.input)
    w, h, x, y = zoom_window(width, height, args.zoom, args.focus_x, args.focus_y)
    out_w, out_h = width - width % 2, height - height % 2
    print(f"🔍 Zoom {args.zoom:g}% toward ({args.focus_x:g}%, {args.focus_y:g}%): "
          f"cropping {w}×{h} at ({x}, {y}), scaled back to {out_w}×{out_h}")

    command = [
        "ffmpeg",
        "-i", args.input,
        "-vf", f"crop={w}:{h}:{x}:{y},scale={out_w}:{out_h}:flags=lanczos",
        "-map", "0:v:0",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        args.output,
    ]
    if getattr(args, "force", False):
        command = command[:1] + ["-y"] + command[1:]

    run_ffmpeg_with_progress(command, args.input, args.output)
