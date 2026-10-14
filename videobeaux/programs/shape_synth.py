"""
shape_synth — a pair of animated shape generators combined into one matte (an homage to the LZX DSG3 Dual
Shape Generator, which makes two shapes from ramps with inverters, frequency doublers, exp/log shapers and
min/max).

Each channel (A and B) draws a shape — circle, ring, diamond, square, cross, stripes, checker or vortex — that you
can size, fold into repeated bands (frequency doubling), bend with an exp/log curve, stretch, rotate, offset and
animate (drift and spin per second). A and B are combined (min, max, sum, difference, xor…) and the result is
painted over the video, used to keep or remove parts of it, to warp it, or exported as a matte / transparent cutout.
"""
import numpy as np

from videobeaux.utils import fields, keying
from videobeaux.utils.cv import hex_to_rgb, require_cv2
from videobeaux.utils.frame_pipe import process_video
from videobeaux.utils.matte_pipeline import run_matte_program

STYLES = ["color shapes over video", "video inside shapes", "video outside shapes", "warp video by shapes",
          "matte (white shapes)", "cutout (inside shapes)"]
CH = ("a", "b")

_args = {
    'combine': {'type': 'select', 'label': 'Combine A + B', 'default': 'max', 'choices': fields.COMBINE,
                'help': 'How the two shapes join: max = union, min = overlap, difference / xor = where they differ.'},
    'style': {'type': 'select', 'label': 'Output style', 'default': STYLES[0], 'choices': STYLES,
              'help': "The Background / View / Edge options at the bottom only apply to 'cutout'."},
    'opacity': {'label': 'Opacity', 'min': 0, 'max': 1, 'step': 0.05, 'good_min': 0.5, 'good_max': 1},
    'warp': {'label': 'Warp amount', 'min': 0, 'max': 1, 'step': 0.05, 'good_min': 0.1, 'good_max': 0.6,
             'help': "For 'warp video by shapes': how strongly the edges of the shapes bend the picture."},
    'invert': {'label': 'Invert result'},
    'a_color': {'type': 'color', 'label': 'A color', 'default': '#FF3D7F'},
    'b_color': {'type': 'color', 'label': 'B color', 'default': '#2EC4B6'},
}
for _c in CH:
    U = _c.upper()
    _args.update({
        f'{_c}_shape': {'type': 'select', 'label': f'{U} shape', 'default': 'circle' if _c == 'a' else 'diamond', 'choices': fields.SHAPES},
        f'{_c}_size': {'label': f'{U} size', 'min': 0.05, 'max': 2.0, 'step': 0.01, 'good_min': 0.2, 'good_max': 0.9,
                       'help': 'Half-size in frame-height units (1 = reaches the top and bottom edge).'},
        f'{_c}_fold': {'label': f'{U} fold', 'min': 1, 'max': 12, 'good_min': 1, 'good_max': 6,
                       'help': 'Frequency doubling: repeats the shape outward as bands. For vortex = number of arms.'},
        f'{_c}_curve': {'label': f'{U} curve', 'min': -4, 'max': 4, 'step': 0.1, 'good_min': -2, 'good_max': 2,
                        'help': 'Exp (positive) / log (negative) shaping of the shape profile.'},
        f'{_c}_softness': {'label': f'{U} edge softness', 'min': 0, 'max': 1, 'step': 0.01, 'good_min': 0.02, 'good_max': 0.3},
        f'{_c}_stretch_x': {'label': f'{U} stretch X', 'min': 0.2, 'max': 5, 'step': 0.05, 'good_min': 0.5, 'good_max': 2},
        f'{_c}_stretch_y': {'label': f'{U} stretch Y', 'min': 0.2, 'max': 5, 'step': 0.05, 'good_min': 0.5, 'good_max': 2},
        f'{_c}_rotate': {'label': f'{U} rotate (°)', 'min': -180, 'max': 180},
        f'{_c}_spin': {'label': f'{U} spin (°/sec)', 'min': -360, 'max': 360, 'good_min': -45, 'good_max': 45},
        f'{_c}_x': {'label': f'{U} offset X', 'min': -2, 'max': 2, 'step': 0.01},
        f'{_c}_y': {'label': f'{U} offset Y', 'min': -1.5, 'max': 1.5, 'step': 0.01},
        f'{_c}_drift_x': {'label': f'{U} drift X (/sec)', 'min': -2, 'max': 2, 'step': 0.05},
        f'{_c}_drift_y': {'label': f'{U} drift Y (/sec)', 'min': -2, 'max': 2, 'step': 0.05},
        f'{_c}_invert': {'label': f'{U} invert'},
    })

