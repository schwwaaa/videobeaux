from videobeaux.utils.media import ensure_audio
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

GUI_METADATA = {
    'args': {
        'loops': {'label': 'Back-and-forths', 'min': 1, 'max': 6, 'step': 1,
                  'help': 'How many forward-then-backward cycles to play (1 = a single ping-pong).'},
    },
}

def _graph(loops):
    """The ping-pong graph; `loops` > 1 repeats the forward+back cycle that many times."""
    base = (
        "[0:v]split[va][vb];[vb]reverse[vr];[va][vr]concat=n=2:v=1:a=0[out_v];"
        "[0:a]asplit[aa][ab];[ab]areverse[ar];[aa][ar]concat=n=2:v=0:a=1[out_a]"
    )
    if loops <= 1:
        return base
    v = ("[0:v]split[va][vb];[vb]reverse[vr];[va][vr]concat=n=2:v=1:a=0[cv];"
         f"[cv]split={loops}" + "".join(f"[cv{i}]" for i in range(loops)) + ";"
         + "".join(f"[cv{i}]" for i in range(loops)) + f"concat=n={loops}:v=1:a=0[out_v];")
    a = ("[0:a]asplit[aa][ab];[ab]areverse[ar];[aa][ar]concat=n=2:v=0:a=1[ca];"
         f"[ca]asplit={loops}" + "".join(f"[ca{i}]" for i in range(loops)) + ";"
         + "".join(f"[ca{i}]" for i in range(loops)) + f"concat=n={loops}:v=0:a=1[out_a]")
    return v + a


def register_arguments(parser):
    parser.description = (
        "Forward-then-reverse ping-pong loop — the clip plays normally, then plays "
        "itself backwards, back to the start."
    )
    parser.add_argument("--loops", type=int, default=1,
                        help="Forward-then-backward cycles to play (1-6). Default: 1.")


def run(args):
    # audio filter graphs need an audio track on every input
    if getattr(args, 'input', None):
        args.input = ensure_audio(args.input)
    filter_complex = _graph(max(1, min(6, int(getattr(args, "loops", 1) or 1))))
    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", filter_complex,
        "-map", "[out_v]",
        "-map", "[out_a]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-movflags", "+faststart",
        args.output,
    ]
    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
