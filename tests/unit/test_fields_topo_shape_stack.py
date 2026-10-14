import argparse
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from videobeaux.utils import fields as F  # noqa: E402


class FieldMath(unittest.TestCase):
    def setUp(self):
        self.x, self.y = F.ramps(90, 160)

    def test_ramps_cover_the_frame_in_aspect_correct_units(self):
        self.assertAlmostEqual(float(self.y.min()), -1.0, places=4)
        self.assertAlmostEqual(float(self.y.max()), 1.0, places=4)
        self.assertAlmostEqual(float(self.x.max()), 160 / 90, places=3)

    def test_rotation_by_90_swaps_axes(self):
        xr, yr = F.ramps(90, 160, rotate_deg=90)
        self.assertLess(float(np.abs(xr + self.y).max()), 1e-4)      # x' = -y
        self.assertLess(float(np.abs(yr - self.x).max()), 1e-4)      # y' =  x

    def test_shapes_are_inside_at_the_centre_and_symmetric(self):
        for name in ("circle", "diamond", "square", "cross"):
            m = F.inside(F.shape_field(name, self.x, self.y, size=0.5), 0.02)
            self.assertEqual(float(m[45, 80]), 1.0, name)
            self.assertEqual(float(m[0, 0]), 0.0, name)
            self.assertLess(float(np.abs(m[:, 1:80] - m[:, -2:79:-1]).max()), 0.05, name)   # left/right mirror

    def test_circle_is_round_in_pixels(self):
        m = F.inside(F.shape_field("circle", self.x, self.y, size=0.5), 0.02) > 0.5
        ys, xs = np.nonzero(m)
        self.assertAlmostEqual((xs.max() - xs.min()) / (ys.max() - ys.min()), 1.0, delta=0.06)

    def test_fold_repeats_the_shape_as_bands(self):
        plain = F.inside(F.shape_field("circle", self.x, self.y, size=0.6, fold_n=1)).mean()
        folded = F.inside(F.shape_field("circle", self.x, self.y, size=0.6, fold_n=4)).mean()
        self.assertGreater(float(folded), float(plain) * 2)

    def test_combine_modes(self):
        a = np.array([[0.0, 1.0, 1.0, 0.0]], np.float32)
        b = np.array([[0.0, 0.0, 1.0, 1.0]], np.float32)
        self.assertEqual(F.combine(a, b, "max").tolist(), [[0, 1, 1, 1]])
        self.assertEqual(F.combine(a, b, "min").tolist(), [[0, 0, 1, 0]])
        self.assertEqual(F.combine(a, b, "xor").tolist(), [[0, 1, 0, 1]])
        self.assertEqual(F.combine(a, b, "difference").tolist(), [[0, 1, 0, 1]])

    def test_curve_keeps_endpoints(self):
        v = np.array([0.0, 1.0], np.float32)
        for k in (-3.0, 2.0):
            out = F.curve(v, k)
            self.assertAlmostEqual(float(out[0]), 0.0, places=5)
            self.assertAlmostEqual(float(out[1]), 1.0, places=5)


class Topobeaux(unittest.TestCase):
    def test_band_weights_sum_to_one_and_partition(self):
        from videobeaux.programs.topobeaux import band_labels, band_weights
        s = np.random.default_rng(1).random((50, 70)).astype(np.float32)
        cuts = [0.15, 0.3, 0.55, 0.8]
        for soft in (0.0, 0.05, 0.4):
            w = band_weights(s, cuts, soft)
            self.assertEqual(w.shape[0], 5)
            self.assertLess(float(np.abs(w.sum(0) - 1).max()), 1e-5)
            self.assertGreaterEqual(float(w.min()), -1e-6)
        hard = band_weights(s, cuts, 0.0)
        self.assertTrue((hard.argmax(0) == band_labels(s, cuts)).mean() > 0.99)

    def test_cut_parsing_falls_back_to_an_even_split(self):
        from videobeaux.programs.topobeaux import parse_band_list, parse_cuts
        self.assertEqual(parse_cuts("0.8, 0.2", 3), [0.2, 0.8])
        self.assertEqual(parse_cuts("nonsense", 4), [0.25, 0.5, 0.75])
        self.assertEqual(parse_band_list("2, 9, 3", 4), [1, 2])


class Stackadelic(unittest.TestCase):
    def _args(self, **kw):
        from videobeaux.programs import stackadelic
        p = argparse.ArgumentParser()
        stackadelic.register_arguments(p)
        a = p.parse_args([])
        for k, v in kw.items():
            setattr(a, k, v)
        return a

    def test_priority_subtracts_upper_layers_from_lower_ones(self):
        from videobeaux.programs.stackadelic import priority_keys
        top = np.array([[1.0, 1.0, 0.0, 0.0]], np.float32)
        mid = np.array([[1.0, 0.0, 1.0, 0.0]], np.float32)
        low = np.array([[1.0, 1.0, 1.0, 1.0]], np.float32)
        k1, k2, k3 = priority_keys([top, mid, low])
        self.assertEqual(k1.tolist(), [[1, 1, 0, 0]])
        self.assertEqual(k2.tolist(), [[0, 0, 1, 0]])
        self.assertEqual(k3.tolist(), [[0, 0, 0, 1]])
        self.assertEqual((k1 + k2 + k3).tolist(), [[1, 1, 1, 1]])

    def test_box_edges_land_where_asked(self):
        from videobeaux.programs.stackadelic import layer_shape
        a = self._args(l1_left=25, l1_right=75, l1_top=20, l1_bottom=80, l1_softness=0.0, l1_opacity=1)
        m = layer_shape(a, 1, 100, 200) > 0.5
        ys, xs = np.nonzero(m)
        self.assertAlmostEqual(xs.min() / 200, 0.25, delta=0.02)
        self.assertAlmostEqual((xs.max() + 1) / 200, 0.75, delta=0.02)
        self.assertAlmostEqual(ys.min() / 100, 0.20, delta=0.02)
        self.assertAlmostEqual((ys.max() + 1) / 100, 0.80, delta=0.02)

    def test_rhombus_is_smaller_than_its_rectangle_and_tiles_repeat(self):
        from videobeaux.programs.stackadelic import layer_shape
        rect = layer_shape(self._args(l1_shape="rectangle", l1_softness=0.0), 1, 100, 200).mean()
        rhomb = layer_shape(self._args(l1_shape="rhombus", l1_softness=0.0), 1, 100, 200).mean()
        self.assertAlmostEqual(float(rhomb / rect), 0.5, delta=0.05)
        one = layer_shape(self._args(l1_tiles=1, l1_softness=0.0, l1_left=0, l1_right=100, l1_top=0, l1_bottom=100, l1_size=0.5), 1, 100, 200)
        many = layer_shape(self._args(l1_tiles=4, l1_softness=0.0, l1_left=0, l1_right=100, l1_top=0, l1_bottom=100, l1_size=0.5), 1, 100, 200)
        self.assertAlmostEqual(float(many.mean()), float(one.mean()), delta=0.03)       # same coverage, split into 16 tiles
        cols = (many > 0.5).any(0).astype(int)
        self.assertGreaterEqual(int(np.abs(np.diff(cols)).sum()), 6)                    # several separate tile columns


