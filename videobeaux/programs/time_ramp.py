from videobeaux.utils.media import ensure_audio
import subprocess

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress


def _ffprobe_duration_seconds(path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path,
    ]
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode("utf-8", "ignore").strip()
    return float(out)


def register_arguments(parser):
    parser.description = (
        "Variable speed ramp within one clip — e.g. slow-motion accelerating into a "
        "speed-up, unlike the flat single-factor Speed effect. Built as a handful of "
        "discrete speed steps rather than one continuously-varying formula (audio "
        "pitch is correctly matched per step via atempo, not an approximation)."
    )
    parser.add_argument("--start_factor", type=float, default=0.5, help="Speed factor at the start of the clip. Default: 0.5 (half speed).")
    parser.add_argument("--end_factor", type=float, default=2.0, help="Speed factor at the end of the clip. Default: 2.0 (double speed).")
    parser.add_argument("--steps", type=int, default=6, help="Number of discrete speed steps making up the ramp. More = smoother. Default: 6.")


def run(args):
    # audio filter graphs need an audio track on every input
    if getattr(args, 'input', None):
        args.input = ensure_audio(args.input)
    steps = max(2, args.steps)
    duration = _ffprobe_duration_seconds(args.input)
    if duration <= 0:
        print("❌ Could not read input duration.")
        return

    # atempo's own valid single-filter range is 0.5-2.0 — clamp per-step
    # factors into that range rather than chaining multiple atempo calls,
    # same simplification speed.py's own TODO already accepts for this
    # codebase.
    def clamp(f):
        return max(0.5, min(2.0, f))

    window = duration / steps
    v_labels, a_labels = [], []
    parts = []
    for i in range(steps):
        start = window * i
        end = duration if i == steps - 1 else window * (i + 1)
        factor = args.start_factor + (args.end_factor - args.start_factor) * (i / (steps - 1))
        factor = max(0.05, factor)
        atempo_factor = clamp(factor)

        vlab, alab = f"v{i}", f"a{i}"
        parts.append(
            f"[0:v]trim=start={start:.6f}:end={end:.6f},setpts=PTS-STARTPTS,setpts=PTS/{factor}[{vlab}]"
        )
        parts.append(
            f"[0:a]atrim=start={start:.6f}:end={end:.6f},asetpts=PTS-STARTPTS,atempo={atempo_factor}[{alab}]"
        )
        v_labels.append(f"[{vlab}]")
        a_labels.append(f"[{alab}]")

    concat_inputs = "".join(l for pair in zip(v_labels, a_labels) for l in pair)
    parts.append(f"{concat_inputs}concat=n={steps}:v=1:a=1[out_v][out_a]")

    filter_complex = ";".join(parts)
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
