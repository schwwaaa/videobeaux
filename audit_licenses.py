#!/usr/bin/env python3
"""
audit_licenses.py
Conservative commercial-redistribution/license-health auditor for Videobeaux
(or another Python/Electron/native desktop application).

Outputs:
  - JSON machine-readable audit
  - HTML human-readable report
  - draft THIRD_PARTY_NOTICES.txt

This is an engineering/compliance triage tool, NOT legal advice and NOT a
legal-clearance engine. "LOW" means "no obvious issue found by this scanner",
not "legally approved".

Python 3.9+; standard library only.
"""

from __future__ import annotations

import argparse
import csv
import html
import importlib.metadata as md
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple
from urllib.parse import urlparse


VERSION = "1.1.0"

SKIP_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "__pycache__", ".tox", ".nox", ".next", ".cache",
    "coverage", ".coverage", "htmlcov",
}

# node_modules is intentionally not globally skipped. We avoid walking it during
# source scans, but inspect installed npm package metadata separately.
SOURCE_SKIP_DIRS = SKIP_DIRS | {
    "node_modules", "dist", "build", "release", "out", ".venv", "venv", "env"
}

LICENSE_NAMES = {
    "license", "license.txt", "license.md", "license.rst",
    "copying", "copying.txt", "copying.md",
    "notice", "notice.txt", "notice.md",
    "copyright", "copyright.txt",
}

MODEL_EXTS = {
    ".safetensors", ".ckpt", ".pth", ".pt", ".onnx", ".gguf", ".ggml",
    ".bin", ".tflite", ".pb", ".h5", ".keras", ".mlmodel", ".mlpackage",
}

NATIVE_EXTS = {
    ".dylib", ".so", ".dll", ".exe", ".node", ".framework", ".a", ".lib"
}

SOURCE_EXTS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".rs", ".go", ".java",
    ".sh", ".bash", ".zsh", ".toml", ".yaml", ".yml", ".json", ".md"
}

URL_RE = re.compile(r'https?://[^\s\'"<>()\]]+', re.I)
GITHUB_RE = re.compile(r'https?://(?:www\.)?github\.com/([^/\s]+)/([^/#?\s]+)', re.I)
SPDX_RE = re.compile(r'SPDX-License-Identifier:\s*([A-Za-z0-9.+\-() ]+)', re.I)
COPYRIGHT_RE = re.compile(r'copyright\s*(?:\(c\))?\s*[^,\n]{0,180}', re.I)

# Conservative classification. Context still matters; copyleft is not
# automatically "bad", but it deserves review for a proprietary distribution.
PERMISSIVE_HINTS = {
    "mit", "bsd", "isc", "apache-2.0", "apache 2.0", "python-2.0",
    "psf", "zlib", "boost", "unlicense", "cc0", "0bsd", "wtfpl",
}
NOTICE_HINTS = {
    "apache", "bsd", "mit", "isc", "mpl", "python", "psf", "zlib",
}
REVIEW_HINTS = {
    "lgpl", "mpl", "epl", "cddl", "artistic", "cecill", "ms-pl",
}
HIGH_HINTS = {
    "agpl", "sspl", "commons clause", "non-commercial", "noncommercial",
    "research only", "academic use only", "no commercial", "source available",
    "polyform", "business source", "bsl",
}
GPL_HINTS = {"gpl", "gnu general public license"}

FFMPEG_GPL_LIBS = {
    "libaom": None,  # license can be permissive; included for visibility only
    "libx264": "GPL-enabled FFmpeg commonly uses libx264; verify exact license/build.",
    "libx265": "GPL-enabled FFmpeg commonly uses libx265; verify exact license/build.",
    "libxavs": "Review FFmpeg licensing implications.",
    "libxavs2": "Review FFmpeg licensing implications.",
    "libvidstab": "FFmpeg documents GPL implications for some external libraries.",
    "frei0r": "FFmpeg documents GPL implications when enabled with frei0r.",
    "rubberband": "Review exact FFmpeg build and linked-library license.",
}

FFMPEG_NONFREE_FLAGS = {
    "--enable-nonfree",
}

