# videobeaux/programs/hash_fingerprint.py
from __future__ import annotations
import argparse, csv, hashlib, json, os, shlex, subprocess, sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Optional deps for perceptual hashing (gracefully degrade if missing)
try:
    from PIL import Image
    PIL_OK = True
except Exception:
    PIL_OK = False

VERSION = "videobeaux hash_fingerprint v1"

# Default file extensions we’ll scan in batch mode (can be overridden)
DEFAULT_EXTS = [
    ".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".wmv", ".mxf",
    ".mp3", ".m4a", ".aac", ".wav", ".flac", ".ogg", ".opus",
    ".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".gif"
]

def register_arguments(parser: argparse.ArgumentParser):
    parser.description = (
        "Compute file hashes (md5/sha1/sha256), optional FFmpeg stream hash, per-frame checksums, "
        "and optional perceptual hashes over sampled frames. Works on a single input or a directory."
    )

    # Discovery / batch
    parser.add_argument("--recursive", action="store_true",
                        help="If input is a directory, scan recursively.")
    parser.add_argument("--exts", nargs="+", default=DEFAULT_EXTS,
                        help="File extensions to include when scanning a directory (case-insensitive).")

    # Algorithms
    parser.add_argument("--file-hashes", nargs="+",
                        choices=["md5", "sha1", "sha256"], default=["md5", "sha256"],
                        help="File-level hashes to compute (streamed, no load into RAM).")
    parser.add_argument("--stream-hash", choices=["none", "md5", "sha256"], default="none",
                        help="Use FFmpeg -f hash to hash the primary video stream (fast, codec-level).")
    parser.add_argument("--framemd5", action="store_true",
                        help="Emit per-frame checksums via FFmpeg -f framemd5 (verbose).")

    # Perceptual hashing (over sampled frames)
    parser.add_argument("--phash", action="store_true",
                        help="Compute perceptual hashes (average hash) over sampled frames. Requires Pillow.")
    parser.add_argument("--phash-fps", type=float, default=0.5,
                        help="Approx frames-per-second to sample for perceptual hashing (0.5 = one frame every 2s).")
    parser.add_argument("--phash-size", type=int, default=8,
                        help="aHash size NxN (default 8 -> 64-bit hash).")

    # Output catalog
    parser.add_argument("--catalog", required=False,
                        help="Output catalog path (.json or .csv). If not provided, writes <first_input>.hashes.json")

    # Stream selection (advanced)
    parser.add_argument("--stream-kind", choices=["video", "audio"], default="video",
                        help="Which primary stream to hash for --stream-hash/--framemd5.")

    # Force overwrite behavior is handled at top-level; we just respect existing files for CSV/JSON if desired.

# ----------------- helpers -----------------

def _iter_files(entry: Path, exts: List[str], recursive: bool) -> List[Path]:
    if entry.is_file():
        return [entry]
    exts_lower = {e.lower() for e in exts}
    files: List[Path] = []
    walker = entry.rglob("*") if recursive else entry.glob("*")
    for p in walker:
        if p.is_file() and p.suffix.lower() in exts_lower:
            files.append(p)
    return sorted(files)

