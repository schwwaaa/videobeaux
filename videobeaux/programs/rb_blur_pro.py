from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

GUI_METADATA = {
    'args': {
        'strength': {'label': 'Debanding strength', 'min': 0.51, 'max': 4, 'good_min': 0.8, 'good_max': 1.5},
        'radius': {'label': 'Neighborhood (px)', 'min': 4, 'max': 32, 'good_min': 8, 'good_max': 16},
    },
}


def register_arguments(parser):
    parser.description = (
        "Filter to reduce color banding in flat, gradient-heavy areas (e.g., skies, shadows)."
    )

    parser.add_argument(
        "--strength",
        type=float,
        default=1.0,
        help=(
            "Debanding intensity. Higher removes more banding but can soften fine detail. Try ~0.8–1.5; increase if banding persists."
        )
    )

    parser.add_argument(
        "--radius",
        type=int,
        default=12,
        help=(
            "Debanding neighborhood size. Larger helps big smooth gradients (skies) but may smooth texture. Try 8–16."
        )
    )

def run(args):
    args.strength = max(0.51, min(64.0, float(args.strength)))
    args.radius = max(4, min(32, int(args.radius)))

    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", f"[0:v]gradfun=strength={args.strength}:radius={args.radius}[out_v]",
        "-map", "[out_v]",
        "-map", "0:a?",
        args.output
    ]

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
