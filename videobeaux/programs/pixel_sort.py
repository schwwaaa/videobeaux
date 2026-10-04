from __future__ import annotations
r"""
videobeaux.programs.pixel_sort - glitch-art pixel sorting

Not a native ffmpeg filter — true pixel-sorting (reordering pixels within a row
by brightness, past a threshold) needs per-pixel control ffmpeg's filter graph
doesn't expose. Frames are streamed through numpy (see utils/frame_pipe.py):
no temporary PNGs, handles any input ffmpeg can decode (phone .MOV, 10-bit,
rotated, variable frame rate). Full size by default; --max_width shrinks 4K
footage so it finishes sooner.
"""
import numpy as np

from videobeaux.utils.frame_pipe import process_video


def pixel_sort_frame(arr: np.ndarray, threshold: int, vertical: bool) -> np.ndarray:
    """
    Sort every run of consecutive pixels brighter than `threshold` (within a
    row, or a column if `vertical`) by brightness — all rows at once.

    Each pixel gets a primary sort key: the index where its run starts if it's
    inside a run (so the whole run sorts as one block, in place), or its own
    index if not (so it never moves). A stable lexsort on (brightness, key)
    then reorders every run simultaneously.
    """
    work = arr.transpose(1, 0, 2) if vertical else arr
    h, w, c = work.shape
    n = h * w
    gray = work[:, :, :3].mean(axis=2, dtype=np.float32).ravel()
    mask = gray > threshold

    idx = np.arange(n)
    prev = np.empty(n, dtype=bool)
    prev[0] = False
    prev[1:] = mask[:-1]
    # Runs never cross a row. Explicit ufunc calls (not chained operators) so numpy never
    # gets the chance to reuse `mask` as scratch space — see utils/numpy_check.py.
    new_run = np.logical_or(np.logical_not(prev), (idx % w) == 0)
    run_start = np.logical_and(mask, new_run)
    start_idx = np.maximum.accumulate(np.where(run_start, idx, 0))
    key = np.where(mask, start_idx, idx)

    order = np.lexsort((gray, key))
    out = work.reshape(n, c)[order].reshape(h, w, c)
    return out.transpose(1, 0, 2) if vertical else out


GUI_METADATA = {
    'args': {
        'max_width': {'label': 'Downscale for speed (px, 0 = off)', 'min': 0, 'max': 4096, 'good_min': 0, 'good_max': 1920,
                      'help': 'Sort at this width to go faster on 4K footage — the result is scaled back up to the original '
                              'size, so the output is never smaller than the input. 0 = no downscaling.'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Glitch-art pixel sorting: within each row (or column), pixels brighter than "
        "the threshold (automatic unless you set --threshold) get sorted by brightness, smearing them into long streaks. Frames are "
        "processed one by one, so it's slower than most effects; for 4K footage set --max_width "
        "(e.g. 1280) to speed it up."
    )
    parser.add_argument("--threshold", type=int, default=None,
                        help="Brightness (0-255) above which pixels get sorted. Leave empty for AUTO: the threshold follows "
                             "each frame's own brightness (about the brightest 60 percent), so dark and bright clips both show "
                             "the effect. Set a number to fix it — lower sorts more.")
    parser.add_argument("--vertical", action="store_true", help="Sort along columns instead of rows.")
    parser.add_argument("--max_width", type=int, default=0,
                        help="Sort at this width if the video is wider (0 = off, the default), then scale the result back up "
                             "to the original size. Use e.g. 1280 to speed up 4K footage.")


def run(args):
    fixed = None if args.threshold is None else max(0, min(255, args.threshold))

    smooth = {"v": None}

    def frame_fn(frame, i, t):
        th = fixed
        if fixed is None:
            # 40th-percentile brightness, eased over time so the streaks don't flicker.
            target = float(np.percentile(frame[::4, ::4, :3].mean(axis=2), 40))
            smooth["v"] = target if smooth["v"] is None else 0.9 * smooth["v"] + 0.1 * target
            th = int(smooth["v"])
        return pixel_sort_frame(frame, th, args.vertical)

    stats = process_video(args.input, args.output, frame_fn, force=bool(getattr(args, "force", False)),
                          max_width=args.max_width or None)
    print(f"✅ Sorted {stats['frames']} frames in {stats['seconds']:.1f}s")
