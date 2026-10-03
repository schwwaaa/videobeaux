"""
face_follow — smart reframe: a smoothed virtual camera that keeps a face in shot (OpenCV).

Zooms in and pans to follow the chosen face while the output stays the same
size as the input. Pairs well with Shortify for vertical clips, or on its own
to turn a wide talking-head shot into a steady close-up.
"""
import numpy as np

from videobeaux.utils.cv import require_cv2
from videobeaux.utils.face_tracking import FaceTracker
from videobeaux.utils.frame_pipe import process_video, probe_video

TARGETS = ["largest", "first", "center"]
NO_FACE = ["hold", "zoom_out"]

GUI_METADATA = {
    'args': {
        'target': {'type': 'select', 'label': 'Follow', 'default': 'largest', 'choices': TARGETS,
                   'help': 'Which face to follow when several are visible.'},
        'no_face': {'type': 'select', 'label': 'When no face', 'default': 'hold', 'choices': NO_FACE,
                    'help': 'hold = stay where the camera was; zoom_out = ease back to the full frame.'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Smart reframe: a smoothed virtual camera that pans and zooms to keep a face in frame. "
        "Output keeps the input's size."
    )
    parser.add_argument("--target", choices=TARGETS, default="largest", help="Which face to follow. Default: largest.")
    parser.add_argument("--zoom", type=float, default=1.6, help="Fixed zoom factor (>=1). Default: 1.6.")
    parser.add_argument("--auto_zoom", action="store_true",
                        help="Pick the zoom so the face fills --face_fraction of the frame width (ignores --zoom).")
    parser.add_argument("--face_fraction", type=float, default=0.3,
                        help="Target face width as a fraction of frame width with --auto_zoom. Default: 0.3.")
    parser.add_argument("--face_y", type=float, default=0.42,
                        help="Where the face sits vertically in the frame, 0 = top, 1 = bottom. Default: 0.42.")
    parser.add_argument("--smoothing", type=float, default=0.9,
                        help="Camera smoothness, 0 = locked on, 0.99 = lazy drift. Default: 0.9.")
    parser.add_argument("--no_face", choices=NO_FACE, default="hold", help="What to do when no face is found. Default: hold.")
    parser.add_argument("--detect_every", type=int, default=3, help="Run detection every N frames. Default: 3.")
    parser.add_argument("--min_confidence", type=float, default=0.6, help="Detection confidence threshold. Default: 0.6.")
    parser.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def run(args):
    cv2 = require_cv2()
    info = probe_video(args.input)
    W, H = info.width - info.width % 2, info.height - info.height % 2
    tracker = FaceTracker(W, H, detect_every=args.detect_every, min_confidence=args.min_confidence,
                          smoothing=0.6)
    follow = 1.0 - min(0.99, max(0.0, args.smoothing))
    state = {"cx": W / 2.0, "cy": H / 2.0, "zoom": 1.0, "have": False}
    fy = min(0.9, max(0.1, args.face_y))

    def pick(tracks):
        if args.target == "largest":
            return max(tracks, key=lambda t: t.w * t.h)
        if args.target == "first":
            return min(tracks, key=lambda t: t.id)
        return min(tracks, key=lambda t: np.hypot(t.center[0] - W / 2, t.center[1] - H / 2))

    def frame_fn(frame, i, t):
        tracks = tracker.update(frame, i)
        if tracks:
            f = pick(tracks)
            z = (args.face_fraction * W / max(f.w, 1.0)) if args.auto_zoom else args.zoom
            z = min(6.0, max(1.0, z))
            cx = f.center[0]
            cy = f.center[1] + (0.5 - fy) * (H / z)         # put the face at face_y of the crop
            if not state["have"]:
                state.update(cx=cx, cy=cy, zoom=z, have=True)
            else:
                state["cx"] += (cx - state["cx"]) * follow
                state["cy"] += (cy - state["cy"]) * follow
                state["zoom"] += (z - state["zoom"]) * follow
        elif args.no_face == "zoom_out":
            state["cx"] += (W / 2.0 - state["cx"]) * follow * 0.5
            state["cy"] += (H / 2.0 - state["cy"]) * follow * 0.5
            state["zoom"] += (1.0 - state["zoom"]) * follow * 0.5
        z = state["zoom"]
        cw, ch = W / z, H / z
        x0 = min(max(0.0, state["cx"] - cw / 2), W - cw)
        y0 = min(max(0.0, state["cy"] - ch / 2), H - ch)
        M = np.array([[z, 0, -x0 * z], [0, z, -y0 * z]], dtype=np.float32)
        return cv2.warpAffine(frame, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    stats = process_video(args.input, args.output, frame_fn, crf=args.crf, force=bool(args.force))
    print(f"✅ {tracker.summary()} — {stats['frames']} frames in {stats['seconds']:.1f}s")
