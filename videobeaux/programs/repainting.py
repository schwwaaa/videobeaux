from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

def register_arguments(parser):
    parser.description = (
        "Akin to repainting the same image while smudged with alcohol."
    )
    print("✅ no additional arguments required")

def run(args):

    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", "[0:v]median=radius=127:radiusV=15:percentile=0.43[3];[0:v]tmix=frames=20:weights=1 2 3 -2 1 2 3 -2 1 -4 4 2 3 -2 1 2 3 -2 1 1[7];[3][7]mix,lagfun=decay=1[out_v]",
        "-map", "[out_v]",
        "-map", "0:a?",
        args.output
    ]

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)