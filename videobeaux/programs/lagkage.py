# videobeaux/programs/lagkage.py
#
# Compose multiple visual layers (images/gifs/videos) on top of a base video
# using a single JSON layout file.
#
# GIF layers are preprocessed into finite videos that loop for roughly the base
# video duration, so the main overlay graph stays simple and stable.

import json
import os
import random
import subprocess
import tempfile
from pathlib import Path

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress


def register_arguments(parser):
    parser.description = (
        "Compose a base video with layered media defined by a JSON layout "
        "(images / videos / GIFs) using the lagkage compositor."
    )
    parser.add_argument(
        "--layout-json",
        dest="layout_json",
        required=True,
        type=str,
        help="Path to layout JSON describing layers.",
    )
    parser.add_argument(
        "--sequence-direction",
        dest="sequence_direction",
        choices=["forward", "backward", "random"],
        default=None,
        help="Override sequence_direction from JSON (forward|backward|random).",
    )


# ----------------- ffprobe helpers -----------------


def _probe_base_info(path: str):
    """
    Return (width, height, duration_seconds) for the base video.
    """
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed for base {path}: {proc.stderr}")
    info = json.loads(proc.stdout)

    width = int(info["streams"][0]["width"])
    height = int(info["streams"][0]["height"])
    duration = float(info["format"]["duration"])
    return width, height, duration


def _probe_video_size(path: str):
    """
    Return (width, height) of the first video/image stream.
    """
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=s=x:p=0",
        path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe size failed for {path}: {proc.stderr}")
    line = proc.stdout.strip()
    if not line:
        raise RuntimeError(f"ffprobe size returned empty output for {path}")
    w_str, h_str = line.split("x")
    return int(w_str), int(h_str)


# ----------------- small helpers -----------------


def _even(x: int) -> int:
    """
    Force an integer to be even (needed for some codecs / filters).
    """
    return x if x % 2 == 0 else x + 1


def _preprocess_gif(src: str, base_duration: float, tmp_dir: Path, idx: int) -> str:
    """
    Convert GIF to a looping RGBA video with even dimensions and alpha.
    Returns path to the temp video file.

    - Loops the GIF for approximately base_duration.
    - Forces even width/height.
    - Keeps alpha via format=rgba + qtrle.
    """
    tmp_dir.mkdir(parents=True, exist_ok=True)
    out_path = tmp_dir / f"gif_pre_{idx:03d}.mov"

    vf = "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=rgba"

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ignore_loop",
        "0",
        "-stream_loop",
        "-1",
        "-i",
        src,
        "-t",
        f"{base_duration:.3f}",
        "-vf",
        vf,
        "-c:v",
        "qtrle",
        "-an",
        str(out_path),
    ]
    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        raise RuntimeError(f"GIF preprocess failed for {src} (code {proc.returncode})")

    return str(out_path)


def _compute_place_coordinates(place: str, base_w: int, base_h: int,
                               box_w: int, box_h: int):
    """
    Compute overlay x,y for place mode, given base and box dimensions.
    """
    place = (place or "center").lower()
    if place == "top_left":
        return 0, 0
    elif place == "top_right":
        return base_w - box_w, 0
    elif place == "bottom_left":
        return 0, base_h - box_h
    elif place == "bottom_right":
        return base_w - box_w, base_h - box_h
    elif place == "center":
        return (base_w - box_w) // 2, (base_h - box_h) // 2
    else:
        # Fallback to center for unknown place values
        return (base_w - box_w) // 2, (base_h - box_h) // 2


def _compute_overlay_box(base_w: int, src_w: int, src_h: int, size_pct: float):
    """
    Compute the final overlay box width/height (even integers) based on:
    - base width
    - layer source aspect ratio
    - size percentage of base width.
    """
    if size_pct <= 0:
        size_pct = 1.0

    target_w = int(base_w * (size_pct / 100.0))
    if target_w < 2:
        target_w = 2
    target_w = _even(target_w)

    if src_h > 0:
        ar = src_w / src_h
        target_h = int(target_w / ar) if ar > 0 else target_w
    else:
        target_h = target_w

    if target_h < 2:
        target_h = 2
    target_h = _even(target_h)

    return target_w, target_h


# ----------------- main entry -----------------


