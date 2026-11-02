"""
audio_denoise: takes the hiss and hum out of speech. A high-pass cuts the rumble below the voice, then ffmpeg's FFT
denoiser (afftdn) lowers the background noise it finds. The picture is copied untouched.
"""
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.media import has_audio

GUI_METADATA = {
    'args': {
        'reduction': {'label': 'Reduce noise by (dB)', 'min': 0, 'max': 40, 'good_min': 6, 'good_max': 20,
                      'help': 'How far the noise is pushed down. More cleans more, but a voice can start to sound watery.'},
        'noise_floor': {'label': 'Noise floor (dB)', 'min': -80, 'max': -20, 'good_min': -50, 'good_max': -25,
                        'help': 'The level of the background noise. Set it near the hiss you hear in the quiet parts.'},
        'highpass': {'label': 'Cut rumble below (Hz, 0 = off)', 'min': 0, 'max': 300, 'good_min': 40, 'good_max': 150,
                     'help': 'Removes low rumble and hum under the voice. 0 leaves the low end alone.'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Audio Denoise: take hiss and hum out of speech. A high-pass removes low rumble, then an FFT denoiser lowers "
        "the background noise. The picture is copied untouched."
    )
    parser.add_argument("--reduction", type=float, default=12.0,
                        help="How far the noise is reduced, in dB (0-40). Default: 12.")
    parser.add_argument("--noise_floor", type=float, default=-25.0,
                        help="The background-noise level in dB (-80 to -20). Default: -25.")
    parser.add_argument("--highpass", type=float, default=80.0,
                        help="Cut rumble below this frequency in Hz. 0 = off. Default: 80.")


def run(args):
    if not has_audio(args.input):
        raise SystemExit("❌ Audio Denoise works on the sound, and this video has no audio track.")
    steps = []
    if args.highpass > 0:
        steps.append(f"highpass=f={args.highpass:.0f}")
    reduction = max(0.01, min(97.0, args.reduction))
    floor = max(-80.0, min(-20.0, args.noise_floor))
    steps.append(f"afftdn=nr={reduction:.2f}:nf={floor:.1f}")
    cmd = ["ffmpeg", "-hide_banner", "-i", args.input,
           "-map", "0:v?", "-c:v", "copy",
           "-map", "0:a?", "-af", ",".join(steps), "-c:a", "aac", "-b:a", "192k"]
    if getattr(args, "force", False):
        cmd.insert(1, "-y")
    cmd.append(str(args.output))
    run_ffmpeg_with_progress(cmd, args.input, args.output)
