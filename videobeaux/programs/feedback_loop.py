"""
feedback_loop — classic video-mixer feedback: the output is fed back into the mix, zoomed, rotated, shifted
and hue-shifted a little each frame, so the picture spirals into itself. OpenCV, fully offline.
"""
import numpy as np

from videobeaux.utils.cv import require_cv2
from videobeaux.utils.frame_pipe import process_video

MIXES = ["screen", "lighten", "add", "mix", "over (keyed by brightness)"]

GUI_METADATA = {
    'args': {
        'decay': {'label': 'Feedback amount', 'min': 0, 'max': 1, 'help': 'How much of the previous output returns. Near 1 = long, endless trails.'},
        'zoom': {'label': 'Zoom (% per frame)', 'min': -20, 'max': 20, 'help': 'Positive zooms the echo outward into a tunnel; negative shrinks it inward.'},
        'rotate': {'label': 'Rotate (° per frame)', 'min': -30, 'max': 30},
        'shift_x': {'label': 'Shift X (px)', 'min': -100, 'max': 100},
        'shift_y': {'label': 'Shift Y (px)', 'min': -100, 'max': 100},
        'hue_shift': {'label': 'Hue shift (° per frame)', 'min': -45, 'max': 45},
        'mix_mode': {'type': 'select', 'label': 'Combine', 'default': MIXES[0], 'choices': MIXES,
                     'help': 'How the live picture joins the feedback.'},
        'threshold': {'label': 'Key threshold', 'min': 0, 'max': 255,
                      'help': "For 'over (keyed)': only live pixels brighter than this are drawn over the feedback."},
        'crf': {'hidden': True},
    }
}


def register_arguments(p):
    p.description = (
        "Video feedback: the output is fed back into the mix, zoomed, rotated, shifted and hue-shifted a little "
        "each frame, spiraling the picture into itself like pointing a camera at its own monitor."
    )
    p.add_argument("--decay", type=float, default=0.7, help="Feedback amount, 0 to 1. Default: 0.7.")
    p.add_argument("--zoom", type=float, default=2.0, help="Zoom per frame in percent. Default: 2.")
    p.add_argument("--rotate", type=float, default=1.0, help="Rotation per frame in degrees. Default: 1.")
    p.add_argument("--shift_x", type=float, default=0.0, help="Horizontal shift per frame in pixels. Default: 0.")
    p.add_argument("--shift_y", type=float, default=0.0, help="Vertical shift per frame in pixels. Default: 0.")
    p.add_argument("--hue_shift", type=float, default=4.0, help="Hue shift per frame in degrees. Default: 4.")
    p.add_argument("--mix_mode", choices=MIXES, default=MIXES[0], help="How the live picture joins the feedback.")
    p.add_argument("--threshold", type=int, default=90, help="Brightness key for the 'over' mode, 0-255. Default: 90.")
    p.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def run(args):
    cv2 = require_cv2()
    decay = max(0.0, min(0.995, args.decay))
    st = {"fb": None}

    def frame_fn(frame, i, t):
        H, W = frame.shape[:2]
        if st["fb"] is None:
            st["fb"] = frame.copy()
        fb = st["fb"]
        m = cv2.getRotationMatrix2D((W / 2.0, H / 2.0), args.rotate, 1.0 + args.zoom / 100.0)
        m[0, 2] += args.shift_x
        m[1, 2] += args.shift_y
        fb = cv2.warpAffine(fb, m, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        if abs(args.hue_shift) > 0.01:
            hsv = cv2.cvtColor(fb, cv2.COLOR_RGB2HSV)
            hsv[..., 0] = (hsv[..., 0].astype(np.int16) + int(round(args.hue_shift / 2.0))) % 180
            fb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
        f = frame.astype(np.float32)
        b = fb.astype(np.float32) * decay
        if args.mix_mode == "screen":
            out = 255.0 - (255.0 - f) * (255.0 - b) / 255.0
        elif args.mix_mode == "lighten":
            out = np.maximum(f, b)
        elif args.mix_mode == "add":
            out = f + b
        elif args.mix_mode == "mix":
            out = f * (1.0 - decay) + fb.astype(np.float32) * decay
        else:
            key = (cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY) > args.threshold)[..., None]
            out = np.where(key, f, b)
        out = np.clip(out, 0, 255).astype(np.uint8)
        st["fb"] = out
        return out

    stats = process_video(args.input, args.output, frame_fn, crf=args.crf, force=bool(getattr(args, "force", False)))
    print(f"✅ {stats['frames']} frames in {stats['seconds']:.1f}s")
