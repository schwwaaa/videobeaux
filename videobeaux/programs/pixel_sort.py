from __future__ import annotations
r"""
videobeaux.programs.pixel_sort - glitch-art pixel sorting

Not a native ffmpeg filter — true pixel-sorting (reordering pixels within a row
by brightness, past a threshold) needs per-pixel/per-row control ffmpeg's filter
graph doesn't expose. Architected like kinetic_captions.py: extract frames,
process each one directly with numpy, re-encode the processed sequence with the
original audio muxed back in. Slower than a single-pass filter effect — real
per-frame work, not a lightweight filter — same tradeoff kinetic_captions.py
already accepts for the same reason.
"""
import json
import math
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple

import numpy as np
from PIL import Image

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress


def _probe_video(video_path: Path) -> Tuple[int, int, float, float]:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate:format=duration",
         "-of", "json", str(video_path)],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(result.stdout)
    stream = data["streams"][0]
    width, height = int(stream["width"]), int(stream["height"])
    num, den = stream["r_frame_rate"].split("/")
    fps = float(num) / float(den)
    duration = float(data["format"]["duration"])
    return width, height, fps, duration


def _pixel_sort_frame(arr: np.ndarray, threshold: int, vertical: bool) -> np.ndarray:
    work = arr.transpose(1, 0, 2) if vertical else arr
    h, w, _ = work.shape
    gray = work[:, :, :3].mean(axis=2)
    mask = gray > threshold
    out = work.copy()

    for y in range(h):
        row_mask = mask[y]
        x = 0
        while x < w:
            if not row_mask[x]:
                x += 1
                continue
            x2 = x
            while x2 < w and row_mask[x2]:
                x2 += 1
            order = np.argsort(gray[y, x:x2])
            out[y, x:x2] = work[y, x:x2][order]
            x = x2

    return out.transpose(1, 0, 2) if vertical else out


def register_arguments(parser):
    parser.description = (
        "Glitch-art pixel sorting: within each row (or column), pixels brighter than "
        "--threshold get sorted by brightness, smearing them into long streaks. Real "
        "per-frame processing (not a single ffmpeg filter pass) — slower than most "
        "effects, similar to Kinetic Captions."
    )
    parser.add_argument("--threshold", type=int, default=100, help="Brightness threshold (0-255) above which pixels get sorted. Default: 100.")
    parser.add_argument("--vertical", action="store_true", help="Sort along columns instead of rows.")


def run(args):
    in_video = Path(args.input)
    out_video = Path(args.output)
    out_video.parent.mkdir(parents=True, exist_ok=True)

    width, height, fps, duration = _probe_video(in_video)
    total_frames = math.ceil(duration * fps)
    print(f"📐 Video dimensions: {width}x{height} @ {fps:.3f}fps, {duration:.2f}s")
    print(f"🖼️  Pixel-sorting {total_frames} frames…")

    threshold = max(0, min(255, args.threshold))

    with tempfile.TemporaryDirectory(prefix="videobeaux_pixel_sort_") as tmp_str:
        frames_dir = Path(tmp_str) / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)

        extract_cmd = [
            "ffmpeg", "-y", "-i", str(in_video),
            str(frames_dir / "frame_%06d.png"),
        ]
        subprocess.run(extract_cmd, check=True, capture_output=True)

        frame_paths = sorted(frames_dir.glob("frame_*.png"))
        for i, fp in enumerate(frame_paths):
            im = Image.open(fp).convert("RGB")
            arr = np.array(im)
            sorted_arr = _pixel_sort_frame(arr, threshold, args.vertical)
            Image.fromarray(sorted_arr).save(fp)
            if (i + 1) % 25 == 0 or i == len(frame_paths) - 1:
                print(f"  …{i + 1}/{len(frame_paths)} frames")

        cmd = [
            "ffmpeg",
            "-framerate", str(fps),
            "-i", str(frames_dir / "frame_%06d.png"),
            "-i", str(in_video),
            "-map", "0:v",
            "-map", "1:a?",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-shortest",
            "-movflags", "+faststart",
            str(out_video),
        ]
        command = (cmd[:1] + ["-y"] + cmd[1:]) if getattr(args, "force", False) else cmd
        print("🎬 Encoding…")
        run_ffmpeg_with_progress(command, str(in_video), str(out_video))

    print(f"✅ Finished: {out_video}")
