from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress


def register_arguments(parser):
    parser.description = (
        "Animated chromatic aberration: red and blue channels pulse apart from green "
        "and back again over time, instead of sitting at a fixed static offset."
    )
    parser.add_argument(
        "--amount", type=float, default=6.0,
        help="Maximum pixel shift at the peak of the pulse. Default: 6.0."
    )
    parser.add_argument(
        "--speed", type=float, default=2.0,
        help="Pulses per second, roughly. Default: 2.0."
    )


def run(args):
    amt = args.amount
    spd = args.speed
    shift = f"({amt}*sin(2*PI*{spd}*T))"

    # geq's r(x,y)/g(x,y)/b(x,y) input-sampling functions are only valid
    # inside RGB-mode geq expressions (r/g/b) — the lum(x,y) sampler used
    # for YUV-mode geq (lum/cb/cr) is a different mode and errors here.
    filter_complex = (
        f"[0:v]format=gbrp,geq="
        f"r='r(X-{shift},Y)':"
        f"g='g(X,Y)':"
        f"b='b(X+{shift},Y)'[out_v]"
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
