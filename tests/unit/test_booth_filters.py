import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
# Never pick up the developer's own ~/.videobeaux/filters while testing the built-ins.
os.environ["VIDEOBEAUX_USER_FILTERS"] = tempfile.mkdtemp()

try:
    import cv2  # noqa: F401
    HAVE_CV2 = True
except ImportError:
    HAVE_CV2 = False


@unittest.skipUnless(HAVE_CV2, "needs OpenCV")
class BoothFilters(unittest.TestCase):
    def test_labels_match_registry(self):
        from videobeaux.utils.booth_filters import build_filters
        from videobeaux.utils.booth_labels import BUILTIN_LABELS
        self.assertEqual(list(build_filters()), BUILTIN_LABELS)

    def test_every_filter_returns_same_shape_uint8(self):
        import numpy as np
        from videobeaux.utils.booth_filters import Ctx, build_filters
        rng = np.random.default_rng(3)
        img = (rng.random((144, 192, 3)) * 255).astype(np.uint8)
        ctx = Ctx(t=1.0, faces=[(60, 30, 50, 60), (120, 40, 40, 50)],
                  eyes=[[(75, 50, 5), (95, 50, 5)], [(130, 55, 4), (145, 55, 4)]])
        for label, effect in build_filters().items():
            for _ in range(3):                       # stateful filters need a few frames
                out = effect(img.copy(), ctx)
            self.assertEqual(out.shape, img.shape, label)
            self.assertEqual(out.dtype, np.uint8, label)

    def test_negative_inverts(self):
        import numpy as np
        from videobeaux.utils.booth_filters import Ctx, build_filters
        img = np.full((20, 20, 3), 40, np.uint8)
        out = build_filters()["Classic · Negative"](img, Ctx())
        self.assertTrue((out == 215).all())

    def test_user_filter_is_discovered(self):
        import numpy as np
        d = Path(os.environ["VIDEOBEAUX_USER_FILTERS"])
        (d / "mine.py").write_text(
            "from videobeaux.utils.booth_filters import register\n"
            "@register('My filters', 'Zero')\n"
            "def zero(img, ctx):\n    return img * 0\n")
        from videobeaux.utils import booth_filters
        booth_filters.load_user_filters._done = False
        filters = booth_filters.build_filters()
        self.assertIn("My filters · Zero", filters)
        self.assertEqual(int(filters["My filters · Zero"](np.ones((4, 4, 3), np.uint8), booth_filters.Ctx()).sum()), 0)


if __name__ == "__main__":
    unittest.main()
