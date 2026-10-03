from __future__ import annotations
import argparse
import json
import subprocess
from pathlib import Path

GUI_METADATA = {'output_type': 'json'}


def _ratio(s):
    try:
        a, b = str(s).split("/")
        return float(a) / float(b) if float(b) else None
    except Exception:
        return None


def _num(v, cast=float):
    try:
        return cast(v)
    except Exception:
        return None


def _hms(sec):
    if sec is None:
        return None
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:05.2f}"


def _human_size(n):
    if n is None:
        return None
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024


def _probe(path: Path) -> dict:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(f"❌ ffprobe failed: {proc.stderr.strip()}")
    return json.loads(proc.stdout or "{}")


def _rotation(st: dict):
    for sd in st.get("side_data_list") or []:
        if "rotation" in sd:
            return _num(sd["rotation"], int)
    return _num((st.get("tags") or {}).get("rotate"), int)


def build_report(path: Path) -> dict:
    data = _probe(path)
    fmt = data.get("format") or {}
    streams = data.get("streams") or []
    v = next((s for s in streams if s.get("codec_type") == "video" and s.get("disposition", {}).get("attached_pic") != 1), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)

    duration = _num(fmt.get("duration")) or (_num(v.get("duration")) if v else None)
    size = _num(fmt.get("size"), int)
    bitrate = _num(fmt.get("bit_rate"))
    fps = _ratio(v.get("avg_frame_rate")) if v else None
    if not fps and v:
        fps = _ratio(v.get("r_frame_rate"))
    nb_frames = _num(v.get("nb_frames"), int) if v else None
    if nb_frames is None and fps and duration:
        nb_frames = int(round(fps * duration))

    report = {
        "file": path.name,
        "path": str(path),
        "container": (fmt.get("format_name") or "").split(",")[0] or None,
        "duration_sec": round(duration, 3) if duration is not None else None,
        "duration_hms": _hms(duration),
        "size_bytes": size,
        "size_human": _human_size(size),
        "overall_bitrate_kbps": round(bitrate / 1000) if bitrate else None,
        "video": None,
        "audio": None,
        "stream_counts": {
            t: sum(1 for s in streams if s.get("codec_type") == t)
            for t in ("video", "audio", "subtitle", "data")
        },
    }
    if v:
        vb = _num(v.get("bit_rate"))
        report["video"] = {
            "codec": v.get("codec_name"),
            "profile": v.get("profile"),
            "width": v.get("width"),
            "height": v.get("height"),
            "resolution": f"{v.get('width')}x{v.get('height')}",
            "aspect_ratio": v.get("display_aspect_ratio"),
            "fps": round(fps, 3) if fps else None,
            "frames": nb_frames,
            "pix_fmt": v.get("pix_fmt"),
            "bitrate_kbps": round(vb / 1000) if vb else None,
            "rotation": _rotation(v),
            "color_space": v.get("color_space"),
            "color_transfer": v.get("color_transfer"),
        }
    if a:
        ab = _num(a.get("bit_rate"))
        report["audio"] = {
            "codec": a.get("codec_name"),
            "sample_rate_hz": _num(a.get("sample_rate"), int),
            "channels": a.get("channels"),
            "channel_layout": a.get("channel_layout"),
            "bitrate_kbps": round(ab / 1000) if ab else None,
        }
    return report


def format_summary(r: dict) -> str:
    lines = [f"📄 {r['file']}"]
    dur = f"{r['duration_hms']} ({r['duration_sec']}s)" if r["duration_sec"] is not None else "unknown"
    lines.append(f"   Container : {r['container']}   Duration: {dur}")
    size = r["size_human"] or "unknown"
    br = f"{r['overall_bitrate_kbps']} kbps" if r["overall_bitrate_kbps"] else "unknown"
    lines.append(f"   Size      : {size}   Bitrate: {br}")
    v, a = r["video"], r["audio"]
    if v:
        extras = [x for x in (
            v["codec"] + (f" ({v['profile']})" if v.get("profile") else ""),
            v["resolution"],
            f"AR {v['aspect_ratio']}" if v.get("aspect_ratio") else None,
            f"{v['fps']} fps" if v.get("fps") else None,
            f"{v['frames']} frames" if v.get("frames") else None,
            v.get("pix_fmt"),
            f"rot {v['rotation']}°" if v.get("rotation") else None,
        ) if x]
        lines.append("   Video     : " + " · ".join(extras))
    else:
        lines.append("   Video     : none")
    if a:
        extras = [x for x in (
            a["codec"],
            f"{a['sample_rate_hz']} Hz" if a.get("sample_rate_hz") else None,
            a.get("channel_layout") or (f"{a['channels']}ch" if a.get("channels") else None),
            f"{a['bitrate_kbps']} kbps" if a.get("bitrate_kbps") else None,
        ) if x]
        lines.append("   Audio     : " + " · ".join(extras))
    else:
        lines.append("   Audio     : none")
    return "\n".join(lines)


def register_arguments(parser: argparse.ArgumentParser):
    parser.description = (
        "Concise media report: dimensions, duration, fps, codecs, bitrate, size and audio "
        "details. Prints a readable summary to the log and writes the same data as JSON."
    )
    parser.add_argument("--no_json", action="store_true",
                        help="Only print the summary; don't write a JSON file.")


def run(args: argparse.Namespace):
    in_path = Path(args.input).resolve()
    if not in_path.exists():
        raise SystemExit(f"❌ Input not found: {in_path}")

    report = build_report(in_path)
    print(format_summary(report))

    if getattr(args, "no_json", False):
        return

    out = Path(args.output) if args.output else in_path.with_suffix(in_path.suffix + ".videobeaux.info.json")
    if out.suffix.lower() != ".json":
        out = out.with_suffix(".json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"🗂  Wrote media info → {out}")
