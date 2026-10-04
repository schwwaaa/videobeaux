"""
Shared building blocks for the Chroma Key and Luma Key programs (pure ffmpeg, fully offline).

The pipeline for both:  key → (spill suppression) → matte clean-up (shrink / feather / invert) →
composite over a background, or export with transparency.

The programs only differ in how they produce the matte (ffmpeg's chromakey/colorkey vs lumakey),
so they each hand `run_key` a filter-chain snippet that outputs a stream with an alpha channel.
"""
from __future__ import annotations

from pathlib import Path

from videobeaux.utils.cv import hex_to_rgb
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.frame_pipe import iter_frames, probe_video
from videobeaux.utils.media import has_audio

BACKGROUNDS = ["auto", "color", "image", "video", "transparent"]
VIEWS = ["composite", "matte", "checkerboard"]

BACKGROUND_HELP = (
    "What shows behind the subject. auto = the connected/picked Background video, else the Background image, "
    "else the Background color. transparent = no background at all: save as .webm or .mov (Output node format)."
)

# Shared GUI field descriptions (merged into each program's GUI_METADATA).
GUI_COMMON = {
    'background': {'type': 'select', 'label': 'Background', 'default': 'auto', 'choices': BACKGROUNDS,
                   'help': BACKGROUND_HELP},
    'bg_color': {'type': 'color', 'label': 'Background color', 'default': '#000000'},
    'bg_image': {'type': 'file', 'subtype': 'image', 'label': 'Background image'},
    'bg_video': {'type': 'file', 'subtype': 'video', 'label': 'Background video',
                 'help': 'Connect a video here (or browse) to put the subject on top of it. Loops if shorter.'},
    'view': {'type': 'select', 'label': 'View', 'default': 'composite', 'choices': VIEWS,
             'help': 'Use matte / checkerboard while tuning: white = kept, black = removed.'},
    'shrink': {'label': 'Edge shrink', 'min': 0, 'max': 10, 'help': 'Eat into the edge of the subject to lose fringing (pixels).'},
    'feather': {'label': 'Edge feather', 'min': 0, 'max': 10, 'help': 'Soften the edge of the matte (pixels).'},
}


def add_common_arguments(p):
    p.add_argument("--background", choices=BACKGROUNDS, default="auto", help=BACKGROUND_HELP)
    p.add_argument("--bg_color", type=str, default="#000000", help="Background color. Default: #000000.")
    p.add_argument("--bg_image", type=str, default=None, help="Background image.")
    p.add_argument("--bg_video", type=str, default=None, help="Background video (loops if shorter than the subject clip).")
    p.add_argument("--view", choices=VIEWS, default="composite",
                   help="composite = the result; matte = the cut-out mask; checkerboard = subject on a checkerboard.")
    p.add_argument("--shrink", type=int, default=1, help="Edge shrink in pixels (0-10). Default: 1.")
    p.add_argument("--feather", type=float, default=1.0, help="Edge feather in pixels (0-10). Default: 1.")
    p.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def ff_color(hex_text: str, default=(0, 0, 0)) -> str:
    r, g, b = hex_to_rgb(hex_text, default)
    return f"0x{r:02X}{g:02X}{b:02X}"


def spill_type_for(hex_text: str):
    """'green' / 'blue' when the key color is clearly one of those (so spill can be suppressed), else None."""
    r, g, b = hex_to_rgb(hex_text, (0, 255, 0))
    if g > r * 1.15 and g > b * 1.15:
        return "green"
    if b > r * 1.15 and b > g * 1.15:
        return "blue"
    return None


def auto_key_color(path) -> str:
    """Median color of the picture's outer border on the first frame — i.e. the screen behind the subject."""
    import numpy as np
    for _, frame in iter_frames(path, width=96):
        h, w = frame.shape[:2]
        t = max(2, int(min(h, w) * 0.12))
        ring = np.concatenate([frame[:t].reshape(-1, 3), frame[-t:].reshape(-1, 3),
                               frame[t:-t, :t].reshape(-1, 3), frame[t:-t, -t:].reshape(-1, 3)])
        r, g, b = (int(v) for v in np.median(ring, axis=0))
        return f"#{r:02X}{g:02X}{b:02X}"
    raise RuntimeError("Couldn't read a frame to detect the key color.")


def _pick_background(args) -> str:
    kind = args.background
    if kind == "auto":
        if getattr(args, "bg_video", None):
            return "video"
        if getattr(args, "bg_image", None):
            return "image"
        return "color"
    return kind


