"""neon_edges — glowing colored edge outlines (OpenCV)."""
import colorsys

import numpy as np

from videobeaux.utils.cv import hex_to_rgb, require_cv2
from videobeaux.utils.frame_pipe import process_video

METHODS = ["canny", "laplacian", "sobel"]
BACKGROUNDS = ["dimmed", "original", "black"]

GUI_METADATA = {
    'args': {
        'method': {'type': 'select', 'label': 'Edge method', 'default': 'canny', 'choices': METHODS},
        'background': {'type': 'select', 'label': 'Background', 'default': 'dimmed', 'choices': BACKGROUNDS,
                       'help': 'What shows behind the neon lines.'},
        'color': {'type': 'color', 'label': 'Line color', 'default': '#00FFFF'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Neon edge outlines: detect edges (Canny, Laplacian or Sobel) and draw them as glowing "
        "colored lines over a dimmed, original or black background."
    )
    parser.add_argument("--method", choices=METHODS, default="canny", help="Edge detector. Default: canny.")
    parser.add_argument("--color", type=str, default="#00FFFF", help="Line color. Default: #00FFFF.")
    parser.add_argument("--rainbow", action="store_true", help="Cycle the line color through the rainbow over time.")
    parser.add_argument("--sensitivity", type=float, default=0.7,
                        help="How many edges are picked up, 0 (few) to 1 (many). Default: 0.7.")
    parser.add_argument("--thickness", type=int, default=2, help="Line thickness in px. Default: 2.")
    parser.add_argument("--glow", type=int, default=12, help="Glow radius in px (0 = no glow). Default: 12.")
    parser.add_argument("--background", choices=BACKGROUNDS, default="dimmed", help="Background. Default: dimmed.")
    parser.add_argument("--dim", type=float, default=0.25, help="Brightness of the dimmed background, 0-1. Default: 0.25.")
    parser.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def run(args):
    cv2 = require_cv2()
    base_color = np.array(hex_to_rgb(args.color, (0, 255, 255)), dtype=np.float32)
    sens = min(1.0, max(0.0, args.sensitivity))
    lo, hi = int(220 - 190 * sens), int(330 - 230 * sens)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(1, args.thickness), max(1, args.thickness)))
    glow_k = (args.glow * 2 + 1) if args.glow > 0 else 0

    def frame_fn(frame, i, t):
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        if args.method == "canny":
            edges = cv2.Canny(gray, lo, hi)
        elif args.method == "laplacian":
            edges = cv2.convertScaleAbs(cv2.Laplacian(gray, cv2.CV_16S, ksize=3))
            edges = np.where(edges > (60 - 50 * sens), 255, 0).astype(np.uint8)
        else:
            gx, gy = cv2.Sobel(gray, cv2.CV_32F, 1, 0), cv2.Sobel(gray, cv2.CV_32F, 0, 1)
            mag = cv2.magnitude(gx, gy)
            edges = np.where(mag > (260 - 220 * sens), 255, 0).astype(np.uint8)
        if args.thickness > 1:
            edges = cv2.dilate(edges, kernel)
        if args.rainbow:
            r, g, b = colorsys.hsv_to_rgb((t * 0.15) % 1.0, 1.0, 1.0)
            color = np.array([r, g, b], dtype=np.float32) * 255.0
        else:
            color = base_color
        line = (edges.astype(np.float32) / 255.0)[..., None] * color
        if glow_k:
            line = line + cv2.GaussianBlur(line, (glow_k, glow_k), 0) * 1.6
        if args.background == "black":
            bg = np.zeros_like(frame, dtype=np.float32)
        elif args.background == "original":
            bg = frame.astype(np.float32)
        else:
            bg = frame.astype(np.float32) * min(1.0, max(0.0, args.dim))
        return np.clip(bg + line, 0, 255).astype(np.uint8)

    stats = process_video(args.input, args.output, frame_fn, crf=args.crf, force=bool(args.force))
    print(f"✅ {stats['frames']} frames in {stats['seconds']:.1f}s")
