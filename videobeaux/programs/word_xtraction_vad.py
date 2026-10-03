from pathlib import Path
from videogrep import parse_transcript
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_supercut
import subprocess
import tempfile
import wave
import numpy as np


GUI_METADATA = {
    'args': {
        'stt_model': {
            'type': 'file',
            'subtype': 'model',
            'label': 'Vosk Model',
            'help': 'Used to transcribe the video first, if no transcript for it exists yet.',
        },
        'keep_nonspeech': {
            'type': 'checkbox',
            'label': 'Keep non-speech sounds',
            'help': 'Keep regions outside speech detected by Vosk and/or Silero VAD.',
        },
        'use_vad': {
            'type': 'checkbox',
            'label': 'Use Silero VAD',
            'help': 'Locally detect speech even when Vosk cannot recognize the words.',
        },
    }
}


def register_arguments(parser):
    parser.description = (
        "Extracts portions of a video that do not contain speech.\n"
        "With --keep_nonspeech, recognized Vosk words become speech exclusion zones. "
        "With --use_vad, local Silero VAD speech detections are added to those zones, "
        "which helps catch intelligible speech masked by applause, music, crowd noise, etc. "
        "Use --vad_keep_short to preserve brief VAD-only vocal texture such as ums, uhs, "
        "grunts, breaths, and small reactions.\n"
        "The VAD runs locally; no API/service is used at runtime.\n"
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
        "--min_d",
        required=True,
        type=float,
        help="Minimum duration (seconds) of a kept non-speech region."
    )
    parser.add_argument(
        "--max_d",
        required=True,
        type=float,
        help=(
            "Maximum duration (seconds) of a kept region. "
            "With --keep_nonspeech, use 0 or a negative value for no maximum."
        )
    )
    parser.add_argument(
        "--adjuster",
        required=True,
        type=float,
        help=(
            "Legacy-mode offset (seconds) that shortens a gap from the end. "
            "Ignored when --keep_nonspeech is enabled; use --speech_pad there instead."
        )
    )
    parser.add_argument(
        "--keep_nonspeech",
        action="store_true",
        help=(
            "Keep all regions outside recognized speech, including material before the first "
            "word and after the last word. This is the preferred mode for retaining applause, "
            "laughter, music, ambience, and noise."
        )
    )
    parser.add_argument(
        "--max_word_d",
        type=float,
        default=1.5,
        help=(
            "In --keep_nonspeech mode, maximum believable duration of a single recognized word "
            "before it is treated as a suspicious Vosk timestamp. Suspicious words are clamped "
            "to this many seconds at the END of their reported span. Default: 1.5."
        )
    )
    parser.add_argument(
        "--speech_pad",
        type=float,
        default=0.08,
        help=(
            "Seconds of padding added before and after each recognized word in --keep_nonspeech "
            "mode, to avoid leaving clipped syllables. Default: 0.08."
        )
    )
    parser.add_argument(
        "--merge_gap",
        type=float,
        default=0.20,
        help=(
            "Merge neighboring speech regions separated by this many seconds or less. "
            "This prevents tiny between-word gaps from becoming clips. Default: 0.20."
        )
    )


    parser.add_argument(
        "--use_vad",
        action="store_true",
        help="Use local Silero VAD in addition to Vosk word timestamps."
    )
    parser.add_argument(
        "--vad_threshold",
        type=float,
        default=0.45,
        help="Silero speech probability threshold. Lower is more aggressive. Default: 0.45."
    )
    parser.add_argument(
        "--vad_min_speech",
        type=int,
        default=150,
        help="Minimum detected speech duration in milliseconds. Default: 150."
    )
    parser.add_argument(
        "--vad_min_silence",
        type=int,
        default=120,
        help="Minimum silence duration in milliseconds before splitting speech. Default: 120."
    )
    parser.add_argument(
        "--vad_pad",
        type=int,
        default=120,
        help="Padding around each VAD speech region in milliseconds. Default: 120."
    )
    parser.add_argument(
        "--vad_keep_short",
        type=float,
        default=0.40,
        help=(
            "Preserve VAD-only vocal events at or below this duration in seconds, such as "
            "short ums, uhs, grunts, breaths, and vocal reactions. Vosk-recognized words are "
            "still removed even when shorter than this. Use 0 to disable. Default: 0.40."
        )
    )


def _get_video_duration(filename):
    """Return media duration in seconds using ffprobe."""
    command = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(filename),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def _duration_allowed(duration, min_d, max_d, allow_unlimited_max=False):
    if duration <= min_d:
        return False
    if allow_unlimited_max and max_d <= 0:
        return True
    return duration < max_d


def _flatten_words(timestamps):
    words = []
    for sentence in timestamps:
        words.extend(sentence.get('words', []))
    return words


