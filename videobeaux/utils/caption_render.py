"""
Kinetic-typography caption renderer (used by Captburn and Auto Narrate).

Each output frame's caption is drawn from scratch with PIL as an RGBA image: the actively-spoken word is rendered at a genuinely
larger font size and in the highlight colour while the rest of the line stays perfectly still. (An ASS/libass subtitle can't do
this cleanly — resizing one word reflows the whole line.) The frames are piped straight into ffmpeg as raw RGBA and overlaid on
the video, so there are no temporary PNG files and ffmpeg needs no PNG decoder.
"""
from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont

from videobeaux.utils.caption_words import coerce_segments, extract_words, is_capton
from videobeaux.utils.fonts import resolve_font


def hex_to_rgba(hex_color: str, alpha: int = 255) -> Tuple[int, int, int, int]:
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


def _frame_bytes(frame_cache: dict, key, make) -> bytes:
    b = frame_cache.get(key)
    if b is None:
        if len(frame_cache) > 64:
            frame_cache.clear()
        b = frame_cache[key] = make().tobytes()
    return b


def burn_captions(args) -> None:
    """
    Burn word-timed captions onto `args.input` → `args.output`.

    args: input, output, force, trans_json (word-timestamped transcript JSON), font (family name or file path), font_size,
    min_font_size, words_per_caption, no_uppercase, caption_max_width (0–1 of the width), caption_max_lines, active_scale,
    vertical_anchor (0–1 of the height), primary / highlight / outline (#RRGGBB), stroke_width, vcodec, crf, preset.
    """
    in_video, out_video = Path(args.input), Path(args.output)
    out_video.parent.mkdir(parents=True, exist_ok=True)

    with open(args.trans_json, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if is_capton(raw):
        raise ValueError("That is a captburn .captburn.json (ASS) file, not a word-timestamped transcript.")
    all_words: List[Dict[str, Any]] = []
    for seg in coerce_segments(raw):
        all_words.extend(extract_words(seg))
    if not all_words:
        raise ValueError("The transcript has no words to caption.")
    groups = _group_words(all_words, int(args.words_per_caption))

    width, height, fps, duration = _probe_video(in_video)
    width, height = width - width % 2, height - height % 2
    print(f"📐 Video dimensions: {width}x{height} @ {fps:.3f}fps, {duration:.2f}s")

    font_path = resolve_font(args.font, bold=True)
    if not font_path:
        raise RuntimeError(f"Could not find a usable font for {args.font!r}. Pick another font or a .ttf/.otf file.")
    print(f"🔤 Font: {Path(font_path).name}")

    kw = dict(
        font_size=int(args.font_size), stroke_width=int(args.stroke_width),
        max_width_ratio=float(args.caption_max_width), max_lines=int(args.caption_max_lines),
        active_scale=float(args.active_scale), vertical_anchor=float(args.vertical_anchor),
        min_font_size=int(args.min_font_size), primary_rgba=hex_to_rgba(args.primary),
        highlight_rgba=hex_to_rgba(args.highlight), outline_rgba=hex_to_rgba(args.outline),
        uppercase=not bool(getattr(args, "no_uppercase", False)),
    )

    total = math.ceil(duration * fps)
    cmd = ["ffmpeg", "-hide_banner", "-y" if getattr(args, "force", False) else "-n",
           "-i", str(in_video),
           "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{width}x{height}", "-framerate", f"{fps:.6f}", "-i", "-",
           "-filter_complex", f"[0:v]crop={width}:{height}:0:0[base];[base][1:v]overlay=0:0:format=auto[vout]",
           "-map", "[vout]", "-map", "0:a?",
           "-c:v", args.vcodec, "-crf", str(args.crf), "-preset", args.preset, "-pix_fmt", "yuv420p",
           "-c:a", "copy", "-shortest"]
    if out_video.suffix.lower() in (".mp4", ".mov", ".m4v"):
        cmd += ["-movflags", "+faststart"]
    cmd.append(str(out_video))

    print(f"🖼️  Rendering {total} caption frames at {fps:.3f} fps…", flush=True)
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    blank = bytes(width * height * 4)
    cache: dict = {}
    ok = False
    try:
        gi = 0
        for n in range(total):
            t = n / fps
            while gi < len(groups) and t > groups[gi]["end"]:
                gi += 1
            g = groups[gi] if gi < len(groups) and groups[gi]["start"] <= t <= groups[gi]["end"] else None
            if g is None:
                data = blank
            else:
                active = next((i for i, w in enumerate(g["words"]) if w["start"] <= t <= w["end"]), None)
                data = _frame_bytes(cache, (gi, active), lambda: _render_caption_frame(width, height, g, t, font_path, **kw))
            enc.stdin.write(data)
        ok = True
    except BrokenPipeError:
        pass                                          # ffmpeg stopped early; its exit code says why
    finally:
        try:
            enc.stdin.close()
        except Exception:
            pass
        code = enc.wait()
    if code != 0:
        raise RuntimeError(f"ffmpeg failed while burning captions (exit code {code}). See the log above.")
    print(f"✅ Burned → {out_video}")
