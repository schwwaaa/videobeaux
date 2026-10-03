from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress


def register_arguments(parser):
    parser.description = (
        "Periodic flash/strobe effect — brightness spikes to near-white for a brief "
        "window at a configurable interval."
    )
    parser.add_argument(
        "--period", type=float, default=0.5,
        help="Seconds between flashes. Default: 0.5."
    )
    parser.add_argument(
        "--flash_duration", type=float, default=0.05,
        help="How long each flash lasts, in seconds. Default: 0.05."
    )


def run(args):
    enable = f"lt(mod(t\\,{args.period})\\,{args.flash_duration})"
    filter_complex = f"[0:v]eq=brightness=1:contrast=2:enable='{enable}'[out_v]"
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
