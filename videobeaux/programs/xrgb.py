from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.preset_filter import add_amount_argument, apply_amount, AMOUNT_METADATA

GUI_METADATA = AMOUNT_METADATA

def register_arguments(parser):
    parser.description = (
        "Extreme RGB adjustment."
    )
    add_amount_argument(parser)

def run(args):

    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", "[0:v]rgbashift=rh=185:rv=160:gh=-1:gv=6:bh=-6:bv=6:ah=-6:av=179,rgbashift=rh=2:rv=27:gh=48:gv=102:bh=3:bv=3:ah=-3:av=2,rgbashift=rh=6:rv=-6:gh=6:gv=-148:bh=16:bv=33:ah=-33:av=-9,rgbashift=rh=10:rv=202:gh=-151,rgbashift=rh=-31:rv=-30:gh=30:gv=-41:bh=78[out_v]",
        "-map", "[out_v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-profile:v", "main",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        args.output
    ]
    command = apply_amount(command, getattr(args, "amount", 1.0))

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)

