# from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
# from pathlib import Path
# import sys
# import math

# # Video dimension presets (unchanged)
# VIDEO_PRESETS = {
#     "sd": (320, 240), "720hd": (640, 360), "1080hd": (960, 540), "widescreen": (320, 180),
#     "portrait1080": (1080, 1620), "480p": (640, 480), "576p": (720, 576), "720p": (1280, 720),
#     "1080p": (1920, 1080), "1440p": (2560, 1440), "4k": (3840, 2160), "8k": (7680, 4320),
#     "vga": (640, 480), "qvga": (320, 240), "wvga": (800, 480), "svga": (800, 600),
#     "xga": (1024, 768), "wxga": (1280, 800), "sxga": (1280, 1024), "uxga": (1600, 1200),
#     "wuxga": (1920, 1200), "qwxga": (2048, 1152), "qhd": (2560, 1440), "wqxga": (2560, 1600),
#     "5k": (5120, 2880), "portrait720": (720, 1280), "portrait4k": (2160, 3840),
#     "square1080": (1080, 1080), "square720": (720, 720), "cinema4k": (4096, 2160),
#     "ultrawide1080": (2560, 1080), "ultrawide1440": (3440, 1440),
#     "instagram_feed": (1080, 1080), "instagram_reels": (1080, 1920),
#     "instagram_stories": (1080, 1920), "tiktok_video": (1080, 1920),
#     "youtube_standard": (1920, 1080), "youtube_shorts": (1080, 1920),
#     "facebook_feed": (1080, 1080), "facebook_stories": (1080, 1920),
#     "twitter_video": (1280, 720), "twitter_square": (1080, 1080),
#     "linkedin_video": (1920, 1080), "linkedin_square": (1080, 1080),
#     "snapchat_video": (1080, 1920), "pinterest_video": (1080, 1920),
#     "pinterest_square": (1000, 1000)
# }

# def register_arguments(parser):
#     parser.description = (
#         "Converts an input video to a specified preset dimension. "
#         "Choose how to handle aspect ratio: pad, fit, fill-crop, or stretch. "
#         "Use --portrait-full to force a 9:16 full-frame vertical output."
#     )
#     parser.add_argument(
#         "--output-format", required=True, type=str,
#         help="Format to convert output into (e.g., mp4, mov). Output can be a filename without extension."
#     )
#     parser.add_argument(
#         "--preset", required=True, type=str, choices=VIDEO_PRESETS.keys(),
#         help="Preset dimension (e.g., 1080p, instagram_reels)."
#     )

#     # Flexible aspect behavior. If provided, overrides --translate.
#     parser.add_argument(
#         "--mode",
#         choices=["pad", "fit", "fill", "fill_crop", "stretch"],
#         help=(
#             "Aspect behavior: "
#             "'pad' (letter/pillarbox to exact size), "
#             "'fit' (scale to fit within box, no pad), "
#             "'fill'/'fill_crop' (cover box, center-crop to exact size), "
#             "'stretch' (ignore AR, stretch to exact size). "
#             "If omitted, falls back to --translate (no→pad, yes→stretch)."
#         )
#     )

#     # Back-compat with existing calls
#     parser.add_argument(
#         "--translate", type=str, choices=["yes", "no"], default="no",
#         help="(Deprecated in favor of --mode) 'yes' = stretch; 'no' = pad."
#     )

#     # NEW: Force a true full-height Portrait 9:16 canvas (no borders).
#     parser.add_argument(
#         "--portrait-full", action="store_true",
#         help=(
#             "Force output to 9:16 portrait and fill the frame (center-crop). "
#             "Uses the larger side of the preset as the output HEIGHT, and sets WIDTH = round(HEIGHT*9/16). "
#             "Example: 1080p -> 1080x1920, 4k -> 2160x3840."
#         )
#     )
#     # NOTE: input/output/force provided by top-level CLI.

# def _resolve_output_path(output: Path, fmt: str) -> Path:
#     suffix = output.suffix.lower().lstrip(".")
#     if suffix == fmt.lower():
#         return output
#     return output.with_suffix(f".{fmt}")

