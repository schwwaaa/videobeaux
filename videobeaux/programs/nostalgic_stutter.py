from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.preset_filter import add_amount_argument, apply_amount, AMOUNT_METADATA

GUI_METADATA = AMOUNT_METADATA

def register_arguments(parser):
    parser.description = (
        "Apply frame stutter akin to a corrupted file."
    )
    add_amount_argument(parser)

def run(args):

    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", "[0:v]random=frames=2:seed=212[1];[0:v]tmix=frames=3:weights=1 2 1 -3[4];[1]chromashift=cbh=192:cbv=-97:crh=-76:crv=81:edge=wrap,random=frames=2:seed=243[3];[4][3][0:v]mix=inputs=3:weights=2 1 1 [out_v]", 
        "-map", "[out_v]",
        "-map", "0:a?",
        args.output
    ]
    command = apply_amount(command, getattr(args, "amount", 1.0))

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)