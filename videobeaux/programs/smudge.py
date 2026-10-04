from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

def register_arguments(parser):
    parser.description = (
        "Introduces motion-like smudges for a soft, blended output."
    )
    print("✅ no additional arguments required.")

def run(args):

    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", "[0:v]setpts=PTS-STARTPTS,tpad=start=7:start_mode=clone:stop=30:stop_mode=clone,setrange=range=limited,tmedian=radius=7,trim=start_frame=7,format=yuv420p[out_v]",
        "-map", "[out_v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-profile:v", "main",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        args.output
    ]

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)