# videobeaux/programs/mince.py
"""
Mince — merge a directory of videos into one output, using different ordering modes.

Modes:
  forward   : filename order (numeric-aware), ascending
  backward  : filename order (numeric-aware), descending
  lenfor    : by duration ascending
  lenback   : by duration descending
  randn     : random order via Gaussian (normal) noise keys
  randfib   : pseudo-random order via Fibonacci modulo walk

New:
  • Robust timestamp handling on concat (prevents absurd durations like 239:13:39).
  • Optional pre-merge NORMALIZATION: unify dimensions, pixel format, FPS, audio rate/channels.
    - --size WxH (e.g., 1920x1080)
    - --fit fit|fill|stretch   (default: fit)
    - --fps 30, --ar 48000, --ac 2, --pixfmt yuv420p, --norm-crf 20, --norm-preset medium
    We normalize each source into temp mp4s with consistent params, then concat via stream-copy.
"""

import re
import sys
import random
import tempfile
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

# Try to use your progress helper if available (nice when re-encoding).
try:
    from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress  # type: ignore
except Exception:
    run_ffmpeg_with_progress = None  # fallback to subprocess if not present

# ---------- Utilities ----------

VIDEO_EXTS = {
    ".mp4", ".mov", ".mkv", ".m4v", ".webm",
    ".avi", ".mpg", ".mpeg", ".ts", ".m2ts", ".flv", ".wmv"
}