LOCKFILES = {
    "package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml",
    "requirements.txt", "requirements-dev.txt", "requirements-prod.txt",
    "poetry.lock", "Pipfile.lock", "uv.lock", "pyproject.toml", "package.json",
}


@dataclass
class Finding:
    severity: str
    category: str
    subject: str
    message: str
    path: str = ""
    evidence: str = ""
    remediation: str = ""


@dataclass
class Component:
    name: str
    version: str = ""
    ecosystem: str = ""
    license: str = ""
    source: str = ""
    path: str = ""
    bundled: Optional[bool] = None
    severity: str = "UNKNOWN"
    notes: List[str] = field(default_factory=list)


@dataclass
class Audit:
    generated_at: str
    tool_version: str
    root: str
    app: str = ""
    platform: str = sys.platform
    findings: List[Finding] = field(default_factory=list)
    components: List[Component] = field(default_factory=list)
    ffmpeg: Dict[str, Any] = field(default_factory=dict)
    models: List[Dict[str, Any]] = field(default_factory=list)
    native_files: List[Dict[str, Any]] = field(default_factory=list)
    license_files: List[str] = field(default_factory=list)
    provenance_urls: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def run(cmd: Sequence[str], cwd: Optional[Path] = None, timeout: int = 30) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(
            list(cmd), cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, errors="replace", timeout=timeout
        )
        return p.returncode, p.stdout, p.stderr
    except (OSError, subprocess.SubprocessError) as e:
        return 127, "", str(e)


def safe_text(path: Path, max_bytes: int = 1_000_000) -> str:
    try:
        with path.open("rb") as f:
            data = f.read(max_bytes)
        if b"\x00" in data[:4096]:
            return ""
        return data.decode("utf-8", errors="replace")
    except OSError:
        return ""


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except Exception:
        return str(path)


def walk(root: Path, skip_dirs: Set[str]) -> Iterable[Path]:
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        b = Path(base)
        for name in files:
            yield b / name


def classify_license(license_text: str) -> Tuple[str, str]:
    s = (license_text or "").strip().lower()
    if not s or s in {"unknown", "none", "n/a"}:
        return "UNKNOWN", "No license metadata detected."
    if any(x in s for x in HIGH_HINTS):
        return "HIGH", "Restrictive/non-commercial/source-available license signal; manual review required."
    # AGPL must be checked before GPL substring.
    if "agpl" in s:
        return "HIGH", "AGPL signal; network/corresponding-source obligations require legal review."
    if any(x in s for x in REVIEW_HINTS):
        return "REVIEW", "Conditional/copy-left license; distribution method and modifications matter."
    if re.search(r'(^|[^a])gpl(?:-| |$)', s) or "gnu general public license" in s:
        return "REVIEW", "GPL signal; proprietary aggregation/linking/distribution details require review."
    if any(x in s for x in PERMISSIVE_HINTS):
        return "NOTICE", "Generally permissive license signal; preserve required notices/license text."
    return "REVIEW", "License was detected but is not confidently classified by this scanner."


def add_finding(audit: Audit, severity: str, category: str, subject: str, message: str,
                path: str = "", evidence: str = "", remediation: str = "") -> None:
    audit.findings.append(Finding(severity, category, subject, message, path, evidence, remediation))


def find_license_files(root: Path, audit: Audit, source_only: bool = False) -> None:
    skip = SOURCE_SKIP_DIRS if source_only else SKIP_DIRS
    for p in walk(root, skip):
        if p.name.lower() in LICENSE_NAMES or p.name.lower().startswith(("license.", "copying.", "notice.")):
            audit.license_files.append(rel(p, root))


def parse_package_json(root: Path, audit: Audit) -> Dict[str, Any]:
    p = root / "package.json"
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        add_finding(audit, "REVIEW", "npm", "package.json", f"Could not parse package.json: {e}", str(p))
        return {}
    lic = data.get("license", "")
    if lic:
        sev, note = classify_license(str(lic))
        audit.metadata["project_npm_license"] = lic
        if sev in {"HIGH", "REVIEW"}:
            add_finding(audit, sev, "project-license", data.get("name", "project"),
                        f"Project package.json declares license {lic}. {note}", rel(p, root))
    return data