def _encode_args(out: Path, transparent: bool, crf: int, has_aud: bool):
    ext = out.suffix.lower()
    if transparent:
        if ext == ".webm":
            v = ["-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-auto-alt-ref", "0", "-b:v", "0", "-crf", "24"]
            a = ["-c:a", "libopus"]
        elif ext == ".mov":
            v = ["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le"]
            a = ["-c:a", "aac"]
        else:
            raise SystemExit(
                "❌ A transparent background needs a format that supports transparency. On the Output node "
                "choose WEBM (small, works in browsers/editors) or MOV (ProRes 4444, best for editing) — "
                f"not {ext.lstrip('.').upper() or 'this format'}. Or pick a Background color / image / video instead.")
    elif ext == ".webm":
        v = ["-c:v", "libvpx-vp9", "-pix_fmt", "yuv420p", "-b:v", "0", "-crf", "24"]
        a = ["-c:a", "libopus"]
    else:
        v = ["-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p",
             "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]
        if ext in (".mp4", ".mov", ".m4v"):
            v += ["-movflags", "+faststart"]
        a = ["-c:a", "aac"]
    return v, (["-map", "0:a?", *a] if has_aud else [])


def run_key(args, key_chain: str, *, spill: str | None = None, spill_mix: float = 0.0,
            invert: bool = False, blend_mode: str | None = None):
    """
    key_chain: ffmpeg filter snippet taking the (even-sized) foreground and producing a stream WITH alpha,
    e.g. "chromakey=color=0x00B140:similarity=0.15:blend=0.05". When `blend_mode` is given (screen/addition/
    lighten...) no matte is used: the clip is blended straight onto the background instead.
    """
    info = probe_video(args.input)
    W, H = info.width - info.width % 2, info.height - info.height % 2
    fps = info.fps
    out = Path(args.output)
    view = args.view
    bg_kind = _pick_background(args)
    if bg_kind == "video" and not getattr(args, "bg_video", None):
        raise SystemExit("❌ Background = video, but no Background video is connected or chosen.")
    if bg_kind == "image" and not getattr(args, "bg_image", None):
        raise SystemExit("❌ Background = image, but no Background image is chosen.")
    if blend_mode and bg_kind == "transparent":
        raise SystemExit("❌ Blend modes (screen / add / lighten) need a visible background — pick a color, image or video.")
    transparent = bg_kind == "transparent" and view == "composite"

    # ── inputs ───────────────────────────────────────────────────────────────
    cmd = ["ffmpeg", "-err_detect", "ignore_err", "-i", args.input]
    scale_bg = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={fps:.6f},format=yuv420p"
    bg_chain = None                                           # filter chain producing [bg]
    if view == "checkerboard":
        cmd += ["-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r={fps:.6f}"]
        bg_chain = ("[1:v]geq=lum='if(mod(floor(X/16)+floor(Y/16),2),205,125)':cb=128:cr=128,format=yuv420p[bg]")
    elif transparent or view == "matte":
        pass
    elif bg_kind == "video":
        cmd += ["-stream_loop", "-1", "-i", args.bg_video]
        bg_chain = f"[1:v]{scale_bg}[bg]"
    elif bg_kind == "image":
        cmd += ["-loop", "1", "-framerate", f"{fps:.6f}", "-i", args.bg_image]
        bg_chain = f"[1:v]{scale_bg}[bg]"
    else:
        cmd += ["-f", "lavfi", "-i", f"color=c={ff_color(args.bg_color)}:s={W}x{H}:r={fps:.6f}"]
        bg_chain = "[1:v]format=yuv420p[bg]"

    # ── filter graph ─────────────────────────────────────────────────────────
    fg_prep = f"[0:v]crop={W}:{H}:0:0,setsar=1"
    g = []
    if blend_mode:
        g.append(f"{fg_prep},format=yuv420p[fg]")
        g.append(bg_chain)
        g.append(f"[bg][fg]blend=all_mode={blend_mode}:shortest=1,format=yuv420p[out]")
    else:
        chain = f"{fg_prep},{key_chain}"
        if spill and spill_mix > 0:
            chain += f",format=gbrap,despill=type={spill}:mix={min(1.0, spill_mix):.3f}:expand=0:brightness=0"
        shrink = max(0, min(10, int(args.shrink)))
        feather = max(0.0, min(10.0, float(args.feather)))
        if shrink or feather > 0 or invert:
            m = "alphaextract"
            if invert:
                m += ",negate"
            m += ",erosion" * shrink
            if feather > 0:
                m += f",gblur=sigma={feather:.2f}"
            g.append(f"{chain},format=gbrap,split[ka][kb]")
            g.append(f"[ka]{m}[km]")
            g.append("[kb][km]alphamerge[fg]")
        else:
            g.append(f"{chain}[fg]")
        if view == "matte":
            g.append("[fg]alphaextract,format=yuv420p[out]")
        elif transparent:
            g.append(f"[fg]format={'yuva420p' if out.suffix.lower() == '.webm' else 'yuva444p10le'}[out]")
        else:
            g.append(bg_chain)
            g.append("[bg][fg]overlay=format=auto:shortest=1,format=yuv420p[out]")

    v_args, a_args = _encode_args(out, transparent, getattr(args, "crf", 18),
                                  has_audio(args.input) and view == "composite")
    cmd += ["-filter_complex", ";".join(x for x in g if x), "-map", "[out]", *v_args, *a_args,
            "-r", f"{fps:.6f}", "-shortest", str(out)]
    if getattr(args, "force", False):
        cmd.insert(1, "-y")
    run_ffmpeg_with_progress(cmd, args.input, out)
