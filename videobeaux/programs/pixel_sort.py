from __future__ import annotations
r"""
videobeaux.programs.pixel_sort - glitch-art pixel sorting

Not a native ffmpeg filter — true pixel-sorting (reordering pixels within a row
or column, by a per-pixel value, past a threshold) needs per-pixel control
ffmpeg's filter graph doesn't expose. Frames are streamed through numpy (see
utils/frame_pipe.py): no temporary PNGs, handles any input ffmpeg can decode
(phone .MOV, 10-bit, rotated, variable frame rate). Full size by default;
--max_width shrinks 4K footage so it finishes sooner.
"""
import numpy as np

from videobeaux.utils.cv import require_cv2
from videobeaux.utils.frame_pipe import process_video

SELECT = ["brighter", "darker"]
SORT_BY = ["brightness", "hue", "saturation", "red", "green", "blue"]
ORDER = ["ascending", "descending"]
# Auto threshold: about this share of the picture is sorted (the brightest 60 percent, or the darkest 60 percent).
AUTO_SHARE = 0.6


def _run_starts(mask, w, n):
    """For every pixel, the index where its run of masked pixels starts. Runs never cross a row of width w."""
    idx = np.arange(n)
    prev = np.empty(n, dtype=bool)
    prev[0] = False
    prev[1:] = mask[:-1]
    # Explicit ufunc calls (not chained operators) so numpy never gets the chance to reuse `mask`
    # as scratch space — see utils/numpy_check.py.
    new_run = np.logical_or(np.logical_not(prev), (idx % w) == 0)
    run_start = np.logical_and(mask, new_run)
    return np.maximum.accumulate(np.where(run_start, idx, 0))


def _sort_value(work, sort_by):
    """The number each pixel is ordered by inside a run: brightness, hue, saturation, or one colour channel."""
    if sort_by == "brightness":
        return work[:, :, :3].mean(axis=2, dtype=np.float32)
    if sort_by in ("red", "green", "blue"):
        return work[:, :, "rgb".index(sort_by[0])].astype(np.float32)
    cv2 = require_cv2()
    hsv = cv2.cvtColor(np.ascontiguousarray(work[:, :, :3]), cv2.COLOR_RGB2HSV)
    return hsv[:, :, 0 if sort_by == "hue" else 1].astype(np.float32)


def pixel_sort_frame(arr: np.ndarray, threshold: int, vertical: bool, *, sort_by: str = "brightness",
                     descending: bool = False, select: str = "brighter", min_run: int = 1,
                     mix: float = 1.0) -> np.ndarray:
    """
    Sort every run of consecutive pixels within a row (or a column if `vertical`) — all rows at once.

    A pixel is picked when its brightness is above `threshold` (select="brighter") or below it (select="darker").
    Each run of picked pixels is then reordered in place by `sort_by` (ascending or descending). Runs shorter than
    `min_run` are left alone. `mix` blends the result with the original picture (1.0 = fully sorted).

    Each pixel gets a primary sort key: the index where its run starts if it's inside a run (so the whole run
    sorts as one block, in place), or its own index if not (so it never moves). A stable lexsort on
    (sort value, key) then reorders every run simultaneously.
    """
    orig = arr
    work = arr.transpose(1, 0, 2) if vertical else arr
    h, w, c = work.shape
    n = h * w
    brightness = work[:, :, :3].mean(axis=2, dtype=np.float32).ravel()
    value = _sort_value(work, sort_by).ravel()
    mask = brightness > threshold if select == "brighter" else brightness < threshold

    idx = np.arange(n)
    start_idx = _run_starts(mask, w, n)
    if min_run > 1:
        counts = np.bincount(start_idx[mask], minlength=n)
        mask = np.logical_and(mask, counts[start_idx] >= min_run)
        start_idx = _run_starts(mask, w, n)
    key = np.where(mask, start_idx, idx)

    order = np.lexsort((-value if descending else value, key))
    sorted_work = work.reshape(n, c)[order].reshape(h, w, c)
    out = sorted_work.transpose(1, 0, 2) if vertical else sorted_work
    if mix < 1.0:
        blend = orig.astype(np.float32) * (1.0 - mix) + out.astype(np.float32) * mix
        out = np.clip(blend + 0.5, 0, 255).astype(np.uint8)
    return out


