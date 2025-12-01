# videobeaux/programs/lagkage.py
#
# Compose multiple visual layers (images/gifs/videos) on top of a base video
# using a single JSON layout file.
#
# GIF layers are preprocessed into finite-length videos that loop for roughly
# the base video duration, so the main overlay graph stays simple and stable.

import json
import os
import random
import subprocess
import tempfile
import math
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
    parser.add_argument(
        "--audio-mode",
        dest="audio_mode",
        choices=["base", "all", "json_only", "external", "none"],
        default="base",
        help=(
            "How to build the audio track: "
            "base (default base video audio only), "
            "all (base + all JSON media audio mixed), "
            "json_only (only JSON media audio), "
            "external (use --audio-src), "
            "none (no audio)."
        ),
    )
    parser.add_argument(
        "--audio-src",
        dest="audio_src",
        type=str,
        help="External audio file when --audio-mode=external.",
    )


# ----------------- ffprobe helpers -----------------


def _run_ffprobe(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"ffprobe failed (code {proc.returncode}): {proc.stderr.strip()}"
        )
    return proc.stdout


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
    out = _run_ffprobe(cmd)
    data = json.loads(out)

    streams = data.get("streams") or []
    if not streams:
        raise RuntimeError(f"No video stream found in {path!r}")

    s0 = streams[0]
    width = int(s0.get("width") or 0)
    height = int(s0.get("height") or 0)
    duration = float(data["format"].get("duration") or 0.0)
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
    out = _run_ffprobe(cmd)
    line = out.strip()
    if not line:
        raise RuntimeError(f"ffprobe size returned empty output for {path}")
    w_str, h_str = line.split("x")
    return int(w_str), int(h_str)


def _probe_has_audio(path: str) -> bool:
    """
    Return True if the file has at least one audio stream.
    """
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=index",
        "-of",
        "csv=p=0",
        path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode == 0 and proc.stdout.strip() != ""


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


def _resolve_layer_path(filename: str, layout_path: Path) -> str:
    """
    Resolve the media path for a layer in a way that:
    - Leaves absolute paths and URLs alone.
    - Treats '../media/...' as project-root 'media/...'.
    - Treats 'media/...' as-is (relative to current working dir).
    - For simple basenames, keeps layout-relative behavior.
    """
    # URLs
    if "://" in filename:
        return filename

    # Absolute path
    if os.path.isabs(filename):
        return filename

    # Special-case ../media/... -> media/...
    if filename.startswith("../media/"):
        return os.path.normpath("media/" + filename[len("../media/"):])

    # Special-case media/... -> as-is (cwd-relative)
    if filename.startswith("media/"):
        return filename

    # Everything else: layout-relative
    return str((layout_path.parent / filename).resolve())


def _load_layout(layout_path: Path):
    data = json.loads(layout_path.read_text())
    if "layers" not in data or not data["layers"]:
        raise ValueError("Layout JSON has no 'layers' array or it's empty.")
    return data


def _resolve_sequence(layout: dict, cli_seq: str):
    seq = cli_seq or layout.get("sequence_direction") or "forward"
    if seq not in ("forward", "backward", "random"):
        seq = "forward"

    layers = sorted(layout["layers"], key=lambda L: L.get("layer_number", 0))
    if seq == "backward":
        layers = list(reversed(layers))
    elif seq == "random":
        layers = random.sample(layers, len(layers))
    return seq, layers


# ----------------- main entry -----------------


