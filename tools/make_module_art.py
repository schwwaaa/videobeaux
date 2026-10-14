#!/usr/bin/env python3
"""
Build the "Output art" look's thumbnails from what every module *actually produces*.

    python tools/make_module_art.py                    # all programs
    python tools/make_module_art.py --only feedback_loop,ascii_art
    python tools/make_module_art.py --ffmpeg-dir /path/with/ffmpeg --jobs 4 --keep

How it works (everything offline, nothing downloaded):
  1. Generates one procedural, colourful source clip with ffmpeg (gradients + moving shapes + the word VIDEOBEAUX).
  2. Runs every program on it through the smoke-test runner (tests/smoke/run_smoke.py) with its normal test arguments.
  3. For each result, picks the most visually interesting frame (edge energy + colour variance, never a blank one),
     crops it to 16:9, resizes to 192x108 and writes <program>.webp.
  4. Writes manifest.json. Programs that can't run here (faces, speech, network) simply get no image and fall back to
     their family pattern in the app.

Use your own footage instead of the generated clip:
    python tools/make_module_art.py --source my_clip.mp4 [--start 5 --duration 4]
or drop a video into ui_design/art_source/ — it is picked up automatically. A clip with faces and speech also gives
the face / speech modules a picture. (Shorter clips are looped so every module has something to work with.)

Output: gui/src/renderer/src/looks/output-art/art/   (or --out DIR; the app uses the user-data folder so packaged
installs can regenerate too)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO / "gui/src/renderer/src/looks/output-art/art"
DROP_DIR = REPO / "ui_design" / "art_source"
FONT = REPO / "videobeaux/assets/fonts/DejaVuSans-Bold.ttf"
THUMB = (192, 108)
VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv", ".avi", ".gif", ".m4v"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def make_source(path: Path) -> None:
    """A deliberately art-directed clip: soft gradient sky, bright moving blocks, a grid and a title — gives edge,
    colour, motion and text for the effects to chew on."""
    graph = (
        "[1:v]format=yuv420p[a];[2:v]format=yuv420p[b];[3:v]format=yuv420p[c];"
        "[0:v][a]overlay=x='W/2-300+260*sin(t*1.7)':y='40+60*cos(t*1.3)'[v1];"
        "[v1][b]overlay=x='W/2+40+200*cos(t*1.1)':y='H-190+50*sin(t*2.1)'[v2];"
        "[v2][c]overlay=x='60+140*sin(t*0.9+1)':y='H/2-40+70*cos(t*1.9)'[v3];"
        "[v3]drawgrid=w=80:h=80:t=2:c=white@0.28,"
        f"drawtext=fontfile={FONT}:text='VIDEOBEAUX':fontsize=70:fontcolor=white:borderw=5:bordercolor=black:"
        "x=(w-text_w)/2+50*sin(t*1.5):y=(h-text_h)/2+24*cos(t*2.3)[v]"
    )
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-f", "lavfi", "-i", "gradients=s=640x360:c0=0xff4fa3:c1=0x32b9df:c2=0xffe500:c3=0x8654aa:nb_colors=4:speed=0.05:d=16:r=24",
           "-f", "lavfi", "-i", "color=c=0xffe500:s=150x150:d=16:r=24",
           "-f", "lavfi", "-i", "color=c=0x080808:s=110x110:d=16:r=24",
           "-f", "lavfi", "-i", "color=c=0xff6847:s=170x90:d=16:r=24",
           "-f", "lavfi", "-i", "sine=f=330:d=16",
           "-filter_complex", graph, "-map", "[v]", "-map", "4:a", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-shortest", str(path)]
    subprocess.run(cmd, check=True)


def find_dropped_clip() -> Path | None:
    if DROP_DIR.is_dir():
        for p in sorted(DROP_DIR.iterdir()):
            if p.suffix.lower() in VIDEO_EXTS and not p.name.startswith("."):
                return p
    return None


def prepare_source(src: Path, tmp: Path, start: float, dur: float) -> tuple[Path, float, float]:
    """The smoke fixtures need start + dur + 8 s of footage; loop a short clip so any clip works."""
    need = start + dur + 8.0
    have = duration(src)
    if have <= 0:
        sys.exit(f"❌ could not read {src}")
    if have >= need:
        return src, start, dur
    looped = tmp / "looped_source.mp4"
    n = int(need // have) + 1
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-stream_loop", str(n), "-i", str(src), "-t", f"{need + 1:.1f}",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                        str(looped)], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"❌ could not loop the short clip:\n{r.stderr[-400:]}")
    print(f"ℹ️  clip is {have:.1f}s — looped to {need:.0f}s so every module gets footage")
    return looped, start, dur


def duration(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def grab(path: Path, t: float, dest: Path) -> bool:
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(path), "-frames:v", "1", str(dest)],
                       capture_output=True)
    return r.returncode == 0 and dest.exists()


def score(img: Image.Image) -> float:
    """Higher = more interesting. Blank / near-black frames score ~0."""
    a = np.asarray(img.convert("RGB").resize((96, 54)), dtype=np.float32) / 255.0
    lum = a.mean(axis=2)
    if lum.mean() < 0.03 or lum.std() < 0.025:
        return 0.0
    gx, gy = np.abs(np.diff(lum, axis=1)).mean(), np.abs(np.diff(lum, axis=0)).mean()
    chroma = (a.max(axis=2) - a.min(axis=2)).mean()
    return float(gx + gy + 0.5 * chroma + 0.5 * lum.std())


def to_thumb(img: Image.Image) -> Image.Image:
    img = img.convert("RGB")
    w, h = img.size
    target = THUMB[0] / THUMB[1]
    if w / h > target:                       # too wide → centre crop
        nw = int(h * target)
        img = img.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:                                    # too tall → centre crop
        nh = int(w / target)
        img = img.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    return img.resize(THUMB, Image.LANCZOS)


def best_frame(result: Path, tmp: Path):
    ext = result.suffix.lower()
    if ext in IMAGE_EXTS:
        try:
            return Image.open(result)
        except Exception:
            return None
    if ext not in VIDEO_EXTS:
        return None
    dur = duration(result) or 2.0
    best, best_s = None, 0.0
    for i, f in enumerate((0.2, 0.4, 0.6, 0.8)):
        p = tmp / f"cand{i}.png"
        if grab(result, max(0.0, dur * f - 0.05), p):
            try:
                im = Image.open(p)
                im.load()
            except Exception:
                continue
            s = score(im)
            if s > best_s:
                best, best_s = im.copy(), s
    return best if best_s > 0 else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="comma-separated program ids")
    ap.add_argument("--ffmpeg-dir", help="directory containing ffmpeg + ffprobe (default: gui/resources/ffmpeg, else PATH)")
    ap.add_argument("--source", help="your own video to run every module on (default: ui_design/art_source/*, else a generated clip)")
    ap.add_argument("--start", type=float, default=0.5, help="where in the clip to start (seconds)")
    ap.add_argument("--duration", type=float, default=4.0, help="how many seconds of it to use")
    ap.add_argument("--out", help="output directory for the thumbnails (default: the look's art folder)")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=240)
    ap.add_argument("--keep", action="store_true", help="keep the temporary working directory")
    args = ap.parse_args()

    ffdir = args.ffmpeg_dir or (str(REPO / "gui/resources/ffmpeg") if (REPO / "gui/resources/ffmpeg/ffmpeg").exists() else None)
    if ffdir:
        os.environ["PATH"] = ffdir + os.pathsep + os.environ["PATH"]
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            sys.exit(f"❌ {tool} not found")

    out_dir = Path(args.out).expanduser() if args.out else DEFAULT_OUT
    tmp = Path(tempfile.mkdtemp(prefix="vb_art_"))
    start, dur = args.start, args.duration
    user_src = Path(args.source).expanduser() if args.source else find_dropped_clip()
    if user_src:
        if not user_src.exists():
            sys.exit(f"❌ source clip not found: {user_src}")
        print(f"🎞️  using your clip: {user_src.name}")
        src, start, dur = prepare_source(user_src, tmp, start, dur)
        source_label = f"user clip: {user_src.name}"
    else:
        src = tmp / "art_source.mp4"
        print("🎨 generating the source clip…")
        make_source(src)
        source_label = "procedural clip (tools/make_module_art.py)"

    smoke = [sys.executable, str(REPO / "tests/smoke/run_smoke.py"), "--system-ffmpeg", "--source", str(src),
             "--start", str(start), "--duration", str(dur), "--keep", "--jobs", str(args.jobs), "--timeout", str(args.timeout),
             "--report-dir", str(tmp / "reports")]
    if args.only:
        smoke += ["--only", args.only]
    print("🏃 running every module on it (this takes a few minutes)…", flush=True)
    proc = subprocess.Popen(smoke, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
                            env={**os.environ, "PYTHONUNBUFFERED": "1"})
    captured = []
    for line in proc.stdout:                       # stream "[n/157] ✅ name" lines so a UI can show progress
        captured.append(line)
        if re.match(r"\s*\[\s*\d+/\d+\]", line):
            print(line.rstrip(), flush=True)
    proc.wait()
    text = "".join(captured)
    m = re.search(r"Outputs kept in: (.+)", text)
    if not m:
        print(text[-1500:])
        sys.exit("❌ the smoke runner did not produce outputs")
    work = Path(m.group(1).strip()) / "out"

    OUT_DIR = out_dir
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not args.only:                              # full regeneration: drop thumbnails of modules that no longer produce one
        for old in OUT_DIR.glob("*.webp"):
            old.unlink()
    manifest_path = OUT_DIR / "manifest.json" if args.out else OUT_DIR.parent / "manifest.json"
    manifest = {"programs": {}}
    if args.only and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
    done, skipped = [], []
    for pdir in sorted(d for d in work.iterdir() if d.is_dir()):
        prog = pdir.name
        results = sorted(pdir.glob("result*"))
        img = best_frame(results[0], tmp) if results else None
        if img is None:
            skipped.append(prog)
            manifest["programs"].pop(prog, None)
            continue
        out = OUT_DIR / f"{prog}.webp"
        to_thumb(img).save(out, "WEBP", quality=72, method=6)
        manifest["programs"][prog] = {"file": f"{prog}.webp", "w": THUMB[0], "h": THUMB[1]}
        done.append(prog)

    manifest["generated"] = dt.datetime.now().isoformat(timespec="seconds")
    manifest["source"] = source_label
    manifest["ffmpeg"] = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout.splitlines()[0]
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    total_kb = sum(f.stat().st_size for f in OUT_DIR.glob("*.webp")) / 1024
    print(f"✅ {len(done)} thumbnails written ({total_kb:.0f} KB total) → {OUT_DIR}", flush=True)
    if skipped:
        print(f"⏭️  no image for {len(skipped)}: {', '.join(skipped)}")
    if not args.keep:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(work.parent, ignore_errors=True)
    else:
        print(f"📂 kept {tmp} and {work.parent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
