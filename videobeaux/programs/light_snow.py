from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

def register_arguments(parser):
    parser.description = (
        "Applies a light static grain. \n"
        "May also mess with the audio - fix it if you like."

    )
    print("✅ This program mode does not require additional arguments")

    
def run(args):
    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", "[0:v]minterpolate,chromashift=cbh=-5.7:cbv=22:crh=1.44:crv=10.8,deband=1thr=0.45003:2thr=0.48003:3thr=0.21003:4thr=0.30003:range=-1.3:r=16:d=1.69681[out_v]",
        "-map", "[out_v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-profile:v", "high",
        "-level:v", "4.2",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        args.output
    ]

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
