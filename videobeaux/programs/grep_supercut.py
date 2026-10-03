import random
import re
from pathlib import Path
from videogrep import search, pad_and_sync
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_supercut


GUI_METADATA = {
    'args': {
        'stt_model': {
            'type': 'file',
            'subtype': 'model',
            'label': 'Vosk Model',
            'help': 'Used to transcribe the video first, if no transcript for it exists yet.',
        },
        'whole_word': {
            'type': 'checkbox',
            'label': 'Whole Word Only',
            'help': 'Match "cut" as a whole word only — turn off to search as a raw regex/substring (e.g. "cut.*ing").',
        },
        'randomize': {
            'type': 'checkbox',
            'label': 'Randomize order',
            'help': 'Shuffle the matched clips before assembling the supercut.',
        },
    }
}


def _whole_word_wrap(query: str) -> str:
    """
    Turn a plain query into a whole-word-anchored regex, one word at a time.
    videogrep's own fragment-mode search splits each query on spaces before
    matching each token against a single transcript word — wrapping the
    whole phrase in one pair of \\b...\\b wouldn't survive that internal
    split, so each word gets its own boundary instead. re.escape guards
    against a plain word containing regex-special characters.
    """
    words = query.split()
    if not words:
        return query
    return " ".join(rf"\b{re.escape(w)}\b" for w in words)


def register_arguments(parser):
    parser.description = (
        "Searches a video's transcript for a word, phrase, or regular expression and cuts "
        "together every match — the classic \"videogrep\": find every time someone says X.\n"
        "--search_type sentence: whole matching sentences. fragment: just the matched phrase, "
        "at word-level precision. mash: picks one random occurrence of each query word and "
        "stitches them together.\n"
        "Looks for a transcript JSON next to --input; if none exists, transcribes first "
        "using --stt_model."
    )
    parser.add_argument(
        "--stt_model",
        required=True,
        type=str,
        help="Path to the Vosk model directory, used to transcribe --input if no transcript exists yet."
    )
    parser.add_argument(
        "--query",
        required=True,
        type=str,
        help="Search term(s), as plain text or a regular expression. Comma-separated for multiple queries."
    )
    parser.add_argument(
        "--search_type",
        choices=["sentence", "fragment", "mash"],
        default="sentence",
        help="sentence: whole matching lines. fragment: exact matched phrase span. mash: random-shuffled word mashup."
    )
    parser.add_argument(
        "--padding",
        type=float,
        default=0.0,
        help="Seconds of padding added before and after each matched clip. Default: 0."
    )
    parser.add_argument(
        "--max_clips",
        type=int,
        default=0,
        help="Maximum number of matched clips to use (0 = unlimited)."
    )
    parser.add_argument(
        "--randomize",
        action="store_true",
        help="Shuffle the matched clips before assembling the supercut."
    )
    parser.add_argument(
        "--whole_word",
        action="store_true",
        help="Match each query as a whole word, not a substring (e.g. \"cut\" won't match inside "
             "\"executioner\"). Disable for raw regex/substring search. The GUI defaults this on; "
             "plain CLI use defaults off unless passed explicitly."
    )


def run(args):
    filename = args.input

    transcript_path = Path(filename).with_suffix(".json")
    if not transcript_path.exists():
        print(f"ℹ️  No transcript found at {transcript_path} — transcribing with Vosk first…")
        try:
            from videobeaux.programs.transcraibe import transcribe_single
            transcribe_single(
                input_video=Path(filename),
                model_path=Path(args.stt_model),
                json_path=transcript_path,
                emit_txt=False,
                overwrite=False,
            )
        except Exception as e:
            print(f"❌ Could not produce a transcript for {filename}: {e}")
            return e

        if not transcript_path.exists():
            print(f"❌ Transcription did not produce {transcript_path}. Nothing to search.")
            return

    queries = [q.strip() for q in args.query.split(",") if q.strip()]
    if not queries:
        print("❌ --query is empty after parsing. Nothing to search for.")
        return

    display_queries = ", ".join(repr(q) for q in queries)

    # mash mode matches transcript words by exact equality, not regex — a
    # \bword\b wrapper would never equal a real word and would silently zero
    # out every result, so whole-word wrapping only applies to sentence/fragment.
    search_queries = queries
    if args.whole_word and args.search_type != "mash":
        search_queries = [_whole_word_wrap(q) for q in queries]

    try:
        segments = search(filename, search_queries, search_type=args.search_type)
    except Exception as e:
        print(f"❌ videogrep search failed: {e}")
        return e

    if not segments:
        print(f"⚠️  No matches found for {display_queries} ({args.search_type} mode). Nothing to extract.")
        return

    segments = pad_and_sync(segments, padding=args.padding)

    if args.randomize:
        random.shuffle(segments)

    if args.max_clips and args.max_clips > 0:
        segments = segments[:args.max_clips]

    print(f"ℹ️  {len(segments)} matching clip(s) found for {display_queries} ({args.search_type} mode).")

    try:
        run_ffmpeg_supercut(segments, filename, args.output, force=getattr(args, 'force', False))
    except Exception as e:
        print(f"❌ Could not build the supercut: {e}")
        return e
