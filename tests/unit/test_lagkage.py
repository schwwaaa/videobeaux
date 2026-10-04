import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "needs ffmpeg")
class LagkageLayers(unittest.TestCase):
    W, H = 320, 180

    def _setup(self, d):
        base = Path(d, "base.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=black:s={self.W}x{self.H}:r=10:d=1",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(base)], check=True)
        img = Path(d, "red.png")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=red:s=100x100", "-frames:v", "1", str(img)],
                       check=True)
        return base, img

    def _render(self, d, base, layer):
        lay = Path(d, "lay.json")
        lay.write_text(json.dumps({"layers": [{"layer_number": 1, "name": "t", "type": "img", "mode": "free",
                                               "opacity": 1.0, **layer}]}))
        out = Path(d, "o.mp4")
        r = subprocess.run([sys.executable, "-m", "videobeaux.cli", "-P", "lagkage", "-i", str(base), "-o", str(out), "-F",
                            "--layout-json", str(lay)], cwd=REPO, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout[-500:] + r.stderr[-500:])
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(out), "-frames:v", "1", "-vf",
                              "scale=in_color_matrix=bt709:in_range=tv,format=rgb24", "-f", "rawvideo", "-"],
                             capture_output=True, check=True).stdout
        return lambda x, y: tuple(raw[(y * self.W + x) * 3:(y * self.W + x) * 3 + 3])

    @staticmethod
    def _red(p):
        return p[0] > 200 and p[1] < 60 and p[2] < 60

    def test_height_pct_stretches_the_box(self):
        with tempfile.TemporaryDirectory() as d:
            base, img = self._setup(d)
            # 50% wide (160 px) x 20% high (36 px), top-left at (10%, 40%) -> x 32..192, y 72..108
            px = self._render(d, base, {"filename": str(img), "size": 50, "height_pct": 20, "pos_x_pct": 10, "pos_y_pct": 40})
            self.assertTrue(self._red(px(100, 90)))
            self.assertFalse(self._red(px(100, 60)))        # a square 160x160 box would have covered this
            self.assertFalse(self._red(px(100, 125)))

    def test_rotation_swaps_the_bar_orientation_about_its_centre(self):
        with tempfile.TemporaryDirectory() as d:
            base, img = self._setup(d)
            layer = {"filename": str(img), "size": 50, "height_pct": 10, "pos_x_pct": 25, "pos_y_pct": 45}
            flat = self._render(d, base, layer)           # centre = (160, 90): a 160x18 bar
            self.assertTrue(self._red(flat(120, 90)))
            self.assertFalse(self._red(flat(160, 40)))
            tall = self._render(d, base, {**layer, "rotate": 90})
            self.assertTrue(self._red(tall(160, 45)))     # now a vertical bar through the same centre
            self.assertFalse(self._red(tall(110, 90)))
            self.assertTrue(self._red(tall(160, 90)))

    def test_blur_softens_the_edge_and_old_layouts_still_work(self):
        with tempfile.TemporaryDirectory() as d:
            base, img = self._setup(d)
            sharp = self._render(d, base, {"filename": str(img), "size": 40, "pos_x_pct": 30, "pos_y_pct": 20})
            soft = self._render(d, base, {"filename": str(img), "size": 40, "pos_x_pct": 30, "pos_y_pct": 20, "blur": 2})
            edge_x, y = int(0.30 * self.W) + 1, 80            # just inside the left edge
            self.assertGreater(sharp(edge_x, y)[0], 200)
            self.assertLess(soft(edge_x, y)[0], sharp(edge_x, y)[0] - 20)
            old = self._render(d, base, {"filename": str(img), "size": 30, "mode": "place", "place": "center"})
            self.assertTrue(self._red(old(160, 90)))


if __name__ == "__main__":
    unittest.main()
