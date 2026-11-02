"""
local_contrast: CLAHE (contrast-limited adaptive histogram equalisation). Contrast is equalised in small patches of the
picture, so a dark corner and a bright sky both show detail at once. Only the lightness channel is touched, so the
colours stay put. OpenCV, frame by frame.
"""
from videobeaux.utils.cv import require_cv2
from videobeaux.utils.frame_pipe import process_video

GUI_METADATA = {
    'args': {
        'clip': {'label': 'Clip limit', 'min': 0.5, 'max': 8, 'good_min': 1, 'good_max': 4,
                 'help': 'How hard the contrast is pushed in each patch. Higher = more punch, and more grain.'},
        'tiles': {'label': 'Patch grid', 'min': 2, 'max': 32, 'good_min': 4, 'good_max': 16,
                  'help': 'How many patches the picture is split into across. More patches = more local.'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Local Contrast (CLAHE): equalise the contrast in small patches of the picture, so dark and bright areas "
        "both show detail. Only the lightness changes; the colours stay."
    )
    parser.add_argument("--clip", type=float, default=2.0,
                        help="How hard the contrast is pushed in each patch, 0.5-8. Default: 2.0.")
    parser.add_argument("--tiles", type=int, default=8,
                        help="Patches across the picture, 2-32. More patches = more local. Default: 8.")


def run(args):
    cv2 = require_cv2()
    tiles = max(2, min(32, int(args.tiles)))
    clahe = cv2.createCLAHE(clipLimit=max(0.5, min(8.0, float(args.clip))), tileGridSize=(tiles, tiles))

    def frame_fn(frame, i, t):
        lab = cv2.cvtColor(frame, cv2.COLOR_RGB2LAB)
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    stats = process_video(args.input, args.output, frame_fn, force=bool(getattr(args, "force", False)))
    print(f"✅ Local contrast on {stats['frames']} frames in {stats['seconds']:.1f}s")
