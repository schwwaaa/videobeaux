"""
sharpen: crisps up soft footage. Unsharp masking (ffmpeg's unsharp) lifts the edges by a set amount, over a chosen
detail size; the cas mode (contrast-adaptive sharpening) adds detail where the picture is flat and leaves the edges
alone. Colour is left untouched and the audio is copied unchanged.
"""
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

MODES = ["unsharp", "cas"]

GUI_METADATA = {
    'args': {
        'mode': {'label': 'Method',
                 'help': 'unsharp = classic edge sharpening. cas = contrast-adaptive: sharpens the soft areas and leaves '
                         'already-crisp edges alone, so it adds less halo.'},
        'amount': {'label': 'Amount', 'min': 0, 'max': 3, 'good_min': 0.3, 'good_max': 1.5,
                   'help': '0 = none. Around 0.5 is subtle; above 1.5 halos show around edges.'},
        'radius': {'label': 'Detail size (px)', 'min': 3, 'max': 13, 'good_min': 3, 'good_max': 7,
                   'help': 'Size of the detail being sharpened (unsharp only). Small = fine edges, large = broader ones. Odd numbers.'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Sharpen: crisp up soft footage. unsharp lifts edges over a chosen detail size; cas adds detail where the "
        "picture is soft and leaves crisp edges alone. Colour is not changed."
    )
    parser.add_argument("--mode", choices=MODES, default="unsharp",
                        help="unsharp (default) = classic edge sharpening; cas = contrast-adaptive, less halo.")
    parser.add_argument("--amount", type=float, default=0.8,
                        help="How much to sharpen, 0-3. Around 0.5 is subtle, above 1.5 gives visible halos. Default: 0.8.")
    parser.add_argument("--radius", type=int, default=5,
                        help="Detail size in pixels for unsharp, 3-13 (odd). Default: 5.")


def run(args):
    amount = max(0.0, min(3.0, float(args.amount)))
    if args.mode == "cas":
        vf = f"cas=strength={min(1.0, amount * 0.5):.3f}"
    else:
        radius = max(3, min(13, int(args.radius)))
        if radius % 2 == 0:
            radius += 1
        # chroma is left alone (amount 0): sharpening colour only adds coloured halos
        vf = (f"unsharp=luma_msize_x={radius}:luma_msize_y={radius}:luma_amount={amount:.3f}:"
              "chroma_msize_x=3:chroma_msize_y=3:chroma_amount=0")
    cmd = ["ffmpeg", "-hide_banner", "-i", args.input,
           "-vf", vf,
           "-map", "0:v", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-map", "0:a?", "-c:a", "copy", "-movflags", "+faststart"]
    if getattr(args, "force", False):
        cmd.insert(1, "-y")
    cmd.append(str(args.output))
    run_ffmpeg_with_progress(cmd, args.input, args.output)
