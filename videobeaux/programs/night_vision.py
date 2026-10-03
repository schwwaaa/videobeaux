from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress


def register_arguments(parser):
    parser.description = (
        "Green-phosphor night-vision-goggle look — desaturated, tinted green, with "
        "sensor grain and lens vignette falloff."
    )
    parser.add_argument("--grain", type=int, default=18, help="Grain/noise amount. Default: 18.")
    parser.add_argument("--brightness", type=float, default=0.05, help="Brightness boost. Default: 0.05.")


def run(args):
    filter_complex = (
        f"[0:v]hue=s=0,eq=brightness={args.brightness}:contrast=1.4,"
        f"colorchannelmixer=rr=0:rg=0:rb=0:gr=0:gg=1:gb=0:br=0:bg=0:bb=0,"
        f"noise=alls={max(0, args.grain)}:allf=t+u,"
        f"vignette=PI/3[out_v]"
    )
    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", filter_complex,
        "-map", "[out_v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        args.output,
    ]
    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