def run(args):
    layout_path = Path(args.layout_json)
    if not layout_path.exists():
        raise FileNotFoundError(f"Layout JSON not found: {layout_path}")

    # Load layout JSON
    layout = json.loads(layout_path.read_text())
    layers = layout.get("layers", [])
    if not isinstance(layers, list) or not layers:
        raise ValueError("Layout JSON has no 'layers' array or it's empty.")

    # Determine sequence direction
    seq_dir = args.sequence_direction or layout.get("sequence_direction", "forward")
    if seq_dir not in ("forward", "backward", "random"):
        seq_dir = "forward"

    # Order layers by layer_number, then adjust sequence if needed
    ordered_layers = sorted(layers, key=lambda L: L.get("layer_number", 0))
    if seq_dir == "backward":
        ordered_layers = list(reversed(ordered_layers))
    elif seq_dir == "random":
        ordered_layers = random.sample(ordered_layers, len(ordered_layers))

    base_input = args.input
    if not base_input:
        raise ValueError("Global --input (base video) is required for lagkage.")

    # Probe base
    base_w, base_h, base_duration = _probe_base_info(base_input)

    # Temp dir for GIF preprocess
    tmp_dir = Path(tempfile.mkdtemp(prefix="lagkage_gifs_"))

    # 1) Build input list for ffmpeg
    # input 0 = base, 1..N = overlays
    input_files = [base_input]
    overlay_specs = []  # (input_index, layer_dict, src_w, src_h)

    for idx, layer in enumerate(ordered_layers, start=1):
        filename = layer.get("filename")
        if not filename:
            raise ValueError(f"Layer missing 'filename': {layer}")

        # Relative paths are relative to the layout JSON directory.
        if not os.path.isabs(filename):
            src = str(layout_path.parent / filename)
        else:
            src = filename

        layer_type = (layer.get("type") or "").lower()

        # If GIF, pre-process to finite-length video that loops to base duration
        if layer_type == "gif":
            overlay_src = _preprocess_gif(src, base_duration, tmp_dir, idx)
        else:
            overlay_src = src

        src_w, src_h = _probe_video_size(overlay_src)

        input_files.append(overlay_src)
        in_index = len(input_files) - 1
        overlay_specs.append((in_index, layer, src_w, src_h))

    # 2) Build filter_complex
    filter_parts = []

    # Start with base video
    current_label = "[0:v]"

    for idx, (in_index, layer, src_w, src_h) in enumerate(overlay_specs, start=1):
        size_pct = float(layer.get("size", 100.0))
        opacity = float(layer.get("opacity", 1.0))
        if opacity < 0.0:
            opacity = 0.0
        if opacity > 1.0:
            opacity = 1.0

        zoom = float(layer.get("zoom", 1.0))
        if zoom < 1.0:
            zoom = 1.0

        # Compute final overlay box size on the base
        box_w, box_h = _compute_overlay_box(base_w, src_w, src_h, size_pct)

        mode = (layer.get("mode") or "place").lower()

        if mode == "free":
            x_expr = str(int(layer.get("pos_x", 0)))
            y_expr = str(int(layer.get("pos_y", 0)))
        else:
            place = layer.get("place", "center")
            px, py = _compute_place_coordinates(place, base_w, base_h, box_w, box_h)
            x_expr, y_expr = str(px), str(py)

        in_label = f"[{in_index}:v]"
        layer_label = f"[lay{idx}]"
        next_label = f"[tmp{idx}]"

        layer_filters = []

        # Optional crop (percent of source, BEFORE zoom/scale)
        cx = layer.get("crop_x")
        cy = layer.get("crop_y")
        cw = layer.get("crop_w")
        ch = layer.get("crop_h")
        if cx is not None and cy is not None and cw is not None and ch is not None:
            try:
                cx_f = float(cx) / 100.0
                cy_f = float(cy) / 100.0
                cw_f = float(cw) / 100.0
                ch_f = float(ch) / 100.0
                layer_filters.append(
                    f"crop=in_w*{cw_f}:in_h*{ch_f}:in_w*{cx_f}:in_h*{cy_f}"
                )
            except Exception:
                # If parsing fails, skip cropping instead of blowing up.
                pass

        # Zoom INSIDE fixed box:
        # 1) scale up to zoom * box size
        # 2) crop center back down to box_w x box_h
        scaled_w = _even(int(box_w * zoom))
        scaled_h = _even(int(box_h * zoom))
        if scaled_w < 2:
            scaled_w = 2
        if scaled_h < 2:
            scaled_h = 2

        layer_filters.append(f"scale={scaled_w}:{scaled_h}")

        if zoom > 1.0:
            layer_filters.append(
                f"crop={box_w}:{box_h}:(iw-{box_w})/2:(ih-{box_h})/2"
            )

        # Force RGBA and apply opacity
        layer_filters.append("format=rgba")
        layer_filters.append(f"colorchannelmixer=aa={opacity}")

        filter_parts.append(
            f"{in_label}{','.join(layer_filters)}{layer_label}"
        )

        # Overlay on top of current composite
        filter_parts.append(
            f"{current_label}{layer_label}"
            f"overlay=x={x_expr}:y={y_expr}:format=auto"
            f"{next_label}"
        )

        current_label = next_label

    out_label = "[out_v]"
    filter_parts.append(f"{current_label}format=yuv420p{out_label}")

    filter_complex = ";".join(filter_parts)

    # 3) Build main ffmpeg command
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error"]

    for path in input_files:
        command.extend(["-i", path])

    command.extend([
        "-filter_complex", filter_complex,
        "-map", out_label,
        "-map", "0:a?",
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
