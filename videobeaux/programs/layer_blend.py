"""
layer_blend — layer two videos with per-layer opacity and a blend mode (multiply, screen,
color burn, difference, ...). Pure ffmpeg, fully offline.

How the opacities work:  R = blend_mode(B over A);  result = opacity_A × A + opacity_B × R.
In "normal" mode 75 / 25 is exactly a 75% A + 25% B cross-mix. In any other mode B's blend
effect is applied at B's opacity, so 100 / 100 in "difference" gives A + |A − B| (bright,
on purpose). Values that don't add up to 100 darken or brighten the result.
"""
from pathlib import Path

from videobeaux.utils import audio_pick
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.frame_pipe import probe_video

# label → ffmpeg `blend` all_mode
MODES = {
    "normal": "normal", "multiply": "multiply", "screen": "screen", "overlay": "overlay",
    "soft light": "softlight", "hard light": "hardlight", "color dodge": "dodge", "color burn": "burn",
    "darken": "darken", "lighten": "lighten", "difference": "difference", "exclusion": "exclusion",
    "addition": "addition", "subtract": "subtract", "divide": "divide", "hard mix": "hardmix",
    "vivid light": "vividlight", "linear light": "linearlight", "pin light": "pinlight",
    "grain merge": "grainmerge", "grain extract": "grainextract", "negation": "negation",
    "average": "average", "phoenix": "phoenix", "glow": "glow", "heat": "heat", "freeze": "freeze",
    "reflect": "reflect",
}
FITS = ["cover", "contain", "stretch"]
LENGTHS = ["A (B loops if shorter)", "shortest", "longest"]

GUI_METADATA = {
    'args': {
        'input2': {'type': 'file', 'subtype': 'video', 'label': 'Layer B (second video)',
                   'help': 'The video layered on top of the main input (A) — connect a node or pick a file.'},
        'opacity_a': {'label': 'Opacity A (%)', 'min': 0, 'max': 100,
                      'help': 'How much of the main input (A) shows.'},
        'opacity_b': {'label': 'Opacity B (%)', 'min': 0, 'max': 100,
                      'help': 'How much of B (blended onto A with the mode) shows. In normal mode 75 / 25 = a 75% A + 25% B mix.'},
        'mode': {'type': 'select', 'label': 'Blend mode', 'default': 'normal', 'choices': list(MODES)},
        'b_fit': {'type': 'select', 'label': 'B size', 'default': 'cover', 'choices': FITS,
                  'help': "cover = fill A's frame (crops), contain = fit inside (black bars), stretch = distort to fit."},
        'length': {'type': 'select', 'label': 'Length', 'default': LENGTHS[0], 'choices': LENGTHS},
        'audio': {'type': 'select', 'label': 'Audio', 'default': 'A', 'choices': list(audio_pick.LAYER_AUDIO)},
    }
}


def register_arguments(p):
    p.description = (
        "Layer two videos with per-layer opacity and a blend mode (multiply, screen, color burn, "
        "difference, overlay…). Result = opacity A × A + opacity B × (B blended over A): in normal mode "
        "75 / 25 is a 75% A + 25% B mix. Choose whose audio to keep: A, B, a mix, or silent."
    )
    p.add_argument("--input2", required=True, type=str, help="Second video (layer B), blended over the main input (A).")
    p.add_argument("--opacity_a", type=float, default=75.0, help="Opacity of A, 0-100. Default: 75.")
    p.add_argument("--opacity_b", type=float, default=25.0, help="Opacity of B, 0-100. Default: 25.")
    p.add_argument("--mode", choices=list(MODES), default="normal", help="Blend mode. Default: normal.")
    p.add_argument("--b_fit", choices=FITS, default="cover", help="How B is fitted to A's frame. Default: cover.")
    p.add_argument("--length", choices=LENGTHS, default=LENGTHS[0], help="Output length. Default: A (B loops if shorter).")
    audio_pick.add_audio_argument(p, audio_pick.LAYER_AUDIO, "A", "Which audio to keep: A, B, Mix A + B, or Silent. Default: A.")
    p.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def fit_chain(fit: str, W: int, H: int) -> str:
    if fit == "contain":
        return f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black"
    if fit == "stretch":
        return f"scale={W}:{H}"
    return f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"


def build_graph(mode: str, wa: float, wb: float, fit: str, W: int, H: int, fps: float,
                length: str, a_dur: float, b_dur: float) -> str:
    """filter_complex for inputs 0 = A, 1 = B → [out]."""
    a_pad = b_pad = ""
    if length == "longest":
        a_pad = f",tpad=stop_mode=clone:stop_duration={max(0.0, b_dur - a_dur) + 1:.3f}"
        b_pad = f",tpad=stop_mode=clone:stop_duration={max(0.0, a_dur - b_dur) + 1:.3f}"
    a = f"[0:v]crop={W}:{H}:0:0,setsar=1,fps={fps:.6f},format=gbrp{a_pad},split[a1][a2]"
    b = f"[1:v]{fit_chain(fit, W, H)},setsar=1,fps={fps:.6f},format=gbrp{b_pad}[b]"
    r = f"[b][a1]blend=all_mode={MODES[mode]}:shortest=1[r]"
    mix = f"[a2][r]blend=all_expr='clip(A*{wa:.4f}+B*{wb:.4f},0,255)':shortest=1"
    out = "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p[out]"
    return ";".join([a, b, r, f"{mix},{out}"])


def run(args):
    A, B = Path(args.input), Path(args.input2)
    if not B.exists():
        raise SystemExit(f"❌ Layer B not found: {B}")
    ia, ib = probe_video(A), probe_video(B)
    W, H = ia.width - ia.width % 2, ia.height - ia.height % 2
    a_dur, b_dur = ia.duration, ib.duration
    if args.length == "shortest":
        total = min(a_dur, b_dur)
    elif args.length == "longest":
        total = max(a_dur, b_dur)
    else:
        total = a_dur
    wa = max(0.0, min(100.0, args.opacity_a)) / 100.0
    wb = max(0.0, min(100.0, args.opacity_b)) / 100.0
    out = Path(args.output)
    force = bool(getattr(args, "force", False))

    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="vb_layerblend_"))
    try:
        wav = audio_pick.build_audio_track(args.audio, audio_pick.LAYER_AUDIO, A, B, total, tmp / "audio.wav", a_dur=a_dur)
        cmd = ["ffmpeg", "-err_detect", "ignore_err", "-i", str(A)]
        if args.length.startswith("A"):
            cmd += ["-stream_loop", "-1"]
        cmd += ["-i", str(B)]
        if wav is not None:
            cmd += ["-i", str(wav)]
        cmd += ["-filter_complex", build_graph(args.mode, wa, wb, args.b_fit, W, H, ia.fps, args.length, a_dur, b_dur),
                "-map", "[out]"]
        cmd += ["-map", "2:a", "-c:a", "aac"] if wav is not None else ["-an"]
        cmd += ["-t", f"{total:.3f}", "-r", f"{ia.fps:.6f}", "-c:v", "libx264", "-preset", "medium", "-crf", str(args.crf),
                "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                "-movflags", "+faststart", str(out)]
        if force:
            cmd.insert(1, "-y")
        run_ffmpeg_with_progress(cmd, str(A), str(out), duration_override=total)
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
