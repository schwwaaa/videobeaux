# videobeaux/programs/frame_interpolate.py
# Frame Interpolation — Create slow motion / higher FPS
# Backends:
#   - ffmpeg (minterpolate) ✅ fully implemented
#   - rife-ncnn (external tool) 🚧 scaffold only
#   - dain-ncnn (external tool) 🚧 scaffold only
#
# Usage (examples at bottom):
#   videobeaux -P frame_interpolate -i in.mp4 --outfile out_60fps.mp4 --fps 60
#
# Notes:
# - Uses --outfile (do NOT use global -o).
# - If you prefer a multiplier (e.g., 2x), pass --multiplier 2 and omit --fps.
#   We'll compute FPS via ffprobe.
# - Default engine is 'ffmpeg' (pure minterpolate).
#
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress


def _probe_fps(input_path: str) -> float:
    """
    Read avg_frame_rate via ffprobe and convert to float FPS.
    Falls back to r_frame_rate if needed.
    """
    def _rate_to_float(rate: str) -> float:
        if not rate or rate == "0/0":
            return 0.0
        if "/" in rate:
            num, den = rate.split("/")
            try:
                return float(num) / float(den)
            except Exception:
                return 0.0
        try:
            return float(rate)
        except Exception:
            return 0.0

    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=avg_frame_rate,r_frame_rate",
        "-of", "json",
        input_path
    ]
    out = subprocess.check_output(cmd).decode("utf-8", errors="ignore")
    data = json.loads(out)
    streams = data.get("streams", [])
    if not streams:
        return 0.0
    s0 = streams[0]
    fps = _rate_to_float(s0.get("avg_frame_rate") or "")
    if fps == 0.0:
        fps = _rate_to_float(s0.get("r_frame_rate") or "")
    return fps


def register_arguments(parser):
    parser.description = (
        "Frame Interpolation\n"
        "Create slow motion or higher FPS output using one of:\n"
        "  • ffmpeg 'minterpolate' (default, no extra installs)\n"
        "  • rife-ncnn (external binary; scaffold only)\n"
        "  • dain-ncnn (external binary; scaffold only)\n"
    )

    # Output path (do NOT use global -o)
    parser.add_argument(
        "--outfile",
        required=True,
        help="Output file path for the interpolated result (mp4 recommended)."
    )

    # Engine selection
    parser.add_argument(
        "--engine",
        choices=["ffmpeg", "rife-ncnn", "dain-ncnn"],
        default="ffmpeg",
        help="Interpolation backend. Default: ffmpeg (minterpolate)."
    )

    # Target FPS OR multiplier
    parser.add_argument(
        "--fps",
        type=float,
        help="Target output FPS (e.g., 60, 120). If omitted, you can use --multiplier."
    )
    parser.add_argument(
        "--multiplier",
        type=float,
        help="Multiply input FPS by this factor (e.g., 2.0 → 30→60). Ignored if --fps is provided."
    )

    # FFmpeg minterpolate knobs (expert)
    parser.add_argument(
        "--mi-mode",
        choices=["dup", "blend", "mci"],
        default="mci",
        help="Motion interpolation mode. 'mci' gives best quality. Default: mci"
    )
    parser.add_argument(
        "--me-mode",
        choices=["bidir", "bilat"],
        default="bidir",
        help="Motion estimation mode. Default: bidir"
    )
    parser.add_argument(
        "--mc-mode",
        choices=["obmc", "aobmc"],
        default="aobmc",
        help="Motion compensation mode. Default: aobmc"
    )
    parser.add_argument(
        "--vsbmc",
        type=int,
        choices=[0, 1],
        default=1,
        help="Variable-size block motion compensation. 1 = on (better). Default: 1"
    )
    parser.add_argument(
        "--scd",
        choices=["none", "fdiff", "mv"],
        default="fdiff",
        help="Scene change detection. Default: fdiff"
    )

    # Encoding controls
    parser.add_argument(
        "--x264-preset",
        default="medium",
        help="libx264 preset (ultrafast..placebo). Default: medium"
    )
    parser.add_argument(
        "--crf",
        type=float,
        default=18.0,
        help="CRF for libx264. Lower = higher quality/larger file. Default: 18"
    )
    parser.add_argument(
        "--copy-audio",
        action="store_true",
        help="Copy audio stream instead of re-encoding."
    )

    # External binary paths (scaffolds)
    parser.add_argument(
        "--rife-bin",
        default="rife-ncnn-vulkan",
        help="[rife-ncnn] Path to rife-ncnn-vulkan executable (if using --engine rife-ncnn)."
    )
    parser.add_argument(
        "--dain-bin",
        default="dain-ncnn-vulkan",
        help="[dain-ncnn] Path to dain-ncnn-vulkan executable (if using --engine dain-ncnn)."
    )