def _repair_word_interval(word, max_word_d):
    """
    Return (start, end, repaired).

    Vosk can occasionally report a single word spanning many seconds of applause,
    music, noise, etc. In the observed failure mode, the actual word tends to occur
    near the END of that span, immediately before the next word. Rather than treating
    the whole multi-second range as speech, clamp suspicious words to max_word_d
    seconds ending at their reported end timestamp.
    """
    start = float(word['start'])
    end = float(word['end'])

    if end < start:
        start, end = end, start

    repaired = False
    if max_word_d > 0 and (end - start) > max_word_d:
        start = max(0.0, end - max_word_d)
        repaired = True

    return start, end, repaired


def _build_speech_regions(words, duration, max_word_d, speech_pad, merge_gap):
    regions = []
    repaired_count = 0

    for word in words:
        try:
            start, end, repaired = _repair_word_interval(word, max_word_d)
        except (KeyError, TypeError, ValueError):
            continue

        if repaired:
            repaired_count += 1

        start = max(0.0, start - speech_pad)
        end = min(duration, end + speech_pad)

        if end > start:
            regions.append([start, end])

    regions.sort(key=lambda item: item[0])

    merged = []
    for start, end in regions:
        if not merged or start > merged[-1][1] + merge_gap:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)

    return merged, repaired_count


def _merge_regions(regions, merge_gap=0.0, duration=None):
    cleaned = []
    for start, end in regions:
        start = float(start)
        end = float(end)
        if duration is not None:
            start = max(0.0, min(start, duration))
            end = max(0.0, min(end, duration))
        if end > start:
            cleaned.append([start, end])

    cleaned.sort(key=lambda item: item[0])
    merged = []
    for start, end in cleaned:
        if not merged or start > merged[-1][1] + merge_gap:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return merged


def _extract_vad_audio(filename, wav_path):
    """Extract mono 16 kHz PCM WAV for Silero using the local ffmpeg binary."""
    command = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(filename),
        "-vn", "-ac", "1", "-ar", "16000",
        "-c:a", "pcm_s16le",
        str(wav_path),
    ]
    subprocess.run(command, check=True)


