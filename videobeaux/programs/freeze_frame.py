"""
freeze_frame — a mixer-style "still": freeze the picture at a moment. Either hold it in place (the clip keeps its
length, audio keeps playing) or insert the freeze (the clip gets longer, with silence under the freeze).
"""
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.frame_pipe import probe_video
from videobeaux.utils.media import ensure_audio, has_audio

MODES = ["hold in place (same length)", "insert (clip gets longer)"]

GUI_METADATA = {
    'args': {
        'at': {'label': 'Freeze at (seconds)', 'min': 0, 'max': 36000},
        'length': {'label': 'Freeze for (seconds)', 'min': 0.04, 'max': 600},
        'mode': {'type': 'select', 'label': 'Mode', 'default': MODES[0], 'choices': MODES,
                 'help': 'hold in place = frames after the freeze point are replaced by the still. '
                         'insert = the still is added, pushing the rest of the clip later (silence under it).'},
        'crf': {'hidden': True},
    }
}


def register_arguments(p):
    p.description = (
        "Freeze frame: hold the picture still at a chosen moment. 'hold in place' replaces frames (length and "
        "audio unchanged); 'insert' adds the freeze, lengthening the clip, with silence under it."
    )
    p.add_argument("--at", type=float, default=2.0, help="Time to freeze at, in seconds. Default: 2.")
    p.add_argument("--length", type=float, default=1.5, help="How long to hold, in seconds. Default: 1.5.")
    p.add_argument("--mode", choices=MODES, default=MODES[0], help="hold in place, or insert. Default: hold in place.")
    p.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def run(args):
    args.input = ensure_audio(args.input)   # audio filters need a track on every input
    info = probe_video(args.input)
    fps = info.fps
    at = max(0.0, min(args.at, max(0.0, info.duration - 0.05)))
    n0 = int(round(at * fps))
    frames = max(1, int(round(args.length * fps)))
    aud = has_audio(args.input)
    force = ["-y"] if getattr(args, "force", False) else []
    tail = ["-c:v", "libx264", "-preset", "medium", "-crf", str(args.crf), "-pix_fmt", "yuv420p",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-movflags", "+faststart"]
    if args.mode == MODES[0]:
        # freezeframes takes the clip plus a second copy to pull the replacement frame from
        graph = f"[0:v]split[s][r];[s][r]freezeframes=first={n0 + 1}:last={n0 + frames}:replace={n0 + 1}[out]"
        cmd = ["ffmpeg", *force, "-i", args.input, "-filter_complex", graph, "-map", "[out]",
               *(["-map", "0:a?", "-c:a", "copy"] if aud else []), *tail, args.output]
        run_ffmpeg_with_progress(cmd, args.input, args.output)
        return
    v = (f"[0:v]split=3[va][vf][vb];"
         f"[va]trim=end_frame={n0 + 1},setpts=PTS-STARTPTS[a];"
         f"[vf]trim=start_frame={n0}:end_frame={n0 + 1},setpts=PTS-STARTPTS,loop=loop={frames - 1}:size=1:start=0,setpts=N/({fps:.6f}*TB)[f];"
         f"[vb]trim=start_frame={n0 + 1},setpts=PTS-STARTPTS[b];"
         f"[a][f][b]concat=n=3:v=1:a=0[out]")
    cmd = ["ffmpeg", *force, "-i", args.input]
    if aud:
        v += (f";[0:a]atrim=end={at:.4f},asetpts=PTS-STARTPTS[a1];"
              f"anullsrc=channel_layout=stereo:sample_rate=48000,atrim=duration={args.length:.4f}[s];"
              f"[0:a]atrim=start={at:.4f},asetpts=PTS-STARTPTS[a2];[a1][s][a2]concat=n=3:v=0:a=1[aout]")
    cmd += ["-filter_complex", v, "-map", "[out]", *(["-map", "[aout]", "-c:a", "aac"] if aud else []), *tail, args.output]
    run_ffmpeg_with_progress(cmd, args.input, args.output)
