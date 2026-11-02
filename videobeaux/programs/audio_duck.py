"""
audio_duck: lowers a music bed whenever the picture's own sound (the narration or dialogue) is speaking. The video's
audio is the voice; the music you connect is turned down under it by a sidechain compressor, then the two are mixed.
The video is copied unchanged.
"""
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.media import has_audio

GUI_METADATA = {
    'args': {
        'music': {'type': 'file', 'subtype': 'video', 'required': True, 'label': 'Music',
                  'help': 'Connect the music (any video or audio file). It loops if it is shorter than the clip.'},
        'threshold_db': {'label': 'Speech level (dB)', 'min': -60, 'max': -10, 'good_min': -45, 'good_max': -20,
                         'help': 'The level the voice must reach before the music ducks. Quiet narration needs a lower number.'},
        'ratio': {'label': 'Duck amount (ratio)', 'min': 1, 'max': 20, 'good_min': 3, 'good_max': 10,
                  'help': 'How hard the music is pulled down under speech. Higher = the music drops further.'},
        'release_ms': {'label': 'Release (ms)', 'min': 50, 'max': 2000, 'good_min': 200, 'good_max': 800,
                       'help': 'How long the music takes to come back up after the voice stops.'},
        'music_db': {'label': 'Music level (dB)', 'min': -30, 'max': 6, 'good_min': -18, 'good_max': 0,
                     'help': 'Level of the music before ducking. Negative = quieter.'},
    }
}


def register_arguments(parser):
    parser.description = (
        "Audio Duck: lower the music under the narration. The clip's own sound is the voice; the connected music "
        "drops whenever the voice is speaking, then comes back up. The picture is copied untouched."
    )
    parser.add_argument("--music", required=True, type=str,
                        help="The music file (any video or audio). It loops if shorter than the clip.")
    parser.add_argument("--threshold_db", type=float, default=-35.0,
                        help="Speech level in dB that triggers ducking, -60 to -10. Default: -35.")
    parser.add_argument("--ratio", type=float, default=6.0,
                        help="How hard the music is ducked, 1-20. Default: 6.")
    parser.add_argument("--release_ms", type=float, default=400.0,
                        help="Milliseconds for the music to come back after speech. Default: 400.")
    parser.add_argument("--music_db", type=float, default=-6.0,
                        help="Music level before ducking, in dB. Default: -6.")


def run(args):
    if not has_audio(args.input):
        raise SystemExit("❌ Audio Duck needs the clip's own sound to key the ducking, and this video has no audio track.")
    if not has_audio(args.music):
        raise SystemExit("❌ The music file has no audio track.")
    threshold = 10 ** (max(-60.0, min(-10.0, args.threshold_db)) / 20.0)
    ratio = max(1.0, min(20.0, args.ratio))
    release = max(50.0, min(2000.0, args.release_ms))
    music_gain = max(-30.0, min(6.0, args.music_db))
    fmt = "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo"
    graph = (
        f"[0:a]{fmt},asplit=2[voice][key];"
        f"[1:a]{fmt},volume={music_gain:.2f}dB[music];"
        f"[music][key]sidechaincompress=threshold={threshold:.6f}:ratio={ratio:.2f}:attack=20:"
        f"release={release:.0f}:makeup=1[ducked];"
        "[voice][ducked]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[aout]"
    )
    cmd = ["ffmpeg", "-hide_banner", "-i", args.input, "-stream_loop", "-1", "-i", args.music,
           "-filter_complex", graph,
           "-map", "0:v?", "-c:v", "copy",
           "-map", "[aout]", "-c:a", "aac", "-b:a", "192k"]
    if getattr(args, "force", False):
        cmd.insert(1, "-y")
    cmd.append(str(args.output))
    run_ffmpeg_with_progress(cmd, args.input, args.output)
    print(f"✅ Music ducked under the clip's sound (threshold {args.threshold_db:.0f} dB, ratio {ratio:.1f}).")
