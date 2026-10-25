"""
captburn — burn the clip's own speech onto the picture as kinetic captions.

Works like Auto Narrate, minus the script and the synthetic voice: the words on screen are the words in the clip. It looks for a
transcript next to the input (`<input>.json`); if there isn't one it transcribes the clip locally with Vosk first (and saves it
there, so the next run — or Grep Supercut, Ngrams … — reuses it). Captions are short bursts of words; the word being spoken
pops larger and takes the highlight colour, and the font size shrinks to fit the frame. The original audio is kept untouched.

This is the one caption program: it replaced the separate "Kinetic Captions" (same renderer, but it needed a transcript JSON
you made yourself) and the older libass-based Captburn (kept in experimental/captburn-ass-module.py).
"""
from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace

from videobeaux.utils.caption_render import burn_captions

GUI_METADATA = {
    'args': {
        'stt_model': {
            'type': 'file', 'subtype': 'model', 'label': 'Vosk Model',
            'help': 'Used to transcribe the clip first. Only needed when the clip has no transcript (<clip>.json) yet.',
        },
        'font': {'type': 'font', 'label': 'Font', 'help': 'Pick a font — each one is shown in its own typeface. The bundled ones work the same on every computer.'},
        'font_size': {'label': 'Font Size', 'min': 12, 'max': 200, 'step': 2, 'good_min': 48, 'good_max': 110,
                      'help': 'Requested size in px — shrunk automatically so every line fits the frame.'},
        'primary_color': {'type': 'color', 'label': 'Text Color', 'help': 'Words that are not being spoken right now.'},
        'highlight_color': {'type': 'color', 'label': 'Highlight Color', 'help': 'The word being spoken.'},
        'outline_color': {'type': 'color', 'label': 'Outline Color'},
        'outline_width': {'label': 'Outline Thickness', 'min': 0, 'max': 24, 'step': 1, 'good_min': 4, 'good_max': 12, 'help': 'Pixels.'},
        'words_per_caption': {'label': 'Words per Caption', 'min': 1, 'max': 10, 'step': 1, 'good_min': 2, 'good_max': 5,
                              'help': 'How many words are on screen together. Short bursts read best.'},
        'highlight_size': {'label': 'Highlight Pop', 'min': 1.0, 'max': 2.0, 'step': 0.02, 'good_min': 1.1, 'good_max': 1.4,
                           'help': 'How much bigger the spoken word is drawn. 1 = same size.'},
        'keep_case': {'label': 'Keep Capitalisation', 'help': 'Leave the words as transcribed instead of ALL CAPS.'},
        'vertical_position': {'label': 'Vertical Position', 'min': 0.05, 'max': 0.95, 'step': 0.01, 'good_min': 0.5, 'good_max': 0.85,
                              'help': 'Where the captions sit: 0 = top of the picture, 1 = bottom.'},
        'max_width': {'label': 'Max Width', 'min': 0.3, 'max': 1.0, 'step': 0.02, 'help': 'Widest a caption may be, as a share of the picture width.'},
        'max_lines': {'label': 'Max Lines', 'min': 1, 'max': 4, 'step': 1, 'help': 'The font shrinks until the caption fits in this many lines.'},
        'trans_json': {'hidden': True},
    }
}