def _hash_file(path: Path, method: str) -> str:
    h = hashlib.new(method)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def _ffmpeg_stream_hash(path: Path, algo: str, kind: str) -> Optional[str]:
    # Map selection
    stream_map = "0:v:0" if kind == "video" else "0:a:0"
    cmd = [
        "ffmpeg", "-v", "error", "-i", str(path),
        "-map", stream_map,
        "-f", "hash", "-hash", algo, "-"
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        return None
    # Output line like "MD5=xxxxxxxx" or "SHA256=xxxxxxxx"
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if "=" in line:
            return line.split("=", 1)[1].strip()
    return None

def _ffmpeg_framemd5(path: Path, kind: str) -> List[str]:
    stream_map = "0:v:0" if kind == "video" else "0:a:0"
    cmd = [
        "ffmpeg", "-v", "error", "-i", str(path),
        "-map", stream_map,
        "-f", "framemd5", "-"
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        return []
    # Return raw lines (CSV/JSON writer can embed or omit)
    return [ln.rstrip("\n") for ln in (proc.stdout or "").splitlines()]

def _extract_sample_frames(path: Path, fps: float) -> List[Path]:
    """
    Extract sampled frames to a temp folder next to file. Caller cleans up or keeps ephemeral.
    For catalog reproducibility we won't delete by default (caller may choose).
    """
    out_dir = path.parent / (path.stem + ".hashframes")
    out_dir.mkdir(parents=True, exist_ok=True)
    # Use -q:v 4 for decent JPEG; names frame_000001.jpg etc.
    cmd = [
        "ffmpeg", "-v", "error", "-i", str(path),
        "-vf", f"fps={fps}",
        "-qscale:v", "4",
        str(out_dir / "frame_%06d.jpg")
    ]
    subprocess.run(cmd, check=False)
    return sorted(out_dir.glob("frame_*.jpg"))

def _ahash_image(p: Path, size: int) -> Optional[str]:
    if not PIL_OK:
        return None
    try:
        img = Image.open(p).convert("L").resize((size, size))
        px = list(img.getdata())
        avg = sum(px) / float(len(px))
        bits = "".join("1" if val >= avg else "0" for val in px)
        # pack into hex (4 bits per hex char)
        width = size * size
        hex_len = (width + 3) // 4
        return f"{int(bits, 2):0{hex_len}x}"
    except Exception:
        return None

def _catalog_default_path(first_input: Path) -> Path:
    return first_input.with_suffix(first_input.suffix + ".hashes.json")

def _write_json(path: Path, rows: List[Dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

def _write_csv(path: Path, rows: List[Dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    # stable column order
    field_order = [
        "path", "size_bytes",
        "file_md5", "file_sha1", "file_sha256",
        "stream_md5", "stream_sha256",
        "phash_algo", "phash_size", "phash_frames",
    ]
    # Include framemd5? We'll omit from CSV (too verbose). JSON includes it if requested.
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=field_order, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

# ----------------- main -----------------

def run(args: argparse.Namespace):
    input_path = Path(args.input)  # global CLI provides this
    entries: List[Path] = []

    if not input_path.exists():
        print(f"❌ Input not found: {input_path}")
        sys.exit(1)

    if input_path.is_dir():
        entries = _iter_files(input_path, args.exts, args.recursive)
        if not entries:
            print(f"⚠️ No files found in {input_path} (recursive={args.recursive}, exts={args.exts})")
            sys.exit(0)
    else:
        entries = [input_path]

    # Determine catalog path
    if args.catalog:
        catalog_path = Path(args.catalog)
    else:
        catalog_path = _catalog_default_path(entries[0])

    results: List[Dict] = []

    for p in entries:
        rec: Dict[str, Optional[str] | int | List[str] | Dict] = {}
        rec["path"] = str(p.resolve())
        try:
            rec["size_bytes"] = p.stat().st_size
        except Exception:
            rec["size_bytes"] = None

        # File-level hashes
        for h in args.file_hashes:
            try:
                rec[f"file_{h}"] = _hash_file(p, h)
            except Exception as e:
                rec[f"file_{h}"] = None

        # Stream hash via FFmpeg
        if args.stream_hash != "none":
            try:
                sh = _ffmpeg_stream_hash(p, args.stream_hash, args.stream_kind)
                rec[f"stream_{args.stream_hash}"] = sh
            except Exception:
                rec[f"stream_{args.stream_hash}"] = None

        # framemd5 (verbose)
        if args.framemd5:
            try:
                rec["framemd5"] = _ffmpeg_framemd5(p, args.stream_kind)
            except Exception:
                rec["framemd5"] = []

        # Perceptual hashing over sampled frames
        if args.phash:
            if not PIL_OK:
                rec["phash_error"] = "Pillow not installed; install Pillow to enable perceptual hashing."
            else:
                frames = _extract_sample_frames(p, fps=max(0.01, float(args.phash_fps)))
                hashes = []
                for fp in frames:
                    h = _ahash_image(fp, size=max(4, int(args.phash_size)))
                    if h:
                        hashes.append(h)
                rec["phash_algo"] = "aHash"
                rec["phash_size"] = int(args.phash_size)
                rec["phash_frames"] = len(hashes)
                rec["phash_list"] = hashes  # keep full list in JSON; CSV will ignore

        results.append(rec)

    # Write catalog
    suffix = catalog_path.suffix.lower()
    if suffix == ".csv":
        _write_csv(catalog_path, results)
    else:
        # default JSON
        _write_json(catalog_path, results)

    print(f"📒 Wrote catalog → {catalog_path} ({len(results)} item(s))")
