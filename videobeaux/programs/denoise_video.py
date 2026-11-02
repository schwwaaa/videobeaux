"""
denoise_video: softens the grain and speckle of noisy footage (low light, high ISO) while keeping edges. Uses ffmpeg's
hqdn3d, which smooths within each frame (spatial) and across frames (temporal). The audio is copied unchanged.
"""
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

# hqdn3d settings: luma spatial, chroma spatial, luma temporal, chroma temporal.
STRENGTHS = {
    "light": (2.0, 1.5, 3.0, 2.25),
    "medium": (4.0, 3.0, 6.0, 4.5),
    "strong": (8.0, 6.0, 12.0, 9.0),
}

GUI_METADATA = {
    'args': {
        'strength': {'label': 'Strength',
                     'help': 'light keeps most of the detail. strong smooths a lot and can look painterly.'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Denoise: soften the grain and speckle of noisy footage (low light, high ISO) while keeping the edges, by "
        "smoothing within each frame and across frames."
    )
    parser.add_argument("--strength", choices=list(STRENGTHS), default="medium",
                        help="light keeps most detail; strong smooths a lot. Default: medium.")


def run(args):
    luma_s, chroma_s, luma_t, chroma_t = STRENGTHS[args.strength]
    cmd = ["ffmpeg", "-hide_banner", "-i", args.input,
           "-vf", f"hqdn3d={luma_s}:{chroma_s}:{luma_t}:{chroma_t}",
           "-map", "0:v", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-map", "0:a?", "-c:a", "copy", "-movflags", "+faststart"]
    if getattr(args, "force", False):
        cmd.insert(1, "-y")
    cmd.append(str(args.output))
    run_ffmpeg_with_progress(cmd, args.input, args.output)
