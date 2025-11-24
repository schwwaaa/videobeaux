# videobeaux/programs/tonemap_hdr_sdr.py
# HDR → SDR tone mapping using zscale + tonemap (default: hable).
# Matches videobeaux program structure: register_arguments() + run(args).

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

def register_arguments(parser):
    parser.description = (
        "HDR → SDR Tone Map\n"
        "Convert HDR (PQ/HLG) video to SDR (BT.709) using zscale + tonemap.\n"
        "Default mapping is Hable with mild desaturation and 1000-nit peak."
    )
    # IO
    parser.add_argument(
        "--outfile",
        required=True,
        help="Output file path for the SDR result (use this instead of the global -o)."
    )

    # Tonemap controls
    parser.add_argument(
        "--algo",
        choices=["hable", "mobius", "reinhard", "clip"],
        default="hable",
        help="Tonemap operator. Default: hable"
    )
    parser.add_argument(
        "--desat",
        type=float,
        default=0.0,
        help="Desaturate highlights during tonemap [0.0–1.0]. Default: 0.0"
    )
    parser.add_argument(
        "--peak",
        type=float,
        default=1000.0,
        help="Nominal HDR peak (nits) for linearization (zscale npl). Default: 1000"
    )
    # Output color / dithering / pixfmt
    parser.add_argument(
        "--dither",
        choices=["none", "ordered", "random", "error_diffusion"],
        default="error_diffusion",
        help="Dither mode applied in zscale prior to format(). Default: error_diffusion"
    )
    parser.add_argument(
        "--pix-fmt",
        default="yuv420p",
        help="Output pixel format. Common picks: yuv420p, yuv422p10le. Default: yuv420p"
    )
    parser.add_argument(
        "--x264-preset",
        default="medium",
        help="libx264 preset (if re-encoding). Default: medium"
    )
    parser.add_argument(
        "--crf",
        type=float,
        default=18.0,
        help="CRF when encoding with libx264. Default: 18"
    )
    parser.add_argument(
        "--copy-audio",
        action="store_true",
        help="Copy audio stream instead of re-encoding."
    )

def run(args):
    """
    Pipeline:
      1) zscale=transfer=linear:npl=PEAK        # Convert to linear using nominal peak
      2) tonemap=ALGO:desat=DESAT               # Apply tonemap curve
      3) zscale=primaries=bt709:transfer=bt709:matrix=bt709:dither=DITHER
      4) format=PIX_FMT
    Notes:
      - We set explicit BT.709 flags on the stream to keep players honest.
      - We re-encode video (libx264). Audio can be copied with --copy-audio.
    """

    outfile = args.outfile

    # Build filtergraph
    filtergraph = (
        f"zscale=transfer=linear:npl={args.peak},"
        f"tonemap={args.algo}:desat={args.desat},"
        f"zscale=primaries=bt709:transfer=bt709:matrix=bt709:dither={args.dither},"
        f"format={args.pix_fmt}"
    )

    # Core command
    command = [
        "ffmpeg",
        "-err_detect", "ignore_err",
        "-fflags", "+genpts+discardcorrupt",
        "-i", args.input,

        "-vf", filtergraph,

        # Color tags (make sure containers/players see BT.709 SDR)
        "-colorspace", "bt709",
        "-color_trc", "bt709",
        "-color_primaries", "bt709",

        # Encode video
        "-c:v", "libx264",
        "-preset", f"{args.x264_preset}",
        "-crf", f"{args.crf}",

        # Audio strategy
        "-c:a", "copy" if getattr(args, "copy_audio", False) else "aac",

        # Output path from --outfile
        outfile,
    ]

    # Respect --force like other programs (inject -y right after 'ffmpeg')
    final_cmd = (command[:1] + ["-y"] + command[1:]) if getattr(args, "force", False) else command

    # Progress helper consistent with other programs
    run_ffmpeg_with_progress(final_cmd, args.input, outfile)
