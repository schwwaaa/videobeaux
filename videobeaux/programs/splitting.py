from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.preset_filter import add_amount_argument, apply_amount, AMOUNT_METADATA

GUI_METADATA = AMOUNT_METADATA

def register_arguments(parser):
    parser.description = (
        "Rearranges pixels vertically and inversely. Looks kind of like a damaged tape."
    )
    add_amount_argument(parser)

def run(args):

    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", "[0:v]shuffleplanes,shufflepixels=direction=inverse:m=vertical:width=157[2];[0:v][2]mix[out_v]",
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
