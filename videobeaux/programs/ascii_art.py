"""
ascii_art — rebuild the video out of text characters (OpenCV, fully offline).

Each block of the picture is replaced by a character whose ink density matches its brightness.
Characters are drawn from a pre-rendered glyph atlas (OpenCV's built-in Hershey font, no font
files needed), so it runs at video speed. Choose a character set, colour style, size, and an
edge boost that makes outlines stand out.
"""
import numpy as np

from videobeaux.utils.cv import hex_to_rgb, require_cv2
from videobeaux.utils.frame_pipe import process_video

RAMPS = {
    "classic":  " .,:;i1tfLCG08@",
    "detailed": " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
    "simple":   " .:-=+*#%@",
    "dots":     " .:oO0@",
    "binary":   " 01",
    "blocks":   "blocks",       # density patterns instead of letters
    "custom":   "custom",
}
COLOR_MODES = ["source colors", "mono", "matrix green", "amber terminal"]

GUI_METADATA = {
    'args': {
        'charset': {'type': 'select', 'label': 'Characters', 'default': 'classic', 'choices': list(RAMPS),
                    'help': 'Which characters build the picture. "blocks" uses shaded squares; "custom" uses the text below.'},
        'custom_chars': {'type': 'text', 'label': 'Custom characters',
                         'help': 'Used when Characters = custom. Order doesn\'t matter — they\'re sorted by how much ink each uses.'},
        'color_mode': {'type': 'select', 'label': 'Color', 'default': 'source colors', 'choices': COLOR_MODES},
        'fg_color': {'type': 'color', 'label': 'Text color (mono)', 'default': '#FFFFFF'},
        'bg_color': {'type': 'color', 'label': 'Background (mono)', 'default': '#000000'},
        'columns': {'label': 'Characters across', 'min': 20, 'max': 400,
                    'help': 'More = finer detail, smaller characters.'},
        'edges': {'label': 'Edge boost', 'min': 0, 'max': 1, 'help': 'Makes outlines pop (0 = off).'},
    }
}


