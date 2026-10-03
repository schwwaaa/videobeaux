"""feature_trails — HUD-style tracked-point network over the video (OpenCV Lucas-Kanade)."""
from collections import deque

import numpy as np

from videobeaux.utils.cv import hex_to_rgb, require_cv2
from videobeaux.utils.frame_pipe import process_video

BACKGROUNDS = ["dimmed", "original", "black"]

GUI_METADATA = {
    'args': {
        'background': {'type': 'select', 'label': 'Background', 'default': 'dimmed', 'choices': BACKGROUNDS},
        'color': {'type': 'color', 'label': 'Color', 'default': '#7CFFCB'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Tracking-HUD look: finds corner features, follows them with optical flow and draws "
        "points, motion trails and connecting lines between nearby points."
    )
    parser.add_argument("--points", type=int, default=140, help="Maximum tracked points. Default: 140.")
    parser.add_argument("--trail_length", type=int, default=10, help="Frames of trail behind each point. Default: 10.")
    parser.add_argument("--link_distance", type=float, default=0.12,
                        help="Connect points closer than this fraction of the frame width (0 = no lines). Default: 0.12.")
    parser.add_argument("--color", type=str, default="#7CFFCB", help="Graphic color. Default: #7CFFCB.")
    parser.add_argument("--background", choices=BACKGROUNDS, default="dimmed", help="Background. Default: dimmed.")
    parser.add_argument("--dim", type=float, default=0.45, help="Brightness of the dimmed background, 0-1. Default: 0.45.")
    parser.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def run(args):
    cv2 = require_cv2()
    color = tuple(int(c) for c in hex_to_rgb(args.color, (124, 255, 203)))
    max_pts = max(10, args.points)
    state = {"prev": None, "pts": None, "hist": []}
    lk = dict(winSize=(21, 21), maxLevel=3,
              criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 20, 0.03))

    def detect(gray, existing):
        mask = np.full(gray.shape, 255, dtype=np.uint8)
        for p in existing:
            cv2.circle(mask, (int(p[0]), int(p[1])), 12, 0, -1)
        return cv2.goodFeaturesToTrack(gray, maxCorners=max_pts, qualityLevel=0.01,
                                       minDistance=14, mask=mask, blockSize=7)

    def frame_fn(frame, i, t):
        H, W = frame.shape[:2]
        pw = 640 if W > 640 else W
        s = pw / W
        small = cv2.resize(frame, (pw, max(2, int(H * s))), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)

        pts, hist = state["pts"], state["hist"]
        if pts is not None and len(pts) and state["prev"] is not None:
            new, st, _ = cv2.calcOpticalFlowPyrLK(state["prev"], gray, pts, None, **lk)
            keep = st.ravel() == 1
            pts = new[keep]
            hist = [h for h, k in zip(hist, keep) if k]
            for h, p in zip(hist, pts):
                h.append((float(p[0, 0]), float(p[0, 1])))
        else:
            pts, hist = np.empty((0, 1, 2), dtype=np.float32), []
        if len(pts) < max_pts * 0.6 or i % 15 == 0:
            fresh = detect(gray, pts.reshape(-1, 2))
            if fresh is not None:
                room = max_pts - len(pts)
                fresh = fresh[:room]
                pts = np.concatenate([pts, fresh.astype(np.float32)]) if len(pts) else fresh.astype(np.float32)
                for p in fresh:
                    h = deque(maxlen=max(2, args.trail_length))
                    h.append((float(p[0, 0]), float(p[0, 1])))
                    hist.append(h)
        state.update(prev=gray, pts=pts, hist=hist)

        if args.background == "black":
            out = np.zeros_like(frame)
        elif args.background == "original":
            out = frame.copy()
        else:
            out = (frame.astype(np.float32) * min(1.0, max(0.0, args.dim))).astype(np.uint8)

        inv = 1.0 / s
        P = pts.reshape(-1, 2) * inv
        if args.link_distance > 0 and len(P) > 1:
            d = np.hypot(P[:, None, 0] - P[None, :, 0], P[:, None, 1] - P[None, :, 1])
            lim = args.link_distance * W
            for a in range(len(P)):
                for b in np.argsort(d[a])[1:4]:
                    if b > a and d[a, b] < lim:
                        fade = 1.0 - d[a, b] / lim
                        c = tuple(int(v * (0.25 + 0.75 * fade)) for v in color)
                        cv2.line(out, (int(P[a, 0]), int(P[a, 1])), (int(P[b, 0]), int(P[b, 1])), c, 1, cv2.LINE_AA)
        for h in hist:
            if len(h) > 1:
                pl = np.array([(x * inv, y * inv) for x, y in h], dtype=np.int32).reshape(-1, 1, 2)
                cv2.polylines(out, [pl], False, color, 1, cv2.LINE_AA)
        for x, y in P:
            cv2.circle(out, (int(x), int(y)), max(2, W // 320), color, -1, cv2.LINE_AA)
        return out

    stats = process_video(args.input, args.output, frame_fn, crf=args.crf, force=bool(args.force))
    print(f"✅ {stats['frames']} frames in {stats['seconds']:.1f}s")
