from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

PRESETS = {
    "shorts_1080x1920": (1080, 1920),   # TikTok / Reels / YouTube Shorts (9:16)
    "portrait_1080x1350": (1080, 1350), # 4:5
    "square_1080x1080": (1080, 1080),
}


def register_arguments(parser):
    parser.description = (
        "Converts a video to vertical Shorts/Reels/TikTok format. Instead of black "
        "letterbox bars, the empty space is filled with an enlarged, blurred copy of "
        "the same video, with the original shot centered and fully visible on top."
    )
    parser.add_argument(
        "--preset",
        choices=PRESETS.keys(),
        default="shorts_1080x1920",
        help="Output frame size. Ignored if --width/--height are both set."
    )
    parser.add_argument(
        "--width",
        type=int,
        default=None,
        help="Custom output width. Must be set together with --height."
    )
    parser.add_argument(
        "--height",
        type=int,
        default=None,
        help="Custom output height. Must be set together with --width."
    )
    parser.add_argument(
        "--blur-sigma",
        type=float,
        default=20.0,
        help="Gaussian blur strength for the background fill layer. Higher = blurrier. 0 = sharp enlarged background, no blur."
    )


def run(args):
    if (args.width is None) != (args.height is None):
        raise SystemExit("❌ --width and --height must be set together, or not at all.")

    if args.width and args.height:
        w, h = args.width, args.height
    else:
        w, h = PRESETS[args.preset]

    filter_complex = (
        f"[0:v]split=2[fg0][bg0];"
        f"[bg0]scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h},setsar=1,gblur=sigma={args.blur_sigma}[bg];"
        f"[fg0]scale={w}:{h}:force_original_aspect_ratio=decrease,setsar=1[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
    )

    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-c:a", "copy",
        args.output
    ]

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
