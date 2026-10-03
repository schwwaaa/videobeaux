from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.programs.kinetic_captions import _hex_to_rgba

GUI_METADATA = {
    'args': {
        'shadow_color': {'type': 'color'},
        'highlight_color': {'type': 'color'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Maps luminance to a 2-color gradient (duotone) — a popular stylized-poster "
        "look. Shadows map to one color, highlights to another."
    )
    parser.add_argument("--shadow_color", default="#1a0038", help="Color for the darkest areas. Default: #1a0038.")
    parser.add_argument("--highlight_color", default="#ffcc00", help="Color for the brightest areas. Default: #ffcc00.")


def run(args):
    sr, sg, sb, _ = _hex_to_rgba(args.shadow_color)
    hr, hg, hb, _ = _hex_to_rgba(args.highlight_color)

    # geq's r(x,y)/g(x,y)/b(x,y) input-sampling functions are the only ones
    # valid inside RGB-mode geq expressions (r/g/b) — lum(x,y) is a
    # YUV-mode-only sampler and errors here, so luminance is approximated
    # from the sampled R/G/B channels directly.
    lum = "(0.299*r(X\\,Y)+0.587*g(X\\,Y)+0.114*b(X\\,Y))"
    r_expr = f"{sr}+({lum}/255)*({hr}-{sr})"
    g_expr = f"{sg}+({lum}/255)*({hg}-{sg})"
    b_expr = f"{sb}+({lum}/255)*({hb}-{sb})"

    filter_complex = f"[0:v]geq=r='{r_expr}':g='{g_expr}':b='{b_expr}'[out_v]"
    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", filter_complex,
        "-map", "[out_v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        args.output,
    ]
    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
