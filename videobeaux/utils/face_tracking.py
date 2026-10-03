"""
Face detection + lightweight multi-face tracking on top of OpenCV.

Detection runs every N frames on a downscaled copy (YuNet via cv2.FaceDetectorYN
when the vendored model is present, else the Haar cascade that ships with
OpenCV). Between detections tracks coast on a smoothed constant-velocity
estimate, so overlays move every frame rather than hopping. Detections are
associated to tracks greedily by IoU / centroid distance; unmatched tracks are
held for a few frames and then dropped.

All frames are RGB (H, W, 3) uint8, as produced by videobeaux.utils.frame_pipe.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from videobeaux.utils.cv import hex_to_rgb, require_cv2  # noqa: F401  (hex_to_rgb re-exported)

MODEL_PATH = Path(__file__).resolve().parents[1] / "assets" / "face_detection_yunet_2023mar.onnx"


@dataclass
class Track:
    id: int
    x: float
    y: float
    w: float
    h: float
    score: float = 1.0
    vx: float = 0.0
    vy: float = 0.0
    missed: int = 0                 # detection cycles since last match
    age: int = 0
    trail: deque = field(default_factory=lambda: deque(maxlen=40))

    @property
    def center(self):
        return (self.x + self.w / 2.0, self.y + self.h / 2.0)

    @property
    def box(self):
        return (self.x, self.y, self.w, self.h)


def _iou(a, b) -> float:
    ax2, ay2, bx2, by2 = a[0] + a[2], a[1] + a[3], b[0] + b[2], b[1] + b[3]
    iw = max(0.0, min(ax2, bx2) - max(a[0], b[0]))
    ih = max(0.0, min(ay2, by2) - max(a[1], b[1]))
    inter = iw * ih
    union = a[2] * a[3] + b[2] * b[3] - inter
    return inter / union if union > 0 else 0.0


class FaceTracker:
    def __init__(self, width: int, height: int, *, detect_every: int = 3,
                 min_confidence: float = 0.6, detect_width: int = 640,
                 smoothing: float = 0.5, max_missed: int = 5):
        self.cv2 = require_cv2()
        self.W, self.H = width, height
        self.detect_every = max(1, detect_every)
        self.min_confidence = min_confidence
        self.smoothing = min(0.95, max(0.0, smoothing))
        self.max_missed = max_missed
        self.scale = min(1.0, detect_width / float(width))
        self.dw, self.dh = max(32, int(round(width * self.scale))), max(32, int(round(height * self.scale)))
        self.tracks: list[Track] = []
        self._next_id = 1
        self._last_detect = -10**9
        self.frames_seen = 0
        self.frames_with_faces = 0
        self.max_faces = 0
        self.detector_name = "none"
        self._yunet = None
        self._haar = None
        self._init_detector()

    def _init_detector(self):
        cv2 = self.cv2
        if MODEL_PATH.exists() and hasattr(cv2, "FaceDetectorYN"):
            try:
                self._yunet = cv2.FaceDetectorYN.create(
                    str(MODEL_PATH), "", (self.dw, self.dh), self.min_confidence, 0.3, 5000)
                self.detector_name = "YuNet"
                return
            except Exception:
                self._yunet = None
        cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        if cascade.empty():
            raise SystemExit("❌ No face detector available (YuNet model missing and Haar cascade not found).")
        self._haar = cascade
        self.detector_name = "Haar cascade"

    # ── detection ────────────────────────────────────────────────────────────
    def _detect(self, frame_rgb: np.ndarray) -> list[tuple[float, float, float, float, float]]:
        cv2 = self.cv2
        small = frame_rgb if self.scale == 1.0 else cv2.resize(
            frame_rgb, (self.dw, self.dh), interpolation=cv2.INTER_AREA)
        inv = 1.0 / self.scale
        out = []
        if self._yunet is not None:
            self._yunet.setInputSize((self.dw, self.dh))
            _, faces = self._yunet.detect(np.ascontiguousarray(small[..., ::-1]))   # YuNet wants BGR
            for f in (faces if faces is not None else []):
                out.append((f[0] * inv, f[1] * inv, f[2] * inv, f[3] * inv, float(f[14])))
        else:
            gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
            for (x, y, w, h) in self._haar.detectMultiScale(gray, 1.1, 5, minSize=(30, 30)):
                out.append((x * inv, y * inv, w * inv, h * inv, 1.0))
        return out

    # ── tracking ─────────────────────────────────────────────────────────────
    def _coast(self):
        for t in self.tracks:
            t.x += t.vx
            t.y += t.vy
            t.vx *= 0.9
            t.vy *= 0.9

    def _associate(self, dets, gap_frames: int):
        alpha = 1.0 - self.smoothing
        pairs = []
        for ti, t in enumerate(self.tracks):
            for di, d in enumerate(dets):
                iou = _iou(t.box, d[:4])
                cx, cy = d[0] + d[2] / 2.0, d[1] + d[3] / 2.0
                dist = float(np.hypot(cx - t.center[0], cy - t.center[1]))
                if iou > 0.1 or dist < max(t.w, t.h) * 0.8:
                    pairs.append((iou - dist / (max(t.w, t.h) * 10.0), ti, di))
        pairs.sort(reverse=True)
        used_t, used_d = set(), set()
        for _, ti, di in pairs:
            if ti in used_t or di in used_d:
                continue
            used_t.add(ti)
            used_d.add(di)
            t, d = self.tracks[ti], dets[di]
            ox, oy = t.center
            t.x += (d[0] - t.x) * alpha
            t.y += (d[1] - t.y) * alpha
            t.w += (d[2] - t.w) * alpha
            t.h += (d[3] - t.h) * alpha
            nx, ny = t.center
            gap = max(1, gap_frames)
            t.vx = 0.5 * t.vx + 0.5 * (nx - ox) / gap
            t.vy = 0.5 * t.vy + 0.5 * (ny - oy) / gap
            t.score = d[4]
            t.missed = 0
        for ti, t in enumerate(self.tracks):
            if ti not in used_t:
                t.missed += 1
        for di, d in enumerate(dets):
            if di not in used_d:
                self.tracks.append(Track(self._next_id, d[0], d[1], d[2], d[3], d[4]))
                self._next_id += 1
        self.tracks = [t for t in self.tracks if t.missed <= self.max_missed]

    def update(self, frame_rgb: np.ndarray, index: int) -> list[Track]:
        """Advance one frame; returns the currently visible tracks."""
        self.frames_seen += 1
        if index - self._last_detect >= self.detect_every:
            gap = index - self._last_detect if self._last_detect > -10**8 else self.detect_every
            self._associate(self._detect(frame_rgb), gap)
            self._last_detect = index
        else:
            self._coast()
        visible = [t for t in self.tracks if t.missed <= 1]
        for t in visible:
            t.age += 1
            t.trail.append(t.center)
        if visible:
            self.frames_with_faces += 1
        self.max_faces = max(self.max_faces, len(visible))
        return visible

    def summary(self) -> str:
        return (f"Faces detected in {self.frames_with_faces}/{self.frames_seen} frames "
                f"(up to {self.max_faces} at once, detector: {self.detector_name})")


# ── drawing helpers shared by the face programs ──────────────────────────────

def clamp_box(x, y, w, h, W, H):
    x0, y0 = max(0, int(round(x))), max(0, int(round(y)))
    x1, y1 = min(W, int(round(x + w))), min(H, int(round(y + h)))
    return x0, y0, x1, y1


def padded(track: Track, pad: float):
    return (track.x - track.w * pad, track.y - track.h * pad,
            track.w * (1 + 2 * pad), track.h * (1 + 2 * pad))
