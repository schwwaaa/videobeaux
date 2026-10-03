"""
face_track — detect and track faces, drawing tracking graphics over them (OpenCV).

Boxes / corner brackets / circles / crosshairs with optional IDs and motion
trails, a spotlight that darkens everything outside the faces, or a picture
(sticker/mask) pasted onto each face. Detection uses YuNet when its model file
is present (falls back to OpenCV's Haar cascade) and smoothed tracks keep the
graphics gliding between detections.
"""
from videobeaux.utils.cv import require_cv2
from videobeaux.utils.face_tracking import FaceTracker, clamp_box, hex_to_rgb, padded
from videobeaux.utils.frame_pipe import process_video, probe_video

STYLES = ["corners", "box", "circle", "crosshair", "none"]

GUI_METADATA = {
    'args': {
        'style': {'type': 'select', 'label': 'Style', 'default': 'corners', 'choices': STYLES,
                  'help': "Tracking graphic drawn on each face. 'none' draws nothing (use with Spotlight or Image)."},
        'color': {'type': 'color', 'label': 'Color', 'default': '#00FF88'},
        'overlay_image': {'type': 'file', 'label': 'Overlay image (optional)',
                          'help': 'PNG/JPG pasted onto each face, scaled to fit. PNGs with transparency work best.'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Detect and track faces and draw tracking graphics over them: boxes, corner brackets, "
        "circles, crosshairs, IDs, motion trails, a spotlight, or an image pasted on each face."
    )
    parser.add_argument("--style", choices=STYLES, default="corners",
                        help="Tracking graphic. Default: corners.")
    parser.add_argument("--color", type=str, default="#00FF88", help="Graphic color. Default: #00FF88.")
    parser.add_argument("--thickness", type=int, default=3, help="Line thickness in px. Default: 3.")
    parser.add_argument("--padding", type=float, default=0.15,
                        help="Grow the face box by this fraction before drawing. Default: 0.15.")
    parser.add_argument("--show_id", action="store_true", help="Label each face with its track ID.")
    parser.add_argument("--trail", action="store_true", help="Draw a motion trail behind each face.")
    parser.add_argument("--spotlight", type=float, default=0.0,
                        help="Darken everything outside the faces by this amount, 0-1. Default: 0 (off).")
    parser.add_argument("--overlay_image", type=str, default=None,
                        help="Image to paste onto each face (e.g. a mask or sticker).")
    parser.add_argument("--detect_every", type=int, default=3,
                        help="Run face detection every N frames (tracking fills the gaps). Default: 3.")
    parser.add_argument("--min_confidence", type=float, default=0.6,
                        help="Detection confidence threshold, 0-1. Default: 0.6.")
    parser.add_argument("--smoothing", type=float, default=0.5,
                        help="Track smoothing, 0 = snappy, 0.9 = very smooth. Default: 0.5.")
    parser.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def _load_overlay(cv2, path):
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise SystemExit(f"❌ Could not read overlay image: {path}")
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
    elif img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    rgba = img.copy()
    rgba[..., 0], rgba[..., 2] = img[..., 2], img[..., 0]       # BGRA -> RGBA
    return rgba


def _paste(cv2, frame, rgba, box):
    H, W = frame.shape[:2]
    x0, y0, x1, y1 = clamp_box(*box, W, H)
    bw, bh = int(round(box[2])), int(round(box[3]))
    if bw < 4 or bh < 4 or x1 <= x0 or y1 <= y0:
        return
    patch = cv2.resize(rgba, (bw, bh), interpolation=cv2.INTER_AREA)
    px0, py0 = x0 - int(round(box[0])), y0 - int(round(box[1]))
    patch = patch[py0:py0 + (y1 - y0), px0:px0 + (x1 - x0)]
    ph, pw = patch.shape[:2]          # rounding can leave the patch a pixel short of the clipped ROI
    if ph == 0 or pw == 0:
        return
    a = (patch[..., 3:4].astype("float32")) / 255.0
    roi = frame[y0:y0 + ph, x0:x0 + pw].astype("float32")
    frame[y0:y0 + ph, x0:x0 + pw] = (patch[..., :3] * a + roi * (1 - a)).astype("uint8")


def _draw_corners(cv2, frame, x0, y0, x1, y1, color, th):
    L = max(8, int(min(x1 - x0, y1 - y0) * 0.22))
    for (cx, cy, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        cv2.line(frame, (cx, cy), (cx + dx * L, cy), color, th, cv2.LINE_AA)
        cv2.line(frame, (cx, cy), (cx, cy + dy * L), color, th, cv2.LINE_AA)


def run(args):
    cv2 = require_cv2()
    color = hex_to_rgb(args.color)
    overlay = _load_overlay(cv2, args.overlay_image) if args.overlay_image else None
    info = probe_video(args.input)
    W, H = info.width - info.width % 2, info.height - info.height % 2
    tracker = FaceTracker(W, H, detect_every=args.detect_every, min_confidence=args.min_confidence,
                          smoothing=args.smoothing)
    th = max(1, args.thickness)
    spot = min(1.0, max(0.0, args.spotlight))

    def frame_fn(frame, i, t):
        tracks = tracker.update(frame, i)
        if spot > 0:
            mask = frame[..., 0] * 0.0
            for tr in tracks:
                x, y, w, h = padded(tr, args.padding + 0.1)
                cv2.ellipse(mask, (int(x + w / 2), int(y + h / 2)), (max(1, int(w / 2)), max(1, int(h / 2))),
                            0, 0, 360, 1.0, -1)
            k = max(3, int(min(W, H) * 0.08) | 1)
            mask = cv2.GaussianBlur(mask, (k, k), 0)[..., None]
            frame = (frame * (mask + (1 - mask) * (1 - spot))).astype("uint8")
        for tr in tracks:
            if overlay is not None:
                _paste(cv2, frame, overlay, padded(tr, args.padding))
            if args.trail and len(tr.trail) > 1:
                pts = [(int(px), int(py)) for px, py in tr.trail]
                for a, b in zip(pts, pts[1:]):
                    cv2.line(frame, a, b, color, max(1, th - 1), cv2.LINE_AA)
            x0, y0, x1, y1 = clamp_box(*padded(tr, args.padding), W, H)
            if args.style == "box":
                cv2.rectangle(frame, (x0, y0), (x1, y1), color, th, cv2.LINE_AA)
            elif args.style == "corners":
                _draw_corners(cv2, frame, x0, y0, x1, y1, color, th)
            elif args.style == "circle":
                cv2.ellipse(frame, ((x0 + x1) // 2, (y0 + y1) // 2), ((x1 - x0) // 2, (y1 - y0) // 2),
                            0, 0, 360, color, th, cv2.LINE_AA)
            elif args.style == "crosshair":
                cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
                r = max(8, (x1 - x0) // 6)
                cv2.line(frame, (cx - r, cy), (cx + r, cy), color, th, cv2.LINE_AA)
                cv2.line(frame, (cx, cy - r), (cx, cy + r), color, th, cv2.LINE_AA)
                _draw_corners(cv2, frame, x0, y0, x1, y1, color, max(1, th - 1))
            if args.show_id:
                cv2.putText(frame, f"ID {tr.id}", (x0, max(14, y0 - 8)), cv2.FONT_HERSHEY_SIMPLEX,
                            max(0.5, (x1 - x0) / 220.0), color, max(1, th - 1), cv2.LINE_AA)
        return frame

    stats = process_video(args.input, args.output, frame_fn, crf=args.crf, force=bool(args.force))
    print(f"✅ {tracker.summary()} — {stats['frames']} frames in {stats['seconds']:.1f}s")
