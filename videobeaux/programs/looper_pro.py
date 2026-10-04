from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

GUI_METADATA = {
    'args': {
        'size_in_frames': {'label': 'Segment length (frames)', 'min': 1, 'max': 300, 'good_min': 6, 'good_max': 48},
        'loop_count': {'label': 'Repeats', 'min': 1, 'max': 20, 'good_min': 1, 'good_max': 6},
        'start_frame': {'label': 'Start frame', 'min': 0, 'max': 100000, 'good_min': 0, 'good_max': 2000},
    },
}


def register_arguments(parser):
    parser.description = (
        "Apply video looper effect base on frame size & start frame."

    )
    parser.add_argument(
        "--size_in_frames",
        type=int,
        default=12,
        help="The number of frames in the segment to loop."
        
    )
    parser.add_argument(
        "--loop_count",
        type=int,
        default=2,
        help=(
            "Number of additional times to repeat the segment. \n"
            "2 means the segment appears 3 times total (original + 2 repeats)."
        )
    )
    parser.add_argument(
        "--start_frame",
        type=int,
        default=0,
        help=(
            "The starting frame number in the video where the segment begins."
        )
    )
    
def run(args):
    args.size_in_frames = max(1, int(args.size_in_frames))
    args.loop_count = max(1, int(args.loop_count))
    args.start_frame = max(0, int(args.start_frame))
    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", f"[0:v]loop=loop={args.loop_count}:size={args.size_in_frames}:start={args.start_frame}[out_v]",
        "-map", "[out_v]",
        args.output
    ]

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)