GUI_METADATA = {
    'args': {
        'threshold': {'label': 'Threshold (0-255, empty = auto)',
                      'help': 'Brightness above (or below) which pixels get sorted. Leave empty for AUTO: the threshold follows '
                              'each frame\'s own brightness, so the picked share stays about the same from clip to clip. '
                              'Lower = more pixels sorted.'},
        'select': {'label': 'Sort pixels that are', 'help': 'brighter = bright areas smear (default). darker = shadows smear instead.'},
        'sort_by': {'label': 'Sort by', 'help': 'What orders the pixels inside a streak. brightness is the classic look; hue, '
                                                 'saturation or a colour channel give banded colour streaks.'},
        'order': {'label': 'Order', 'help': 'ascending = low values first (streaks run up to bright). descending = the reverse.'},
        'vertical': {'label': 'Vertical streaks', 'help': 'Sort down the columns instead of across the rows.'},
        'min_run': {'label': 'Shortest streak (px)', 'min': 1, 'max': 400, 'good_min': 1, 'good_max': 60,
                    'help': 'Streaks shorter than this stay as they are. 1 = sort everything picked; 8–30 keeps only long streaks.'},
        'mix': {'label': 'Mix with original', 'min': 0, 'max': 1, 'good_min': 0, 'good_max': 1,
                'help': '1 = fully sorted. Lower blends the sorted picture back over the original.'},
        'max_width': {'label': 'Downscale for speed (px, 0 = off)', 'min': 0, 'max': 4096, 'good_min': 0, 'good_max': 1920,
                      'help': 'Sort at this width to go faster on 4K footage — the result is scaled back up to the original '
                              'size, so the output is never smaller than the input. 0 = no downscaling.'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Glitch-art pixel sorting: within each row (or column), the pixels brighter than the threshold "
        "(automatic unless you set --threshold) are sorted and smear into long streaks. Choose what gets sorted "
        "(--select), what orders the streak (--sort_by, --order), the shortest streak (--min_run) and how much of "
        "the effect shows (--mix). Frames are processed one by one, so it's slower than most effects; for 4K "
        "footage set --max_width (e.g. 1280) to speed it up."
    )
    parser.add_argument("--threshold", type=int, default=None,
                        help="Brightness (0-255) above which pixels get sorted (or below, with --select darker). Leave "
                             "empty for AUTO: the threshold follows each frame's own brightness so about 60 percent of the "
                             "picture is sorted, and dark and bright clips both show the effect. Set a number to fix it.")
    parser.add_argument("--select", choices=SELECT, default="brighter",
                        help="Which pixels get sorted: brighter (default) or darker than the threshold.")
    parser.add_argument("--sort_by", choices=SORT_BY, default="brightness",
                        help="What orders the pixels inside a streak: brightness (default), hue, saturation, or one "
                             "colour channel (red, green, blue).")
    parser.add_argument("--order", choices=ORDER, default="ascending",
                        help="ascending (default): low values first, so streaks run up to bright. descending: the reverse.")
    parser.add_argument("--vertical", action="store_true", help="Sort along columns instead of rows.")
    parser.add_argument("--min_run", type=int, default=1,
                        help="Shortest streak that gets sorted, in pixels. Shorter runs stay as they are. Default: 1 (sort "
                             "everything picked). Try 8-30 to keep only the long streaks.")
    parser.add_argument("--mix", type=float, default=1.0,
                        help="Blend the sorted picture with the original: 1.0 = fully sorted (default), 0.5 = half-way.")
    parser.add_argument("--max_width", type=int, default=0,
                        help="Sort at this width if the video is wider (0 = off, the default), then scale the result back up "
                             "to the original size. Use e.g. 1280 to speed up 4K footage.")


def run(args):
    fixed = None if args.threshold is None else max(0, min(255, args.threshold))
    darker = args.select == "darker"
    # The percentile that leaves about AUTO_SHARE of the picture on the sorted side of the threshold.
    pct = 100 * AUTO_SHARE if darker else 100 * (1 - AUTO_SHARE)
    mix = max(0.0, min(1.0, args.mix))
    min_run = max(1, args.min_run)

    smooth = {"v": None}

    def frame_fn(frame, i, t):
        th = fixed
        if fixed is None:
            # Eased over time so the streaks don't flicker from frame to frame.
            target = float(np.percentile(frame[::4, ::4, :3].mean(axis=2), pct))
            smooth["v"] = target if smooth["v"] is None else 0.9 * smooth["v"] + 0.1 * target
            th = int(smooth["v"])
        return pixel_sort_frame(frame, th, args.vertical, sort_by=args.sort_by, descending=args.order == "descending",
                                select=args.select, min_run=min_run, mix=mix)

    stats = process_video(args.input, args.output, frame_fn, force=bool(getattr(args, "force", False)),
                          max_width=args.max_width or None)
    print(f"✅ Sorted {stats['frames']} frames in {stats['seconds']:.1f}s")
