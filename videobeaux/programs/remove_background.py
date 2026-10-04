"""
remove_background — cut the subject out of a video and put anything behind it, or export it with a transparent
background (WebM / MOV).

Engines:
  • static camera  — no download. Builds a clean "empty scene" from the clip itself and masks whatever differs from
    it; best when the camera doesn't move and the subject does.
  • AI (u2netp)    — small, general-purpose cut-out model (~5 MB, one-time opt-in download).
  • AI (people)    — U²-Net trained for people (~170 MB, one-time opt-in download).
Everything runs locally. Use View = matte to tune: white = kept, black = removed.
"""
import tempfile
from pathlib import Path

import numpy as np

from videobeaux.utils import bgremove, keying
from videobeaux.utils.cv import require_cv2
from videobeaux.utils.frame_pipe import process_video

ENGINES = ["static camera (no download)", "AI · fast (u2netp)", "AI · people (u2net human)"]
_MODEL_FOR = {ENGINES[1]: "u2netp", ENGINES[2]: "u2net_human_seg"}

GUI_METADATA = {
    'args': {
        **keying.GUI_COMMON,
        'engine': {'type': 'select', 'label': 'Engine', 'default': ENGINES[0], 'choices': ENGINES,
                   'help': 'static camera works instantly if the camera is locked off. The AI engines need a one-time '
                           'model download from Setup → Local AI features.'},
        'sensitivity': {'label': 'Sensitivity (static)', 'min': 2, 'max': 120,
                        'help': 'Static engine: how different from the empty scene a pixel must be to count as subject. Lower = more.'},
        'threshold': {'label': 'Threshold (AI)', 'min': 0, 'max': 1, 'help': 'AI engines: matte level that counts as subject.'},
        'softness': {'label': 'Edge softness', 'min': 0.02, 'max': 1},
        'smoothing': {'label': 'Temporal smoothing', 'min': 0, 'max': 0.95, 'help': 'Blends each frame\'s matte with the previous one to stop flicker.'},
        'fill_holes': {'label': 'Fill holes', 'help': 'Fill gaps inside the subject.'},
        'largest_only': {'label': 'Keep largest subject only', 'help': 'Drop small stray blobs; keep the biggest connected shape.'},
        'invert': {'label': 'Invert', 'help': 'Keep the background instead of the subject.'},
        'detail': {'label': 'Processing width (px)', 'min': 240, 'max': 3840, 'help': 'The matte is computed at this width, then scaled up.'},
        'shrink': {'label': 'Edge shrink', 'min': 0, 'max': 10},
        'feather': {'label': 'Edge feather', 'min': 0, 'max': 10},
    }
}


def register_arguments(p):
    p.description = (
        "Remove the background: cut the subject out and replace what's behind it, or export transparent "
        "WebM/MOV. Engines: static camera (no download), AI fast (u2netp), AI people (u2net human). "
        "Use --view matte to tune; --smoothing steadies the edges over time."
    )
    p.add_argument("--engine", choices=ENGINES, default=ENGINES[0], help="How the subject is found.")
    p.add_argument("--sensitivity", type=float, default=28.0, help="Static engine: difference threshold. Default: 28.")
    p.add_argument("--threshold", type=float, default=0.5, help="AI engines: matte threshold, 0 to 1. Default: 0.5.")
    p.add_argument("--softness", type=float, default=0.25, help="Edge softness of the matte, 0 to 1. Default: 0.25.")
    p.add_argument("--smoothing", type=float, default=0.5, help="Temporal smoothing 0 to 0.95. Default: 0.5.")
    p.add_argument("--fill_holes", action="store_true", help="Fill holes inside the subject.")
    p.add_argument("--largest_only", action="store_true", help="Keep only the largest connected subject.")
    p.add_argument("--invert", action="store_true", help="Keep the background, remove the subject.")
    p.add_argument("--detail", type=int, default=960, help="Width the matte is computed at. Default: 960.")
    keying.add_common_arguments(p)


def clean_matte(cv2, m, *, fill_holes=False, largest_only=False):
    """m: float 0..1 → cleaned float 0..1 (structure fixes on the hard shape, soft edges kept)."""
    if not (fill_holes or largest_only):
        return m
    hard = (m > 0.5).astype(np.uint8)
    cnts, _ = cv2.findContours(hard, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    keep = np.zeros_like(hard)
    if cnts:
        picks = [max(cnts, key=cv2.contourArea)] if largest_only else cnts
        cv2.drawContours(keep, picks, -1, 1, thickness=-1 if fill_holes else 1)
        if not fill_holes:                       # largest only, but holes stay: mask the original shape
            single = np.zeros_like(hard)
            cv2.drawContours(single, picks, -1, 1, thickness=-1)
            keep = single & hard
    region = cv2.dilate(keep, np.ones((3, 3), np.uint8)).astype(np.float32)
    out = np.maximum(m * region if largest_only else m, keep.astype(np.float32) if fill_holes else 0.0)
    return np.clip(out, 0.0, 1.0)


def run(args):
    cv2 = require_cv2()
    engine = args.engine
    out = Path(args.output)
    smoothing = max(0.0, min(0.95, args.smoothing))
    soft = max(0.02, min(1.0, args.softness))
    st = {"prev": None, "plate": None, "matter": None}

    if engine in _MODEL_FOR:
        st["matter"] = bgremove.OnnxMatter(_MODEL_FOR[engine])
    else:
        print("ℹ️  Building the empty-scene plate from the clip…", flush=True)
        st["plate"] = bgremove.static_plate(args.input, width=max(160, min(args.detail, 960)))

    def frame_fn(frame, i, t):
        if st["matter"] is not None:
            raw = st["matter"](cv2, frame)
            m = np.clip((raw - (args.threshold - soft / 2.0)) / soft, 0.0, 1.0)
        else:
            m = bgremove.plate_matte(cv2, frame, st["plate"], args.sensitivity, softness=10.0 + 70.0 * soft)
            m = cv2.medianBlur((m * 255).astype(np.uint8), 5).astype(np.float32) / 255.0
        m = clean_matte(cv2, m, fill_holes=args.fill_holes, largest_only=args.largest_only)
        if args.invert:
            m = 1.0 - m
        if smoothing > 0:
            st["prev"] = m if st["prev"] is None else smoothing * st["prev"] + (1.0 - smoothing) * m
            m = st["prev"]
        g = (np.clip(m, 0, 1) * 255.0 + 0.5).astype(np.uint8)
        return np.dstack([g, g, g])

    tmp = Path(tempfile.mkdtemp(prefix="vb_bgremove_"))
    try:
        matte = tmp / "matte.mp4"
        print("ℹ️  Finding the subject in every frame…", flush=True)
        process_video(args.input, matte, frame_fn, crf=12, force=True, audio=False, max_width=args.detail or None)
        print("ℹ️  Compositing…", flush=True)
        keying.run_key(args, "", matte_path=str(matte))
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