def _build_vad_regions(filename, duration, threshold, min_speech_ms, min_silence_ms, pad_ms):
    """Run Silero VAD locally and return [[start_seconds, end_seconds], ...]."""
    try:
        from silero_vad import load_silero_vad, get_speech_timestamps
        import torch
    except ImportError as e:
        raise RuntimeError(
            "Silero VAD is not installed. Install it in Videobeaux's Python environment with: "
            "python -m pip install silero-vad"
        ) from e

    with tempfile.TemporaryDirectory(prefix="videobeaux_vad_") as temp_dir:
        wav_path = Path(temp_dir) / "vad_audio.wav"
        _extract_vad_audio(filename, wav_path)

        model = load_silero_vad(onnx=False)

        # Read the FFmpeg-produced PCM WAV ourselves instead of silero_vad.read_audio().
        # This avoids torchaudio/torchcodec entirely and keeps the VAD pipeline local.
        with wave.open(str(wav_path), "rb") as wf:
            if wf.getnchannels() != 1:
                raise RuntimeError(f"Expected mono VAD audio, got {wf.getnchannels()} channels")
            if wf.getframerate() != 16000:
                raise RuntimeError(f"Expected 16 kHz VAD audio, got {wf.getframerate()} Hz")
            if wf.getsampwidth() != 2:
                raise RuntimeError(f"Expected 16-bit PCM VAD audio, got {wf.getsampwidth() * 8}-bit")
            pcm = wf.readframes(wf.getnframes())

        audio_np = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
        wav = torch.from_numpy(audio_np)
        timestamps = get_speech_timestamps(
            wav,
            model,
            sampling_rate=16000,
            threshold=float(threshold),
            min_speech_duration_ms=int(min_speech_ms),
            min_silence_duration_ms=int(min_silence_ms),
            speech_pad_ms=int(pad_ms),
            return_seconds=True,
        )

    regions = []
    for item in timestamps:
        try:
            start = float(item["start"])
            end = float(item["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if end > start:
            regions.append([max(0.0, start), min(duration, end)])

    return _merge_regions(regions, merge_gap=0.0, duration=duration)


def _filter_short_vad_regions(vad_regions, keep_short_seconds):
    """
    Remove short VAD-only detections from the speech exclusion list.

    This intentionally preserves brief human vocal texture (ums, uhs, grunts, breaths,
    small reactions) when Silero detects it but Vosk did not recognize a word there.
    Vosk regions are handled separately and are always kept as speech exclusions.
    """
    if keep_short_seconds <= 0:
        return vad_regions, []

    kept_as_speech = []
    preserved_vocal = []
    for start, end in vad_regions:
        if (end - start) <= keep_short_seconds:
            preserved_vocal.append([start, end])
        else:
            kept_as_speech.append([start, end])

    return kept_as_speech, preserved_vocal


def _invert_regions(speech_regions, duration, filename, min_d, max_d):
    """Return the complement of speech_regions across 0..duration."""
    kept = []
    cursor = 0.0

    for speech_start, speech_end in speech_regions:
        if speech_start > cursor:
            gap_start = cursor
            gap_end = speech_start
            gap_duration = gap_end - gap_start
            if _duration_allowed(gap_duration, min_d, max_d, allow_unlimited_max=True):
                kept.append({'start': gap_start, 'end': gap_end, 'file': filename})
        cursor = max(cursor, speech_end)

    # Crucial difference from the old algorithm: include the tail after the last word.
    if cursor < duration:
        gap_start = cursor
        gap_end = duration
        gap_duration = gap_end - gap_start
        if _duration_allowed(gap_duration, min_d, max_d, allow_unlimited_max=True):
            kept.append({'start': gap_start, 'end': gap_end, 'file': filename})

    return kept


def _legacy_word_gaps(words, filename, min_d, max_d, adjuster):
    """Original behavior, with the final adjacent word pair bug fixed."""
    silences = []

    # words[:-1], not words[:-2], so the final adjacent pair is included.
    for word1, word2 in zip(words[:-1], words[1:]):
        start = float(word1['end'])
        end = float(word2['start']) - adjuster
        duration = end - start
        if _duration_allowed(duration, min_d, max_d):
            silences.append({'start': start, 'end': end, 'file': filename})

    return silences


def run(args):
    filename = args.input

    # videogrep's parse_transcript looks for a JSON with the same name as the
    # input, in the same directory. Transcribe on the spot if it's not there.
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
            print(f"❌ Transcription did not produce {transcript_path}. Nothing to extract.")
            return

    try:
        timestamps = parse_transcript(filename)
        words = _flatten_words(timestamps)

        if args.keep_nonspeech:
            try:
                duration = _get_video_duration(filename)
            except Exception as e:
                print(f"❌ Could not determine video duration with ffprobe: {e}")
                return e

            if not words:
                # No recognized words means the entire file is non-speech.
                nonspeech = []
                if _duration_allowed(duration, args.min_d, args.max_d, allow_unlimited_max=True):
                    nonspeech.append({'start': 0.0, 'end': duration, 'file': filename})
                repaired_count = 0
                speech_regions = []
            else:
                speech_regions, repaired_count = _build_speech_regions(
                    words=words,
                    duration=duration,
                    max_word_d=args.max_word_d,
                    speech_pad=args.speech_pad,
                    merge_gap=args.merge_gap,
                )

            vad_regions = []
            if args.use_vad:
                try:
                    print("ℹ️  Running local Silero VAD…")
                    vad_regions = _build_vad_regions(
                        filename=filename,
                        duration=duration,
                        threshold=args.vad_threshold,
                        min_speech_ms=args.vad_min_speech,
                        min_silence_ms=args.vad_min_silence,
                        pad_ms=args.vad_pad,
                    )
                    print(f"ℹ️  Silero VAD found {len(vad_regions)} raw speech regions.")

                    vad_regions, preserved_vocal_regions = _filter_short_vad_regions(
                        vad_regions,
                        args.vad_keep_short,
                    )

                    if args.vad_keep_short > 0:
                        print(
                            f"ℹ️  Vocal-texture filter preserved {len(preserved_vocal_regions)} "
                            f"VAD-only regions ≤ {args.vad_keep_short:.2f}s; "
                            f"{len(vad_regions)} longer VAD regions remain speech exclusions."
                        )
                except Exception as e:
                    print(f"❌ Silero VAD failed: {e}")
                    return e

            # Union Vosk transcript speech with the remaining VAD speech.
            # Short VAD-only events can be intentionally preserved, but any speech Vosk
            # actually recognized remains excluded regardless of its duration.
            speech_regions = _merge_regions(
                speech_regions + vad_regions,
                merge_gap=args.merge_gap,
                duration=duration,
            )

            nonspeech = _invert_regions(
                speech_regions=speech_regions,
                duration=duration,
                filename=filename,
                min_d=args.min_d,
                max_d=args.max_d,
            )

            print(
                f"ℹ️  Non-speech mode: {len(words)} recognized words, "
                f"{len(speech_regions)} merged Vosk/VAD speech regions, "
                f"{repaired_count} suspicious long word timestamps repaired."
            )

            if args.max_d <= 0:
                max_desc = "no maximum"
            else:
                max_desc = f"{args.max_d}s"

            print(
                f"ℹ️  Keeping {len(nonspeech)} non-speech regions "
                f"(min {args.min_d}s, max {max_desc})."
            )
            clips = nonspeech

        else:
            clips = _legacy_word_gaps(
                words=words,
                filename=filename,
                min_d=args.min_d,
                max_d=args.max_d,
                adjuster=args.adjuster,
            )

        if not clips:
            print("⚠️  No qualifying regions found. Nothing to extract.")
            return

        try:
            run_ffmpeg_supercut(clips, filename, args.output, force=getattr(args, 'force', False))
        except Exception as e:
            print(f"❌ Could not build the supercut: {e}")
            return e

    except Exception as e:
        print(f"❌ videogrep parse_transcript failed on {transcript_path}: {e}")
        return e
