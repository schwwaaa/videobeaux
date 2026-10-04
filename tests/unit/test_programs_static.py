"""Static guards over videobeaux/programs/*.py (no ffmpeg needed).

    python -m unittest discover -s tests/unit -v
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
PROGRAMS = sorted((ROOT / "videobeaux" / "programs").glob("*.py"))


class AudioHandling(unittest.TestCase):
    def test_audio_is_never_mapped_unconditionally(self):
        """`-map 0:a` fails on silent clips (phone videos, screen recordings): it must be `0:a?`."""
        bad = []
        for p in PROGRAMS:
            for m in re.finditer(r'"-map",\s*"(0:a(?::\d+)?)"', p.read_text(encoding="utf-8")):
                bad.append(f"{p.name}: -map {m.group(1)}")
        self.assertEqual(bad, [])

    def test_audio_filter_graphs_ensure_a_track_first(self):
        """Programs whose filter graphs reference [N:a] must call ensure_audio on their inputs."""
        missing = []
        for p in PROGRAMS:
            src = p.read_text(encoding="utf-8")
            if re.search(r'\[\d:a\]', src) and "ensure_audio(" not in src:
                missing.append(p.name)
        self.assertEqual(missing, [])


def _reference_sort(arr, threshold, vertical):
    import numpy as np
    work = arr.transpose(1, 0, 2) if vertical else arr
    h, w, _ = work.shape
    gray = work[:, :, :3].mean(axis=2)
    mask = gray > threshold
    out = work.copy()
    for y in range(h):
        x = 0
        while x < w:
            if not mask[y, x]:
                x += 1
                continue
            x2 = x
            while x2 < w and mask[y, x2]:
                x2 += 1
            out[y, x:x2] = work[y, x:x2][np.argsort(gray[y, x:x2], kind="stable")]
            x = x2
    return out.transpose(1, 0, 2) if vertical else out



class PixelSort(unittest.TestCase):
    def test_vectorized_sort_matches_row_by_row_reference(self):
        import numpy as np
        from videobeaux.programs.pixel_sort import pixel_sort_frame

        rng = np.random.default_rng(5)
        for shape in [(40, 57, 3), (33, 64, 3)]:
            for th in (60, 127, 200):
                for vert in (False, True):
                    a = (rng.random(shape) * 255).astype(np.uint8)
                    self.assertTrue(np.array_equal(_reference_sort(a, th, vert), pixel_sort_frame(a, th, vert)),
                                    (shape, th, vert))

    def test_large_smooth_frame_actually_sorts(self):
        # Regression: on numpy 2.2.x + Python 3.14 frames >= 256 KiB came back unchanged
        # (silent in-place clobbering), which tiny random test frames never caught.
        import numpy as np
        from videobeaux.programs.pixel_sort import pixel_sort_frame
        h, w = 480, 640
        x = np.linspace(0, 255, w, dtype=np.float32)[None, :]
        y = np.linspace(0, 255, h, dtype=np.float32)[:, None]
        noise = np.random.default_rng(1).random((h, w)).astype(np.float32) * 60
        frame = np.stack([x + 0 * y, y + 0 * x, (x + y) / 2 + noise], axis=2).clip(0, 255).astype(np.uint8)
        out = pixel_sort_frame(frame, 100, False)
        self.assertGreater(float((out != frame).mean()), 0.2)
        self.assertTrue(np.array_equal(out, _reference_sort(frame, 100, False)))
        self.assertTrue(np.array_equal(pixel_sort_frame(frame, 100, True), _reference_sort(frame, 100, True)))


class NumpySanity(unittest.TestCase):
    def test_large_array_expressions_are_not_clobbered(self):
        from videobeaux.utils.numpy_check import numpy_is_sane
        self.assertTrue(numpy_is_sane(), "numpy miscomputes large arrays here — pin numpy 2.3.2+ on Python 3.14")


if __name__ == "__main__":
    unittest.main()
