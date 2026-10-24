#!/usr/bin/env python3
"""
Measure how every numeric slider *feels*.

For each program and each ranged number argument, render the program at 0 / 25 / 50 / 75 / 100 % of the slider's linear
range (everything else at its default), measure how much the picture changed compared with the input, and report:

  s(x)  = change(x) / max change     (change = picture difference from the render at the slider's minimum)          (0 … 1: share of the strongest effect reached)
  class = late (half-way gives < 20 % of the effect) · slow · even · fast · early (> 80 %) · flat (nothing visible happens)

and, for the uneven ones, the response curve that would make the slider linear in *effect*: a power curve `pow:γ` (γ > 1 means
"slow start") or `log` for ranges spanning decades. The result is written to
  ui_design/slider-audit.md      the table to review
  ui_design/slider-audit.json    raw numbers (re-runs resume from it)
  gui/slider_curves.json         only with --write-curves: { program: { arg: "pow:1.8" } }, read by gui/discover_programs.py

    python tools/audit_sliders.py [--only halftone,digital_boss] [--jobs 4] [--write-curves] [--fresh]

Needs the full Python environment and an ffmpeg on PATH (use gui/resources/ffmpeg). ~15-20 minutes for everything.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tests" / "smoke"))
import run_smoke as rs  # noqa: E402

OUT_JSON = REPO / "ui_design" / "slider-audit.json"
OUT_MD = REPO / "ui_design" / "slider-audit.md"
CURVES = REPO / "gui" / "slider_curves.json"
POINTS = (0.0, 0.25, 0.5, 0.75, 1.0)
# not "how strong is the effect" controls: quality, bookkeeping, detection cadence …
SKIP_ARGS = {"crf", "seed", "detail", "detect_every", "gop", "qscale", "bitrate", "width", "height", "fps", "threads"}
# measured as uneven but a curve doesn't help: threshold-like steps, placement percentages, or siblings that disagree
NO_CURVE = {"freeze_punch.freeze_duration", "pixel_sort.threshold", "pixelate.block", "remove_background.shrink", "thumbs.margin",
            "triptych.zoom1", "shape_synth.b_stretch_y", "stackadelic.l1_size", "stackadelic.l2_bottom", "stackadelic.l2_left",
            "stackadelic.l2_right", "stackadelic.l2_ratio"}
FRAMES = 6
SIZE = (96, 54)


def frames(path: Path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv,fps=6,scale={SIZE[0]}:{SIZE[1]},format=gray",
                        "-frames:v", str(FRAMES), "-f", "rawvideo", "-"], capture_output=True)
    a = np.frombuffer(r.stdout, np.uint8)
    n = len(a) // (SIZE[0] * SIZE[1])
    return a[: n * SIZE[0] * SIZE[1]].reshape(n, -1).astype(np.float32) if n else None


def change(ref, out_path: Path):
    f = frames(out_path)
    if f is None or ref is None:
        return None
    n = min(len(f), len(ref))
    return float(np.abs(f[:n] - ref[:n]).mean())


def sample_values(a):
    lo = a.get("slider_min", a.get("min"))
    hi = a.get("slider_max", a.get("max"))
    vals = []
    for t in POINTS:
        v = lo + (hi - lo) * t
        v = round(v) if a.get("integer") or (isinstance(a.get("default"), int) and not isinstance(a.get("default"), bool) and (hi - lo) >= 5) else float(f"{v:.4g}")
        vals.append(v)
    return vals


def classify(s50):
    return "late" if s50 < 0.2 else "slow" if s50 < 0.35 else "even" if s50 <= 0.65 else "fast" if s50 <= 0.8 else "early"


def fit_curve(a, s):
    """Scale that makes the slider linear in effect, or None if the slider is fine / the data is unreliable."""
    xs = np.array(POINTS[1:4])
    ys = np.array([max(s[1], 1e-3), max(s[2], 1e-3), max(s[3], 1e-3)])
    if not (s[1] <= s[2] + 0.05 <= s[3] + 0.1):                      # not (roughly) monotone → leave it alone
        return None
    p = float((np.log(ys) * np.log(xs)).sum() / (np.log(xs) ** 2).sum())   # s(x) ≈ x^p
    if not math.isfinite(p) or p <= 0:
        return None
    g = 1.0 / p
    g = min(3.0, max(0.35, g))
    lo = a.get("slider_min", a.get("min"))
    hi = a.get("slider_max", a.get("max"))
    if lo is not None and lo > 0 and hi / lo >= 100 and g > 1.2:
        return "log"
    if abs(g - 1.0) < 0.25:
        return None
    return f"pow:{g:.2f}".rstrip("0").rstrip(".")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="comma-separated program ids")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--fresh", action="store_true", help="ignore the previous results")
    ap.add_argument("--write-curves", action="store_true", help="write gui/slider_curves.json from the flagged sliders")
    ap.add_argument("--timeout", type=int, default=120)
    args = ap.parse_args()

    discovered = rs.discover_programs()
    cats = rs.load_categories()
    wanted = {p.strip() for p in args.only.split(",")} if args.only else None
    work = Path(tempfile.mkdtemp(prefix="vb_slider_"))
    source = Path(tempfile.mkdtemp(prefix="vb_slider_src_")) / "src.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=24:duration=20", "-f", "lavfi",
                    "-i", "sine=f=330:d=20", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(source)], check=True)
    fx = rs.build_fixtures(work / "fx", source, 1.0, 1.0, False)
    fx.synthetic = True
    ref_cache = {}

    results = {}
    if OUT_JSON.exists() and not args.fresh:
        results = json.loads(OUT_JSON.read_text())

    jobs = []
    for prog, info in sorted(discovered.items()):
        if wanted and prog not in wanted:
            continue
        spec = rs.SPECS.get(prog, {})
        if "skip" in spec and spec["skip"](fx):
            continue
        if (info.get("outputType") or "video") != "video":
            continue
        base_args = spec["args"](fx) if "args" in spec else []
        in_path = spec["input"](fx) if "input" in spec else fx.clip
        for a in info.get("args", []):
            if a.get("type") != "number" or a.get("hidden") or a.get("free"):
                continue
            lo = a.get("slider_min", a.get("min"))
            hi = a.get("slider_max", a.get("max"))
            if lo is None or hi is None or hi <= lo:
                continue
            if f"--{a['name']}" in base_args or a["name"] in SKIP_ARGS:
                continue
            key = f"{prog}.{a['name']}"
            if key in results and results[key].get("done"):
                continue
            jobs.append((prog, a, key, base_args, in_path))

    print(f"{len(jobs)} sliders to measure ({sum(len(POINTS) for _ in jobs)} renders)…", flush=True)

    def run_one(prog, a, key, base_args, in_path):
        ref = None                     # the render at the slider's minimum: "travel" = how far the picture moves from there
        vals = sample_values(a)
        diffs = []
        for i, v in enumerate(vals):
            out = work / f"{prog}_{a['name']}_{i}.mp4"
            cmd = [sys.executable, "-m", "videobeaux.cli", "-P", prog, "-i", str(in_path), "-o", str(out), "-F", *base_args, f"--{a['name']}", str(v)]
            try:
                p = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=args.timeout,
                                   env={**os.environ, "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"})
            except subprocess.TimeoutExpired:
                diffs.append(None)
                continue
            if p.returncode != 0 or not out.exists():
                diffs.append(None)
            elif ref is None:
                ref = frames(out)
                diffs.append(0.0 if ref is not None else None)
            else:
                diffs.append(change(ref, out))
            out.unlink(missing_ok=True)
        rec = {"program": prog, "arg": a["name"], "label": a.get("label"), "default": a.get("default"), "values": vals, "diff": diffs, "done": True,
               "range": [a.get("slider_min", a.get("min")), a.get("slider_max", a.get("max"))], "scale": a.get("scale")}
        if all(d is not None for d in diffs):
            base = diffs[0]
            dev = [abs(d - base) for d in diffs]
            top = max(dev)
            if top < 0.8:
                rec["class"] = "flat"
            else:
                s = [d / top for d in dev]
                rec["s"] = [round(x, 3) for x in s]
                wobbly = any(s[i + 1] < s[i] - 0.2 for i in range(len(s) - 1))      # effect goes up and down: not a strength slider
                rec["class"] = "varies" if wobbly else classify(s[2])
                rec["curve"] = fit_curve(a, s) if rec["class"] not in ("even", "varies") else None
                # only trust it when the range doesn't straddle zero and the fit is
                # not pinned at its limits (a step-like response is a threshold, not something a curve fixes)
                rec["d0"] = round(base, 2)
                c = rec["curve"]
                g = float(c.split(":")[1]) if c and c.startswith("pow:") else None
                rec["confident"] = bool(c and key not in NO_CURVE and rec["range"][0] >= 0 and (g is None or 0.4 <= g <= 2.9))
        else:
            rec["class"] = "error"
        return key, rec

    done = 0
    with cf.ThreadPoolExecutor(max_workers=args.jobs) as ex:
        for fut in cf.as_completed([ex.submit(run_one, *j) for j in jobs]):
            key, rec = fut.result()
            results[key] = rec
            done += 1
            if done % 25 == 0 or done == len(jobs):
                OUT_JSON.write_text(json.dumps(results, indent=1))
                print(f"  {done}/{len(jobs)}", flush=True)
    OUT_JSON.write_text(json.dumps(results, indent=1))

    # ── report ──
    rows = sorted(results.values(), key=lambda r: (r["program"], r["arg"]))
    for r in rows:                                                  # the exclusion list may have changed since the numbers were taken
        if f"{r['program']}.{r['arg']}" in NO_CURVE:
            r["confident"] = False
    from collections import Counter
    cnt = Counter(r.get("class") for r in rows)
    md = ["# Slider response audit", "",
          "How much the picture changes at 0 / 25 / 50 / 75 / 100 % of each slider (linear slider position → value, as shipped before the curves).",
          "`s50` = share of the strongest effect reached at half-way. **late** < 0.20 · slow < 0.35 · even 0.35–0.65 · fast ≤ 0.80 · **early** > 0.80 · flat = no visible change.", "",
          "**" + " · ".join(f"{k}: {v}" for k, v in sorted(cnt.items(), key=lambda kv: -kv[1])) + "**", "",
          "| program | slider | range | default | s25 | s50 | s75 | class | suggested curve |", "|---|---|---|---|---|---|---|---|---|"]
    md[3:3] = ["Curves are only written for **trusted** rows (✔): non-negative range, fit not pinned at its limits.", ""]
    for r in rows:
        s = r.get("s") or [None] * 5
        f = lambda x: "" if x is None else f"{x:.2f}"
        md.append(f"| {r['program']} | {r['arg']} | {r['range'][0]}…{r['range'][1]} | {r['default']} | {f(s[1])} | {f(s[2])} | {f(s[3])} | {r.get('class')} | {(r.get('curve') or '') + (' ✔' if r.get('confident') else '')} |")
    OUT_MD.write_text("\n".join(md) + "\n")
    print(f"✅ {len(rows)} sliders → {OUT_MD}\n   " + " · ".join(f"{k}: {v}" for k, v in cnt.items()))

    if args.write_curves:
        table = {}
        for r in rows:
            if r.get("curve") and r.get("confident"):
                table.setdefault(r["program"], {})[r["arg"]] = r["curve"]
        CURVES.write_text(json.dumps(table, indent=1, sort_keys=True) + "\n")
        print(f"✍️  {sum(len(v) for v in table.values())} curves → {CURVES}")


if __name__ == "__main__":
    main()
