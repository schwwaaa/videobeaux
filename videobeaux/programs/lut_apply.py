# videobeaux/programs/lut_apply.py
# Color Correction / LUT Apply — requires --outfile (no -o/--output fallback)

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

def _is_hi_bit_pf(pix_fmt: str) -> bool:
    if not pix_fmt:
        return False
    pf = pix_fmt.lower()
    return "p10" in pf or "p12" in pf

def register_arguments(parser):
    parser.description = (
        "Color Correction / LUT Apply\n"
        "• Apply a 3D LUT (.cube/.3dl) with adjustable intensity.\n"
        "• Basic color tweaks: brightness, contrast, saturation, gamma.\n"
        "• Uses only --outfile for output (no -o/--output)."
    )

    # Program-specific output ONLY (no short alias; avoids global -o)
    parser.add_argument(
        "--outfile",
        required=True,
        help="Output video file (required)"
    )

    # Optional explicit vcodec; if omitted we auto-pick based on pix_fmt
    parser.add_argument(
        "--vcodec",
        choices=["libx264", "libx265", "prores_ks", "dnxhd"],
        help="Force a specific video codec (else auto-select)."
    )

    # LUT controls
    parser.add_argument("--lut", help="Path to a 3D LUT file (.cube, .3dl).")
    parser.add_argument("--interp", choices=["tetrahedral", "trilinear", "nearest"],
                        default="tetrahedral", help="LUT interpolation. Default: tetrahedral")
    parser.add_argument("--intensity", type=float, default=1.0,
                        help="Mix of LUT with original [0.0–1.0]. Default: 1.0")

    # EQ (basic color)
    parser.add_argument("--brightness", type=float, default=0.0, help="Brightness offset [-1..1].")
    parser.add_argument("--contrast",   type=float, default=1.0, help="Contrast multiplier [0..2].")
    parser.add_argument("--saturation", type=float, default=1.0, help="Saturation multiplier [0..3].")
    parser.add_argument("--gamma",      type=float, default=1.0, help="Gamma multiplier [0.1..10].")

    # Output / encode
    parser.add_argument("--pix-fmt", default="yuv420p",
                        help="Output pixel format (e.g., yuv420p, yuv422p10le).")
    parser.add_argument("--x264-preset", default="medium", help="Encoder preset (x264/x265). Default: medium")
    parser.add_argument("--crf", type=float, default=18.0,
                        help="CRF (x264/x265). Lower = higher quality.")
    parser.add_argument("--copy-audio", action="store_true",
                        help="Copy audio instead of re-encoding.")

    # NOTE: Do NOT declare --force here — it’s global. We’ll still read args.force if present.

def run(args):
    infile = getattr(args, "input", None)  # provided by global CLI
    outfile = args.outfile                 # required here
    if not infile:
        raise SystemExit("❌ Missing input. Provide -i/--input globally.")

    # EQ chain
    eq = (
        f"eq=brightness={args.brightness}:"
        f"contrast={args.contrast}:"
        f"saturation={args.saturation}:"
        f"gamma={args.gamma}"
    )

    fg_parts = []

    # LUT branch w/ intensity blend
    if args.lut:
        intensity = max(0.0, min(1.0, float(args.intensity)))
        if intensity >= 0.9999:
            fg_parts.append(f"[0:v]lut3d=file='{args.lut}':interp={args.interp}[v_lut]")
            src = "[v_lut]"
        elif intensity <= 0.0001:
            src = "[0:v]"
        else:
            fg_parts.append(
                f"[0:v]split[v_o][v_b];"
                f"[v_b]lut3d=file='{args.lut}':interp={args.interp}[v_lut];"
                f"[v_o][v_lut]blend=all_mode=normal:all_opacity={intensity}[v_mix]"
            )
            src = "[v_mix]"
    else:
        src = "[0:v]"

    fg_parts.append(f"{src},{eq}[v_eq]")
    fg_parts.append(f"[v_eq]format={args.pix_fmt}[out_v]")
    filtergraph = ";".join(fg_parts)

    # Decide codec (auto if not forced)
    pix_fmt = args.pix_fmt
    vcodec = args.vcodec or ("libx265" if _is_hi_bit_pf(pix_fmt) else "libx264")

    # Optional audio map so silent inputs don’t fail
    audio_map = ["-map", "0:a?"]
    audio_codec = ["-c:a", "copy" if getattr(args, "copy_audio", False) else "aac"]

    cmd = [
        "ffmpeg",
        "-err_detect", "ignore_err",
        "-fflags", "+genpts+discardcorrupt",
        "-i", infile,
        "-filter_complex", filtergraph,
        "-map", "[out_v]",
        *audio_map,
        "-c:v", vcodec,
        "-crf", f"{args.crf}",
        "-preset", f"{args.x264_preset}",  # accepted by x264/x265
        *audio_codec,
        "-pix_fmt", f"{pix_fmt}",
        outfile
    ]

    # Respect global --force if present (we didn’t declare it locally)
    final_cmd = (cmd[:1] + ["-y"] + cmd[1:]) if getattr(args, "force", False) else cmd
    run_ffmpeg_with_progress(final_cmd, infile, outfile)
