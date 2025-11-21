# videobeaux/programs/lagkage.py
#
# Compose multiple visual layers (images/gifs/videos) on top of a base video
# using a single JSON layout file.
#
# GIF layers are preprocessed into finite MP4s that loop for roughly the base
# video duration, so the main overlay graph stays simple and stable.

import json
import os
import random
import subprocess
from pathlib import Path

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress


def register_arguments(parser):
    parser.description = (
        "Compose multiple visual layers (images/gifs/videos) on a base video "
        "using a JSON layout file. All layers are sized & positioned relative "
        "to the base video dimensions."
    )
    parser.add_argument(
        "--layout-json",
        required=True,
        help="Path to JSON layout describing all layers."
    )
    parser.add_argument(
        "--sequence-direction",
        choices=["forward", "backward", "random"],
        help="Override sequence_direction in the JSON (optional)."
    )


def _load_layout(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        layout = json.load(f)
    if "layers" not in layout or not layout["layers"]:
        raise ValueError("Layout JSON must contain a non-empty 'layers' array.")
    return layout


def _resolve_sequence(layout, override=None):
    seq = override or layout.get("sequence_direction", "forward")
    layers = layout["layers"]
    layers_sorted = sorted(layers, key=lambda L: L.get("layer_number", 0))

    if seq == "forward":
        ordered = layers_sorted
    elif seq == "backward":
        ordered = list(reversed(layers_sorted))
    elif seq == "random":
        ordered = layers_sorted[:]
        random.shuffle(ordered)
    else:
        ordered = layers_sorted

    return seq, ordered


def _probe_base_info(path: str):
    """Return (width, height, duration_seconds) for the base video."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-show_entries", "format=duration",
        "-of", "json",
        path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"ffprobe failed for {path} (code {proc.returncode}): {proc.stderr}"
        )

    data = json.loads(proc.stdout)
    streams = data.get("streams") or []
    if not streams:
        raise RuntimeError(f"No video stream found in {path}")

    s0 = streams[0]
    width = int(s0.get("width", 0) or 0)
    height = int(s0.get("height", 0) or 0)
    if width <= 0 or height <= 0:
        raise RuntimeError(f"Invalid video size from ffprobe for {path}: {width}x{height}")

    fmt = data.get("format") or {}
    dur_str = fmt.get("duration") or "0"
    try:
        duration = float(dur_str)
    except ValueError:
        duration = 0.0

    if duration <= 0:
        duration = 0.0

    return width, height, duration


def _place_expr(layer):
    """Return (x, y) expressions for the overlay filter."""
    mode = layer.get("mode", "free")

    if mode == "free":
        x = str(layer.get("pos_x", 0))
        y = str(layer.get("pos_y", 0))
        return x, y

    slot = layer.get("place", "center")

    if slot == "top_left":
        return "0", "0"
    if slot == "top_right":
        return "W-w", "0"
    if slot == "bottom_left":
        return "0", "H-h"
    if slot == "bottom_right":
        return "W-w", "H-h"

    return "(W-w)/2", "(H-h)/2"


def _preprocess_gif(src: str, base_duration: float, tmp_dir: Path, idx: int) -> str:
    """
    Transcode a GIF to a looping video with alpha that roughly matches
    the base duration.

    IMPORTANT:
    - We force even dimensions so filters/encoders don't choke.
    - We use an alpha-capable codec (qtrle in a MOV container),
      so transparency is preserved instead of being flattened.
    """
    tmp_dir.mkdir(parents=True, exist_ok=True)
    # Use .mov since qtrle is typically stored in a QuickTime container
    temp_path = tmp_dir / f"lagkage_gif_{idx}.mov"

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-ignore_loop", "0",
        "-stream_loop", "-1",
        "-i", src,
        # Make width/height even and ensure we have RGBA (with alpha)
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=rgba",
    ]

    # If we know the base duration, trim to that; otherwise just loop and
    # let the main overlay graph's base video duration cap play-out.
    if base_duration > 0:
        cmd += ["-t", f"{base_duration:.3f}"]

    cmd += [
        # Alpha-capable codec
        "-c:v", "qtrle",
        "-an",
        "-y",
        str(temp_path),
    ]

    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        raise RuntimeError(f"GIF preprocess failed for {src} (code {proc.returncode})")

    return str(temp_path)


def run(args):
    layout_path = Path(args.layout_json)
    if not layout_path.exists():
        raise FileNotFoundError(f"Layout JSON not found: {layout_path}")

    layout = _load_layout(layout_path)
    seq, ordered_layers = _resolve_sequence(layout, args.sequence_direction)

    base_input = args.input
    if not base_input:
        raise ValueError("Global --input (base video) is required for json_layers.")

    # 1) Probe base video info once
    base_w, base_h, base_duration = _probe_base_info(base_input)

    # 2) Prepare inputs for main ffmpeg call
    #    index 0: base video
    #    index 1..N: layer sources (with GIFs preprocessed to MP4)
    inputs_for_ffmpeg = [("base", base_input)]
    layer_inputs = []  # (layer_dict, input_index, target_width_px)

    # Folder to hold temp GIF->MP4 files (next to the output file)
    tmp_dir = Path(args.output).with_suffix("")

    for idx, layer in enumerate(ordered_layers, start=1):
        filename = layer.get("filename")
        if not filename:
            raise ValueError(f"Layer missing 'filename': {layer}")

        # Resolve relative to layout JSON file
        if not os.path.isabs(filename):
            src = str(layout_path.parent / filename)
        else:
            src = filename

        size_pct = float(layer.get("size", 100)) / 100.0
        target_w = max(1, int(base_w * size_pct))

        layer_type = (layer.get("type") or "").lower()

        # If GIF, pre-process to finite-length MP4 that loops to base duration
        if layer_type == "gif":
            overlay_src = _preprocess_gif(src, base_duration, tmp_dir, idx)
        else:
            overlay_src = src

        inputs_for_ffmpeg.append(("video", overlay_src))
        layer_inputs.append((layer, len(inputs_for_ffmpeg) - 1, target_w))

    # 3) Build filter_complex
    filter_parts = []

    # Base video label is [0:v] directly (like overlay_img_pro)
    current_label = "[0:v]"

    for idx, (layer, input_index, target_w) in enumerate(layer_inputs, start=1):
        lay_in = f"[{input_index}:v]"
        lay_alpha = f"[lay{idx}]"
        next_label = f"[tmp{idx}]"

        opacity = float(layer.get("opacity", 1.0))
        # blend_mode is kept for future use but ignored here
        _blend_mode = (layer.get("blend_mode") or "normal").lower()

        x_expr, y_expr = _place_expr(layer)

        # scale + alpha
        filter_parts.append(
            f"{lay_in}"
            f"scale={target_w}:-1,"
            f"format=rgba,colorchannelmixer=aa={opacity}"
            f"{lay_alpha}"
        )

        # overlay
        filter_parts.append(
            f"{current_label}{lay_alpha}"
            f"overlay=x={x_expr}:y={y_expr}:format=auto"
            f"{next_label}"
        )

        current_label = next_label

    out_label = "[out_v]"
    filter_parts.append(f"{current_label}format=yuv420p{out_label}")

    filter_complex = ";".join(filter_parts)

    # 4) Build main ffmpeg command
    command = [
        "ffmpeg",
        "-err_detect", "ignore_err",
        "-fflags", "+discardcorrupt+genpts",
    ]

    for _typ, src in inputs_for_ffmpeg:
        command.extend(["-i", src])

    command.extend([
        "-filter_complex", filter_complex,
        "-map", out_label,
        "-map", "0:a",
        "-c:v", "libx264",
        "-profile:v", "high",
        "-level:v", "4.2",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-c:a", "aac",
        args.output,
    ])

    final_cmd = (command[:1] + ["-y"] + command[1:]) if args.force else command

    run_ffmpeg_with_progress(final_cmd, args.input, args.output)
