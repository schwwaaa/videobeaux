# videobeaux/programs/qwikchop.py
# Qwikchop (export-only, seamless heads)
# - Create EXACTLY N edits from each input video.
# - Optional: trim leading black/fade at each edit head, and lightly pad edges.
# - Export edits into a folder. No concat/merge.

import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress


# ---------------- helpers ----------------

def _ffprobe_duration_seconds(path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode("utf-8", "ignore").strip()
    try:
        return float(out)
    except Exception:
        return 0.0


def _mkdir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def _videos_in_dir(d: Path, recurse: bool) -> List[Path]:
    exts = {".mp4", ".mov", ".m4v"}
    it = d.rglob("*") if recurse else d.iterdir()
    return sorted([p for p in it if p.is_file() and p.suffix.lower() in exts])


def _work_and_export_paths(inp: Path, output_base: str | None) -> Tuple[Path, Path]:
    """
    Return (work_dir, export_dir).
    - If -o/--output is provided (cli may coerce .mp4), use its stem as base.
    - Otherwise use folders next to the input.
    """
    if output_base:
        base = Path(output_base).with_suffix("")  # strip .mp4 if cli added it
        work_dir = base.parent / f"{base.stem}_{inp.stem}_qwik_tmp"
        export_dir = base.parent / f"{inp.stem}_qwikchop"
    else:
        work_dir = inp.parent / f"{inp.stem}_qwik_tmp"
        export_dir = inp.parent / f"{inp.stem}_qwikchop"
    return work_dir, export_dir


# ---- black leader detection ----

_BLACK_LINE = re.compile(r"black_start:(?P<bs>[-\d\.]+)\s+black_end:(?P<be>[-\d\.]+)\s+black_duration:(?P<bd>[-\d\.]+)")

def _measure_leading_black(
    src: Path,
    start_ts: float,
    scan_window: float,
    thresh: float,
    pic_th: float
) -> float:
    """
    Probe the first 'scan_window' seconds of the would-be edit for black content
    using ffmpeg blackdetect. Returns how many seconds to skip at the head.
    """
    # We analyze a short snippet starting at start_ts
    cmd = [
        "ffmpeg",
        "-ss", f"{start_ts:.6f}",
        "-t", f"{max(0.01, scan_window):.6f}",
        "-i", str(src),
        "-vf", f"blackdetect=d=0.02:thresh={thresh}:pic_th={pic_th}",
        "-an",
        "-f", "null",
        "-"
    ]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stderr = proc.stderr or ""
        # Look for first black region starting at 0
        trim = 0.0
        for line in stderr.splitlines():
            m = _BLACK_LINE.search(line)
            if not m:
                continue
            bs = float(m.group("bs"))
            be = float(m.group("be"))
            # blackdetect reports times relative to snippet start; if it starts near 0, trim to its end
            if -0.005 <= bs <= 0.005 and be > 0:
                trim = max(trim, be)
                break
        return max(0.0, trim)
    except Exception:
        return 0.0


def _segment_into_n_edits(
    inp: Path,
    work_dir: Path,
    pieces: int,
    edge_pad_pre: float,
    edge_pad_post: float,
    trim_black_front: bool,
    black_scan: float,
    black_thresh: float,
    black_pict: float,
    min_edit: float,
) -> List[Path]:
    """
    Split video into exactly N edits with optional leader trim and edge pads.
    Returns list of temp segment paths in natural order.
    """
    dur = _ffprobe_duration_seconds(inp)
    if dur <= 0:
        raise RuntimeError(f"Cannot read duration for {inp}")

    pieces = max(1, int(pieces))
    base_chunk = dur / pieces

    segs: List[Path] = []
    _mkdir(work_dir)
    pad_digits = max(4, len(str(pieces)))

    for i in range(pieces):
        # nominal bounds
        start = base_chunk * i
        end = dur if i == pieces - 1 else base_chunk * (i + 1)
        seg_dur = max(0.0, end - start)

        # shave tiny edges to dodge boundary fades
        start += edge_pad_pre
        seg_dur = max(0.0, seg_dur - (edge_pad_pre + edge_pad_post))

        # optional: detect and trim leading black within a small scan window
        if trim_black_front and seg_dur > 0.0:
            to_scan = min(black_scan, seg_dur)
            trim = _measure_leading_black(
                src=inp,
                start_ts=start,
                scan_window=to_scan,
                thresh=black_thresh,
                pic_th=black_pict,
            )
            if trim > 0:
                start += trim
                seg_dur = max(0.0, seg_dur - trim)

        # enforce minimum viable duration
        if seg_dur < min_edit:
            # collapse extremely short edits by borrowing a bit forward if possible
            # (keep simple: if last edit is too short, merge into previous by skipping)
            # For export-only and simplicity, skip zero/near-zero segments.
            if seg_dur <= 0.0:
                continue

        out_path = work_dir / f"seg_{i+1:0{pad_digits}d}.mp4"
        cmd = [
            "ffmpeg",
            "-ss", f"{start:.6f}",
            "-t", f"{seg_dur:.6f}",
            "-i", str(inp),
            "-map", "0:v:0",
            "-map", "0:a?",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-movflags", "+faststart",
            str(out_path),
        ]
        # Use the source file for progress probing (real media path)
        run_ffmpeg_with_progress(cmd, str(inp), str(out_path))
        segs.append(out_path)

    return segs


def _export_segments(inp: Path, segs: List[Path], export_dir: Path, force: bool):
    """
    Copy temp segments into export_dir with final names.
    """
    if export_dir.exists() and force:
        shutil.rmtree(export_dir, ignore_errors=True)
    _mkdir(export_dir)

    pad = max(4, len(str(len(segs))))
    for i, src in enumerate(segs, start=1):
        dst = export_dir / f"{inp.stem}_edit_{i:0{pad}d}.mp4"
        shutil.copy2(src, dst)

    print(f"📦 Exported {len(segs)} edits → {export_dir}")


def _qwikchop_one(args, inp: Path):
    work_dir, export_dir = _work_and_export_paths(inp, args.output)
    if work_dir.exists() and args.force:
        shutil.rmtree(work_dir, ignore_errors=True)

    segs = _segment_into_n_edits(
        inp=inp,
        work_dir=work_dir,
        pieces=args.pieces,
        edge_pad_pre=max(0.0, args.edge_pad_pre),
        edge_pad_post=max(0.0, args.edge_pad_post),
        trim_black_front=bool(args.trim_black_front),
        black_scan=max(0.01, args.black_scan),
        black_thresh=max(0.0, min(1.0, args.black_thresh)),
        black_pict=max(0.0, min(1.0, args.black_pict)),
        min_edit=max(0.01, args.min_edit),
    )
    if not segs:
        print(f"⚠️ No edits produced for {inp}")
        return

    _export_segments(inp, segs, export_dir, force=args.force)

    if not args.keep_temp:
        shutil.rmtree(work_dir, ignore_errors=True)


# ---------------- program API ----------------

def register_arguments(parser):
    parser.description = (
        "Qwikchop (export-only): create EXACTLY N edits from each input video and "
        "place them in a folder. Optional leader trim for seamless heads. No merging."
    )

    parser.add_argument("--pieces", type=int, required=True, help="Number of edits to create (exact count).")
    parser.add_argument("--recurse", action="store_true", help="If input is a directory, include subdirectories.")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary chunk files (debugging).")

    # Seamless options
    parser.add_argument("--trim-black-front", action="store_true",
                        help="Detect and remove leading black at the start of each edit.")
    parser.add_argument("--black-scan", type=float, default=0.25,
                        help="Seconds to scan at each edit head for black (default: 0.25).")
    parser.add_argument("--black-thresh", type=float, default=0.10,
                        help="Black luma threshold for blackdetect (0..1, default: 0.10).")
    parser.add_argument("--black-pict", type=float, default=0.10,
                        help="Min fraction of black pixels to count as black (0..1, default: 0.10).")
    parser.add_argument("--edge-pad-pre", type=float, default=0.03,
                        help="Seconds to shave from the very start of each edit (default: 0.03).")
    parser.add_argument("--edge-pad-post", type=float, default=0.02,
                        help="Seconds to shave from the end of each edit (default: 0.02).")
    parser.add_argument("--min-edit", type=float, default=0.20,
                        help="Minimum allowed edit duration after trims (default: 0.20).")


def run(args):
    inp = Path(args.input) if getattr(args, "input", None) else None
    if not inp or not inp.exists():
        print("❌ You must pass a valid --input file or directory.")
        return

    if inp.is_file():
        _qwikchop_one(args, inp)
    else:
        vids = _videos_in_dir(inp, recurse=args.recurse)
        if not vids:
            print(f"⚠️ No videos found in {inp} (use --recurse to include subdirs).")
            return
        for v in vids:
            _qwikchop_one(args, v)
