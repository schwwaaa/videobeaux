"""
ken_burns: a slow push-in (or pull-out) across the whole clip, like a camera dolly moving over a still photo. The zoom
changes in a straight line from the start zoom to the end zoom and closes in on the focus point you choose.
Pure ffmpeg (zoompan). The video is re-encoded; the audio is copied unchanged.
"""
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.frame_pipe import probe_video

GUI_METADATA = {
    'args': {
        'start_zoom': {'label': 'Start zoom', 'min': 1, 'max': 4, 'good_min': 1, 'good_max': 2,
                       'help': 'Zoom at the first frame. 1 = the whole picture.'},
        'end_zoom': {'label': 'End zoom', 'min': 1, 'max': 4, 'good_min': 1, 'good_max': 2,
                     'help': 'Zoom at the last frame. Bigger than the start zooms in; smaller pulls out.'},
        'focus_x': {'label': 'Focus across (0 left, 1 right)', 'min': 0, 'max': 1, 'good_min': 0, 'good_max': 1,
                    'help': 'The point the zoom closes in on, horizontally. 0.5 = the middle.'},
        'focus_y': {'label': 'Focus down (0 top, 1 bottom)', 'min': 0, 'max': 1, 'good_min': 0, 'good_max': 1,
                    'help': 'The point the zoom closes in on, vertically. 0.5 = the middle.'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Ken Burns: a slow push-in (or pull-out) across the whole clip. The zoom moves evenly from the start zoom to "
        "the end zoom and closes in on the focus point. Works on a still picture made into a clip as well as on footage."
    )
    parser.add_argument("--start_zoom", type=float, default=1.0,
                        help="Zoom at the first frame; 1 = the whole picture. Default: 1.0.")
    parser.add_argument("--end_zoom", type=float, default=1.3,
                        help="Zoom at the last frame. Default: 1.3. Set it below the start zoom to pull out.")
    parser.add_argument("--focus_x", type=float, default=0.5,
                        help="Horizontal focus, 0 (left) to 1 (right). Default: 0.5.")
    parser.add_argument("--focus_y", type=float, default=0.5,
                        help="Vertical focus, 0 (top) to 1 (bottom). Default: 0.5.")


def run(args):
    start, end = float(args.start_zoom), float(args.end_zoom)
    if start < 1 or end < 1:
        raise SystemExit("❌ Zoom must be 1 or more (1 = the whole picture).")
    fx = max(0.0, min(1.0, args.focus_x))
    fy = max(0.0, min(1.0, args.focus_y))
    info = probe_video(args.input)
    if info.frames < 2:
        raise SystemExit("❌ The clip is too short to zoom across.")
    width = info.width - info.width % 2
    height = info.height - info.height % 2
    last = info.frames - 1
    # zoompan works per frame: `on` is the frame number, so the zoom runs from start (frame 0) to end (last frame).
    zoom = f"{start:.4f}+({end:.4f}-{start:.4f})*on/{last}"
    x = f"(iw-iw/zoom)*{fx:.4f}"
    y = f"(ih-ih/zoom)*{fy:.4f}"
    graph = (f"[0:v]zoompan=z='{zoom}':x='{x}':y='{y}':d=1:s={width}x{height}:fps={info.fps:.6f},"
             "format=yuv420p[v]")
    cmd = ["ffmpeg", "-hide_banner", "-i", args.input, "-filter_complex", graph,
           "-map", "[v]", "-map", "0:a?",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "copy", "-movflags", "+faststart"]
    if getattr(args, "force", False):
        cmd.insert(1, "-y")
    cmd.append(str(args.output))
    run_ffmpeg_with_progress(cmd, args.input, args.output)