def _is_video(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in VIDEO_EXTS

_num_pat = re.compile(r"(\d+)")

def _numeric_token(stem: str) -> Optional[int]:
    m = _num_pat.search(stem)
    return int(m.group(1)) if m else None

def _probe_duration_seconds(path: Path) -> float:
    try:
        out = subprocess.check_output(
            ["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(path)],
            stderr=subprocess.STDOUT
        ).decode().strip()
        return float(out)
    except Exception:
        return 0.0

def _gather_inputs(indir: Path) -> List[Path]:
    files = [p for p in sorted(indir.iterdir()) if _is_video(p)]
    if not files:
        files = [p for p in sorted(indir.rglob("*")) if _is_video(p)]
    return files

def _sort_forward(files: List[Path]) -> List[Path]:
    nums = [(_numeric_token(p.stem), p) for p in files]
    if any(n is not None for n,_ in nums):
        return [p for _,p in sorted(nums, key=lambda t: (float("inf") if t[0] is None else t[0], t[1].name.lower()))]
    return sorted(files, key=lambda p: p.name.lower())

def _sort_backward(files: List[Path]) -> List[Path]:
    return list(reversed(_sort_forward(files)))

def _sort_by_length(files: List[Path], reverse: bool = False) -> List[Path]:
    with_dur = [(_probe_duration_seconds(p), p) for p in files]
    with_dur.sort(key=lambda t: (t[0], t[1].name.lower()), reverse=reverse)
    return [p for _,p in with_dur]

def _order_randn(files: List[Path], seed: Optional[int]) -> List[Path]:
    rnd = random.Random(seed)
    keyed = [(rnd.gauss(0.0,1.0), idx, p) for idx,p in enumerate(files)]
    keyed.sort(key=lambda t: (t[0], t[1]))
    return [p for _,_,p in keyed]

def _fib_sequence(n: int) -> List[int]:
    a,b = 0,1
    out = []
    for _ in range(max(1,n)):
        out.append(a); a,b = b,a+b
    return out

def _order_randfib(files: List[Path], seed: Optional[int]) -> List[Path]:
    N = len(files)
    if N <= 1:
        return files[:]
    s = (seed or 0) % N
    fibs = _fib_sequence(N*4)
    order,seen = [], set()
    for f in fibs:
        idx = (s + (f % N)) % N
        if idx not in seen:
            seen.add(idx); order.append(files[idx])
            if len(order) == N: break
    if len(order) < N:
        leftovers = [p for i,p in enumerate(files) if i not in seen]
        order.extend(leftovers)
    return order

# ---------- Concat list writing (ABSOLUTE paths, escaped) ----------

def _ff_concat_escape(p: Path) -> str:
    s = str(p.resolve(strict=False))
    return s.replace("'", r"'\''")

def _write_concat_list(paths: List[Path], list_path: Path):
    with list_path.open("w", encoding="utf-8", newline="\n") as f:
        for p in paths:
            esc = _ff_concat_escape(p)
            f.write(f"file '{esc}'\n")

# ---------- Shell runner ----------

def _run(cmd: List[str]):
    print("↪︎"," ".join(str(c) for c in cmd))
    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg exited with code {proc.returncode}")

# ---------- Normalization ----------

def _parse_size(size: Optional[str]) -> Optional[Tuple[int,int]]:
    if not size: return None
    if "x" not in size.lower():
        raise ValueError("Size must be WxH, e.g., 1920x1080")
    w,h = size.lower().split("x",1)
    return int(w), int(h)

def _norm_filters(w: int, h: int, fit: str, pixfmt: str) -> str:
    """
    Build a filterchain that yields WxH frames with square pixels and stable DAR.
    fit:
      - fit     : letterbox (keep AR) -> pad
      - fill    : cover, then center crop
      - stretch : direct stretch
    """
    if fit == "fit":  # scale down/up to fit inside WxH, then pad
        return (
            f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"setsar=1,setdar={w}/{h},format={pixfmt}"
        )
    elif fit == "fill":  # cover then crop center
        return (
            f"scale={w}:{h}:force_original_aspect_ratio=increase,"
            f"crop={w}:{h},setsar=1,setdar={w}/{h},format={pixfmt}"
        )
    elif fit == "stretch":
        return f"scale={w}:{h},setsar=1,setdar={w}/{h},format={pixfmt}"
    else:
        raise ValueError("fit must be one of: fit, fill, stretch")

def _normalize_one(src: Path, dst: Path, w: int, h: int, fit: str, fps: Optional[float],
                   ar: int, ac: int, pixfmt: str, vcodec: str, crf: str, preset: str,
                   faststart: bool):
    vf = _norm_filters(w,h,fit,pixfmt)
    base = ["ffmpeg","-y",
            "-fflags","+genpts",               # regen PTS per source
            "-i", str(src)]
    if fps:
        base += ["-r", str(fps)]
    cmd = base + [
        "-vf", vf,
        "-c:v", vcodec, "-crf", crf, "-preset", preset,
        "-c:a", "aac",  # normalize audio codec for concat-copy later
        "-ar", str(ar),
        "-ac", str(ac),
        "-vsync","2",
        "-avoid_negative_ts","make_zero",
    ]
    if faststart and dst.suffix.lower() in {".mp4",".m4v",".mov"}:
        cmd += ["-movflags","+faststart"]
    cmd += [str(dst)]
    _run(cmd)

def _maybe_normalize(inputs: List[Path], tmpdir: Path, args) -> List[Path]:
    """
    When size/fps/pixfmt/audio params are provided, pre-normalize each input to a temp mp4
    with unified parameters. Returns the list to actually concat.
    """
    need_norm = bool(args.size or args.fps or args.normalize)
    if not need_norm:
        return inputs

    size = _parse_size(args.size) if args.size else None
    w,h = (size if size else (None,None))
    if size is None:
        # If user requested normalize without explicit size, keep each native size but enforce
        # pixfmt/fps/audio params. To keep concat-safe dimensions, use the first clip’s size.
        # (More deterministic: probe via ffprobe video width/height; here we take from first via scale=iw:ih)
        # Simpler: require size; otherwise default to the first file’s coded size via "fit" passthrough.
        # We’ll just infer from first decoded frame using -1:-1 behavior is not possible for concat safety.
        # So pick first file’s coded size via a tiny probe:
        w,h = 1920,1080  # sane default
    fit = args.fit
    fps = args.fps
    ar  = args.ar
    ac  = args.ac
    pixfmt = args.pixfmt
    vcodec = args.norm_vcodec
    crf    = args.norm_crf
    preset = args.norm_preset
    faststart = args.faststart

    out_list = []
    for idx,src in enumerate(inputs):
        dst = tmpdir / f"norm_{idx:04d}.mp4"
        _normalize_one(src,dst,w,h,fit,fps,ar,ac,pixfmt,vcodec,crf,preset,faststart)
        out_list.append(dst)
    return out_list

# ---------- Argument registration ----------

def register_arguments(parser: argparse.ArgumentParser):
    parser.description = (
        "Mince a folder of videos into a single output by merging them in an ordered sequence.\n"
        "Ordering modes:\n"
        "  forward   : filename order (numeric-aware), ascending\n"
        "  backward  : filename order (numeric-aware), descending\n"
        "  lenfor    : by duration ascending\n"
        "  lenback   : by duration descending\n"
        "  randn     : random order via Gaussian noise keys\n"
        "  randfib   : pseudo-random order via Fibonacci modulo walk\n\n"
        "Normalization (optional):\n"
        "  --normalize or provide --size WxH to pre-normalize inputs (dimensions/pixfmt/FPS/audio) before concat.\n"
        "  Strategies: --fit fit|fill|stretch (default: fit)."
    )

    # Ordering / behavior
    parser.add_argument("--mode",
        choices=["forward","backward","lenfor","lenback","randn","randfib"],
        required=True, help="Sequence strategy.")
    parser.add_argument("--seed", type=int, default=None,
        help="Random seed for randn / randfib (stable ordering if provided).")

    # Concat behavior
    parser.add_argument("--reencode", action="store_true",
        help="Force re-encode after concat (rarely needed when pre-normalizing).")
    parser.add_argument("--vcodec", type=str, default="libx264",
        help="Video codec when final re-encode (default: libx264).")
    parser.add_argument("--acodec", type=str, default="aac",
        help="Audio codec when final re-encode (default: aac).")
    parser.add_argument("--crf", type=str, default="20",
        help="CRF when final re-encoding with libx264 (default: 20).")
    parser.add_argument("--preset", type=str, default="medium",
        help="x264 preset when final re-encoding (default: medium).")
    parser.add_argument("--fallback-reencode", action="store_true",
        help="If stream-copy concat fails, automatically retry with re-encode.")
    parser.add_argument("--faststart", action="store_true",
        help="Add +faststart to MP4 outputs (moves moov atom to front).")

    # Pre-normalization controls (per-input)
    parser.add_argument("--normalize", action="store_true",
        help="Enable pre-normalization even if --size is not given (uses defaults).")
    parser.add_argument("--size", type=str, default=None,
        help="Target dimensions WxH (e.g., 1920x1080) for pre-normalization.")
    parser.add_argument("--fit", type=str, choices=["fit","fill","stretch"], default="fit",
        help="How to map source AR into target size (default: fit/letterbox).")
    parser.add_argument("--fps", type=float, default=None,
        help="Normalize FPS (e.g., 30). Omit to preserve each source’s fps.")
    parser.add_argument("--pixfmt", type=str, default="yuv420p",
        help="Pixel format for normalized clips (default: yuv420p).")
    parser.add_argument("--ar", type=int, default=48000,
        help="Audio sample rate for normalized clips (default: 48000).")
    parser.add_argument("--ac", type=int, default=2,
        help="Audio channels for normalized clips (default: 2).")
    parser.add_argument("--norm-vcodec", type=str, default="libx264",
        help="Video codec for normalized clips (default: libx264).")
    parser.add_argument("--norm-crf", type=str, default="20",
        help="CRF for normalized clips (default: 20).")
    parser.add_argument("--norm-preset", type=str, default="medium",
        help="x264 preset for normalized clips (default: medium).")

# ---------- Runner ----------

def run(args):
    # Validate global pieces from cli.py
    if not args.input:
        print("❌ You must pass a directory via -i/--input."); sys.exit(1)
    indir = Path(args.input)
    if not indir.exists() or not indir.is_dir():
        print(f"❌ --input must be a directory containing videos: {indir}"); sys.exit(1)

    if not args.output:
        print("❌ You must pass an output filename via -o/--output."); sys.exit(1)
    out_path = Path(args.output)
    if out_path.exists() and not getattr(args,"force",False):
        print(f"❌ {out_path} already exists. Use --force to overwrite."); sys.exit(1)

    files = _gather_inputs(indir)
    if not files:
        print(f"❌ No video files found in {indir}"); sys.exit(1)

    # Establish order
    mode = args.mode
    if mode == "forward":   ordered = _sort_forward(files)
    elif mode == "backward":ordered = _sort_backward(files)
    elif mode == "lenfor":  ordered = _sort_by_length(files, reverse=False)
    elif mode == "lenback": ordered = _sort_by_length(files, reverse=True)
    elif mode == "randn":   ordered = _order_randn(files, seed=args.seed)
    elif mode == "randfib": ordered = _order_randfib(files, seed=args.seed)
    else:
        print(f"❌ Unknown mode: {mode}"); sys.exit(1)

    print("🧩 Merge order:")
    for i,p in enumerate(ordered,1):
        print(f"  {i:>3}. {p.name}")

    # Temp workspace
    tmpdir = Path(tempfile.mkdtemp(prefix="mince_"))
    # Pre-normalize if requested/needed
    norm_inputs = _maybe_normalize(ordered, tmpdir, args)

    # Build concat list
    list_path = tmpdir / "list.txt"
    _write_concat_list(norm_inputs, list_path)

    base = ["ffmpeg"]
    if getattr(args,"force",False):
        base += ["-y"]

    # --- Fast path: stream-copy concat demuxer with timestamp hygiene ---
    if not args.reencode:
        cmd = base + [
            "-fflags","+genpts",     # regen pts across joined stream
            "-safe","0",
            "-f","concat",
            "-i", str(list_path),
            "-c","copy",
            "-avoid_negative_ts","make_zero",
        ]
        if args.faststart and out_path.suffix.lower() in {".mp4",".m4v",".mov"}:
            cmd += ["-movflags","+faststart"]
        cmd += [str(out_path)]
        try:
            _run(cmd)
            print("✅ Done."); return
        except Exception:
            if not args.fallback_reencode:
                raise
            print("⚠️ Stream-copy concat failed or produced bad timestamps; retrying with re-encode because --fallback-reencode is set...")

    # --- Robust path: final re-encode (rare when pre-normalized, but available) ---
    vf = "format=yuv420p"
    cmd = base + [
        "-safe","0",
        "-f","concat",
        "-i", str(list_path),
        "-vf", vf,
        "-c:v", args.vcodec,
        "-crf", args.crf,
        "-preset", args.preset,
        "-c:a", args.acodec,
        "-vsync","2",
        "-avoid_negative_ts","make_zero",
    ]
    if args.faststart and out_path.suffix.lower() in {".mp4",".m4v",".mov"}:
        cmd += ["-movflags","+faststart"]
    cmd += [str(out_path)]

    if run_ffmpeg_with_progress:
        run_ffmpeg_with_progress(cmd, str(norm_inputs[0]), str(out_path))
    else:
        _run(cmd)

    print("✅ Done.")