def npm_inventory(root: Path, audit: Audit) -> None:
    pkg = parse_package_json(root, audit)
    if not pkg:
        return

    declared = {}
    for group in ("dependencies", "optionalDependencies", "peerDependencies", "devDependencies"):
        for name, spec in (pkg.get(group) or {}).items():
            declared[name] = (spec, group)

    node_modules = root / "node_modules"
    if not node_modules.exists():
        add_finding(
            audit, "UNKNOWN", "npm", "node_modules",
            "node_modules is absent; npm license inventory is limited to declared dependencies.",
            rel(root / "package.json", root),
            remediation="Run npm ci before the audit for a complete installed-package inventory."
        )
        for name, (spec, group) in sorted(declared.items()):
            audit.components.append(Component(name=name, version=spec, ecosystem=f"npm:{group}",
                                              source="package.json", severity="UNKNOWN"))
        return

    seen = set()
    package_jsons: List[Path] = []
    # Top-level plus scoped packages; transitive packages may be nested, so walk.
    for base, dirs, files in os.walk(node_modules):
        # Avoid gigantic irrelevant caches.
        dirs[:] = [d for d in dirs if d not in {".cache", ".bin"}]
        if "package.json" in files:
            package_jsons.append(Path(base) / "package.json")

    for p in package_jsons:
        try:
            data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        name = str(data.get("name") or p.parent.name)
        version = str(data.get("version") or "")
        key = (name, version)
        if key in seen:
            continue
        seen.add(key)
        lic = data.get("license")
        if isinstance(lic, dict):
            lic = lic.get("type", "")
        if isinstance(lic, list):
            lic = " OR ".join(str(x.get("type", x)) if isinstance(x, dict) else str(x) for x in lic)
        lic = str(lic or "")
        sev, note = classify_license(lic)
        comp = Component(
            name=name, version=version, ecosystem="npm", license=lic,
            source=str(data.get("homepage") or data.get("repository") or ""),
            path=rel(p.parent, root), severity=sev, notes=[note]
        )
        audit.components.append(comp)
        if sev in {"HIGH", "REVIEW", "UNKNOWN"}:
            add_finding(
                audit, sev, "npm-license", f"{name}@{version}",
                f"npm package license: {lic or 'UNKNOWN'}. {note}",
                rel(p, root),
                remediation="Verify the package's canonical license and obligations; replace or document if necessary."
            )


def python_inventory(root: Path, audit: Audit) -> None:
    # Inventory the interpreter running the audit. This is useful when run from
    # Videobeaux's bundled/packaging environment; report makes that explicit.
    audit.metadata["python_inventory_interpreter"] = sys.executable
    try:
        dists = list(md.distributions())
    except Exception as e:
        add_finding(audit, "UNKNOWN", "python", "installed environment",
                    f"Could not enumerate installed Python distributions: {e}")
        return

    for dist in dists:
        name = dist.metadata.get("Name") or "unknown"
        version = dist.version or ""
        license_value = (dist.metadata.get("License") or "").strip()
        classifiers = dist.metadata.get_all("Classifier") or []
        lic_classifiers = [x.split(" :: ")[-1] for x in classifiers if x.startswith("License ::")]
        if not license_value and lic_classifiers:
            license_value = " / ".join(lic_classifiers)
        home = dist.metadata.get("Home-page") or ""
        sev, note = classify_license(license_value)
        audit.components.append(Component(
            name=name, version=version, ecosystem="python-installed",
            license=license_value, source=home, severity=sev,
            notes=[note, f"Inventoried from interpreter: {sys.executable}"]
        ))
        if sev in {"HIGH", "REVIEW", "UNKNOWN"}:
            add_finding(
                audit, sev, "python-license", f"{name}=={version}",
                f"Installed Python package license: {license_value or 'UNKNOWN'}. {note}",
                evidence=f"Interpreter: {sys.executable}",
                remediation="Verify canonical package metadata/LICENSE and whether this package is actually bundled."
            )

    # Also list requirement/lock manifests for provenance.
    for name in LOCKFILES:
        p = root / name
        if p.exists():
            audit.metadata.setdefault("dependency_manifests", []).append(rel(p, root))


