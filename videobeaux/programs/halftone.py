from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress


def register_arguments(parser):
    parser.description = (
        "Newsprint-style halftone dot pattern — dot size in each cell is driven by "
        "the source's local brightness."
    )
    parser.add_argument(
        "--cell_size", type=int, default=8,
        help="Size in pixels of each dot cell. Smaller = finer detail, slower to render. Default: 8."
    )


def run(args):
    c = max(2, args.cell_size)
    half = c / 2.0
    # lum(x,y) samples the INPUT frame's luminance — valid inside geq's own
    # `lum` expression (YUV-mode geq); this is a different sampling context
    # than geq's RGB-mode r/g/b expressions, which only expose r(x,y)/g(x,y)/b(x,y).
    lum_expr = (
        f"if(lt(hypot(mod(X\\,{c})-{half}\\,mod(Y\\,{c})-{half})\\,"
        f"(255-lum(X\\,Y))/255*{half})\\,0\\,255)"
    )
    filter_complex = f"[0:v]format=gray,geq=lum='{lum_expr}'[out_v]"
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
