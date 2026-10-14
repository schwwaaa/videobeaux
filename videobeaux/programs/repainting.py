from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.preset_filter import add_amount_argument, apply_amount, AMOUNT_METADATA

GUI_METADATA = AMOUNT_METADATA

def register_arguments(parser):
    parser.description = (
        "Akin to repainting the same image while smudged with alcohol."
    )
    add_amount_argument(parser)

def run(args):

    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", "[0:v]median=radius=127:radiusV=15:percentile=0.43[3];[0:v]tmix=frames=20:weights=1 2 3 -2 1 2 3 -2 1 -4 4 2 3 -2 1 2 3 -2 1 1[7];[3][7]mix,lagfun=decay=1[out_v]",
        "-map", "[out_v]",
        "-map", "0:a?",
        args.output
    ]
    command = apply_amount(command, getattr(args, "amount", 1.0))

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)