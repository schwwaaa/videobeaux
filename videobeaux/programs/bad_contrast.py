from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

def register_arguments(parser):
    parser.description = (
            "Harsh blend-mode contrast corruption — hard-mix, vivid-light and exclusion blends over a softened copy."
    )
    print("✅ This program mode does not require additional arguments")

def run(args):
    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", "[0:v]unsharp=luma_msize_x=9:lx=11:luma_amount=-0.26,tblend=c0_mode=reflect:c1_mode=hardmix:c2_mode=vividlight:c3_mode=exclusion:all_mode=grainmerge[out_v]",
        "-map", "[out_v]",
        "-map", "0:a",
        args.output
    ]
    
    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
