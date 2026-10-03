# videobeaux/programs/tonemap_hdr_sdr.py
# HDR → SDR tone mapping using zscale + tonemap (default: hable).
# Matches videobeaux program structure: register_arguments() + run(args).

import subprocess

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress, ffmpeg_has_filter

# The GUI always supplies the output path (-o) from the connected Output node,
# so this program-specific fallback flag is hidden from the node's fields.
GUI_METADATA = {'args': {'outfile': {'hidden': True}}}


HDR_TRANSFERS = {"smpte2084", "arib-std-b67"}   # PQ, HLG


def _probe_transfer(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=color_transfer", "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True)
    return (r.stdout or "").strip() or None


def register_arguments(parser):
    parser.description = (
        "HDR → SDR Tone Map\n"
        "Convert HDR (PQ/HLG) video to SDR (BT.709) using zscale + tonemap.\n"
        "Default mapping is Hable with mild desaturation and 1000-nit peak."
    )
    # IO — prefer the global -o/--output when given (e.g. the GUI always
    # sets it); --outfile is a fallback for direct CLI use without -o.
    parser.add_argument(
        "--outfile",
        required=False,
        help="Output file path for the SDR result. Falls back to -o/--output when omitted."
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
        help="Peak brightness of the HDR source in nits (1000 is typical, 4000 for some masters). Default: 1000"
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

    outfile = getattr(args, "output", None) or args.outfile
    if not outfile:
        raise SystemExit("❌ Missing output. Provide -o/--output or --outfile.")

    # zscale comes from libzimg, which some ffmpeg builds (e.g. a minimal
    # Homebrew/dev build) omit. Fail up front with a clear reason instead of
    # a cryptic "Filter not found" from deep inside the filtergraph.
    if not ffmpeg_has_filter("zscale"):
        raise SystemExit(
            "❌ This ffmpeg build has no 'zscale' filter (needs libzimg), which HDR→SDR "
            "tone mapping requires. Install or point PATH at an ffmpeg built with "
            "--enable-libzimg. On macOS: `brew install ffmpeg-full` (keg-only — the GUI picks it up automatically; for the CLI run with PATH=/opt/homebrew/opt/ffmpeg-full/bin:$PATH)."
        )

    # Only PQ (HDR10 / Dolby Vision base) and HLG sources need tone mapping.
    # Running the curve over an already-SDR clip just flattens it.
    transfer = _probe_transfer(args.input)
    if transfer not in HDR_TRANSFERS:
        print(f"⚠️  Input doesn't look like HDR (transfer: {transfer or 'unknown'}) — "
              "re-encoding it unchanged instead of tone mapping.")
        filtergraph = f"format={args.pix_fmt}"
    else:
        # Canonical zimg tone-map chain: linearize against a 100-nit reference
        # white, work in float RGB with BT.709 primaries (tonemap needs float
        # gbrp), compress highlights, then convert back to BT.709 limited range.
        peak = f":peak={args.peak / 100.0:g}" if args.peak and args.peak > 0 else ""
        filtergraph = (
            "zscale=t=linear:npl=100,"
            "format=gbrpf32le,"
            "zscale=p=bt709,"
            f"tonemap=tonemap={args.algo}:desat={args.desat}{peak},"
            f"zscale=t=bt709:m=bt709:r=tv:dither={args.dither},"
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
