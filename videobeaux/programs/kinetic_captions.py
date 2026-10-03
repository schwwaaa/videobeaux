from __future__ import annotations
r"""
videobeaux.programs.kinetic_captions - per-frame rendered kinetic captions

Direct port of the caption-rendering core of the user's reference script
(capt_gen_burn.py): each output frame's caption is drawn from scratch as a
PIL RGBA image — the actively-spoken word rendered at a genuinely larger
font size and a distinct color, everything else untouched — then the whole
PNG sequence is overlaid onto the input video with ffmpeg.

This exists alongside captburn.py (which drives libass/ASS's flowed-text
engine) because a per-word SIZE pop that doesn't perturb the rest of the
line is not something ASS's text-layout model can do cleanly: any change to
one word's rendered width or height makes libass reflow or re-anchor the
whole line, which reads as the caption jittering (confirmed directly this
session via consecutive-frame pixel diffs). A from-scratch per-frame bitmap
render sidesteps that entirely, at the cost of a slower render (real frames
written to disk and re-encoded, not a single lightweight subtitle filter).

Scope: only the reference's caption-RENDERING core is ported. Its
topic-generation/TTS/transcription glue is intentionally left out —
videobeaux already has that decomposed into its own composable pieces
(auto_narrate's Ollama/kokoro-tts orchestration, transcraibe's Vosk
transcription) — so this program takes a transcript JSON (the same shape
captburn.py accepts: a word-timestamped list, or {"segments": [...]}) and
burns captions onto any video standalone, matching captburn's own
input/output contract.

Entry points expected by cli.py:
  * register_arguments(parser)
  * run(args)
"""
from pathlib import Path
from typing import Any, Dict, List, Tuple
import argparse
import json
import math
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

from videobeaux.programs.captburn import _coerce_segments, _extract_words, _find_font_file, _is_capton
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress


def _hex_to_rgba(hex_color: str, alpha: int = 255) -> Tuple[int, int, int, int]:
    hx = hex_color.strip()
    if hx.startswith("#"):
        hx = hx[1:]
    if len(hx) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}")
    r, g, b = int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)
    return (r, g, b, alpha)


def _probe_video(video_path: Path) -> Tuple[int, int, float, float]:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate:format=duration",
         "-of", "json", str(video_path)],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(result.stdout)
    stream = data["streams"][0]
    width, height = int(stream["width"]), int(stream["height"])
    num, den = stream["r_frame_rate"].split("/")
    fps = float(num) / float(den)
    duration = float(data["format"]["duration"])
    return width, height, fps, duration


def _group_words(words: List[Dict[str, Any]], words_per_caption: int) -> List[Dict[str, Any]]:
    groups = []
    for i in range(0, len(words), max(1, words_per_caption)):
        chunk = words[i:i + words_per_caption]
        if not chunk:
            continue
        groups.append({"words": chunk, "start": chunk[0]["start"], "end": chunk[-1]["end"]})
    return groups


def _measure_text(draw, text, font, stroke_width):
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _split_oversize_word(draw, text, font, stroke_width, max_width):
    """
    Last-resort splitter for a single word that cannot fit on one line.
    Prefers no hyphenation; only splits when the word itself exceeds max_width.
    A hyphen is appended to non-final pieces when it fits.
    """
    full_width, _ = _measure_text(draw, text, font, stroke_width)
    if full_width <= max_width:
        return [text]

    pieces = []
    remaining = text
    while remaining:
        best = None
        for cut in range(1, len(remaining) + 1):
            candidate = remaining[:cut]
            is_final = cut == len(remaining)
            rendered = candidate if is_final else candidate + "-"
            width, _ = _measure_text(draw, rendered, font, stroke_width)
            if width <= max_width:
                best = (cut, rendered)
            else:
                break
        if best is None:
            cut, rendered = 1, remaining[:1]
        else:
            cut, rendered = best
        pieces.append(rendered)
        remaining = remaining[cut:]
    return pieces


def _wrap_caption_words(draw, display_words, active_index, base_font, active_font, stroke_width, max_width, spacing):
    """
    Wrap caption text by actual rendered pixel width. Whole words are kept
    intact whenever possible; a word is only split (with minimal
    hyphenation) when that single word is wider than max_width. Returns a
    list of lines, each a list of (original_word_index, rendered_text,
    rendered_width, is_fragment) tuples.
    """
    lines = []
    current_line = []
    current_width = 0

    for i, text in enumerate(display_words):
        font = active_font if i == active_index else base_font
        fragments = _split_oversize_word(draw, text, font, stroke_width, max_width)

        for fragment_index, fragment in enumerate(fragments):
            fragment_width, _ = _measure_text(draw, fragment, font, stroke_width)
            gap = spacing if current_line else 0
            proposed_width = current_width + gap + fragment_width

            if current_line and proposed_width > max_width:
                lines.append(current_line)
                current_line = []
                current_width = 0
                gap = 0

            current_line.append((i, fragment, fragment_width, len(fragments) > 1))
            current_width += gap + fragment_width

            if len(fragments) > 1 and fragment_index < len(fragments) - 1:
                lines.append(current_line)
                current_line = []
                current_width = 0

    if current_line:
        lines.append(current_line)
    return lines


