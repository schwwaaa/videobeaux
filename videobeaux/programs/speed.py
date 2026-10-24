"""
speed — change how fast the clip plays, from ultra slow-motion (0.05×) to time-lapse (100×).

The video is retimed with setpts; the audio is retimed with a chain of `atempo` filters (each one only accepts 0.5–100,
so 0.1× is 0.5 · 0.5 · 0.5 · 0.8) and keeps its pitch. At very slow speeds you can mute the audio, and turn on
"Smooth slow-motion" to invent the in-between frames instead of repeating frames (slow to render).
"""
import sys

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.media import ensure_audio

MIN_SPEED = 0.05
MAX_SPEED = 100.0
AUDIO_CHOICES = ["Stretch (keep pitch)", "Mute"]

GUI_METADATA = {
    'args': {
        'speed_factor': {
            'label': 'Speed (×)', 'default': 1.0, 'min': MIN_SPEED, 'max': MAX_SPEED,
            'slider_min': 0.1, 'slider_max': 8, 'scale': 'log', 'good_min': 0.25, 'good_max': 4,
            'help': '1 = normal · below 1 slows down (0.1 = ten times slower) · above 1 speeds up. The slider is logarithmic so slow '
                    'and fast get equal room; type any value from 0.05 to 100.',
        },
        'audio': {'type': 'select', 'label': 'Audio', 'default': AUDIO_CHOICES[0], 'choices': AUDIO_CHOICES,
                  'help': 'Stretch keeps the pitch and follows the new speed (a drone at 0.1×) · Mute drops the sound.'},
        'smooth': {'label': 'Smooth slow-motion',
                   'help': 'Invents in-between frames instead of repeating frames when slowing down. Much nicer at 0.1–0.5×, much slower to render.'},
    },
    'presets': {
        'Ultra slow (0.1×)': {'speed_factor': 0.1},
        'Slow-mo (0.25×)': {'speed_factor': 0.25},
        'Half speed': {'speed_factor': 0.5},
        'Double': {'speed_factor': 2},
        'Time-lapse (8×)': {'speed_factor': 8},
    },
}


def atempo_chain(factor: float):
    """The atempo values whose product is `factor` (each stage within ffmpeg's 0.5–100 limit)."""
    stages = []
    remaining = float(factor)
    while remaining < 0.5:
        stages.append(0.5)
        remaining /= 0.5
    while remaining > 100.0:
        stages.append(100.0)
        remaining /= 100.0
    if abs(remaining - 1.0) > 1e-9 or not stages:
        stages.append(remaining)
    return stages


def build_filtergraph(factor: float, fps: float = 0.0, smooth: bool = False, audio: bool = True) -> str:
    v = f"[0:v]setpts=PTS/{factor:.6f}"
    if smooth and factor < 1.0 and fps > 0:
        v += f",minterpolate=fps={fps:.3f}:mi_mode=mci:mc_mode=aobmc:vsbmc=1"
    graph = v + "[v]"
    if audio:
        graph += ";[0:a]" + ",".join(f"atempo={s:.6f}" for s in atempo_chain(factor)) + "[a]"
    return graph


def register_arguments(parser):
    parser.description = (
        "Changes the speed of the video file, from 0.05× (ultra slow-motion) to 100×. "
        "The audio follows the same speed without changing its pitch (or can be muted)."
    )
    parser.add_argument(
        "--speed_factor", type=float, default=1.0,
        help=(f"{MIN_SPEED} to {MAX_SPEED:g}. Above 1 the video plays faster, below 1 slower (0.1 = ten times slower). Default: 1."))
    parser.add_argument("--audio", choices=AUDIO_CHOICES, default=AUDIO_CHOICES[0],
                        help="Stretch (keep pitch, default) or Mute.")
    parser.add_argument("--smooth", action="store_true",
                        help="Smooth slow-motion: interpolate in-between frames when slowing down (slow).")


def run(args):
    if not (MIN_SPEED <= args.speed_factor <= MAX_SPEED):
        print(f"❌ --speed_factor must be between {MIN_SPEED} and {MAX_SPEED:g} (got {args.speed_factor:g}).")
        sys.exit(1)

    keep_audio = getattr(args, "audio", AUDIO_CHOICES[0]) != "Mute"
    if keep_audio and getattr(args, 'input', None):
        args.input = ensure_audio(args.input)          # audio filter graphs need an audio track

    fps = 0.0
    if getattr(args, "smooth", False) and args.speed_factor < 1.0:
        from videobeaux.utils.frame_pipe import probe_video
        fps = probe_video(args.input).fps
        print(f"Smooth slow-motion: interpolating to {fps:g} fps (this takes a while).", flush=True)

    command = ["ffmpeg", "-i", args.input,
               "-filter_complex", build_filtergraph(args.speed_factor, fps, getattr(args, "smooth", False), keep_audio),
               "-map", "[v]"]
    command += ["-map", "[a]"] if keep_audio else ["-an"]
    command += [args.output]

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
