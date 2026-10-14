from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.preset_filter import add_amount_argument, apply_amount, AMOUNT_METADATA

GUI_METADATA = AMOUNT_METADATA

def register_arguments(parser):
    parser.description = (
        "Apply a frame stutter and exposing the video like the file is corrupted."
    )
    add_amount_argument(parser)

def run(args):

    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", "[0:v]tblend=c0_mode=or:c1_mode=freeze:c2_mode=negation:c3_mode=geometric:all_mode=vividlight,random=frames=2,lagfun[out_v]", 
        "-map", "[out_v]",
        "-map", "0:a?",
        args.output
    ]
    command = apply_amount(command, getattr(args, "amount", 1.0))

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)