# videobeaux/programs/triptych.py
#
# "triptych" – arrange three videos in a symmetric layout
# Layouts:
#   - hstack : three videos side-by-side horizontally
#   - vstack : three videos stacked vertically
#
# Audio modes:
#   1 : play audio from video 1 (with --vol1)
#   2 : play audio from video 2 (with --vol2)
#   3 : play audio from video 3 (with --vol3)
#   4 : mix audio from all three videos (with --vol1/2/3)
#   5 : mute (no audio track)
#   6 : external audio track (--audio-external)
#
# Video graph is always in -filter_complex.
# Audio is:
#   - for modes 1,2,3,6: handled via -map and optional -filter:a
#   - for mode 4: mixed in -filter_complex
#   - for mode 5: disabled with -an

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress


def register_arguments(parser):
    parser.description = (
        "Compose three videos into a symmetric triptych layout.\n"
        "Layouts:\n"
        "  - hstack : three videos side-by-side horizontally\n"
        "  - vstack : three videos stacked vertically\n\n"
        "Audio modes:\n"
        "  1 : play audio from video 1\n"
        "  2 : play audio from video 2\n"
        "  3 : play audio from video 3\n"
        "  4 : mix audio from all three videos\n"
        "  5 : mute (no audio track)\n"
        "  6 : external audio track (requires --audio-external)\n"
    )

    # Additional inputs (input #1 is the global -i / --input)
    parser.add_argument(
        "--input2",
        required=True,
        help="Second input video (mp4 recommended).",
    )
    parser.add_argument(
        "--input3",
        required=True,
        help="Third input video (mp4 recommended).",
    )

    # Layout selection (diag removed)
    parser.add_argument(
        "--layout",
        choices=["hstack", "vstack"],
        default="hstack",
        help="Triptych layout: hstack (default) or vstack.",
    )

    # Per-video zoom controls
    parser.add_argument(
        "--zoom1",
        type=float,
        default=1.0,
        help="Zoom factor for input #1 (global -i). >1 zooms in, <1 zooms out.",
    )
    parser.add_argument(
        "--zoom2",
        type=float,
        default=1.0,
        help="Zoom factor for input #2. >1 zooms in, <1 zooms out.",
    )
    parser.add_argument(
        "--zoom3",
        type=float,
        default=1.0,
        help="Zoom factor for input #3. >1 zooms in, <1 zooms out.",
    )

    # Audio mode selector
    parser.add_argument(
        "--audio-mode",
        choices=["1", "2", "3", "4", "5", "6"],
        default="1",
        help=(
            "Audio behavior:\n"
            " 1 = video 1 audio only\n"
            " 2 = video 2 audio only\n"
            " 3 = video 3 audio only\n"
            " 4 = mix audio from all three videos\n"
            " 5 = mute (no audio track)\n"
            " 6 = external audio (requires --audio-external)\n"
        ),
    )

    # Per-video volume controls (linear multiplier)
    parser.add_argument(
        "--vol1",
        type=float,
        default=1.0,
        help="Volume multiplier for audio from video 1 (default 1.0).",
    )
    parser.add_argument(
        "--vol2",
        type=float,
        default=1.0,
        help="Volume multiplier for audio from video 2 (default 1.0).",
    )
    parser.add_argument(
        "--vol3",
        type=float,
        default=1.0,
        help="Volume multiplier for audio from video 3 (default 1.0).",
    )

    # External audio (for mode 6)
    parser.add_argument(
        "--audio-external",
        help="External audio file (used when --audio-mode 6).",
    )

    # Basic encoding controls
    parser.add_argument(
        "--x264-preset",
        default="medium",
        help="libx264 preset. Default: medium",
    )
    parser.add_argument(
        "--crf",
        type=float,
        default=18.0,
        help="CRF for libx264. Lower = higher quality. Default: 18",
    )


