from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress


def register_arguments(parser):
    parser.description = (
        "Vintage film-print damage — desaturated/faded vintage color grade, grain and "
        "dust, random brightness flicker, and a subtle gate-weave jitter."
    )
    parser.add_argument("--intensity", type=float, default=1.0, help="Overall strength multiplier. Default: 1.0.")


def run(args):
    i = args.intensity
    grain = max(1, int(round(22 * i)))
    flicker_amt = 0.06 * i
    jitter = max(1, int(round(3 * i)))
    flicker_expr = f"lt(random(1)\\,{0.15 * i})"

    filter_complex = (
        f"[0:v]curves=preset=vintage,"
        f"noise=alls={grain}:allf=t+u,"
        f"eq=brightness={flicker_amt}*sin(t*37):enable='{flicker_expr}',"
        f"crop=iw-{jitter * 2}:ih:{jitter}+{jitter // 2 + 1}*sin(t*11):0,"
        f"pad=iw+{jitter * 2}:ih:{jitter}:0[out_v]"
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
