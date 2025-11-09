#!/usr/bin/env python3
# videobeaux/programs/subs_convert.py
#
# Subtitles Extract / Convert for videobeaux.
#
# Modes:
#  A) VIDEO INPUT  (-i video.{mp4,mov,mkv,...})
#     - --list                : print subtitle streams and exit
#     - extract/convert tracks to files:
#         --indexes 0,2       : extract by stream index
#         --langs eng,spa     : extract by language code (ffprobe 'tags:language')
#         --all               : extract all subtitle streams
#         --forced-only       : only streams with disposition.forced == 1
#         --exclude-hi        : exclude hearing_impaired disposition
#         --format srt|vtt|ass: convert to target format (default: inferred)
#         --outdir DIR        : write multiple outputs
#         --outputfile PATH   : write exactly one output (only valid when extracting a single stream)
#         --time-shift +/-S   : shift subs by seconds (float; may be negative)
#
#  B) SUBTITLE INPUT (-i subs.{srt,ass,vtt})
#     - Convert single file to target format:
#         --format srt|vtt|ass (required)
#         --outputfile PATH   (required)
#         --time-shift +/-S   (optional)
#
# Notes:
#  - We prefer --outputfile for single-output artifacts and --outdir for multi-output batches.
#  - ffprobe + ffmpeg must be on PATH.

from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress


# ------------------------------
# Helpers
# ------------------------------
def _run_ffprobe_streams(input_path: Path) -> List[Dict[str, Any]]:
    """Return list of subtitle streams from ffprobe (may be empty)."""
    cmd = [
        "ffprobe", "-v", "error",
        "-print_format", "json",
        "-show_entries", "stream=index,codec_name,codec_type,disposition:stream_tags=language,title",
        "-select_streams", "s",
        str(input_path)
    ]
    try:
        out = subprocess.check_output(cmd)
        data = json.loads(out.decode("utf-8", errors="replace"))
        return data.get("streams", []) or []
    except subprocess.CalledProcessError as e:
        raise SystemExit(f"❌ ffprobe failed: {e}")

def _is_subtitle_file(path: Path) -> bool:
    return path.suffix.lower() in {".srt", ".ass", ".ssa", ".vtt", ".sub"}

def _infer_target_ext(codec_name: Optional[str]) -> str:
    # Sensible defaults when --format not provided for video-extract mode
    if not codec_name:
        return ".srt"
    c = codec_name.lower()
    if c in {"subrip"}:           # ffprobe calls SRT 'subrip'
        return ".srt"
    if c in {"webvtt", "vtt"}:
        return ".vtt"
    if c in {"ass", "ssa"}:
        return ".ass"
    if c in {"mov_text"}:
        return ".srt"  # transcode mov_text to SRT by default
    return ".srt"

def _format_to_ext(fmt: str) -> str:
    fmt = fmt.lower()
    if fmt not in {"srt","vtt","ass"}:
        raise SystemExit("❌ --format must be one of: srt, vtt, ass")
    return f".{fmt}"

def _parse_index_list(val: str) -> List[int]:
    try:
        return [int(x.strip()) for x in val.split(",") if x.strip() != ""]
    except Exception:
        raise SystemExit("❌ --indexes expects a comma-separated list of integers, e.g., 0,2,3")

def _parse_langs(val: str) -> List[str]:
    return [x.strip().lower() for x in val.split(",") if x.strip() != ""]

def _disp_is_forced(disp: Dict[str, Any]) -> bool:
    return bool(disp.get("forced", 0))

def _disp_is_hi(disp: Dict[str, Any]) -> bool:
    # Some containers mark 'hearing_impaired'; if absent, assume False
    return bool(disp.get("hearing_impaired", 0))

