from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

GUI_METADATA = {
    'args': {
        'frames': {'label': 'Frames mixed', 'min': 8, 'max': 32, 'good_min': 8, 'good_max': 16},
    },
}


def register_arguments(parser):
    parser.description = (
        "Wicked trippy bro."
    )

    parser.add_argument(
        "--frames",
        type=int,
        default=8,
        help=(
            "Number of frames to mix across time. Higher values create longer motion trails and heavier ghosting. Must be >= 8. Try 8–16."
        )
    )

def run(args):
    args.frames = max(8, min(128, int(args.frames)))   # the built-in weight pattern needs at least 8

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