def register_arguments(parser: argparse.ArgumentParser):
    parser.description = (
        "Burns the clip's own speech onto the video as kinetic-typography captions (the actively-spoken word pops "
        "larger), exactly like Auto Narrate's captions but using what is said in the clip instead of a narration. "
        "Uses <input>.json if it exists; otherwise transcribes locally (Vosk) first and saves it there."
    )
    parser.add_argument("--stt_model", type=str, default=None,
                        help="Path to the Vosk model directory — used to transcribe the clip when no transcript exists yet.")
    parser.add_argument("--font", type=str, default="Arial",
                        help="Font family name (bundled or installed) or a path to a .ttf/.otf file. Default: Arial.")
    parser.add_argument("--font_size", type=int, default=76,
                        help="Requested caption font size in px — auto-shrunk as needed to fit the frame. Default: 76.")
    parser.add_argument("--primary_color", type=str, default="#FFFFFF",
                        help="Color of words that aren't currently being spoken. Default: #FFFFFF (white).")
    parser.add_argument("--highlight_color", type=str, default="#FFE128",
                        help="Color of the word currently being spoken. Default: #FFE128 (gold).")
    parser.add_argument("--outline_color", type=str, default="#000000",
                        help="Caption text outline color. Default: #000000 (black).")
    parser.add_argument("--outline_width", type=int, default=8, help="Outline thickness in px. Default: 8.")
    parser.add_argument("--words_per_caption", type=int, default=4, help="Words on screen together. Default: 4.")
    parser.add_argument("--highlight_size", type=float, default=1.18,
                        help="How much larger the spoken word is drawn (1 = same size). Default: 1.18.")
    parser.add_argument("--keep_case", action="store_true", help="Keep the transcript's capitalisation instead of ALL CAPS.")
    parser.add_argument("--vertical_position", type=float, default=0.67,
                        help="Vertical centre of the captions as a share of the picture height (0 = top, 1 = bottom). Default: 0.67.")
    parser.add_argument("--max_width", type=float, default=0.86,
                        help="Widest a caption may be, as a share of the picture width. Default: 0.86.")
    parser.add_argument("--max_lines", type=int, default=2, help="The font shrinks until a caption fits in this many lines. Default: 2.")
    # CLI-only: use a transcript you edited / made elsewhere instead of <input>.json
    parser.add_argument("-t", "--trans_json", "--trans-json", dest="trans_json", type=str, default=None,
                        help="Use this transcript JSON instead of <input>.json.")


def _transcript_for(args) -> Path:
    """The transcript to caption from: --trans-json, else <input>.json, else make it with Vosk (saved as <input>.json)."""
    in_video = Path(args.input)
    explicit = getattr(args, "trans_json", None)
    if explicit:
        p = Path(explicit)
        if not p.exists():
            raise SystemExit(f"❌ Transcript not found: {p}")
        print(f"ℹ️  Using transcript {p}")
        return p

    found = in_video.with_suffix(".json")
    if found.exists():
        print(f"ℹ️  Using the existing transcript {found}")
        return found

    model = getattr(args, "stt_model", None)
    if not model:
        raise SystemExit(
            "❌ This clip has no transcript yet, and no Vosk model was chosen to make one. Pick a Vosk Model "
            "(Setup → Speech model) — or run Transcraibe first."
        )
    if not Path(model).exists():
        raise SystemExit(f"❌ Vosk model folder not found: {model}")

    from videobeaux.programs.transcraibe import transcribe_single
    print(f"ℹ️  No transcript at {found} — transcribing the clip locally (Vosk)…")
    try:
        transcribe_single(input_video=in_video, model_path=Path(model), json_path=found, emit_txt=False, overwrite=False)
    except Exception as e:
        raise SystemExit(f"❌ Could not transcribe {in_video.name}: {e}")
    if not found.exists():
        raise SystemExit(
            f"❌ No words were found in {in_video.name}, so there is nothing to caption "
            "(no speech, or the Vosk model doesn't match the language)."
        )
    return found


def run(args) -> None:
    transcript = _transcript_for(args)
    print("ℹ️  Burning captions…")
    font_size = int(args.font_size)
    burn_captions(SimpleNamespace(
        input=str(args.input), output=args.output, force=getattr(args, "force", False),
        trans_json=str(transcript), font=args.font,
        # a requested starting size — the renderer shrinks it to fit the video's real width
        font_size=font_size, min_font_size=min(36, font_size),
        words_per_caption=args.words_per_caption, no_uppercase=bool(args.keep_case),
        caption_max_width=args.max_width, caption_max_lines=args.max_lines,
        active_scale=args.highlight_size, vertical_anchor=args.vertical_position,
        primary=args.primary_color, highlight=args.highlight_color, outline=args.outline_color,
        stroke_width=args.outline_width, vcodec="libx264", crf=18, preset="medium",
    ))
    print(f"\n✅ Finished: {args.output}")
