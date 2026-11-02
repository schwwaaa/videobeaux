"""
color_match: matches the colour of the clip to a reference clip (or still image). The Reinhard method: the average and
spread of each channel in LAB colour are moved from the clip's own to the reference's. The statistics are measured
once over sampled frames, so the whole clip gets one consistent correction and does not flicker. Audio is copied.
"""
import numpy as np

from videobeaux.utils.cv import require_cv2
from videobeaux.utils.frame_pipe import iter_frames, probe_video, process_video

GUI_METADATA = {
    'args': {
        'reference': {'type': 'file', 'subtype': 'video', 'required': True, 'label': 'Reference',
                      'help': 'Connect the clip or still whose colour you want to match.'},
        'strength': {'label': 'Strength', 'min': 0, 'max': 1, 'good_min': 0.3, 'good_max': 1,
                     'help': '1 = the reference colour in full. Lower blends the match back toward the original.'},
        'samples': {'label': 'Frames sampled', 'min': 3, 'max': 60, 'good_min': 10, 'good_max': 30,
                    'help': 'Frames used to measure each clip\'s colour. More = steadier, slower to measure.'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Color Match: move the clip's colour toward a reference clip or still (Reinhard LAB transfer). The colour is "
        "measured once over sampled frames, so the correction is the same across the whole clip."
    )
    parser.add_argument("--reference", required=True, type=str,
                        help="The clip or still image whose colour to match.")
    parser.add_argument("--strength", type=float, default=1.0,
                        help="How far to move toward the reference, 0-1. Default: 1.0.")
    parser.add_argument("--samples", type=int, default=20,
                        help="Frames sampled from each video to measure its colour, 3-60. Default: 20.")


def _sample_lab(path, samples, cv2):
    """Mean and standard deviation of each LAB channel over evenly sampled frames of `path`."""
    total = max(1, probe_video(path).frames)          # a still image counts as one frame
    wanted = set(np.linspace(0, max(0, total - 1), min(samples, total)).astype(int).tolist())
    pixels = []
    for i, frame in iter_frames(path, width=320):
        if i in wanted:
            lab = cv2.cvtColor(frame, cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(np.float32)
            pixels.append(lab[::7])                      # every 7th pixel is plenty for a colour average
        if len(pixels) >= len(wanted):
            break
    if not pixels:
        raise RuntimeError(f"Couldn't read colour from {path}.")
    stack = np.concatenate(pixels)
    # a flat-coloured clip has almost no spread, which would blow the gain up: keep at least 1 level
    return stack.mean(axis=0), np.maximum(stack.std(axis=0), 1.0)


def run(args):
    cv2 = require_cv2()
    strength = max(0.0, min(1.0, args.strength))
    samples = max(3, min(60, args.samples))
    src_mean, src_std = _sample_lab(args.input, samples, cv2)
    ref_mean, ref_std = _sample_lab(args.reference, samples, cv2)
    gain = ref_std / src_std

    def frame_fn(frame, i, t):
        lab = cv2.cvtColor(frame, cv2.COLOR_RGB2LAB).astype(np.float32)
        moved = (lab - src_mean) * gain + ref_mean
        blended = lab * (1.0 - strength) + moved * strength
        blended = np.clip(blended, 0, 255).astype(np.uint8)
        return cv2.cvtColor(blended, cv2.COLOR_LAB2RGB)

    stats = process_video(args.input, args.output, frame_fn, force=bool(getattr(args, "force", False)))
    print(f"✅ Colour matched on {stats['frames']} frames in {stats['seconds']:.1f}s")