def run(args):
    layout_path = Path(args.layout_json)
    if not layout_path.exists():
        raise FileNotFoundError(f"Layout JSON not found: {layout_path}")

    audio_mode = getattr(args, "audio_mode", "base") or "base"
    audio_src = getattr(args, "audio_src", None)

    if audio_mode == "external" and not audio_src:
        raise ValueError("--audio-mode=external requires --audio-src")

    layout = _load_layout(layout_path)
    seq, ordered_layers = _resolve_sequence(layout, args.sequence_direction)

    base_input = args.input
    if not base_input:
        raise ValueError("Global --input (base video) is required for lagkage.")

    # 1) Probe base video info once
    base_w, base_h, base_duration = _probe_base_info(base_input)
    base_has_audio = _probe_has_audio(base_input)

    # 2) Prepare inputs for main ffmpeg call
    tmp_dir = Path(tempfile.mkdtemp(prefix="lagkage_gifs_"))

    input_files = [base_input]  # index 0 = base
    overlay_specs = []          # (input_index, layer_dict, src_w, src_h)
    overlay_audio_indices = []  # which overlay inputs actually have audio
    audio_vol_db_by_index = {}  # per-input gain in dB

    for idx, layer in enumerate(ordered_layers, start=1):
        filename = layer.get("filename")
        if not filename:
            raise ValueError(f"Layer missing 'filename': {layer}")

        src = _resolve_layer_path(filename, layout_path)
        layer_type = (layer.get("type") or "").lower()

        if layer_type == "gif":
            overlay_src = _preprocess_gif(src, base_duration, tmp_dir, idx)
        else:
            overlay_src = src

        src_w, src_h = _probe_video_size(overlay_src)

        input_files.append(overlay_src)
        in_index = len(input_files) - 1
        overlay_specs.append((in_index, layer, src_w, src_h))

        if _probe_has_audio(overlay_src):
            overlay_audio_indices.append(in_index)

            # Per-layer audio gain: audio_gain_db or audio_gain (linear)
            gain_db = None
            if "audio_gain_db" in layer:
                try:
                    gain_db = float(layer["audio_gain_db"])
                except Exception:
                    gain_db = None
            elif "audio_gain" in layer:
                try:
                    g = float(layer["audio_gain"])
                    if g > 0:
                        gain_db = 20.0 * math.log10(g)
                except Exception:
                    gain_db = None

            if gain_db is not None:
                audio_vol_db_by_index[in_index] = gain_db

    # external audio as extra input
    external_audio_index = None
    if audio_mode == "external":
        if not os.path.isabs(audio_src):
            audio_src_resolved = audio_src  # cwd-relative
        else:
            audio_src_resolved = audio_src
        input_files.append(audio_src_resolved)
        external_audio_index = len(input_files) - 1

    # figure out which indices feed audio mix
    audio_mix_indices = []
    if audio_mode == "all":
        if base_has_audio:
            audio_mix_indices.append(0)
        audio_mix_indices.extend(overlay_audio_indices)
    elif audio_mode == "json_only":
        audio_mix_indices.extend(overlay_audio_indices)
    # base/external/none handled later

    # 3) Build filter_complex (video + optional audio mix)
    filter_parts = []

    # video chain: start from base
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

        # compute overlay box size
        box_w, box_h = _compute_overlay_box(base_w, src_w, src_h, size_pct)

        mode = (layer.get("mode") or "place").lower()
        if mode == "free":
            x_expr = str(int(layer.get("pos_x", 0)))
            y_expr = str(int(layer.get("pos_y", 0)))
        else:
            place = (layer.get("place") or "center").lower()
            px, py = _compute_place_coordinates(place, base_w, base_h, box_w, box_h)
            x_expr, y_expr = str(px), str(py)

        in_label = f"[{in_index}:v]"
        layer_label = f"[lay{idx}]"
        next_label = f"[tmp{idx}]"

        layer_filters = []

        # optional crop (percent of source BEFORE zoom/scale)
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

        # zoom inside fixed box:
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

        filter_parts.append(f"{in_label}{','.join(layer_filters)}{layer_label}")

        # overlay
        filter_parts.append(
            f"{current_label}{layer_label}"
            f"overlay=x={x_expr}:y={y_expr}:format=auto"
            f"{next_label}"
        )

        current_label = next_label

    out_v_label = "[out_v]"
    filter_parts.append(f"{current_label}format=yuv420p{out_v_label}")

    # audio mix (for all/json_only + per-layer gain)
    audio_filter_output = None

    if audio_mode in ("all", "json_only") and len(audio_mix_indices) >= 1:
        if len(audio_mix_indices) == 1:
            # Single audio source: optionally apply volume, no amix needed
            idx = audio_mix_indices[0]
            gain_db = audio_vol_db_by_index.get(idx)
            if gain_db is not None:
                audio_filter_output = "[out_a]"
                filter_parts.append(
                    f"[{idx}:a]volume={gain_db}dB{audio_filter_output}"
                )
            else:
                # direct map of the input's audio stream
                audio_filter_output = f"{idx}:a"
        else:
            # Multiple sources: per-input volume (if any), then amix
            audio_inputs = []
            for idx in audio_mix_indices:
                gain_db = audio_vol_db_by_index.get(idx)
                if gain_db is not None:
                    lbl = f"[av{idx}]"
                    filter_parts.append(
                        f"[{idx}:a]volume={gain_db}dB{lbl}"
                    )
                    audio_inputs.append(lbl)
                else:
                    audio_inputs.append(f"[{idx}:a]")

            audio_filter_output = "[out_a]"
            filter_parts.append(
                "".join(audio_inputs)
                + f"amix=inputs={len(audio_mix_indices)}:normalize=0{audio_filter_output}"
            )

    filter_complex = ";".join(filter_parts)

    # 4) Build main ffmpeg command
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error"]

    for path in input_files:
        command.extend(["-i", path])

    command.extend(["-filter_complex", filter_complex, "-map", out_v_label])

    # audio mapping according to mode
    if audio_mode == "base":
        command.extend(["-map", "0:a?"])
    elif audio_mode in ("all", "json_only"):
        if len(audio_mix_indices) == 0:
            # no audio
            pass
        elif len(audio_mix_indices) == 1:
            if audio_filter_output == "[out_a]":
                command.extend(["-map", audio_filter_output])
            else:
                # audio_filter_output is like "N:a"
                command.extend(["-map", audio_filter_output])
        else:
            command.extend(["-map", audio_filter_output or "0:a?"])
    elif audio_mode == "external":
        if external_audio_index is not None:
            command.extend(["-map", f"{external_audio_index}:a?"])
    elif audio_mode == "none":
        command.append("-an")

    # video codec settings
    command.extend(
        [
            "-c:v",
            "libx264",
            "-profile:v",
            "high",
            "-level:v",
            "4.2",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
        ]
    )

    # audio codec if not explicitly disabled
    if audio_mode != "none":
        command.extend(["-c:a", "aac"])

    command.append(args.output)

    final_cmd = (command[:1] + ["-y"] + command[1:]) if args.force else command
    run_ffmpeg_with_progress(final_cmd, args.input, args.output)
