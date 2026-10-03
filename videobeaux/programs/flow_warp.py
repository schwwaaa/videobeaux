"""flow_warp — optical-flow smear / push / visualization (OpenCV Farneback)."""
import numpy as np

from videobeaux.utils.cv import require_cv2
from videobeaux.utils.frame_pipe import process_video

MODES = ["smear", "push", "flow_view"]

GUI_METADATA = {
    'args': {
        'mode': {'type': 'select', 'label': 'Mode', 'default': 'smear', 'choices': MODES,
                 'help': 'smear = pixels keep dragging along motion (datamosh-like), push = current frame warped by its motion, flow_view = motion shown as color.'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Motion-driven warping from dense optical flow: Smear drags pixels along motion with "
        "persistence (a datamosh-style melt without codec tricks), Push displaces the current "
        "frame by its motion, Flow View paints the motion as color."
    )
    parser.add_argument("--mode", choices=MODES, default="smear", help="Mode. Default: smear.")
    parser.add_argument("--strength", type=float, default=3.0,
                        help="How far pixels are pushed along the motion. Default: 3.")
    parser.add_argument("--persistence", type=float, default=0.9,
                        help="Smear: how long smeared pixels persist, 0-0.99. Default: 0.9.")
    parser.add_argument("--flow_width", type=int, default=320,
                        help="Width the motion is analyzed at (smaller = faster). Default: 320.")
    parser.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def run(args):
    cv2 = require_cv2()
    state = {"prev": None, "acc": None, "grid": None}
    persist = min(0.99, max(0.0, args.persistence))

    def frame_fn(frame, i, t):
        H, W = frame.shape[:2]
        fw = min(W, max(64, args.flow_width))
        fh = max(2, int(round(H * fw / W)))
        gray = cv2.cvtColor(cv2.resize(frame, (fw, fh), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2GRAY)
        if state["grid"] is None:
            ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
            state["grid"] = (xs, ys)
            state["acc"] = frame.astype(np.float32)
        prev = state["prev"] if state["prev"] is not None else gray
        flow = cv2.calcOpticalFlowFarneback(prev, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        state["prev"] = gray
        flow = cv2.resize(flow, (W, H), interpolation=cv2.INTER_LINEAR)
        flow[..., 0] *= W / fw
        flow[..., 1] *= H / fh
        xs, ys = state["grid"]

        if args.mode == "flow_view":
            mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            hsv = np.zeros((H, W, 3), dtype=np.uint8)
            hsv[..., 0] = (ang * 90 / np.pi).astype(np.uint8)
            hsv[..., 1] = 255
            hsv[..., 2] = np.clip(mag * 12, 0, 255).astype(np.uint8)
            return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

        mx, my = xs - flow[..., 0] * args.strength, ys - flow[..., 1] * args.strength
        if args.mode == "push":
            return cv2.remap(frame, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

        acc = cv2.remap(state["acc"], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        acc = acc * persist + frame.astype(np.float32) * (1.0 - persist)
        state["acc"] = acc
        return np.clip(acc, 0, 255).astype(np.uint8)

    stats = process_video(args.input, args.output, frame_fn, crf=args.crf, force=bool(args.force))
    print(f"✅ {stats['frames']} frames in {stats['seconds']:.1f}s")
