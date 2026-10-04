"""
proc_amp — a video processing amplifier: brightness, contrast, saturation, hue rotation, gamma, black and white
levels, color temperature, and an optional broadcast-safe clamp. Pure ffmpeg (audio is copied untouched).
"""
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.media import has_audio

GUI_METADATA = {
    'args': {
        'brightness': {'label': 'Brightness', 'min': -1, 'max': 1, 'help': '0 = unchanged.'},
        'contrast': {'label': 'Contrast', 'min': 0, 'max': 3, 'help': '1 = unchanged.'},
        'saturation': {'label': 'Saturation', 'min': 0, 'max': 3, 'help': '1 = unchanged, 0 = black and white.'},
        'hue': {'label': 'Hue rotate (°)', 'min': -180, 'max': 180},
        'gamma': {'label': 'Gamma', 'min': 0.1, 'max': 3, 'help': '1 = unchanged; above 1 lifts the mid-tones.'},
        'black_level': {'label': 'Black level', 'min': 0, 'max': 0.5, 'help': 'Everything at or below this becomes black.'},
        'white_level': {'label': 'White level', 'min': 0.5, 'max': 1, 'help': 'Everything at or above this becomes white.'},
        'temperature': {'label': 'Color temperature (K)', 'min': 2000, 'max': 12000,
                        'help': '6500 = unchanged. Lower is warmer (orange), higher is cooler (blue).'},
        'broadcast_safe': {'label': 'Broadcast-safe', 'help': 'Clamp to legal video levels (16-235 luma).'},
        'crf': {'hidden': True},
    }
}


def register_arguments(p):
    p.description = (
        "Proc amp: brightness, contrast, saturation, hue rotation, gamma, black/white levels and color "
        "temperature, with an optional broadcast-safe clamp. Audio is copied untouched."
    )
    p.add_argument("--brightness", type=float, default=0.0, help="Brightness, -1 to 1. Default: 0.")
    p.add_argument("--contrast", type=float, default=1.0, help="Contrast multiplier. Default: 1.")
    p.add_argument("--saturation", type=float, default=1.0, help="Saturation multiplier. Default: 1.")
    p.add_argument("--hue", type=float, default=0.0, help="Hue rotation in degrees. Default: 0.")
    p.add_argument("--gamma", type=float, default=1.0, help="Gamma. Default: 1.")
    p.add_argument("--black_level", type=float, default=0.0, help="Input black point, 0 to 0.5. Default: 0.")
    p.add_argument("--white_level", type=float, default=1.0, help="Input white point, 0.5 to 1. Default: 1.")
    p.add_argument("--temperature", type=float, default=6500.0, help="Color temperature in Kelvin. Default: 6500.")
    p.add_argument("--broadcast_safe", action="store_true", help="Clamp to legal broadcast levels.")
    p.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def build_filter(a) -> str:
    f = []
    if a.black_level > 0 or a.white_level < 1:
        bl = max(0.0, min(0.9, a.black_level))
        wl = max(bl + 0.05, min(1.0, a.white_level))
        f.append(f"colorlevels=rimin={bl}:gimin={bl}:bimin={bl}:rimax={wl}:gimax={wl}:bimax={wl}")
    if abs(a.temperature - 6500) > 1:
        f.append(f"colortemperature=temperature={max(1000.0, min(40000.0, a.temperature)):.0f}")
    f.append(f"eq=brightness={a.brightness}:contrast={a.contrast}:saturation={a.saturation}:gamma={a.gamma}")
    if abs(a.hue) > 0.01:
        f.append(f"hue=h={a.hue}")
    f.append("format=yuv420p")
    if a.broadcast_safe:
        f.append("limiter=min=16:max=235:planes=1,limiter=min=16:max=240:planes=6")
    return ",".join(f)


def run(args):
    cmd = ["ffmpeg", *(["-y"] if getattr(args, "force", False) else []), "-i", args.input, "-vf", build_filter(args),
           "-c:v", "libx264", "-preset", "medium", "-crf", str(args.crf), "-pix_fmt", "yuv420p",
           "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-movflags", "+faststart",
           *(["-c:a", "copy"] if has_audio(args.input) else ["-an"]), args.output]
    run_ffmpeg_with_progress(cmd, args.input, args.output)
