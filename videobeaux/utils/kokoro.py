"""Locating kokoro-tts (the offline narration voice) and its model files."""
from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path

MODEL_NAME = "kokoro-v1.0.onnx"
VOICES_NAME = "voices-v1.0.bin"

_REPO_ROOT = Path(__file__).resolve().parents[2]


def models_dir() -> Path:
    """The GUI sets VIDEOBEAUX_MODELS_DIR to the real models folder (dev repo or user data dir)."""
    env = os.environ.get("VIDEOBEAUX_MODELS_DIR")
    return Path(env) if env else _REPO_ROOT / "models"


def model_paths() -> tuple[Path, Path]:
    base = models_dir() / "kokoro-tts"
    return base / MODEL_NAME, base / VOICES_NAME


def models_present() -> bool:
    m, v = model_paths()
    return m.exists() and v.exists()


def kokoro_command() -> list[str] | None:
    """
    Command prefix that runs kokoro-tts, or None if it isn't available.

    Prefers the package installed in *this* interpreter (the packaged app's
    bundled Python ships it) via `python -m kokoro_tts` — a console-script
    installed into a relocatable bundle has a shebang pointing at the build
    machine — then falls back to a `kokoro-tts` on PATH.
    """
    if importlib.util.find_spec("kokoro_tts") is not None:
        return [sys.executable, "-m", "kokoro_tts"]
    exe = shutil.which("kokoro-tts")
    return [exe] if exe else None


SETUP_HINT = "Open ⚙ Setup in the app → Optional features → Narration voice."
