"""Zoom's crop window, Crop Black's detection and standard-size fit, and Watermark's timestamps."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from videobeaux.programs.crop_black import is_whole_frame, most_common_crop, nominal_size  # noqa: E402
from videobeaux.programs.watermark import _parse_time  # noqa: E402
from videobeaux.programs.zoom import zoom_window  # noqa: E402

HAVE_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


class ZoomWindow(unittest.TestCase):
    def test_no_zoom_keeps_the_whole_frame(self):
        self.assertEqual(zoom_window(1920, 1080, 100, 50, 50), (1920, 1080, 0, 0))

    def test_double_zoom_centred_is_the_middle_quarter(self):
        self.assertEqual(zoom_window(1920, 1080, 200, 50, 50), (960, 540, 480, 270))

    def test_focus_is_the_centre_of_the_window_when_it_fits(self):
        w, h, x, y = zoom_window(1920, 1080, 200, 25, 75)
        self.assertEqual((w, h), (960, 540))
        self.assertAlmostEqual(x + w / 2, 1920 * 0.25, delta=2)
        self.assertAlmostEqual(y + h / 2, 1080 * 0.75, delta=2)

    def test_a_focus_near_an_edge_stays_inside_the_frame(self):
        w, h, x, y = zoom_window(1920, 1080, 300, 0, 100)
        self.assertEqual(x, 0)
        self.assertEqual(y + h, 1080)

    def test_window_is_even_and_inside_for_odd_inputs(self):
        for zoom in (101, 137.5, 250, 399):
            w, h, x, y = zoom_window(1281, 721, zoom, 37, 91)
            self.assertEqual((w % 2, h % 2, x % 2, y % 2), (0, 0, 0, 0))
            self.assertTrue(0 <= x and x + w <= 1281)
            self.assertTrue(0 <= y and y + h <= 721)


class NominalSize(unittest.TestCase):
    def test_a_frame_already_standard_stays_put(self):
        self.assertEqual(nominal_size(1920, 1080), (1920, 1080))
        self.assertEqual(nominal_size(1280, 720), (1280, 720))

    def test_a_cinemascope_crop_goes_to_a_widescreen_frame(self):
        self.assertEqual(nominal_size(1920, 800), (1920, 800))
        self.assertEqual(nominal_size(1920, 816), (1920, 800))

    def test_a_portrait_crop_goes_to_a_portrait_frame(self):
        self.assertEqual(nominal_size(608, 1080), (720, 1280))


class CropDetection(unittest.TestCase):
    def test_the_most_common_picture_box_wins(self):
        boxes = [(1920, 816, 0, 132)] * 9 + [(1920, 1080, 0, 0)]
        self.assertEqual(most_common_crop(boxes), (1920, 816, 0, 132))

    def test_no_detections_means_no_crop(self):
        self.assertIsNone(most_common_crop([]))

    def test_a_frame_that_is_already_whole_is_not_treated_as_barred(self):
        self.assertTrue(is_whole_frame((1920, 1080, 0, 0), 1920, 1080))
        self.assertTrue(is_whole_frame((1918, 1078, 1, 1), 1920, 1080))
        self.assertFalse(is_whole_frame((1920, 816, 0, 132), 1920, 1080))


class WatermarkTimes(unittest.TestCase):
    def test_seconds_and_timestamps_read_the_same_way(self):
        self.assertEqual(_parse_time("83.5", "--start"), 83.5)
        self.assertEqual(_parse_time("1:23", "--start"), 83.0)
        self.assertEqual(_parse_time("1:23.5", "--start"), 83.5)
        self.assertEqual(_parse_time("0:01:23.5", "--start"), 83.5)
        self.assertEqual(_parse_time("0", "--start"), 0.0)
        self.assertEqual(_parse_time("", "--end"), 0.0)

    def test_nonsense_is_refused_with_the_flag_named(self):
        for bad in ("soon", "1:2:3:4", "-5"):
            with self.assertRaises(SystemExit) as caught:
                _parse_time(bad, "--start")
            self.assertIn("--start", str(caught.exception))


@unittest.skipUnless(HAVE_FFMPEG, "needs ffmpeg and ffprobe")
class CropBlackOnRealVideo(unittest.TestCase):
    """A 16:9 picture with black bars top and bottom: cropdetect should find the picture box."""

    def test_detects_the_bars_on_a_letterboxed_clip(self):
        from videobeaux.programs.crop_black import detect_crop

        with tempfile.TemporaryDirectory() as tmp:
            clip = Path(tmp) / "letterbox.mp4"
            subprocess.run([
                "ffmpeg", "-v", "error", "-y",
                "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=24:duration=2",
                "-vf", "pad=640:480:0:60:black", "-pix_fmt", "yuv420p", str(clip),
            ], check=True)
            crop = detect_crop(str(clip), 24)
            self.assertIsNotNone(crop)
            w, h, x, y = crop
            self.assertEqual((w, h), (640, 360))
            self.assertEqual(y, 60)


if __name__ == "__main__":
    unittest.main()
