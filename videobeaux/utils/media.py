"""Small media helpers shared by programs."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


def has_audio(path) -> bool:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True)
    return bool(r.stdout.strip())


def ensure_audio(path):
    """
    Return `path` if it has an audio track; otherwise a temp copy with a silent
    stereo track added (video stream-copied, so it's fast and lossless).

    Many programs build audio filter graphs ([0:a]atempo, acrossfade, …) that
    fail outright on a silent clip — phone videos and screen recordings often
    have none. Calling this first makes those programs work on any input.
    """
    p = Path(path)
    if has_audio(p):
        return str(p)
    out = Path(tempfile.mkdtemp(prefix="videobeaux_silent_")) / f"{p.stem}.mkv"
    r = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(p),
         "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
         "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-shortest", str(out)],
        capture_output=True, text=True)
    if r.returncode != 0 or not out.exists():
        raise SystemExit(f"❌ {p.name} has no audio track and a silent one couldn't be added:\n"
                         f"{r.stderr.strip()[-400:]}\nTry running it through Convert first.")
    print(f"ℹ️  {p.name} has no audio — added a silent track so this effect can run.", flush=True)
    return str(out)
