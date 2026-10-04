import argparse
import importlib
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

try:
    import cv2  # noqa: F401
    HAVE_CV2 = True
except ImportError:
    HAVE_CV2 = False


def booth_modules():
    return sorted(p.stem for p in (REPO / "videobeaux" / "programs").glob("*.py")
                  if "booth_runner" in p.read_text() and p.stem != "photobooth")


@unittest.skipUnless(HAVE_CV2, "needs OpenCV")
class BoothPrograms(unittest.TestCase):
    def test_there_are_individual_programs(self):
        self.assertGreaterEqual(len(booth_modules()), 26)

    def test_every_program_builds_and_returns_same_shape_uint8(self):
        import numpy as np
        from videobeaux.utils.booth_filters import Ctx
        from videobeaux.utils.booth_runner import _two_arg
        img = (np.random.default_rng(2).random((120, 160, 3)) * 255).astype(np.uint8)
        ctx = Ctx(t=1.0, faces=[(50, 25, 40, 50), (100, 30, 35, 45)],
                  eyes=[[(62, 42, 4), (80, 42, 4)], [(110, 45, 4), (125, 45, 4)]])
        for name in booth_modules():
            mod = importlib.import_module(f"videobeaux.programs.{name}")
            parser = argparse.ArgumentParser()
            mod.register_arguments(parser)
            args = parser.parse_args([])
            fn = _two_arg(mod.build(args))
            for _ in range(3):
                out = fn(img.copy(), ctx)
            self.assertEqual(out.shape, img.shape, name)
            self.assertEqual(out.dtype, np.uint8, name)

    def test_every_program_has_gui_labels_for_its_params(self):
        for name in booth_modules():
            mod = importlib.import_module(f"videobeaux.programs.{name}")
            for p in mod.PARAMS:
                self.assertIn(p.name, mod.GUI_METADATA["args"], f"{name}.{p.name}")
                self.assertTrue(mod.GUI_METADATA["args"][p.name]["label"], f"{name}.{p.name}")

    def test_seed_makes_random_filters_repeatable(self):
        import numpy as np
        from videobeaux.utils import booth_filters as bf
        img = (np.random.default_rng(4).random((96, 128, 3)) * 255).astype(np.uint8)
        outs = []
        for _ in range(2):
            bf.seed(7)
            outs.append(bf.make_glitch()(img.copy()))
        self.assertTrue((outs[0] == outs[1]).all())

    def test_solarize_and_posterize_tables(self):
        import numpy as np
        from videobeaux.utils import booth_filters as bf
        ramp = np.tile(np.arange(256, dtype=np.uint8), (4, 1))[..., None].repeat(3, 2)
        post = bf.make_posterize(4, smooth=False)(ramp)
        self.assertEqual(len(np.unique(post)), 4)
        sol = bf.make_solarize(128)(ramp)
        self.assertLessEqual(int(sol[0, 255, 0]), 3)       # brightest tones fold back to ~black


if __name__ == "__main__":
    unittest.main()
