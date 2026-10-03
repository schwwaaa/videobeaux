"""
ordered_dither — ordered / noise dithering with selectable patterns (numpy).

Things ffmpeg's paletteuse can't do: Bayer matrices of different sizes,
clustered-dot (halftone-like), blue noise, interleaved-gradient noise, white
noise, and an --animate mode where the pattern changes every frame for a
boiling, flickering look. Quantizes to a named/custom palette, or posterizes
each channel to N levels.
"""
from videobeaux.utils.dither_core import METHODS, dither_frame
from videobeaux.utils.frame_pipe import process_video
from videobeaux.utils.palettes import PALETTE_CHOICES, resolve_palette, to_array

PALETTE_OPTIONS = ["levels"] + PALETTE_CHOICES

GUI_METADATA = {
    'args': {
        'method': {'type': 'select', 'label': 'Pattern', 'default': 'bayer8', 'choices': METHODS,
                   'help': 'bayerN = classic ordered grid, clustered = halftone-like dots, blue_noise / ign = smooth film-like noise, white_noise = harsh static.'},
        'palette': {'type': 'select', 'label': 'Palette', 'default': 'levels', 'choices': PALETTE_OPTIONS,
                    'help': "'levels' posterizes each color channel to N steps; others snap to a named palette."},
        'custom_colors': {'label': 'Custom colors',
                          'help': "Comma-separated hex colors for the 'custom' palette."},
    }
}


def register_arguments(parser):
    parser.description = (
        "Ordered/noise dithering: Bayer, clustered-dot, blue-noise and static patterns onto a "
        "palette or posterized colors, with an optional animated pattern. Per-frame processing — "
        "slower than the ffmpeg-based dither modes."
    )
    parser.add_argument("--method", choices=METHODS, default="bayer8",
                        help="Threshold pattern. Default: bayer8.")
    parser.add_argument("--palette", choices=PALETTE_OPTIONS, default="levels",
                        help="'levels' (per-channel posterize) or a palette name. Default: levels.")
    parser.add_argument("--custom_colors", type=str, default=None,
                        help="Hex colors for --palette custom, comma-separated.")
    parser.add_argument("--levels", type=int, default=2,
                        help="Steps per color channel when --palette levels (2 = 8 colors). Default: 2.")
    parser.add_argument("--strength", type=float, default=1.0,
                        help="Dither amount: 0 = hard quantize, 1 = full, >1 = noisier. Default: 1.")
    parser.add_argument("--pixel_size", type=int, default=2,
                        help="Dither at 1/N resolution and scale up for chunky pixels. Default: 2.")
    parser.add_argument("--animate", action="store_true",
                        help="Change the pattern every frame (boiling/flicker look).")
    parser.add_argument("--crf", type=int, default=14,
                        help="x264 quality (lower = better). Default: 14.")


def run(args):
    palette = None
    if args.palette != "levels":
        try:
            palette = to_array(resolve_palette(args.palette, args.custom_colors))
        except ValueError as e:
            raise SystemExit(f"❌ {e}")

    def frame_fn(frame, i, t):
        return dither_frame(frame, method=args.method, palette=palette,
                            levels=max(2, args.levels), strength=args.strength,
                            pixel_size=args.pixel_size, frame_index=i, animate=args.animate)

    stats = process_video(args.input, args.output, frame_fn, crf=args.crf, force=bool(args.force))
    print(f"✅ Dithered {stats['frames']} frames in {stats['seconds']:.1f}s")
