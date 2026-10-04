from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

GUI_METADATA = {
    'args': {
        'horiz_speed': {'label': 'Horizontal speed', 'min': -1, 'max': 1, 'good_min': -0.05, 'good_max': 0.05, 'step': 0.001},
        'vert_speed': {'label': 'Vertical speed', 'min': -1, 'max': 1, 'good_min': -0.05, 'good_max': 0.05, 'step': 0.001},
    },
}


def register_arguments(parser):
    parser.description = (
        "Apply video scrolling effect with definable directions."
    )
    parser.add_argument(
        "--horiz_speed",
        type=float,
        default=0.01,
        help=(
            "Value between -1.0 and 1.0 representing scroll speed left to right as a fraction of the frame size per frame. \n"
            "0.01 scrolls left by 1 percent of the frame width per frame."
        )
    )
    parser.add_argument(
        "--vert_speed",
        type=float,
        default=0.0,
        help=(
            "Value between -1.0 and 1.0 representing scroll speed up to down as a fraction of the frame size per frame. \n"
            "0.005: Scrolls up by 0.5 percent of the frame height per frame."
        )
    )

def run(args):
    args.horiz_speed = max(-1.0, min(1.0, float(args.horiz_speed)))
    args.vert_speed = max(-1.0, min(1.0, float(args.vert_speed)))

    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", f"[0:v]scroll=horizontal={args.horiz_speed}:vertical={args.vert_speed}[out_v]", 
        "-map", "[out_v]",
        "-map", "0:a?",
        args.output
    ]

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
