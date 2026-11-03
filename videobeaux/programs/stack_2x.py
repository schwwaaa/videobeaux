"""
stack_2x — stack two videos vertically (input on top of input2), at the top video's width.

The second video is scaled to the first one's width (so clips of different sizes always work); choose how: keep its
whole picture with bars (contain), fill and crop (cover), or stretch. Duration: the output can run as long as the longer
video (the shorter one holds its last frame), or stop when the top or the bottom video stops. Audio: the top video, the
bottom video, both mixed, or silence.
"""
from videobeaux.utils import audio_pick
from videobeaux.utils.encode import even, h264_mp4_args
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.frame_pipe import probe_video
from videobeaux.utils.media import ensure_audio

FITS = ["keep whole picture (scale to width)", "fill and crop to the top video's height", "stretch to the top video's size"]
AUDIO = ["Top video", "Bottom video", "Mix both", "Silent"]
_AUDIO_MODE = {AUDIO[0]: "a", AUDIO[1]: "b", AUDIO[2]: "both", AUDIO[3]: "none"}
DURATIONS = ["Longest", "Top video", "Bottom video"]

GUI_METADATA = {
    'args': {
        'input2': {
            'type': 'file',
            'subtype': 'video',
            'label': 'Second Video',
            'help': 'Video placed on the bottom of the stack — connect a node or pick a file.',
        },
        'fit': {'type': 'select', 'label': 'Bottom video fit', 'default': FITS[0], 'choices': FITS,
                'help': 'The bottom video always ends up as wide as the top one. This chooses how its height is handled.'},
        'duration': {'type': 'select', 'label': 'Length set by', 'default': DURATIONS[0], 'choices': DURATIONS,
                     'help': 'Longest: the output runs as long as the longer video, and the shorter one holds its last frame. '
                             'Top video / Bottom video: the output stops when that video stops, and the other is cut to match.'},
        'audio': {'type': 'select', 'label': 'Audio', 'default': AUDIO[0], 'choices': AUDIO,
                  'help': 'Top video or Bottom video keeps only that one\'s sound · Mix both plays the two together at equal level · Silent drops all sound.'},
        'gap': {'label': 'Gap (px)', 'min': 0, 'max': 80},
        'crf': {'hidden': True},
    }
}


def register_arguments(parser):
    parser.description = (
        "Stacks 2 videos, --input on top of --input2, in a vertical column. The second video is scaled to the "
        "first one's width. Choose with --duration which video sets the length; the other holds its last frame or is cut."
    )
    parser.add_argument("--input2", required=True, type=str, help="Path to the video you want on the bottom of the stack.")
    parser.add_argument("--fit", choices=FITS, default=FITS[0], help="How the bottom video is fitted to the top one's width.")
    parser.add_argument("--duration", choices=DURATIONS, default=DURATIONS[0],
                        help="Which video sets the length of the output. Default: the longer one.")
    parser.add_argument("--audio", choices=AUDIO, default=AUDIO[0], help="Which audio to keep. Default: top video.")
    parser.add_argument("--gap", type=int, default=0, help="Black gap between the two videos in pixels. Default: 0.")
    parser.add_argument("--crf", type=int, default=20, help="x264 quality. Default: 20.")


def build_graph(w: int, h_top: int, h2: int, fit: str, fps: float, gap: int, total: float) -> str:
    """Filter graph for inputs 0 (top) and 1 (bottom) → [v]. Both are held on their last frame out to `total` seconds."""
    hold = f",tpad=stop_mode=clone:stop_duration={total:.3f}"
    top = f"[0:v]crop={w}:{h_top}:0:0,setsar=1,fps={fps:.6f},format=yuv420p{hold}[t]"
    if fit == FITS[1]:                      # fill + crop to the top video's height
        bottom = (f"[1:v]scale={w}:{h_top}:force_original_aspect_ratio=increase,crop={w}:{h_top},setsar=1,"
                  f"fps={fps:.6f},format=yuv420p{hold}[b]")
    elif fit == FITS[2]:                    # stretch
        bottom = f"[1:v]scale={w}:{h_top},setsar=1,fps={fps:.6f},format=yuv420p{hold}[b]"
    else:                                   # keep the whole picture at the top video's width
        bottom = f"[1:v]scale={w}:{h2},setsar=1,fps={fps:.6f},format=yuv420p{hold}[b]"
    graph = f"{top};{bottom}"
    if gap > 0:
        graph += f";color=c=black:s={w}x{gap}:r={fps:.6f},format=yuv420p[g];[t][g][b]vstack=inputs=3:shortest=0[v]"
    else:
        graph += ";[t][b]vstack=inputs=2:shortest=0[v]"
    return graph


def run(args):
    args.input = ensure_audio(args.input)
    args.input2 = ensure_audio(args.input2)
    a, b = probe_video(args.input), probe_video(args.input2)
    w, h_top = even(a.width), even(a.height)
    h2 = even(round(w * b.height / max(1, b.width)))
    lengths = {DURATIONS[0]: max(a.duration, b.duration), DURATIONS[1]: a.duration, DURATIONS[2]: b.duration}
    total = lengths[args.duration]
    graph = build_graph(w, h_top, h2, args.fit, a.fps, max(0, int(args.gap)), total)

    mode = _AUDIO_MODE[args.audio]
    cmd = ["ffmpeg", "-i", args.input, "-i", args.input2]
    if mode == "none":
        cmd += ["-filter_complex", graph, "-map", "[v]", "-an"]
        full = h264_mp4_args(crf=args.crf)
        enc = full[:full.index("-c:a")]                       # video flags only
    else:
        fmt = "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo"
        if mode == "a":
            agraph = f"[0:a]{fmt},apad=whole_dur={total:.3f},atrim=0:{total:.3f}[a]"
        elif mode == "b":
            agraph = f"[1:a]{fmt},apad=whole_dur={total:.3f},atrim=0:{total:.3f}[a]"
        else:
            agraph = (f"[0:a]{fmt},apad=whole_dur={total:.3f}[a0];[1:a]{fmt},apad=whole_dur={total:.3f}[a1];"
                      f"[a0][a1]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:{total:.3f}[a]")
        cmd += ["-filter_complex", graph + ";" + agraph, "-map", "[v]", "-map", "[a]"]
        enc = h264_mp4_args(crf=args.crf)
    cmd += ["-t", f"{total:.3f}", *enc, args.output]
    run_ffmpeg_with_progress((cmd[:1] + ["-y"] + cmd[1:]) if args.force else cmd, args.input, args.output, duration_override=total)
