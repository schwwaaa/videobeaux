from videobeaux.utils.media import ensure_audio
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from pathlib import Path
import sys
import subprocess

# List of supported xfade transition presets
VIDEO_TRANSITIONS = [
    "fade", "wipeleft", "wiperight", "wipeup", "wipedown",
    "slideleft", "slideright", "slideup", "slidedown",
    "circlecrop", "circleclose", "circleopen",
    "horizopen", "horizclose", "vertopen", "vertclose",
    "dissolve", "pixelize",
    "diagtl", "diagtr", "diagbl", "diagbr",
    "hlslice", "hrslice", "vuslice", "vdslice",
    "hblur", "fadeblack", "fadewhite",
    "radial", "smoothleft", "smoothright", "smoothup", "smoothdown",
    "rectcrop", "distance", "fadegrays",
    "squeezeh", "squeezev", "zoomin"
]

def get_video_duration(input_file):
    """Get the duration of a video file using ffprobe."""
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(input_file)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if result.returncode != 0:
        print(f"❌ Error getting duration for {input_file}: {result.stderr}")
        sys.exit(1)
    try:
        return float(result.stdout.strip())
    except ValueError:
        print(f"❌ Invalid duration for {input_file}")
        sys.exit(1)

def get_video_dims_fps(input_file):
    """Get (width, height, fps) of a video's first video stream using ffprobe."""
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
         '-show_entries', 'stream=width,height,r_frame_rate',
         '-of', 'default=noprint_wrappers=1:nokey=1', str(input_file)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if result.returncode != 0:
        print(f"❌ Error getting video info for {input_file}: {result.stderr}")
        sys.exit(1)
    lines = result.stdout.strip().splitlines()
    if len(lines) < 3:
        print(f"❌ Unexpected ffprobe output for {input_file}")
        sys.exit(1)
    width, height, rate = int(lines[0]), int(lines[1]), lines[2]
    if '/' in rate:
        num, den = rate.split('/')
        fps = float(num) / float(den) if float(den) != 0 else 0.0
    else:
        fps = float(rate)
    return width, height, fps

GUI_METADATA = {
    'args': {
        'input2': {
            'type': 'file',
            'subtype': 'video',
            'label': 'Second Video',
            'help': 'Video that transitions in — connect a node or pick a file.',
        },
    }
}

def register_arguments(parser):
    parser.description = "Combines two input videos with a transitional wipe using FFmpeg's xfade filter. Supports various preset transitions and customizable duration."
    # The first video comes from the standard global -i/--input, matching
    # every other multi-input program; only the second is an extra arg.
    parser.add_argument(
        "--input2",
        required=True,
        type=str,
        help="Path to the second input video."
    )
    parser.add_argument(
        "--preset",
        type=str,
        default="fade",
        choices=VIDEO_TRANSITIONS,
        help="Preset transition type (e.g., wipeleft, fade, etc)."
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=1.0,
        help="Duration of the transition in seconds (default: 1.0). Can be long for artistic effects, but may be capped by clip lengths."
    )
    parser.add_argument(
        "--offset",
        type=float,
        default=3.0,
        help="Offset in seconds where the transition starts in the first video (default: 3)."
    )

def run(args):
    # audio filter graphs need an audio track on every input
    if getattr(args, 'input', None):
        args.input = ensure_audio(args.input)
    if getattr(args, 'input2', None):
        args.input2 = ensure_audio(args.input2)
    # Output goes straight to the global -o/--output, like every other
    # program — no separate format flag needed.
    clean_output = Path(args.output)

    if clean_output.exists() and not args.force:
        print(f"❌ {clean_output} already exists. Use --force to overwrite.")
        sys.exit(1)

    # Get durations
    dur1 = get_video_duration(args.input)
    dur2 = get_video_duration(args.input2)

    # Warn if transition might exceed lengths
    if args.offset + args.duration > dur1 or args.duration > dur2:
        print("⚠️ Warning: Transition duration exceeds available clip lengths. Output may be truncated or incomplete.")

    # xfade requires both video streams to share dimensions and frame rate —
    # real-world clips rarely match by default, so normalize the second clip
    # (and the first clip's frame rate) to the first clip's geometry before
    # blending. Without this, ffmpeg fails deep inside the encoder with an
    # opaque "Invalid argument" error rather than a clear message.
    w1, h1, fps1 = get_video_dims_fps(args.input)

    # acrossfade only takes `duration` — unlike xfade, it has no `offset`
    # concept (it assumes a plain sequential concat with an overlap at the
    # join, not two simultaneous streams sharing a timeline).
    filter_complex = (
        f"[1:v]scale={w1}:{h1}:force_original_aspect_ratio=decrease,"
        f"pad={w1}:{h1}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps1}[v1n];"
        f"[0:v]fps={fps1},setsar=1[v0n];"
        f"[v0n][v1n]xfade=transition={args.preset}:duration={args.duration}:offset={args.offset}[v];"
        f"[0:a][1:a]acrossfade=duration={args.duration}[a]"
    )

    command = [
        "ffmpeg",
        "-i", str(args.input),
        "-i", str(args.input2),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",  # Use H.264 for compatibility
        "-c:a", "aac",      # Use AAC for audio compatibility
        "-b:v", "5000k",    # Set reasonable video bitrate
        str(clean_output)
    ]

    # Add -y flag if force overwrite is enabled
    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, clean_output)