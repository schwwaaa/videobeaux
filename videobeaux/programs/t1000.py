from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.preset_filter import add_amount_argument, apply_amount, AMOUNT_METADATA

# The two temporal medians (a 39-frame and a 19-frame window, per pixel) are by far the heaviest thing in ffmpeg's
# arsenal: about 0.7x real time at 1080p and far worse at 4K. The effect is soft by nature, so it is computed at a reduced
# size ("Working detail") and scaled back up to the original size.
GUI_METADATA = {
    'args': {
        **AMOUNT_METADATA['args'],
        'detail': {'label': 'Working detail (px)', 'min': 0, 'max': 2160, 'step': 60, 'good_min': 360, 'good_max': 1080,
                   'help': 'The effect is computed at this picture height, then scaled back up. Lower = much faster '
                           '(540 runs ≈1.5× real time on HD and 4K; full size is ≈0.7× on HD and ≈0.2× on 4K). Higher = sharper still parts.'},
    },
    'presets': {
        'Fast (360)': {'detail': 360},
        'Balanced (540)': {'detail': 540},
        'Sharper (720)': {'detail': 720},
        'Full size': {'detail': 0},
    },
}

# rgbashift offsets are in pixels of the full-size picture; scale them with the working size so the look stays the same.
_SHIFTS = dict(rh=-2, rv=2, gh=-3, gv=3, bh=-4, bv=-2, ah=-12, av=3)


def _even(n):
    n = int(round(n))
    return max(2, n - n % 2)


def register_arguments(parser):
    parser.description = (
        "As if the video surface were made of reflective mercury. \n\n"
        "       'It's just a stutter step.' \n"
        "               -Liquid T-1000          "
    )
    add_amount_argument(parser)
    parser.add_argument("--detail", type=int, default=540,
                        help="Picture height the effect is computed at, then scaled back up (0 = full size, slow). Default: 540.")


def build_graph(width, height, detail):
    """(filter graph ending in [out_v], working size or None) for a width×height picture."""
    work = None
    k = 1.0
    short = min(width, height)
    if detail and short > detail:
        k = detail / short
        work = (_even(width * k), _even(height * k))
    shifts = ":".join(f"{n}={int(round(v * k)) if abs(v * k) >= 0.5 else (1 if v > 0 else -1)}" for n, v in _SHIFTS.items())
    head = f"scale={work[0]}:{work[1]}:flags=area," if work else ""
    tail = f",scale={_even(width)}:{_even(height)}:flags=bicubic" if work else ""
    graph = (
        "[0:v]" + head +
        # Two temporal medians (windows of 39 and 19 frames) emit nothing until their window is full and don't flush at the
        # end, so the picture shrinks by 19+9 frames at each end — a clip shorter than ~57 frames came out with no video at
        # all. Clone-padding by the combined radius gives back exactly the frames that went in, in step with the original.
        "tpad=start=28:start_mode=clone:stop=28:stop_mode=clone,"
        "setrange=range=limited,tmedian=radius=19:percentile=0.47,"
        f"rgbashift={shifts},"
        "tmedian=radius=9:percentile=0.32" + tail + "[out_v]"
    )
    return graph, work


def run(args):
    from videobeaux.utils.frame_pipe import probe_video
    info = probe_video(args.input)
    graph, work = build_graph(info.width, info.height, int(getattr(args, "detail", 540) or 0))
    if work:
        print(f"Working at {work[0]}x{work[1]} (then scaled back to {info.width}x{info.height}) — "
              f"set Working detail to 0 for full size.", flush=True)

    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", graph,
        "-map", "[out_v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-profile:v", "main",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        args.output
    ]
    command = apply_amount(command, getattr(args, "amount", 1.0))

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
