from videobeaux.utils.media import ensure_audio
import json
import re
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace

import requests

from videobeaux.utils.caption_render import burn_captions
from videobeaux.programs.transcraibe import transcribe_single
from videobeaux.utils.ffmpeg_operations import get_video_duration, run_ffmpeg_with_progress
from videobeaux.utils.kokoro import SETUP_HINT, kokoro_command, model_paths, models_present
from videobeaux.utils.script_align import align_script, to_transcript, vosk_words

OLLAMA_URL = "http://localhost:11434/api/chat"

GUI_METADATA = {
    'args': {
        'stt_model': {
            'type': 'file',
            'subtype': 'model',
            'label': 'Vosk Model',
            'help': 'Used to transcribe the synthesized narration.',
        },
        'llm_model': {
            'type': 'file',
            'subtype': 'ollama_model',
            'label': 'Ollama Model (optional)',
            'help': 'Only used with Topic — pick a locally-pulled Ollama model to draft the narration. Leave blank if using Script.',
        },
    }
}


def register_arguments(parser):
    parser.description = (
        "Adds AI-narrated captions to a video. Give it your own narration text with --script — "
        "the default, fully offline path, no service of any kind involved — or a topic with --topic "
        "to draft one via an optional local Ollama model instead. Either way: synthesizes speech "
        "with kokoro-tts, transcribes it locally (Vosk), mixes it over the original audio at a lower "
        "volume, and burns kinetic-typography captions (the actively-spoken word pops larger).\n"
        "With --script, the captions use the words of your script, timed from the narration, so names and "
        "unusual words are spelled as you wrote them. Put <<p:SECONDS>> in the script for silence at that "
        "point, and use --start_delay to hold the narration back from the start of the video.\n"
        "Exactly one of --script or --topic is required."
    )
    parser.add_argument(
        "--script", type=str, default=None,
        help="Your own narration text, used exactly as written. The default, no-setup path — no network/service call happens. "
             "<<p:SECONDS>> inserts silence (e.g. <<p:2>> or <<p:.5>> for half a second)."
    )
    parser.add_argument(
        "--start_delay", type=float, default=0.0,
        help="Seconds of silence before the narration starts, so it begins that long after the video does. Default: 0."
    )
    parser.add_argument(
        "--topic", type=str, default=None,
        help="Alternative to --script: draft narration from a topic via the optional local Ollama path (requires --llm_model)."
    )
    parser.add_argument(
        "--llm_model", type=str, default=None,
        help="Ollama model to use when --topic is given. Ignored when --script is used."
    )
    parser.add_argument(
        "--duration", type=float, default=30.0,
        help="Target narration length in seconds — only steers Ollama generation when --topic is used. Default: 30."
    )
    parser.add_argument(
        "--voice", type=str, default="am_adam",
        help="kokoro-tts voice name. Default: am_adam."
    )
    parser.add_argument(
        "--voice_speed", type=float, default=1.0,
        help="kokoro-tts speech speed multiplier. Default: 1.0."
    )
    parser.add_argument(
        "--stt_model", required=True, type=str,
        help="Path to the Vosk model directory, used to transcribe the synthesized narration."
    )
    parser.add_argument(
        "--original_volume", type=float, default=0.2,
        help="Background volume of the original audio under the narration, 0-1. Default: 0.2."
    )
    parser.add_argument(
        "--font", type=str, default="Arial",
        help="Caption font name (or a path to a .ttf/.otf file). Default: Arial."
    )
    parser.add_argument(
        "--font_size", type=int, default=76,
        help="Requested caption font size in px — auto-shrunk as needed to fit the frame. Default: 76."
    )
    parser.add_argument(
        "--primary_color", type=str, default="#FFFFFF",
        help="Color of words that aren't currently being spoken. Default: #FFFFFF (white)."
    )
    parser.add_argument(
        "--highlight_color", type=str, default="#FFE128",
        help="Color of the word currently being spoken. Default: #FFE128 (gold)."
    )
    parser.add_argument(
        "--outline_color", type=str, default="#000000",
        help="Caption text outline color. Default: #000000 (black)."
    )


