"""
strobe_hold — a mixer-style stroboscope: show one frame and hold it for N frames (a stuttering, low-frame-rate
look), optionally blinking to a color for part of every hold, with optional random hold lengths.
"""
import random

import numpy as np

from videobeaux.utils.cv import hex_to_rgb
from videobeaux.utils.frame_pipe import process_video

GUI_METADATA = {
    'args': {
        'hold': {'label': 'Hold (frames)', 'min': 1, 'max': 60, 'help': 'Each picture is held for this many frames.'},
        'blink': {'label': 'Blink (%)', 'min': 0, 'max': 100,
                  'help': 'How much of each hold shows the blink color instead of the picture (0 = never).'},
        'blink_color': {'type': 'color', 'label': 'Blink color', 'default': '#000000'},
        'random_hold': {'label': 'Random hold', 'help': 'Hold lengths vary randomly from 1 up to Hold.'},
        'seed': {'hidden': True}, 'crf': {'hidden': True},
    }
}


def register_arguments(p):
    p.description = (
        "Stroboscope: hold each picture for N frames for a stuttering low-frame-rate look; optionally blink to a "
        "color for part of every hold, and vary the hold length randomly."
    )
    p.add_argument("--hold", type=int, default=4, help="Frames each picture is held for. Default: 4.")
    p.add_argument("--blink", type=float, default=0.0, help="Percent of each hold shown as the blink color. Default: 0.")
    p.add_argument("--blink_color", type=str, default="#000000", help="Blink color. Default: #000000.")
    p.add_argument("--random_hold", action="store_true", help="Random hold lengths, 1 to --hold frames.")
    p.add_argument("--seed", type=int, default=0, help="Seed for random holds (0 = different every run).")
    p.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def run(args):
    hold = max(1, int(args.hold))
    rng = random.Random(args.seed or None)
    color = np.array(hex_to_rgb(args.blink_color, (0, 0, 0)), np.uint8)
    blink = max(0.0, min(100.0, args.blink)) / 100.0
    st = {"frame": None, "left": 0, "len": 1, "pos": 0}

    def frame_fn(frame, i, t):
        if st["left"] <= 0:
            st["frame"] = frame.copy()
            st["len"] = rng.randint(1, hold) if args.random_hold else hold
            st["left"], st["pos"] = st["len"], 0
        st["left"] -= 1
        pos = st["pos"]
        st["pos"] += 1
        # the last `blink` fraction of each hold shows the blink color
        if blink > 0 and pos >= st["len"] * (1.0 - blink):
            out = np.empty_like(frame)
            out[:] = color
            return out
        return st["frame"]

    stats = process_video(args.input, args.output, frame_fn, crf=args.crf, force=bool(getattr(args, "force", False)))
    print(f"✅ {stats['frames']} frames in {stats['seconds']:.1f}s")
