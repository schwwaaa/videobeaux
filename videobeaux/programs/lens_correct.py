"""
lens_correct: straightens the bend of a wide-angle or action-camera lens. Barrel distortion (straight edges bowing
outward) and pincushion (edges pinched inward) are both corrected with ffmpeg's lenscorrection filter, using the two
radial coefficients k1 (main) and k2 (fine). The audio is copied unchanged.
"""
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

GUI_METADATA = {
    'args': {
        'k1': {'label': 'Correction k1', 'min': -0.5, 'max': 0.5, 'good_min': -0.4, 'good_max': 0.1,
               'help': 'The main correction. Try negative values for a barrel bulge (wide lenses, action cameras); '
                       'positive values for pinched edges.'},
        'k2': {'label': 'Correction k2', 'min': -0.5, 'max': 0.5, 'good_min': -0.2, 'good_max': 0.2,
               'help': 'A fine correction for the far edges. Set it after k1.'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Lens Correct: straighten the bend of a wide-angle or action-camera lens. Negative k1 removes barrel "
        "distortion (edges bowing out); positive k1 removes pincushion (edges pinched in). k2 is a fine tune."
    )
    parser.add_argument("--k1", type=float, default=-0.2,
                        help="Main correction. Negative for barrel bulge, positive for pincushion. Default: -0.2.")
    parser.add_argument("--k2", type=float, default=0.0,
                        help="Fine correction for the far edges, set after k1. Default: 0.")


def run(args):
    cmd = ["ffmpeg", "-hide_banner", "-i", args.input,
           "-vf", f"lenscorrection=k1={args.k1:.4f}:k2={args.k2:.4f}",
           "-map", "0:v", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-map", "0:a?", "-c:a", "copy", "-movflags", "+faststart"]
    if getattr(args, "force", False):
        cmd.insert(1, "-y")
    cmd.append(str(args.output))
    run_ffmpeg_with_progress(cmd, args.input, args.output)
