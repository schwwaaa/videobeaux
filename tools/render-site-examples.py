#!/usr/bin/env python3
"""
Render the website's example library.

Each example in tools/site_examples.json is a chain of real program modes run on one source clip, then encoded as a
small 8-second MP4 + a poster frame into site/previews/. The site reads site/previews/examples.json (written here), so
adding an example is: add an entry to tools/site_examples.json, run this, reload the page.

    python tools/render-site-examples.py                 # render anything that's missing, rewrite examples.json
    python tools/render-site-examples.py --only halftone # (re)render just these ids (comma-separated)
    python tools/render-site-examples.py --force         # re-render everything
    python tools/render-site-examples.py --jobs 3

Needs the project's Python environment and an ffmpeg on PATH (gui/resources/ffmpeg or ffmpeg-full).

The website lives in its own repo (schwwaaa/videobeaux-website). The clips are written straight into that clone's site/previews/
— default ../videobeaux-website, or set VB_SITE_DIR / pass --site DIR. Nothing to copy afterwards: review, commit and push there.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "tools" / "site_examples.json"
OUT = ROOT / "site" / "previews"          # replaced by main() with <website clone>/site/previews
ENC = ["-c:v", "libx264", "-crf", "25", "-maxrate", "1400k", "-bufsize", "2800k", "-preset", "slow", "-an", "-movflags", "+faststart", "-pix_fmt", "yuv420p"]


def sh(cmd, **kw):
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, **kw)


def encode(src: Path, dst: Path, seconds: int):
    r = sh(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-t", str(seconds),
            "-vf", "scale=640:480:flags=bicubic,fps=24", *ENC, str(dst)])
    if r.returncode:
        raise RuntimeError(r.stderr[-400:])


def poster(src: Path, dst: Path, at: float = 3.0):
    sh(["ffmpeg", "-y", "-v", "error", "-ss", str(at), "-i", str(src), "-frames:v", "1", "-q:v", "4", str(dst)])


def render(ex: dict, source: Path, seconds: int) -> str:
    mp4, jpg = OUT / f"{ex['id']}.mp4", OUT / f"{ex['id']}.jpg"
    with tempfile.TemporaryDirectory(prefix="vb_site_") as tmp:
        cur = source
        for i, st in enumerate(ex["steps"]):
            nxt = Path(tmp) / f"{i}.mp4"
            r = sh([sys.executable, "-m", "videobeaux.cli", "-P", st["program"], "-i", str(cur), "-o", str(nxt), "-F", *st.get("args", [])])
            if r.returncode or not nxt.exists():
                raise RuntimeError(f"{st['program']} failed: {(r.stdout + r.stderr)[-400:]}")
            cur = nxt
        encode(cur, mp4, seconds)
    poster(mp4, jpg, float(ex.get("poster", 3.0)))
    return ex["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="comma-separated example ids to (re)render")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--site", help="the videobeaux-website clone (default: $VB_SITE_DIR, else ../videobeaux-website)")
    a = ap.parse_args()
    global OUT
    site = Path(a.site or os.environ.get("VB_SITE_DIR") or ROOT.parent / "videobeaux-website").expanduser().resolve()
    if not (site / "index.html").exists():
        sys.exit(f"❌ {site} doesn't look like the website clone (no index.html). Pass --site DIR or set VB_SITE_DIR.")
    OUT = site / "site" / "previews"
    print(f"→ writing into {OUT}")

    spec = json.loads(SPEC.read_text())
    source = ROOT / spec["source"]
    seconds = int(spec.get("seconds", 8))
    OUT.mkdir(parents=True, exist_ok=True)
    only = {s.strip() for s in a.only.split(",")} if a.only else None

    if a.force or not (OUT / "original.mp4").exists() or (only and "original" in only):
        encode(source, OUT / "original.mp4", seconds)
        poster(OUT / "original.mp4", OUT / "original.jpg")
        print("✓ original")

    missing = {e["id"]: [r for r in e.get("requires", []) if not (ROOT / r).exists()] for e in spec["examples"]}
    for k, v in missing.items():
        if v:
            print(f"⏭  {k}: needs {', '.join(v)} (not found)")
    def have(e):
        return (OUT / f"{e['id']}.mp4").exists() and (OUT / f"{e['id']}.jpg").exists()

    todo = [e for e in spec["examples"]
            if not missing[e["id"]] and ((e["id"] in only) if only else (a.force or not have(e)))]
    print(f"{len(todo)} to render ({len(spec['examples'])} in the library)")
    failed = []
    with cf.ThreadPoolExecutor(max_workers=a.jobs) as ex:
        futs = {ex.submit(render, e, source, seconds): e["id"] for e in todo}
        for f in cf.as_completed(futs):
            try:
                print("✓", f.result(), flush=True)
            except Exception as err:
                failed.append(futs[f])
                print("✗", futs[f], str(err).strip().splitlines()[-1] if str(err).strip() else err, flush=True)

    # what the page reads: no commands, just display data, and only examples whose files exist
    out = []
    for e in spec["examples"]:
        if not ((OUT / f"{e['id']}.mp4").exists() and (OUT / f"{e['id']}.jpg").exists()):
            continue
        out.append({"id": e["id"], "name": e["name"], "category": e["category"], "blurb": e["blurb"], "featured": bool(e.get("featured")),
                    "chain": [{"name": s["name"], "settings": s.get("settings", "")} for s in e["steps"]]})
    (OUT / "examples.json").write_text(json.dumps({"categories": spec["categories"], "examples": out}, indent=1))
    print(f"✅ examples.json: {len(out)} examples" + (f" · failed: {', '.join(failed)}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
