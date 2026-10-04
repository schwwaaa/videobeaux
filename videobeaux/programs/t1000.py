from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

def register_arguments(parser):
    parser.description = (
        "As if the video surface were made of reflective mercury. \n\n"
        "       'It's just a stutter step.' \n"
        "               -Liquid T-1000          "
    )
    print("✅ no additional arguments required.")

def run(args):

    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", "[0:v]setrange=range=limited,tmedian=radius=19:percentile=0.47,rgbashift=rh=-2:rv=2:gh=-3:gv=3:bh=-4:bv=-2:ah=-12:av=3,tmedian=radius=9:percentile=0.32[out_v]",
        "-map", "[out_v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-profile:v", "main",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        args.output
    ]

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)