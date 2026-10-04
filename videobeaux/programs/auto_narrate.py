from videobeaux.utils.media import ensure_audio
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace

import requests

from videobeaux.programs import kinetic_captions
from videobeaux.programs.transcraibe import transcribe_single
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.kokoro import SETUP_HINT, kokoro_command, model_paths, models_present

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
        "Exactly one of --script or --topic is required."
    )
    parser.add_argument(
        "--script", type=str, default=None,
        help="Your own narration text, used exactly as written. The default, no-setup path — no network/service call happens."
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

    with tempfile.TemporaryDirectory(prefix="videobeaux_narrate_") as tmp_str:
        tmp = Path(tmp_str)

        script_file = tmp / "narration.txt"
        script_file.write_text(script, encoding="utf-8")

        narration_wav = tmp / "narration.wav"
        print("ℹ️  Synthesizing narration with kokoro-tts…")
        kokoro_cmd = [
            *kokoro, str(script_file), str(narration_wav),
            "--voice", args.voice, "--speed", str(args.voice_speed), "--lang", "en-us",
        ]
        if have_models:
            kokoro_cmd += ["--model", str(kokoro_model), "--voices", str(kokoro_voices)]
        try:
            subprocess.run(kokoro_cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise SystemExit(f"❌ kokoro-tts failed: {e}")

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
            trans_json=str(transcript_path),
            caption=None,
            font=args.font,
            # A requested starting size, not a guaranteed final one — kinetic_captions
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
        kinetic_captions.run(cap_ns)

    print(f"\n✅ Finished: {args.output}")