def _select_streams(streams: List[Dict[str, Any]],
                    indexes: Optional[List[int]],
                    langs: Optional[List[str]],
                    forced_only: bool,
                    exclude_hi: bool) -> List[Dict[str, Any]]:
    sel = []
    for st in streams:
        if st.get("codec_type") != "subtitle":
            continue
        idx_ok = True
        lang_ok = True
        forced_ok = True
        hi_ok = True

        if indexes is not None:
            idx_ok = (st.get("index") in indexes)

        if langs is not None:
            lang_tag = (st.get("tags", {}) or {}).get("language", "")
            lang_ok = (lang_tag.lower() in langs)

        if forced_only:
            forced_ok = _disp_is_forced(st.get("disposition", {}) or {})

        if exclude_hi:
            hi_ok = not _disp_is_hi(st.get("disposition", {}) or {})

        if idx_ok and lang_ok and forced_ok and hi_ok:
            sel.append(st)
    return sel

def _shift_args(seconds: float) -> List[str]:
    # Apply time shift using -itsoffset on the subtitle input branch.
    # We’ll insert these flags just before the subtitle -i when needed.
    return ["-itsoffset", str(seconds)]

def _target_codec_for(fmt: str) -> str:
    # ffmpeg subtitle encoders by container:
    # srt:     -c:s srt
    # webvtt:  -c:s webvtt
    # ass:     -c:s ass
    m = {"srt":"srt", "vtt":"webvtt", "ass":"ass"}
    return m[fmt]

def _print_list(streams: List[Dict[str, Any]], src: Path) -> None:
    if not streams:
        print(f"(no subtitle streams) — {src}")
        return
    print(f"Subtitle streams in: {src}")
    for st in streams:
        i   = st.get("index")
        c   = st.get("codec_name", "?")
        tag = st.get("tags", {}) or {}
        lang = tag.get("language", "")
        title = tag.get("title", "")
        disp = st.get("disposition", {}) or {}
        forced = "forced" if disp.get("forced",0)==1 else ""
        hi     = "hearing_impaired" if disp.get("hearing_impaired",0)==1 else ""
        flags  = ", ".join(x for x in (forced, hi) if x)
        flags  = f" [{flags}]" if flags else ""
        print(f"  index={i:>2}  codec={c:8}  lang={lang or '-':3}  title={title or '-'}{flags}")

# ------------------------------
# CLI
# ------------------------------
def register_arguments(parser: argparse.ArgumentParser):
    parser.description = (
        "List, extract, and convert subtitle tracks. "
        "Works with container-embedded subtitles or standalone .srt/.ass/.vtt files."
    )

    # Selection (video mode)
    parser.add_argument("--list", action="store_true",
                        help="List subtitle streams in the input video and exit.")
    parser.add_argument("--indexes", type=str,
                        help="Comma-separated list of subtitle stream indexes to extract (e.g., '0,2').")
    parser.add_argument("--langs", type=str,
                        help="Comma-separated list of language codes to extract (e.g., 'eng,spa').")
    parser.add_argument("--all", action="store_true",
                        help="Extract all subtitle streams.")
    parser.add_argument("--forced-only", action="store_true",
                        help="Only include streams with 'forced' disposition.")
    parser.add_argument("--exclude-hi", action="store_true",
                        help="Exclude streams with 'hearing_impaired' disposition.")

    # Output control
    parser.add_argument("--format", choices=["srt","vtt","ass"],
                        help="Target subtitle format for output. Required for standalone subtitle conversion; optional for video mode.")
    parser.add_argument("--outdir", type=str,
                        help="Directory for multiple extracted subtitle files.")
    parser.add_argument("--outputfile", type=str,
                        help="Single output file path (only valid when extracting a single stream or converting a single subtitle file).")

    # Timing
    parser.add_argument("--time-shift", type=float, default=0.0,
                        help="Apply time shift in seconds (can be negative).")

    # Note: -i/--input and -F/--force are handled by top-level CLI.

