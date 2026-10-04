from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

def register_arguments(parser):
    parser.description = (
        "Apply frame stutter akin to a corrupted file."
    )
    print("✅ no additional arguments required")

def run(args):

    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", "[0:v]random=frames=2:seed=212[1];[0:v]tmix=frames=3:weights=1 2 1 -3[4];[1]chromashift=cbh=192:cbv=-97:crh=-76:crv=81:edge=wrap,random=frames=2:seed=243[3];[4][3][0:v]mix=inputs=3:weights=2 1 1 [out_v]", 
        "-map", "[out_v]",
        "-map", "0:a?",
        args.output
    ]

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)