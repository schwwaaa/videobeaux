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


# ----------------- main entry -----------------


def run(args):
    layout_path = Path(args.layout_json)
    if not layout_path.exists():
        raise FileNotFoundError(f"Layout JSON not found: {layout_path}")

    audio_mode = getattr(args, "audio_mode", "base") or "base"
    audio_src = getattr(args, "audio_src", None)

    if audio_mode == "external" and not audio_src:
        raise ValueError("--audio-mode=external requires --audio-src")

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
    base_w, base_h, base_duration

::contentReference[oaicite:0]{index=0}
