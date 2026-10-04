"""
quad_split — split screen: up to four videos in one frame (2×2 grid, side by side, stacked, or one big
picture with three small), with adjustable gaps. Inputs you leave empty repeat the main video.
Pure ffmpeg; choose whose audio you hear.
"""
import shutil
import subprocess
import tempfile
from pathlib import Path

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.frame_pipe import probe_video
from videobeaux.utils.media import ensure_audio
from videobeaux.utils.mixer import encode_args, even, ff_color, fit_chain

LAYOUTS = ["2x2 grid", "side by side (2)", "stacked (2)", "1 big + 3 small"]
AUDIO = ["Input 1", "Input 2", "Input 3", "Input 4", "Mix all", "Silent"]

GUI_METADATA = {
    'args': {
        'input2': {'type': 'file', 'subtype': 'video', 'label': 'Video 2', 'help': 'Optional. Empty = repeats the main video.'},
        'input3': {'type': 'file', 'subtype': 'video', 'label': 'Video 3', 'help': 'Optional (layouts with 3+ cells).'},
        'input4': {'type': 'file', 'subtype': 'video', 'label': 'Video 4', 'help': 'Optional (layouts with 4 cells).'},
        'layout': {'type': 'select', 'label': 'Layout', 'default': LAYOUTS[0], 'choices': LAYOUTS},
        'gap': {'label': 'Gap (px)', 'min': 0, 'max': 60},
        'gap_color': {'type': 'color', 'label': 'Gap color', 'default': '#000000'},
        'fit': {'type': 'select', 'label': 'Fit', 'default': 'cover', 'choices': ['cover', 'contain', 'stretch'],
                'help': 'How each video fills its cell: cover crops, contain adds bars, stretch distorts.'},
        'audio': {'type': 'select', 'label': 'Audio', 'default': AUDIO[0], 'choices': AUDIO},
        'crf': {'hidden': True},
    }
}


def register_arguments(p):
    p.description = (
        "Split screen: up to four videos in a 2×2 grid, side by side, stacked, or one big picture plus "
        "three small. Empty inputs repeat the main video. Adjustable gap and color; choose whose audio to keep."
    )
    p.add_argument("--input2", type=str, default=None, help="Second video (optional).")
    p.add_argument("--input3", type=str, default=None, help="Third video (optional).")
    p.add_argument("--input4", type=str, default=None, help="Fourth video (optional).")
    p.add_argument("--layout", choices=LAYOUTS, default=LAYOUTS[0], help="Arrangement. Default: 2x2 grid.")
    p.add_argument("--gap", type=int, default=4, help="Gap between pictures in pixels. Default: 4.")
    p.add_argument("--gap_color", type=str, default="#000000", help="Gap color. Default: #000000.")
    p.add_argument("--fit", choices=["cover", "contain", "stretch"], default="cover", help="How each video fills its cell.")
    p.add_argument("--audio", choices=AUDIO, default=AUDIO[0], help="Whose audio to use. Default: Input 1.")
    p.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def cells(layout: str, W: int, H: int, g: int):
    """[(x, y, w, h), ...] for each picture, all even."""
    if layout == "side by side (2)":
        w = even((W - g) / 2)
        return [(0, 0, w, H), (W - w, 0, w, H)]
    if layout == "stacked (2)":
        h = even((H - g) / 2)
        return [(0, 0, W, h), (0, H - h, W, h)]
    if layout == "1 big + 3 small":
        bw = even((W - g) * 2 / 3)
        sw = even(W - g - bw)
        sh = even((H - 2 * g) / 3)
        return [(0, 0, bw, H), (W - sw, 0, sw, sh), (W - sw, (H - sh) // 2, sw, sh), (W - sw, H - sh, sw, sh)]
    w, h = even((W - g) / 2), even((H - g) / 2)
    return [(0, 0, w, h), (W - w, 0, w, h), (0, H - h, w, h), (W - w, H - h, w, h)]


def audio_graph(choice: str, n_inputs: int, total: float):
    fmt = "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo"
    if choice == "Silent":
        return None
    if choice == "Mix all":
        parts = "".join(f"[{k}:a]{fmt}[m{k}];" for k in range(n_inputs))
        mix = "".join(f"[m{k}]" for k in range(n_inputs))
        return f"{parts}{mix}amix=inputs={n_inputs}:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:{total:.3f}[aout]"
    k = min(n_inputs - 1, int(choice.split()[-1]) - 1)
    return f"[{k}:a]{fmt},atrim=0:{total:.3f}[aout]"


def run(args):
    main = Path(args.input)
    ia = probe_video(main)
    W, H = even(ia.width), even(ia.height)
    fps, total = ia.fps, ia.duration
    g = max(0, int(args.gap))
    rects = cells(args.layout, W, H, g)
    given = [args.input, args.input2, args.input3, args.input4]
    sources = [ensure_audio(given[i] or args.input) for i in range(len(rects))]

    parts = [f"color=c={ff_color(args.gap_color)}:s={W}x{H}:r={fps:.6f}:d={total:.3f},format=yuv420p[bg]"]
    for k, (x, y, w, h) in enumerate(rects):
        parts.append(f"[{k}:v]{fit_chain(args.fit, w, h)},setsar=1,fps={fps:.6f},format=yuv420p[c{k}]")
    prev = "bg"
    for k, (x, y, w, h) in enumerate(rects):
        parts.append(f"[{prev}][c{k}]overlay=x={x}:y={y}:shortest=0:eof_action=pass[o{k}]")
        prev = f"o{k}"
    parts.append(f"[{prev}]format=yuv420p[out]")
    ag = audio_graph(args.audio, len(rects), total)
    if ag:
        parts.append(ag)

    cmd = ["ffmpeg", "-err_detect", "ignore_err"]
    for k, src in enumerate(sources):
        cmd += (["-i", src] if k == 0 else ["-stream_loop", "-1", "-i", src])
    cmd += ["-filter_complex", ";".join(parts), "-map", "[out]"]
    cmd += ["-map", "[aout]", "-c:a", "aac"] if ag else ["-an"]
    out = Path(args.output)
    cmd += ["-t", f"{total:.3f}", *encode_args(args.crf, fps), str(out)]
    if getattr(args, "force", False):
        cmd.insert(1, "-y")
    run_ffmpeg_with_progress(cmd, str(main), str(out), duration_override=total)
