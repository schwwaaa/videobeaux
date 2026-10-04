from videobeaux.utils.media import ensure_audio
import subprocess
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

GUI_METADATA = {
    'args': {
        'input2': {
            'type': 'file',
            'subtype': 'video',
            'label': 'Second Video',
            'help': 'Video that plays after the first — connect a node or pick a file.',
        },
    }
}


def _get_video_dims_fps(input_file):
    """Get (width, height, fps) of a video's first video stream using ffprobe."""
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
        "Concatenates two videos, first then second, back to back. "
        "Optionally crossfade between them, or insert a blank/silent gap. "
        "Good for adding a slate or title card before the main video."
    )
    parser.add_argument(
        "--input2",
        required=True,
        type=str,
        help="Second video — plays after the first."
    )
    parser.add_argument(
        "--crossfade",
        type=float,
        default=0.0,
        help="Crossfade duration in seconds at the join (0 = hard cut)."
    )
    parser.add_argument(
        "--gap",
        type=float,
        default=0.0,
        help="Blank (black + silent) gap in seconds between the two clips (0 = none). Cannot be combined with --crossfade."
    )


def run(args):
    # audio filter graphs need an audio track on every input
    if getattr(args, 'input', None):
        args.input = ensure_audio(args.input)
    if getattr(args, 'input2', None):
        args.input2 = ensure_audio(args.input2)
    if args.crossfade > 0 and args.gap > 0:
        raise SystemExit(
            "❌ --crossfade and --gap can't both be set — a gap needs a hard boundary, "
            "a crossfade needs the clips to overlap."
        )

    # Normalize the second clip to the first's resolution/fps (real clips
    # rarely match by default) — same approach as wipe_transitions.py, and
    # for the same reason: mismatched geometry makes ffmpeg fail deep inside
    # the encoder with an opaque error rather than a clear one.
    w1, h1, fps1 = _get_video_dims_fps(args.input)
    norm = (
        f"[1:v]scale={w1}:{h1}:force_original_aspect_ratio=decrease,"
        f"pad={w1}:{h1}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps1}[v1n];"
        f"[0:v]fps={fps1},setsar=1[v0n]"
    )

    if args.crossfade > 0:
        dur1 = _get_video_duration(args.input)
        offset = max(0.0, dur1 - args.crossfade)
        # acrossfade only takes `duration` — unlike xfade it has no `offset`
        # concept (it assumes a plain sequential concat with an overlap at
        # the join, not two simultaneous streams sharing a timeline).
        filter_complex = (
            f"{norm};"
            f"[v0n][v1n]xfade=transition=fade:duration={args.crossfade}:offset={offset}[v];"
            f"[0:a][1:a]acrossfade=duration={args.crossfade}[a]"
        )
    elif args.gap > 0:
        filter_complex = (
            f"{norm};"
            f"color=black:size={w1}x{h1}:rate={fps1}:duration={args.gap}[gapv];"
            f"anullsrc=channel_layout=stereo:sample_rate=48000:duration={args.gap}[gapa];"
            f"[v0n][0:a][gapv][gapa][v1n][1:a]concat=n=3:v=1:a=1[v][a]"
        )
    else:
        filter_complex = (
            f"{norm};"
            f"[v0n][0:a][v1n][1:a]concat=n=2:v=1:a=1[v][a]"
        )

    command = [
        "ffmpeg",
        "-i", args.input,
        "-i", args.input2,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-c:a", "aac",
        args.output
    ]

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
