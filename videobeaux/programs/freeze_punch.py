from __future__ import annotations
r"""
videobeaux.programs.freeze_punch - freeze-frame emphasis on audio peaks

Not a single-filter effect — needs multi-segment orchestration, architected
like insert_clip.py/qwikchop.py: scan the whole audio for loud moments (a
windowed loudness pass, the same technique qwikchop_deluxe.py's
_measure_loudness_db uses per-candidate), pick well-spaced peaks, then build
one ffmpeg command that alternates normal-playback segments with brief
frozen-frame holds at each peak (video held via tpad, audio silenced for the
same span via apad) and concatenates them back together. This extends the
total output duration by roughly (num_freezes * freeze_duration) — a classic
freeze-frame "punch" edit, not a same-length effect.
"""
import subprocess
from pathlib import Path
from typing import List, Tuple

from videobeaux.utils.media import ensure_audio
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress


def _ffprobe_duration_seconds(path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode("utf-8", "ignore").strip()
    return float(out)


def _ffprobe_sample_rate(path: Path) -> int:
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "a:0",
        "-show_entries", "stream=sample_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode("utf-8", "ignore").strip()
    return int(out) if out else 44100


def _measure_loudness_db(src: Path, start: float, dur: float) -> float:
    """Mean volume in dB for the given window (higher = louder). -91.0 (silence floor) on failure."""
    cmd = [
        "ffmpeg", "-ss", f"{start:.3f}", "-t", f"{max(0.05, dur):.3f}",
        "-i", str(src), "-af", "volumedetect", "-vn", "-f", "null", "-",
    ]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        import re
        m = re.search(r"mean_volume:\s*(-?[\d.]+)\s*dB", proc.stderr or "")
        return float(m.group(1)) if m else -91.0
    except Exception:
        return -91.0


def _find_peaks(duration: float, window: float, count: int, min_gap: float, scan) -> List[float]:
    windows = []
    t = 0.0
    while t < duration - window * 0.5:
        windows.append(t + window / 2.0)
        t += window
    scores = [(scan(max(0.0, ts - window / 2), window), ts) for ts in windows]
    scores.sort(key=lambda p: -p[0])

    picked: List[float] = []
    for _score, ts in scores:
        if len(picked) >= count:
            break
        if any(abs(ts - p) < min_gap for p in picked):
            continue
        picked.append(ts)
    picked.sort()
    return picked


def register_arguments(parser):
    parser.description = (
        "Freezes on detected audio peaks/transients (a local loudness scan — no ML, "
        "no network) then resumes, for a punchy freeze-frame emphasis edit. Adds "
        "roughly (peaks × --freeze_duration) to the total output length."
    )
    parser.add_argument("--count", type=int, default=4, help="Number of freeze points to insert. Default: 4.")
    parser.add_argument("--freeze_duration", type=float, default=0.4, help="How long each freeze holds, in seconds. Default: 0.4.")
    parser.add_argument("--min_gap", type=float, default=3.0, help="Minimum seconds between freeze points. Default: 3.0.")
    parser.add_argument("--scan_window", type=float, default=0.5, help="Window size for the loudness scan, in seconds. Default: 0.5.")


def run(args):
    # audio filter graphs need an audio track on every input
    if getattr(args, 'input', None):
        args.input = ensure_audio(args.input)
    in_video = Path(args.input)
    duration = _ffprobe_duration_seconds(in_video)
    if duration <= 0:
        print("❌ Could not read input duration.")
        return

    print("ℹ️  Scanning audio for peaks…")
    peaks = _find_peaks(
        duration, max(0.1, args.scan_window), max(0, args.count), max(0.1, args.min_gap),
        lambda start, dur: _measure_loudness_db(in_video, start, dur),
    )
    if not peaks:
        print("⚠️ No freeze points found (is there audio?). Exporting unchanged.")
        peaks = []

    print(f"ℹ️  Freezing at: {', '.join(f'{p:.2f}s' for p in peaks) or '(none)'}")

    sample_rate = _ffprobe_sample_rate(in_video)
    freeze_samples = max(1, int(round(args.freeze_duration * sample_rate)))

    parts: List[str] = []
    v_labels, a_labels = [], []
    prev_end = 0.0
    seg_i = 0

    def add_playback_segment(start: float, end: float):
        nonlocal seg_i
        if end - start <= 0.01:
            return
        vlab, alab = f"v{seg_i}", f"a{seg_i}"
        parts.append(f"[0:v]trim=start={start:.6f}:end={end:.6f},setpts=PTS-STARTPTS[{vlab}]")
        parts.append(f"[0:a]atrim=start={start:.6f}:end={end:.6f},asetpts=PTS-STARTPTS[{alab}]")
        v_labels.append(f"[{vlab}]")
        a_labels.append(f"[{alab}]")
        seg_i += 1

    for peak in peaks:
        if peak <= prev_end or peak >= duration:
            continue
        add_playback_segment(prev_end, peak)

        vlab, alab = f"v{seg_i}", f"a{seg_i}"
        sliver_end = min(duration, peak + 0.04)
        parts.append(
            f"[0:v]trim=start={peak:.6f}:end={sliver_end:.6f},setpts=PTS-STARTPTS,"
            f"tpad=stop_mode=clone:stop_duration={args.freeze_duration}[{vlab}]"
        )
        parts.append(
            f"[0:a]atrim=start={peak:.6f}:end={sliver_end:.6f},asetpts=PTS-STARTPTS,"
            f"apad=pad_len={freeze_samples}[{alab}]"
        )
        v_labels.append(f"[{vlab}]")
        a_labels.append(f"[{alab}]")
        seg_i += 1
        prev_end = peak

    add_playback_segment(prev_end, duration)

    if seg_i == 0:
        print("❌ No segments to export.")
        return

    concat_inputs = "".join(l for pair in zip(v_labels, a_labels) for l in pair)
    parts.append(f"{concat_inputs}concat=n={seg_i}:v=1:a=1[out_v][out_a]")

    filter_complex = ";\n".join(parts)
    command = [
        "ffmpeg",
        "-i", str(in_video),
        "-filter_complex", filter_complex,
        "-map", "[out_v]",
        "-map", "[out_a]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-movflags", "+faststart",
        args.output,
    ]
    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)
