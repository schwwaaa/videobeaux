from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.preset_filter import add_amount_argument, apply_amount, AMOUNT_METADATA

GUI_METADATA = AMOUNT_METADATA

def register_arguments(parser):
    parser.description = (
            "Harsh blend-mode contrast corruption — hard-mix, vivid-light and exclusion blends over a softened copy."
    )
    add_amount_argument(parser)

def run(args):
    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", "[0:v]unsharp=luma_msize_x=9:lx=11:luma_amount=-0.26,tblend=c0_mode=reflect:c1_mode=hardmix:c2_mode=vividlight:c3_mode=exclusion:all_mode=grainmerge[out_v]",
        "-map", "[out_v]",
        "-map", "0:a?",
        args.output
    ]
    command = apply_amount(command, getattr(args, "amount", 1.0))
    
    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
