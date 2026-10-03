"""
dither — adaptive-palette dithering (pure ffmpeg).

Reduces the video to N colors chosen from the footage itself (palettegen), then
re-renders it through one of ffmpeg's paletteuse dithering algorithms — the same
machinery as GIF encoding, applied as a look. --pixel_size makes the dither
chunky (quantize at reduced resolution, scale back up with nearest-neighbor),
which is what makes it read as dithering and also survives h264 compression.
"""
import subprocess
import tempfile
from pathlib import Path

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.frame_pipe import probe_video

ALGORITHMS = ["floyd_steinberg", "atkinson", "sierra2", "sierra2_4a", "sierra3",
              "burkes", "heckbert", "bayer"]

GUI_METADATA = {
    'args': {
        'algorithm': {'type': 'select', 'label': 'Algorithm', 'default': 'floyd_steinberg',
                      'choices': ALGORITHMS,
                      'help': 'Error-diffusion (floyd_steinberg, atkinson, sierra*, burkes, heckbert) or ordered (bayer).'},
        'palette_scope': {'type': 'select', 'label': 'Palette', 'default': 'global',
                          'choices': ['global', 'per_frame'],
                          'help': "global = one palette for the whole clip (stable). per_frame = a new palette every frame (shimmers)."},
    }
}


def register_arguments(parser):
    parser.description = (
        "Adaptive-palette dithering: reduce the video to N colors picked from the footage and "
        "re-render it with a dithering algorithm. Use Pixel Size for chunky, retro dither."
    )
    parser.add_argument("--algorithm", choices=ALGORITHMS, default="floyd_steinberg",
                        help="Dithering algorithm. Default: floyd_steinberg.")
    parser.add_argument("--colors", type=int, default=16,
                        help="Number of palette colors (2-256). Default: 16.")
    parser.add_argument("--bayer_scale", type=int, default=3,
                        help="Bayer pattern strength 0-5 (only used with the bayer algorithm). Default: 3.")
    parser.add_argument("--palette_scope", choices=["global", "per_frame"], default="global",
                        help="One palette for the whole clip, or a new one per frame. Default: global.")
    parser.add_argument("--pixel_size", type=int, default=2,
                        help="Dither at 1/N resolution and scale up for chunky pixels (1 = full resolution). Default: 2.")
    parser.add_argument("--crf", type=int, default=14,
                        help="x264 quality (lower = better). Dither patterns need a low CRF to survive compression. Default: 14.")


def _paletteuse(args):
    opts = f"dither={args.algorithm}"
    if args.algorithm == "bayer":
        opts += f":bayer_scale={max(0, min(5, args.bayer_scale))}"
    return opts


def run(args):
    colors = max(2, min(256, args.colors))
    p = max(1, args.pixel_size)
    info = probe_video(args.input)
    W, H = info.width - info.width % 2, info.height - info.height % 2
    small_w, small_h = max(2, (W // p) // 2 * 2), max(2, (H // p) // 2 * 2)

    pre = f"scale={small_w}:{small_h}:flags=area," if p > 1 else ""
    post = f"scale={W}:{H}:flags=neighbor," if p > 1 else f"crop={W}:{H}:0:0,"
    out_args = ["-c:v", "libx264", "-preset", "medium", "-crf", str(args.crf),
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart", args.output]
    force = ["-y"] if args.force else []

    if args.palette_scope == "per_frame":
        fc = (f"[0:v]{pre}split[a][b];[a]palettegen=max_colors={colors}:stats_mode=single[pal];"
              f"[b][pal]paletteuse={_paletteuse(args)}:new=1[q];[q]{post}format=yuv420p[out_v]")
        cmd = ["ffmpeg", *force, "-i", args.input, "-filter_complex", fc,
               "-map", "[out_v]", "-map", "0:a?", *out_args]
        run_ffmpeg_with_progress(cmd, args.input, args.output)
        return

    # global palette: analyze first (a split would buffer the whole video in memory)
    with tempfile.TemporaryDirectory(prefix="videobeaux_dither_") as tmp:
        pal = Path(tmp) / "palette.png"
        print(f"🎨 Building a {colors}-color palette…", flush=True)
        r = subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", args.input, "-vf",
             f"{pre}palettegen=max_colors={colors}:stats_mode=full", "-frames:v", "1", str(pal)],
            capture_output=True, text=True)
        if r.returncode != 0 or not pal.exists():
            raise RuntimeError(f"❌ palette generation failed:\n{r.stderr.strip()[-400:]}")
        fc = (f"[0:v]{pre.rstrip(',')}[x];[x][1:v]paletteuse={_paletteuse(args)}[q];"
              f"[q]{post}format=yuv420p[out_v]") if pre else \
             (f"[0:v][1:v]paletteuse={_paletteuse(args)}[q];[q]{post}format=yuv420p[out_v]")
        cmd = ["ffmpeg", *force, "-i", args.input, "-i", str(pal), "-filter_complex", fc,
               "-map", "[out_v]", "-map", "0:a?", *out_args]
        run_ffmpeg_with_progress(cmd, args.input, args.output)
