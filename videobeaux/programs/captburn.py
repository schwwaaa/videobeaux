"""
captburn — burn the clip's own speech onto the picture as kinetic captions.

Works like Auto Narrate, minus the script and the synthetic voice: the words on screen are the words in the clip. It
looks for a transcript next to the input (`<input>.json`); if there isn't one it transcribes the clip locally with Vosk
first (and saves it there, so the next run — or Grep Supercut, Ngrams … — reuses it). The captions are the same
kinetic-typography style as Auto Narrate: short bursts of words, the word being spoken pops larger and takes the highlight
colour, font size shrinks to fit the frame. The original audio is kept untouched.

(The previous ASS/libass-based captburn, with pop-on / paint-on styles and exact placement, is kept in
experimental/captburn-ass-module.py.)
"""
from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace

from videobeaux.programs import kinetic_captions

GUI_METADATA = {
    'args': {
        'stt_model': {
            'type': 'file',
            'subtype': 'model',
            'label': 'Vosk Model',
            'help': 'Used to transcribe the clip first, if no transcript (<input>.json) exists yet.',
        },
        'trans_json': {'hidden': True},
    }
}


def register_arguments(parser: argparse.ArgumentParser):
    parser.description = (
        "Burns the clip's own speech onto the video as kinetic-typography captions (the actively-spoken word pops "
        "larger), exactly like Auto Narrate's captions but using what is said in the clip instead of a narration. "
        "Uses <input>.json if it exists; otherwise transcribes locally (Vosk) first and saves it there."
    )
    parser.add_argument(
        "--stt_model", type=str, default=None,
        help="Path to the Vosk model directory — used to transcribe the clip when no transcript exists yet."
    )
    parser.add_argument("--font", type=str, default="Arial",
                        help="Caption font name (or a path to a .ttf/.otf file). Default: Arial.")
    parser.add_argument("--font_size", type=int, default=76,
                        help="Requested caption font size in px — auto-shrunk as needed to fit the frame. Default: 76.")
    parser.add_argument("--primary_color", type=str, default="#FFFFFF",
                        help="Color of words that aren't currently being spoken. Default: #FFFFFF (white).")
    parser.add_argument("--highlight_color", type=str, default="#FFE128",
                        help="Color of the word currently being spoken. Default: #FFE128 (gold).")
    parser.add_argument("--outline_color", type=str, default="#000000",
                        help="Caption text outline color. Default: #000000 (black).")
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
    kinetic_captions.run(SimpleNamespace(
        input=str(args.input),
        output=args.output,
        force=getattr(args, "force", False),
        trans_json=str(transcript),
        caption=None,
        font=args.font,
        # a requested starting size — kinetic_captions shrinks it to fit the video's real width
        font_size=args.font_size,
        min_font_size=36,
        words_per_caption=4,
        no_uppercase=False,
        caption_max_width=0.86,
        caption_max_lines=2,
        active_scale=1.18,
        vertical_anchor=0.67,
        primary=args.primary_color,
        highlight=args.highlight_color,
        outline=args.outline_color,
        stroke_width=8,
        vcodec="libx264",
        crf=18,
        preset="medium",
    ))
    print(f"\n✅ Finished: {args.output}")
