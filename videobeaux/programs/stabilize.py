"""stabilize — remove camera shake with OpenCV feature tracking (two-pass)."""
import numpy as np

from videobeaux.utils.cv import require_cv2
from videobeaux.utils.frame_pipe import iter_frames, probe_video, process_video

GUI_METADATA = {'args': {}}


def register_arguments(parser):
    parser.description = (
        "Video stabilization: tracks camera motion with feature points, smooths the camera path, "
        "and re-renders each frame along the smoothed path. Zooms in slightly to hide the edges."
    )
    parser.add_argument("--smoothness", type=int, default=30,
                        help="Smoothing window in frames — larger = steadier, floatier camera. Default: 30.")
    parser.add_argument("--zoom", type=float, default=1.06,
                        help="Zoom to hide moving borders (1.0 = none, shows edges). Default: 1.06.")
    parser.add_argument("--analysis_width", type=int, default=480,
                        help="Width the motion is analyzed at (smaller = faster). Default: 480.")
    parser.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def estimate_transforms(path, cv2, analysis_width):
    """Per-frame (dx, dy, dangle) between consecutive frames, in analysis-scale pixels."""
    prev, out, scale_w = None, [], None
    for i, frame in iter_frames(path, analysis_width):
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        scale_w = gray.shape[1]
        if prev is None:
            out.append((0.0, 0.0, 0.0))
        else:
            pts = cv2.goodFeaturesToTrack(prev, maxCorners=300, qualityLevel=0.01, minDistance=15, blockSize=3)
            dx = dy = da = 0.0
            if pts is not None and len(pts) >= 6:
                nxt, st, _ = cv2.calcOpticalFlowPyrLK(prev, gray, pts, None)
                ok = st.ravel() == 1
                if ok.sum() >= 6:
                    m, _ = cv2.estimateAffinePartial2D(pts[ok], nxt[ok], method=cv2.RANSAC)
                    if m is not None:
                        dx, dy, da = float(m[0, 2]), float(m[1, 2]), float(np.arctan2(m[1, 0], m[0, 0]))
            out.append((dx, dy, da))
        prev = gray
    return np.array(out, dtype=np.float64), scale_w


def smooth_path(traj, radius):
    r = max(1, int(radius))
    kernel = np.ones(2 * r + 1) / (2 * r + 1)
    padded = np.pad(traj, ((r, r), (0, 0)), mode="edge")
    return np.stack([np.convolve(padded[:, c], kernel, mode="valid") for c in range(traj.shape[1])], axis=1)


def run(args):
    cv2 = require_cv2()
    info = probe_video(args.input)
    print("🔎 Analyzing camera motion (pass 1 of 2)…", flush=True)
    deltas, aw = estimate_transforms(args.input, cv2, args.analysis_width)
    if len(deltas) < 3:
        raise SystemExit("❌ Not enough frames to stabilize.")
    traj = np.cumsum(deltas, axis=0)
    smooth = smooth_path(traj, args.smoothness)
    corr = smooth - traj                                   # how far to move each frame to sit on the smooth path
    px = (info.width - info.width % 2) / float(aw)         # analysis px -> full-res px
    corr[:, 0] *= px
    corr[:, 1] *= px
    raw_jitter = float(np.sqrt(((traj - smooth)[:, :2] * px) ** 2).mean())
    print(f"📐 Average camera shake removed: {raw_jitter:.1f}px", flush=True)
    print("🎞️  Rendering stabilized video (pass 2 of 2)…", flush=True)
    zoom = max(1.0, args.zoom)

    def frame_fn(frame, i, t):
        H, W = frame.shape[:2]
        dx, dy, da = corr[min(i, len(corr) - 1)]
        c, s = np.cos(da) * zoom, np.sin(da) * zoom
        cx, cy = W / 2.0, H / 2.0
        M = np.array([[c, -s, (1 - c) * cx + s * cy + dx],
                      [s, c, (1 - c) * cy - s * cx + dy]], dtype=np.float32)
        return cv2.warpAffine(frame, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    stats = process_video(args.input, args.output, frame_fn, crf=args.crf, force=bool(args.force))
    print(f"✅ {stats['frames']} frames in {stats['seconds']:.1f}s")
