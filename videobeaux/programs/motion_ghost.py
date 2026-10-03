"""motion_ghost — isolate and highlight only what moves (OpenCV background subtraction)."""
import numpy as np

from videobeaux.utils.cv import hex_to_rgb, require_cv2
from videobeaux.utils.frame_pipe import process_video

MODES = ["highlight", "silhouette", "trails"]

GUI_METADATA = {
    'args': {
        'mode': {'type': 'select', 'label': 'Mode', 'default': 'highlight', 'choices': MODES,
                 'help': 'highlight = tint movers over a dimmed scene, silhouette = only the moving areas, trails = glowing ghost trails of motion.'},
        'color': {'type': 'color', 'label': 'Tint color', 'default': '#FF2D95'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Motion isolation with background subtraction (MOG2): tint what moves, show only the "
        "moving parts, or leave glowing ghost trails behind them. Works best with a still camera."
    )
    parser.add_argument("--mode", choices=MODES, default="highlight", help="Mode. Default: highlight.")
    parser.add_argument("--color", type=str, default="#FF2D95", help="Tint/trail color. Default: #FF2D95.")
    parser.add_argument("--sensitivity", type=float, default=0.5,
                        help="0 = only big movement, 1 = pick up subtle movement. Default: 0.5.")
    parser.add_argument("--decay", type=float, default=0.92,
                        help="Trails: how slowly trails fade, 0-0.99. Default: 0.92.")
    parser.add_argument("--dim", type=float, default=0.35, help="Brightness of the non-moving scene, 0-1. Default: 0.35.")
    parser.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def run(args):
    cv2 = require_cv2()
    sens = min(1.0, max(0.0, args.sensitivity))
    sub = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=int(60 - 45 * sens), detectShadows=False)
    color = np.array(hex_to_rgb(args.color, (255, 45, 149)), dtype=np.float32)
    k_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    k_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    dim = min(1.0, max(0.0, args.dim))
    decay = min(0.99, max(0.0, args.decay))
    state = {"trail": None}

    def frame_fn(frame, i, t):
        h, w = frame.shape[:2]
        sw = 480 if w > 480 else w
        small = cv2.resize(frame, (sw, max(2, int(h * sw / w))), interpolation=cv2.INTER_AREA)
        mask = sub.apply(cv2.GaussianBlur(small, (5, 5), 0))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k_open)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k_close)
        mask = cv2.GaussianBlur(cv2.resize(mask, (w, h), interpolation=cv2.INTER_LINEAR), (9, 9), 0)
        m = (mask.astype(np.float32) / 255.0)[..., None]
        f = frame.astype(np.float32)
        if args.mode == "silhouette":
            return np.clip(f * m, 0, 255).astype(np.uint8)
        if args.mode == "highlight":
            tint = f * 0.45 + color * 0.55
            return np.clip(f * dim * (1 - m) + tint * m, 0, 255).astype(np.uint8)
        trail = state["trail"] if state["trail"] is not None else np.zeros_like(m)
        trail = np.maximum(trail * decay, m)
        state["trail"] = trail
        glow = cv2.GaussianBlur(trail, (0, 0), max(2.0, w / 160.0))
        glow = glow[..., None] if glow.ndim == 2 else glow
        return np.clip(f * dim + color * trail * 0.9 + color * glow * 0.6, 0, 255).astype(np.uint8)

    stats = process_video(args.input, args.output, frame_fn, crf=args.crf, force=bool(args.force))
    print(f"✅ {stats['frames']} frames in {stats['seconds']:.1f}s")
