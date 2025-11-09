from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from pathlib import Path
import sys

# Video dimension presets
VIDEO_PRESETS = {
    "sd": (320, 240),         # Standard Definition (4:3)
    "720hd": (640, 360),      # 720p HD reduced (16:9)
    "1080hd": (960, 540),     # 1080p HD reduced (16:9)
    "widescreen": (320, 180), # Widescreen low-res (16:9)
    "portrait1080": (1080, 1620), # Portrait 1080p (9:13.5)
    "480p": (640, 480),       # Standard Definition (4:3)
    "576p": (720, 576),       # PAL Standard Definition (4:3)
    "720p": (1280, 720),      # HD (16:9)
    "1080p": (1920, 1080),    # Full HD (16:9)
    "1440p": (2560, 1440),    # QHD/2K (16:9)
    "4k": (3840, 2160),       # 4K UHD (16:9)
    "8k": (7680, 4320),       # 8K UHD (16:9)
    "vga": (640, 480),        # VGA (4:3)
    "qvga": (320, 240),       # Quarter VGA (4:3)
    "wvga": (800, 480),       # Wide VGA (5:3)
    "svga": (800, 600),       # Super VGA (4:3)
    "xga": (1024, 768),       # Extended Graphics Array (4:3)
    "wxga": (1280, 800),      # Wide XGA (16:10)
    "sxga": (1280, 1024),     # Super XGA (5:4)
    "uxga": (1600, 1200),     # Ultra XGA (4:3)
    "wuxga": (1920, 1200),    # Widescreen Ultra XGA (16:10)
    "qwxga": (2048, 1152),    # Quad Wide XGA (16:9)
    "qhd": (2560, 1440),      # Quad HD (16:9)
    "wqxga": (2560, 1600),    # Wide Quad XGA (16:10)
    "5k": (5120, 2880),       # 5K (16:9)
    "portrait720": (720, 1280), # Portrait 720p (9:16)
    "portrait4k": (2160, 3840), # Portrait 4K (9:16)
    "square1080": (1080, 1080), # Square 1080p (1:1)
    "square720": (720, 720),  # Square 720p (1:1)
    "cinema4k": (4096, 2160), # 4K DCI (Digital Cinema, ~17:9)
    "ultrawide1080": (2560, 1080), # Ultrawide 1080p (21:9)
    "ultrawide1440": (3440, 1440), # Ultrawide 1440p (21:9)
    "instagram_feed": (1080, 1080), # Instagram square video (1:1)
    "instagram_reels": (1080, 1920), # Instagram Reels/TikTok (9:16)
    "instagram_stories": (1080, 1920), # Instagram Stories (9:16)
    "tiktok_video": (1080, 1920), # TikTok standard video (9:16)
    "youtube_standard": (1920, 1080), # YouTube standard video (16:9)
    "youtube_shorts": (1080, 1920), # YouTube Shorts (9:16)
    "facebook_feed": (1080, 1080), # Facebook in-feed video (1:1 recommended)
    "facebook_stories": (1080, 1920), # Facebook Stories (9:16)
    "twitter_video": (1280, 720), # Twitter/X video (16:9, recommended)
    "twitter_square": (1080, 1080), # Twitter/X square video (1:1)
    "linkedin_video": (1920, 1080), # LinkedIn video (16:9, recommended)
    "linkedin_square": (1080, 1080), # LinkedIn square video (1:1)
    "snapchat_video": (1080, 1920), # Snapchat video (9:16)
    "pinterest_video": (1080, 1920), # Pinterest video (9:16)
    "pinterest_square": (1000, 1000) # Pinterest square video (1:1)
}

def register_arguments(parser):
    parser.description = ("Converts an input video to a specified preset dimension. "
                          "Optionally stretch to fit dimensions or maintain aspect ratio with padding.")
    parser.add_argument(
        "--output-format", required=True, type=str,
        help="Format to convert output into (e.g., mp4, mov). Output can be a filename without extension."
    )
    parser.add_argument(
        "--preset", required=True, type=str, choices=VIDEO_PRESETS.keys(),
        help="Preset dimension (e.g., 1080p, instagram_reels)."
    )
    parser.add_argument(
        "--translate", type=str, choices=["yes", "no"], default="no",
        help="Stretch to fit dimensions exactly ('yes') or maintain aspect ratio with padding ('no')."
    )
    # NOTE: input/output/force provided by top-level CLI.

def _resolve_output_path(output: Path, fmt: str) -> Path:
    """
    If user supplied an extension already and it matches fmt, keep it.
    If they supplied a different extension, replace it with fmt.
    If no extension, append fmt.
    """
    suffix = output.suffix.lower().lstrip(".")
    if suffix == fmt.lower():
        return output
    return output.with_suffix(f".{fmt}")

def run(args):
    output_path = Path(args.output)
    clean_output = _resolve_output_path(output_path, args.output_format)

    # Ensure destination folder exists
    clean_output.parent.mkdir(parents=True, exist_ok=True)

    if clean_output.exists() and not getattr(args, "force", False):
        print(f"❌ {clean_output} already exists. Use --force to overwrite.")
        sys.exit(1)

    if args.preset not in VIDEO_PRESETS:
        print(f"❌ Invalid preset: {args.preset}. Available presets: {', '.join(VIDEO_PRESETS.keys())}")
        sys.exit(1)

    target_width, target_height = VIDEO_PRESETS[args.preset]

    # Filter graph (keep your translate semantics)
    if args.translate == "yes":
        vf = (
            f"scale={target_width}:{target_height}:force_original_aspect_ratio=disable,"
            f"setsar=1,setdar={target_width}/{target_height}"
        )
    else:
        vf = (
            f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,"
            f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2,"
            f"setsar=1,setdar={target_width}/{target_height}"
        )

    command = [
        "ffmpeg",
        "-i", str(args.input),

        # Map robustly: succeed even if the source has no audio
        "-map", "0:v:0",
        "-map", "0:a?:0",

        "-vf", vf,
        "-c:v", "libx264",
        "-b:v", "5000k",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",

        "-c:a", "aac",
        "-b:a", "160k",
        "-ar", "48000",

        "-movflags", "+faststart",

        str(clean_output),
    ]

    if getattr(args, "force", False):
        command = command[:1] + ["-y"] + command[1:]

    run_ffmpeg_with_progress(command, args.input, clean_output)