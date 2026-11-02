#!/usr/bin/env python3
# videobeaux/programs/crop_black.py
#
# Crop away black bars (letterbox on the top and bottom, or pillarbox on the sides). ffmpeg's cropdetect reads the
# picture box in sampled frames, and the box most frames agree on is taken as the picture. The picture is then scaled
# to fill the nearest standard frame size (any small overflow is trimmed), unless --keep_size is set.

from __future__ import annotations

import argparse
import math
import re
import subprocess
from collections import Counter
from typing import Optional, Sequence, Tuple

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

GUI_METADATA = {
    'args': {
        'threshold': {'label': 'Black Threshold', 'min': 4, 'max': 64,
                      'help': 'How dark a pixel must be to count as black (0–255). Raise it if the bars are not pure black.'},
        'keep_size': {'label': 'Keep Cropped Size',
                      'help': 'Keep the picture at the size it was cropped to. Off = scale it to the nearest standard frame size.'},
    }
}

# Standard frame sizes. The picture goes to the one closest in shape, with a small preference for the one nearest its
# height, so a picture is not stretched far up or down.
NOMINAL_SIZES = [
    (1920, 1080), (1280, 720), (854, 480), (640, 360),
    (2560, 1080), (1920, 800),
    (1440, 1080), (1024, 768), (640, 480),
    (1080, 1080), (720, 720),
    (1080, 1920), (720, 1280),
]
HEIGHT_WEIGHT = 0.3
# A crop this close to the whole frame (in pixels, per side) is not treated as having bars.
BAR_TOLERANCE = 4

CROP_LINE = re.compile(r"crop=(\d+):(\d+):(\d+):(\d+)")


def nominal_size(width: int, height: int) -> Tuple[int, int]:
    """The standard frame size whose shape is closest to width x height."""
    shape = math.log(width / height)

    def cost(size: Tuple[int, int]) -> float:
        sw, sh = size
        return abs(math.log(sw / sh) - shape) + HEIGHT_WEIGHT * abs(math.log(sh / height))

    return min(NOMINAL_SIZES, key=cost)


def most_common_crop(detections: Sequence[Tuple[int, int, int, int]]) -> Optional[Tuple[int, int, int, int]]:
    """The crop (w, h, x, y) that the most sampled frames agree on, or None when there were none."""
    usable = [d for d in detections if d[0] >= 2 and d[1] >= 2]
    if not usable:
        return None
    return Counter(usable).most_common(1)[0][0]


def is_whole_frame(crop: Tuple[int, int, int, int], width: int, height: int) -> bool:
    w, h = crop[0], crop[1]
    return width - w <= BAR_TOLERANCE and height - h <= BAR_TOLERANCE


def _probe_size(path: str) -> Tuple[int, int]:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", path],
        capture_output=True, text=True, check=True,
    )
    width, height = (int(v) for v in result.stdout.strip().split("x"))
    return width, height


def detect_crop(path: str, threshold: int) -> Optional[Tuple[int, int, int, int]]:
    """Run cropdetect over the clip (two frames a second, each judged on its own) and return the most common picture box."""
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", path,
         "-vf", f"fps=2,cropdetect=limit={threshold}:round=2:reset=1",
         "-an", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    detections = [tuple(int(v) for v in m.groups()) for m in CROP_LINE.finditer(result.stderr)]
    return most_common_crop(detections)


def register_arguments(parser: argparse.ArgumentParser):
    parser.description = (
        "Crop away black bars (top and bottom, or the sides) and keep the picture. The picture is then scaled to the "
        "nearest standard frame size (for example 1920×1080 or 1920×800), unless --keep_size is set."
    )
    parser.add_argument("--threshold", type=int, default=24,
                        help="How dark a pixel must be to count as black, 0–255. Default: 24.")
    parser.add_argument("--keep_size", action="store_true",
                        help="Keep the picture at the size it was cropped to, instead of scaling it to a standard size.")


def run(args):
    width, height = _probe_size(args.input)
    print("🔎 Looking for black bars…", flush=True)
    crop = detect_crop(args.input, int(args.threshold))

    filters = []
    if crop is None or is_whole_frame(crop, width, height):
        print("ℹ️  No black bars found, so the picture is unchanged.")
    else:
        w, h, x, y = crop
        filters.append(f"crop={w}:{h}:{x}:{y}")
        if args.keep_size:
            print(f"✂️  Cropping {width}×{height} to {w}×{h}")
        else:
            # Fill the nearest standard frame and trim the small overflow: padding would put black bars back in.
            tw, th = nominal_size(w, h)
            filters += [
                f"scale={tw}:{th}:force_original_aspect_ratio=increase",
                f"crop={tw}:{th}",
                "setsar=1",
            ]
            print(f"✂️  Cropping {width}×{height} to {w}×{h}, scaled to {tw}×{th}")

    command = ["ffmpeg", "-i", args.input]
    if filters:
        command += ["-vf", ",".join(filters), "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-pix_fmt", "yuv420p"]
    else:
        command += ["-c:v", "copy"]
    command += ["-map", "0:v:0", "-map", "0:a?", "-c:a", "copy", args.output]
    if getattr(args, "force", False):
        command = command[:1] + ["-y"] + command[1:]

    run_ffmpeg_with_progress(command, args.input, args.output)
