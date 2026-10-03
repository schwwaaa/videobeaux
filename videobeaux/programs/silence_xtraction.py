from pathlib import Path
from videogrep import parse_transcript
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_supercut
import sys

GUI_METADATA = {
    'args': {
        'stt_model': {
            'type': 'file',
            'subtype': 'model',
            'label': 'Vosk Model',
            'help': 'Used to transcribe the video first, if no transcript for it exists yet.',
        },
    }
}

def register_arguments(parser):
    parser.description = (
        "Identifies instances of speech, per a transcript's timestamps, and removes those portions of the video. \n"
        "The output will be what's left. Not exactly silence, but no discernable words. \n"
        "Looks for a transcript JSON next to --input (same name, same directory, matching --program transcraibe's "
        "own convention); if none exists yet, transcribes it first using --stt_model."
    )
    parser.add_argument(
        "--stt_model",
        required=True,
        type=str,
        help="Path to the Vosk model directory, used to transcribe --input if no transcript exists yet."
    )
    parser.add_argument(
        "--min_d",
        required=True,
        type=float,
        help=(
            "Minimum duration (in seconds) of a silence to consider."
        )
    )
    parser.add_argument(
        "--max_d",
        required=True,
        type=float,
        help=(
            "Maximum duration (in seconds) of a silence to consider."
        )
    )
    parser.add_argument(
        "--adjuster",
        required=True,
        type=float,
        help=(
            "Adjustment offset (seconds) to shorten the silence from the end."
            "Anecdotally, the closer to 0, the more gutteral speech non-word sounds are included."
        )
    )

def run(args):
    filename = args.input

    # videogrep's parse_transcript looks for a JSON with the same name as the
    # input, in the same directory. Transcribe on the spot if it's not there
    # yet — this also makes standalone GUI use work, since the pipeline's
    # temp intermediate files never have a pre-existing matching transcript.
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
            print(f"❌ Transcription did not produce {transcript_path} (no speech found?). Nothing to extract.")
            return

    silences = []
    try:
        timestamps = parse_transcript(filename)
        words = []
        for sentence in timestamps:
            words += sentence['words']
        for word1, word2 in zip(words[:-1], words[1:]):
            start = word1['end']
            end = word2['start'] - args.adjuster
            duration = end - start
            if duration > args.min_d and duration < args.max_d:
                silences.append({'start': start, 'end': end, 'file': filename})

        if not silences:
            print(f"⚠️  No qualifying silences found between {args.min_d}s and {args.max_d}s. Nothing to extract.")
            return

        try:
            run_ffmpeg_supercut(silences, filename, args.output, force=getattr(args, 'force', False))
        except Exception as e:
            print(f"❌ Could not build the supercut: {e}")
            return e

    except Exception as e:
        print(f"❌ videogrep parse_transcript failed on {transcript_path}: {e}")
        return e