# ------------------------------
# Main execution
# ------------------------------
def run(args: argparse.Namespace):
    in_path = Path(args.input)
    if not in_path.exists():
        raise SystemExit(f"❌ Input not found: {in_path}")

    is_sub_file = _is_subtitle_file(in_path)

    # Standalone subtitle conversion mode
    if is_sub_file:
        if not args.format:
            raise SystemExit("❌ --format is required when input is a subtitle file.")
        if not args.outputfile:
            raise SystemExit("❌ --outputfile is required when input is a subtitle file.")

        fmt = args.format.lower()
        out_path = Path(args.outputfile)
        if out_path.suffix.lower() != f".{fmt}":
            out_path = out_path.with_suffix(f".{fmt}")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # ffmpeg: sub file -> target format
        # Use -itsoffset if time-shift != 0
        cmd = ["ffmpeg"]
        if args.time_shift and args.time_shift != 0.0:
            cmd += _shift_args(args.time_shift)
        cmd += ["-i", str(in_path),
                "-map", "0:s:0",
                "-c:s", _target_codec_for(fmt),
                str(out_path)]
        if getattr(args, "force", False):
            cmd = cmd[:1] + ["-y"] + cmd[1:]
        run_ffmpeg_with_progress(cmd, args.input, out_path)
        return

    # Video mode (container with possible subtitle streams)
    streams = _run_ffprobe_streams(in_path)

    if args.list:
        _print_list(streams, in_path)
        return

    # Build selection
    indexes = _parse_index_list(args.indexes) if args.indexes else None
    langs = _parse_langs(args.langs) if args.langs else None
    selected = _select_streams(streams, indexes, langs, args.forced_only, args.exclude_hi)

    if args.all:
        selected = streams[:]  # all subtitle streams (already filtered by ffprobe)

    if not selected:
        raise SystemExit("❌ No subtitle streams matched your selection. Use --list to inspect indices and languages.")

    # Output policy
    single_output = (len(selected) == 1)
    if single_output and args.outputfile:
        # Write exactly one file
        st = selected[0]
        fmt = (args.format or _infer_target_ext(st.get("codec_name"))[1:]).lower()
        out_path = Path(args.outputfile)
        if out_path.suffix.lower() != f".{fmt}":
            out_path = out_path.with_suffix(f".{fmt}")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Build command
        # If time-shift, we insert -itsoffset before the video input, then map the subtitle stream.
        # We use -map 0:s:<RELATIVE_INDEX> ? Careful: stream.index is global stream index, not 's' index.
        # In ffmpeg, selecting a specific subtitle by absolute index can be done via -map 0:<stream_index>.
        abs_index = st.get("index")
        if abs_index is None:
            raise SystemExit("❌ Unexpected: stream lacks 'index' field.")

        fmt_target = (args.format or _infer_target_ext(st.get("codec_name"))[1:]).lower()
        cmd = ["ffmpeg"]
        if args.time_shift and args.time_shift != 0.0:
            cmd += _shift_args(args.time_shift)
        cmd += [
            "-i", str(in_path),
            "-map", f"0:{abs_index}",
            "-c:s", _target_codec_for(fmt_target),
            str(out_path)
        ]
        if getattr(args, "force", False):
            cmd = cmd[:1] + ["-y"] + cmd[1:]
        run_ffmpeg_with_progress(cmd, args.input, out_path)
        return

    # Multiple outputs → --outdir required
    if not args.outdir:
        raise SystemExit("❌ Multiple streams selected. Provide --outdir to write batch outputs.")

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # Build and run per-stream extraction
    for st in selected:
        idx = st.get("index")
        codec = st.get("codec_name", "")
        tags = (st.get("tags", {}) or {})
        lang = (tags.get("language") or "und").lower()
        title = tags.get("title") or ""
        # Decide extension
        ext = _format_to_ext(args.format) if args.format else _infer_target_ext(codec)
        # out name: <basename>_sIDX_LANG[optional_title_sanitized].ext
        base = in_path.stem
        title_part = f"_{_sanitize_filename(title)}" if title else ""
        out_path = outdir / f"{base}_s{idx}_{lang}{title_part}{ext}"

        # Build command
        cmd = ["ffmpeg"]
        if args.time_shift and args.time_shift != 0.0:
            cmd += _shift_args(args.time_shift)
        cmd += [
            "-i", str(in_path),
            "-map", f"0:{idx}",
            "-c:s", _target_codec_for((args.format or ext[1:]).lower()),
            str(out_path)
        ]
        if getattr(args, "force", False):
            cmd = cmd[:1] + ["-y"] + cmd[1:]
        run_ffmpeg_with_progress(cmd, args.input, out_path)


def _sanitize_filename(s: str) -> str:
    bad = '<>:"/\\|?*'
    out = "".join("_" if ch in bad else ch for ch in s)
    return out.strip()
