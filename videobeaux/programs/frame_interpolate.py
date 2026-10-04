# videobeaux/programs/frame_interpolate.py
# Frame Interpolation — smoother motion and smooth slow motion.
#
# ffmpeg's 'minterpolate' filter estimates how things move between two frames and
# paints new in-between frames, so 30 fps footage can become 60 fps (smoother), or be
# slowed to half speed without looking like a slideshow.
#
# Usage (examples):
#   videobeaux -P frame_interpolate -i in.mp4 -o smooth.mp4                    # 2x the frame rate
#   videobeaux -P frame_interpolate -i in.mp4 -o slow.mp4 --multiplier 1 --slow_motion 2
#   videobeaux -P frame_interpolate -i in.mp4 -o out_60.mp4 --fps 60
#
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.media import has_audio


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


# The GUI always supplies the output path (-o) from the connected Output node,
# so this program-specific fallback flag is hidden from the node's fields.
GUI_METADATA = {'args': {
    'outfile': {'hidden': True},
    'multiplier': {'label': 'Frame rate multiplier',
                   'help': '2 = twice as many frames per second (30 → 60: smoother motion). 1 = keep the frame rate (use with Slow motion).',
                   'min': 1, 'max': 8},
    'slow_motion': {'label': 'Slow motion',
                    'help': '1 = normal speed. 2 = half speed, 4 = quarter speed — the extra frames are painted in so it stays smooth.',
                    'min': 1, 'max': 16},
    'fps': {'label': 'Target FPS (optional)',
            'help': 'Set an exact output frame rate (e.g. 60). Leave empty to use the multiplier.'},
    'mi_mode': {'label': 'Quality', 'help': "mci = best (moves detail along with motion, slowest). blend = fast cross-fade. dup = repeat frames."},
    # expert knobs — sensible defaults, kept off the node to keep it simple
    'me-mode': {'hidden': True}, 'mc-mode': {'hidden': True}, 'vsbmc': {'hidden': True},
    'scd': {'hidden': True}, 'x264-preset': {'hidden': True}, 'copy-audio': {'hidden': True},
}}


def register_arguments(parser):
    parser.description = (
        "Frame Interpolation — makes motion smoother, or slows footage down smoothly.\n"
        "It looks at how things move between frames and paints new in-between frames "
        "(ffmpeg 'minterpolate'). Default: doubles the frame rate (30→60 fps). Add --slow_motion 2 "
        "for half speed. It analyses motion, so it's slow on long or large clips; fast scenes can "
        "show warping around moving edges."
    )
    parser.add_argument("--outfile", required=False,
                        help="Output file path (mp4 recommended). Falls back to -o/--output when omitted.")
    parser.add_argument("--multiplier", type=float, default=2.0,
                        help="Multiply the frame rate by this (2 = 30→60 fps). 1 keeps it. Default: 2.")
    parser.add_argument("--slow_motion", type=float, default=1.0,
                        help="Slow down by this factor (2 = half speed). 1 = normal speed. Default: 1.")
    parser.add_argument("--fps", type=float, default=None,
                        help="Exact target frame rate; overrides --multiplier.")
    parser.add_argument("--mi_mode", "--mi-mode", dest="mi_mode", choices=["dup", "blend", "mci"], default="mci",
                        help="Interpolation quality: mci (best), blend (fast), dup (repeat). Default: mci")
    parser.add_argument("--me-mode", choices=["bidir", "bilat"], default="bidir",
                        help="Motion estimation mode. Default: bidir")
    parser.add_argument("--mc-mode", choices=["obmc", "aobmc"], default="aobmc",
                        help="Motion compensation mode. Default: aobmc")
    parser.add_argument("--vsbmc", type=int, choices=[0, 1], default=1,
                        help="Variable-size block motion compensation. 1 = on (better). Default: 1")
    parser.add_argument("--scd", choices=["none", "fdiff", "mv"], default="fdiff",
                        help="Scene change detection. Default: fdiff")
    parser.add_argument("--x264-preset", default="medium", help="libx264 preset (ultrafast..placebo). Default: medium")
    parser.add_argument("--crf", type=float, default=18.0,
                        help="CRF for libx264. Lower = higher quality/larger file. Default: 18")
    parser.add_argument("--copy-audio", action="store_true", help="Copy the audio stream instead of re-encoding it.")


def _resolve_target_fps(args) -> float:
    """Playback frame rate of the result."""
    if args.fps and args.fps > 0:
        return float(args.fps)
    src_fps = _probe_fps(args.input)
    if src_fps <= 0:
        raise RuntimeError("Could not determine the source frame rate; set Target FPS explicitly.")
    mult = args.multiplier if args.multiplier and args.multiplier > 0 else 2.0
    return float(src_fps * mult)


def _atempo_chain(factor: float) -> str:
    """atempo only accepts 0.5–100 per instance; chain halvings for stronger slowdowns."""
    parts = []
    f = factor
    while f < 0.5:
        parts.append("atempo=0.5")
        f /= 0.5
    parts.append(f"atempo={f:.6f}")
    return ",".join(parts)


def _run_ffmpeg_minterpolate(args, target_fps: float):
    slow = args.slow_motion if args.slow_motion and args.slow_motion > 1 else 1.0
    # Paint frames at (playback fps × slowdown), then stretch time so they play at target_fps.
    interp_fps = target_fps * slow
    mi = (
        f"minterpolate=fps={interp_fps:.6f}:mi_mode={args.mi_mode}:"
        f"me_mode={args.me_mode}:mc_mode={args.mc_mode}:vsbmc={args.vsbmc}:scd={args.scd}"
    )
    vf = mi + (f",setpts=PTS*{slow:.6f}" if slow > 1 else "") + ",format=yuv420p"
    command = [
        "ffmpeg", "-err_detect", "ignore_err", "-fflags", "+genpts+discardcorrupt",
        "-i", args.input,
        "-vf", vf,
        "-colorspace", "bt709", "-color_trc", "bt709", "-color_primaries", "bt709",
        "-r", f"{target_fps:.6f}",
        "-c:v", "libx264", "-preset", f"{args.x264_preset}", "-crf", f"{args.crf}",
    ]
    if has_audio(args.input):
        if slow > 1:
            command += ["-af", _atempo_chain(1.0 / slow), "-c:a", "aac"]
        else:
            command += ["-c:a", "copy" if getattr(args, "copy_audio", False) else "aac"]
    else:
        command += ["-an"]
    command.append(args.outfile)
    final_cmd = (command[:1] + ["-y"] + command[1:]) if getattr(args, "force", False) else command
    run_ffmpeg_with_progress(final_cmd, args.input, args.outfile)


def run(args):
    args.outfile = getattr(args, "output", None) or args.outfile
    if not args.outfile:
        raise SystemExit("❌ Missing output. Provide -o/--output or --outfile.")
    target_fps = _resolve_target_fps(args)
    print(f"ℹ️  Output plays at {target_fps:g} fps"
          + (f", {args.slow_motion:g}× slower" if args.slow_motion and args.slow_motion > 1 else "")
          + ". Motion analysis is slow — be patient on long clips.", flush=True)
    _run_ffmpeg_minterpolate(args, target_fps)
