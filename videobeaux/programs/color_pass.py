"""
color_pass — keep one color range and drain the rest to gray ("color pass" on hardware mixers): a red
dress in a gray world. Or flip it to remove just that color. OpenCV, fully offline.
"""
import numpy as np

from videobeaux.utils.cv import hex_to_rgb, require_cv2
from videobeaux.utils.frame_pipe import process_video

MODES = ["keep this color", "remove this color"]

GUI_METADATA = {
    'args': {
        'color': {'type': 'color', 'label': 'Color', 'default': '#FF0000',
                  'help': 'Pick the color to keep (or remove); only its hue matters.'},
        'mode': {'type': 'select', 'label': 'Mode', 'default': MODES[0], 'choices': MODES},
        'range': {'label': 'Range (°)', 'min': 1, 'max': 180, 'help': 'How far around the color wheel still counts as the color.'},
        'softness': {'label': 'Softness (°)', 'min': 0, 'max': 90, 'help': 'Fade at the edge of the range.'},
        'min_saturation': {'label': 'Ignore grays below', 'min': 0, 'max': 1,
                           'help': 'Pixels less colorful than this are treated as gray, never as the picked color.'},
        'desaturate': {'label': 'Drain the rest', 'min': 0, 'max': 1, 'help': '1 = fully gray, lower keeps some color.'},
        'boost': {'label': 'Boost the color', 'min': 0, 'max': 3, 'help': 'Extra saturation on the kept color.'},
        'crf': {'hidden': True},
    }
}


def register_arguments(p):
    p.description = (
        "Color pass: keep one color range and turn everything else gray (or remove just that color). "
        "Pick the color, then widen or narrow the range and softness."
    )
    p.add_argument("--color", type=str, default="#FF0000", help="Color to keep. Default: #FF0000.")
    p.add_argument("--mode", choices=MODES, default=MODES[0], help="Keep or remove the color.")
    p.add_argument("--range", type=float, default=30.0, help="Hue range around the color, degrees. Default: 30.")
    p.add_argument("--softness", type=float, default=20.0, help="Soft edge, degrees. Default: 20.")
    p.add_argument("--min_saturation", type=float, default=0.15, help="Treat less-colorful pixels as gray. Default: 0.15.")
    p.add_argument("--desaturate", type=float, default=1.0, help="How much to drain the rest, 0 to 1. Default: 1.")
    p.add_argument("--boost", type=float, default=1.0, help="Saturation multiplier on the kept color. Default: 1.")
    p.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def color_pass_frame(cv2, frame, hue_deg, rng, soft, min_sat, drain, boost, keep=True):
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV).astype(np.float32)
    hue = hsv[..., 0] * 2.0                                   # OpenCV hue is 0-179 → degrees
    d = np.abs(hue - hue_deg)
    d = np.minimum(d, 360.0 - d)
    inside = np.clip(1.0 - (d - rng) / max(soft, 1e-3), 0.0, 1.0)
    inside = np.where(hsv[..., 1] / 255.0 >= min_sat, inside, 0.0)
    weight = inside if keep else 1.0 - inside                 # 1 = stays colorful
    scale = 1.0 - drain * (1.0 - weight)                      # 0 = fully gray
    if boost != 1.0:
        scale = scale * (1.0 + (boost - 1.0) * inside)
    f = frame.astype(np.float32)
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY).astype(np.float32)[..., None]   # luma, so grays keep their brightness
    out = gray + (f - gray) * scale[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


def run(args):
    cv2 = require_cv2()
    r, g, b = hex_to_rgb(args.color, (255, 0, 0))
    hue_deg = float(cv2.cvtColor(np.uint8([[[r, g, b]]]), cv2.COLOR_RGB2HSV)[0, 0, 0]) * 2.0
    keep = args.mode == MODES[0]

    def frame_fn(frame, i, t):
        return color_pass_frame(cv2, frame, hue_deg, args.range, args.softness, args.min_saturation,
                                max(0.0, min(1.0, args.desaturate)), args.boost, keep)

    stats = process_video(args.input, args.output, frame_fn, crf=args.crf, force=bool(getattr(args, "force", False)))
    print(f"✅ {stats['frames']} frames in {stats['seconds']:.1f}s")