def register_arguments(parser):
    parser.description = (
        "ASCII art video: replaces each block of the picture with a text character matching its "
        "brightness. Pick a character set, colors (source / mono / matrix green / amber), size and "
        "an edge boost."
    )
    parser.add_argument("--charset", choices=list(RAMPS), default="classic", help="Character set. Default: classic.")
    parser.add_argument("--custom_chars", type=str, default="", help="Characters to use with --charset custom.")
    parser.add_argument("--color_mode", choices=COLOR_MODES, default="source colors", help="Color style.")
    parser.add_argument("--fg_color", type=str, default="#FFFFFF", help="Text color for mono. Default: #FFFFFF.")
    parser.add_argument("--bg_color", type=str, default="#000000", help="Background color for mono. Default: #000000.")
    parser.add_argument("--columns", type=int, default=110, help="Characters across the frame. Default: 110.")
    parser.add_argument("--edges", type=float, default=0.0, help="Edge boost 0-1. Default: 0.")
    parser.add_argument("--invert", action="store_true", help="Flip the brightness mapping: dark areas get the dense characters (pair with a light background color in mono mode).")
    parser.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def build_atlas(cv2, chars: str, cw: int, ch: int) -> np.ndarray:
    """(N, ch, cw) float32 ink coverage per character, sorted light → dense."""
    tiles = []
    if chars == "blocks":
        yy, xx = np.mgrid[0:ch, 0:cw]
        checker = ((xx + yy) % 2).astype(np.float32)
        dots = ((xx % 2 == 0) & (yy % 2 == 0)).astype(np.float32)
        tiles = [np.zeros((ch, cw), np.float32), dots, checker,
                 np.clip(checker + dots, 0, 1), np.ones((ch, cw), np.float32)]
    else:
        font = cv2.FONT_HERSHEY_SIMPLEX
        (bw, bh), base = cv2.getTextSize("M", font, 1.0, 1)
        scale = min(ch * 0.78 / max(bh, 1), cw * 0.95 / max(bw, 1))
        thick = 1 if ch < 28 else 2
        for c in dict.fromkeys(chars):          # unique, order kept
            t = np.zeros((ch, cw), np.uint8)
            if c != " ":
                (tw, th), _ = cv2.getTextSize(c, font, scale, thick)
                cv2.putText(t, c, (max(0, (cw - tw) // 2), (ch + th) // 2), font, scale, 255, thick, cv2.LINE_AA)
            tiles.append(t.astype(np.float32) / 255.0)
    atlas = np.array(tiles, np.float32)
    atlas = atlas[np.argsort(atlas.reshape(len(atlas), -1).mean(axis=1), kind="stable")]
    peak = float(atlas.max()) or 1.0
    return atlas / peak


def run(args):
    cv2 = require_cv2()
    chars = RAMPS[args.charset]
    if args.charset == "custom":
        chars = " " + (args.custom_chars or "")
        if len(chars.strip()) < 1:
            raise SystemExit("❌ Characters = custom needs some characters in 'Custom characters'.")
    mode = args.color_mode
    fg = np.array(hex_to_rgb(args.fg_color, (255, 255, 255)), np.float32)
    bg = np.array(hex_to_rgb(args.bg_color, (0, 0, 0)), np.float32)
    if mode == "matrix green":
        fg, bg = np.array([0, 255, 65], np.float32), np.array([0, 10, 0], np.float32)
    elif mode == "amber terminal":
        fg, bg = np.array([255, 176, 0], np.float32), np.array([18, 8, 0], np.float32)
    edges_amt = min(1.0, max(0.0, args.edges))

    st = {}

    def setup(info):
        cols = max(10, args.columns)
        cw = max(3, int(round(info.width / cols)))
        ch = int(round(cw * 2.0))
        st.update(cw=cw, ch=ch, atlas=build_atlas(cv2, chars, cw, ch),
                  cols=-(-info.width // cw), rows=-(-info.height // ch))

    def frame_fn(frame, i, t):
        H, W = frame.shape[:2]
        cw, ch, atlas, cols, rows = st["cw"], st["ch"], st["atlas"], st["cols"], st["rows"]
        small = cv2.resize(frame, (cols, rows), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY).astype(np.float32)
        lo, hi = np.percentile(gray, (2, 98))
        gray = np.clip((gray - lo) / max(hi - lo, 1.0), 0, 1).astype(np.float32)
        if edges_amt > 0:
            gx, gy = cv2.Sobel(gray, cv2.CV_32F, 1, 0), cv2.Sobel(gray, cv2.CV_32F, 0, 1)
            mag = np.clip(cv2.magnitude(gx, gy) * 1.5, 0, 1)
            gray = np.clip(gray + mag * edges_amt, 0, 1)
        if args.invert:
            gray = 1.0 - gray
        lvl = np.minimum((gray * len(atlas)).astype(np.int32), len(atlas) - 1)
        cov = atlas[lvl].transpose(0, 2, 1, 3).reshape(rows * ch, cols * cw)[..., None]
        if mode == "source colors":
            hsv = cv2.cvtColor(small, cv2.COLOR_RGB2HSV)
            if not args.invert:
                hsv[..., 2] = 255
            hsv[..., 1] = np.minimum(255, hsv[..., 1].astype(np.int32) * 3 // 2)
            col = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB).astype(np.float32)
            col = np.repeat(np.repeat(col, ch, axis=0), cw, axis=1)
            bg_img = np.full_like(col, 255.0 if args.invert else 0.0)
        else:
            col, bg_img = fg, bg
        out = bg_img * (1.0 - cov) + col * cov
        return np.clip(out, 0, 255).astype(np.uint8)[:H, :W]

    stats = process_video(args.input, args.output, frame_fn, crf=args.crf,
                          force=bool(getattr(args, "force", False)), setup=setup)
    print(f"✅ ASCII art: {stats['frames']} frames in {stats['seconds']:.1f}s")
