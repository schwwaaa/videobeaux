#!/usr/bin/env python3
"""
Make the example library: one ready-to-load canvas (.vbpreset.json) per program mode, plus a few chains of several modes.
Every example uses the bundled sample clips.

    python tools/make_example_presets.py            # make the clips and presets, then test every one
    python tools/make_example_presets.py --no-test  # write presets only (not verified)

Output (committed; shipped inside the app as resources/examples):
    examples/sample.mp4                 the main clip (copied from tools/site_source/)
    examples/sample2.mp4, sample3.mp4   two more clips made from sample.mp4 (hue-shifted, and played backwards), so
                                        multi-input modes have a second and third clip to take
    examples/presets/<id>.vbpreset.json one canvas per example:
                                        a program mode: Input → program → Output
                                        a chain (CHAINS below): Input → program → program → … → Output
                                        extra clips become extra Input nodes wired to the program's video handles
    examples/index.json                 the list the app shows (name, description, category, file, clip and step counts)

Each preset refers to clips with tokens ({{sample}}, {{sample2}}, {{sample3}}) and writes to {{outputs}}/<id>.mp4. The app
replaces the tokens with real paths when an example is opened (see presets:resolveTokens in gui/src/main/index.js).

What goes in a single-mode preset: the program mode's own first preset (the chips in the app), if it has one and it uses no
files; otherwise the defaults. Video inputs are filled from the example clips, the required ones first. Program modes are left
out when they are hidden from the app, produce something other than a video, need a file the examples don't include (a speech
model, an image), or fail when tested. Each skipped mode and the reason is printed, so nothing disappears silently.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EX = ROOT / "examples"
PRE = EX / "presets"
SAMPLE_SRC = ROOT / "tools" / "site_source" / "example_original.mp4"
PY = ROOT / "venv" / "bin" / "python" if (ROOT / "venv" / "bin" / "python").exists() else Path(sys.executable)
FFMPEG = ROOT / "gui" / "resources" / "ffmpeg" / "ffmpeg"

# Clip tokens and the files they stand for. The first is the main input; the other two fill extra input handles.
CLIP_FILES = {"sample": "sample.mp4", "sample2": "sample2.mp4", "sample3": "sample3.mp4"}
EXTRA_CLIPS = ["sample2", "sample3"]
STEP_WIDTH = 520                                # canvas spacing between program nodes (wide modes like Triptych need room)

# Chains: several program modes in a row. Each step is (program id, {video argument: clip token}).
CHAINS = [
    {"id": "chain_steady_warm_fast", "name": "Steady, Warm, Fast",
     "description": "Steady the shake, warm the colour, then speed it up.",
     "steps": [("stabilize", {}), ("gamma_fix", {}), ("speed", {})]},
    {"id": "chain_thermal_echo_crt", "name": "Thermal Echo CRT",
     "description": "Heat-map colours, a mirror echo, then an old CRT screen.",
     "steps": [("thermal", {}), ("mirror_delay", {}), ("crt_monitor", {})]},
    {"id": "chain_night_tape", "name": "Night Tape",
     "description": "Night vision, VHS tracking, then a weak signal.",
     "steps": [("night_vision", {}), ("vhs_tracking", {}), ("weak_signal", {})]},
    {"id": "chain_backwards_strobe", "name": "Backwards Strobe",
     "description": "Play it backwards, cut it into strobes, then freeze the frames.",
     "steps": [("reverse", {}), ("strobe_cut", {}), ("freeze_frame", {})]},
    {"id": "chain_ghost_layer", "name": "Ghost Layer",
     "description": "Blend a second clip over the first, feed it back, then add edges.",
     "steps": [("layer_blend", {"input2": "sample2"}), ("lsd_feedback", {}), ("neon_edges", {})]},
    {"id": "chain_stacked_sort", "name": "Stacked Sort",
     "description": "Stack two clips, pixel-sort the result, then add tracking noise.",
     "steps": [("stack_2x", {"input2": "sample2"}), ("pixel_sort", {}), ("vhs_tracking", {})]},
    {"id": "chain_three_screens", "name": "Three Screens, One Glitch",
     "description": "Three clips side by side, then chromatic pulses and a CRT.",
     "steps": [("triptych", {"input2": "sample2", "input3": "sample3"}), ("chromatic_pulse", {}), ("crt_monitor", {})]},
    {"id": "chain_dot_drift", "name": "Dot Drift",
     "description": "Halftone dots, a warp, then a palette of a few colours.",
     "steps": [("halftone", {}), ("warp", {}), ("kmeans_palette", {})]},
]


def ffmpeg_bin() -> str:
    return str(FFMPEG) if FFMPEG.exists() else (shutil.which("ffmpeg") or "ffmpeg")


def program_catalog():
    """Categories and hidden ids from the app's own program list (programs.js), read by node so there is one source of truth."""
    js = ("import { CATEGORIES, EXCLUDED_FROM_GUI } from './src/renderer/src/programs.js';"
          "const out = { categories: CATEGORIES.map(c => ({ label: c.label, ids: c.programs.map(p => ({ id: p.id, label: p.label, "
          "description: p.description || '', batch: !!p.batchOutput, outputType: p.outputType || 'video', args: p.args || [] })) })), "
          "hidden: [...EXCLUDED_FROM_GUI] }; console.log(JSON.stringify(out));")
    r = subprocess.run(["node", "--input-type=module", "-e", js], cwd=ROOT / "gui", capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def discovered():
    r = subprocess.run([str(PY), str(ROOT / "gui" / "discover_programs.py")], cwd=ROOT, capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def make_clips():
    """sample2.mp4 and sample3.mp4, made from sample.mp4: hue-shifted, and played backwards. Same size, length and frame rate."""
    enc = ["-c:v", "libx264", "-crf", "23", "-pix_fmt", "yuv420p", "-r", "24000/1001",
           "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart"]
    for name, vf, af in [("sample2.mp4", "hue=h=180", "anull"), ("sample3.mp4", "reverse", "areverse")]:
        subprocess.run([ffmpeg_bin(), "-hide_banner", "-loglevel", "error", "-y", "-i", str(EX / "sample.mp4"),
                        "-vf", vf, "-af", af, *enc, str(EX / name)], check=True)


def preset_args(info: dict, known: dict) -> dict:
    """The program mode's first preset chip, if it sets only plain (non-file) values."""
    for _name, values in (info.get("presets") or {}).items():
        if all(k in known and known[k].get("type") not in ("file", "color") for k in values):
            return dict(values)
        break
    return {}


def plan_inputs(info: dict):
    """How a program mode gets its inputs from the example clips.

    Returns (clips, fixed, reason). clips maps each video argument to a clip token, required ones first; fixed holds argument
    values the examples set (a soundtrack's audio is the sample's own sound); reason says why the mode can't be an example
    (None when it can)."""
    args = info.get("args", [])
    slots = [a for a in args if a.get("type") == "file" and a.get("subtype") == "video"]
    ordered = [a for a in slots if a.get("required")] + [a for a in slots if not a.get("required")]
    if sum(1 for a in slots if a.get("required")) > len(EXTRA_CLIPS):
        return {}, {}, "needs more clips than the examples include"
    clips = {a["name"]: clip for a, clip in zip(ordered, EXTRA_CLIPS)}
    fixed = {}
    for a in args:
        if a in slots or not a.get("required") or a.get("type") != "file":
            continue
        if a.get("subtype") == "audio":
            fixed[a["name"]] = "{{sample}}"
        elif a.get("subtype") == "model" or "model" in a["name"]:
            return {}, {}, "needs a speech model (downloaded in the app)"
        else:
            return {}, {}, f"needs a file the examples don't include ({a.get('label') or a['name']})"
    return clips, fixed, None


def cli_args(args: dict) -> list[str]:
    out = []
    for k, v in args.items():
        if v is None or v is False:
            continue
        if v is True:
            out.append(f"--{k}")
        else:
            out += [f"--{k}", str(v)]
    return out


def canvas(name: str, steps: list[dict]) -> dict:
    """The preset canvas: the main clip in, the steps in a row, the output file named after the example."""
    nodes = [{"id": "input-1", "type": "inputNode", "position": {"x": 0, "y": 120},
              "data": {"filePath": "{{sample}}"}, "deletable": False}]
    edges = []

    def edge(src, tgt, handle=None):
        eid = f"xy-edge__{src}-{tgt}" + (f"-{handle}" if handle else "")
        return {"id": eid, "source": src, "target": tgt, "sourceHandle": None, "targetHandle": handle, "type": "smoothstep"}

    clip_node = {"sample": "input-1"}
    for clip in dict.fromkeys(c for s in steps for c in s["clips"].values()):
        cid = f"input-{len(clip_node) + 1}"
        clip_node[clip] = cid
        nodes.append({"id": cid, "type": "inputNode", "position": {"x": 0, "y": 120 + 280 * (len(clip_node) - 1)},
                      "data": {"filePath": "{{" + clip + "}}"}})

    prev = "input-1"
    for k, s in enumerate(steps, start=1):
        eid = f"effect-1-{k}"
        nodes.append({"id": eid, "type": "effectNode", "position": {"x": 380 + STEP_WIDTH * (k - 1), "y": 60},
                      "data": {"program": s["program"], "args": s["args"]}})
        edges.append(edge(prev, eid))
        for arg, clip in s["clips"].items():
            edges.append(edge(clip_node[clip], eid, arg))
        prev = eid
    nodes.append({"id": "output-1", "type": "outputNode", "position": {"x": 380 + STEP_WIDTH * len(steps), "y": 120},
                  "data": {"filePath": "{{outputs}}/" + name + ".mp4", "format": "mp4"}, "deletable": False})
    edges.append(edge(prev, "output-1"))
    return {
        "presetFormatVersion": 1,
        "savedAt": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "nodes": nodes,
        "edges": edges,
    }


def run_program(pid: str, args: dict, clips: dict, src: Path, out: Path, timeout: int):
    """One program mode through the CLI. Returns (ok, error)."""
    cmd = [str(PY), "-m", "videobeaux.cli", "-P", pid, "-i", str(src), "-o", str(out), "-F"]
    for arg, clip in clips.items():
        cmd += [f"--{arg}", str(EX / CLIP_FILES[clip])]
    cmd += cli_args({k: (str(EX / CLIP_FILES["sample"]) if v == "{{sample}}" else v) for k, v in args.items()})
    try:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout,
                           env={**os.environ, "VB_QUIET": "1", "PYTHONUTF8": "1"})
    except subprocess.TimeoutExpired:
        return False, "timed out"
    if r.returncode == 0 and out.exists() and out.stat().st_size > 0:
        return True, ""
    tail = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
    return False, (tail[-1] if tail else f"exit {r.returncode}")[:200]


def run_steps(steps: list[dict], args_list: list[dict], tmp: Path, timeout: int):
    """Run the steps in order, each step's output feeding the next. Returns (ok, error)."""
    src = EX / CLIP_FILES["sample"]
    for s, args in zip(steps, args_list):
        out = tmp / f"{s['program']}-{uuid.uuid4().hex[:8]}.mp4"
        ok, err = run_program(s["program"], args, s["clips"], src, out, timeout)
        if not ok:
            return False, f"{s['program']}: {err}"
        src = out
    return True, ""


def test_steps(steps: list[dict], tmp: Path, timeout: int):
    """Run the steps with their preset values; if that fails, with the defaults. Returns (ok, args_used, error)."""
    chosen = [s["args"] for s in steps]
    ok, err = run_steps(steps, chosen, tmp, timeout)
    if ok:
        return True, chosen, ""
    if any(chosen):                              # the preset's values didn't work here: fall back to the defaults
        defaults = [s["defaults"] for s in steps]
        ok2, err2 = run_steps(steps, defaults, tmp, timeout)
        if ok2:
            return True, defaults, ""
        return False, chosen, f"{err} (defaults also failed: {err2})"
    return False, chosen, err


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-test", action="store_true", help="write the presets without testing them on the sample")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=300)
    a = ap.parse_args()

    EX.mkdir(exist_ok=True)
    PRE.mkdir(exist_ok=True)
    shutil.copyfile(SAMPLE_SRC, EX / "sample.mp4")
    make_clips()

    cat = program_catalog()
    hidden = set(cat["hidden"])
    disc = discovered()
    entries, skipped = [], []
    for c in cat["categories"]:
        for p in c["ids"]:
            pid = p["id"]
            info = disc.get(pid, {})
            known = {x["name"]: x for x in info.get("args", [])}
            reason = None
            clips, fixed = {}, {}
            if pid in hidden:
                reason = "hidden from the app"
            elif p["batch"]:
                reason = "batch mode (needs a folder)"
            elif p["outputType"] not in ("video", None):
                reason = f"makes {p['outputType']}, not a video"
            elif info.get("error"):
                reason = "does not load"
            else:
                clips, fixed, reason = plan_inputs(info)
                if not reason:
                    chip = preset_args(info, known)
                    unset = [a.get("label") or a["name"] for a in info.get("args", [])
                             if a.get("required") and a.get("type") != "file" and a.get("default") is None
                             and a["name"] not in chip]
                    if unset:
                        reason = f"needs a value the examples don't set ({unset[0]})"
            if reason:
                skipped.append((pid, reason))
                continue
            defaults = dict(fixed)
            step = {"program": pid, "args": {**preset_args(info, known), **fixed}, "defaults": defaults, "clips": clips}
            entries.append({"id": pid, "name": p["label"], "description": p["description"], "category": c["label"], "steps": [step]})

    for chain in CHAINS:
        steps, reason = [], None
        for pid, clips in chain["steps"]:
            info = disc.get(pid, {})
            known = {x["name"]: x for x in info.get("args", [])}
            if pid in hidden or info.get("error") or not info:
                reason = f"{pid} is not available"
                break
            steps.append({"program": pid, "args": preset_args(info, known), "defaults": {}, "clips": clips})
        if reason:
            skipped.append((chain["id"], reason))
            continue
        entries.append({"id": chain["id"], "name": chain["name"], "description": chain["description"], "category": "Chains",
                        "steps": steps})

    print(f"{len(entries)} candidate examples ({sum(1 for e in entries if len(e['steps']) == 1)} program modes, "
          f"{sum(1 for e in entries if len(e['steps']) > 1)} chains), {len(skipped)} skipped before testing")
    if not a.no_test:
        tmp = Path(tempfile.mkdtemp(prefix="vb_examples_"))
        print(f"testing each on the sample clips ({a.jobs} at a time)…", flush=True)
        results = {}
        with cf.ThreadPoolExecutor(max_workers=a.jobs) as ex:
            futs = {ex.submit(test_steps, e["steps"], tmp, a.timeout): e for e in entries}
            for f in cf.as_completed(futs):
                e = futs[f]
                ok, used, err = f.result()
                results[e["id"]] = (ok, used, err)
                print(("  ✓ " if ok else "  ✗ ") + e["id"] + ("" if ok else f"  — {err}"), flush=True)
        shutil.rmtree(tmp, ignore_errors=True)
        kept = []
        for e in entries:
            ok, used, err = results[e["id"]]
            if ok:
                for s, args in zip(e["steps"], used):
                    s["args"] = args
                kept.append(e)
            else:
                skipped.append((e["id"], f"failed on the sample: {err}"))
        entries = kept

    for old in PRE.glob("*.vbpreset.json"):
        old.unlink()
    index = []
    for e in entries:
        fname = f"{e['id']}.vbpreset.json"
        clip_count = 1 + len({c for s in e["steps"] for c in s["clips"].values()})
        (PRE / fname).write_text(json.dumps(canvas(e["id"], e["steps"]), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        index.append({"id": e["id"], "name": e["name"], "description": e["description"], "category": e["category"],
                      "file": f"presets/{fname}", "clips": clip_count, "steps": len(e["steps"])})
    (EX / "index.json").write_text(json.dumps({"sample": "sample.mp4", "clips": list(CLIP_FILES.values()), "examples": index},
                                              indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\n✅ {len(entries)} example presets → {PRE}")
    if skipped:
        print(f"⏭  {len(skipped)} left out:")
        for pid, why in sorted(skipped):
            print(f"   {pid}: {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
