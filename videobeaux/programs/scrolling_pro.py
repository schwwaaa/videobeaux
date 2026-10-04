from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

def register_arguments(parser):
    parser.description = (
        "Apply video scrolling effect with definable directions."
    )
    parser.add_argument(
        "--horiz_speed",
        required=True,
        type=str,
        help=(
            "Value between -1.0 and 1.0 representing scroll speed left to right as a fraction of the frame size per frame. \n"
            "0.01 scrolls left by 1 percent of the frame width per frame."
        )
    )
    parser.add_argument(
        "--vert_speed",
        required=True,
        type=str,
        help=(
            "Value between -1.0 and 1.0 representing scroll speed up to down as a fraction of the frame size per frame. \n"
            "0.005: Scrolls up by 0.5 percent of the frame height per frame."
        )
    )

def run(args):

    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", f"[0:v]scroll=horizontal={args.horiz_speed}:vertical={args.vert_speed}[out_v]", 
        "-map", "[out_v]",
        "-map", "0:a?",
        args.output
    ]

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
