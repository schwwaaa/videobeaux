from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.preset_filter import add_amount_argument, apply_amount, AMOUNT_METADATA

GUI_METADATA = AMOUNT_METADATA

def register_arguments(parser):
    parser.description = (
        "Amplifies visual features or distortions for a spiritual-esque experience."
    )
    add_amount_argument(parser)

    
def run(args):
    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", "[0:v]tpad=start=8:start_mode=clone:stop=9:stop_mode=clone,amplify=radius=8:factor=4,colorbalance[out_v]",
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
