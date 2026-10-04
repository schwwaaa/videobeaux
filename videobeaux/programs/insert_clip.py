from videobeaux.utils.media import ensure_audio
import re
import subprocess
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

GUI_METADATA = {
    'args': {
        'input2': {
            'type': 'file',
            'subtype': 'video',
            'label': 'Insert Video',
            'help': 'Video to insert into the master — connect a node or pick a file.',
        },
    }
}

_TIMESTAMP_RE = re.compile(r"^(?:(\d+):)?(\d{1,2}):(\d{1,2}(?:\.\d+)?)$|^(\d+(?:\.\d+)?)$")


def _parse_timestamp(ts, arg_name):
    ts = ts.strip()
    m = _TIMESTAMP_RE.match(ts)
    if not m:
        raise SystemExit(
            f"❌ Could not parse {arg_name} {ts!r}. Use seconds (12.5) or HH:MM:SS(.ms) (01:02:03.5)."
        )
    if m.group(4) is not None:
        return float(m.group(4))
    h = int(m.group(1)) if m.group(1) else 0
    mi = int(m.group(2))
    s = float(m.group(3))
    return h * 3600 + mi * 60 + s


def _get_video_dims_fps(input_file):
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
         '-show_entries', 'stream=width,height,r_frame_rate',
         '-of', 'default=noprint_wrappers=1:nokey=1', str(input_file)],
        capture_output=True, text=True
    )
    lines = result.stdout.strip().splitlines()
    width, height, rate = int(lines[0]), int(lines[1]), lines[2]
    if '/' in rate:
        num, den = rate.split('/')
        fps = float(num) / float(den) if float(den) != 0 else 30.0
    else:
        fps = float(rate)
    return width, height, fps


def _get_video_duration(input_file):
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', str(input_file)],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def register_arguments(parser):
    parser.description = (
        "Inserts a second video into the master at a chosen timestamp, then picks up the "
        "master from where it left off — e.g. dropping an intermission slate into the middle "
        "of a longer video. Independent transition control at each boundary: the entry "
        "(master → insert) and exit (insert → master) can each be a hard cut, a crossfade, "
        "or a blank/silent gap."
    )
    parser.add_argument(
        "--input2",
        required=True,
        type=str,
        help="Video to insert into the master."
    )
    parser.add_argument(
        "--insert_at",
        required=True,
        type=str,
        help="Timestamp in the master to insert at. Seconds (12.5) or HH:MM:SS(.ms)."
    )
    parser.add_argument(
        "--entry_transition",
        choices=["cut", "crossfade", "gap"],
        default="cut",
        help="Transition from the master into the insert. Default: cut."
    )
    parser.add_argument(
        "--entry_duration",
        type=float,
        default=0.5,
        help="Crossfade or gap length (seconds) at the entry boundary. Ignored for cut. Default: 0.5."
    )
    parser.add_argument(
        "--exit_transition",
        choices=["cut", "crossfade", "gap"],
        default="cut",
        help="Transition from the insert back into the master. Default: cut."
    )
    parser.add_argument(
        "--exit_duration",
        type=float,
        default=0.5,
        help="Crossfade or gap length (seconds) at the exit boundary. Ignored for cut. Default: 0.5."
    )


def _join(parts, va, durA, vb, durB, mode, duration, w, h, fps, gap_label):
    """
    Join two labeled [v][a] streams (durA/durB seconds long) with the given
    mode, appending the needed filter fragments to `parts`. Returns
    (new_v_label, new_a_label, new_duration).

    The video output is always re-normalized with an explicit fps filter
    before being returned: xfade requires both of its inputs to share the
    same internal timebase, but concat's output timebase doesn't match a
    trim+fps chain's — chaining a second xfade straight off a concat (or
    another xfade) output fails with "do not match... xfade timebase"
    otherwise, since this function's result may itself feed a second join.
    """
    av, aa = va
    bv, ba = vb
    raw_v, out_a = f"{gap_label}_v0", f"{gap_label}_a"

    if mode == "cut":
        parts.append(f"[{av}][{aa}][{bv}][{ba}]concat=n=2:v=1:a=1[{raw_v}][{out_a}]")
        new_dur = durA + durB

    elif mode == "crossfade":
        offset = max(0.0, durA - duration)
        parts.append(f"[{av}][{bv}]xfade=transition=fade:duration={duration}:offset={offset}[{raw_v}]")
        parts.append(f"[{aa}][{ba}]acrossfade=duration={duration}[{out_a}]")
        new_dur = durA + durB - duration

    else:  # gap
        gv, ga = f"{gap_label}_fill_v", f"{gap_label}_fill_a"
        parts.append(f"color=black:size={w}x{h}:rate={fps}:duration={duration}[{gv}]")
        parts.append(f"anullsrc=channel_layout=stereo:sample_rate=48000:duration={duration}[{ga}]")
        parts.append(f"[{av}][{aa}][{gv}][{ga}][{bv}][{ba}]concat=n=3:v=1:a=1[{raw_v}][{out_a}]")
        new_dur = durA + duration + durB

    out_v = f"{gap_label}_v"
    parts.append(f"[{raw_v}]fps={fps}[{out_v}]")
    return out_v, out_a, new_dur


