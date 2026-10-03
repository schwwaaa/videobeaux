from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress


def register_arguments(parser):
    parser.description = (
        "The 'deep-fried meme' look: blown-out saturation and contrast, oversharpened, "
        "baked-in compression artifacts."
    )
    parser.add_argument(
        "--intensity", type=float, default=1.0,
        help="Overall strength multiplier. Default: 1.0."
    )


def run(args):
    i = args.intensity
    contrast = 1.0 + 0.8 * i
    saturation = 1.0 + 2.0 * i
    brightness = 0.05 * i
    sharpen = 2.0 * i
    noise_amt = max(1, int(round(8 * i)))
    crf = min(51, int(round(20 + 12 * i)))

    filter_complex = (
        f"[0:v]eq=contrast={contrast}:saturation={saturation}:brightness={brightness},"
        f"unsharp=7:7:{sharpen}:7:7:0.0,"
        f"noise=alls={noise_amt}:allf=t[out_v]"
    )
    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", filter_complex,
        "-map", "[out_v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", str(crf),
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        args.output,
    ]
    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
