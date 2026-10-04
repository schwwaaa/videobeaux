"""
video_wall — repeat the picture in a grid of tiles, like a bank of monitors: straight repeats, mirrored tiles
(kaleidoscope-like seams), or a delay wall where every tile lags a little more than the one before.
"""
from collections import deque

import numpy as np

from videobeaux.utils.cv import hex_to_rgb, require_cv2
from videobeaux.utils.frame_pipe import process_video

MODES = ["repeat", "mirror tiles", "delay wall"]

GUI_METADATA = {
    'args': {
        'cols': {'label': 'Columns', 'min': 1, 'max': 12},
        'rows': {'label': 'Rows', 'min': 1, 'max': 12},
        'mode': {'type': 'select', 'label': 'Mode', 'default': MODES[0], 'choices': MODES,
                 'help': 'repeat = the same picture in every tile. mirror tiles = alternate tiles flipped so edges line up. '
                         'delay wall = each tile is a little behind the previous one.'},
        'delay': {'label': 'Delay per tile (frames)', 'min': 1, 'max': 30, 'help': 'For delay wall.'},
        'invert_alt': {'label': 'Invert every other tile'},
        'gap': {'label': 'Gap (px)', 'min': 0, 'max': 40},
        'gap_color': {'type': 'color', 'label': 'Gap color', 'default': '#000000'},
        'crf': {'hidden': True},
    }
}


def register_arguments(p):
    p.description = (
        "Video wall: the picture repeated in a grid of tiles — plain repeats, mirrored tiles, or a delay wall "
        "where every tile lags a bit more. Optional inverted checkerboard and gaps between tiles."
    )
    p.add_argument("--cols", type=int, default=3, help="Tiles across. Default: 3.")
    p.add_argument("--rows", type=int, default=3, help="Tiles down. Default: 3.")
    p.add_argument("--mode", choices=MODES, default=MODES[0], help="Tile behavior. Default: repeat.")
    p.add_argument("--delay", type=int, default=4, help="Frames of delay per tile (delay wall). Default: 4.")
    p.add_argument("--invert_alt", action="store_true", help="Invert every other tile, checkerboard style.")
    p.add_argument("--gap", type=int, default=0, help="Gap between tiles in pixels. Default: 0.")
    p.add_argument("--gap_color", type=str, default="#000000", help="Gap color. Default: #000000.")
    p.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def run(args):
    cv2 = require_cv2()
    cols, rows = max(1, args.cols), max(1, args.rows)
    gap = max(0, args.gap)
    gap_rgb = np.array(hex_to_rgb(args.gap_color, (0, 0, 0)), np.uint8)
    n = cols * rows
    st = {"hist": deque(maxlen=max(2, (n - 1) * max(1, args.delay) + 2))}

    def frame_fn(frame, i, t):
        H, W = frame.shape[:2]
        cw, ch = max(2, (W - gap * (cols - 1)) // cols), max(2, (H - gap * (rows - 1)) // rows)
        small = cv2.resize(frame, (cw, ch), interpolation=cv2.INTER_AREA)
        if args.mode == "delay wall":
            st["hist"].append(small)
        out = np.empty_like(frame)
        out[:] = gap_rgb
        for r in range(rows):
            for c in range(cols):
                k = r * cols + c
                tile = small
                if args.mode == "mirror tiles":
                    tile = small[:, ::-1] if c % 2 else small
                    tile = tile[::-1] if r % 2 else tile
                elif args.mode == "delay wall":
                    back = min(len(st["hist"]) - 1, k * max(1, args.delay))
                    tile = st["hist"][-1 - back]
                if args.invert_alt and (r + c) % 2:
                    tile = 255 - tile
                x0, y0 = c * (cw + gap), r * (ch + gap)
                out[y0:y0 + ch, x0:x0 + cw] = tile
        return out

    stats = process_video(args.input, args.output, frame_fn, crf=args.crf, force=bool(getattr(args, "force", False)))
    print(f"✅ {stats['frames']} frames in {stats['seconds']:.1f}s")
