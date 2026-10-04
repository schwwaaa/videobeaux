"""
picture_in_picture — a small second video inset over the main one, like a video mixer's PinP:
choose the corner (or exact spot), size, border, opacity, and whose audio you hear. Pure ffmpeg.
"""
import shutil
import tempfile
from pathlib import Path

from videobeaux.utils import audio_pick
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.frame_pipe import probe_video
from videobeaux.utils.mixer import encode_args, even, ff_color, fit_chain

POSITIONS = ["bottom right", "bottom left", "top right", "top left", "center", "custom"]

GUI_METADATA = {
    'args': {
        'input2': {'type': 'file', 'subtype': 'video', 'label': 'Inset video',
                   'help': 'The small video shown inside the main one — connect a node or pick a file. Loops if shorter.'},
        'size': {'label': 'Size (% of width)', 'min': 5, 'max': 100},
        'position': {'type': 'select', 'label': 'Position', 'default': 'bottom right', 'choices': POSITIONS},
        'margin': {'label': 'Margin (%)', 'min': 0, 'max': 30, 'help': 'Distance from the edge, as % of the width.'},
        'x': {'label': 'X (custom, %)', 'min': 0, 'max': 100, 'help': 'Used when Position = custom.'},
        'y': {'label': 'Y (custom, %)', 'min': 0, 'max': 100},
        'border': {'label': 'Border (px)', 'min': 0, 'max': 40},
        'border_color': {'type': 'color', 'label': 'Border color', 'default': '#FFFFFF'},
        'opacity': {'label': 'Opacity (%)', 'min': 0, 'max': 100},
        'swap': {'label': 'Swap', 'help': 'Make the second video the full-screen picture and the main input the inset.'},
        'audio': {'type': 'select', 'label': 'Audio', 'default': 'A', 'choices': list(audio_pick.LAYER_AUDIO),
                  'help': 'A = main input, B = inset video.'},
        'crf': {'hidden': True},
    }
}


def register_arguments(p):
    p.description = (
        "Picture-in-picture: a small inset video over the main one. Choose the corner (or exact position), "
        "size, border and opacity; use --swap to flip which video is full-screen; choose whose audio to keep."
    )
    p.add_argument("--input2", required=True, type=str, help="The inset video.")
    p.add_argument("--size", type=float, default=30.0, help="Inset width as percent of the picture width. Default: 30.")
    p.add_argument("--position", choices=POSITIONS, default="bottom right", help="Where the inset sits. Default: bottom right.")
    p.add_argument("--margin", type=float, default=3.0, help="Gap to the edge, percent of width. Default: 3.")
    p.add_argument("--x", type=float, default=50.0, help="Custom X, percent of the way across (centre of the inset). Default: 50.")
    p.add_argument("--y", type=float, default=50.0, help="Custom Y, percent of the way down (centre of the inset). Default: 50.")
    p.add_argument("--border", type=int, default=4, help="Border width in pixels. Default: 4.")
    p.add_argument("--border_color", type=str, default="#FFFFFF", help="Border color. Default: #FFFFFF.")
    p.add_argument("--opacity", type=float, default=100.0, help="Inset opacity, 0 to 100. Default: 100.")
    p.add_argument("--swap", action="store_true", help="Swap which video is full-screen and which is the inset.")
    audio_pick.add_audio_argument(p, audio_pick.LAYER_AUDIO, "A", "Which audio to keep: A (main), B (inset), Mix A + B, or Silent.")
    p.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def overlay_position(position: str, margin_pct: float, x_pct: float, y_pct: float):
    m = f"main_w*{margin_pct / 100.0:.4f}"
    table = {
        "bottom right": (f"main_w-overlay_w-{m}", f"main_h-overlay_h-{m}"),
        "bottom left": (m, f"main_h-overlay_h-{m}"),
        "top right": (f"main_w-overlay_w-{m}", m),
        "top left": (m, m),
        "center": ("(main_w-overlay_w)/2", "(main_h-overlay_h)/2"),
    }
    if position in table:
        return table[position]
    return (f"main_w*{x_pct / 100.0:.4f}-overlay_w/2", f"main_h*{y_pct / 100.0:.4f}-overlay_h/2")


def run(args):
    A, B = Path(args.input), Path(args.input2)
    if not B.exists():
        raise SystemExit(f"❌ Inset video not found: {B}")
    ia, ib = probe_video(A), probe_video(B)
    W, H = even(ia.width), even(ia.height)
    fps, total = ia.fps, ia.duration
    base_in, inset_in = ("1:v", ia) if args.swap else ("0:v", ib)
    inset_label = "0:v" if args.swap else "1:v"
    iw = even(W * max(5.0, min(100.0, args.size)) / 100.0)
    ih = even(iw * inset_in.height / max(1, inset_in.width))
    b = max(0, int(args.border))
    op = max(0.0, min(100.0, args.opacity)) / 100.0

    base = (f"[{'1:v' if args.swap else '0:v'}]{fit_chain('cover', W, H)},setsar=1,fps={fps:.6f},format=yuv420p[base]"
            if args.swap else f"[0:v]crop={W}:{H}:0:0,setsar=1,fps={fps:.6f},format=yuv420p[base]")
    inset = f"[{inset_label}]scale={iw}:{ih},setsar=1,fps={fps:.6f}"
    if b:
        inset += f",pad={iw + 2 * b}:{ih + 2 * b}:{b}:{b}:color={ff_color(args.border_color, (255, 255, 255))}"
    inset += ",format=rgba" + (f",colorchannelmixer=aa={op:.3f}" if op < 1.0 else "") + "[inset]"
    x, y = overlay_position(args.position, args.margin, args.x, args.y)
    graph = ";".join([base, inset, f"[base][inset]overlay=x={x}:y={y}:shortest=1:format=auto,format=yuv420p[out]"])

    out = Path(args.output)
    tmp = Path(tempfile.mkdtemp(prefix="vb_pip_"))
    try:
        wav = audio_pick.build_audio_track(args.audio, audio_pick.LAYER_AUDIO, A, B, total, tmp / "audio.wav", a_dur=ia.duration)
        cmd = ["ffmpeg", "-err_detect", "ignore_err", "-i", str(A), "-stream_loop", "-1", "-i", str(B)]
        if wav is not None:
            cmd += ["-i", str(wav)]
        cmd += ["-filter_complex", graph, "-map", "[out]"]
        cmd += ["-map", "2:a", "-c:a", "aac"] if wav is not None else ["-an"]
        cmd += ["-t", f"{total:.3f}", *encode_args(args.crf, fps), str(out)]
        if getattr(args, "force", False):
            cmd.insert(1, "-y")
        run_ffmpeg_with_progress(cmd, str(A), str(out), duration_override=total)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
