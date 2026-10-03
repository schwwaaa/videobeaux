"""cartoon — flat colors with inked outlines (OpenCV)."""
import numpy as np

from videobeaux.utils.cv import require_cv2
from videobeaux.utils.frame_pipe import process_video

GUI_METADATA = {'args': {}}


def register_arguments(parser):
    parser.description = (
        "Cartoon look: edge-preserving smoothing, posterized flat colors and black ink outlines "
        "from adaptive thresholding."
    )
    parser.add_argument("--levels", type=int, default=6, help="Color steps per channel (2-16). Default: 6.")
    parser.add_argument("--smooth", type=int, default=3,
                        help="Smoothing passes — more = flatter, more painted. Default: 3.")
    parser.add_argument("--edge_size", type=int, default=9,
                        help="Outline detail window, odd number: small = fine lines, large = bold. Default: 9.")
    parser.add_argument("--edge_strength", type=int, default=4,
                        help="Outline threshold offset — higher = fewer lines. Default: 4.")
    parser.add_argument("--saturation", type=float, default=1.25, help="Color boost. Default: 1.25.")
    parser.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def run(args):
    cv2 = require_cv2()
    levels = min(16, max(2, args.levels))
    step = 256.0 / levels
    block = max(3, args.edge_size | 1)

    def frame_fn(frame, i, t):
        h, w = frame.shape[:2]
        # smooth at half resolution — bilateral filtering is the slow part
        small = cv2.resize(frame, (max(2, w // 2), max(2, h // 2)), interpolation=cv2.INTER_AREA)
        for _ in range(max(1, args.smooth)):
            small = cv2.bilateralFilter(small, 7, 40, 7)
        color = cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)
        gray = cv2.medianBlur(cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY), 5)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY,
                                      block, args.edge_strength)
        q = (np.floor(color.astype(np.float32) / step) * step + step / 2.0)
        if args.saturation != 1.0:
            hsv = cv2.cvtColor(np.clip(q, 0, 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
            hsv[..., 1] = np.clip(hsv[..., 1] * args.saturation, 0, 255)
            q = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
        out = np.clip(q, 0, 255).astype(np.uint8)
        return cv2.bitwise_and(out, out, mask=edges)

    stats = process_video(args.input, args.output, frame_fn, crf=args.crf, force=bool(args.force))
    print(f"✅ {stats['frames']} frames in {stats['seconds']:.1f}s")