@unittest.skipUnless(shutil.which("ffmpeg"), "needs ffmpeg")
class Rendering(unittest.TestCase):
    def _src(self, d):
        p = Path(d, "s.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "nullsrc=s=320x180:r=10:d=1,geq=lum='255*X/W':cb=128:cr=128",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(p)], check=True)
        return p

    def _run(self, prog, src, out, *a):
        r = subprocess.run([sys.executable, "-m", "videobeaux.cli", "-P", prog, "-i", str(src), "-o", str(out), "-F", *a],
                           cwd=REPO, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout[-500:] + r.stderr[-500:])

    def _frame(self, path):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-frames:v", "1", "-vf",
                              "scale=in_color_matrix=bt709:in_range=tv,format=rgb24", "-f", "rawvideo", "-"],
                             capture_output=True, check=True).stdout
        return np.frombuffer(raw, np.uint8).reshape(180, 320, 3)

    def test_topobeaux_false_color_uses_the_band_colors_left_to_right(self):
        with tempfile.TemporaryDirectory() as d:
            src, out = self._src(d), Path(d, "o.mp4")
            self._run("topobeaux", src, out, "--bands", "2", "--cuts", "0.5", "--colors", "#ff0000,#0000ff", "--smooth", "0")
            f = self._frame(out)
            self.assertGreater(int(f[90, 40, 0]), 200)          # dark side → band 1 = red
            self.assertLess(int(f[90, 40, 2]), 60)
            self.assertGreater(int(f[90, 280, 2]), 200)         # bright side → band 2 = blue

    def test_shape_synth_matte_is_a_centred_disc(self):
        with tempfile.TemporaryDirectory() as d:
            src, out = self._src(d), Path(d, "o.mp4")
            self._run("shape_synth", src, out, "--style", "matte (white shapes)", "--combine", "A", "--a_shape", "circle",
                      "--a_size", "0.5", "--a_softness", "0.02")
            f = self._frame(out)[..., 0]
            self.assertGreater(int(f[90, 160]), 200)
            self.assertLess(int(f[5, 5]), 30)

    def test_stackadelic_layers_cut_out_of_each_other(self):
        with tempfile.TemporaryDirectory() as d:
            src, out = self._src(d), Path(d, "o.mp4")
            self._run("stackadelic", src, out, "--base", "black",
                      "--l1_left", "40", "--l1_right", "60", "--l1_top", "40", "--l1_bottom", "60", "--l1_color", "#ff0000", "--l1_opacity", "1",
                      "--l2_left", "20", "--l2_right", "80", "--l2_top", "20", "--l2_bottom", "80", "--l2_color", "#00ff00", "--l2_opacity", "1",
                      "--l1_softness", "0", "--l2_softness", "0")
            f = self._frame(out)
            self.assertGreater(int(f[90, 160, 0]), 200)          # centre: layer 1 (red) on top
            self.assertLess(int(f[90, 160, 1]), 60)
            self.assertGreater(int(f[90, 110, 1]), 200)          # ring between the boxes: layer 2 (green)
            self.assertLess(int(f[90, 110, 0]), 60)
            self.assertLess(int(f[5, 5, 1]), 40)                 # outside both: black base




class TopobeauxSources(unittest.TestCase):
    def test_pictures_per_band(self):
        from videobeaux.programs.topobeaux import parse_sources
        self.assertEqual(parse_sources("A,B,A", 3, 3), [0, 1, 0])
        self.assertEqual(parse_sources("A,B,C", 3, 2), [0, 1, 0])       # C not connected → falls back to A
        self.assertEqual(parse_sources("", 4, 3), [0, 1, 2, 0])         # default cycles A,B,C
        self.assertEqual(parse_sources("x,b", 4, 3), [0, 1, 0, 1])

    def test_options_are_shown_only_for_the_styles_that_use_them(self):
        from videobeaux.programs.topobeaux import GUI_METADATA
        a = GUI_METADATA["args"]
        self.assertEqual(a["input2"]["show_if"], {"style": "bands from inputs"})
        self.assertIn("false color", a["colors"]["show_if"]["style"])
        self.assertEqual(a["matte_bands"]["show_if"], {"style": "band matte (cutout)"})
        self.assertNotIn("show_if", a["signal"])


if __name__ == "__main__":
    unittest.main()
