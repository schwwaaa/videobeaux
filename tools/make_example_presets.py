#!/usr/bin/env python3
"""
Make the example library: one ready-to-load canvas (.vbpreset.json) per program mode, all using the same bundled sample clip.

    python tools/make_example_presets.py            # write presets, then test every one on the sample clip
    python tools/make_example_presets.py --no-test  # write presets only (not verified)

Output (committed; shipped inside the app as resources/examples):
    examples/sample.mp4                 the clip every example uses (copied from tools/site_source/)
    examples/presets/<id>.vbpreset.json one canvas per program mode: Input → program → Output
    examples/index.json                 the list the app shows (name, one-line description, category, file)

Each preset refers to the sample with the token {{sample}} and writes to {{outputs}}/<id>.mp4; the app replaces those tokens with
real paths when the preset is loaded (see presets:resolveTokens in gui/src/main/index.js).

What goes in a preset: the program mode's own first preset (the chips in the app), if it has one and it uses no files; otherwise
the defaults. Program modes are left out when they are hidden from the app, produce something other than a video, need a file
they can't get from the sample (a speech model, a second clip), or fail on the sample when tested. Each skipped mode and the
reason is printed, so nothing disappears silently.
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


def preset_args(info: dict, known: dict) -> dict:
    """The program mode's first preset chip, if it sets only plain (non-file) values."""
    for _name, values in (info.get("presets") or {}).items():
        if all(k in known and known[k].get("type") not in ("file", "color") for k in values):
            return dict(values)
        break
    return {}


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


def canvas(pid: str, args: dict, name: str) -> dict:
    return {
        "presetFormatVersion": 1,
        "savedAt": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "nodes": [
            {"id": "input-1", "type": "inputNode", "position": {"x": 0, "y": 120},
             "data": {"filePath": "{{sample}}"}, "deletable": False},
            {"id": "effect-1-1", "type": "effectNode", "position": {"x": 380, "y": 60},
             "data": {"program": pid, "args": args}},
            {"id": "output-1", "type": "outputNode", "position": {"x": 760, "y": 120},
             "data": {"filePath": f"{{{{outputs}}}}/{pid}.mp4", "format": "mp4"}, "deletable": False},
        ],
        "edges": [
            {"id": "xy-edge__input-1-effect-1-1", "source": "input-1", "target": "effect-1-1", "sourceHandle": None, "targetHandle": None, "type": "smoothstep"},
            {"id": "xy-edge__effect-1-1-output-1", "source": "effect-1-1", "target": "output-1", "sourceHandle": None, "targetHandle": None, "type": "smoothstep"},
        ],
    }


def test_one(pid: str, args: dict, sample: Path, tmp: Path, timeout: int):
    """Run the program through the CLI on the sample. Returns (ok, args_used, error)."""
    def run(a):
        out = tmp / f"{pid}-{uuid.uuid4().hex[:8]}.mp4"
        cmd = [str(PY), "-m", "videobeaux.cli", "-P", pid, "-i", str(sample), "-o", str(out), "-F", *cli_args(a)]
        try:
            r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout,
                               env={**os.environ, "VB_QUIET": "1", "PYTHONUTF8": "1"})
        except subprocess.TimeoutExpired:
            return False, "timed out"
        if r.returncode == 0 and out.exists() and out.stat().st_size > 0:
            return True, ""
        tail = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
        return False, (tail[-1] if tail else f"exit {r.returncode}")[:200]
    ok, err = run(args)
    if ok:
        return True, args, ""
    if args:                                    # the preset's values didn't work here: fall back to the defaults
        ok2, err2 = run({})
        if ok2:
            return True, {}, ""
        return False, {}, f"{err} (defaults also failed: {err2})"
    return False, {}, err


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-test", action="store_true", help="write the presets without testing them on the sample")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=300)
    a = ap.parse_args()

    EX.mkdir(exist_ok=True)
    PRE.mkdir(exist_ok=True)
    shutil.copyfile(SAMPLE_SRC, EX / "sample.mp4")
    sample = EX / "sample.mp4"

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
            if pid in hidden:
                reason = "hidden from the app"
            elif p["batch"]:
                reason = "batch mode (needs a folder)"
            elif p["outputType"] not in ("video", None):
                reason = f"makes {p['outputType']}, not a video"
            elif info.get("error"):
                reason = "does not load"
            elif any(x.get("required") and x.get("type") == "file" for x in info.get("args", [])):
                reason = "needs a file the sample can't provide (a model or a second clip)"
            if reason:
                skipped.append((pid, reason))
                continue
            entries.append({"id": pid, "name": p["label"], "description": p["description"], "category": c["label"],
                            "args": preset_args(info, known)})

    print(f"{len(entries)} candidate program modes, {len(skipped)} skipped before testing")
    if not a.no_test:
        tmp = Path(tempfile.mkdtemp(prefix="vb_examples_"))
        print(f"testing each on the sample clip ({a.jobs} at a time)…", flush=True)
        results = {}
        with cf.ThreadPoolExecutor(max_workers=a.jobs) as ex:
            futs = {ex.submit(test_one, e["id"], e["args"], sample, tmp, a.timeout): e for e in entries}
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
                e["args"] = used
                kept.append(e)
            else:
                skipped.append((e["id"], f"failed on the sample: {err}"))
        entries = kept

    for old in PRE.glob("*.vbpreset.json"):
        old.unlink()
    index = []
    for e in entries:
        fname = f"{e['id']}.vbpreset.json"
        (PRE / fname).write_text(json.dumps(canvas(e["id"], e["args"], e["name"]), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        index.append({"id": e["id"], "name": e["name"], "description": e["description"], "category": e["category"],
                      "file": f"presets/{fname}"})
    (EX / "index.json").write_text(json.dumps({"sample": "sample.mp4", "examples": index}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\n✅ {len(entries)} example presets → {PRE}")
    if skipped:
        print(f"⏭  {len(skipped)} program modes left out:")
        for pid, why in sorted(skipped):
            print(f"   {pid}: {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
