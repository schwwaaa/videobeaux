from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from pathlib import Path
import sys

RATES = ["22050", "32000", "44100", "48000"]
CHANNELS = ["Stereo", "Mono"]

GUI_METADATA = {
    'args': {
        'sample_rate': {'type': 'select', 'label': 'Sample rate (Hz)', 'default': '44100', 'choices': RATES,
                        'help': '44100 = CD quality (default) · 48000 = video standard · 22050 = small voice-only files.'},
        'channels': {'type': 'select', 'label': 'Channels', 'default': 'Stereo', 'choices': CHANNELS,
                     'help': 'Mono mixes both channels into one (half the size).'},
    },
}

def register_arguments(parser):
    parser.description = (
        "Extracts the audio as a .wav file from the --input video file."
    )
    parser.add_argument("--sample_rate", choices=RATES, default="44100", help="Sample rate in Hz. Default: 44100.")
    parser.add_argument("--channels", choices=CHANNELS, default="Stereo", help="Stereo (default) or Mono.")

def run(args):
    output_path = Path(args.output)
    clean_output = output_path.with_suffix(f".wav")
    if clean_output.exists() and not args.force:
        print(f"❌ {clean_output} already exists. Use --force to overwrite.")
        sys.exit(1)
    command = [
        "ffmpeg",
        "-i", args.input,
        "-vn", 
        "-acodec", "pcm_s16le",
        "-ar", str(getattr(args, "sample_rate", "44100")),
        "-ac", "1" if getattr(args, "channels", "Stereo") == "Mono" else "2",
        clean_output
    ]
    
    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, clean_output)
