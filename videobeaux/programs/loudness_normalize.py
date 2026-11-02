"""
loudness_normalize: evens out how loud the sound is. It is brought to a target loudness (LUFS, the EBU R128 measure)
with a true-peak ceiling, so quiet and loud clips land at the same level. The video is copied untouched.
"""
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.media import has_audio

GUI_METADATA = {
    'args': {
        'target': {'label': 'Target loudness (LUFS)', 'min': -30, 'max': -5, 'good_min': -24, 'good_max': -12,
                   'help': '-16 is the usual level for online video and podcasts; -23 is the broadcast standard.'},
        'true_peak': {'label': 'Peak ceiling (dBTP)', 'min': -9, 'max': 0, 'good_min': -3, 'good_max': -1,
                      'help': 'The loudest peak allowed after normalising. -1.5 leaves headroom so the sound cannot clip.'},
        'lra': {'label': 'Loudness range (LU)', 'min': 1, 'max': 20, 'good_min': 5, 'good_max': 15,
                'help': 'How much the loudness may vary within the clip. Smaller is more even, but can sound pumped.'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Loudness Normalize: bring the sound to a target loudness (EBU R128, in LUFS) with a true-peak ceiling, so "
        "quiet and loud clips come out at the same level. The picture is copied untouched."
    )
    parser.add_argument("--target", type=float, default=-16.0,
                        help="Target loudness in LUFS. Default: -16 (online video and podcasts; -23 is broadcast).")
    parser.add_argument("--true_peak", type=float, default=-1.5,
                        help="Peak ceiling in dBTP. Default: -1.5, which leaves headroom against clipping.")
    parser.add_argument("--lra", type=float, default=11.0,
                        help="Loudness range in LU, how much the level may vary. Default: 11.")


def run(args):
    if not has_audio(args.input):
        raise SystemExit("❌ Loudness Normalize works on the sound, and this video has no audio track.")
    # aresample: loudnorm may return a 192 kHz stream; bring it back to 48 kHz for the output.
    af = f"loudnorm=I={args.target:.1f}:TP={args.true_peak:.1f}:LRA={args.lra:.1f},aresample=48000"
    cmd = ["ffmpeg", "-hide_banner", "-i", args.input,
           "-map", "0:v?", "-c:v", "copy",
           "-map", "0:a?", "-af", af, "-c:a", "aac", "-b:a", "192k"]
    if getattr(args, "force", False):
        cmd.insert(1, "-y")
    cmd.append(str(args.output))
    run_ffmpeg_with_progress(cmd, args.input, args.output)
