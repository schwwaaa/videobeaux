from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

def register_arguments(parser):
    parser.description = (
        "Causes a dramatic bloom or edge glow. Like overexposure/ video burn."
    )
    print("✅ no additional arguments required")

def run(args):

    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", "[0:v]setpts=PTS-STARTPTS,tpad=start=7:start_mode=clone:stop=30:stop_mode=clone,setrange=range=limited,amplify=radius=14:factor=20[out_v]",
        "-map", "[out_v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-profile:v", "main",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        args.output
    ]
    print(" ".join(f'"{arg}"' if ' ' in arg or ':' in arg or '=' in arg else arg for arg in command))

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)