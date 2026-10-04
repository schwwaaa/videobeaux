from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

GUI_METADATA = {
    'args': {
        'sigma': {'label': 'Smoothing (sigma)', 'min': 0.1, 'max': 64, 'good_min': 2, 'good_max': 20},
    },
}


def register_arguments(parser):
    parser.description = (
        "Apply filter with a blown out white-balance flare."
    )
    parser.add_argument(
        "--sigma",
        type=float,
        default=5.0,
        help=(
            "Apply bilateral filter, spatial smoothing while preserving edges"
            "Set sigma of gaussian function to calculate spatial weight. Allowed range is 0 to 512. Default is 0.1."
        )
    )

def run(args):
    args.sigma = max(0.0, min(512.0, float(args.sigma)))

    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", f"[0:v]bilateral=sigmaS={args.sigma}[out_v]",
        "-map", "[out_v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-profile:v", "main",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        args.output
    ]

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)