# def _even(x: int) -> int:
#     return x if x % 2 == 0 else x - 1

# def _portrait_full_dims(w: int, h: int) -> tuple[int, int]:
#     """
#     Use the larger side of the preset as HEIGHT, set WIDTH for exact 9:16.
#     Ensures even dimensions (some encoders require mod2).
#     """
#     H = max(w, h)
#     W = int(round(H * 9 / 16))
#     return _even(W), _even(H)

# def _vf_for_mode(mode: str, w: int, h: int) -> str:
#     """
#     - pad: keep AR, add borders to reach exact WxH
#     - fit: keep AR, scale to fit within WxH (no padding)
#     - fill_crop: keep AR, scale to cover WxH then crop center to exact WxH
#     - stretch: ignore AR, force exact WxH
#     """
#     if mode == "stretch":
#         return f"scale={w}:{h}:force_original_aspect_ratio=disable,setsar=1,setdar={w}/{h}"

#     if mode == "fit":
#         return f"scale={w}:{h}:force_original_aspect_ratio=decrease,setsar=1"

#     if mode in ("fill", "fill_crop"):
#         return (
#             f"scale={w}:{h}:force_original_aspect_ratio=increase,"
#             f"crop={w}:{h}:(in_w-out_w)/2:(in_h-out_h)/2,setsar=1,setdar={w}/{h}"
#         )

#     # default = pad
#     return (
#         f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
#         f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,setdar={w}/{h}"
#     )

# def run(args):
#     output_path = Path(args.output)
#     clean_output = _resolve_output_path(output_path, args.output_format)

#     # Ensure destination folder exists
#     clean_output.parent.mkdir(parents=True, exist_ok=True)

#     if clean_output.exists() and not getattr(args, "force", False):
#         print(f"❌ {clean_output} already exists. Use --force to overwrite.")
#         sys.exit(1)

#     if args.preset not in VIDEO_PRESETS:
#         print(f"❌ Invalid preset: {args.preset}. Available presets: {', '.join(VIDEO_PRESETS.keys())}")
#         sys.exit(1)

#     target_width, target_height = VIDEO_PRESETS[args.preset]

#     # If full portrait requested, override canvas to strict 9:16 using preset's larger side.
#     if getattr(args, "portrait_full", False):
#         target_width, target_height = _portrait_full_dims(target_width, target_height)
#         # Force a fill/crop behavior to guarantee full-frame portrait (no borders).
#         chosen_mode = "fill_crop"
#     else:
#         # Choose behavior: --mode overrides legacy --translate
#         chosen_mode = args.mode if args.mode else ("stretch" if args.translate == "yes" else "pad")

#     vf = _vf_for_mode(chosen_mode, target_width, target_height)

#     command = [
#         "ffmpeg",
#         "-i", str(args.input),

#         # Map robustly: succeed even if the source has no audio
#         "-map", "0:v:0",
#         "-map", "0:a:0?",  # optional first audio track

#         "-vf", vf,
#         "-c:v", "libx264",
#         "-b:v", "5000k",
#         "-pix_fmt", "yuv420p",
#         "-preset", "medium",

#         "-c:a", "aac",
#         "-b:a", "160k",
#         "-ar", "48000",
#         "-movflags", "+faststart",

#         str(clean_output),
#     ]

#     if getattr(args, "force", False):
#         command = command[:1] + ["-y"] + command[1:]

#     run_ffmpeg_with_progress(command, args.input, clean_output)

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from pathlib import Path
import sys

