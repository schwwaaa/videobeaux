"""
text_overlay: a simple titler. A block of text laid over the video, with the font and colours of Auto Narrate's
captions and the placement and timing of Watermark.

The text is drawn once into a transparent PNG (same font lookup and outline as the captions, at the size you asked for,
wrapped to the frame width), then the watermark program lays that PNG over the video. Placement, the Appear/Disappear window and the
encoding are all shared with it, so a title behaves exactly like a watermark.
"""
from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace

from PIL import Image, ImageDraw, ImageFont

from videobeaux.programs import watermark
from videobeaux.utils.caption_render import hex_to_rgba
from videobeaux.utils.fonts import resolve_font

PLACEMENTS = [
    "top-left", "top-center", "top-right",
    "center-left", "center", "center-right",
    "bottom-left", "bottom-center", "bottom-right",
    "custom",
]


def register_arguments(parser: argparse.ArgumentParser):
    parser.description = (
        "Overlay a block of text (a title, a lower third, a caption card) on the video. Same font and colour options "
        "as Auto Narrate; the same placement grid and Appear/Disappear timing as Watermark."
    )
    parser.add_argument("--text", required=True, type=str,
                        help="The text to show. Put a new line in the text for a second line.")
    parser.add_argument("--font", type=str, default="Arial",
                        help="Font name (or a path to a .ttf/.otf file). Default: Arial.")
    parser.add_argument("--font_size", type=int, default=76,
                        help="Font size in px. Every title uses this size, whatever its length: long text wraps onto more "
                             "lines instead of shrinking. Default: 76.")
    parser.add_argument("--primary_color", type=str, default="#FFFFFF",
                        help="Text colour. Default: #FFFFFF (white).")
    parser.add_argument("--outline_color", type=str, default="#000000",
                        help="Text outline colour. Default: #000000 (black).")
    parser.add_argument("--placement", choices=PLACEMENTS, default="bottom-center",
                        help="Where the text sits. Use 'custom' with --x_pos/--y_pos for exact control.")
    parser.add_argument("--margin", type=int, default=24, help="Margin (px) from the edges. Default: 24.")
    parser.add_argument("--x_pos", type=str, default=None,
                        help="Horizontal position, in pixels or an ffmpeg expression. Only used with --placement custom.")
    parser.add_argument("--y_pos", type=str, default=None,
                        help="Vertical position, in pixels or an ffmpeg expression. Only used with --placement custom.")
    parser.add_argument("--opacity", type=float, default=1.0, help="Text opacity, 0.0 to 1.0. Default: 1.0.")
    parser.add_argument("--spin", type=float, default=0.0,
                        help="Spin in degrees per second, like Watermark (0 = no rotation). Default: 0.")
    parser.add_argument("--wobble", type=float, default=0.0,
                        help="Swing in degrees: the text goes this far one way, back through upright, then as far the other "
                             "way (0 = none). Default: 0.")
    parser.add_argument("--wobble_period", type=float, default=2.0,
                        help="Seconds for one full wobble. Default: 2.")
    parser.add_argument("--start", type=str, default="0",
                        help="When the text appears: seconds (83.5) or a timestamp (1:23). 0 = from the start.")
    parser.add_argument("--end", type=str, default="0",
                        help="When the text goes away: seconds or a timestamp. 0 = it stays to the end.")


def _probe_size(path: Path) -> tuple[int, int]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
         "-of", "csv=p=0:s=x", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    w, h = out.split("x")
    return int(w), int(h)


def _wrap(draw, text, font, stroke, max_width):
    """Greedy word wrap, one paragraph per line of the input text."""
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        line = words[0]
        for word in words[1:]:
            candidate = f"{line} {word}"
            if draw.textbbox((0, 0), candidate, font=font, stroke_width=stroke)[2] <= max_width:
                line = candidate
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def _render_title(text, font_name, font_size, fill, outline, frame_w, frame_h, path: Path) -> bool:
    """
    Draw the text as a transparent RGBA PNG at exactly font_size, wrapped to 86% of the frame width.
    Returns False when the block is taller than the frame (it is still drawn; the top or bottom gets cut off).
    """
    font_path = resolve_font(font_name)
    fill_rgba, outline_rgba = hex_to_rgba(fill), hex_to_rgba(outline)
    scratch = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    size = int(font_size)
    font = ImageFont.truetype(font_path, size)
    stroke = max(1, round(size * 0.1))
    lines = _wrap(scratch, text, font, stroke, frame_w * 0.86)
    line_h = int(size * 1.2)
    block_h = len(lines) * line_h

    widths = [scratch.textbbox((0, 0), ln, font=font, stroke_width=stroke)[2] for ln in lines]
    pad = stroke * 2
    image = Image.new("RGBA", (max(widths) + pad, block_h + pad), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    for i, (line, width) in enumerate(zip(lines, widths)):
        x = (image.width - width) / 2
        y = stroke + i * line_h
        draw.text((x, y), line, font=font, fill=fill_rgba, stroke_width=stroke, stroke_fill=outline_rgba, anchor="la")
    image.save(path)
    return block_h <= frame_h


def run(args: argparse.Namespace):
    in_path = Path(args.input)
    if not in_path.exists():
        raise SystemExit(f"❌ Input not found: {in_path}")
    if not args.text or not args.text.strip():
        raise SystemExit("❌ --text is empty. Give the words to show.")
    if args.font_size <= 0:
        raise SystemExit("❌ --font_size must be above 0.")

    frame_w, frame_h = _probe_size(in_path)
    with tempfile.TemporaryDirectory(prefix="vb_title_") as tmp:
        title = Path(tmp) / "title.png"
        fits = _render_title(args.text.strip("\n"), args.font, args.font_size, args.primary_color, args.outline_color,
                             frame_w, frame_h, title)
        if not fits:
            print("⚠️  The text is taller than the frame at this font size, so the top or bottom will be cut off. "
                  "Use a smaller --font_size or less text.", flush=True)
        # Same placement, timing and encoding as Watermark; the PNG is already at its final size, so scale 1.0.
        watermark.run(SimpleNamespace(
            input=args.input, output=args.output, force=getattr(args, "force", False),
            watermark=str(title), placement=args.placement, margin=args.margin,
            x_pos=args.x_pos, y_pos=args.y_pos, width=None, height=None, scale=1.0,
            opacity=args.opacity, spin=args.spin, wobble=args.wobble, wobble_period=args.wobble_period,
            start=args.start, end=args.end,
            wm_loop=0, ignore_loop=False, video_crf=18, video_preset="fast",
        ))
