from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.preset_filter import add_amount_argument, apply_amount, AMOUNT_METADATA

GUI_METADATA = AMOUNT_METADATA

def register_arguments(parser):
   parser.description = (
            "introduces uneven timing to simulate poorly animated sequences."
    )
   add_amount_argument(parser)

def run(args):
    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", "[0:v]detelecine=first_field=bottom:pattern=5:start_frame=4[out_v]",
        "-map", "[out_v]",
        "-map", "0:a?",
        args.output
    ]
    command = apply_amount(command, getattr(args, "amount", 1.0))

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
