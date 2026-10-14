"""
Two-pass "matte program" flow shared by Remove Background, Topobeaux, Shape Synth and Stackadelic:

  pass 1  a per-frame float matte (0..1, same size as the frame) is rendered to a temporary grayscale video;
  pass 2  `keying.run_key(matte_path=...)` composites the source over a color / image / video, or exports it with
          a real alpha channel (transparent WebM / MOV), with the shared shrink / feather / view controls.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Callable, Optional, Sequence

import numpy as np

from videobeaux.utils import keying
from videobeaux.utils.frame_pipe import process_video


def matte_to_frame(m: np.ndarray) -> np.ndarray:
    """float 0..1 (H, W) → uint8 RGB gray frame."""
    g = (np.clip(m, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)
    return np.dstack([g, g, g])


def run_matte_program(args, matte_fn: Callable, *, detail: Optional[int] = None,
                      extra_inputs: Optional[Sequence[str]] = None, setup=None) -> None:
    """
    matte_fn(frame, i, t) → float matte, or (frame, i, t, extras) when `extra_inputs` are given.
    `args` must carry the keying common arguments (see keying.add_common_arguments).
    """
    tmp = Path(tempfile.mkdtemp(prefix="vb_matte_"))
    try:
        matte = tmp / "matte.mp4"

        if extra_inputs:
            def frame_fn(frame, i, t, extras):
                return matte_to_frame(matte_fn(frame, i, t, extras))
        else:
            def frame_fn(frame, i, t):
                return matte_to_frame(matte_fn(frame, i, t))

        print("ℹ️  Rendering the matte…", flush=True)
        process_video(args.input, matte, frame_fn, crf=12, force=True, audio=False, setup=setup,
                      max_width=detail or None, extra_inputs=list(extra_inputs or []) or None)
        print("ℹ️  Compositing…", flush=True)
        keying.run_key(args, "", matte_path=str(matte))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
