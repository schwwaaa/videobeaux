"""
Streaming per-frame video processing.

ffmpeg decodes the input to raw RGB frames on a pipe, a Python callback
transforms each frame (numpy / OpenCV / PIL), and a second ffmpeg encodes the
result — muxing the original audio back in. No frames are written to disk,
unlike the older extract-to-PNG programs (pixel_sort, kinetic_captions).

Progress is reported the same way run_ffmpeg_with_progress does it, so the GUI
progress bar keeps working: an "Input duration: N seconds" line on stdout, and
"time=HH:MM:SS.mmm speed=Nx" lines on stderr.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import numpy as np


CONVERT_HINT = ("💡 If this file is an unusual format (e.g. a phone .MOV with HDR/HEVC, ProRes, or a "
                "variable-frame-rate recording), run it through the Convert program first "
                "(Media Tools → Convert, to mp4) and use that result here.")


@dataclass
class VideoInfo:
    width: int
    height: int
    fps: float
    duration: float
    frames: int
    has_audio: bool


def probe_video(path) -> VideoInfo:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"❌ ffprobe failed on {path}: {r.stderr.strip()}")
    data = json.loads(r.stdout or "{}")
    streams = data.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"
              and s.get("disposition", {}).get("attached_pic") != 1), None)
    if v is None:
        raise RuntimeError(f"❌ No video stream in {path}")
    w, h = int(v["width"]), int(v["height"])
    rotation = 0
    for sd in v.get("side_data_list") or []:
        if "rotation" in sd:
            rotation = int(float(sd["rotation"]))
    rotation = rotation or int(float((v.get("tags") or {}).get("rotate") or 0))
    if abs(rotation) % 180 == 90:  # ffmpeg auto-rotates on decode
        w, h = h, w
    num, _, den = (v.get("avg_frame_rate") or v.get("r_frame_rate") or "0/1").partition("/")
    fps = float(num) / float(den or 1) if float(den or 1) else 0.0
    if fps <= 0:
        num, _, den = (v.get("r_frame_rate") or "30/1").partition("/")
        fps = float(num) / float(den or 1)
    try:
        duration = float(data.get("format", {}).get("duration") or v.get("duration") or 0)
    except ValueError:
        duration = 0.0
    frames = int(round(duration * fps)) if duration else 0
    return VideoInfo(w, h, fps, duration, frames, any(s.get("codec_type") == "audio" for s in streams))


def _tail(f, n=10) -> str:
    f.seek(0)
    lines = [ln.strip() for ln in f.read().splitlines() if ln.strip()]
    return "\n".join(lines[-n:])


def process_video(
    in_path,
    out_path,
    fn: Callable[[np.ndarray, int, float], np.ndarray],
    *,
    crf: int = 18,
    preset: str = "medium",
    force: bool = True,
    max_frames: Optional[int] = None,
    setup: Optional[Callable[[VideoInfo], None]] = None,
    audio: bool = True,
    max_width: Optional[int] = None,
) -> dict:
    """
    Run `fn(frame, index, t_seconds) -> frame` over every frame of in_path and
    write the result (with the original audio) to out_path.

    frame is an (H, W, 3) uint8 RGB array (writable). fn must return an array of
    the same shape. If `max_width` is set and the video is wider, frames are
    scaled down to it first (and the output is that smaller size) — useful for
    slow per-pixel effects on 4K phone footage. Returns {"frames": n, "seconds": wall_time}.
    """
    in_path, out_path = Path(in_path), Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    info = probe_video(in_path)
    # yuv420p needs even dimensions — crop at most one pixel on an odd edge.
    W, H = info.width - info.width % 2, info.height - info.height % 2
    scale_vf = f"crop={W}:{H}:0:0"
    if max_width and W > max_width:
        W = max_width - max_width % 2
        H = max(2, int(round(info.height * W / info.width)) // 2 * 2)
        scale_vf = f"scale={W}:{H}:flags=area"
        print(f"ℹ️  Processing at {W}x{H} (down from {info.width}x{info.height}) to keep this effect fast.", flush=True)
    if setup:
        setup(VideoInfo(W, H, info.fps, info.duration, info.frames, info.has_audio))

    print(f"Input duration: {info.duration:.2f} seconds", flush=True)

    dec_err = tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace")
    enc_err = tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace")

    dec_cmd = ["ffmpeg", "-v", "error", "-i", str(in_path), "-an",
               "-vf", f"fps={info.fps:.6f},{scale_vf}",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    enc_cmd = ["ffmpeg", "-v", "error", "-y" if force else "-n",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-framerate", f"{info.fps:.6f}", "-i", "-"]
    if audio and info.has_audio:
        enc_cmd += ["-i", str(in_path), "-map", "0:v:0", "-map", "1:a:0?", "-c:a", "aac", "-shortest"]
    enc_cmd += ["-c:v", "libx264", "-preset", preset, "-crf", str(crf),
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out_path)]

    dec = subprocess.Popen(dec_cmd, stdout=subprocess.PIPE, stderr=dec_err)
    enc = subprocess.Popen(enc_cmd, stdin=subprocess.PIPE, stderr=enc_err)

    frame_bytes = W * H * 3
    interactive = sys.stderr.isatty()
    pbar = None
    if interactive:
        from tqdm import tqdm
        pbar = tqdm(total=max(info.frames, 1), unit="f", dynamic_ncols=True,
                    desc=f"🔨 Processing {in_path.name}")

    start = last_report = time.monotonic()
    last_t = 0.0
    n = 0
    clean = False
    try:
        while max_frames is None or n < max_frames:
            buf = dec.stdout.read(frame_bytes)
            if len(buf) < frame_bytes:
                break
            frame = np.frombuffer(buf, dtype=np.uint8).reshape(H, W, 3).copy()
            t = n / info.fps
            out = fn(frame, n, t)
            if out.dtype != np.uint8:
                out = np.clip(out, 0, 255).astype(np.uint8)
            if out.shape != (H, W, 3):
                raise RuntimeError(f"Frame function returned shape {out.shape}, expected {(H, W, 3)}")
            enc.stdin.write(np.ascontiguousarray(out).tobytes())
            n += 1

            now = time.monotonic()
            if pbar is not None:
                pbar.update(1)
            elif now - last_report >= 0.25:
                d_wall = now - last_report
                speed = ((t - last_t) / d_wall) if d_wall > 0 else 0.0
                h_, rem = divmod(t, 3600)
                m_, s_ = divmod(rem, 60)
                print(f"time={int(h_):02d}:{int(m_):02d}:{s_:06.3f} speed={speed:.2f}x",
                      file=sys.stderr, flush=True)
                last_report, last_t = now, t
        clean = True
    except BrokenPipeError:
        clean = True   # the encoder died; its stderr (below) says why
    finally:
        try:
            enc.stdin.close()
        except Exception:
            pass
        # On an exception in fn (or an early stop) the decoder is still blocked
        # writing to a pipe nobody reads — kill it or wait() would hang forever.
        if max_frames is not None or not clean:
            dec.kill()
        dec.wait()
        enc.wait()
        if pbar is not None:
            pbar.close()

    if enc.returncode != 0:
        raise RuntimeError(f"❌ ffmpeg encode failed (code {enc.returncode})\n{_tail(enc_err)}\n{CONVERT_HINT}")
    if dec.returncode not in (0, None) and max_frames is None:
        raise RuntimeError(f"❌ ffmpeg decode failed (code {dec.returncode})\n{_tail(dec_err)}\n{CONVERT_HINT}")
    if n == 0:
        raise RuntimeError("❌ No frames were decoded from the input.\n" + _tail(dec_err) + "\n" + CONVERT_HINT)

    print(f"\n📺 Process Complete: {out_path} \n", flush=True)
    return {"frames": n, "seconds": time.monotonic() - start}


def iter_frames(in_path, width: Optional[int] = None):
    """
    Yield (index, frame) RGB frames from in_path, optionally scaled to `width`
    (aspect preserved) — handy for analysis passes that don't need full
    resolution (stabilization, motion estimation).
    """
    info = probe_video(in_path)
    if width and width < info.width:
        w = width - width % 2
        h = max(2, int(round(info.height * w / info.width)) // 2 * 2)
        vf = f"fps={info.fps:.6f},scale={w}:{h}:flags=area"
    else:
        w, h = info.width - info.width % 2, info.height - info.height % 2
        vf = f"fps={info.fps:.6f},crop={w}:{h}:0:0"
    err = tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace")
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", str(in_path), "-an", "-vf", vf,
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE, stderr=err)
    size = w * h * 3
    n = 0
    try:
        while True:
            buf = proc.stdout.read(size)
            if len(buf) < size:
                break
            yield n, np.frombuffer(buf, dtype=np.uint8).reshape(h, w, 3).copy()
            n += 1
    finally:
        proc.kill()
        proc.wait()
