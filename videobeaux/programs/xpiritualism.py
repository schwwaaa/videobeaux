# videobeaux/programs/xpiritualism.py
#
# Xpiritualism-style aesthetic:
# - Soft pastel glow
# - Multi-layer bloom
# - Hazy vignette (implemented via blend, not fragile options)
# - Gentle film grain
# - Optional hue shift
#
# Usage example:
#   videobeaux -P xpiritualism -i input.mp4 -o xpiri_soft.mp4 \
#     --style soft --bloom-radius 10 --bloom-strength 0.8 \
#     --saturation 1.2 --grain 8 --vignette 0.4

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress


def register_arguments(parser):
    parser.description = (
        "Xpiritualism aesthetic: multi-layer bloom + pastel spiritualizer.\n"
        "Layers:\n"
        "  - Soft bloom / glow\n"
        "  - Pastel color grade / hue shift\n"
        "  - Hazy vignette\n"
        "  - Film-like grain overlay\n"
        "Presets via --style, with tunable intensities."
    )

    # High-level “mood” preset
    parser.add_argument(
        "--style",
        choices=["soft", "deep", "cosmic"],
        default="soft",
        help=(
            "Xpiritualism style preset:\n"
            "  soft   = gentle, pastel, minimal grain (default)\n"
            "  deep   = richer contrast, stronger vignette & bloom\n"
            "  cosmic = more hue shift, grainier, dreamy"
        )
    )

    # Bloom controls
    parser.add_argument(
        "--bloom-radius",
        type=float,
        default=8.0,
        help="Bloom blur radius (luma_radius for boxblur). Higher = softer glow. Default: 8.0"
    )
    parser.add_argument(
        "--bloom-strength",
        type=float,
        default=0.7,
        help="Bloom blend opacity (0.0–1.0). Default: 0.7"
    )

    # Color & tone
    parser.add_argument(
        "--saturation",
        type=float,
        default=1.15,
        help="Overall saturation multiplier. Default: 1.15"
    )
    parser.add_argument(
        "--hue-shift",
        type=float,
        default=0.0,
        help="Hue shift in DEGREES (used in ffmpeg hue filter). Default: 0.0"
    )

    # Vignette intensity (we implement this via blend, not filter options)
    parser.add_argument(
        "--vignette",
        type=float,
        default=0.35,
        help="Vignette blend strength (0.0–1.0-ish). Default: 0.35"
    )

    # Grain
    parser.add_argument(
        "--grain",
        type=float,
        default=8.0,
        help="Film grain strength (ffmpeg noise alls parameter). Default: 8.0"
    )


def run(args):
    """
    Filtergraph structure:

      [0:v] format=yuv444p,split=4 [base][bloom_src][grain_src][vig_src];

      # Bloom layer:
      [bloom_src] boxblur -> eq (sat bump) -> [bloom]
      [base][bloom] blend=screen -> [bloomed]

      # Pastel grade + hue shift:
      [bloomed] eq (contrast/brightness/sat) + hue -> [pastel]

      # Vignette branch (no fancy options; defaults are robust):
      [vig_src] vignette [vig_mask]
      [pastel][vig_mask] blend=multiply:opacity=VIGNETTE -> [vigged]

      # Grain layer:
      [grain_src] noise -> [grain]

      # Final composite:
      [vigged][grain] blend=overlay:opacity=0.30 -> [out_v]
    """

    # Start with user-provided values
    bloom_radius = float(getattr(args, "bloom_radius", 8.0))
    bloom_strength = float(getattr(args, "bloom_strength", 0.7))
    saturation = float(getattr(args, "saturation", 1.15))
    hue_shift = float(getattr(args, "hue_shift", 0.0))
    vignette = float(getattr(args, "vignette", 0.35))
      # this is a blend opacity, not a direct vignette filter param now
    grain = float(getattr(args, "grain", 8.0))

    # Adjust based on style preset
    style = getattr(args, "style", "soft")

    if style == "deep":
        bloom_strength *= 1.15
        saturation *= 1.10
        vignette *= 1.20
        grain *= 1.05
    elif style == "cosmic":
        # if user left hue_shift at default, give it a gentle cosmic twist
        if abs(hue_shift) < 0.01:
            hue_shift = 18.0  # degrees
        bloom_strength *= 1.10
        saturation *= 1.05
        vignette *= 1.10
        grain *= 1.30

    # Clamp some values into sane ranges
    def clamp(val, lo, hi):
        return max(lo, min(hi, val))

    bloom_strength = clamp(bloom_strength, 0.0, 1.0)
    saturation = clamp(saturation, 0.5, 2.0)
    vignette = clamp(vignette, 0.0, 1.0)  # now used directly as blend opacity
    grain = clamp(grain, 0.0, 40.0)

    # Build filtergraph
    # Note: hue filter uses radians internally; we pass degrees * PI/180.
    filtergraph = (
        # Prep + split into four branches
        f"[0:v]format=yuv444p,split=4[base][bloom_src][grain_src][vig_src];"

        # Bloom branch
        f"[bloom_src]boxblur=luma_radius={bloom_radius}:luma_power=2,"
        f"eq=saturation=1.20[bloom];"

        # Screen bloom over base
        f"[base][bloom]blend=all_mode=screen:all_opacity={bloom_strength}[bloomed];"

        # Pastel EQ + hue shift
        f"[bloomed]eq=contrast=1.02:brightness=0.02:saturation={saturation},"
        f"hue=h={hue_shift}*PI/180[pastel];"

        # Vignette branch – robust: use default vignette, then multiply with pastel
        f"[vig_src]vignette[vig_mask];"
        f"[pastel][vig_mask]blend=all_mode=multiply:all_opacity={vignette}[vigged];"

        # Grain branch
        f"[grain_src]noise=alls={int(grain)}:allf=t+u[grain];"

        # Final overlay blend
        f"[vigged][grain]blend=all_mode=overlay:all_opacity=0.30[out_v]"
    )

    command = [
        "ffmpeg",
        "-err_detect", "ignore_err",
        "-fflags", "+genpts+discardcorrupt",

        "-i", args.input,

        "-filter_complex", filtergraph,
        "-map", "[out_v]",
        "-map", "0:a?",           # keep audio if present

        # Video encoding
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",

        # Audio – copy to avoid unnecessary re-encode
        "-c:a", "copy",

        args.output,
    ]

    # Respect global --force: inject -y right after 'ffmpeg'
    final_cmd = (command[:1] + ["-y"] + command[1:]) if getattr(args, "force", False) else command

    # Uncomment this if we need to debug the exact ffmpeg command later:
    # print(" ".join(f'"{c}"' if " " in c else c for c in final_cmd))

    run_ffmpeg_with_progress(final_cmd, args.input, args.output)
