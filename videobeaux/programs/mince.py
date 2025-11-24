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

Engines:
  demuxer (default) : concat demuxer. Fast (copy) when inputs match; safest if you pre-normalize.
  filter            : single-pass filter_complex concat. Use when you want everything in one encode.

Safeties:
  --decode-tolerant : ignore tiny decode errors; drop corrupt packets instead of stalling.
  --hard-trim       : trim each clip’s A/V to its probed duration before concat (prevents frozen tails).
"""

import re
import sys
import random
import tempfile
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

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
            ["ffprobe","-v","error","-show_entries","format=duration",
             "-of","default=noprint_wrappers=1:nokey=1",str(path)],
            stderr=subprocess.STDOUT
        ).decode().strip()
        return float(out)
    except Exception:
        return 0.0

def _probe_wh(path: Path) -> Tuple[int,int]:
    try:
        out = subprocess.check_output(
            ["ffprobe","-v","error","-select_streams","v:0",
             "-show_entries","stream=width,height",
             "-of","csv=p=0", str(path)],
            stderr=subprocess.STDOUT
        ).decode().strip()
        w,h = out.split(",")
        return int(w), int(h)
    except Exception:
        return 1920,1080

def _has_audio(path: Path) -> bool:
    try:
        out = subprocess.check_output(
            ["ffprobe","-v","error","-select_streams","a:0",
             "-show_entries","stream=index","-of","csv=p=0", str(path)],
            stderr=subprocess.STDOUT
        ).decode().strip()
        return bool(out)
    except Exception:
        return False

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

def _parse_size(size: Optional[str]) -> Optional[tuple]:
    if not size: return None
    if "x" not in size.lower():
        raise ValueError("Size must be WxH, e.g., 1920x1080")
    w,h = size.lower().split("x",1)
    return int(w), int(h)

# ---------- Filters for filter engine ----------

def _norm_vfilter(w: int, h: int, fit: str, pixfmt: str, fps: Optional[float]) -> str:
    chain = "settb=AVTB,setpts=PTS-STARTPTS,"
    if fit == "fit":
        chain += (f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
                  f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black,"
                  f"setsar=1,setdar={w}/{h},format={pixfmt}")
    elif fit == "fill":
        chain += (f"scale={w}:{h}:force_original_aspect_ratio=increase,"
                  f"crop={w}:{h},setsar=1,setdar={w}/{h},format={pixfmt}")
    elif fit == "stretch":
        chain += f"scale={w}:{h},setsar=1,setdar={w}/{h},format={pixfmt}"
    else:
        raise ValueError("fit must be one of: fit, fill, stretch")
    if fps:
        chain += f",fps={fps}:round=near"
    return chain

def _norm_afilter_existing(ar: int, ac: int) -> str:
    layout = "stereo" if ac == 2 else "mono"
    return (f"asetpts=PTS-STARTPTS,"
            f"aresample={ar}:async=1:first_pts=0,"
            f"aformat=sample_rates={ar}:channel_layouts={layout}")

def _norm_afilter_silence(ar: int, ac: int, dur: float) -> str:
    layout = "stereo" if ac == 2 else "mono"
    return (f"anullsrc=r={ar}:cl={layout},"
            f"atrim=0:{dur:.6f},"
            f"asetpts=PTS-STARTPTS,"
            f"aformat=sample_rates={ar}:channel_layouts={layout}")

# ---------- File list writer for demuxer ----------

def _ff_concat_escape(p: Path) -> str:
    s = str(p.resolve(strict=False))
    return s.replace("'", r"'\''")

def _write_concat_list(paths: List[Path], list_path: Path):
    list_path.parent.mkdir(parents=True, exist_ok=True)
    with list_path.open("w", encoding="utf-8", newline="\n") as f:
        for p in paths:
            esc = _ff_concat_escape(p)
            f.write(f"file '{esc}'\n")

# ---------- Pre-normalize (demuxer engine, optional) ----------

def _build_norm_cmd(src: Path, dst: Path, w: int, h: int, fit: str,
                    fps: Optional[float], ar: int, ac: int, pixfmt: str,
                    vcodec: str, crf: str, preset: str, faststart: bool,
                    decode_tolerant: bool, hard_trim: bool, dur: float) -> List[str]:
    # Video normalize chain
    if fit == "fit":
        vf = (f"settb=AVTB,setpts=PTS-STARTPTS,"
              f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
              f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black,"
              f"setsar=1,setdar={w}/{h},format={pixfmt}")
    elif fit == "fill":
        vf = (f"settb=AVTB,setpts=PTS-STARTPTS,"
              f"scale={w}:{h}:force_original_aspect_ratio=increase,"
              f"crop={w}:{h},setsar=1,setdar={w}/{h},format={pixfmt}")
    else:
        vf = f"settb=AVTB,setpts=PTS-STARTPTS,scale={w}:{h},setsar=1,setdar={w}/{h},format={pixfmt}"
    if fps:
        vf += f",fps={fps}:round=near"
    if hard_trim and dur > 0:
        vf += f",trim=start=0:duration={dur:.6f},setpts=PTS-STARTPTS"

    # input flags (FIX: combine -fflags values into one arg)
    inp = ["-fflags","+genpts"]
    if decode_tolerant:
        inp = ["-err_detect","ignore_err","-fflags","+discardcorrupt+genpts"]

    cmd = ["ffmpeg","-y"] + inp + ["-i", str(src),
           "-vf", vf,
           "-c:v", vcodec, "-crf", crf, "-preset", preset,
           "-c:a", "aac", "-ar", str(ar), "-ac", str(ac),
           "-avoid_negative_ts","make_zero"]
    if faststart and dst.suffix.lower() in {".mp4",".m4v",".mov"}:
        cmd += ["-movflags","+faststart"]
    if hard_trim and dur > 0:
        cmd += ["-af", f"atrim=start=0:duration={dur:.6f},asetpts=PTS-STARTPTS"]
    cmd += [str(dst)]
    return cmd

def _maybe_prenormalize(inputs: List[Path], tmpdir: Path, args) -> List[Path]:
    need = bool(args.size or args.fps or args.normalize or args.hard_trim)
    if not need:
        return inputs
    w,h = _parse_size(args.size) if args.size else (_probe_wh(inputs[0]))
    out = []
    for i, src in enumerate(inputs):
        dst = tmpdir / f"norm_{i:04d}.mp4"
        dur = _probe_duration_seconds(src)
        cmd = _build_norm_cmd(src, dst, w, h, args.fit, args.fps,
                              args.ar, args.ac, args.pixfmt,
                              args.norm_vcodec, args.norm_crf, args.norm_preset, args.faststart,
                              getattr(args,"decode_tolerant",False),
                              getattr(args,"hard_trim",False), dur if dur>0 else 0.0)
        print("↪︎", " ".join(cmd))
        if subprocess.run(cmd).returncode != 0:
            raise RuntimeError("ffmpeg normalization failed")
        out.append(dst)
    return out

# ---------- Args ----------

def register_arguments(parser: argparse.ArgumentParser):
    parser.description = (
        "Mince: merge a folder of videos into one output in a chosen order.\n"
        "Default engine is 'demuxer' (concat demuxer). Use --engine filter for in-graph concat."
    )

    parser.add_argument("--mode",
        choices=["forward","backward","lenfor","lenback","randn","randfib"],
        required=True, help="Sequence strategy.")
    parser.add_argument("--seed", type=int, default=None,
        help="Random seed for randn / randfib (stable ordering if provided).")

    parser.add_argument("--engine", choices=["demuxer","filter"], default="demuxer",
        help="Concat engine: 'demuxer' (fast) or 'filter' (single-pass encode). Default: demuxer.")

    # Demuxer engine options
    parser.add_argument("--normalize", action="store_true",
        help="(demuxer) Pre-normalize sources so -c copy concat is safe.")
    parser.add_argument("--size", type=str, default=None,
        help="Target WxH (e.g., 1920x1080). If omitted and --normalize, infer from first clip.")
    parser.add_argument("--fit", type=str, choices=["fit","fill","stretch"], default="fit",
        help="Mapping from source AR to target size (default: fit).")
    parser.add_argument("--fps", type=float, default=None,
        help="Normalize video FPS (e.g., 30). Omit to keep native cadence.")
    parser.add_argument("--pixfmt", type=str, default="yuv420p",
        help="Pixel format for normalized clips (default: yuv420p).")
    parser.add_argument("--ar", type=int, default=48000,
        help="Audio sample rate (default: 48000).")
    parser.add_argument("--ac", type=int, default=2,
        help="Audio channels (default: 2).")
    parser.add_argument("--norm-vcodec", type=str, default="libx264",
        help="Video codec for normalized clips (default: libx264).")
    parser.add_argument("--norm-crf", type=str, default="20",
        help="CRF for normalized clips (default: 20).")
    parser.add_argument("--norm-preset", type=str, default="medium",
        help="x264 preset for normalized clips (default: medium).")

    # Final encode (filter engine) or demuxer fallback re-encode
    parser.add_argument("--vcodec", type=str, default="libx264",
        help="Final video codec (default: libx264).")
    parser.add_argument("--acodec", type=str, default="aac",
        help="Final audio codec (default: aac).")
    parser.add_argument("--crf", type=str, default="20",
        help="CRF for libx264 (default: 20).")
    parser.add_argument("--preset", type=str, default="medium",
        help="x264 preset (default: medium).")
    parser.add_argument("--faststart", action="store_true",
        help="Add +faststart for MP4/MOV containers.")
    parser.add_argument("--fallback-reencode", action="store_true",
        help="(demuxer) If copy-concat fails, retry with a re-encode.")

    # New safeties
    parser.add_argument("--decode-tolerant", action="store_true",
        help="Ignore minor decode errors and drop corrupt packets on input.")
    parser.add_argument("--hard-trim", action="store_true",
        help="Trim each clip’s A/V to its probed duration before concat.")

# ---------- Runner ----------

def run(args):
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

    if args.mode == "forward":    ordered = _sort_forward(files)
    elif args.mode == "backward": ordered = _sort_backward(files)
    elif args.mode == "lenfor":   ordered = _sort_by_length(files, reverse=False)
    elif args.mode == "lenback":  ordered = _sort_by_length(files, reverse=True)
    elif args.mode == "randn":    ordered = _order_randn(files, seed=args.seed)
    elif args.mode == "randfib":  ordered = _order_randfib(files, seed=args.seed)
    else:
        print(f"❌ Unknown mode: {args.mode}"); sys.exit(1)

    print("🧩 Merge order:")
    for i,p in enumerate(ordered,1):
        print(f"  {i:>3}. {p.name}")

    if args.engine == "demuxer":
        tmpdir = Path(tempfile.mkdtemp(prefix="mince_"))
        inputs = _maybe_prenormalize(ordered, tmpdir, args)

        list_path = tmpdir / "list.txt"
        _write_concat_list(inputs, list_path)

        base = ["ffmpeg"]
        if getattr(args,"force",False):
            base += ["-y"]

        # Fast copy-concat
        cmd = base + [
            "-fflags","+genpts",
            "-safe","0",
            "-f","concat",
            "-i", str(list_path),
            "-c","copy",
            "-avoid_negative_ts","make_zero",
            str(out_path)
        ]
        print("↪︎", " ".join(cmd))
        r = subprocess.run(cmd)
        if r.returncode == 0:
            print("✅ Done.")
            return

        if not args.fallback_reencode:
            raise RuntimeError(f"ffmpeg exited with code {r.returncode}")

        # Fallback re-encode
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
            "-avoid_negative_ts","make_zero",
            str(out_path)
        ]
        if args.faststart and out_path.suffix.lower() in {".mp4",".m4v",".mov"}:
            cmd += ["-movflags","+faststart"]
        print("↪︎", " ".join(cmd))
        if subprocess.run(cmd).returncode != 0:
            raise RuntimeError("ffmpeg re-encode failed")
        print("✅ Done.")
        return

    # ---------- filter engine ----------
    size = _parse_size(args.size)
    if size is None:
        w0,h0 = _probe_wh(ordered[0])
        size = (w0,h0)
        print(f"ℹ️  No --size provided; inferring from first clip: {w0}x{h0}")
    W,H = size

    cmd = ["ffmpeg"]
    if getattr(args,"force",False):
        cmd += ["-y"]

    vfilters: List[str] = []
    afilters: List[str] = []
    has_any_audio = False
    has_audio_list = []
    durations = []

    for idx, p in enumerate(ordered):
        # Input flags per clip (FIX: combine -fflags values)
        inp_flags = ["-fflags","+genpts"]
        if getattr(args,"decode_tolerant",False):
            inp_flags = ["-err_detect","ignore_err","-fflags","+discardcorrupt+genpts"]
        cmd += inp_flags + ["-i", str(p)]

        dur = _probe_duration_seconds(p)
        durations.append(dur if dur > 0 else 0.0)

        has_a = _has_audio(p)
        has_audio_list.append(has_a)
        if has_a:
            has_any_audio = True

        vnorm = _norm_vfilter(W,H,args.fit,args.pixfmt,args.fps)
        if getattr(args,"hard_trim",False) and dur > 0:
            vnorm += f",trim=start=0:duration={dur:.6f},setpts=PTS-STARTPTS"
        vfilters.append(f"[{idx}:v] {vnorm} [v{idx}]")

        if has_a:
            anorm = _norm_afilter_existing(args.ar,args.ac)
            if getattr(args,"hard_trim",False) and dur > 0:
                anorm += f",atrim=start=0:duration={dur:.6f},asetpts=PTS-STARTPTS"
            afilters.append(f"[{idx}:a] {anorm} [a{idx}]")
        else:
            # if any audio exists elsewhere, we'll synth silence later for this one
            pass

    parts: List[str] = []
    if vfilters:
        parts.append(";".join(vfilters))

    v_stack = "".join([f"[v{idx}]" for idx in range(len(ordered))])

    if has_any_audio:
        for idx, has_a in enumerate(has_audio_list):
            if not has_a:
                dur = durations[idx] if durations[idx] > 0 else 0.001
                anorm = _norm_afilter_silence(args.ar,args.ac,dur)
                afilters.append(f"{anorm} [a{idx}]")
        if afilters:
            parts.append(";".join(afilters))

        a_stack = "".join([f"[a{idx}]" for idx in range(len(ordered))])
        concat = f"{v_stack}{a_stack}concat=n={len(ordered)}:v=1:a=1[vout][aout]"
        parts.append(concat)

        filter_complex = ";".join(parts)
        cmd += ["-filter_complex", filter_complex,
                "-map","[vout]","-map","[aout]",
                "-c:v", args.vcodec,
                "-crf", args.crf,
                "-preset", args.preset,
                "-c:a", args.acodec,
                "-pix_fmt", args.pixfmt]
    else:
        concat = f"{v_stack}concat=n={len(ordered)}:v=1:a=0[vout]"
        parts.append(concat)
        filter_complex = ";".join(parts)
        cmd += ["-filter_complex", filter_complex,
                "-map","[vout]",
                "-c:v", args.vcodec,
                "-crf", args.crf,
                "-preset", args.preset,
                "-pix_fmt", args.pixfmt]

    if args.faststart and out_path.suffix.lower() in {".mp4",".m4v",".mov"}:
        cmd += ["-movflags","+faststart"]
    cmd += [str(out_path)]

    print("↪︎"," ".join(map(str,cmd)))
    if subprocess.run(cmd).returncode != 0:
        raise RuntimeError("ffmpeg filter-engine failed")

    print("✅ Done.")
