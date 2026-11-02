"""
clean_plate: removes things that move through a locked-off shot. A clean plate (the empty scene) is built from the
per-pixel median of frames sampled across the clip, so people and cars that pass through are dropped from it. Then:
  remove_movers  every frame keeps its still parts and takes the plate where something moves through it
  plate_only     the empty scene itself, for the whole clip (a useful still background for other effects)
Only works when the camera does not move. A thing that stops for most of the clip becomes part of the plate.
"""
import numpy as np

from videobeaux.utils import bgremove
from videobeaux.utils.cv import require_cv2
from videobeaux.utils.frame_pipe import process_video

MODES = ["remove_movers", "plate_only"]

GUI_METADATA = {
    'args': {
        'mode': {'label': 'Mode',
                 'help': 'remove_movers = take the empty scene wherever something moves through the shot. '
                         'plate_only = the empty scene itself, for the whole clip.'},
        'sensitivity': {'label': 'Sensitivity', 'min': 4, 'max': 120, 'good_min': 15, 'good_max': 50,
                        'help': 'How different a pixel must be from the empty scene to count as something moving. Lower = more sensitive.'},
        'samples': {'label': 'Frames sampled for the plate', 'min': 5, 'max': 80, 'good_min': 15, 'good_max': 40,
                    'help': 'More frames = a cleaner plate, but a slower first pass.'},
        'detail': {'label': 'Processing width (px)', 'min': 160, 'max': 1920, 'good_min': 480, 'good_max': 960,
                   'help': 'The plate and the moving-part mask are worked out at this width, then scaled up.'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Clean Plate: remove people and cars that move through a locked-off shot. The empty scene is built from the "
        "median of sampled frames; remove_movers swaps the moving parts for it, plate_only outputs the empty scene."
    )
    parser.add_argument("--mode", choices=MODES, default="remove_movers",
                        help="remove_movers (default) = replace what moves with the empty scene; plate_only = the empty scene.")
    parser.add_argument("--sensitivity", type=float, default=28.0,
                        help="How different a pixel must be from the empty scene to count as moving, 4-120. Default: 28.")
    parser.add_argument("--samples", type=int, default=25,
                        help="Frames sampled across the clip to build the plate, 5-80. Default: 25.")
    parser.add_argument("--detail", type=int, default=960,
                        help="Width the plate and mask are worked out at, then scaled up. Default: 960.")


def run(args):
    cv2 = require_cv2()
    width = max(160, min(1920, args.detail))
    print("ℹ️  Building the empty scene from the clip…", flush=True)
    plate_small = bgremove.static_plate(args.input, samples=max(5, min(80, args.samples)), width=width)
    stash = {"plate": None}

    def frame_fn(frame, i, t):
        h, w = frame.shape[:2]
        if stash["plate"] is None or stash["plate"].shape[:2] != (h, w):
            stash["plate"] = cv2.resize(plate_small, (w, h), interpolation=cv2.INTER_LINEAR)
        plate = stash["plate"]
        if args.mode == "plate_only":
            return plate.copy()
        m = bgremove.plate_matte(cv2, frame, plate_small, args.sensitivity, softness=18.0)[..., None]
        out = frame.astype(np.float32) * (1.0 - m) + plate.astype(np.float32) * m
        return np.clip(out + 0.5, 0, 255).astype(np.uint8)

    stats = process_video(args.input, args.output, frame_fn, force=bool(getattr(args, "force", False)))
    print(f"✅ Clean plate on {stats['frames']} frames in {stats['seconds']:.1f}s")