# Video dimension presets (unchanged)
VIDEO_PRESETS = {
    "sd": (320, 240), "720hd": (640, 360), "1080hd": (960, 540), "widescreen": (320, 180),
    "portrait1080": (1080, 1620), "480p": (640, 480), "576p": (720, 576), "720p": (1280, 720),
    "1080p": (1920, 1080), "1440p": (2560, 1440), "4k": (3840, 2160), "8k": (7680, 4320),
    "vga": (640, 480), "qvga": (320, 240), "wvga": (800, 480), "svga": (800, 600),
    "xga": (1024, 768), "wxga": (1280, 800), "sxga": (1280, 1024), "uxga": (1600, 1200),
    "wuxga": (1920, 1200), "qwxga": (2048, 1152), "qhd": (2560, 1440), "wqxga": (2560, 1600),
    "5k": (5120, 2880), "portrait720": (720, 1280), "portrait4k": (2160, 3840),
    "square1080": (1080, 1080), "square720": (720, 720), "cinema4k": (4096, 2160),
    "ultrawide1080": (2560, 1080), "ultrawide1440": (3440, 1440),
    "instagram_feed": (1080, 1080), "instagram_reels": (1080, 1920),
    "instagram_stories": (1080, 1920), "tiktok_video": (1080, 1920),
    "youtube_standard": (1920, 1080), "youtube_shorts": (1080, 1920),
    "facebook_feed": (1080, 1080), "facebook_stories": (1080, 1920),
    "twitter_video": (1280, 720), "twitter_square": (1080, 1080),
    "linkedin_video": (1920, 1080), "linkedin_square": (1080, 1080),
    "snapchat_video": (1080, 1920), "pinterest_video": (1080, 1920),
    "pinterest_square": (1000, 1000)
}

def register_arguments(parser):
    parser.description = (
        "Converts an input video to a specified preset dimension. "
        "Choose how to handle aspect ratio: pad, fit, fill-crop, or stretch. "
        "Use --portrait-full to force a 9:16 full-frame vertical output."
    )
    parser.add_argument("--output-format", required=True, type=str,
                        help="Format for output file extension (e.g., mp4, mov).")
    parser.add_argument("--preset", required=True, type=str, choices=VIDEO_PRESETS.keys(),
                        help="Preset dimension (e.g., 1080p, instagram_reels).")

    # Flexible aspect behavior (overrides --translate when provided)
    parser.add_argument("--mode",
                        choices=["pad", "fit", "fill", "fill_crop", "stretch"],
                        help="pad: keep AR + borders; fit: keep AR, no pad; "
                             "fill/fill_crop: cover + center-crop; stretch: ignore AR.")

    # Back-compat
    parser.add_argument("--translate", type=str, choices=["yes", "no"], default="no",
                        help="(Deprecated) yes=stretch, no=pad if --mode not set.")

    # NEW: crop/pad alignment & cosmetics
    parser.add_argument("--anchor",
                        choices=["center", "top", "bottom", "left", "right",
                                 "top_left", "top_right", "bottom_left", "bottom_right"],
                        default="center",
                        help="Where to bias the crop or padding.")
    parser.add_argument("--pad-color", default="#000000",
                        help="Padding color for --mode pad. Hex like #000000, #FFFFFF.")
    parser.add_argument("--scale-flags",
                        choices=["lanczos", "bicubic", "bilinear", "neighbor"],
                        default="lanczos",
                        help="Scaler kernel for the scale filter.")

    # 9:16 portrait override (no borders)
    parser.add_argument("--portrait-full", action="store_true",
                        help="Force 9:16 portrait output and fill (cover + crop).")

def _resolve_output_path(output: Path, fmt: str) -> Path:
    sfx = output.suffix.lower().lstrip(".")
    return output if sfx == fmt.lower() else output.with_suffix(f".{fmt}")

def _even(x: int) -> int:
    return x if x % 2 == 0 else x - 1

def _portrait_full_dims(w: int, h: int) -> tuple[int, int]:
    # Use the larger side of the preset as HEIGHT; WIDTH = round(HEIGHT*9/16)
    H = max(w, h)
    W = int(round(H * 9 / 16))
    return _even(W), _even(H)

def _color_hex_to_ffmpeg(color: str) -> str:
    c = color.strip()
    if c.startswith("#"):
        c = c[1:]
    # Accept 3/6 hex; normalize to 6
    if len(c) == 3:
        c = "".join(ch*2 for ch in c)
    return f"0x{c}"

