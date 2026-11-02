"""
audio_visualizer: draws the sound over the picture, a waveform line (wave) or a spectrum of bars (bars), in a strip at
the bottom or top of the frame, or across the whole picture. Pure ffmpeg (showwaves / showfreqs). The audio is
encoded to AAC; the drawing is composited with its black background made transparent.
"""
from videobeaux.utils.cv import hex_to_rgb
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.frame_pipe import probe_video
from videobeaux.utils.media import has_audio

STYLES = ["wave", "bars"]
POSITIONS = ["bottom", "top", "full"]

GUI_METADATA = {
    'args': {
        'style': {'label': 'Style', 'help': 'wave = a line that follows the sound. bars = a spectrum, one bar per band of pitches.'},
        'position': {'label': 'Position', 'help': 'bottom or top = a strip of the chosen height. full = drawn over the whole picture.'},
        'height': {'label': 'Strip height (% of frame)', 'min': 5, 'max': 100, 'good_min': 10, 'good_max': 40,
                   'help': 'How tall the strip is, as a share of the picture. Ignored for full.'},
        'color': {'type': 'color', 'label': 'Color', 'help': 'Colour of the line or bars.'},
        'opacity': {'label': 'Opacity', 'min': 0, 'max': 1, 'good_min': 0.3, 'good_max': 1,
                    'help': '1 = solid. Lower lets the picture show through the drawing.'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Draw the sound over the picture: a waveform line (wave) or a spectrum of bars (bars), in a strip at the bottom "
        "or top of the frame, or across the whole picture. The sound itself is kept."
    )
    parser.add_argument("--style", choices=STYLES, default="wave",
                        help="wave = a line that follows the sound; bars = a spectrum of frequency bars.")
    parser.add_argument("--position", choices=POSITIONS, default="bottom",
                        help="Where the drawing goes: bottom, top, or full (over the whole picture).")
    parser.add_argument("--height", type=float, default=20.0,
                        help="Strip height as a percent of the frame, 5-100. Default: 20. Ignored for full.")
    parser.add_argument("--color", type=str, default="#FFFFFF", help="Colour of the line or bars. Default: #FFFFFF.")
    parser.add_argument("--opacity", type=float, default=0.9, help="Opacity, 0 to 1. Default: 0.9.")


def _ff_color(text: str) -> str:
    r, g, b = hex_to_rgb(text, (255, 255, 255))
    return f"0x{r:02X}{g:02X}{b:02X}"


def run(args):
    if not has_audio(args.input):
        raise SystemExit("❌ Audio Visualizer draws the sound, and this video has no audio track.")
    info = probe_video(args.input)
    width = info.width - info.width % 2
    height = info.height - info.height % 2
    pct = 100.0 if args.position == "full" else max(5.0, min(100.0, args.height))
    strip_h = max(2, int(height * pct / 100) // 2 * 2)
    y = "main_h-overlay_h" if args.position == "bottom" else "0"
    opacity = max(0.0, min(1.0, args.opacity))
    if args.style == "bars":
        draw = "showfreqs=mode=bar:ascale=sqrt:fscale=log"
    else:
        draw = "showwaves=mode=cline:scale=sqrt"
    # The drawing's background is black: key it out so only the line or bars show, then set the opacity.
    graph = (
        "[0:a]asplit=2[aw][ao];"
        f"[aw]{draw}:s={width}x{strip_h}:rate={info.fps:.6f}:colors={_ff_color(args.color)},"
        "format=rgba,colorkey=0x000000:0.08:0.0,"
        f"colorchannelmixer=aa={opacity:.3f}[bar];"
        f"[0:v][bar]overlay=x=0:y={y}:eof_action=pass,format=yuv420p[out]"
    )
    cmd = ["ffmpeg", "-hide_banner", "-i", args.input, "-filter_complex", graph,
           "-map", "[out]", "-map", "[ao]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"]
    if getattr(args, "force", False):
        cmd.insert(1, "-y")
    cmd.append(str(args.output))
    run_ffmpeg_with_progress(cmd, args.input, args.output)