def _generate_script_via_ollama(topic, duration, model):
    prompt = f"""
Write narration for a short-form video.

TOPIC:
{topic}

TARGET LENGTH:
{duration} seconds

STYLE:
- conversational
- immediate hook
- short sentences
- no introduction
- no "welcome back"
- avoid hashtags
- avoid stage directions
- narration only
- build curiosity
- strong final sentence

Assume approximately 2.5 spoken words per second.

Return ONLY the narration.
"""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
            timeout=300,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise SystemExit(
            f"❌ Could not reach Ollama at {OLLAMA_URL} ({e}). Ollama is optional — start it "
            f"(Setup → Optional features shows its status), or use --script to provide your own "
            f"narration text instead, no Ollama needed."
        )
    return response.json()["message"]["content"].strip()


# <<p:2>> in a script is two seconds of silence at that point; <<p:.5>> and <<p:0.5>> are half a second.
PAUSE_RE = re.compile(r"<<\s*p\s*:\s*(\d+\.?\d*|\.\d+)\s*>>", re.IGNORECASE)
KOKORO_RATE = 24000


def split_script(script, start_delay=0.0):
    """
    The narration as an ordered list: ("text", str) to speak and ("pause", seconds) of silence.
    A <<p:N>> marker is N seconds of silence where it sits; start_delay is silence before everything.
    """
    for marker in re.findall(r"<<.*?>>", script):
        if not PAUSE_RE.fullmatch(marker):
            raise SystemExit(
                f"❌ Unknown marker {marker} in the script. The only marker is <<p:SECONDS>>, e.g. <<p:2>> or <<p:.5>>."
            )
    items = [("pause", start_delay)] if start_delay > 0 else []
    pos = 0
    for m in PAUSE_RE.finditer(script):
        items.append(("text", script[pos:m.start()]))
        items.append(("pause", float(m.group(1))))
        pos = m.end()
    items.append(("text", script[pos:]))
    return [
        (kind, value.strip() if kind == "text" else value)
        for kind, value in items
        if (kind == "text" and value.strip()) or (kind == "pause" and value > 0)
    ]


def _join_narration(items, tmp, speak):
    """
    Speak each text part with speak(text_file, wav), then join the parts and their pauses into one wav. The pauses are
    real silence in that wav, so Vosk's timings (and the captions) already include them.
    """
    inputs, chains = [], []
    wav = None
    for n, (kind, value) in enumerate(items):
        if kind == "text":
            text_file, wav = tmp / f"part_{n:03d}.txt", tmp / f"part_{n:03d}.wav"
            text_file.write_text(value, encoding="utf-8")
            speak(text_file, wav)
            inputs += ["-i", str(wav)]
        else:
            inputs += ["-f", "lavfi", "-t", f"{value:.3f}", "-i", f"anullsrc=r={KOKORO_RATE}:cl=mono"]
        chains.append(f"[{n}:a]aformat=sample_rates={KOKORO_RATE}:channel_layouts=mono[p{n}]")
    if len(items) == 1:
        return wav
    out = tmp / "narration.wav"
    labels = "".join(f"[p{n}]" for n in range(len(items)))
    filter_complex = ";".join(chains) + f";{labels}concat=n={len(items)}:v=0:a=1[out]"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", filter_complex,
             "-map", "[out]", "-c:a", "pcm_s16le", str(out)],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise SystemExit(f"❌ Joining the narration with its pauses failed: {e}")
    return out


def _script_captions(script, vosk_json, narration_wav, tmp):
    """
    The transcript the captions are drawn from: the script's own words, timed by Vosk's word timings. When Vosk
    heard none of the script's words, the script is spread evenly over the narration instead, so the captions
    still read as the script.
    """
    heard = vosk_words(vosk_json) if vosk_json.exists() else []
    words, matched = align_script(script, heard, duration=get_video_duration(str(narration_wav)))
    if matched == 0:
        print("⚠️  Vosk heard none of the script's words, so the script is timed evenly over the narration.")
    else:
        print(f"ℹ️  Timed {matched} of {len(words)} script words from the narration.")
    out = tmp / "narration_script.json"
    out.write_text(json.dumps(to_transcript(words), ensure_ascii=False), encoding="utf-8")
    return out


