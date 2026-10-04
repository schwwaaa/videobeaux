from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

GUI_METADATA = {
    'args': {
        'radius': {'label': 'Glow radius (px)', 'min': 1, 'max': 32, 'good_min': 2, 'good_max': 8},
        'factor': {'label': 'Glow intensity', 'min': 0.5, 'max': 10, 'good_min': 1.2, 'good_max': 3.0},
    },
    'presets': {'Soft glow': {'radius': 3, 'factor': 1.4}, 'Burn': {'radius': 6, 'factor': 2.5}, 'Meltdown': {'radius': 12, 'factor': 5.0}},
}


def register_arguments(parser):
    parser.description = (
        "Causes a dramatic bloom or edge glow. Like overexposure/ video burn."
    )
    print("✅ no additional arguments required")

    parser.add_argument(
        "--radius",
        type=int,
        default=4,
        help=(
            "Glow neighborhood size for amplify. Small = tight edge glow; large = thicker bloom/halo. Try 2–8, push higher for heavy burn."
        )
    )

    parser.add_argument(
        "--factor",
        type=float,
        default=2.0,
        help=(
            "Glow intensity for amplify. Higher values increase bloom/burn and highlight clipping. Try 1.2–3.0; push higher for dramatic damage."
        )
    )

def run(args):
    args.radius = max(1, min(63, int(args.radius)))
    args.factor = max(0.0, min(100.0, float(args.factor)))

    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", f"[0:v]setpts=PTS-STARTPTS,tpad=start=7:start_mode=clone:stop=30:stop_mode=clone,setrange=range=limited,amplify=radius={args.radius}:factor={args.factor}[out_v]",
        "-map", "[out_v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-profile:v", "main",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        args.output
    ]
    print(" ".join(f'"{arg}"' if ' ' in arg or ':' in arg or '=' in arg else arg for arg in command))

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
