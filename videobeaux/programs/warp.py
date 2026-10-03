"""warp — swirl, bulge, pinch, ripple, kaleidoscope and mirror distortions (OpenCV remap)."""
import numpy as np

from videobeaux.utils.cv import require_cv2
from videobeaux.utils.frame_pipe import process_video

MODES = ["swirl", "bulge", "pinch", "ripple", "kaleidoscope", "mirror_h", "mirror_v", "mirror_quad"]

GUI_METADATA = {
    'args': {
        'mode': {'type': 'select', 'label': 'Warp', 'default': 'swirl', 'choices': MODES},
    }
}


def register_arguments(parser):
    parser.description = (
        "Geometric warps: swirl, bulge, pinch, ripple, kaleidoscope and mirror modes, optionally "
        "animated. Fast (precomputed remap)."
    )
    parser.add_argument("--mode", choices=MODES, default="swirl", help="Warp type. Default: swirl.")
    parser.add_argument("--amount", type=float, default=1.0, help="Effect strength. Default: 1.")
    parser.add_argument("--radius", type=float, default=0.7,
                        help="Affected radius as a fraction of the frame (swirl/bulge/pinch). Default: 0.7.")
    parser.add_argument("--center_x", type=float, default=0.5, help="Center X, 0-1. Default: 0.5.")
    parser.add_argument("--center_y", type=float, default=0.5, help="Center Y, 0-1. Default: 0.5.")
    parser.add_argument("--segments", type=int, default=6, help="Kaleidoscope segments. Default: 6.")
    parser.add_argument("--speed", type=float, default=0.0,
                        help="Animation speed (0 = static). Swirl oscillates, ripple travels, kaleidoscope rotates.")
    parser.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def build_maps(mode, W, H, t, args):
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = args.center_x * (W - 1), args.center_y * (H - 1)
    dx, dy = xs - cx, ys - cy
    r = np.hypot(dx, dy)
    theta = np.arctan2(dy, dx)
    R = max(1.0, args.radius * 0.5 * float(np.hypot(W, H)))
    rn = np.clip(r / R, 0, 1)

    if mode == "swirl":
        amt = args.amount * (np.sin(t * args.speed) if args.speed else 1.0)
        th = theta + amt * 4.0 * (1.0 - rn) ** 2 * (r < R)
        return cx + r * np.cos(th), cy + r * np.sin(th)
    if mode in ("bulge", "pinch"):
        a = max(0.0, args.amount)
        if args.speed:
            a *= 0.5 * (1 + np.sin(t * args.speed))
        e = (1.0 + a) if mode == "bulge" else 1.0 / (1.0 + a)
        sr = np.where(r < R, R * rn ** e, r)
        scale = np.divide(sr, r, out=np.ones_like(r), where=r > 1e-3)
        return cx + dx * scale, cy + dy * scale
    if mode == "ripple":
        amp = args.amount * 0.012 * H
        wl = 0.18 * H
        ph = t * args.speed * 3.0
        return xs + amp * np.sin(2 * np.pi * ys / wl + ph), ys + amp * np.sin(2 * np.pi * xs / wl + ph)
    if mode == "kaleidoscope":
        seg = max(2, args.segments)
        wedge = 2 * np.pi / seg
        th = np.mod(theta + t * args.speed * 0.5, wedge)
        th = np.where(th > wedge / 2, wedge - th, th)
        return cx + r * np.cos(th), cy + r * np.sin(th)
    if mode == "mirror_h":
        return np.where(xs > cx, 2 * cx - xs, xs), ys
    if mode == "mirror_v":
        return xs, np.where(ys > cy, 2 * cy - ys, ys)
    if mode == "mirror_quad":
        return np.where(xs > cx, 2 * cx - xs, xs), np.where(ys > cy, 2 * cy - ys, ys)
    raise ValueError(mode)


def run(args):
    cv2 = require_cv2()
    cache = {}

    def frame_fn(frame, i, t):
        H, W = frame.shape[:2]
        animated = bool(args.speed) and args.mode in ("swirl", "bulge", "pinch", "ripple", "kaleidoscope")
        key = None if animated else (W, H)
        if key is None or key not in cache:
            mx, my = build_maps(args.mode, W, H, t, args)
            maps = (mx.astype(np.float32), my.astype(np.float32))
            if key is not None:
                cache[key] = maps
        else:
            maps = cache[key]
        return cv2.remap(frame, maps[0], maps[1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

    stats = process_video(args.input, args.output, frame_fn, crf=args.crf, force=bool(args.force))
    print(f"✅ {stats['frames']} frames in {stats['seconds']:.1f}s")
