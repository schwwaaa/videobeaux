from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.preset_filter import add_amount_argument, apply_amount, AMOUNT_METADATA

GUI_METADATA = AMOUNT_METADATA

def register_arguments(parser):
    parser.description = (
        "As if the video was dipped in pickle juice."
    )
    add_amount_argument(parser)

def run(args):

    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", "[0:v]shear,vibrance=intensity=0.36:rbal=2.94:gbal=3.34:bbal=-3.83:rlum=0.41:glum=0.15:blum=0.28[out_v]",
        "-map", "[out_v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-profile:v", "high",
        "-level:v", "4.2",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        args.output
    ]
    command = apply_amount(command, getattr(args, "amount", 1.0))
    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)