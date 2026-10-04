"""
Choosing which input's audio a two-input program keeps (A, B, both, or silence).

`build_audio_track` renders the chosen audio to a temp WAV so a program can mux it onto a
finished video with a simple stream copy — no matter how the picture was built.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from videobeaux.utils.media import ensure_audio

# Labels shown in the GUI → internal mode.
CROSSMOSH_AUDIO = {
    "A then B (follows the picture)": ("both", True),     # (mode, B starts after A ends)
    "A only": ("a", False),
    "B only (after A)": ("b", True),
    "Mix A + B (together from the start)": ("both", False),
    "Silent": ("none", False),
}
LAYER_AUDIO = {
    "A": ("a", False),
    "B": ("b", False),
    "Mix A + B": ("both", False),
    "Silent": ("none", False),
}


def add_audio_argument(parser, choices: dict, default: str, help_text: str):
    parser.add_argument("--audio", choices=list(choices), default=default, help=help_text)


def duration_of(path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def _has_encoder(name: str) -> bool:
    out = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    return any(len(p) > 1 and p[1] == name for p in (ln.split() for ln in out.splitlines()))


def audio_codec_for_avi() -> list:
    """MP3 plays everywhere an AVI does; fall back to PCM if this ffmpeg has no LAME."""
    return ["-c:a", "libmp3lame", "-b:a", "192k"] if _has_encoder("libmp3lame") else ["-c:a", "pcm_s16le"]


def build_graph(mode: str, a_dur: float, b_offset: float, total: float) -> str:
    """ffmpeg filter_complex (inputs 0 = A, 1 = B, both with audio) producing [aout] of length `total`."""
    fmt = "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo"
    ms = int(round(b_offset * 1000))
    a = f"[0:a]{fmt},atrim=0:{a_dur:.3f}[a]"
    b = f"[1:a]{fmt},adelay={ms}|{ms}[b]" if ms else f"[1:a]{fmt}[b]"
    pad = f"apad=whole_dur={total:.3f},atrim=0:{total:.3f}"
    if mode == "a":
        return f"{a};[a]{pad}[aout]"
    if mode == "b":
        return f"{b};[b]{pad}[aout]"
    # Pad each track to full length *before* mixing — padding after amix doesn't extend it.
    return (f"{a};{b};[a]apad=whole_dur={total:.3f}[a2];[b]apad=whole_dur={total:.3f}[b2];"
            f"[a2][b2]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:{total:.3f}[aout]")


def build_audio_track(choice: str, choices: dict, a_path, b_path, total: float, out_wav, *, a_dur: float | None = None,
                      force: bool = True):
    """
    Render the chosen audio to `out_wav` (48 kHz stereo WAV, exactly `total` seconds). Returns the
    path, or None for "Silent". Inputs without audio are given a silent track first.
    """
    mode, b_after_a = choices[choice]
    if mode == "none":
        return None
    a_path, b_path = ensure_audio(a_path), ensure_audio(b_path)
    a_dur = duration_of(a_path) if a_dur is None else a_dur
    graph = build_graph(mode, a_dur, a_dur if b_after_a else 0.0, total)
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(a_path), "-i", str(b_path), "-filter_complex", graph,
           "-map", "[aout]", "-c:a", "pcm_s16le", "-t", f"{total:.3f}", str(out_wav)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"❌ Couldn't build the audio track:\n{r.stderr.strip()[-500:]}")
    return Path(out_wav)
