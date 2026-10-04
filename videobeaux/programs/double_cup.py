from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

def register_arguments(parser):
    parser.description = (
            "Apply the effect of purple drank. Yum."
    )
    print("✅ no additional arguments required")

def run(args):
    
    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", "[0:v]median=radius=127:radiusV=15:percentile=0.93[3];[0:v]tmix=frames=20:weights=1 2 3 -2 1 2 3 -2 1 -4 4 2 3 -2 1 2 3 -2 1 1[7];[3][7]mix=weights=1 .5[8];[8][0:v]mix=weights=9 -4[out_v]",
        "-map", "[out_v]",
        "-map", "0:a?",
        args.output
    ]
    
    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)

