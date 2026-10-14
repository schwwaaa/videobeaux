"""
soundtrack — put your own music / audio under a video: replace the existing sound, mix it in, or duck it under the
original (like a radio: the music dips whenever someone speaks). The picture is stream-copied when it can be, so this
is fast and lossless.
"""
import subprocess
from pathlib import Path

from videobeaux.utils.encode import h264_mp4_args
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.media import has_audio

MODES = ["Replace the original sound", "Mix under the original", "Duck under the original (voice stays clear)"]
LOOPS = ["Loop to fill the video", "Play once"]
_COPY_OK = {"h264", "hevc", "mpeg4", "av1", "vp9", "prores", "mjpeg", "png"}
_MP4_VIDEO = {"h264", "hevc", "mpeg4", "av1", "mjpeg"}

GUI_METADATA = {
    'args': {
        'audio': {'type': 'file', 'subtype': 'audio', 'label': 'Music / audio file',
                  'help': 'Any audio file (mp3, wav, m4a, flac…) — or a video file, to use its sound.'},
        'mode': {'type': 'select', 'label': 'How to combine', 'default': MODES[0], 'choices': MODES,
                 'help': 'Replace = only your audio. Mix = your audio plays together with the original. '
                         'Duck = like Mix, but your audio automatically dips while the original is loud (speech).'},
        'music_volume': {'label': 'Music volume (%)', 'min': 0, 'max': 200, 'good_min': 40, 'good_max': 100},
        'original_volume': {'label': 'Original volume (%)', 'min': 0, 'max': 200, 'good_min': 60, 'good_max': 100,
                            'help': 'Only used when mixing or ducking.'},
        'start': {'label': 'Start music at (s)', 'min': 0, 'max': 3600, 'help': 'Delay before the music begins.'},
        'trim_start': {'label': 'Skip into the music (s)', 'min': 0, 'max': 3600, 'help': 'Start playing the audio file from this point.'},
        'fade_in': {'label': 'Fade in (s)', 'min': 0, 'max': 30},
        'fade_out': {'label': 'Fade out (s)', 'min': 0, 'max': 30, 'good_min': 1, 'good_max': 4},
        'loop': {'type': 'select', 'label': 'If the music is shorter', 'default': LOOPS[0], 'choices': LOOPS},
        'duck_amount': {'label': 'Duck strength', 'min': 1, 'max': 20, 'good_min': 4, 'good_max': 10,
                        'help': 'How hard the music dips under the original sound (Duck mode).'},
        'crf': {'hidden': True},
    },
    'presets': {
        'Replace': {'mode': MODES[0], 'music_volume': 100, 'fade_out': 2},
        'Music bed (quiet)': {'mode': MODES[1], 'music_volume': 25, 'original_volume': 100, 'fade_in': 1, 'fade_out': 2},
        'Voice-over friendly (duck)': {'mode': MODES[2], 'music_volume': 70, 'original_volume': 100, 'duck_amount': 8, 'fade_in': 1, 'fade_out': 2},
    },
}


def register_arguments(p):
    p.description = (
        "Add your own soundtrack to a video: replace the existing audio, mix under it, or duck the music beneath "
        "the original sound. Loop or play once, with start offset and fades. The picture is copied untouched when possible."
    )
    p.add_argument("--audio", required=True, type=str, help="Audio (or video) file to use as the soundtrack.")
    p.add_argument("--mode", choices=MODES, default=MODES[0], help="Replace, mix under, or duck. Default: replace.")
    p.add_argument("--music_volume", type=float, default=100.0, help="Soundtrack volume in percent. Default: 100.")
    p.add_argument("--original_volume", type=float, default=100.0, help="Original volume in percent (mix/duck). Default: 100.")
    p.add_argument("--start", type=float, default=0.0, help="Seconds into the video where the music starts. Default: 0.")
    p.add_argument("--trim_start", type=float, default=0.0, help="Seconds into the audio file to start from. Default: 0.")
    p.add_argument("--fade_in", type=float, default=0.0, help="Fade-in seconds. Default: 0.")
    p.add_argument("--fade_out", type=float, default=0.0, help="Fade-out seconds at the end of the video. Default: 0.")
    p.add_argument("--loop", choices=LOOPS, default=LOOPS[0], help="Loop the music to fill the video, or play it once.")
    p.add_argument("--duck_amount", type=float, default=8.0, help="Duck strength 1-20. Default: 8.")
    p.add_argument("--crf", type=int, default=18, help="x264 quality when the picture has to be re-encoded.")


