"""
What can the ffmpeg we are running actually do?

Different ffmpeg builds (our own static build, Homebrew's plain `ffmpeg`, `ffmpeg-full`, a user's own) differ in which
encoders, decoders and filters they contain. This module reads `assets/ffmpeg_requirements.json` (shared with the GUI's
Setup screen), inspects the binary once, and turns "Unknown encoder 'libsvtav1'" into a sentence a person can act on.

    python -m videobeaux.utils.ffmpeg_caps            # human report, exit 1 if a *required* feature is missing
    python -m videobeaux.utils.ffmpeg_caps --json
    python -m videobeaux.utils.ffmpeg_caps --ffmpeg /path/to/ffmpeg
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

_REQ_FILE = Path(__file__).resolve().parent.parent / "assets" / "ffmpeg_requirements.json"


class MissingCapability(RuntimeError):
    """The ffmpeg in use lacks an encoder/filter a program needs. The message is meant to be read by a person."""


def requirements() -> List[dict]:
    return json.loads(_REQ_FILE.read_text(encoding="utf-8"))["features"]


def _run(binary: str, *args: str) -> str:
    try:
        r = subprocess.run([binary, "-hide_banner", *args], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return ""
    return (r.stdout or "") + (r.stderr or "")


def _names(listing: str) -> Set[str]:
    """Second column of ffmpeg's `-encoders/-decoders/-filters` tables (skips the legend)."""
    names: Set[str] = set()
    for line in listing.splitlines():
        parts = line.split()
        # flag column is 2 chars for filters on ffmpeg 9 ("TS"), 3 on 7 ("T.C"), 6 for codecs ("V....D"); legend lines have "="
        if len(parts) >= 3 and parts[1] != "=" and re.fullmatch(r"[A-Z.]{2,6}", parts[0]):
            names.add(parts[1])
    return names


@lru_cache(maxsize=8)
def inspect(binary: str = "ffmpeg") -> dict:
    """Version, licence flavor and the encoder/decoder/filter names of `binary` (cached per path)."""
    version_text = _run(binary, "-version")
    first = version_text.splitlines()[0] if version_text else ""
    conf = _run(binary, "-buildconf") or version_text
    flavor = "nonfree" if "--enable-nonfree" in conf else "gpl" if "--enable-gpl" in conf else "lgpl"
    m = re.search(r"version\s+(\S+)", first)
    return {
        "binary": binary,
        "found": bool(first),
        "version": m.group(1) if m else None,
        "license": flavor,
        "encoders": _names(_run(binary, "-encoders")),
        "decoders": _names(_run(binary, "-decoders")),
        "filters": _names(_run(binary, "-filters")),
    }


def _have(info: dict, feat: dict) -> bool:
    pool = info[{"encoder": "encoders", "decoder": "decoders", "filter": "filters"}[feat["kind"]]]
    return any(n in pool for n in feat["any"])


def report(binary: str = "ffmpeg") -> dict:
    info = inspect(binary)
    feats = [{**f, "ok": info["found"] and _have(info, f)} for f in requirements()]
    return {
        "binary": binary, "found": info["found"], "version": info["version"], "license": info["license"],
        "features": feats,
        "missing_required": [f["id"] for f in feats if f["required"] and not f["ok"]],
        "missing_optional": [f["id"] for f in feats if not f["required"] and not f["ok"]],
    }


def has_encoder(name: str, binary: str = "ffmpeg") -> bool:
    return name in inspect(binary)["encoders"]


def has_decoder(name: str, binary: str = "ffmpeg") -> bool:
    return name in inspect(binary)["decoders"]


def friendly_missing_encoder(codec: str, binary: str = "ffmpeg") -> str:
    info = inspect(binary)
    feat = next((f for f in requirements() if f["kind"] == "encoder" and codec in f["any"]), None)
    alternatives = [n for n in (feat["any"] if feat else []) if n != codec and n in info["encoders"]]
    needed = f" (needed for: {feat['usedBy']})" if feat else ""
    msg = (f"This ffmpeg ({info['version'] or 'unknown version'}) doesn't include the '{codec}' encoder{needed}. "
           "Videobeaux's own bundled ffmpeg does: open Setup → Repair (or 'Use the bundled ffmpeg'), "
           "or pick a different format.")
    if alternatives:
        msg += f" This build does have: {', '.join(alternatives)}."
    return msg


_ENC_FLAGS = {"-c:v", "-vcodec", "-codec:v", "-c:a", "-acodec", "-codec:a", "-c:s", "-scodec", "-codec:s"}


def encoders_in_command(cmd: Iterable[str]) -> List[str]:
    """Encoder names a command asks for (options after the last -i only; `copy` and options before -i are decoders)."""
    cmd = list(cmd)
    last_i = max((i for i, t in enumerate(cmd) if t == "-i"), default=-1)
    out: List[str] = []
    for i in range(last_i + 1, len(cmd) - 1):
        if cmd[i] in _ENC_FLAGS and isinstance(cmd[i + 1], str) and cmd[i + 1] not in ("copy", "none"):
            out.append(cmd[i + 1])
    return out


def check_command(cmd: List[str]) -> Optional[str]:
    """Return a friendly message when `cmd` asks for an encoder this ffmpeg lacks; None if fine (or can't tell)."""
    if not cmd or Path(str(cmd[0])).name not in ("ffmpeg", "ffmpeg.exe"):
        return None
    binary = str(cmd[0])
    info = inspect(binary)
    if not info["found"] or not info["encoders"]:
        return None                       # can't tell → let ffmpeg speak for itself
    for codec in encoders_in_command(cmd):
        if codec not in info["encoders"]:
            return friendly_missing_encoder(codec, binary)
    return None


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    binary = "ffmpeg"
    if "--ffmpeg" in argv:
        binary = argv[argv.index("--ffmpeg") + 1]
    rep = report(binary)
    if "--json" in argv:
        print(json.dumps(rep, indent=2))
    else:
        print(f"ffmpeg: {binary}  version {rep['version']}  licence {rep['license'].upper()}")
        if not rep["found"]:
            print("  ❌ could not run it")
        for f in rep["features"]:
            tag = "required" if f["required"] else "optional"
            print(f"  {'✅' if f['ok'] else ('❌' if f['required'] else '⚠️ ')} {f['label']:<38} {tag:<9} {f['usedBy']}")
    return 1 if (not rep["found"] or rep["missing_required"] or rep["license"] == "nonfree") else 0


if __name__ == "__main__":
    raise SystemExit(main())
