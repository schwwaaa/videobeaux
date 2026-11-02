"""
motion_mask: separates what moves from what stands still, by background subtraction (OpenCV MOG2). The background is
learned from the frames so far, and anything that differs from it counts as moving. Three looks: a black-and-white
mask, the picture with the moving parts tinted, or only the moving parts left on black.
"""
import numpy as np

from videobeaux.utils.cv import require_cv2
from videobeaux.utils.frame_pipe import process_video

MODES = ["mask", "highlight", "isolate"]

GUI_METADATA = {
    'args': {
        'mode': {'label': 'Look',
                 'help': 'mask = white where things move. highlight = the picture with the moving parts tinted red. '
                         'isolate = only the moving parts, on black.'},
        'history': {'label': 'Memory (frames)', 'min': 10, 'max': 1000, 'good_min': 60, 'good_max': 400,
                    'help': 'How many frames the background is learned from. Longer = slower to forget something that stopped moving.'},
        'threshold': {'label': 'Sensitivity', 'min': 4, 'max': 100, 'good_min': 10, 'good_max': 40,
                      'help': 'How different a pixel must be from the background to count as moving. Lower = more sensitive.'},
        'invert': {'label': 'Invert (show what stands still)',
                   'help': 'Swap the moving and still parts.'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Motion Mask: find what moves and show it. The background is learned from the frames so far (OpenCV MOG2); "
        "anything that differs from it is moving. mask = black and white; highlight = the picture with the moving "
        "parts tinted; isolate = only the moving parts."
    )
    parser.add_argument("--mode", choices=MODES, default="mask",
                        help="mask (default) = white where things move; highlight = tinted picture; isolate = moving parts only.")
    parser.add_argument("--history", type=int, default=200,
                        help="Frames the background is learned from, 10-1000. Default: 200.")
    parser.add_argument("--threshold", type=int, default=16,
                        help="How different a pixel must be to count as moving, 4-100. Lower = more sensitive. Default: 16.")
    parser.add_argument("--invert", action="store_true", help="Show what stands still instead of what moves.")


def run(args):
    cv2 = require_cv2()
    subtractor = cv2.createBackgroundSubtractorMOG2(history=max(10, args.history),
                                                    varThreshold=max(4, args.threshold), detectShadows=False)

    def frame_fn(frame, i, t):
        moving = cv2.medianBlur(subtractor.apply(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)), 5)
        if args.invert:
            moving = 255 - moving
        on = moving > 127
        if args.mode == "mask":
            return np.dstack([moving, moving, moving])
        if args.mode == "isolate":
            return frame * on[..., None]
        out = frame.copy()
        out[on] = (frame[on] * 0.4 + np.array([255, 60, 60]) * 0.6).astype(np.uint8)
        return out

    stats = process_video(args.input, args.output, frame_fn, force=bool(getattr(args, "force", False)))
    print(f"✅ Motion mask on {stats['frames']} frames in {stats['seconds']:.1f}s")