def source_provenance_scan(root: Path, audit: Audit) -> None:
    """
    Scan *project-authored source* for provenance clues.

    Important: ordinary occurrences of words such as "non-commercial",
    "GPL", or "all rights reserved" are NOT license evidence. Libraries often
    contain SPDX vocabularies, schemas, documentation, tests, user-agent text,
    or data that mention license names. We therefore only classify an explicit
    SPDX-License-Identifier header here.

    External repository/model URLs are recorded as provenance leads, not as
    license violations.
    """
    urls_seen = set()

    # Generated audit outputs must never audit themselves.
    generated_names = {
        "license-audit.json", "license-audit.html",
        "third_party_notices.draft.txt", "third-party_notices.draft.txt",
        "third_party_notices.txt", "third-party_notices.txt",
    }

    for p in walk(root, SOURCE_SKIP_DIRS):
        if p.name.lower() in generated_names:
            continue
        if p.suffix.lower() not in SOURCE_EXTS:
            continue
        try:
            if p.stat().st_size > 2_000_000:
                continue
        except OSError:
            continue

        text = safe_text(p, 500_000)
        if not text:
            continue

        # Explicit SPDX headers are meaningful evidence.
        for m in SPDX_RE.finditer(text):
            lic = m.group(1).strip()
            sev, note = classify_license(lic)
            if sev in {"HIGH", "REVIEW"}:
                add_finding(
                    audit, sev, "source-license-header", p.name,
                    f"Source file declares SPDX license {lic}. {note}",
                    rel(p, root), evidence=m.group(0),
                    remediation="Verify the file's provenance and comply with its declared license."
                )

        # URLs are provenance hints only. They do not create a REVIEW finding.
        for u in URL_RE.findall(text):
            clean = u.rstrip(".,;:")
            if clean in urls_seen:
                continue
            urls_seen.add(clean)
            try:
                host = urlparse(clean).netloc.lower()
            except ValueError:
                continue
            if "github.com" in host or "huggingface.co" in host or "gitlab.com" in host:
                audit.provenance_urls.append({"url": clean, "path": rel(p, root)})

def scan_models(root: Path, audit: Audit, label: str) -> None:
    for p in walk(root, SKIP_DIRS):
        suffix = p.suffix.lower()
        if suffix in MODEL_EXTS:
            try:
                size = p.stat().st_size
            except OSError:
                size = 0
            # .bin is noisy; only treat large .bin as likely model/weights.
            if suffix == ".bin" and size < 5 * 1024 * 1024:
                continue
            item = {
                "path": rel(p, root), "scope": label, "extension": suffix,
                "bytes": size
            }
            audit.models.append(item)
            add_finding(
                audit, "REVIEW", "model-weight", p.name,
                "Potential model/weight file is present in the audited distribution/tree.",
                rel(p, root),
                evidence=f"{size / (1024*1024):.1f} MiB",
                remediation="Confirm the weight/model license permits redistribution and commercial use, or remove it from the package."
            )


def scan_native(root: Path, audit: Audit, label: str) -> None:
    for p in walk(root, SKIP_DIRS):
        suffix = p.suffix.lower()
        is_framework = ".framework" in p.parts
        executable = False
        try:
            executable = p.is_file() and os.access(p, os.X_OK)
        except OSError:
            pass
        if suffix in NATIVE_EXTS or is_framework or executable:
            # Avoid recording scripts as native executables.
            if suffix in SOURCE_EXTS or p.name.endswith((".py", ".sh", ".command")):
                continue
            try:
                size = p.stat().st_size
            except OSError:
                size = 0
            audit.native_files.append({
                "path": rel(p, root), "scope": label, "bytes": size
            })


def locate_ffmpeg(search_roots: Sequence[Path], explicit: Optional[str]) -> Optional[Path]:
    if explicit:
        p = Path(explicit).expanduser()
        return p if p.exists() else None
    candidates: List[Path] = []
    names = {"ffmpeg", "ffmpeg.exe"}
    for root in search_roots:
        if not root or not root.exists():
            continue
        for p in walk(root, SKIP_DIRS):
            if p.name.lower() in names:
                candidates.append(p)
    if candidates:
        # Prefer paths that look packaged/vendorized.
        candidates.sort(key=lambda p: (
            0 if any(x in str(p).lower() for x in ("resources", "vendor", "bin", "app")) else 1,
            len(str(p))
        ))
        return candidates[0]
    sys_ffmpeg = shutil.which("ffmpeg")
    return Path(sys_ffmpeg) if sys_ffmpeg else None


