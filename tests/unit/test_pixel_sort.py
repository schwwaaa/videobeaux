"""Pixel sort: the sorting rules on tiny hand-checked rows (brightness = the mean of R, G and B)."""
import unittest

import numpy as np

from videobeaux.programs.pixel_sort import pixel_sort_frame


def row(*values):
    """A 1-pixel-high picture; each value is a grey level (R = G = B)."""
    return np.array([[(v, v, v) for v in values]], dtype=np.uint8)


def grey(picture):
    return [int(p[0]) for p in picture[0]]


class Ascending(unittest.TestCase):
    def test_brighter_runs_sort_in_place_and_darker_pixels_stay(self):
        out = pixel_sort_frame(row(10, 200, 120, 30, 250, 240, 90), 100, False)
        self.assertEqual(grey(out), [10, 120, 200, 30, 240, 250, 90])

    def test_descending_reverses_each_run(self):
        out = pixel_sort_frame(row(10, 200, 120, 30, 250, 240, 90), 100, False, descending=True)
        self.assertEqual(grey(out), [10, 200, 120, 30, 250, 240, 90])


class Select(unittest.TestCase):
    def test_darker_sorts_the_shadows_instead(self):
        out = pixel_sort_frame(row(200, 50, 10, 250, 20, 90), 100, False, select="darker")
        self.assertEqual(grey(out), [200, 10, 50, 250, 20, 90])

    def test_darker_descending(self):
        out = pixel_sort_frame(row(200, 50, 10, 250, 20, 90), 100, False, select="darker", descending=True)
        self.assertEqual(grey(out), [200, 50, 10, 250, 90, 20])


class SortBy(unittest.TestCase):
    def test_red_channel_orders_differently_from_brightness(self):
        # brightness order would be P2, P1, P3 (33, 83, 100); red order is P2, P3, P1 (0, 100, 250)
        picture = np.array([[(250, 0, 0), (0, 0, 100), (100, 100, 100)]], dtype=np.uint8)
        by_brightness = pixel_sort_frame(picture, 10, False)
        by_red = pixel_sort_frame(picture, 10, False, sort_by="red")
        self.assertEqual([tuple(p) for p in by_brightness[0]], [(0, 0, 100), (250, 0, 0), (100, 100, 100)])
        self.assertEqual([tuple(p) for p in by_red[0]], [(0, 0, 100), (100, 100, 100), (250, 0, 0)])

    def test_hue_and_saturation_run_without_error(self):
        picture = np.random.default_rng(0).integers(0, 256, size=(20, 30, 3), dtype=np.uint8)
        for key in ("hue", "saturation"):
            out = pixel_sort_frame(picture, 60, False, sort_by=key)
            self.assertEqual(out.shape, picture.shape)
            self.assertEqual(sorted(out.ravel().tolist()), sorted(picture.ravel().tolist()))


class MinRun(unittest.TestCase):
    def test_streaks_shorter_than_min_run_stay_put(self):
        # two separate runs of length two (the 50 splits them): with min_run 3 neither is sorted
        self.assertEqual(grey(pixel_sort_frame(row(200, 120, 50, 250, 240, 90), 100, False, min_run=3)),
                         [200, 120, 50, 250, 240, 90])

    def test_streaks_at_or_above_min_run_are_sorted(self):
        self.assertEqual(grey(pixel_sort_frame(row(200, 120, 50, 250, 240, 90), 100, False, min_run=2)),
                         [120, 200, 50, 240, 250, 90])


class Mix(unittest.TestCase):
    def test_half_mix_is_halfway_between_original_and_sorted(self):
        out = pixel_sort_frame(row(200, 120, 90), 100, False, mix=0.5)
        self.assertEqual(grey(out), [160, 160, 90])     # sorted row is [120, 200, 90] → halfway each way

    def test_zero_mix_is_the_original(self):
        picture = row(200, 120, 250, 240, 90)
        np.testing.assert_array_equal(pixel_sort_frame(picture, 100, False, mix=0.0), picture)


class Rows(unittest.TestCase):
    def test_runs_never_cross_a_row(self):
        picture = np.array([[(200, 200, 200), (250, 250, 250)],
                            [(120, 120, 120), (90, 90, 90)]], dtype=np.uint8)
        out = pixel_sort_frame(picture, 100, False)
        self.assertEqual(out[0, :, 0].tolist(), [200, 250])     # 200 and 250 are sorted, not joined to row 2
        self.assertEqual(out[1, :, 0].tolist(), [120, 90])      # 120 is in the bright run, 90 is not picked

    def test_vertical_matches_horizontal_on_the_transpose(self):
        picture = np.random.default_rng(1).integers(0, 256, size=(12, 17, 3), dtype=np.uint8)
        vertical = pixel_sort_frame(picture, 90, True)
        horizontal = pixel_sort_frame(picture.transpose(1, 0, 2).copy(), 90, False)
        np.testing.assert_array_equal(vertical, horizontal.transpose(1, 0, 2))


if __name__ == "__main__":
    unittest.main()
