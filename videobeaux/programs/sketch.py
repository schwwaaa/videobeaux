"""sketch — pencil, painterly and stylized looks from OpenCV's photo module."""
import numpy as np

from videobeaux.utils.cv import require_cv2
from videobeaux.utils.frame_pipe import process_video

MODES = ["pencil", "color_pencil", "stylize", "smooth_paint", "detail"]

GUI_METADATA = {
    'args': {
        'mode': {'type': 'select', 'label': 'Mode', 'default': 'pencil', 'choices': MODES,
                 'help': 'pencil = grey pencil drawing, color_pencil = tinted pencil, stylize = watercolor-ish, smooth_paint = edge-preserving flatten, detail = crisp detail boost.'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Sketch and painterly looks (OpenCV photo filters): pencil drawing, colored pencil, "
        "stylization, edge-preserving paint smoothing, detail enhancement. Processes at reduced "
        "size for speed."
    )
    parser.add_argument("--mode", choices=MODES, default="pencil", help="Look. Default: pencil.")
    parser.add_argument("--spatial", type=float, default=60.0, help="Smoothing size (sigma_s, 0-200). Default: 60.")
    parser.add_argument("--range", dest="range_", type=float, default=0.3,
                        help="Edge sensitivity (sigma_r, 0-1): low keeps more detail. Default: 0.3.")
    parser.add_argument("--shade", type=float, default=0.05,
                        help="Pencil shading darkness (0-0.1). Default: 0.05.")
    parser.add_argument("--work_scale", type=float, default=0.5,
                        help="Process at this fraction of the frame size, then scale back up (speed). Default: 0.5.")
    parser.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def run(args):
    cv2 = require_cv2()
    s = min(1.0, max(0.1, args.work_scale))
    sig_s = min(200.0, max(0.0, args.spatial))
    sig_r = min(1.0, max(0.0, args.range_))

    def frame_fn(frame, i, t):
        h, w = frame.shape[:2]
        src = frame if s == 1.0 else cv2.resize(frame, (int(w * s) // 2 * 2, int(h * s) // 2 * 2),
                                                 interpolation=cv2.INTER_AREA)
        if args.mode in ("pencil", "color_pencil"):
            gray, color = cv2.pencilSketch(src, sigma_s=sig_s, sigma_r=min(sig_r, 0.2), shade_factor=args.shade)
            out = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB) if args.mode == "pencil" else color
        elif args.mode == "stylize":
            out = cv2.stylization(src, sigma_s=sig_s, sigma_r=sig_r)
        elif args.mode == "smooth_paint":
            out = cv2.edgePreservingFilter(src, flags=1, sigma_s=sig_s, sigma_r=sig_r)
        else:
            out = cv2.detailEnhance(src, sigma_s=sig_s, sigma_r=sig_r)
        if out.shape[:2] != (h, w):
            out = cv2.resize(out, (w, h), interpolation=cv2.INTER_LINEAR)
        return out

    stats = process_video(args.input, args.output, frame_fn, crf=args.crf, force=bool(args.force))
    print(f"✅ {stats['frames']} frames in {stats['seconds']:.1f}s")
