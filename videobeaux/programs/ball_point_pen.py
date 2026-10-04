from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

def register_arguments(parser):
    parser.description = (
            "Applies a hand-drawn blue ballpoint pen effect with sketch-like lines and shading. \n"
            "It also fucks with the audio, wich may or may not be fixed in a future release."
    )
    print("✅ This program mode does not require additional arguments")

def run(args):
    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", "[0:v]setpts=PTS-STARTPTS,tpad=start=10:start_mode=clone:stop=60:stop_mode=clone,amplify=radius=6:factor=2,bwdif=mode=send_frame:parity=bff,colorbalance=gs=-0.34:bs=0.47:rm=-0.18:gm=-0.7:bm=0.5,trim=start_frame=10,format=yuv420p[out_v]",
        "-map", "[out_v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-profile:v", "high",
        "-level:v", "4.2",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        args.output
    ]
    print(" ".join(f'"{arg}"' if ' ' in arg or ':' in arg or '=' in arg else arg for arg in command))
    
    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
