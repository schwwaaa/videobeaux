# videobeaux/programs/meta_extract.py
# Gather rich metadata with ffprobe + optional analyses (blackdetect, loudness, sampled frames).
# Writes INPUT.videobeaux.meta.json unless -o is provided.

from __future__ import annotations
import argparse, json, os, shlex, subprocess, sys, time
from pathlib import Path
from typing import Any, Dict, List, Tuple

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress  # not used directly but kept for parity

VERSION = "videobeaux meta_extract v1"

# ---------- Helpers ----------

def _run(cmd: List[str]) -> Tuple[int, str, str]:
    """Run a command, capture stdout/stderr, return (code, out, err)."""
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc.returncode, proc.stdout, proc.stderr

def _rational_to_float(s: str | None) -> float | None:
    if not s:
        return None
    if "/" in s:
        a, b = s.split("/", 1)
        try:
            return float(a) / float(b)
        except Exception:
            return None
    try:
        return float(s)
    except Exception:
        return None

def _fmt_hms(seconds: float | None) -> str | None:
    if seconds is None:
        return None
    s = float(seconds)
    hh = int(s // 3600)
    mm = int((s % 3600) // 60)
    ss = s - hh*3600 - mm*60
    return f"{hh:02d}:{mm:02d}:{ss:05.2f}"

def _infer_container(fmt_name: str | None) -> str | None:
    if not fmt_name:
        return None
    # ffprobe may return a comma list: "mov,mp4,m4a,3gp,3g2,mj2"
    return fmt_name.split(",")[0]

def _ensure_even(x: int) -> int:
    return x if x % 2 == 0 else x - 1

def _now_utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def _sidecar_path(in_path: Path, explicit_out: str | None) -> Path:
    if explicit_out:
        p = Path(explicit_out)
        if p.suffix.lower() != ".json":
            return p.with_suffix(".json")
        return p
    return in_path.with_suffix(in_path.suffix + ".videobeaux.meta.json")

def _safe_float(val: Any, default: float | None = None) -> float | None:
    try:
        return float(val)
    except Exception:
        return default

# ---------- ffprobe core ----------

def _ffprobe_basic(input_path: Path) -> Dict[str, Any]:
    cmd = [
        "ffprobe", "-v", "error",
        "-print_format", "json",
        "-show_format", "-show_streams", "-show_chapters",
        str(input_path)
    ]
    code, out, err = _run(cmd)
    if code != 0:
        raise SystemExit(f"❌ ffprobe failed ({code}): {err.strip() or out.strip()}")
    data = json.loads(out or "{}")

    # Derive a few niceties
    fmt = data.get("format", {}) or {}
    duration_sec = _safe_float(fmt.get("duration"))
    size_bytes = int(fmt.get("size")) if fmt.get("size") and str(fmt.get("size")).isdigit() else None
    bit_rate = _safe_float(fmt.get("bit_rate"))
    bitrate_mbps = (bit_rate / 1_000_000.0) if bit_rate else None

    # Stream partition
    v_streams, a_streams, s_streams = [], [], []
    for st in data.get("streams", []):
        codec_type = st.get("codec_type")
        if codec_type == "video":
            # SAR & DAR shapes + fps
            sar = st.get("sample_aspect_ratio") or "1:1"
            dar = st.get("display_aspect_ratio")
            avg_fps = st.get("avg_frame_rate") or st.get("r_frame_rate")
            v_streams.append({
                "index": st.get("index"),
                "codec_name": st.get("codec_name"),
                "profile": st.get("profile"),
                "width": st.get("width"),
                "height": st.get("height"),
                "pix_fmt": st.get("pix_fmt"),
                "sar": sar,
                "dar": dar,
                "avg_fps": avg_fps,
                "avg_fps_float": _rational_to_float(avg_fps),
                "time_base": st.get("time_base"),
                "color": {
                    "space": st.get("color_space"),
                    "primaries": st.get("color_primaries"),
                    "transfer": st.get("color_transfer")
                },
                "rotation": (st.get("tags") or {}).get("rotate") or st.get("side_data_list", [{}])[0].get("rotation"),
                "nb_frames": _safe_float(st.get("nb_frames"))
            })
        elif codec_type == "audio":
            a_streams.append({
                "index": st.get("index"),
                "codec_name": st.get("codec_name"),
                "sample_rate": _safe_float(st.get("sample_rate")),
                "channels": st.get("channels"),
                "channel_layout": st.get("channel_layout"),
                "bit_rate": _safe_float(st.get("bit_rate"))
            })
        elif codec_type == "subtitle":
            s_streams.append({
                "index": st.get("index"),
                "codec_name": st.get("codec_name"),
                "tags": st.get("tags", {})
            })

    chapters = []
    for ch in data.get("chapters", []):
        chapters.append({
            "id": ch.get("id"),
            "start_time": _safe_float(ch.get("start_time")),
            "end_time": _safe_float(ch.get("end_time")),
            "tags": ch.get("tags", {})
        })

    derived = {
        "has_video": bool(v_streams),
        "has_audio": bool(a_streams),
        "has_subtitles": bool(s_streams),
        "video_codecs": sorted({vs.get("codec_name") for vs in v_streams if vs.get("codec_name")}),
        "audio_codecs": sorted({as_.get("codec_name") for as_ in a_streams if as_.get("codec_name")}),
        "container": _infer_container(fmt.get("format_name")),
        "display_aspect_ratio": (v_streams[0].get("dar") if v_streams and v_streams[0].get("dar") else None),
        "duration_hms": _fmt_hms(duration_sec)
    }

    return {
        "format": {
            "filename": fmt.get("filename"),
            "format_name": fmt.get("format_name"),
            "duration_sec": duration_sec,
            "size_bytes": size_bytes,
            "bitrate_mbps": bitrate_mbps,
            "tags": fmt.get("tags", {})
        },
        "streams": {"video": v_streams, "audio": a_streams, "subtitle": s_streams},
        "chapters": chapters,
        "derived": derived,
        "provenance_cmd": " ".join(shlex.quote(c) for c in cmd)
    }

# ---------- Optional: sample frames ----------

def _sample_frames(input_path: Path, stride_sec: float, limit: int | None) -> Dict[str, Any]:
    """
    Use ffprobe to sample frames every `stride_sec`.
    We'll read a time range list to probe quickly.
    """
    out_frames: List[Dict[str, Any]] = []
    counts = {"I": 0, "P": 0, "B": 0}

    # ffprobe can't "step" directly by time, so use read_intervals with many short spans.
    # A simpler/robust approach: show_frames and let ffprobe emit frames; we downsample by time modulo.
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "frame=pkt_pts_time,key_frame,pict_type,width,height",
        "-of", "json",
        str(input_path)
    ]
    code, out, err = _run(cmd)
    if code != 0:
        return {"enabled": False, "reason": "ffprobe error", "frames": [], "frame_type_histogram": {}}

    data = json.loads(out or "{}")
    frames = data.get("frames", [])
    last_emit_t = -1e9
    for f in frames:
        t = _safe_float(f.get("pkt_pts_time"))
        if t is None:
            continue
        if (t - last_emit_t) >= stride_sec - 1e-6:
            rec = {
                "t": round(t, 3),
                "pict_type": f.get("pict_type"),
                "key_frame": int(f.get("key_frame") or 0),
                "w": f.get("width"),
                "h": f.get("height")
            }
            out_frames.append(rec)
            last_emit_t = t
            if limit and len(out_frames) >= limit:
                break
        # histogram (count all frames, not just sampled)
        pt = f.get("pict_type")
        if pt in counts:
            counts[pt] += 1

    return {
        "enabled": True,
        "frame_sample_stride_sec": stride_sec,
        "frames": out_frames,
        "frame_type_histogram": {k: v for k, v in counts.items() if v}
    }

# ---------- Optional: blackdetect ----------

def _blackdetect(input_path: Path, pic_th: float, dur_th: float) -> Dict[str, Any]:
    """
    Run ffmpeg blackdetect and parse 'black_start', 'black_end', 'black_duration' log lines.
    """
    vf = f"blackdetect=d={dur_th}:pic_th={pic_th}"
    cmd = [
        "ffmpeg", "-v", "error", "-nostats",
        "-i", str(input_path),
        "-vf", vf,
        "-f", "null", "-"
    ]
    # We must capture stderr where blackdetect logs to.
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = proc.communicate()
    if proc.returncode not in (0, 255):  # ffmpeg often returns 255 with -f null - on some builds; accept both
        return {"enabled": True, "events": [], "total_black_time": 0.0, "error": err.strip()}

    events = []
    total = 0.0
    for line in (err or "").splitlines():
        line = line.strip()
        # lines like: black_start:0 black_end:0.24 black_duration:0.24
        if "black_start" in line and "black_end" in line and "black_duration" in line:
            parts = line.replace(":", " ").split()
            # ["black_start","0","black_end","0.24","black_duration","0.24"]
            try:
                bs = float(parts[1]); be = float(parts[3]); bd = float(parts[5])
                events.append({"start": round(bs, 3), "end": round(be, 3), "dur": round(bd, 3)})
                total += bd
            except Exception:
                pass

    return {
        "enabled": True,
        "threshold": pic_th,
        "duration_min": dur_th,
        "events": events,
        "total_black_time": round(total, 3)
    }

# ---------- Optional: loudness (EBU R128) ----------

def _loudness_ebur128(input_path: Path) -> Dict[str, Any]:
    """
    Use ffmpeg loudnorm analysis mode (I, LRA, true peak).
    """
    cmd = [
        "ffmpeg", "-v", "error", "-nostats",
        "-i", str(input_path),
        "-filter_complex", "ebur128=peak=true",
        "-f", "null", "-"
    ]
    code, out, err = _run(cmd)
    if code not in (0, 255):
        return {"enabled": True, "error": err.strip()}
    # ebur128 emits lines to stderr like: [Parsed_ebur128_0 ...] Summary:
    # I: -16.0 LUFS   LRA: 6.5 LU   TP: -1.23 dBFS
    integrated = lra = tp = None
    for line in (err or "").splitlines():
        s = line.strip()
        if "I:" in s and "LRA:" in s and "TP:" in s:
            # crude parse
            try:
                parts = s.replace("I:", "I ").replace("LRA:", "LRA ").replace("TP:", "TP ").split()
                # e.g., ["...", "I", "-16.0", "LUFS", "LRA", "6.5", "LU", "TP", "-1.23", "dBFS"]
                for i, tok in enumerate(parts):
                    if tok == "I":
                        integrated = _safe_float(parts[i+1])
                    if tok == "LRA":
                        lra = _safe_float(parts[i+1])
                    if tok == "TP":
                        tp = _safe_float(parts[i+1])
            except Exception:
                pass
    return {
        "enabled": True,
        "integrated_lufs": integrated,
        "lra": lra,
        "true_peak_dbfs": tp
    }

# ---------- CLI wiring ----------

def register_arguments(parser: argparse.ArgumentParser):
    parser.description = (
        "Extract extensive metadata to JSON, with optional analysis passes "
        "(frame sampling, blackdetect, EBU R128 loudness)."
    )
    parser.add_argument("--outputfile", "-O", help="Output JSON path (defaults to INPUT.videobeaux.meta.json)")
    parser.add_argument("--sample-frames", action="store_true",
                        help="Enable frame sampling via ffprobe (pict_type, keyframe, WxH).")
    parser.add_argument("--sample-stride", type=float, default=0.5,
                        help="Sampling stride in seconds (default 0.5).")
    parser.add_argument("--sample-limit", type=int, default=200,
                        help="Max sampled frames to keep (default 200).")
    parser.add_argument("--blackdetect", action="store_true",
                        help="Enable black frame detection summary.")
    parser.add_argument("--black-pic-th", type=float, default=0.10,
                        help="blackdetect picture threshold (default 0.10).")
    parser.add_argument("--black-dur-min", type=float, default=0.10,
                        help="Minimum black duration in seconds (default 0.10).")
    parser.add_argument("--loudness", action="store_true",
                        help="Run EBU R128 loudness analysis (integrated, LRA, true peak).")

def run(args: argparse.Namespace):
    in_path = Path(args.input).resolve()
    if not in_path.exists():
        raise SystemExit(f"❌ Input not found: {in_path}")

    out_json = _sidecar_path(in_path, args.output)

    # Base probe
    base = _ffprobe_basic(in_path)

    # Envelope + provenance
    result: Dict[str, Any] = {
        "input_path": str(in_path),
        "generated_at_utc": _now_utc_iso(),
        "provenance": {
            "version": VERSION,
            "ffprobe_cmd": base.get("provenance_cmd"),
        },
        "format": base.get("format"),
        "streams": base.get("streams"),
        "chapters": base.get("chapters"),
        "derived": base.get("derived"),
        "sampling": { "enabled": False },
        "analysis": {}
    }

    # Optional frame sampling
    if getattr(args, "sample_frames", False):
        samp = _sample_frames(in_path, float(args.sample_stride), int(args.sample_limit) if args.sample_limit else None)
        result["sampling"] = samp

    # Optional blackdetect
    if getattr(args, "blackdetect", False):
        bd = _blackdetect(in_path, float(args.black_pic_th), float(args.black_dur_min))
        result.setdefault("analysis", {})["blackdetect"] = bd

    # Optional loudness
    if getattr(args, "loudness", False):
        loud = _loudness_ebur128(in_path)
        result.setdefault("analysis", {})["loudness"] = loud

    # Write JSON
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"🗂  Wrote metadata → {out_json}")