def run(args):
    # audio filter graphs need an audio track on every input
    if getattr(args, 'input', None):
        args.input = ensure_audio(args.input)
    if getattr(args, 'input2', None):
        args.input2 = ensure_audio(args.input2)
    insert_at = _parse_timestamp(args.insert_at, "--insert_at")

    master_dur = _get_video_duration(args.input)
    if not (0 < insert_at < master_dur):
        raise SystemExit(
            f"❌ --insert_at ({args.insert_at}) must fall strictly within the master video "
            f"(0 to {master_dur:.2f}s)."
        )

    insert_dur = _get_video_duration(args.input2)
    dur_mA = insert_at
    dur_mB = master_dur - insert_at

    if args.entry_transition == "crossfade" and (dur_mA < args.entry_duration or insert_dur < args.entry_duration):
        raise SystemExit(
            f"❌ Entry crossfade ({args.entry_duration}s) is longer than the master segment before "
            f"the insert point ({dur_mA:.2f}s) or the insert clip itself ({insert_dur:.2f}s)."
        )
    if args.exit_transition == "crossfade" and (dur_mB < args.exit_duration or insert_dur < args.exit_duration):
        raise SystemExit(
            f"❌ Exit crossfade ({args.exit_duration}s) is longer than the master segment after "
            f"the insert point ({dur_mB:.2f}s) or the insert clip itself ({insert_dur:.2f}s)."
        )
    if (args.entry_transition == "crossfade" and args.exit_transition == "crossfade"
            and insert_dur < args.entry_duration + args.exit_duration):
        raise SystemExit(
            f"❌ The insert clip ({insert_dur:.2f}s) is too short to supply both an entry "
            f"crossfade ({args.entry_duration}s) and an exit crossfade ({args.exit_duration}s) — "
            f"it needs at least {args.entry_duration + args.exit_duration:.2f}s."
        )

    w, h, fps = _get_video_dims_fps(args.input)

    parts = [
        f"[0:v]trim=start=0:end={insert_at:.6f},setpts=PTS-STARTPTS,fps={fps},setsar=1[mA_v]",
        f"[0:a]atrim=start=0:end={insert_at:.6f},asetpts=PTS-STARTPTS[mA_a]",
        f"[0:v]trim=start={insert_at:.6f},setpts=PTS-STARTPTS,fps={fps},setsar=1[mB_v]",
        f"[0:a]atrim=start={insert_at:.6f},asetpts=PTS-STARTPTS[mB_a]",
        f"[1:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps}[ins_v]",
        f"[1:a]asetpts=PTS-STARTPTS[ins_a]",
    ]

    v1, a1, dur1 = _join(
        parts, ("mA_v", "mA_a"), dur_mA, ("ins_v", "ins_a"), insert_dur,
        args.entry_transition, args.entry_duration, w, h, fps, "j1"
    )
    v2, a2, _dur2 = _join(
        parts, (v1, a1), dur1, ("mB_v", "mB_a"), dur_mB,
        args.exit_transition, args.exit_duration, w, h, fps, "j2"
    )

    filter_complex = ";".join(parts)

    command = [
        "ffmpeg",
        "-i", args.input,
        "-i", args.input2,
        "-filter_complex", filter_complex,
        "-map", f"[{v2}]",
        "-map", f"[{a2}]",
        "-c:v", "libx264",
        "-c:a", "aac",
        args.output
    ]

    run_ffmpeg_with_progress(
        (command[:1] + ["-y"] + command[1:]) if args.force else command,
        args.input, args.output
    )
