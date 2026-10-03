from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

GUI_METADATA = {
    'args': {
        'input2': {
            'type': 'file',
            'subtype': 'video',
            'label': 'Second Video',
            'help': 'Video placed on the bottom of the stack — connect a node or pick a file.',
        },
    }
}

def register_arguments(parser):
    parser.description = (
        "Stacks 2 videos, --input on top of --input2, in a vertical column."
        "The shorter video will stop on the last frame while the other continues."
    )
    parser.add_argument(
        "--input2",
        required=True,
        type=str,
        help=(
            "Path to the video you want on the bottom of the stack."
        )
    )

def run(args):

    command = [
        "ffmpeg",
        "-i", args.input,
        "-i", args.input2,
        "-filter_complex", "[0:v][1:v]vstack=inputs=2[v]; [0:a][1:a]amerge=inputs=2[a]", 
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-crf", "23",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "128k",
        "-ac", "2",
        args.output
    ]

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
