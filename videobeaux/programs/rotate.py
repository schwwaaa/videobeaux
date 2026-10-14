"""
rotate — turn the picture: upside down, on its side, tilted 45°, or slowly spinning. The output is the rotated picture
(its dimensions follow), not just a flag the player may ignore.

Right angles (90 / 180 / 270) use the exact, lossless transpose/flip filters. Any other angle uses ffmpeg's `rotate`
filter and a choice of what happens to the corners:
  · grow the canvas  — the whole picture stays visible, with empty corners in the fill colour
  · zoom to fill     — the picture is enlarged just enough that no empty corner shows
  · keep frame size  — the frame stays the same size and the corners of the picture are cut off
"""
import math

from videobeaux.utils.encode import h264_mp4_args
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

EXPAND = "Grow the canvas (nothing cut off)"
FILL = "Zoom to fill (no empty corners)"
KEEP = "Keep the frame size (corners cut off)"
FITS = [EXPAND, FILL, KEEP]
FLIPS = ["None", "Mirror left–right", "Flip top–bottom"]

GUI_METADATA = {
    'args': {
        'angle': {'label': 'Angle (° clockwise)', 'min': -180, 'max': 180, 'step': 1, 'good_min': -180, 'good_max': 180,
                  'help': '90 lays it on its side, 180 turns it upside down, 45 tilts it. Negative turns the other way.'},
        'flip': {'type': 'select', 'label': 'Flip', 'default': FLIPS[0], 'choices': FLIPS,
                 'help': 'Optionally mirror the picture as well (applied before the rotation).'},
        'fit': {'type': 'select', 'label': 'Corners', 'default': FITS[0], 'choices': FITS,
                'help': 'Only matters for angles that are not 90 / 180 / 270. Grow the canvas keeps everything; Zoom to fill '
                        'enlarges the picture so there are no empty corners; Keep the frame size cuts the corners off.'},
        'fill': {'type': 'color', 'label': 'Empty-corner color', 'default': '#000000'},
        'spin': {'label': 'Spin (° per second)', 'min': -360, 'max': 360, 'step': 5, 'good_min': -90, 'good_max': 90,
                 'help': 'Keeps turning while it plays, starting from the angle above. 0 = a still rotation.'},
        'crf': {'hidden': True},
    },
    'presets': {
        'Upside down': {'angle': 180, 'flip': FLIPS[0], 'spin': 0},
        'On its side (right)': {'angle': 90, 'flip': FLIPS[0], 'spin': 0},
        'On its side (left)': {'angle': -90, 'flip': FLIPS[0], 'spin': 0},
        'Tilt 45°': {'angle': 45, 'fit': EXPAND, 'spin': 0},
        'Slight tilt, filled': {'angle': 8, 'fit': FILL, 'spin': 0},
        'Slow spin': {'angle': 0, 'fit': KEEP, 'spin': 30},
    },
}


def register_arguments(p):
    p.description = (
        "Rotate the video: upside down, on its side, tilted at any angle, or slowly spinning. "
        "The output file really is rotated (its size follows)."
    )
    p.add_argument("--angle", type=float, default=180.0, help="Degrees clockwise (negative = counter-clockwise). Default: 180.")
    p.add_argument("--flip", choices=FLIPS, default=FLIPS[0], help="Also mirror the picture.")
    p.add_argument("--fit", choices=FITS, default=FITS[0], help="What to do with the corners at non-right angles.")
    p.add_argument("--fill", default="#000000", help="Color of empty corners. Default: #000000.")
    p.add_argument("--spin", type=float, default=0.0, help="Degrees per second of continuous rotation. Default: 0.")
    p.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def _even(n: float) -> int:
    n = int(math.ceil(n))
    return max(2, n + (n % 2))


def build_filter(w: int, h: int, angle: float, flip: str = FLIPS[0], fit: str = FITS[0],
                 fill: str = "#000000", spin: float = 0.0):
    """Return (video filter chain, output width, output height) for a w×h picture."""
    a = ((float(angle) + 180.0) % 360.0) - 180.0                      # normalise to [-180, 180)
    parts = []
    if flip == FLIPS[1]:
        parts.append("hflip")
    elif flip == FLIPS[2]:
        parts.append("vflip")
    colour = "0x" + (fill or "#000000").lstrip("#")[:6].upper().ljust(6, "0")

    if not spin and abs(a) % 90 == 0:                                   # exact, lossless turns
        if abs(a) == 180:
            parts += ["hflip", "vflip"]
            ow, oh = w, h
        elif a == 90:
            parts.append("transpose=1")
            ow, oh = h, w
        elif a == -90:
            parts.append("transpose=2")
            ow, oh = h, w
        else:
            ow, oh = w, h
        parts.append("setsar=1")
        return ",".join(parts), ow, oh

    # Arbitrary angle (or spinning)
    expr = f"({a:.4f}+{float(spin):.4f}*t)*PI/180" if spin else f"{a:.4f}*PI/180"
    th = math.radians(a if not spin else 45.0)                          # a spinning picture is sized for its worst case
    c, s = abs(math.cos(th)), abs(math.sin(th))
    if fit == FILL:
        k = max(c + (h / w) * s, (w / h) * s + c)
        parts.append(f"scale={_even(w * k)}:{_even(h * k)}")
        ow, oh = _even(w), _even(h)
    elif fit == KEEP:
        ow, oh = _even(w), _even(h)
    else:                                                               # EXPAND
        if spin:
            ow = oh = _even(math.hypot(w, h))
        else:
            ow, oh = _even(w * c + h * s), _even(w * s + h * c)
    parts.append(f"rotate=a='{expr}':ow={ow}:oh={oh}:c={colour}")
    parts.append("setsar=1")
    return ",".join(parts), ow, oh


def run(args):
    from videobeaux.utils.frame_pipe import probe_video
    info = probe_video(args.input)
    vf, ow, oh = build_filter(info.width, info.height, args.angle, args.flip, args.fit, args.fill, args.spin)
    print(f"Rotate {args.angle:g}°{' + spin ' + format(args.spin, 'g') + '°/s' if args.spin else ''}: "
          f"{info.width}x{info.height} → {ow}x{oh}", flush=True)

    out = str(args.output)
    ext = out.rsplit(".", 1)[-1].lower() if "." in out else "mp4"
    enc = h264_mp4_args(crf=int(getattr(args, "crf", 18))) if ext in ("mp4", "mov", "m4v", "mkv") else []
    command = ["ffmpeg", "-i", args.input, "-vf", vf, "-map", "0:v:0", "-map", "0:a?", *enc, out]
    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if getattr(args, "force", False) else command,
                             args.input, out)
