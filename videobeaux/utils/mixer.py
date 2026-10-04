"""Small helpers shared by the video-mixer style programs (Layer Blend, Picture-in-Picture, Quad Split...)."""
from __future__ import annotations

from videobeaux.utils.keying import ff_color  # noqa: F401  (re-exported: '#RRGGBB' -> '0xRRGGBB')


def even(n) -> int:
    n = int(round(n))
    return max(2, n - n % 2)


def fit_chain(fit: str, W: int, H: int) -> str:
    """Scale a clip into a W×H box: cover (fill + crop), contain (fit + black bars) or stretch."""
    if fit == "contain":
        return f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black"
    if fit == "stretch":
        return f"scale={W}:{H}"
    return f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"


def encode_args(crf: int, fps: float) -> list:
    """libx264 + BT.709 tags, matching the rest of the toolkit."""
    return ["-r", f"{fps:.6f}", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-movflags", "+faststart"]
