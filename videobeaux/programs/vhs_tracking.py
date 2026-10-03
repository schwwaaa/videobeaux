from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress


def register_arguments(parser):
    parser.description = (
        "Classic worn-VHS-tape look: horizontal tracking-jitter wobble plus chroma "
        "bleed/smear, like a tape that's been rewound one too many times."
    )
    parser.add_argument(
        "--intensity", type=float, default=1.0,
        help="Overall strength multiplier for the chroma bleed, grain, and jitter. Default: 1.0."
    )
    parser.add_argument(
        "--speed", type=float, default=6.0,
        help="Wobble frequency — higher jitters faster. Default: 6.0."
    )


def run(args):
    bleed = max(1, int(round(6 * args.intensity)))
    jitter = max(1, int(round(6 * args.intensity)))
    noise_amt = max(1, int(round(10 * args.intensity)))

    filter_complex = (
        f"[0:v]chromashift=cbh={bleed}:crh=-{bleed},"
        f"noise=alls={noise_amt}:allf=t+u,"
        f"crop=iw-{jitter * 2}:ih:{jitter}+{jitter}*sin(t*{args.speed}):0,"
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
