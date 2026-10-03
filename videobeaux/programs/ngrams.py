import json
from collections import Counter
from pathlib import Path
from videogrep import get_ngrams


def register_arguments(parser):
    parser.description = (
        "Lists the most common word sequences (n-grams) spoken in a video's transcript — "
        "useful for finding good search terms before running Grep Supercut.\n"
        "Looks for a transcript JSON next to --input; if none exists, transcribes first "
        "using --stt_model. Writes a ranked JSON list next to --input (or at --output if given)."
    )
    parser.add_argument(
        "--stt_model",
        required=True,
        type=str,
        help="Path to the Vosk model directory, used to transcribe --input if no transcript exists yet."
    )
    parser.add_argument(
        "--n",
        type=int,
        default=2,
        help="N-gram size — 1 for single words, 2 for pairs of words, etc. Default: 2."
    )
    parser.add_argument(
        "--top",
        type=int,
        default=30,
        help="Number of ranked results to keep. Default: 30."
    )


def _sidecar_path(in_path: Path, explicit_out: str | None) -> Path:
    if explicit_out:
        p = Path(explicit_out)
        if p.suffix.lower() != ".json":
            return p.with_suffix(".json")
        return p
    return in_path.with_suffix(in_path.suffix + ".videobeaux.ngrams.json")


def run(args):
    filename = args.input
    in_path = Path(filename)

    transcript_path = in_path.with_suffix(".json")
    if not transcript_path.exists():
        print(f"ℹ️  No transcript found at {transcript_path} — transcribing with Vosk first…")
        try:
            from videobeaux.programs.transcraibe import transcribe_single
            transcribe_single(
                input_video=in_path,
                model_path=Path(args.stt_model),
                json_path=transcript_path,
                emit_txt=False,
                overwrite=False,
            )
        except Exception as e:
            print(f"❌ Could not produce a transcript for {filename}: {e}")
            return e

        if not transcript_path.exists():
            print(f"❌ Transcription did not produce {transcript_path}. Nothing to analyze.")
            return

    try:
        grams = get_ngrams(filename, args.n)
    except Exception as e:
        print(f"❌ videogrep ngram extraction failed: {e}")
        return e

    ranked = Counter(grams).most_common(args.top if args.top and args.top > 0 else None)

    if not ranked:
        print("⚠️  No n-grams found — the transcript may be empty.")
        return

    out_path = _sidecar_path(in_path, getattr(args, 'output', None))
    results = [{"phrase": " ".join(gram), "count": count} for gram, count in ranked]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"🗂  Wrote {len(results)} ranked {args.n}-gram(s) → {out_path}")
    print("\nTop results:")
    for item in results[:10]:
        print(f"  {item['count']:>4}  {item['phrase']}")
