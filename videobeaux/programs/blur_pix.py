from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.preset_filter import add_amount_argument, apply_amount, AMOUNT_METADATA

GUI_METADATA = AMOUNT_METADATA

def register_arguments(parser):
    parser.description = (
            "Applies a double-layered blur and pixelation combined effect."
    )
    add_amount_argument(parser)


def run(args):
    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", "[0:v]pixelize=width=1:w=9:height=1:h=1,lagfun=decay=0.97:planes=1,tmix=frames=19,chromashift=cbh=-152:cbv=95:crh=-79:crv=142:edge=wrap[out_v]", 
        "-map", "[out_v]",
        "-map", "0:a?",
        args.output
    ]
    command = apply_amount(command, getattr(args, "amount", 1.0))
    
    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
