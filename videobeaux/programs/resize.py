from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

GUI_METADATA = {
    'args': {
        'new_width': {'label': 'Width (px, -2 = keep aspect)', 'min': -2, 'max': 7680, 'good_min': 640, 'good_max': 3840},
        'new_height': {'label': 'Height (px, -2 = keep aspect)', 'min': -2, 'max': 7680, 'good_min': 360, 'good_max': 2160},
    },
}


def register_arguments(parser):
    parser.description = (
        "Akin to repainting the same image while smudged with alcohol."
    )
    parser.add_argument(
        "--new_height",
        type=int,
        default=720,
        help="Height, in pixels of the desiered resized --output video."
    )
    parser.add_argument(
        "--new_width",
        type=int,
        default=1280,
        help="Width, in pixels of the desiered resized --output video."
    )

def run(args):

    command = [
        "ffmpeg",
        "-i", args.input,
        "-vf", f"scale={args.new_width}:{args.new_height}",
        args.output
    ]

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)