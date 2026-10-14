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

from videobeaux.utils.media import ensure_audio
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.frame_pipe import probe_video

GUI_METADATA = {
    'args': {
        'input2':         {'type': 'file', 'subtype': 'video', 'label': 'Second Video'},
        'input3':         {'type': 'file', 'subtype': 'video', 'label': 'Third Video'},
        'audio-external': {'type': 'file', 'label': 'External Audio'},
        'panel_size': {'label': 'Panel size (px, 0 = match first video)', 'min': 0, 'max': 4320, 'good_min': 0, 'good_max': 1080,
                       'help': 'hstack: height of every panel; vstack: width. 0 uses the first video. Smaller = much faster.'},
        'zoom1': {'label': 'Zoom 1', 'min': 1, 'max': 4, 'step': 0.05},
        'zoom2': {'label': 'Zoom 2', 'min': 1, 'max': 4, 'step': 0.05},
        'zoom3': {'label': 'Zoom 3', 'min': 1, 'max': 4, 'step': 0.05},
    }
}


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
        "--panel_size", type=int, default=0,
        help="Panel height (hstack) / width (vstack) in pixels; 0 = match the first video. Default: 0.",
    )
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


MAX_SIDE = 7680   # keep the stacked frame within 8K so encoding stays fast


def panel_sizes(layout, dims, panel_size=0):
    """
    Panel sizes [(w, h), ...] for the three inputs. hstack: all panels share one height (the first video's, or
    `panel_size`), each keeps its own aspect ratio; vstack: all share one width. The stacked frame is capped at MAX_SIDE.
    """
    even = lambda n: max(2, int(round(n)) // 2 * 2)
    if layout == "hstack":
        h = even(panel_size or dims[0][1])
        widths = [h * w / max(1, hh) for (w, hh) in dims]
        if sum(widths) > MAX_SIDE:
            h = even(h * MAX_SIDE / sum(widths))
            widths = [h * w / max(1, hh) for (w, hh) in dims]
        return [(even(wd), h) for wd in widths]
    w = even(panel_size or dims[0][0])
    heights = [w * hh / max(1, ww) for (ww, hh) in dims]
    if sum(heights) > MAX_SIDE:
        w = even(w * MAX_SIDE / sum(heights))
        heights = [w * hh / max(1, ww) for (ww, hh) in dims]
    return [(w, even(hv)) for hv in heights]


def _build_video_filter_complex(layout, zoom1, zoom2, zoom3, sizes=None, fps=30.0):
    """
    Build the ffmpeg -filter_complex graph for VIDEO ONLY → [out_v].

    Every input is scaled to its panel size *first* (so stacking is cheap), then zoomed by cropping into the panel
    (zoom 1 = whole picture, 2 = the central half) — the output no longer grows with the zoom value.
    """
    zooms = (zoom1, zoom2, zoom3)
    for z in zooms:
        if z <= 0:
            raise ValueError("All zoom values must be > 0 (got one <= 0).")
    if layout not in ("hstack", "vstack"):
        raise ValueError(f"Unsupported layout: {layout}")
    sizes = sizes or [(640, 360)] * 3
    chains = []
    for i, (z, (pw, ph)) in enumerate(zip(zooms, sizes)):
        zw, zh = max(pw, int(round(pw * max(z, 1.0)))), max(ph, int(round(ph * max(z, 1.0))))
        zw, zh = zw // 2 * 2, zh // 2 * 2
        crop = f",crop={pw}:{ph}"      # always: rounding in "increase" can overshoot the panel by a pixel
        chains.append(f"[{i}:v]fps={fps:.6f},scale={zw}:{zh}:force_original_aspect_ratio=increase{crop},setsar=1[p{i}]")
    chains.append(f"[p0][p1][p2]{layout}=inputs=3:shortest=1,format=yuv420p[out_v]")
    return ";".join(chains)


def run(args):
    # audio filter graphs need an audio track on every input
    if getattr(args, 'input', None):
        args.input = ensure_audio(args.input)
    if getattr(args, 'input2', None):
        args.input2 = ensure_audio(args.input2)
    if getattr(args, 'input3', None):
        args.input3 = ensure_audio(args.input3)
    # --- Build VIDEO filtergraph ---
    infos = [probe_video(args.input), probe_video(args.input2), probe_video(args.input3)]
    sizes = panel_sizes(args.layout, [(i.width, i.height) for i in infos], getattr(args, "panel_size", 0) or 0)
    video_filter = _build_video_filter_complex(
        layout=args.layout, zoom1=args.zoom1, zoom2=args.zoom2, zoom3=args.zoom3, sizes=sizes, fps=infos[0].fps,
    )
    tw = sum(w for w, _ in sizes) if args.layout == "hstack" else sizes[0][0]
    th = sizes[0][1] if args.layout == "hstack" else sum(h for _, h in sizes)
    print(f"ℹ️  Triptych output: {tw}x{th} ({args.layout}, panels {sizes})", flush=True)

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