def ffmpeg_audit(path: Optional[Path], audit: Audit, root: Path) -> None:
    if not path:
        add_finding(audit, "UNKNOWN", "ffmpeg", "FFmpeg",
                    "No FFmpeg executable was found. The shipped FFmpeg build configuration was not audited.",
                    remediation="Pass --ffmpeg /path/to/the/exact/ffmpeg/bundled/with/Videobeaux.")
        return

    rc1, out1, err1 = run([str(path), "-version"], timeout=15)
    rc2, out2, err2 = run([str(path), "-buildconf"], timeout=15)
    text = (out1 + "\n" + err1 + "\n" + out2 + "\n" + err2).strip()
    audit.ffmpeg = {
        "path": str(path),
        "version_output": (out1 + err1).strip(),
        "buildconf_output": (out2 + err2).strip(),
        "returncodes": [rc1, rc2],
    }
    if rc1 != 0:
        add_finding(audit, "HIGH", "ffmpeg", "FFmpeg executable",
                    "Found FFmpeg but could not execute it.", str(path),
                    evidence=(err1 or out1)[:1000],
                    remediation="Audit the exact distributable FFmpeg binary on its target platform.")
        return

    lower = text.lower()
    for flag in FFMPEG_NONFREE_FLAGS:
        if flag in lower:
            add_finding(
                audit, "HIGH", "ffmpeg-build", flag,
                "FFmpeg was built with --enable-nonfree. FFmpeg describes nonfree builds as not redistributable.",
                str(path), evidence=flag,
                remediation="STOP commercial redistribution of this binary until the build is replaced/reviewed."
            )

    if "--enable-gpl" in lower:
        add_finding(
            audit, "REVIEW", "ffmpeg-build", "--enable-gpl",
            "The bundled FFmpeg build has GPL components enabled.",
            str(path), evidence="--enable-gpl",
            remediation="Review GPL compliance, corresponding-source obligations, notices, and how Videobeaux invokes/distributes FFmpeg."
        )
    else:
        add_finding(
            audit, "LOW", "ffmpeg-build", "GPL flag",
            "No --enable-gpl flag was detected in this FFmpeg build configuration.",
            str(path)
        )

    for lib, note in FFMPEG_GPL_LIBS.items():
        flag = f"--enable-{lib}"
        if flag in lower and note:
            add_finding(audit, "REVIEW", "ffmpeg-library", lib,
                        note, str(path), evidence=flag,
                        remediation="Verify this library's exact license and FFmpeg's resulting distribution obligations.")

    # Preserve all --enable-* flags for review.
    flags = sorted(set(re.findall(r'--(?:enable|disable)-[A-Za-z0-9_\-]+', text)))
    audit.ffmpeg["configure_flags"] = flags


def app_metadata(app: Path, audit: Audit) -> None:
    plist = app / "Contents" / "Info.plist"
    if plist.exists():
        try:
            with plist.open("rb") as f:
                d = plistlib.load(f)
            audit.metadata["app_bundle"] = {
                "name": d.get("CFBundleName"),
                "identifier": d.get("CFBundleIdentifier"),
                "version": d.get("CFBundleShortVersionString"),
                "build": d.get("CFBundleVersion"),
            }
        except Exception as e:
            add_finding(audit, "UNKNOWN", "app", "Info.plist",
                        f"Could not parse app metadata: {e}", str(plist))


def severity_rank(s: str) -> int:
    return {"HIGH": 5, "REVIEW": 4, "UNKNOWN": 3, "NOTICE": 2, "LOW": 1}.get(s, 3)


def dedupe_findings(findings: List[Finding]) -> List[Finding]:
    seen = set()
    out = []
    for f in findings:
        key = (f.severity, f.category, f.subject, f.message, f.path)
        if key not in seen:
            seen.add(key)
            out.append(f)
    return sorted(out, key=lambda f: (-severity_rank(f.severity), f.category.lower(), f.subject.lower()))


