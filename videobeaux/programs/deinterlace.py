"""
deinterlace: turns interlaced footage (the comb-teeth lines on old camcorder and broadcast video) into clean
progressive frames, with yadif or bwdif. The video is re-encoded; the audio is copied unchanged.
"""
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

METHODS = ["yadif", "bwdif"]

GUI_METADATA = {
    'args': {
        'method': {'label': 'Method',
                   'help': 'yadif is quick and reliable. bwdif keeps a little more fine detail, but is slower.'},
        'double': {'label': 'One frame per field (double rate)',
                   'help': 'Doubles the frame rate so every field becomes a frame: the smoothest motion. Off = one frame per frame.'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Deinterlace: turn interlaced footage (the comb lines on camcorder and broadcast video) into clean progressive "
        "frames. yadif or bwdif. Use --double to keep every field as its own frame (double frame rate)."
    )
    parser.add_argument("--method", choices=METHODS, default="yadif",
                        help="yadif (default) is quick and reliable; bwdif keeps a little more detail but is slower.")
    parser.add_argument("--double", action="store_true",
                        help="One output frame per field: doubles the frame rate for the smoothest motion.")


def run(args):
    mode = 1 if args.double else 0
    cmd = ["ffmpeg", "-hide_banner", "-i", args.input,
           "-vf", f"{args.method}=mode={mode}",
           "-map", "0:v", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-map", "0:a?", "-c:a", "copy", "-movflags", "+faststart"]
    if getattr(args, "force", False):
        cmd.insert(1, "-y")
    cmd.append(str(args.output))
    run_ffmpeg_with_progress(cmd, args.input, args.output)