def _build_video_filter_complex(layout, zoom1, zoom2, zoom3):
    """
    Build the ffmpeg -filter_complex graph for VIDEO ONLY.

    Outputs:
      - [out_v]
    """
    # Sanity: zoom must be > 0
    for z in (zoom1, zoom2, zoom3):
        if z <= 0:
            raise ValueError("All zoom values must be > 0 (got one <= 0).")

    chains = []

    # Base zoomed streams
    chains.append(f"[0:v]scale=iw*{zoom1}:ih*{zoom1},setsar=1[v0z]")
    chains.append(f"[1:v]scale=iw*{zoom2}:ih*{zoom2},setsar=1[v1z]")
    chains.append(f"[2:v]scale=iw*{zoom3}:ih*{zoom3},setsar=1[v2z]")

    if layout == "hstack":
        # Horizontal triptych: match heights using scale2ref
        chains.append("[v1z][v0z]scale2ref=w=-1:h=ih[v1m][v0m]")
        chains.append("[v2z][v0m]scale2ref=w=-1:h=ih[v2m][v0mm]")
        chains.append(
            "[v0mm][v1m][v2m]hstack=inputs=3:shortest=1,format=yuv420p[out_v]"
        )

    elif layout == "vstack":
        # Vertical triptych: match widths using scale2ref
        chains.append("[v1z][v0z]scale2ref=w=iw:h=-1[v1m][v0m]")
        chains.append("[v2z][v0m]scale2ref=w=iw:h=-1[v2m][v0mm]")
        chains.append(
            "[v0mm][v1m][v2m]vstack=inputs=3:shortest=1,format=yuv420p[out_v]"
        )

    else:
        raise ValueError(f"Unsupported layout: {layout}")

    return ";".join(chains)


def run(args):
    # --- Build VIDEO filtergraph ---
    video_filter = _build_video_filter_complex(
        layout=args.layout,
        zoom1=args.zoom1,
        zoom2=args.zoom2,
        zoom3=args.zoom3,
    )

    # --- ffmpeg base command & inputs ---
    command = [
        "ffmpeg",
        "-err_detect",
        "ignore_err",
        "-fflags",
        "+genpts+discardcorrupt",
        # Three video inputs (global -i is args.input)
        "-i",
        args.input,
        "-i",
        args.input2,
        "-i",
        args.input3,
    ]

    # External audio input for mode 6
    if args.audio_mode == "6":
        if not args.audio_external:
            raise ValueError(
                "audio-mode 6 (external) requires --audio-external to be set."
            )
        command.extend(["-i", args.audio_external])

    # --- Build full filter_complex (video + optional audio mix) ---
    filter_complex = video_filter

    if args.audio_mode == "4":
        # Mix audio from all three video inputs with independent volumes
        audio_chains = [
            f"[0:a]volume={args.vol1}[a0]",
            f"[1:a]volume={args.vol2}[a1]",
            f"[2:a]volume={args.vol3}[a2]",
            "[a0][a1][a2]amix=inputs=3:normalize=0[out_a]",
        ]
        filter_complex = filter_complex + ";" + ";".join(audio_chains)

    # Attach filter_complex (always at least video)
    command.extend(["-filter_complex", filter_complex])

    # Always map the composed video
    command.extend(["-map", "[out_v]"])

    # --- Audio mapping depending on mode ---
    if args.audio_mode == "1":
        # Audio from video 1, with volume vol1
        command.extend(
            [
                "-map",
                "0:a?",
                "-filter:a",
                f"volume={args.vol1}",
                "-c:a",
                "aac",
            ]
        )

    elif args.audio_mode == "2":
        # Audio from video 2, with volume vol2
        command.extend(
            [
                "-map",
                "1:a?",
                "-filter:a",
                f"volume={args.vol2}",
                "-c:a",
                "aac",
            ]
        )

    elif args.audio_mode == "3":
        # Audio from video 3, with volume vol3
        command.extend(
            [
                "-map",
                "2:a?",
                "-filter:a",
                f"volume={args.vol3}",
                "-c:a",
                "aac",
            ]
        )

    elif args.audio_mode == "4":
        # Mixed audio from filter_complex
        command.extend(
            [
                "-map",
                "[out_a]",
                "-c:a",
                "aac",
            ]
        )

    elif args.audio_mode == "5":
        # Mute: no audio at all
        command.append("-an")

    elif args.audio_mode == "6":
        # External audio (4th input, index 3), no extra volume filter
        command.extend(
            [
                "-map",
                "3:a?",
                "-c:a",
                "aac",
            ]
        )

    else:
        raise ValueError(f"Unsupported audio_mode: {args.audio_mode}")

    # --- Video codec/options ---
    command.extend(
        [
            "-c:v",
            "libx264",
            "-preset",
            f"{args.x264_preset}",
            "-crf",
            f"{args.crf}",
            "-pix_fmt",
            "yuv420p",
            args.output,
        ]
    )

    # Respect global --force (inject -y after 'ffmpeg')
    final_cmd = (
        command[:1] + ["-y"] + command[1:]
        if getattr(args, "force", False)
        else command
    )

    run_ffmpeg_with_progress(final_cmd, args.input, args.output)