def summarize(audit: Audit) -> Dict[str, Any]:
    counts = Counter(f.severity for f in audit.findings)
    comp_counts = Counter(c.severity for c in audit.components)
    worst = "LOW"
    for sev in ("HIGH", "REVIEW", "UNKNOWN", "NOTICE", "LOW"):
        if counts.get(sev):
            worst = sev
            break
    return {
        "overall": worst,
        "findings": dict(counts),
        "components": dict(comp_counts),
        "component_count": len(audit.components),
        "model_file_count": len(audit.models),
        "native_file_count": len(audit.native_files),
    }


def write_json(audit: Audit, path: Path) -> None:
    data = asdict(audit)
    data["summary"] = summarize(audit)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def esc(x: Any) -> str:
    return html.escape(str(x or ""))


def write_html(audit: Audit, path: Path) -> None:
    summary = summarize(audit)
    findings_rows = []
    for f in audit.findings:
        findings_rows.append(
            "<tr>"
            f"<td><strong>{esc(f.severity)}</strong></td>"
            f"<td>{esc(f.category)}</td><td>{esc(f.subject)}</td>"
            f"<td>{esc(f.message)}"
            + (f"<br><small><b>Evidence:</b> {esc(f.evidence)}</small>" if f.evidence else "")
            + (f"<br><small><b>Action:</b> {esc(f.remediation)}</small>" if f.remediation else "")
            + "</td>"
            f"<td><code>{esc(f.path)}</code></td></tr>"
        )

    comp_rows = []
    for c in sorted(audit.components, key=lambda x: (-severity_rank(x.severity), x.ecosystem, x.name.lower())):
        comp_rows.append(
            "<tr>"
            f"<td>{esc(c.severity)}</td><td>{esc(c.ecosystem)}</td>"
            f"<td>{esc(c.name)}</td><td>{esc(c.version)}</td>"
            f"<td>{esc(c.license or 'UNKNOWN')}</td><td>{esc(c.path)}</td>"
            "</tr>"
        )

    counts = summary["findings"]
    body = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Videobeaux License Audit</title>
