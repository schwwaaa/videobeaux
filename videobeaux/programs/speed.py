from videobeaux.utils.media import ensure_audio
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from pathlib import Path
import sys

"""
TODO: 
--------------------------------
- break setpts and atempto into 
    two separate speed factor args

- chain atempo filters if 
    speed_factor is outside of 
    default range

"""

def register_arguments(parser):
    parser.description = (
        "Changes the speed of the video file."
        "Will change the speed of the audio to the same speed_factor, without changing the pitch."
    )
    parser.add_argument(
        "--speed_factor",
        required=True,
        type=float,
        help=(
            "Value must be >= 0.5 \n"
            "Speed up: For speed_factor > 1, video plays faster. \n"
            "Slow down: For speed_factor < 1, video plays slower."
        )
    )

def run(args):
    # audio filter graphs need an audio track on every input
    if getattr(args, 'input', None):
        args.input = ensure_audio(args.input)

    if args.speed_factor < 0.5:
        print(f"❌ --speed_factor must be greater than 0.5")
        sys.exit(1)

    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", f"[0:v]setpts=PTS/{args.speed_factor}[v];[0:a]atempo={args.speed_factor}[a]",
        "-map", "[v]",
        "-map", "[a]",
        args.output
    ]

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