def run(args):
    # audio filter graphs need an audio track on every input
    if getattr(args, 'input', None):
        args.input = ensure_audio(args.input)
    if bool(args.script) == bool(args.topic):
        raise SystemExit(
            "❌ Provide exactly one of --script (your own narration text — works fully offline) "
            "or --topic (drafts narration via the optional local Ollama path)."
        )
    if args.topic and not args.llm_model:
        raise SystemExit(
            "❌ --topic requires --llm_model (pick a locally-pulled Ollama model). "
            "Or skip Ollama entirely by using --script instead."
        )

    # All argument-level validation is done before touching the filesystem
    # for external-tool availability, so a bad invocation fails fast and
    # cheaply rather than after a "kokoro-tts not found" detour.
    kokoro = kokoro_command()
    if kokoro is None:
        raise SystemExit(
            "❌ The narration voice (kokoro-tts) isn't installed. " + SETUP_HINT
        )
    kokoro_model, kokoro_voices = model_paths()
    have_models = models_present()
    if not have_models and not (Path("kokoro-v1.0.onnx").exists() and Path("voices-v1.0.bin").exists()):
        raise SystemExit(
            "❌ The narration voice models haven't been downloaded yet (~335 MB, one time). " + SETUP_HINT
        )

    if args.script:
        script = args.script.strip()
    else:
        print(f"ℹ️  Drafting narration for topic {args.topic!r} via Ollama ({args.llm_model})…")
        script = _generate_script_via_ollama(args.topic, args.duration, args.llm_model)
        print("\n--- Generated script ---")
        print(script)
        print("-------------------------\n")

    if not script:
        raise SystemExit("❌ Narration script is empty. Nothing to narrate.")
    if args.start_delay < 0:
        raise SystemExit("❌ --start_delay can't be negative.")
    items = split_script(script, args.start_delay)
    if not any(kind == "text" for kind, _ in items):
        raise SystemExit("❌ The script has only pause markers and nothing to say.")
    spoken = PAUSE_RE.sub(" ", script)   # the words the captions are drawn from: the script without its markers

    with tempfile.TemporaryDirectory(prefix="videobeaux_narrate_") as tmp_str:
        tmp = Path(tmp_str)

        def speak(text_file, wav):
            kokoro_cmd = [
                *kokoro, str(text_file), str(wav),
                "--voice", args.voice, "--speed", str(args.voice_speed), "--lang", "en-us",
            ]
            if have_models:
                kokoro_cmd += ["--model", str(kokoro_model), "--voices", str(kokoro_voices)]
            try:
                subprocess.run(kokoro_cmd, check=True)
            except subprocess.CalledProcessError as e:
                raise SystemExit(f"❌ kokoro-tts failed: {e}")

        print("ℹ️  Synthesizing narration with kokoro-tts…")
        narration_wav = _join_narration(items, tmp, speak)

        transcript_path = tmp / "narration.json"
        print("ℹ️  Transcribing narration locally (Vosk)…")
        transcribe_single(
            input_video=narration_wav,
            model_path=Path(args.stt_model),
            json_path=transcript_path,
            emit_txt=False,
            overwrite=True,
        )

        mixed_path = tmp / "mixed.mp4"
        filter_complex = (
            f"[0:a]volume={args.original_volume}[orig];"
            f"[1:a]volume=1.0[voice];"
            f"[orig][voice]amix=inputs=2:duration=first:normalize=0[aout]"
        )
        mix_command = [
            "ffmpeg", "-y",
            "-i", args.input,
            "-i", str(narration_wav),
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(mixed_path),
        ]
        print("ℹ️  Mixing narration over original audio…")
        run_ffmpeg_with_progress(mix_command, args.input, mixed_path)

        print("ℹ️  Burning captions…")
        cap_ns = SimpleNamespace(
            input=str(mixed_path),
            output=args.output,
            force=getattr(args, 'force', False),
            trans_json=str(_script_captions(spoken, transcript_path, narration_wav, tmp)),
            caption=None,
            font=args.font,
            # A requested starting size, not a guaranteed final one — the caption renderer
            # auto-shrinks this as needed to keep every line within the video's
            # actual width (real pixel measurement, not a guess).
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
        )
        burn_captions(cap_ns)

    print(f"\n✅ Finished: {args.output}")
