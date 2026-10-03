"""
face_redact — blur, pixelate, fill or dither over tracked faces (OpenCV).

Privacy/anonymization for faces in video. Faces are detected and tracked with
smoothed boxes; --invert flips it so everything EXCEPT the faces is obscured.
"""
import numpy as np

from videobeaux.utils.cv import require_cv2
from videobeaux.utils.dither_core import dither_frame
from videobeaux.utils.face_tracking import FaceTracker, hex_to_rgb, padded
from videobeaux.utils.frame_pipe import process_video, probe_video
from videobeaux.utils.palettes import PALETTES, to_array

EFFECTS = ["blur", "pixelate", "solid", "dither"]
SHAPES = ["ellipse", "box"]

GUI_METADATA = {
    'args': {
        'effect': {'type': 'select', 'label': 'Effect', 'default': 'blur', 'choices': EFFECTS},
        'shape': {'type': 'select', 'label': 'Shape', 'default': 'ellipse', 'choices': SHAPES},
        'color': {'type': 'color', 'label': 'Fill color (solid)', 'default': '#000000'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Obscure tracked faces with blur, pixelation, a solid fill or 1-bit dither. "
        "Use Invert to hide everything except the faces."
    )
    parser.add_argument("--effect", choices=EFFECTS, default="blur", help="Obscuring effect. Default: blur.")
    parser.add_argument("--shape", choices=SHAPES, default="ellipse", help="Region shape. Default: ellipse.")
    parser.add_argument("--strength", type=int, default=30,
                        help="Blur radius / pixel block size, relative to face size (1-100). Default: 30.")
    parser.add_argument("--color", type=str, default="#000000", help="Fill color for the solid effect.")
    parser.add_argument("--padding", type=float, default=0.25,
                        help="Grow the face region by this fraction (covers hair/ears and tracking lag). Default: 0.25.")
    parser.add_argument("--invert", action="store_true", help="Obscure everything except the faces.")
    parser.add_argument("--detect_every", type=int, default=2,
                        help="Run face detection every N frames. Lower = safer for fast motion. Default: 2.")
    parser.add_argument("--min_confidence", type=float, default=0.5,
                        help="Detection confidence threshold, 0-1. Lower catches more faces. Default: 0.5.")
    parser.add_argument("--smoothing", type=float, default=0.3,
                        help="Track smoothing, 0 = snappy. Keep low for redaction. Default: 0.3.")
    parser.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def _apply_effect(cv2, img, effect, strength, color):
    h, w = img.shape[:2]
    if effect == "blur":
        k = max(3, int(max(w, h) * strength / 100.0 / 2) * 2 + 1)
        return cv2.GaussianBlur(img, (k, k), 0)
    if effect == "pixelate":
        block = max(2, int(max(w, h) * strength / 100.0 / 3))
        small = cv2.resize(img, (max(1, w // block), max(1, h // block)), interpolation=cv2.INTER_AREA)
        return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
    if effect == "solid":
        out = np.empty_like(img)
        out[:] = color
        return out
    return dither_frame(img, method="bayer4", palette=to_array(PALETTES["bw"]),
                        pixel_size=max(1, strength // 10))


def run(args):
    cv2 = require_cv2()
    color = hex_to_rgb(args.color, (0, 0, 0))
    info = probe_video(args.input)
    W, H = info.width - info.width % 2, info.height - info.height % 2
    tracker = FaceTracker(W, H, detect_every=args.detect_every, min_confidence=args.min_confidence,
                          smoothing=args.smoothing, max_missed=8)
    strength = min(100, max(1, args.strength))

    def frame_fn(frame, i, t):
        tracks = tracker.update(frame, i)
        if not tracks and not args.invert:
            return frame
        mask = np.zeros((H, W), dtype=np.float32)
        for tr in tracks:
            x, y, w, h = padded(tr, args.padding)
            if args.shape == "ellipse":
                cv2.ellipse(mask, (int(x + w / 2), int(y + h / 2)),
                            (max(1, int(w / 2)), max(1, int(h / 2))), 0, 0, 360, 1.0, -1)
            else:
                cv2.rectangle(mask, (int(x), int(y)), (int(x + w), int(y + h)), 1.0, -1)
        if args.invert:
            mask = 1.0 - mask
        if not mask.any():
            return frame
        k = max(3, int(min(W, H) * 0.012) | 1)
        mask = cv2.GaussianBlur(mask, (k, k), 0)[..., None]
        effected = _apply_effect(cv2, frame, args.effect, strength, color)
        return (frame * (1 - mask) + effected * mask).astype(np.uint8)

    stats = process_video(args.input, args.output, frame_fn, crf=args.crf, force=bool(args.force))
    print(f"✅ {tracker.summary()} — {stats['frames']} frames in {stats['seconds']:.1f}s")
