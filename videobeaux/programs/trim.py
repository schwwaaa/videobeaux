import re
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress, get_video_duration

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


def register_arguments(parser):
    parser.description = (
        "Extracts a single section of a video by timestamp — grab a clip from the "
        "middle, or trim off the start. Give --start plus either --end or "
        "--duration; leave both off to trim from --start to the end of the video."
    )
    parser.add_argument(
        "--start", type=str, default="0",
        help="Start timestamp: seconds (12.5) or HH:MM:SS(.ms). Default: 0 (start of video)."
    )
    parser.add_argument(
        "--end", type=str, default=None,
        help="End timestamp. Mutually exclusive with --duration."
    )
    parser.add_argument(
        "--duration", type=str, default=None,
        help="Length to keep, from --start. Mutually exclusive with --end."
    )
    parser.add_argument(
        "--copy", action="store_true",
        help="Stream-copy instead of re-encoding — much faster, but the cut snaps to the nearest keyframe rather than the exact timestamp."
    )


def run(args):
    if args.end is not None and args.duration is not None:
        raise SystemExit("❌ --end and --duration can't both be set — pick one.")

    start_s = _parse_timestamp(args.start, "--start")

    if args.end is not None:
        end_s = _parse_timestamp(args.end, "--end")
        duration_s = end_s - start_s
        if duration_s <= 0:
            raise SystemExit(f"❌ --end ({args.end}) must be after --start ({args.start}).")
    elif args.duration is not None:
        duration_s = _parse_timestamp(args.duration, "--duration")
    else:
        total = get_video_duration(args.input)
        duration_s = max(0.0, total - start_s)
        if duration_s <= 0:
            raise SystemExit(f"❌ --start ({args.start}) is at or past the end of the video.")

    command = ["ffmpeg", "-ss", f"{start_s:.3f}", "-i", args.input, "-t", f"{duration_s:.3f}"]
    if args.copy:
        command += ["-c", "copy"]
    else:
        command += ["-c:v", "libx264", "-c:a", "aac"]
    command += [args.output]

    run_ffmpeg_with_progress(
        (command[:1] + ["-y"] + command[1:]) if args.force else command,
        args.input, args.output, duration_override=duration_s
    )
