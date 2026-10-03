"""
retro_dither — dithering onto a fixed, named palette (pure ffmpeg).

Unlike `dither` (which picks colors from the footage), this forces every pixel
onto a classic fixed palette — 1-bit black & white, Game Boy greens, CGA, EGA,
C64, PICO-8, phosphor monitors — or your own hex list, using ffmpeg's
paletteuse dithering algorithms.
"""
import tempfile
from pathlib import Path

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.frame_pipe import probe_video
from videobeaux.utils.palettes import PALETTE_CHOICES, resolve_palette, write_palette_png

ALGORITHMS = ["floyd_steinberg", "atkinson", "sierra2", "sierra2_4a", "sierra3",
              "burkes", "heckbert", "bayer"]

GUI_METADATA = {
    'args': {
        'palette': {'type': 'select', 'label': 'Palette', 'default': 'bw', 'choices': PALETTE_CHOICES,
                    'help': "Pick a classic palette, or 'custom' to use the hex list below."},
        'custom_colors': {'label': 'Custom colors',
                          'help': "Comma-separated hex colors for the 'custom' palette, e.g. #000000, #ff6847, #ffffff."},
        'algorithm': {'type': 'select', 'label': 'Algorithm', 'default': 'floyd_steinberg',
                      'choices': ALGORITHMS},
    }
}


def register_arguments(parser):
    parser.description = (
        "Dither onto a fixed palette: 1-bit B&W, Game Boy, CGA, EGA, C64, PICO-8, phosphor "
        "monitors, or your own colors. Tweak Contrast/Brightness first for best 1-bit results."
    )
    parser.add_argument("--palette", choices=PALETTE_CHOICES, default="bw",
                        help="Palette to use. Default: bw (1-bit black & white).")
    parser.add_argument("--custom_colors", type=str, default=None,
                        help="Hex colors for --palette custom, comma-separated (e.g. '#000000, #ff6847, #ffffff').")
    parser.add_argument("--algorithm", choices=ALGORITHMS, default="floyd_steinberg",
                        help="Dithering algorithm. Default: floyd_steinberg.")
    parser.add_argument("--bayer_scale", type=int, default=3,
                        help="Bayer pattern strength 0-5 (only with the bayer algorithm). Default: 3.")
    parser.add_argument("--pixel_size", type=int, default=2,
                        help="Dither at 1/N resolution and scale up for chunky pixels (1 = full resolution). Default: 2.")
    parser.add_argument("--contrast", type=float, default=1.2,
                        help="Contrast before dithering (1.0 = unchanged). Default: 1.2.")
    parser.add_argument("--brightness", type=float, default=0.0,
                        help="Brightness before dithering, -1 to 1. Default: 0.")
    parser.add_argument("--crf", type=int, default=14,
                        help="x264 quality (lower = better). Default: 14.")


def run(args):
    try:
        colors = resolve_palette(args.palette, args.custom_colors)
    except ValueError as e:
        raise SystemExit(f"❌ {e}")

    p = max(1, args.pixel_size)
    info = probe_video(args.input)
    W, H = info.width - info.width % 2, info.height - info.height % 2
    small_w, small_h = max(2, (W // p) // 2 * 2), max(2, (H // p) // 2 * 2)

    pre = f"scale={small_w}:{small_h}:flags=area," if p > 1 else f"crop={W}:{H}:0:0,"
    eq = f"eq=contrast={args.contrast}:brightness={args.brightness},format=rgb24"
    opts = f"dither={args.algorithm}"
    if args.algorithm == "bayer":
        opts += f":bayer_scale={max(0, min(5, args.bayer_scale))}"
    post = f"scale={W}:{H}:flags=neighbor," if p > 1 else ""

    with tempfile.TemporaryDirectory(prefix="videobeaux_retro_") as tmp:
        pal = write_palette_png(colors, Path(tmp) / "palette.png")
        fc = (f"[0:v]{pre}{eq}[x];[x][1:v]paletteuse={opts}[q];[q]{post}format=yuv420p[out_v]")
        cmd = ["ffmpeg", *(["-y"] if args.force else []), "-i", args.input, "-i", str(pal),
               "-filter_complex", fc, "-map", "[out_v]", "-map", "0:a?",
               "-c:v", "libx264", "-preset", "medium", "-crf", str(args.crf),
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart", args.output]
        run_ffmpeg_with_progress(cmd, args.input, args.output)
