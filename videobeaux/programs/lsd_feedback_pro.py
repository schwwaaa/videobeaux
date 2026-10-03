from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

def register_arguments(parser):
    parser.description = (
        "Wicked trippy bro."
    )

    parser.add_argument(
        "--frames",
        required=True,
        type=str,
        help=(
            "Number of frames to mix across time. Higher values create longer motion trails and heavier ghosting. Must be >= 8. Try 8–16."
        )
    )

def run(args):

    command = [
        "ffmpeg",
        "-i", args.input,
        "-vf", f"tmix=frames={args.frames}:weights=1 1 -3 2 1 1 -3 1",
        "-c:v", "libx264",
        "-crf", "23",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "128k",
        "-ac", "2",
        args.output
    ]

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