GUI_METADATA = {
    'args': {**_args, **keying.GUI_COMMON, 'crf': {'hidden': True}},
    'presets': {
        'Target': {'a_shape': 'circle', 'a_size': 0.8, 'a_fold': 4, 'a_softness': 0.05, 'b_size': 0.3, 'b_shape': 'ring',
                   'combine': 'xor', 'style': STYLES[0], 'opacity': 0.9},
        'Diamond tunnel': {'a_shape': 'diamond', 'a_size': 0.9, 'a_fold': 6, 'a_curve': 1.5, 'a_spin': 20,
                           'b_shape': 'diamond', 'b_size': 0.45, 'b_fold': 3, 'b_spin': -35, 'combine': 'difference',
                           'style': STYLES[0], 'a_color': '#FFB000', 'b_color': '#6B0F7A', 'opacity': 1},
        'Vortex': {'a_shape': 'vortex', 'a_size': 0.5, 'a_fold': 3, 'a_spin': 40, 'a_softness': 0.1, 'b_shape': 'circle',
                   'b_size': 1.4, 'combine': 'min', 'style': STYLES[0], 'opacity': 0.85},
        'Checker warp': {'a_shape': 'checker', 'a_size': 0.3, 'a_spin': 12, 'a_softness': 0.2, 'b_size': 0.5, 'combine': 'A',
                         'style': STYLES[3], 'warp': 0.5},
        'Window cross': {'a_shape': 'cross', 'a_size': 0.5, 'b_shape': 'square', 'b_size': 0.35, 'combine': 'max',
                         'style': STYLES[1], 'opacity': 1, 'a_softness': 0.05, 'b_softness': 0.05},
    },
}


def register_arguments(p):
    p.description = (
        "Shape Synth — two animated shape generators (circle, ring, diamond, square, cross, stripes, checker, "
        "vortex), combined and painted over the video, used to keep/remove parts of it, to warp it, or exported "
        "as a matte / cutout. Homage to the LZX DSG3 Dual Shape Generator."
    )
    p.add_argument("--combine", choices=fields.COMBINE, default="max", help="How A and B combine. Default: max.")
    p.add_argument("--style", choices=STYLES, default=STYLES[0], help="What to render.")
    p.add_argument("--opacity", type=float, default=0.9, help="Shape opacity, 0 to 1. Default: 0.9.")
    p.add_argument("--warp", type=float, default=0.3, help="Warp amount for 'warp video by shapes'. Default: 0.3.")
    p.add_argument("--invert", action="store_true", help="Invert the combined shape.")
    p.add_argument("--a_color", type=str, default="#FF3D7F", help="Color of shape A.")
    p.add_argument("--b_color", type=str, default="#2EC4B6", help="Color of shape B.")
    for c in CH:
        d = {"a": dict(shape="circle", size=0.6), "b": dict(shape="diamond", size=0.4)}[c]
        p.add_argument(f"--{c}_shape", choices=fields.SHAPES, default=d["shape"], help=f"Shape {c.upper()}.")
        p.add_argument(f"--{c}_size", type=float, default=d["size"], help="Half-size, in frame-height units.")
        p.add_argument(f"--{c}_fold", type=int, default=1, help="Frequency doubling (bands / vortex arms).")
        p.add_argument(f"--{c}_curve", type=float, default=0.0, help="Exp (+) / log (-) shaping.")
        p.add_argument(f"--{c}_softness", type=float, default=0.08, help="Edge softness.")
        p.add_argument(f"--{c}_stretch_x", type=float, default=1.0, help="Horizontal stretch.")
        p.add_argument(f"--{c}_stretch_y", type=float, default=1.0, help="Vertical stretch.")
        p.add_argument(f"--{c}_rotate", type=float, default=0.0, help="Rotation in degrees.")
        p.add_argument(f"--{c}_spin", type=float, default=0.0, help="Spin in degrees per second.")
        p.add_argument(f"--{c}_x", type=float, default=0.0, help="Horizontal offset.")
        p.add_argument(f"--{c}_y", type=float, default=0.0, help="Vertical offset.")
        p.add_argument(f"--{c}_drift_x", type=float, default=0.0, help="Horizontal drift per second.")
        p.add_argument(f"--{c}_drift_y", type=float, default=0.0, help="Vertical drift per second.")
        p.add_argument(f"--{c}_invert", action="store_true", help=f"Invert shape {c.upper()}.")
    keying.add_common_arguments(p)


