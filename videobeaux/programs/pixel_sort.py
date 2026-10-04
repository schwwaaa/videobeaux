from __future__ import annotations
r"""
videobeaux.programs.pixel_sort - glitch-art pixel sorting

Not a native ffmpeg filter — true pixel-sorting (reordering pixels within a row
by brightness, past a threshold) needs per-pixel control ffmpeg's filter graph
doesn't expose. Frames are streamed through numpy (see utils/frame_pipe.py):
no temporary PNGs, handles any input ffmpeg can decode (phone .MOV, 10-bit,
rotated, variable frame rate), and 4K footage is processed at a reduced size
(--max_width) so it finishes in reasonable time.
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
    run_start = mask & (~prev | (idx % w == 0))          # runs never cross a row
    start_idx = np.maximum.accumulate(np.where(run_start, idx, 0))
    key = np.where(mask, start_idx, idx)

    order = np.lexsort((gray, key))
    out = work.reshape(n, c)[order].reshape(h, w, c)
    return out.transpose(1, 0, 2) if vertical else out


def register_arguments(parser):
    parser.description = (
        "Glitch-art pixel sorting: within each row (or column), pixels brighter than "
        "--threshold get sorted by brightness, smearing them into long streaks. Frames are "
        "processed one by one, so it's slower than most effects; wide footage (4K) is "
        "processed at --max_width."
    )
    parser.add_argument("--threshold", type=int, default=100,
                        help="Brightness threshold (0-255) above which pixels get sorted. Default: 100.")
    parser.add_argument("--vertical", action="store_true", help="Sort along columns instead of rows.")
    parser.add_argument("--max_width", type=int, default=1280,
                        help="Process at this width if the video is wider (0 = full size, much slower). Default: 1280.")


def run(args):
    threshold = max(0, min(255, args.threshold))

    def frame_fn(frame, i, t):
        return pixel_sort_frame(frame, threshold, args.vertical)

    stats = process_video(args.input, args.output, frame_fn, force=bool(getattr(args, "force", False)),
                          max_width=args.max_width or None)
    print(f"✅ Sorted {stats['frames']} frames in {stats['seconds']:.1f}s")
