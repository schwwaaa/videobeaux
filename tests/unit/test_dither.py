"""Numpy-only tests for the dithering core and palette helpers (no ffmpeg/OpenCV needed).

    python -m unittest discover -s tests/unit -v
"""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from videobeaux.utils import dither_core as dc  # noqa: E402
from videobeaux.utils import palettes as pal  # noqa: E402


class ThresholdMatrices(unittest.TestCase):
    def test_bayer_is_a_permutation(self):
        for n in (2, 4, 8, 16):
            self.assertEqual(sorted(dc.bayer_matrix(n).ravel()), list(range(n * n)))

    def test_clustered_and_blue_noise_are_permutations(self):
        self.assertEqual(sorted(dc.clustered_dot_matrix(8).ravel()), list(range(64)))
        self.assertEqual(sorted(dc.blue_noise_tile(64).ravel()), list(range(64 * 64)))

    def test_threshold_map_range_and_shape(self):
        for m in dc.METHODS:
            t = dc.threshold_map(m, 37, 53)
            self.assertEqual(t.shape, (37, 53), m)
            self.assertGreaterEqual(float(t.min()), 0.0, m)
            self.assertLess(float(t.max()), 1.0 + 1e-6, m)

    def test_animate_changes_pattern_but_static_does_not(self):
        for m in ("bayer8", "white_noise", "ign"):
            a, b = dc.threshold_map(m, 32, 32, 0, True), dc.threshold_map(m, 32, 32, 1, True)
            self.assertFalse(np.array_equal(a, b), m)
            c, d = dc.threshold_map(m, 32, 32, 0, False), dc.threshold_map(m, 32, 32, 5, False)
            self.assertTrue(np.array_equal(c, d), m)


class DitherFrame(unittest.TestCase):
    def setUp(self):
        self.frame = (np.random.default_rng(3).random((90, 120, 3)) * 255).astype(np.uint8)

    def test_output_only_contains_palette_colors(self):
        for name in ("bw", "gameboy", "pico8"):
            p = pal.to_array(pal.PALETTES[name])
            for m in dc.METHODS:
                out = dc.dither_frame(self.frame, method=m, palette=p)
                got = {tuple(c) for c in out.reshape(-1, 3)}
                self.assertTrue(got <= {tuple(c) for c in p}, f"{name}/{m}")

    def test_levels_posterize(self):
        out = dc.dither_frame(self.frame, method="bayer4", levels=3)
        for ch in range(3):
            self.assertLessEqual(len(np.unique(out[..., ch])), 3)

    def test_pixel_size_keeps_shape_and_blocks(self):
        out = dc.dither_frame(self.frame, method="bayer4", levels=2, pixel_size=4)
        self.assertEqual(out.shape, self.frame.shape)
        self.assertTrue(np.array_equal(out[0:4, 0:4], np.broadcast_to(out[0, 0], (4, 4, 3))))

    def test_non_divisible_size_is_padded_back(self):
        f = self.frame[:89, :119]
        out = dc.dither_frame(f, method="ign", levels=2, pixel_size=3)
        self.assertEqual(out.shape, f.shape)

    def test_solid_black_and_white_stay_put(self):
        p = pal.to_array(pal.PALETTES["bw"])
        black = np.zeros((16, 16, 3), np.uint8)
        white = np.full((16, 16, 3), 255, np.uint8)
        self.assertTrue((dc.dither_frame(black, method="bayer8", palette=p) == 0).all())
        self.assertTrue((dc.dither_frame(white, method="bayer8", palette=p) == 255).all())


class Palettes(unittest.TestCase):
    def test_parse_hex_list(self):
        self.assertEqual(pal.parse_hex_list("#ff0000, 00ff00 ,#00f"), ["FF0000", "00FF00", "0000FF"])
        with self.assertRaises(ValueError):
            pal.parse_hex_list("#ff0000, banana")

    def test_resolve_palette(self):
        self.assertEqual(len(pal.resolve_palette("gameboy")), 4)
        with self.assertRaises(ValueError):
            pal.resolve_palette("custom", "#000000")        # needs >= 2
        with self.assertRaises(ValueError):
            pal.resolve_palette("nope")

    def test_palette_png_is_256_pixels_with_same_colors(self):
        import tempfile
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            p = pal.write_palette_png(pal.PALETTES["bw"], Path(d) / "p.png")
            im = Image.open(p).convert("RGB")
            self.assertEqual(im.size[0] * im.size[1], 256)
            self.assertEqual({c for _, c in im.getcolors()}, {(0, 0, 0), (255, 255, 255)})


if __name__ == "__main__":
    unittest.main()
