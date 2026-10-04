"""
Shared runner for the single-purpose photo-booth programs (Negative, Pixelate, VHS Camcorder, ...).

A program module declares its own parameters (`Param`) and a `build(args)` function that returns an
effect — a callable `fn(bgr_frame, ctx)` (optionally with `reset()`) from videobeaux.utils.booth_filters.
`make_program` turns that into the `register_arguments` / `run` / `GUI_METADATA` trio the CLI and the
GUI discovery expect, and the runner handles everything else: working at a consistent detail size,
face tracking when asked, the Amount blend, and the streaming encode.

OpenCV is only imported inside run(), so GUI discovery works even where OpenCV is missing.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from videobeaux.utils.cv import hex_to_rgb, require_cv2
from videobeaux.utils.frame_pipe import process_video


@dataclass
class Param:
    name: str
    kind: str                    # int | float | bool | select | color | text
    default: object
    label: str
    help: str = ""
    min: float | None = None
    max: float | None = None
    choices: list = field(default_factory=list)


COMMON = [
    Param("amount", "float", 1.0, "Amount", "1 = full effect; lower values blend the original back in.", 0, 1),
    Param("detail", "int", 720, "Detail (px)",
          "The effect is applied at this size on the short side, then scaled back up — keeps the look consistent "
          "on any resolution and is faster. 0 = full resolution.", 0, 2160),
]


def _add(parser, p: Param):
    flag = f"--{p.name}"
    if p.kind == "bool":
        parser.add_argument(flag, action="store_true", help=p.help)
    elif p.kind == "select":
        parser.add_argument(flag, choices=p.choices, default=p.default, help=p.help)
    elif p.kind == "int":
        parser.add_argument(flag, type=int, default=p.default, help=p.help)
    elif p.kind == "float":
        parser.add_argument(flag, type=float, default=p.default, help=p.help)
    else:                                         # color / text
        parser.add_argument(flag, type=str, default=p.default, help=p.help)


def _meta(p: Param) -> dict:
    m = {"label": p.label}
    if p.help:
        m["help"] = p.help
    if p.kind == "color":
        m["type"] = "color"
    if p.kind == "select":
        m.update(type="select", choices=list(p.choices), default=p.default)
    if p.min is not None:
        m["min"] = p.min
    if p.max is not None:
        m["max"] = p.max
    return m


def make_program(description: str, params: list, build, *, faces=False, eyes=False):
    """
    Returns (register_arguments, run, GUI_METADATA).
      build(args) -> effect callable fn(bgr, ctx);   faces/eyes: the effect needs face boxes (and eye points).
    """
    all_params = list(params) + COMMON

    def register_arguments(parser):
        parser.description = description
        for p in all_params:
            _add(parser, p)
        parser.add_argument("--seed", type=int, default=0,
                            help="Seed for the random parts (0 = different every run).")
        parser.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")

    def run(args):
        run_effect(args, build, faces=faces, eyes=eyes)

    gui = {"args": {p.name: _meta(p) for p in all_params}}
    gui["args"]["seed"] = {"hidden": True}
    gui["args"]["crf"] = {"hidden": True}
    return register_arguments, run, gui


def _two_arg(fn):
    """Accept both fn(img) and fn(img, ctx) effects."""
    import inspect
    try:
        n = len([p for p in inspect.signature(fn).parameters.values()
                 if p.default is p.empty and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)])
    except (TypeError, ValueError):
        return fn
    if n >= 2 or hasattr(fn, "needs_faces"):
        return fn

    def wrapped(img, ctx):
        return fn(img)
    wrapped.reset = getattr(fn, "reset", lambda: None)
    return wrapped


def eyes_for(face):
    """Approximate eye centres/radius from a face box (the tracker only reports the box)."""
    x, y, w, h = face
    r = 0.11 * w
    return [(x + 0.31 * w, y + 0.40 * h, r), (x + 0.69 * w, y + 0.40 * h, r)]


def run_effect(args, build, *, faces=False, eyes=False, label=None):
    cv2 = require_cv2()
    from videobeaux.utils import booth_filters
    from videobeaux.utils.booth_filters import Ctx

    booth_filters.seed(getattr(args, "seed", 0))
    fn = _two_arg(build(args))
    reset = getattr(fn, "reset", None)
    if reset:
        reset()
    amount = min(1.0, max(0.0, getattr(args, "amount", 1.0)))
    detail = getattr(args, "detail", 720)
    if label:
        print(f"ℹ️  Filter: {label}", flush=True)

    st = {"tracker": None, "dt": 1 / 30, "size": None}

    def setup(info):
        st["dt"] = 1.0 / max(1.0, info.fps)
        short = min(info.width, info.height)
        scale = detail / short if detail and short > detail else 1.0
        if scale < 1.0:
            st["size"] = (max(8, int(round(info.width * scale))), max(8, int(round(info.height * scale))))
        if faces or eyes:
            from videobeaux.utils.face_tracking import FaceTracker
            w, h = st["size"] or (info.width, info.height)
            st["tracker"] = FaceTracker(w, h)

    def frame_fn(frame, i, t):
        size = st["size"]
        work = cv2.resize(frame, size, interpolation=cv2.INTER_AREA) if size else frame
        boxes, eye_pts = [], []
        if st["tracker"] is not None:
            boxes = [tr.box for tr in st["tracker"].update(work, i)]
            if eyes:
                eye_pts = [eyes_for(b) for b in boxes]
        bgr = np.ascontiguousarray(work[..., ::-1])
        out = fn(bgr, Ctx(t=t, dt=st["dt"], faces=boxes, eyes=eye_pts))
        out = np.ascontiguousarray(out[..., ::-1])
        if out.shape != work.shape:
            out = cv2.resize(out, (work.shape[1], work.shape[0]), interpolation=cv2.INTER_LINEAR)
        if size:
            out = cv2.resize(out, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_LINEAR)
        if amount < 1.0:
            out = cv2.addWeighted(frame, 1.0 - amount, out, amount, 0)
        return out

    stats = process_video(args.input, args.output, frame_fn, crf=getattr(args, "crf", 18),
                          force=bool(getattr(args, "force", False)), setup=setup)
    print(f"✅ {stats['frames']} frames in {stats['seconds']:.1f}s")


def rgb(hex_text, default):
    return hex_to_rgb(hex_text, default)