def _render_caption_frame(
    width, height, group, current_time, font_path,
    font_size, stroke_width, max_width_ratio, max_lines,
    active_scale, vertical_anchor, min_font_size,
    primary_rgba, highlight_rgba, outline_rgba, uppercase,
):
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    words = group["words"]

    active_index = None
    for i, word in enumerate(words):
        if word["start"] <= current_time <= word["end"]:
            active_index = i
            break

    display_words = [(w["text"].strip().upper() if uppercase else w["text"].strip()) for w in words]
    max_caption_width = width * max_width_ratio

    # Start at the requested size, but shrink slightly if the caption would
    # otherwise require too many lines.
    working_font_size = font_size
    while True:
        base_font = ImageFont.truetype(font_path, working_font_size)
        active_font = ImageFont.truetype(font_path, max(1, int(working_font_size * active_scale)))
        spacing = max(1, int(working_font_size * 0.22))

        lines = _wrap_caption_words(
            draw=draw, display_words=display_words, active_index=active_index,
            base_font=base_font, active_font=active_font, stroke_width=stroke_width,
            max_width=max_caption_width, spacing=spacing,
        )

        if len(lines) <= max_lines or working_font_size <= min_font_size:
            break
        working_font_size -= 2

    line_height = int(working_font_size * 1.28)
    block_height = len(lines) * line_height
    block_top = (height * vertical_anchor) - (block_height / 2)

    for line_number, line in enumerate(lines):
        line_width = sum(item[2] for item in line) + spacing * (len(line) - 1)
        x = (width - line_width) / 2
        line_y = block_top + (line_number * line_height)

        for original_index, text, word_width, _is_fragment in line:
            active = original_index == active_index
            font = active_font if active else base_font
            fill = highlight_rgba if active else primary_rgba
            y = line_y - (14 if active else 0)

            draw.text(
                (x, y), text, font=font, fill=fill,
                stroke_width=stroke_width, stroke_fill=outline_rgba, anchor="la",
            )
            x += word_width + spacing

    return image