def channel_matte(args, c: str, h: int, w: int, t: float) -> np.ndarray:
    g = lambda name: getattr(args, f"{c}_{name}")
    x, y = fields.ramps(h, w, rotate_deg=g("rotate") + g("spin") * t,
                        cx=g("x") + g("drift_x") * t, cy=g("y") + g("drift_y") * t)
    x = x / max(g("stretch_x"), 1e-3)
    y = y / max(g("stretch_y"), 1e-3)
    f = fields.shape_field(g("shape"), x, y, size=g("size"), fold_n=g("fold"), curve_k=g("curve"))
    m = fields.inside(f, max(g("softness"), 0.005))
    return 1.0 - m if g("invert") else m


def combined_matte(args, h: int, w: int, t: float):
    a = channel_matte(args, "a", h, w, t)
    b = channel_matte(args, "b", h, w, t)
    m = fields.combine(a, b, args.combine)
    return (1.0 - m if args.invert else m), a, b


def run(args):
    cv2 = require_cv2()
    ca = np.array(hex_to_rgb(args.a_color, (255, 61, 127)), np.float32)
    cb = np.array(hex_to_rgb(args.b_color, (46, 196, 182)), np.float32)

    def matte_fn(frame, i, t):
        return combined_matte(args, frame.shape[0], frame.shape[1], t)[0]

    if args.style == STYLES[5]:
        run_matte_program(args, matte_fn)
        return

    def render(frame, i, t):
        h, w = frame.shape[:2]
        m, a, b = combined_matte(args, h, w, t)
        f = frame.astype(np.float32)
        op = float(np.clip(args.opacity, 0.0, 1.0))
        if args.style == STYLES[0]:
            wsum = np.maximum(a + b, 1e-4)[..., None]
            col = (a[..., None] * ca + b[..., None] * cb) / wsum
            if args.combine == "A":
                col = np.broadcast_to(ca, f.shape)
            elif args.combine == "B":
                col = np.broadcast_to(cb, f.shape)
            k = (m * op)[..., None]
            return np.clip(f * (1.0 - k) + col * k, 0, 255).astype(np.uint8)
        if args.style == STYLES[1]:
            return np.clip(f * (1.0 - op * (1.0 - m)[..., None]), 0, 255).astype(np.uint8)
        if args.style == STYLES[2]:
            return np.clip(f * (1.0 - op * m[..., None]), 0, 255).astype(np.uint8)
        if args.style == STYLES[3]:
            ms = cv2.GaussianBlur(m, (0, 0), max(2.0, min(h, w) * 0.01))
            gx = cv2.Sobel(ms, cv2.CV_32F, 1, 0, ksize=3)
            gy = cv2.Sobel(ms, cv2.CV_32F, 0, 1, ksize=3)
            k = float(args.warp) * min(h, w) * 0.5
            yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
            return cv2.remap(frame, xx + gx * k, yy + gy * k, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        g = (np.clip(m, 0, 1) * 255).astype(np.uint8)                      # matte
        return np.dstack([g, g, g])

    stats = process_video(args.input, args.output, render, crf=args.crf, force=bool(getattr(args, "force", False)))
    print(f"✅ {stats['frames']} frames in {stats['seconds']:.1f}s")
