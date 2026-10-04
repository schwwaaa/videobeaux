from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

GUI_METADATA = {
    'args': {
        'radius': {'label': 'Radius (px)', 'min': 1, 'max': 32, 'good_min': 2, 'good_max': 8},
        'factor': {'label': 'Amplify strength', 'min': 0.5, 'max': 10, 'good_min': 1.2, 'good_max': 3.0},
        'blend': {'label': 'Key edge softness', 'min': 0, 'max': 1, 'good_min': 0, 'good_max': 0.2},
        'similarity': {'label': 'Blue tolerance', 'min': 0.01, 'max': 1, 'good_min': 0.1, 'good_max': 0.35},
    },
    'presets': {'Gentle': {'radius': 2, 'factor': 1.2, 'blend': 0.1, 'similarity': 0.12}, 'Medium': {'radius': 4, 'factor': 2.0, 'blend': 0.1, 'similarity': 0.2}, 'Wild': {'radius': 8, 'factor': 3.0, 'blend': 0.2, 'similarity': 0.35}},
}


def register_arguments(parser):
    parser.description = (
        "Apply filter from the perspective of a zombie on TC-1 hallucinogens."
    )

    parser.add_argument(
        "--radius",
        type=int,
        default=4,
        help=(
            "Neighborhood size for amplify. Small = sharp/edgy; large = broad smeary hallucination. Try 2–8."
        )
    )

    parser.add_argument(
        "--factor",
        type=float,
        default=2.0,
        help=(
            "Amplify strength. 1.0 is mild; higher values get more intense/crunchy. Try 1.2–3.0."
        )
    )

    parser.add_argument(
        "--blend",
        type=float,
        default=0.1,
        help=(
            "Chromakey edge softness. 0 = hard edge; higher = feathered edge. Try 0.0–0.20."
        )
    )

    parser.add_argument(
        "--similarity",
        type=float,
        default=0.2,
        help=(
            "Chromakey tolerance for blue. Higher removes more blues (and can eat nearby colors). Try 0.10–0.35."
        )
    )

def run(args):
    args.radius = max(1, min(63, int(args.radius)))
    args.factor = max(0.0, min(100.0, float(args.factor)))
    args.blend = max(0.0, min(1.0, float(args.blend)))
    args.similarity = max(0.00001, min(1.0, float(args.similarity)))

    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", f"[0:v]amplify=radius={args.radius}:factor={args.factor},chromakey=color=blue:similarity={args.similarity}:blend={args.blend}[out_v]",
        "-map", "[out_v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-profile:v", "main",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        args.output
    ]

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)

