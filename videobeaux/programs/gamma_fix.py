import subprocess
import re
import statistics
from pathlib import Path

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

# -----------------------------
# Helpers
# -----------------------------

_YAVG_RE = re.compile(r"YAVG[:=]\s*([0-9]+(?:\.[0-9]+)?)")

def _probe_yavg_values(input_path: str, max_samples: int = 200) -> list[float]:
    """
    Run a fast ffmpeg prepass with signalstats to gather YAVG samples.
    Returns a list of YAVG values in 0..255.
    """
    # We downscale + fps limit during probe for speed, without altering stats trends much.
    # (stats before scale is ideal, but signalstats after a mild, fast scale is fine for global mean.)
    cmd = [
        "ffmpeg",
        "-hide_banner", "-nostdin",
        "-i", input_path,
        # Keep it quick: sample at ~4 fps, tiny scale, metadata only.
        "-vf", "signalstats,framestep=2,scale=iw*0.25:ih*0.25",
        "-f", "null", "-"
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    text = proc.stderr + proc.stdout

    yvals = [float(m.group(1)) for m in _YAVG_RE.finditer(text)]
    if not yvals:
        # Fallback: try again without framestep/scale if a weird codec/stream blocks it
        cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-i", input_path, "-vf", "signalstats", "-f", "null", "-"]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        text = proc.stderr + proc.stdout
        yvals = [float(m.group(1)) for m in _YAVG_RE.finditer(text)]

    if len(yvals) > max_samples:
        # Uniformly downsample the list to max_samples for median stability
        step = max(1, len(yvals) // max_samples)
        yvals = yvals[::step]

    return yvals

def _compute_eq_params(yavg_values: list[float], target_yavg: float, min_contrast: float, max_contrast: float):
    """
    Compute eq filter brightness/contrast that maps the measured median YAVG close to target.
    eq works in normalized [0..1] domain as: y' = (y - 0.5)*contrast + 0.5 + brightness

    We choose a contrast around (target/current), clamped; then derive brightness to hit target.
    Returns (contrast, brightness). Brightness is in [-1, 1]; contrast is typically [0.5, 1.5].
    """
    if not yavg_values:
        # If probing failed, do nothing (neutral)
        return 1.0, 0.0

    current = statistics.median(yavg_values)  # robust against bright/dark spikes
    # Convert 8-bit YAVG to normalized [0,1]
    y_cur = max(0.0, min(1.0, current / 255.0))
    y_tgt = max(0.0, min(1.0, target_yavg / 255.0))

    # Initial contrast guess: keep gentle moves, clamp to avoid harsh clipping
    raw_gain = (y_tgt / y_cur) if y_cur > 1e-6 else 1.0
    contrast = max(min_contrast, min(max_contrast, raw_gain))

    # Solve for brightness that maps the current median to target
    # t = (y_cur - 0.5)*c + 0.5 + b  =>  b = t - ((y_cur - 0.5)*c + 0.5)
    brightness = y_tgt - ((y_cur - 0.5) * contrast + 0.5)

    # Clamp brightness to eq valid range [-1, 1]
    brightness = max(-1.0, min(1.0, brightness))

    return contrast, brightness

def _build_filter_chain(contrast: float, brightness: float, gamma: float | None, legalize: bool, sat_boost: float) -> str:
    """
    Build the ffmpeg -vf filter chain.
    - eq for exposure normalization
    - (optional) gamma tweak
    - (optional) saturation boost
    - (optional) legalize to broadcast-safe luma/chroma (TV range)
    """
    chain = []

    # exposure/contrast/brightness normalize
    eq_parts = [f"contrast={contrast:.3f}", f"brightness={brightness:.3f}"]
    if gamma is not None and abs(gamma - 1.0) > 1e-6:
        eq_parts.append(f"gamma={gamma:.3f}")
    chain.append("eq=" + ":".join(eq_parts))

    # saturation tweak (via hsv / hue sat)
    if abs(sat_boost - 1.0) > 1e-6:
        # hue=s=multiplier; 1.10 = +10%
        chain.append(f"hue=s={sat_boost:.3f}")

    # broadcast legalize: convert from full->TV range if needed
    if legalize:
        # Use zscale to remap to TV (limited) range safely
        # rangein=auto tries to detect; range=tv enforces legal range outputs
        chain.append("zscale=range=tv")
        # yuv420p for web/broadcast delivery compat
        chain.append("format=yuv420p")

    return ",".join(chain)

# -----------------------------
# Public API expected by cli.py
# -----------------------------

def register_arguments(parser):
    parser.description = (
        "Gamma / Exposure Fix — auto-detect overall luminance and normalize for web/broadcast.\n"
        "Prepass samples luma (YAVG) with signalstats, computes friendly contrast/brightness (and optional gamma),\n"
        "and applies safe clamping if requested."
    )
    # Core behavior flags (global --input/--output/--force are provided by cli.py)
    parser.add_argument(
        "--target-yavg",
        type=float,
        default=64.0,
        help="Target average luma (0..255). ~64 is a balanced web midpoint. Try 60–70 for darker footage, 70–90 for bright."
    )
    parser.add_argument(
        "--min-contrast",
        type=float,
        default=0.80,
        help="Lower clamp for auto contrast mapping. Default 0.80."
    )
    parser.add_argument(
        "--max-contrast",
        type=float,
        default=1.35,
        help="Upper clamp for auto contrast mapping. Default 1.35."
    )
    parser.add_argument(
        "--gamma",
        type=float,
        default=1.00,
        help="Optional gamma override (1.00 = neutral). Leave at 1.00 to rely on contrast/brightness mapping."
    )
    parser.add_argument(
        "--sat",
        type=float,
        default=1.00,
        help="Optional saturation multiplier via hue filter (1.00 = unchanged). e.g., 1.10 = +10%% saturation."
    )
    parser.add_argument(
        "--legalize",
        action="store_true",
        help="Clamp output to broadcast-legal (TV) range using zscale and output yuv420p."
    )
    parser.add_argument(
        "--vcodec",
        type=str,
        default="libx264",
        help="Video codec for output. Default libx264."
    )
    parser.add_argument(
        "--crf",
        type=str,
        default="18",
        help="CRF for output quality (x264/x265). Default 18."
    )
    parser.add_argument(
        "--preset",
        type=str,
        default="medium",
        help="Encoder preset (x264/x265). Default medium."
    )
    parser.add_argument(
        "--acodec",
        type=str,
        default="aac",
        help="Audio codec. Default aac."
    )
    parser.add_argument(
        "--ab",
        type=str,
        default="160k",
        help="Audio bitrate. Default 160k."
    )

def run(args):
    # 1) Probe luminance stats
    yvals = _probe_yavg_values(args.input)
    contrast, brightness = _compute_eq_params(
        yavg_values=yvals,
        target_yavg=args.target_yavg,
        min_contrast=args.min_contrast,
        max_contrast=args.max_contrast
    )
    # If user forcibly set gamma != 1.0, honor it; otherwise pass None to omit param
    gamma = args.gamma if args.gamma and abs(args.gamma - 1.0) > 1e-6 else None

    # 2) Build filter graph
    vf = _build_filter_chain(
        contrast=contrast,
        brightness=brightness,
        gamma=gamma,
        legalize=args.legalize,
        sat_boost=args.sat
    )

    # 3) Encode
    command = [
        "ffmpeg",
        "-i", args.input,
        "-vf", vf,
        "-c:v", args.vcodec,
        "-crf", args.crf,
        "-preset", args.preset,
        "-c:a", args.acodec,
        "-b:a", args.ab,
        "-ac", "2",
        args.output
    ]

    # Use your standard progress runner that respects --force just like other programs
    run_ffmpeg_with_progress(
        (command[:1] + ["-y"] + command[1:]) if args.force else command,
        args.input,
        args.output
    )
