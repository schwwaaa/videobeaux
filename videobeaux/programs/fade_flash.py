"""
fade_flash — fade in / out from a color (black, white, any color) and add timed flashes, like a mixer's
auto-transition and flash button. Pure ffmpeg.
"""
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.frame_pipe import probe_video
from videobeaux.utils.media import ensure_audio, has_audio
from videobeaux.utils.mixer import ff_color

STYLES = ["decay (fades away)", "hard (on/off)"]

GUI_METADATA = {
    'args': {
        'fade_in': {'label': 'Fade in (s)', 'min': 0, 'max': 60},
        'fade_out': {'label': 'Fade out (s)', 'min': 0, 'max': 60},
        'fade_color': {'type': 'color', 'label': 'Fade color', 'default': '#000000'},
        'fade_audio': {'label': 'Fade audio too', 'help': 'Fade the sound in and out along with the picture.'},
        'flash_times': {'type': 'text', 'label': 'Flash at (seconds)',
                        'help': 'Comma-separated times for flashes, e.g. 1.5, 4, 6.25. Leave empty for none.'},
        'flash_length': {'label': 'Flash length (s)', 'min': 0.04, 'max': 5},
        'flash_color': {'type': 'color', 'label': 'Flash color', 'default': '#FFFFFF'},
        'flash_style': {'type': 'select', 'label': 'Flash style', 'default': STYLES[0], 'choices': STYLES},
        'crf': {'hidden': True},
    }
}


def register_arguments(p):
    p.description = (
        "Fade in and out from a color (black, white or any color) and add timed flashes. Flashes either decay "
        "smoothly or snap on and off. Optionally fades the audio with the picture."
    )
    p.add_argument("--fade_in", type=float, default=1.0, help="Seconds to fade in from the color. Default: 1.")
    p.add_argument("--fade_out", type=float, default=1.0, help="Seconds to fade out to the color. Default: 1.")
    p.add_argument("--fade_color", type=str, default="#000000", help="Fade color. Default: #000000.")
    p.add_argument("--fade_audio", action="store_true", help="Fade the audio along with the picture.")
    p.add_argument("--flash_times", type=str, default="", help="Comma-separated flash times in seconds.")
    p.add_argument("--flash_length", type=float, default=0.25, help="Flash length in seconds. Default: 0.25.")
    p.add_argument("--flash_color", type=str, default="#FFFFFF", help="Flash color. Default: #FFFFFF.")
    p.add_argument("--flash_style", choices=STYLES, default=STYLES[0], help="Flash style. Default: decay.")
    p.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def parse_times(text: str):
    out = []
    for part in (text or "").replace(";", ",").split(","):
        part = part.strip()
        if part:
            try:
                out.append(max(0.0, float(part)))
            except ValueError:
                raise SystemExit(f"❌ Couldn't read the flash time {part!r} — use numbers like 1.5, 4, 6.25.")
    return out


def build_graph(a, W: int, H: int, fps: float, dur: float):
    chain = ["[0:v]format=yuv420p"]
    fi, fo = max(0.0, a.fade_in), max(0.0, a.fade_out)
    col = ff_color(a.fade_color)
    if fi > 0:
        chain.append(f"fade=t=in:st=0:d={fi:.3f}:color={col}")
    if fo > 0:
        chain.append(f"fade=t=out:st={max(0.0, dur - fo):.3f}:d={fo:.3f}:color={col}")
    parts = [",".join(chain) + "[v0]"]
    prev = "v0"
    ln = max(0.04, a.flash_length)
    for i, t in enumerate(parse_times(a.flash_times)):
        fade = "" if a.flash_style == STYLES[1] else f",fade=t=out:st=0:d={ln:.3f}:alpha=1"
        parts.append(f"color=c={ff_color(a.flash_color, (255, 255, 255))}:s={W}x{H}:r={fps:.6f}:d={ln + 0.05:.3f},"
                     f"format=rgba{fade},setpts=PTS+{t:.3f}/TB[fl{i}]")
        parts.append(f"[{prev}][fl{i}]overlay=eof_action=pass:format=auto,format=yuv420p[v{i + 1}]")
        prev = f"v{i + 1}"
    parts.append(f"[{prev}]null[out]")
    if a.fade_audio:
        af = []
        if fi > 0:
            af.append(f"afade=t=in:st=0:d={fi:.3f}")
        if fo > 0:
            af.append(f"afade=t=out:st={max(0.0, dur - fo):.3f}:d={fo:.3f}")
        if af:
            parts.append(f"[0:a]{','.join(af)}[aout]")
    return ";".join(parts)


def run(args):
    args.input = ensure_audio(args.input)   # audio filters need a track on every input
    info = probe_video(args.input)
    W, H = info.width - info.width % 2, info.height - info.height % 2
    graph = build_graph(args, W, H, info.fps, info.duration)
    aud = has_audio(args.input)
    fade_audio = aud and args.fade_audio and "[aout]" in graph
    cmd = ["ffmpeg", *(["-y"] if getattr(args, "force", False) else []), "-i", args.input, "-filter_complex", graph, "-map", "[out]"]
    cmd += ["-map", "[aout]", "-c:a", "aac"] if fade_audio else (["-map", "0:a?", "-c:a", "copy"] if aud else ["-an"])
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", str(args.crf), "-pix_fmt", "yuv420p",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-movflags", "+faststart", args.output]
    run_ffmpeg_with_progress(cmd, args.input, args.output)