<style>
body{{font-family:system-ui,-apple-system,sans-serif;max-width:1400px;margin:40px auto;padding:0 24px;line-height:1.45}}
h1,h2{{margin-top:1.5em}} .warning{{padding:16px;border:2px solid currentColor}}
.cards{{display:flex;gap:12px;flex-wrap:wrap}} .card{{border:1px solid #aaa;padding:12px 18px;min-width:120px}}
table{{border-collapse:collapse;width:100%;font-size:14px}} th,td{{border:1px solid #bbb;padding:8px;text-align:left;vertical-align:top}}
th{{position:sticky;top:0;background:Canvas}} code{{overflow-wrap:anywhere}} small{{opacity:.8}}
</style></head><body>
<h1>Videobeaux Commercial Redistribution / License Health Audit</h1>
<div class="warning"><strong>Engineering triage only — not legal advice or legal clearance.</strong>
A LOW/NOTICE result means this scanner found no obvious blocker; it does not establish legal eligibility.</div>
<p><b>Generated:</b> {esc(audit.generated_at)}<br>
<b>Source root:</b> <code>{esc(audit.root)}</code><br>
<b>Packaged app/directory:</b> <code>{esc(audit.app or 'not supplied')}</code><br>
<b>Overall triage status:</b> <strong>{esc(summary['overall'])}</strong></p>
<div class="cards">
<div class="card"><b>HIGH</b><br>{counts.get('HIGH',0)}</div>
<div class="card"><b>REVIEW</b><br>{counts.get('REVIEW',0)}</div>
<div class="card"><b>UNKNOWN</b><br>{counts.get('UNKNOWN',0)}</div>
<div class="card"><b>NOTICE</b><br>{counts.get('NOTICE',0)}</div>
<div class="card"><b>LOW</b><br>{counts.get('LOW',0)}</div>
<div class="card"><b>Components</b><br>{len(audit.components)}</div>
</div>
<h2>Priority findings</h2>
<table><thead><tr><th>Severity</th><th>Category</th><th>Subject</th><th>Finding / action</th><th>Path</th></tr></thead>
<tbody>{''.join(findings_rows) or '<tr><td colspan="5">No findings recorded.</td></tr>'}</tbody></table>
<h2>Dependency inventory</h2>
<table><thead><tr><th>Status</th><th>Ecosystem</th><th>Package</th><th>Version</th><th>License</th><th>Path</th></tr></thead>
<tbody>{''.join(comp_rows) or '<tr><td colspan="6">No components inventoried.</td></tr>'}</tbody></table>
<h2>FFmpeg</h2>
<pre>{esc(json.dumps(audit.ffmpeg, indent=2))}</pre>
<h2>Potential bundled models / weights</h2>
<pre>{esc(json.dumps(audit.models, indent=2))}</pre>
<h2>Native/binary inventory</h2>
<p>{len(audit.native_files)} potential native/binary files detected. Full list is in the JSON report.</p>
<h2>Source provenance URLs</h2>
<pre>{esc(json.dumps(audit.provenance_urls[:500], indent=2))}</pre>
<h2>Interpretation</h2>
<p><b>HIGH:</b> likely release blocker until manually resolved. <b>REVIEW:</b> obligations/context need review.
<b>UNKNOWN:</b> insufficient license data. <b>NOTICE:</b> generally permissive signal but notices/license text may be required.
<b>LOW:</b> no obvious concern detected for that specific check.</p>
</body></html>"""
    path.write_text(body, encoding="utf-8")


def write_notices(audit: Audit, path: Path) -> None:
    lines = [
        "VIDEOBEAUX — DRAFT THIRD-PARTY SOFTWARE NOTICES",
        "=" * 54,
        "",
        "AUTOGENERATED DRAFT. VERIFY AGAINST CANONICAL LICENSE FILES BEFORE RELEASE.",
        "This file is an inventory aid and is not a substitute for the actual",
        "license/copyright/NOTICE texts required by each dependency.",
        "",
    ]
    by_key = {}
    for c in audit.components:
        key = (c.ecosystem, c.name.lower(), c.version)
        by_key[key] = c
    for c in sorted(by_key.values(), key=lambda x: (x.ecosystem, x.name.lower())):
        lines.extend([
            c.name,
            "-" * max(3, len(c.name)),
            f"Version: {c.version or 'unknown'}",
            f"Ecosystem: {c.ecosystem}",
            f"Detected license: {c.license or 'UNKNOWN — MANUAL REVIEW REQUIRED'}",
        ])
        if c.source:
            lines.append(f"Project/source metadata: {c.source}")
        if c.path:
            lines.append(f"Detected at: {c.path}")
        lines.extend(["", ""])
    if audit.ffmpeg:
        lines.extend([
            "FFmpeg", "------",
            f"Audited executable: {audit.ffmpeg.get('path','')}",
            "IMPORTANT: Insert the canonical FFmpeg license/copyright notices",
            "appropriate to the exact build distributed with Videobeaux.",
            "", ""
        ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Audit source + packaged app for commercial redistribution/license-health risks."
    )
    ap.add_argument("root", nargs="?", default=".", help="Repository root (default: current directory)")
    ap.add_argument("--app", help="Packaged .app or distribution directory to audit")
    ap.add_argument("--ffmpeg", help="Exact FFmpeg executable to interrogate")
    ap.add_argument(
        "--ignore-models", action="store_true",
        help="Do not scan/report model or weight files. Useful when models are user-downloaded and intentionally outside the shipped product audit."
    )
    ap.add_argument("--html", default="license-audit.html", help="HTML output path")
    ap.add_argument("--json", dest="json_out", default="license-audit.json", help="JSON output path")
    ap.add_argument("--notices", default="THIRD_PARTY_NOTICES.draft.txt", help="Draft notices output path")
    ap.add_argument("--fail-on", choices=["high", "review", "unknown", "never"], default="high",
                    help="CI exit threshold (default: high)")
    args = ap.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        print(f"ERROR: root does not exist: {root}", file=sys.stderr)
        return 2

    app = Path(args.app).expanduser().resolve() if args.app else None
    if app and not app.exists():
        print(f"ERROR: --app does not exist: {app}", file=sys.stderr)
        return 2

    audit = Audit(
        generated_at=now_iso(), tool_version=VERSION, root=str(root),
        app=str(app) if app else ""
    )

    print("[1/7] Inventorying project/npm dependencies...")
    npm_inventory(root, audit)

    print("[2/7] Inventorying current Python environment...")
    python_inventory(root, audit)

    print("[3/7] Scanning source provenance/license signals...")
    find_license_files(root, audit, source_only=True)
    source_provenance_scan(root, audit)

    if args.ignore_models:
        print("[4/7] Model/weight scan skipped (--ignore-models).")
        audit.metadata["model_scan"] = "ignored by --ignore-models"
    else:
        print("[4/7] Scanning source tree for accidentally bundled model weights...")
        scan_models(root, audit, "source")

    search_roots = [root]
    if app:
        print("[5/7] Auditing packaged application/distribution...")
        search_roots.insert(0, app)
        app_metadata(app, audit)
        if not args.ignore_models:
            scan_models(app, audit, "packaged")
        scan_native(app, audit, "packaged")
        # License files in the app matter for notice compliance.
        packaged_license_files = []
        for p in walk(app, SKIP_DIRS):
            if p.name.lower() in LICENSE_NAMES or p.name.lower().startswith(("license.", "copying.", "notice.")):
                packaged_license_files.append(str(p))
        audit.metadata["packaged_license_files"] = packaged_license_files
        if not packaged_license_files:
            add_finding(
                audit, "REVIEW", "notices", "Packaged third-party notices",
                "No obvious LICENSE/COPYING/NOTICE files were detected in the packaged application.",
                str(app),
                remediation="Ensure required third-party license texts/notices are shipped in the app and/or installer."
            )
    else:
        print("[5/7] No --app supplied; packaged artifact checks skipped.")
        add_finding(
            audit, "UNKNOWN", "distribution", "Packaged artifact",
            "No packaged app/directory was supplied, so the actual customer-delivered artifact was not audited.",
            remediation="Re-run with --app pointing at the exact release .app/directory."
        )

    print("[6/7] Interrogating FFmpeg build...")
    ffmpeg_path = locate_ffmpeg(search_roots, args.ffmpeg)
    ffmpeg_audit(ffmpeg_path, audit, root)

    # Useful general checks.
    if not audit.license_files:
        add_finding(audit, "REVIEW", "project-license", "Repository license",
                    "No obvious top-level/source LICENSE/COPYING/NOTICE file was detected.",
                    remediation="Add/verify Videobeaux's own license and third-party notices.")

    if audit.provenance_urls:
        audit.metadata["external_provenance_url_count"] = len(audit.provenance_urls)

    audit.findings = dedupe_findings(audit.findings)

    print("[7/7] Writing reports...")
    html_path = Path(args.html).expanduser().resolve()
    json_path = Path(args.json_out).expanduser().resolve()
    notices_path = Path(args.notices).expanduser().resolve()
    for p in (html_path, json_path, notices_path):
        p.parent.mkdir(parents=True, exist_ok=True)
    write_json(audit, json_path)
    write_html(audit, html_path)
    write_notices(audit, notices_path)

    s = summarize(audit)
    print()
    print("=== LICENSE HEALTH SUMMARY ===")
    print(f"Overall: {s['overall']}")
    for sev in ("HIGH", "REVIEW", "UNKNOWN", "NOTICE", "LOW"):
        print(f"{sev:7}: {s['findings'].get(sev, 0)}")
    print(f"Components inventoried: {s['component_count']}")
    print(f"Potential model files:   {s['model_file_count']}")
    print(f"Native/binary files:     {s['native_file_count']}")
    print()
    print(f"HTML:    {html_path}")
    print(f"JSON:    {json_path}")
    print(f"Notices: {notices_path}")
    print()
    print("Reminder: this is conservative engineering triage, not legal clearance.")

    threshold = args.fail_on
    if threshold == "never":
        return 0
    ranks = {"unknown": 3, "review": 4, "high": 5}
    cutoff = ranks[threshold]
    worst = max((severity_rank(f.severity) for f in audit.findings), default=1)
    return 1 if worst >= cutoff else 0


if __name__ == "__main__":
    raise SystemExit(main())
