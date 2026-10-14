from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.preset_filter import add_amount_argument, apply_amount, AMOUNT_METADATA

GUI_METADATA = AMOUNT_METADATA

def register_arguments(parser):
    parser.description = (
            "Amplified frame differences plus a slow vertical scroll — a rolling, broken-tracking look."
    )
    add_amount_argument(parser)

def run(args):
    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", "[0:v]setpts=PTS-STARTPTS,tpad=start=12:start_mode=clone:stop=12:stop_mode=clone,amplify=radius=12:factor=12:low=17213.43:high=4310.24,scroll=h=0.003:v=1:vpos=0.2,trim=start_frame=12,format=yuv420p[out_v]",
        "-map", "[out_v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-profile:v", "high",
        "-level:v", "4.2",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-movflags", "+faststart",
        "-shortest",
        args.output
    ]
    command = apply_amount(command, getattr(args, "amount", 1.0))
    # print(" ".join(f'"{arg}"' if ' ' in arg or ':' in arg or '=' in arg else arg for arg in command))
    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
