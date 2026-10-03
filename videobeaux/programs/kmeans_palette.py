"""kmeans_palette — reduce the video to its N dominant colors (OpenCV k-means), optionally dithered."""
import numpy as np

from videobeaux.utils.cv import require_cv2
from videobeaux.utils.dither_core import quantize_to_palette, threshold_map, palette_spread
from videobeaux.utils.frame_pipe import process_video

DITHERS = ["none", "bayer4", "bayer8", "blue_noise", "ign"]

GUI_METADATA = {
    'args': {
        'dither': {'type': 'select', 'label': 'Dither', 'default': 'none', 'choices': DITHERS,
                   'help': 'Optionally dither between the palette colors instead of hard banding.'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Adaptive posterize: k-means finds the video's N dominant colors and every pixel snaps to "
        "the nearest one. The palette is refreshed periodically (and smoothed) so it follows scene "
        "changes without flickering."
    )
    parser.add_argument("--colors", type=int, default=6, help="Number of palette colors (2-32). Default: 6.")
    parser.add_argument("--refresh", type=int, default=24,
                        help="Recompute the palette every N frames. Default: 24.")
    parser.add_argument("--dither", choices=DITHERS, default="none", help="Dither pattern. Default: none.")
    parser.add_argument("--pixel_size", type=int, default=1, help="Chunky pixels: process at 1/N size. Default: 1.")
    parser.add_argument("--crf", type=int, default=16, help="x264 quality. Default: 16.")


def run(args):
    cv2 = require_cv2()
    k = min(32, max(2, args.colors))
    state = {"palette": None}
    p = max(1, args.pixel_size)

    def compute_palette(frame):
        small = cv2.resize(frame, (96, 54), interpolation=cv2.INTER_AREA).reshape(-1, 3).astype(np.float32)
        crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 12, 1.0)
        cv2.setRNGSeed(1)
        _, _, centers = cv2.kmeans(small, k, None, crit, 2, cv2.KMEANS_PP_CENTERS)
        centers = centers[np.argsort(centers @ np.array([0.299, 0.587, 0.114], dtype=np.float32))]
        old = state["palette"]
        if old is not None and old.shape == centers.shape:
            centers = old * 0.5 + centers * 0.5          # ease between refreshes
        return centers

    def frame_fn(frame, i, t):
        if state["palette"] is None or i % max(1, args.refresh) == 0:
            state["palette"] = compute_palette(frame)
        pal = np.clip(state["palette"], 0, 255).astype(np.uint8)
        H, W = frame.shape[:2]
        src = frame if p == 1 else cv2.resize(frame, (max(2, W // p), max(2, H // p)), interpolation=cv2.INTER_AREA)
        x = src.astype(np.float32)
        if args.dither != "none":
            thr = threshold_map(args.dither, src.shape[0], src.shape[1], i, False)
            x = x + ((thr - 0.5) * palette_spread(pal) * 255.0)[..., None]
        out = quantize_to_palette(x, pal)
        if p > 1:
            out = cv2.resize(out, (W, H), interpolation=cv2.INTER_NEAREST)
        return out

    stats = process_video(args.input, args.output, frame_fn, crf=args.crf, force=bool(args.force))
    print(f"✅ {stats['frames']} frames in {stats['seconds']:.1f}s")