def _resolve_target_fps(args) -> float:
    if args.fps and args.fps > 0:
        return float(args.fps)
    if args.multiplier and args.multiplier > 0:
        src_fps = _probe_fps(args.input)
        if src_fps <= 0:
            raise RuntimeError("Could not determine source FPS via ffprobe; please pass --fps explicitly.")
        return float(src_fps * args.multiplier)
    raise RuntimeError("You must provide either --fps or --multiplier.")


def _run_ffmpeg_minterpolate(args, target_fps: float):
    """
    Build and run a pure-FFmpeg minterpolate pipeline.
    """
    # Construct minterpolate filter
    mi = (
        f"minterpolate=fps={target_fps}:mi_mode={args.mi_mode}:"
        f"me_mode={args.me_mode}:mc_mode={args.mc_mode}:vsbmc={args.vsbmc}:scd={args.scd}"
    )

    filtergraph = f"{mi},format=yuv420p"
    command = [
        "ffmpeg",
        "-err_detect", "ignore_err",
        "-fflags", "+genpts+discardcorrupt",
        "-i", args.input,

        "-vf", filtergraph,

        # Keep SDR tagging sane
        "-colorspace", "bt709",
        "-color_trc", "bt709",
        "-color_primaries", "bt709",

        "-r", f"{target_fps}",               # ensure container/timebase reflects new fps
        "-c:v", "libx264",
        "-preset", f"{args.x264_preset}",
        "-crf", f"{args.crf}",

        "-c:a", "copy" if getattr(args, "copy_audio", False) else "aac",
        args.outfile,
    ]
    final_cmd = (command[:1] + ["-y"] + command[1:]) if getattr(args, "force", False) else command
    run_ffmpeg_with_progress(final_cmd, args.input, args.outfile)


def _run_rife_scaffold(args, target_fps: float):
    """
    Scaffold placeholder for RIFE. Left as a clear error with guidance.
    """
    raise NotImplementedError(
        "RIFE backend is scaffolded but not implemented here.\n"
        "Install rife-ncnn-vulkan and wire a frames→frames workflow:\n"
        "  1) ffmpeg: extract frames (source fps) to a temp dir\n"
        "  2) rife-ncnn-vulkan: interpolate to target fps (temp dir → temp dir)\n"
        "  3) ffmpeg: encode interpolated frames + original audio → --outfile\n"
        "For now, use --engine ffmpeg (minterpolate) which is fully implemented."
    )


def _run_dain_scaffold(args, target_fps: float):
    """
    Scaffold placeholder for DAIN. Left as a clear error with guidance.
    """
    raise NotImplementedError(
        "DAIN backend is scaffolded but not implemented here.\n"
        "Install dain-ncnn-vulkan and wire a frames→frames workflow similar to RIFE.\n"
        "For now, use --engine ffmpeg (minterpolate) which is fully implemented."
    )


def run(args):
    outfile = Path(args.outfile)
    if outfile.suffix.lower() != ".mp4":
        # We allow any extension, but mp4+x264 is what most of videobeaux uses.
        pass

    target_fps = _resolve_target_fps(args)

    if args.engine == "ffmpeg":
        _run_ffmpeg_minterpolate(args, target_fps)
        return
    elif args.engine == "rife-ncnn":
        _run_rife_scaffold(args, target_fps)
    elif args.engine == "dain-ncnn":
        _run_dain_scaffold(args, target_fps)
    else:
        raise RuntimeError(f"Unknown engine: {args.engine}")