def _render_caption_frames(width, height, fps, duration, groups, output_dir, font_path, **kw):
    output_dir = Path(output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    total_frames = math.ceil(duration * fps)
    print(f"🖼️  Rendering {total_frames} caption frames at {fps:.3f} fps…")

    for frame_number in range(total_frames):
        t = frame_number / fps
        active_group = None
        for group in groups:
            if group["start"] <= t <= group["end"]:
                active_group = group
                break

        if active_group:
            frame = _render_caption_frame(width, height, active_group, t, font_path, **kw)
        else:
            frame = Image.new("RGBA", (width, height), (0, 0, 0, 0))

        frame.save(output_dir / f"caption_{frame_number:06d}.png")

    return total_frames


GUI_METADATA = {
    'args': {
        'trans_json': {'type': 'file', 'label': 'Transcript JSON', 'help': 'Word-timestamped transcript JSON (default: <input>.json)'},
        'primary': {'type': 'color'},
        'highlight': {'type': 'color'},
        'outline': {'type': 'color'},
    }
}


def register_arguments(parser: argparse.ArgumentParser):
    parser.description = (
        "Kinetic-typography captions burned in via per-frame PIL rendering (not ASS/libass), so the "
        "currently-spoken word can grow larger while the rest of the line stays perfectly still — the "
        "same technique short-form caption tools use. Slower than captburn (real frames written and "
        "re-encoded) but supports a true per-word size pop that ASS's text-flow engine can't do cleanly."
    )
    parser.add_argument("-t", "--trans-json", type=str, help="Transcript JSON (default: <input>.json)")
    parser.add_argument("--caption", dest="caption", type=str, help="Transcript JSON to re-burn (alt. to --trans-json)")

    parser.add_argument("--words-per-caption", type=int, default=4,
                        help="Words shown per caption burst (default: 4) — short bursts, not whole sentences.")
    parser.add_argument("--no-uppercase", action="store_true",
                        help="Keep the transcript's original case instead of forcing UPPERCASE.")

    parser.add_argument("--font", default="Arial")
    parser.add_argument("--font-size", type=int, default=76)
    parser.add_argument("--min-font-size", type=int, default=36, help="Auto-shrink floor in px.")
    parser.add_argument("--caption-max-width", type=float, default=0.86,
                        help="Max caption width as a fraction of video width.")
    parser.add_argument("--caption-max-lines", type=int, default=2,
                        help="Max preferred lines before the font size is auto-shrunk.")
    parser.add_argument("--active-scale", type=float, default=1.18,
                        help="How much larger the actively-spoken word renders, e.g. 1.18 = 18%% bigger.")
    parser.add_argument("--vertical-anchor", type=float, default=0.67,
                        help="Vertical center of the caption block as a fraction of video height.")

    parser.add_argument("--primary", default="#FFFFFF", help="Normal (not-yet-active) word color.")
    parser.add_argument("--highlight", default="#FFE128", help="Active word color.")
    parser.add_argument("--outline", default="#000000", help="Text outline/stroke color.")
    parser.add_argument("--stroke-width", type=int, default=8, help="Outline stroke width in px.")

    parser.add_argument("--vcodec", default="libx264")
    parser.add_argument("--crf", type=int, default=18)
    parser.add_argument("--preset", default="medium")


def run(args) -> None:
    in_video = Path(args.input)
    out_video = Path(args.output)
    out_video.parent.mkdir(parents=True, exist_ok=True)

    trans_json = Path(args.trans_json) if getattr(args, "trans_json", None) else None
    caption_in = Path(args.caption) if getattr(args, "caption", None) else None
    src = caption_in if (caption_in and caption_in.exists()) else trans_json
    if not src:
        candidate = in_video.with_suffix(".json")
        if candidate.exists():
            src = candidate
        else:
            raise FileNotFoundError("No transcript JSON provided and <input>.json not found.")

    with open(src, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if _is_capton(raw):
        raise ValueError(
            "kinetic_captions takes a word-timestamped transcript JSON, not a captburn .captburn.json "
            "capton file — point --trans-json/--caption at the original transcript instead."
        )
    segments = _coerce_segments(raw)

    all_words: List[Dict[str, Any]] = []
    for seg in segments:
        all_words.extend(_extract_words(seg))
    if not all_words:
        raise ValueError("Transcript has no words to caption.")

    groups = _group_words(all_words, int(args.words_per_caption))

    width, height, fps, duration = _probe_video(in_video)
    print(f"📐 Video dimensions: {width}x{height} @ {fps:.3f}fps, {duration:.2f}s")

    font_path = _find_font_file(args.font)
    if not font_path:
        raise RuntimeError(
            f"Could not locate a usable font file for {args.font!r}. Try a different --font or "
            "pass a full path to a .ttf/.otf file."
        )

    primary_rgba = _hex_to_rgba(args.primary)
    highlight_rgba = _hex_to_rgba(args.highlight)
    outline_rgba = _hex_to_rgba(args.outline)

    with tempfile.TemporaryDirectory(prefix="videobeaux_kinetic_captions_") as tmp_str:
        frames_dir = Path(tmp_str) / "caption_frames"

        _render_caption_frames(
            width, height, fps, duration, groups, frames_dir, font_path,
            font_size=int(args.font_size),
            stroke_width=int(args.stroke_width),
            max_width_ratio=float(args.caption_max_width),
            max_lines=int(args.caption_max_lines),
            active_scale=float(args.active_scale),
            vertical_anchor=float(args.vertical_anchor),
            min_font_size=int(args.min_font_size),
            primary_rgba=primary_rgba,
            highlight_rgba=highlight_rgba,
            outline_rgba=outline_rgba,
            uppercase=not bool(getattr(args, "no_uppercase", False)),
        )

        caption_pattern = frames_dir / "caption_%06d.png"
        cmd = [
            "ffmpeg",
            "-i", str(in_video),
            "-framerate", str(fps),
            "-i", str(caption_pattern),
            "-filter_complex", "[0:v][1:v]overlay=0:0:format=auto[vout]",
            "-map", "[vout]",
            "-map", "0:a?",
            "-c:v", args.vcodec,
            "-crf", str(args.crf),
            "-preset", args.preset,
            "-c:a", "copy",
            "-pix_fmt", "yuv420p",
            "-shortest",
            str(out_video),
        ]
        command = (cmd[:1] + ["-y"] + cmd[1:]) if getattr(args, "force", False) else cmd
        print("🎬 Compositing captions onto video…")
        run_ffmpeg_with_progress(command, str(in_video), str(out_video))

    print(f"✅ Burned → {out_video}")