def _probe(path, entries, stream="v:0"):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", stream, "-show_entries", entries, "-of", "default=nw=1:nk=1",
                        str(path)], capture_output=True, text=True)
    return r.stdout.split()


def _duration(path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def build_audio_graph(a, video_dur: float, original_has_audio: bool) -> str:
    """filter_complex fragment for audio: inputs 0 = video (maybe with audio), 1 = soundtrack → [aout]."""
    fmt = "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo"
    mv = max(0.0, a.music_volume) / 100.0
    ov = max(0.0, a.original_volume) / 100.0
    start = max(0.0, a.start)
    avail = max(0.05, video_dur - start)
    chain = [f"[1:a]{fmt}"]
    if a.trim_start > 0:
        chain.append(f"atrim=start={a.trim_start:.3f},asetpts=PTS-STARTPTS")
    if a.loop == LOOPS[0]:
        chain.append("aloop=loop=-1:size=2147483647")
    chain.append(f"atrim=0:{avail:.3f},asetpts=PTS-STARTPTS")
    chain.append(f"volume={mv:.4f}")
    if a.fade_in > 0:
        chain.append(f"afade=t=in:st=0:d={a.fade_in:.3f}")
    if a.fade_out > 0:
        chain.append(f"afade=t=out:st={max(0.0, avail - a.fade_out):.3f}:d={a.fade_out:.3f}")
    if start > 0:
        ms = int(round(start * 1000))
        chain.append(f"adelay={ms}|{ms}")
    chain.append(f"apad=whole_dur={video_dur:.3f}")
    music = ",".join(chain) + "[m]"

    if a.mode == MODES[0] or not original_has_audio:
        return f"{music};[m]atrim=0:{video_dur:.3f}[aout]"
    orig = f"[0:a]{fmt},volume={ov:.4f}"
    if a.mode == MODES[1]:
        return (f"{music};{orig}[o];[o][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95,"
                f"atrim=0:{video_dur:.3f}[aout]")
    # duck: the (louder) original side-chains a compressor on the music
    ratio = max(1.0, min(20.0, a.duck_amount))
    return (f"{music};{orig},asplit=2[o1][o2];[m][o2]sidechaincompress=threshold=0.04:ratio={ratio:.1f}:attack=20:release=350[md];"
            f"[o1][md]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95,atrim=0:{video_dur:.3f}[aout]")


def run(args):
    src, music, out = Path(args.input), Path(args.audio), Path(args.output)
    if not music.exists():
        raise SystemExit(f"❌ Audio file not found: {music}")
    if not has_audio(str(music)):
        raise SystemExit(f"❌ {music.name} has no audio track.")
    dur = _duration(src)
    vcodec = (_probe(src, "stream=codec_name") or [""])[0]
    graph = build_audio_graph(args, dur, has_audio(str(src)))
    to_mp4 = out.suffix.lower() in (".mp4", ".m4v", ".mov")
    can_copy = vcodec in _COPY_OK and (not to_mp4 or vcodec in _MP4_VIDEO or out.suffix.lower() == ".mov")
    v_args = ["-c:v", "copy"] if can_copy else h264_mp4_args(crf=args.crf)[: h264_mp4_args().index("-c:a")]
    if not can_copy:
        print(f"ℹ️  The picture ({vcodec or 'unknown'}) can't be copied into {out.suffix}; re-encoding it as H.264.", flush=True)
    cmd = ["ffmpeg", "-i", str(src), "-i", str(music), "-filter_complex", graph, "-map", "0:v:0", "-map", "[aout]",
           *v_args, "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{dur:.3f}", str(out)]
    if getattr(args, "force", False):
        cmd.insert(1, "-y")
    run_ffmpeg_with_progress(cmd, str(src), str(out), duration_override=dur)
