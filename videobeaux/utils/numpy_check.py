"""
Guard against a numpy/Python pairing that silently computes wrong answers.

numpy 2.2.x on Python 3.14 mis-applies its "reuse this temporary array" optimisation
to arrays of 256 KiB or more inside functions: `b = a & (...)` overwrites `a`, and
nothing errors — effects just quietly do nothing or the wrong thing on full-size
video frames. numpy 2.3.2+ fixed it. Small test arrays never trigger it, so check
explicitly with a large one.
"""
import numpy as np

SETUP_HINT = ("Your numpy is broken on this Python version (it silently miscomputes large images). "
              "Open Setup → Repair to update it, or run: pip install -r requirements.txt")


def numpy_is_sane() -> bool:
    h, w = 480, 640                      # 307 200 elements, above the elision threshold
    idx = np.arange(h * w)
    mask = (idx % 7) > 2
    before = mask.copy()
    prev = np.empty(h * w, dtype=bool)
    prev[0] = False
    prev[1:] = mask[:-1]
    _ = mask & (~prev | (idx % w == 0))
    return bool((mask == before).all())


def require_sane_numpy() -> None:
    if not numpy_is_sane():
        raise RuntimeError("❌ " + SETUP_HINT)
