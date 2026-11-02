"""
subtitle_burn: burns an .srt subtitle file into the picture, styled: font, size, colours, outline and where it sits.
Uses ffmpeg's subtitles filter (libass). The video is re-encoded; the audio is copied unchanged.
(Captburn makes captions from the speech itself; this one uses subtitles you already have.)
"""
import shutil
import tempfile
from pathlib import Path

from videobeaux.utils.cv import hex_to_rgb
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

# SSA alignment numbers, as libass reads them in force_style: 2 = bottom centre, 10 = middle centre, 6 = top centre.
POSITIONS = {"bottom": 2, "middle": 10, "top": 6}

GUI_METADATA = {
    'args': {
        'srt': {'label': 'Subtitle file (.srt)', 'help': 'The subtitle file to burn in. Times are read from the file.'},
        'font': {'type': 'font', 'label': 'Font', 'help': 'A font name installed on this computer, for example Arial.'},
        'font_size': {'label': 'Font size', 'min': 8, 'max': 120, 'good_min': 16, 'good_max': 60,
                      'help': 'Subtitle size in pixels, as the video is drawn.'},
        'primary_color': {'type': 'color', 'label': 'Text color', 'help': 'Colour of the subtitle text.'},
        'outline_color': {'type': 'color', 'label': 'Outline color', 'help': 'Colour of the outline around the text.'},
        'outline': {'label': 'Outline width', 'min': 0, 'max': 6, 'good_min': 0, 'good_max': 4,
                    'help': 'Thickness of the outline, in pixels. 0 = none.'},
        'position': {'label': 'Position', 'help': 'Where the subtitles sit on the picture.'},
        'margin': {'label': 'Margin from the edge (px)', 'min': 0, 'max': 300, 'good_min': 0, 'good_max': 120,
                   'help': 'Distance from the bottom or top edge. Ignored for middle.'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Subtitle Burn: burn an .srt subtitle file into the picture with the font, size, colours, outline and position "
        "you choose. The sound is kept."
    )
    parser.add_argument("--srt", required=True, type=str, help="The .srt subtitle file to burn in.")
    parser.add_argument("--font", type=str, default="Arial", help="Font name installed on this computer. Default: Arial.")
    parser.add_argument("--font_size", type=int, default=24, help="Subtitle size in pixels. Default: 24.")
    parser.add_argument("--primary_color", type=str, default="#FFFFFF", help="Text colour. Default: #FFFFFF.")
    parser.add_argument("--outline_color", type=str, default="#000000", help="Outline colour. Default: #000000.")
    parser.add_argument("--outline", type=float, default=2.0, help="Outline width in pixels, 0-6. Default: 2.")
    parser.add_argument("--position", choices=list(POSITIONS), default="bottom",
                        help="Where the subtitles sit. Default: bottom.")
    parser.add_argument("--margin", type=int, default=30,
                        help="Distance from the top or bottom edge in pixels. Default: 30.")


def _ass_colour(text: str) -> str:
    """#RRGGBB → the ASS &HAABBGGRR form (alpha 00 = opaque)."""
    r, g, b = hex_to_rgb(text, (255, 255, 255))
    return f"&H00{b:02X}{g:02X}{r:02X}"


_FILTER_SPECIAL = set("\\:'[],;")


def _escape_path(path) -> str:
    """Backslash-escape the characters ffmpeg's filter parser treats as syntax (a quoted value can't hold a quote)."""
    return "".join("\\" + ch if ch in _FILTER_SPECIAL else ch for ch in str(path))


def run(args):
    srt = Path(args.srt)
    if not srt.exists():
        raise SystemExit(f"❌ Subtitle file not found: {srt}")
    style = ",".join([
        f"Fontname={args.font}",
        f"Fontsize={int(args.font_size)}",
        f"PrimaryColour={_ass_colour(args.primary_color)}",
        f"OutlineColour={_ass_colour(args.outline_color)}",
        f"Outline={max(0.0, min(6.0, args.outline)):g}",
        f"Alignment={POSITIONS[args.position]}",
        f"MarginV={max(0, int(args.margin))}",
    ])
    # The subtitles filter parses its file name itself, so a name with an apostrophe or a colon breaks it. The file is
    # copied to a temporary folder under a plain name first; the copy is removed when the run finishes.
    with tempfile.TemporaryDirectory(prefix="vb_subs_") as tmp:
        safe = Path(tmp) / "subtitles.srt"
        shutil.copyfile(srt, safe)
        vf = f"subtitles=filename={_escape_path(safe)}:force_style='{style}'"
        cmd = ["ffmpeg", "-hide_banner", "-i", args.input,
               "-vf", vf,
               "-map", "0:v", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
               "-map", "0:a?", "-c:a", "copy", "-movflags", "+faststart"]
        if getattr(args, "force", False):
            cmd.insert(1, "-y")
        cmd.append(str(args.output))
        run_ffmpeg_with_progress(cmd, args.input, args.output)
