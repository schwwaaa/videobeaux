#!/usr/bin/env python3
"""
Smoke-test every videobeaux program against a short clip and report what works.

Each program is run through the same CLI entry point the GUI uses
(`python -m videobeaux.cli -P <program> -i <clip> -o <out> -F ...`) with
sensible arguments, then its output is validated (exists, non-empty, and for
media outputs, decodes via ffprobe). Results are grouped by GUI category and
written to a markdown + JSON report.

    python tests/smoke/run_smoke.py                       # everything
    python tests/smoke/run_smoke.py --only pixel_sort,thumbs
    python tests/smoke/run_smoke.py --category glitch
    python tests/smoke/run_smoke.py --jobs 4              # parallel
    python tests/smoke/run_smoke.py --full-res            # don't downscale clip

Exit code is 1 if any program FAILs or TIMEOUTs (SKIPs don't count).
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures as cf
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO))
from videobeaux.utils.kokoro import kokoro_command  # noqa: E402
DEFAULT_SOURCE = REPO / "gui" / "Wil_Willis-OnTheJob_edit_0001.mp4"
PROGRAMS_JS = REPO / "gui" / "src" / "renderer" / "src" / "programs.js"
MEDIA = REPO / "media"

PASS, FAIL, SKIP, TIMEOUT = "PASS", "FAIL", "SKIP", "TIMEOUT"


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def find_full_ffmpeg_dir() -> str | None:
    """A full-featured ffmpeg (zscale/libass/drawtext): the app's own .tools build, else Homebrew's keg-only ffmpeg-full."""
    for d in (str(REPO / ".tools" / "ffmpeg"),      # the app's own downloaded build, if present
              "/opt/homebrew/opt/ffmpeg-full/bin", "/usr/local/opt/ffmpeg-full/bin"):
        if (Path(d) / "ffmpeg").exists():
            return d
    return None


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def ffprobe_json(path: Path) -> dict | None:
    r = sh(["ffprobe", "-v", "error", "-print_format", "json",
            "-show_format", "-show_streams", str(path)])
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def ffmpeg_filters() -> set[str]:
    out = sh(["ffmpeg", "-hide_banner", "-filters"]).stdout
    names = set()
    for ln in out.splitlines():
        parts = ln.split()
        if len(parts) > 2 and len(parts[0]) <= 4:
            names.add(parts[1])
    return names


def load_categories() -> dict[str, tuple[str, str]]:
    """program id -> (category id, category label), parsed from programs.js via node."""
    if not shutil.which("node") or not PROGRAMS_JS.exists():
        return {}
    tmp = Path(tempfile.mkdtemp()) / "programs.mjs"
    shutil.copy(PROGRAMS_JS, tmp)
    js = (f"import('{tmp.as_posix()}').then(m=>{{const o={{}};"
          "for(const c of m.CATEGORIES)for(const p of c.programs)o[p.id]=[c.id,c.label];"
          "console.log(JSON.stringify(o))})")
    r = sh(["node", "-e", js])
    shutil.rmtree(tmp.parent, ignore_errors=True)
    try:
        return {k: tuple(v) for k, v in json.loads(r.stdout).items()}
    except Exception:
        return {}


def discover_programs() -> dict:
    r = sh([sys.executable, str(REPO / "gui" / "discover_programs.py")], cwd=REPO,
           env={**os.environ, "PYTHONUTF8": "1"})
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {}


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class Fixtures:
    root: Path
    clip: Path
    clip2: Path
    clip3: Path
    folder: Path            # two clips, for mince
    image: Path
    lut: Path
    srt: Path
    layout: Path
    chain_config: Path
    vosk: Path | None
    transcript: Path | None = None
    speech_query: str | None = None
    filters: set = field(default_factory=set)
    has_cv2: bool = False
    hdr_clip: Path | None = None
    synthetic: bool = False


def cut(source: Path, dest: Path, start: float, dur: float, full_res: bool):
    vf = [] if full_res else ["-vf", "scale=640:-2"]
    r = sh(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-ss", str(start), "-t", str(dur), "-i", str(source), *vf,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-c:a", "aac", str(dest)])
    if r.returncode != 0 or not dest.exists():
        sys.exit(f"❌ Could not cut test clip from {source}:\n{r.stderr}")


def build_fixtures(root: Path, source: Path, start: float, dur: float, full_res: bool) -> Fixtures:
    root.mkdir(parents=True, exist_ok=True)
    clip, clip2, clip3 = root / "clip.mp4", root / "clip2.mp4", root / "clip3.mp4"
    cut(source, clip, start, dur, full_res)
    cut(source, clip2, start + dur, min(dur, 4), full_res)
    cut(source, clip3, start + dur + 4, min(dur, 4), full_res)

    folder = root / "folder"
    folder.mkdir(exist_ok=True)
    shutil.copy(clip2, folder / "a.mp4")
    shutil.copy(clip3, folder / "b.mp4")

    image = MEDIA / "logo.png"
    gif = MEDIA / "bunny.gif"

    # Identity 3D LUT (size 2) so lut_apply has a valid .cube to load.
    lut = root / "identity.cube"
    lines = ["LUT_3D_SIZE 2"]
    for b in (0, 1):
        for g in (0, 1):
            for r in (0, 1):
                lines.append(f"{r:.1f} {g:.1f} {b:.1f}")
    lut.write_text("\n".join(lines) + "\n")

    srt = root / "sample.srt"
    srt.write_text("1\n00:00:00,500 --> 00:00:02,000\nHello from the smoke test\n\n"
                   "2\n00:00:02,500 --> 00:00:04,000\nSecond subtitle line\n")

    layout = root / "layout.json"
    layout.write_text(json.dumps({
        "sequence_direction": "forward",
        "layers": [
            {"layer_number": 1, "name": "logo", "filename": str(image), "type": "img",
             "mode": "place", "place": "top_right", "size": 20, "opacity": 0.85,
             "blend_mode": "normal"},
            {"layer_number": 2, "name": "sticker", "filename": str(gif), "type": "gif",
             "mode": "place", "place": "bottom_left", "size": 15, "opacity": 0.6,
             "blend_mode": "normal"},
        ],
    }, indent=2))

    chain_config = root / "chain.json"
    chain_config.write_text(json.dumps([
        {"program": "reverse", "args": {}},
        {"program": "boomerang", "args": {}},
    ]))

    vosk = None
    models = REPO / "models"
    for name in ("vosk-model-en-us-0.22-lgraph", "vosk-model-en-us-0.22",
                 "vosk-model-en-us-0.42-gigaspeech"):
        if (models / name / "conf" / "model.conf").exists():
            vosk = models / name
            break

    filters = ffmpeg_filters()
    hdr = None
    if "zscale" in filters:
        # Synthetic PQ / BT.2020 clip so tonemap_hdr_sdr gets a real HDR input.
        hdr = root / "hdr.mp4"
        r = sh(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(clip),
                "-vf", "zscale=rin=tv:pin=bt709:tin=bt709:min=bt709,zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt2020,"
                       "zscale=t=smpte2084:m=bt2020nc:r=tv,format=yuv420p10le",
                "-c:v", "libx265", "-preset", "ultrafast", "-crf", "22", "-x265-params", "log-level=error",
                "-tag:v", "hvc1", "-color_primaries", "bt2020", "-color_trc", "smpte2084",
                "-colorspace", "bt2020nc", "-c:a", "aac", str(hdr)])
        if r.returncode != 0 or not hdr.exists():
            hdr = None
    import importlib.util
    return Fixtures(root, clip, clip2, clip3, folder, image, lut, srt, layout,
                    chain_config, vosk, filters=filters, hdr_clip=hdr,
                    has_cv2=importlib.util.find_spec('cv2') is not None)


# ──────────────────────────────────────────────────────────────────────────────
# Per-program specs
# ──────────────────────────────────────────────────────────────────────────────
#
# Programs not listed here run with just -i/-o and their defaults. Each spec:
#   args(fx)   -> extra CLI args
#   kind       -> output validation: video | json | image | audio | text | dir
#   ext        -> output extension (default by kind)
#   input(fx)  -> override -i path
#   skip(fx)   -> reason string to skip, or None
#   timeout    -> seconds (default --timeout)
#   expect     -> regex that must appear in the program's stdout (e.g. detection summaries)

def need_vosk(fx):
    return None if fx.vosk else "no Vosk model found under models/"


def need_filter(fx, name, lib):
    if name in fx.filters:
        return None
    return f"ffmpeg lacks the '{name}' filter ({lib}) — environment, not a code bug"


def need_cv2(fx):
    return None if fx.has_cv2 else "OpenCV (cv2) not installed — pip install opencv-python-headless"


def need_face(fx):
    if fx.synthetic:
        return "the built-in synthetic clip has no faces — pass --source with a clip of a person"
    return need_cv2(fx)


def need_transcript(fx):
    return None if fx.transcript else "needs a transcript (transcraibe must pass first)"


def need_speech(fx):
    if fx.synthetic:
        return "the built-in synthetic clip has no speech — pass --source with a clip of someone talking"
    if not fx.vosk:
        return "no Vosk model found under models/"
    if not fx.speech_query:
        return "no speech detected in the test clip (transcraibe produced no words)"
    return None


SPECS: dict[str, dict] = {
    # inputs that need a second/third clip
    "concat":           {"args": lambda fx: ["--input2", str(fx.clip2)]},
    "stack_2x":         {"args": lambda fx: ["--input2", str(fx.clip2)]},
    "wipe_transitions": {"args": lambda fx: ["--input2", str(fx.clip2)]},
    "insert_clip":      {"args": lambda fx: ["--input2", str(fx.clip2), "--insert_at", "2"]},
    "triptych":         {"args": lambda fx: ["--input2", str(fx.clip2), "--input3", str(fx.clip3)]},
    "crossmosh":        {"args": lambda fx: ["--b-input", str(fx.clip2)]},
    "watermark":        {"args": lambda fx: ["--watermark", str(fx.image)]},
    "lagkage":          {"args": lambda fx: ["--layout-json", str(fx.layout)]},
    "mince":            {"args": lambda fx: ["--mode", "forward", "--normalize"],
                         "input": lambda fx: fx.folder},

    # required numeric/text args
    "convert_dims":     {"args": lambda fx: ["--output-format", "mp4", "--preset", "480p"]},
    "convert":          {"args": lambda fx: ["--output-format", "mp4"]},
    "resize":           {"args": lambda fx: ["--new_height", "180", "--new_width", "320"]},
    "speed":            {"args": lambda fx: ["--speed_factor", "1.5"]},
    "trim":             {"args": lambda fx: ["--start", "1", "--duration", "2"]},
    "frame_delay_pro1": {"args": lambda fx: ["--frame_quantity", "3", "--frame_weights", "0.5"]},
    "frame_delay_pro2": {"args": lambda fx: ["--decay", "0.8", "--planes", "7"]},
    "looper_pro":       {"args": lambda fx: ["--size_in_frames", "12", "--loop_count", "2",
                                             "--start_frame", "10"]},
    "lsd_feedback_pro": {"args": lambda fx: ["--frames", "8"]},
    "rb_blur_pro":      {"args": lambda fx: ["--strength", "1.0", "--radius", "8"]},
    "recalled_sensor_pro": {"args": lambda fx: ["--radius", "4", "--factor", "2"]},
    "scrolling_pro":    {"args": lambda fx: ["--horiz_speed", "0.01", "--vert_speed", "0"]},
    "splitting_pro":    {"args": lambda fx: ["--width", "20", "--position", "vertical"]},
    "stutter_pro":      {"args": lambda fx: ["--stutter", "5"]},
    "twociz_pro":       {"args": lambda fx: ["--radius", "4", "--factor", "2",
                                             "--blend", "0.1", "--similarity", "0.2"]},
    "wbflare_pro":      {"args": lambda fx: ["--sigma", "5"]},
    "lut_apply":        {"args": lambda fx: ["--lut", str(fx.lut), "--intensity", "0.7"]},
    "frame_interpolate": {"args": lambda fx: ["--multiplier", "2"], "timeout": 600},
    "photobooth":       {"args": lambda fx: ["--filter", "Retro TV · VHS"]},
    "layer_blend":      {"args": lambda fx: ["--input2", str(fx.clip2), "--mode", "difference", "--audio", "Mix A + B"]},
    "ascii_art":        {"args": lambda fx: ["--columns", "80", "--color_mode", "matrix green"]},
    "chroma_key":       {"args": lambda fx: ["--auto_key", "--bg_video", str(fx.clip2)]},
    "luma_key":         {"args": lambda fx: ["--key", "dark", "--tolerance", "0.3", "--bg_color", "#2244ff"]},
    "chain_builder":    {"args": lambda fx: ["--chain", "reverse,boomerang"]},
    "chain_builder_pro": {"args": lambda fx: ["--chain_config", str(fx.chain_config)]},

    # non-video outputs
    "media_info":       {"kind": "json", "ext": ".json"},
    "meta_extraction":  {"kind": "json", "ext": ".json"},
    "hash_fingerprint": {"kind": "json", "ext": ".json",
                         "args": lambda fx: ["--file-hashes", "md5"]},
    "extract_sound":    {"kind": "audio", "ext": ".wav"},
    "thumbs":           {"kind": "image", "ext": ".png",
                         "args": lambda fx: ["--fps", "1", "--tile", "3x2"]},
    "extract_frames":   {"kind": "dir", "args": lambda fx: ["--frame_rate", "1"]},
    "qwikchop":         {"kind": "dir", "args": lambda fx: ["--pieces", "3"]},
    "subs_convert":     {"kind": "text", "ext": ".vtt",
                         "input": lambda fx: fx.srt,
                         "args": lambda fx: ["--format", "vtt"]},

    # dithering (the first two are pure ffmpeg; ordered_dither is numpy)
    "dither":           {"args": lambda fx: ["--colors", "8", "--pixel_size", "2"]},
    "retro_dither":     {"args": lambda fx: ["--palette", "gameboy"]},
    "ordered_dither":   {"args": lambda fx: ["--method", "bayer8", "--palette", "pico8"]},

    # OpenCV programs — skipped (not failed) if cv2 isn't installed
    "face_track":       {"skip": need_face, "expect": r"Faces detected in [1-9]\d*/",
                         "args": lambda fx: ["--style", "corners", "--show_id", "--trail"]},
    "face_redact":      {"skip": need_face, "expect": r"Faces detected in [1-9]\d*/",
                         "args": lambda fx: ["--effect", "pixelate"]},
    "face_follow":      {"skip": need_face, "expect": r"Faces detected in [1-9]\d*/"},
    "neon_edges":       {"skip": need_cv2},
    "cartoon":          {"skip": need_cv2},
    "sketch":           {"skip": need_cv2, "args": lambda fx: ["--mode", "pencil"]},
    "kmeans_palette":   {"skip": need_cv2, "args": lambda fx: ["--colors", "5", "--dither", "bayer8"]},
    "warp":             {"skip": need_cv2, "args": lambda fx: ["--mode", "swirl", "--speed", "2"]},
    "flow_warp":        {"skip": need_cv2},
    "motion_ghost":     {"skip": need_cv2, "args": lambda fx: ["--mode", "trails"]},
    "feature_trails":   {"skip": need_cv2},
    "stabilize":        {"skip": need_cv2},

    # environment-dependent
    "tonemap_hdr_sdr":  {"skip": lambda fx: need_filter(fx, "zscale", "libzimg") or
                         (None if fx.hdr_clip else "could not build the synthetic HDR clip"),
                         "input": lambda fx: fx.hdr_clip},
    "download_yt":      {"skip": lambda fx: "needs network + a real YouTube URL as -i"},

    # speech / model-dependent (Vosk). transcraibe also produces the transcript
    # fixture the caption programs and query-based programs reuse.
    "transcraibe":      {"kind": "json", "ext": ".json", "skip": need_vosk, "timeout": 600,
                         "args": lambda fx: ["--stt_model", str(fx.vosk)]},
    "ngrams":           {"kind": "json", "ext": ".json", "skip": need_speech, "timeout": 600,
                         "args": lambda fx: ["--stt_model", str(fx.vosk)]},
    "grep_supercut":    {"skip": need_speech, "timeout": 600,
                         "args": lambda fx: ["--stt_model", str(fx.vosk),
                                             "--query", fx.speech_query or "the"]},
    "silence_xtraction": {"skip": need_speech, "timeout": 600,
                          "args": lambda fx: ["--stt_model", str(fx.vosk), "--min_d", "0.05",
                                              "--max_d", "3", "--adjuster", "0.02"]},
    "word_xtraction_vad": {"skip": need_speech, "timeout": 600,
                           "args": lambda fx: ["--stt_model", str(fx.vosk), "--min_d", "0.05",
                                               "--max_d", "3", "--adjuster", "0.02"]},
    "qwikchop_deluxe":  {"kind": "dir", "skip": need_speech, "timeout": 900,
                         "args": lambda fx: ["--stt_model", str(fx.vosk), "--count", "2",
                                             "--min_time", "1", "--max_time", "4"]},
    "captburn":         {"skip": lambda fx: need_filter(fx, "ass", "libass") or need_transcript(fx),
                         "args": lambda fx: ["--trans-json", str(fx.transcript)]},
    "kinetic_captions": {"skip": need_transcript,
                         "args": lambda fx: ["--trans-json", str(fx.transcript)], "timeout": 600},
    "auto_narrate":     {"skip": lambda fx: (need_vosk(fx) or
                                             (None if kokoro_command() else "kokoro-tts not installed")),
                         "args": lambda fx: ["--script", "This is a short smoke test narration.",
                                             "--stt_model", str(fx.vosk)],
                         "timeout": 900},
}

# Programs that must run before others (they produce fixtures).
FIXTURE_PRODUCERS = ["transcraibe"]

KIND_EXT = {"video": ".mp4", "json": ".json", "image": ".png", "audio": ".wav",
            "text": ".txt", "dir": ".mp4"}


# ──────────────────────────────────────────────────────────────────────────────
# Running + validating
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class Result:
    program: str
    category: str = "uncategorized"
    category_label: str = "Uncategorized"
    status: str = PASS
    seconds: float = 0.0
    detail: str = ""
    error: str = ""
    cmd: str = ""


def tail(text: str, n: int = 6) -> str:
    lines = [ln for ln in (text or "").splitlines() if ln.strip()]
    return "\n".join(lines[-n:])


def extract_error(proc_out: str, proc_err: str) -> str:
    """Prefer the last traceback line / ❌ line; fall back to the stderr tail."""
    for blob in (proc_err, proc_out):
        for ln in reversed((blob or "").splitlines()):
            s = ln.strip()
            if s.startswith("❌") or re.match(r"^[A-Za-z_.]*(Error|Exception|SystemExit)\b", s):
                return s
    return tail(proc_err or proc_out, 4)


def validate(kind: str, out: Path) -> tuple[bool, str]:
    if kind == "dir":
        d = out.with_suffix("")
        if not d.is_dir():
            return False, f"expected output directory {d.name}/ was not created"
        files = [p for p in d.iterdir() if p.is_file()]
        if not files:
            return False, f"output directory {d.name}/ is empty"
        return True, f"{len(files)} file(s) in {d.name}/"

    # program may legitimately change the suffix (e.g. subs_convert → format)
    if not out.exists():
        siblings = sorted(out.parent.glob(out.stem + ".*"))
        if siblings:
            return False, f"output written to {siblings[0].name}, not the requested {out.name}"
        return False, f"output file {out.name} was not created"
    if out.stat().st_size == 0:
        return False, "output file is empty"

    if kind == "video":
        info = ffprobe_json(out)
        if not info:
            return False, "output is not a decodable media file"
        vids = [s for s in info["streams"] if s["codec_type"] == "video"]
        if not vids:
            return False, "output has no video stream"
        dur = float(info["format"].get("duration") or 0)
        if dur < 0.1:
            return False, f"output duration is {dur:.2f}s"
        return True, f"{vids[0]['width']}x{vids[0]['height']}, {dur:.1f}s"
    if kind == "audio":
        info = ffprobe_json(out)
        if not info or not any(s["codec_type"] == "audio" for s in info["streams"]):
            return False, "output has no audio stream"
        return True, f"{float(info['format'].get('duration') or 0):.1f}s audio"
    if kind == "image":
        info = ffprobe_json(out)
        if not info or not any(s["codec_type"] == "video" for s in info["streams"]):
            return False, "output is not a decodable image"
        s = next(s for s in info["streams"] if s["codec_type"] == "video")
        return True, f"{s['width']}x{s['height']} image"
    if kind == "json":
        try:
            json.loads(out.read_text(encoding="utf-8"))
        except Exception as e:
            return False, f"output is not valid JSON ({e})"
        return True, f"{out.stat().st_size} bytes JSON"
    return True, f"{out.stat().st_size} bytes"


def run_one(prog: str, fx: Fixtures, meta: dict, cats: dict, work: Path,
            default_timeout: int) -> Result:
    cid, clabel = cats.get(prog, ("uncategorized", "Uncategorized"))
    res = Result(prog, cid, clabel)
    spec = SPECS.get(prog, {})

    skip = spec["skip"](fx) if "skip" in spec else None
    if skip:
        res.status, res.detail = SKIP, skip
        return res

    kind = spec.get("kind") or meta.get("outputType") or "video"
    if kind not in KIND_EXT:
        kind = "video"
    ext = spec.get("ext", KIND_EXT[kind])
    in_path = spec["input"](fx) if "input" in spec else fx.clip
    extra = spec["args"](fx) if "args" in spec else []

    pdir = work / prog
    pdir.mkdir(parents=True, exist_ok=True)
    out = pdir / f"result{ext}"

    cmd = [sys.executable, "-m", "videobeaux.cli", "-P", prog,
           "-i", str(in_path), "-o", str(out), "-F", *extra]
    res.cmd = " ".join(cmd[1:])

    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True,
                           timeout=spec.get("timeout", default_timeout),
                           env={**os.environ, "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1",
                                "VIDEOBEAUX_MODELS_DIR": str(REPO / "models")})
    except subprocess.TimeoutExpired:
        res.status, res.seconds = TIMEOUT, time.time() - t0
        res.error = f"timed out after {spec.get('timeout', default_timeout)}s"
        return res
    res.seconds = time.time() - t0

    crashed = "Program crashed with an unhandled exception" in (p.stdout + p.stderr)
    if p.returncode != 0 or crashed:
        res.status = FAIL
        res.error = extract_error(p.stdout, p.stderr)
        return res

    if "expect" in spec and not re.search(spec["expect"], p.stdout):
        res.status = FAIL
        res.error = f"expected output matching /{spec['expect']}/ but got: {tail(p.stdout, 2)}"
        return res

    ok, detail = validate(kind, out)
    res.status = PASS if ok else FAIL
    res.detail = detail if ok else ""
    res.error = "" if ok else detail

    # transcraibe doubles as the transcript fixture for caption/query programs
    if prog == "transcraibe" and ok and kind == "json":
        fx.transcript = out
        fx.speech_query = pick_query_word(out)
    return res


def pick_query_word(path: Path) -> str | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    words = []

    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get("word"), str):
                words.append(o["word"].lower())
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(data)
    words = [w for w in words if len(w) >= 3 and w.isalpha()]
    if not words:
        return None
    return collections.Counter(words).most_common(1)[0][0]


# ──────────────────────────────────────────────────────────────────────────────
# Reporting
# ──────────────────────────────────────────────────────────────────────────────

ICON = {PASS: "✅", FAIL: "❌", SKIP: "⏭️", TIMEOUT: "⏱️"}


def write_reports(results: list[Result], outdir: Path, meta: dict) -> tuple[Path, Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    counts = collections.Counter(r.status for r in results)

    by_cat: dict[tuple[str, str], list[Result]] = collections.defaultdict(list)
    for r in results:
        by_cat[(r.category, r.category_label)].append(r)

    md = [f"# videobeaux smoke test — {dt.datetime.now():%Y-%m-%d %H:%M}", "",
          f"- Source: `{meta['source']}` (section {meta['start']}s + {meta['dur']}s"
          f"{'' if meta['full_res'] else ', downscaled to 640px wide'})",
          f"- ffmpeg: {meta['ffmpeg']}", "",
          f"**{counts[PASS]} passed · {counts[FAIL]} failed · {counts[TIMEOUT]} timed out · "
          f"{counts[SKIP]} skipped** (of {len(results)})", ""]

    bad = [r for r in results if r.status in (FAIL, TIMEOUT)]
    if bad:
        md += ["## Needs attention", ""]
        for r in sorted(bad, key=lambda r: (r.category, r.program)):
            md.append(f"- {ICON[r.status]} **{r.program}** ({r.category_label}) — {r.error or r.status}")
        md.append("")

    for (cid, label), rs in sorted(by_cat.items(), key=lambda kv: kv[0][1]):
        p = sum(r.status == PASS for r in rs)
        md += [f"## {label} — {p}/{len(rs)} passing", "",
               "| | program | time | result |", "|---|---|---|---|"]
        for r in sorted(rs, key=lambda r: r.program):
            note = (r.error or r.detail).replace("\n", " ").replace("|", "\\|")
            md.append(f"| {ICON[r.status]} | `{r.program}` | {r.seconds:.1f}s | {note} |")
        md.append("")

    md_path = outdir / f"smoke-{stamp}.md"
    md_path.write_text("\n".join(md), encoding="utf-8")
    (outdir / "latest.md").write_text("\n".join(md), encoding="utf-8")
    json_path = outdir / f"smoke-{stamp}.json"
    json_path.write_text(json.dumps(
        {"meta": meta, "counts": counts, "results": [r.__dict__ for r in results]},
        indent=2), encoding="utf-8")
    (outdir / "latest.json").write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    return md_path, json_path


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", default=None,
                    help="Source video to cut the test section from. Default: gui/Wil_Willis-OnTheJob_edit_0001.mp4 "
                         "if present, else a generated synthetic clip (no faces/speech, so those programs skip).")
    ap.add_argument("--start", type=float, default=6.0, help="Section start (s). Default 6.")
    ap.add_argument("--duration", type=float, default=8.0, help="Section length (s). Default 8.")
    ap.add_argument("--full-res", action="store_true", help="Keep the source resolution (slower).")
    ap.add_argument("--only", help="Comma-separated program ids to run.")
    ap.add_argument("--category", help="Only programs in this GUI category id (e.g. glitch, utility).")
    ap.add_argument("--jobs", type=int, default=1, help="Programs to run in parallel. Default 1.")
    ap.add_argument("--timeout", type=int, default=240, help="Default per-program timeout (s).")
    ap.add_argument("--report-dir", default=str(HERE / "reports"))
    ap.add_argument("--keep", action="store_true", help="Keep the working directory with all outputs.")
    ap.add_argument("--system-ffmpeg", action="store_true",
                    help="Use whatever ffmpeg is on PATH instead of preferring Homebrew's ffmpeg-full.")
    args = ap.parse_args()

    full = None if args.system_ffmpeg else find_full_ffmpeg_dir()
    if full:
        os.environ["PATH"] = full + os.pathsep + os.environ["PATH"]
        print(f"🎬 Using ffmpeg-full from {full}")

    synthetic = False
    if args.source:
        source = Path(args.source)
        if not source.exists():
            sys.exit(f"❌ Source video not found: {source}")
    elif DEFAULT_SOURCE.exists():
        source = DEFAULT_SOURCE
    else:
        synthetic = True
        source = Path(tempfile.mkdtemp(prefix="vb_smoke_src_")) / "synthetic.mp4"
        r = sh(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=24:duration=30",
                "-f", "lavfi", "-i", "sine=frequency=440:duration=30",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(source)])
        if r.returncode != 0:
            sys.exit(f"❌ Could not generate a synthetic test clip:\n{r.stderr}")
        print("ℹ️  No source clip found — using a generated synthetic one (face/speech programs will skip).")
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            sys.exit(f"❌ {tool} not found on PATH")

    print("🔎 Discovering programs…")
    discovered = discover_programs()
    if not discovered:
        sys.exit("❌ Program discovery failed — try: python gui/discover_programs.py")
    cats = load_categories()

    programs = sorted(discovered)
    if args.only:
        wanted = {p.strip() for p in args.only.split(",")}
        unknown = wanted - set(programs)
        if unknown:
            sys.exit(f"❌ Unknown program(s): {', '.join(sorted(unknown))}")
        programs = [p for p in programs if p in wanted]
    if args.category:
        programs = [p for p in programs if cats.get(p, ("",))[0] == args.category]
    if not programs:
        sys.exit("❌ No programs selected.")

    work = Path(tempfile.mkdtemp(prefix="vb_smoke_"))
    print(f"🎞️  Cutting {args.duration}s test section at {args.start}s from {source.name}…")
    fx = build_fixtures(work / "fixtures", source, args.start, args.duration, args.full_res)
    fx.synthetic = synthetic
    if not fx.vosk:
        print("⚠️  No Vosk model under models/ — speech-dependent programs will be skipped.")

    ordered = [p for p in FIXTURE_PRODUCERS if p in programs] + \
              [p for p in programs if p not in FIXTURE_PRODUCERS]
    # Fixture producers run first (serially) so dependents can see their output.
    first = ordered[:len([p for p in FIXTURE_PRODUCERS if p in programs])]
    rest = ordered[len(first):]

    results: list[Result] = []
    total = len(ordered)

    def report(r: Result):
        results.append(r)
        tag = f"[{len(results):>2}/{total}]"
        extra = (r.error or r.detail).splitlines()[0] if (r.error or r.detail) else ""
        print(f"{tag} {ICON[r.status]} {r.program:<22} {r.seconds:6.1f}s  {extra[:90]}", flush=True)

    for p in first:
        report(run_one(p, fx, discovered[p], cats, work / "out", args.timeout))

    if args.jobs > 1:
        with cf.ThreadPoolExecutor(max_workers=args.jobs) as ex:
            futs = [ex.submit(run_one, p, fx, discovered[p], cats, work / "out", args.timeout)
                    for p in rest]
            for f in cf.as_completed(futs):
                report(f.result())
    else:
        for p in rest:
            report(run_one(p, fx, discovered[p], cats, work / "out", args.timeout))

    unconfigured = [p for p in programs
                    if p not in SPECS and any(a.get("required") for a in discovered[p].get("args", []))]
    if unconfigured:
        print("\n⚠️  Programs with required args but no SPECS entry (add one in run_smoke.py): "
              + ", ".join(unconfigured))

    ver = sh(["ffmpeg", "-version"]).stdout.splitlines()[0]
    md_path, json_path = write_reports(results, Path(args.report_dir), {
        "source": str(source), "start": args.start, "dur": args.duration,
        "full_res": args.full_res, "ffmpeg": ver})

    counts = collections.Counter(r.status for r in results)
    print(f"\n{counts[PASS]} passed · {counts[FAIL]} failed · {counts[TIMEOUT]} timed out · "
          f"{counts[SKIP]} skipped")
    print(f"📄 Report: {md_path}")
    if args.keep:
        print(f"📂 Outputs kept in: {work}")
    else:
        shutil.rmtree(work, ignore_errors=True)
    sys.exit(1 if counts[FAIL] or counts[TIMEOUT] else 0)


if __name__ == "__main__":
    main()
