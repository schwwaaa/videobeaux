from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

def register_arguments(parser):
    parser.description = (
            "Apply bad Predator heat vision effect"
    )
    print("✅ This program mode does not require additional arguments")

def run(args):
    
    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", "[0:v]setpts=PTS-STARTPTS,shuffleplanes=map0=0:map1=1:map2=2,tpad=start=33:start_mode=clone:stop=33:stop_mode=clone,smartblur=luma_radius=1.6:luma_strength=0.11:lt=-17:cr=0.93,amplify=radius=33:factor=4:threshold=10721.12:tolerance=12:low=12420.26:high=49802.12,despill=mix=0.58:expand=0.85:red=-1.2:green=1.21:blue=2.3:brightness=4.45:alpha=false,lagfun=decay=0.85,trim=start_frame=33,format=yuv420p[out_v]",
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

