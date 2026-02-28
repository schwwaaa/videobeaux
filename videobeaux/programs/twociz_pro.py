from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

def register_arguments(parser):
    parser.description = (
        "Apply filter from the perspective of a zombie on TC-1 hallucinogens."
    )

    parser.add_argument(
        "--radius",
        required=True,
        type=str,
        help=(
            "Neighborhood size for amplify. Small = sharp/edgy; large = broad smeary hallucination. Try 2–8."
        )
    )

    parser.add_argument(
        "--factor",
        required=True,
        type=str,
        help=(
            "Amplify strength. 1.0 is mild; higher values get more intense/crunchy. Try 1.2–3.0."
        )
    )

    parser.add_argument(
        "--blend",
        required=True,
        type=str,
        help=(
            "Chromakey edge softness. 0 = hard edge; higher = feathered edge. Try 0.0–0.20."
        )
    )

    parser.add_argument(
        "--similarity",
        required=True,
        type=str,
        help=(
            "Chromakey tolerance for blue. Higher removes more blues (and can eat nearby colors). Try 0.10–0.35."
        )
    )

def run(args):

    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", f"[0:v]amplify=radius={args.radius}:factor={args.factor},chromakey=color=blue:similarity={args.similarity}:blend={args.blend}[out_v]",
        "-map", "[out_v]",
        "-map", "0:a",
        "-c:v", "libx264",
        "-profile:v", "main",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        args.output
    ]

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)

