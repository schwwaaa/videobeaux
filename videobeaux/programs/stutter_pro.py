from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

def register_arguments(parser):
    parser.description = (
        "Imagine watching a video where random frames are played instead of a smooth progression."
    )
    parser.add_argument(
        "--stutter",
        required=True,
        type=str,
        help=(
            "Replaces the current video frame with a randomly selected one from the most recent N frames."
            "The larger the value, the larger the variation."
        )
    )

def run(args):

    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", f"[0:v]random=frames={args.stutter}[out_v]", 
        "-map", "[out_v]",
        "-map", "0:a?",
        args.output
    ]

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
