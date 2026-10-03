from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

def register_arguments(parser):
    parser.description = (
        "Rearranges pixels vertically and inversely. Looks kind of like a damaged tape."
    )

    parser.add_argument(
        "--width",
        required=False,
        type=str,
        default="157",
        help="Size in pixels of the shuffled slices. Default: 157."
    )

    parser.add_argument(
        "--position",
        required=False,
        choices=["vertical", "horizontal", "block"],
        default="vertical",
        help="Shuffle direction: vertical slices, horizontal slices, or square blocks. Default: vertical."
    )

def run(args):

    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", f"[0:v]shuffleplanes,shufflepixels=direction=inverse:m={args.position}:width={args.width}[2];[0:v][2]mix[out_v]",
        "-map", "[out_v]",
        "-map", "0:a",
        "-c:v", "libx264",
        "-profile:v", "main",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        args.output
    ]
    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
