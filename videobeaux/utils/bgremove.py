"""
Background removal helpers: the optional ONNX models (U²-Net family) and the no-download "static camera"
background plate. Models are opt-in downloads kept under <models dir>/bgremove/.

    python -m videobeaux.utils.bgremove u2netp          # download the small model from the command line
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

import numpy as np

from videobeaux.utils.kokoro import models_dir

_BASE = "https://github.com/danielgatis/rembg/releases/download/v0.0.0"

# id → (file, url, exact size in bytes, label)
MODELS = {
    "u2netp": ("u2netp.onnx", f"{_BASE}/u2netp.onnx", 4_574_861, "fast, general (U²-Net-P, ~5 MB)"),
    "u2net_human_seg": ("u2net_human_seg.onnx", f"{_BASE}/u2net_human_seg.onnx", 175_997_641,
                        "best for people (U²-Net human, ~170 MB)"),
}
INPUT_SIZE = 320
MEAN = np.array([0.485, 0.456, 0.406], np.float32)
STD = np.array([0.229, 0.224, 0.225], np.float32)


def model_file(model_id: str) -> Path:
    return models_dir() / "bgremove" / MODELS[model_id][0]


def have_model(model_id: str) -> bool:
    p = model_file(model_id)
    return p.exists() and p.stat().st_size == MODELS[model_id][2]


def missing_message(model_id: str) -> str:
    _, _, size, label = MODELS[model_id]
    return (f"❌ The background-removal model ({label}) hasn't been downloaded yet. Open Setup → "
            f"Local AI features and tick it (one-time, ~{size / 1e6:.0f} MB, then it works offline), or run:\n"
            f"   python -m videobeaux.utils.bgremove {model_id}")


def download_model(model_id: str, progress=print) -> Path:
    file, url, size, _ = MODELS[model_id]
    dest = model_file(model_id)
    if have_model(model_id):
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    with urllib.request.urlopen(url, timeout=60) as r, open(tmp, "wb") as f:
        got = 0
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
            got += len(chunk)
            progress(f"  {got / 1e6:.1f} / {size / 1e6:.1f} MB")
    if tmp.stat().st_size != size:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Download of {file} was incomplete — try again.")
    tmp.replace(dest)
    return dest


class OnnxMatter:
    """Runs a U²-Net style model: RGB frame → soft foreground matte (float 0..1, same size as the frame)."""

    def __init__(self, model_id: str):
        if not have_model(model_id):
            raise SystemExit(missing_message(model_id))
        try:
            import onnxruntime as ort
        except ImportError:
            raise SystemExit("❌ This engine needs onnxruntime (pip install onnxruntime).")
        self.sess = ort.InferenceSession(str(model_file(model_id)), providers=["CPUExecutionProvider"])
        self.input = self.sess.get_inputs()[0].name

    def __call__(self, cv2, frame_rgb: np.ndarray) -> np.ndarray:
        h, w = frame_rgb.shape[:2]
        small = cv2.resize(frame_rgb, (INPUT_SIZE, INPUT_SIZE), interpolation=cv2.INTER_AREA).astype(np.float32)
        small = small / max(float(small.max()), 1e-6)
        x = ((small - MEAN) / STD).transpose(2, 0, 1)[None]
        pred = self.sess.run(None, {self.input: x.astype(np.float32)})[0][0, 0]
        lo, hi = float(pred.min()), float(pred.max())
        pred = (pred - lo) / max(hi - lo, 1e-6)
        return cv2.resize(pred, (w, h), interpolation=cv2.INTER_LINEAR)


def static_plate(path, samples: int = 25, width: int = 480) -> np.ndarray:
    """Per-pixel median of frames sampled across the clip: the empty scene, if the subject moves around."""
    from videobeaux.utils.frame_pipe import iter_frames, probe_video
    info = probe_video(path)
    total = max(1, info.frames)
    keep = set(np.linspace(0, total - 1, min(samples, total)).astype(int).tolist())
    frames = [f for i, f in iter_frames(path, width=width) if i in keep]
    if not frames:
        raise RuntimeError("Couldn't read frames to build the background plate.")
    return np.median(np.stack(frames), axis=0).astype(np.uint8)


def plate_matte(cv2, frame_rgb: np.ndarray, plate_small: np.ndarray, sensitivity: float, softness: float = 18.0) -> np.ndarray:
    """Soft matte (0..1): how much each pixel differs from the clean plate."""
    h, w = frame_rgb.shape[:2]
    ph, pw = plate_small.shape[:2]
    work = cv2.resize(frame_rgb, (pw, ph), interpolation=cv2.INTER_AREA)
    diff = np.abs(work.astype(np.int16) - plate_small.astype(np.int16)).max(axis=2).astype(np.float32)
    diff = cv2.GaussianBlur(diff, (0, 0), 1.5)
    m = np.clip((diff - sensitivity) / max(softness, 1.0), 0.0, 1.0)
    return cv2.resize(m, (w, h), interpolation=cv2.INTER_LINEAR)


if __name__ == "__main__":
    ids = sys.argv[1:] or ["u2netp"]
    for mid in ids:
        if mid not in MODELS:
            sys.exit(f"Unknown model {mid!r}. Choose from: {', '.join(MODELS)}")
        print(f"Downloading {mid} …")
        print(download_model(mid))