def _anchor_offsets(anchor: str, axis_len: str) -> tuple[str, str]:
    """
    Return (x_expr, y_expr) for pad or crop offsets based on anchor.
    axis_len is 'pad' or 'crop' context indicating how to compute expressions.
    """
    # Center expressions
    cx = "(ow-iw)/2" if axis_len == "pad" else "(in_w-out_w)/2"
    cy = "(oh-ih)/2" if axis_len == "pad" else "(in_h-out_h)/2"

    if anchor == "center": return cx, cy
    if anchor == "top": return cx, ( "0" if axis_len == "pad" else "0")
    if anchor == "bottom": return cx, ( "(oh-ih)" if axis_len == "pad" else "(in_h-out_h)" )
    if anchor == "left": return ( "0" if axis_len == "pad" else "0"), cy
    if anchor == "right": return ( "(ow-iw)" if axis_len == "pad" else "(in_w-out_w)"), cy
    if anchor == "top_left": return ( "0" if axis_len == "pad" else "0"), ( "0" if axis_len == "pad" else "0")
    if anchor == "top_right": return ( "(ow-iw)" if axis_len == "pad" else "(in_w-out_w)"), ( "0" if axis_len == "pad" else "0")
    if anchor == "bottom_left": return ( "0" if axis_len == "pad" else "0"), ( "(oh-ih)" if axis_len == "pad" else "(in_h-out_h)")
    if anchor == "bottom_right": return ( "(ow-iw)" if axis_len == "pad" else "(in_w-out_w)"), ( "(oh-ih)" if axis_len == "pad" else "(in_h-out_h)")
    return cx, cy

def _vf_for_mode(mode: str, w: int, h: int, anchor: str, pad_color_hex: str, scale_flags: str) -> str:
    color = _color_hex_to_ffmpeg(pad_color_hex)

    if mode == "stretch":
        return f"scale={w}:{h}:flags={scale_flags}:force_original_aspect_ratio=disable,setsar=1,setdar={w}/{h}"

    if mode == "fit":
        # Keep AR, fit into WxH; no padding
        return f"scale={w}:{h}:flags={scale_flags}:force_original_aspect_ratio=decrease,setsar=1"

    if mode in ("fill", "fill_crop"):
        # Cover, then crop based on anchor
        x, y = _anchor_offsets(anchor, "crop")
        return (f"scale={w}:{h}:flags={scale_flags}:force_original_aspect_ratio=increase,"
                f"crop={w}:{h}:{x}:{y},setsar=1,setdar={w}/{h}")

    # default = pad
    x, y = _anchor_offsets(anchor, "pad")
    return (f"scale={w}:{h}:flags={scale_flags}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:{x}:{y}:{color},setsar=1,setdar={w}/{h}")

def run(args):
    output_path = Path(args.output)
    clean_output = _resolve_output_path(output_path, args.output_format)
    clean_output.parent.mkdir(parents=True, exist_ok=True)

    if clean_output.exists() and not getattr(args, "force", False):
        print(f"❌ {clean_output} already exists. Use --force to overwrite.")
        sys.exit(1)

    if args.preset not in VIDEO_PRESETS:
        print(f"❌ Invalid preset: {args.preset}. Available presets: {', '.join(VIDEO_PRESETS.keys())}")
        sys.exit(1)

    target_width, target_height = VIDEO_PRESETS[args.preset]

    if getattr(args, "portrait_full", False):
        target_width, target_height = _portrait_full_dims(target_width, target_height)
        chosen_mode = "fill_crop"  # guarantee full-frame portrait
    else:
        chosen_mode = args.mode if args.mode else ("stretch" if args.translate == "yes" else "pad")

    vf = _vf_for_mode(chosen_mode, target_width, target_height, args.anchor, args.pad_color, args.scale_flags)

    command = [
        "ffmpeg",
        "-i", str(args.input),

        # Map robustly: succeed even if the source has no audio
        "-map", "0:v:0",
        "-map", "0:a:0?",  # optional first audio track

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
