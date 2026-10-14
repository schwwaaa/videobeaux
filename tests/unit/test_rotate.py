"""Rotate: exact turns for right angles, sized canvases for the rest, and real output dimensions."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from videobeaux.programs.rotate import EXPAND, FILL, FITS, FLIPS, KEEP, build_filter  # noqa: E402

HAVE_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


class BuildFilter(unittest.TestCase):
    def test_right_angles_use_lossless_filters_and_swap_dimensions(self):
        vf, w, h = build_filter(640, 360, 90)
        self.assertIn("transpose=1", vf)
        self.assertNotIn("rotate=", vf)
        self.assertEqual((w, h), (360, 640))
        self.assertIn("transpose=2", build_filter(640, 360, -90)[0])
        self.assertIn("transpose=2", build_filter(640, 360, 270)[0])        # 270° == -90°
        vf, w, h = build_filter(640, 360, 180)
        self.assertTrue("hflip" in vf and "vflip" in vf)
        self.assertEqual((w, h), (640, 360))
        self.assertEqual(build_filter(640, 360, 0)[1:], (640, 360))
        self.assertEqual(build_filter(640, 360, 360)[1:], (640, 360))

    def test_flip_is_added_before_the_turn(self):
        vf, _, _ = build_filter(640, 360, 90, flip=FLIPS[1])
        self.assertTrue(vf.index("hflip") < vf.index("transpose=1"))

    def test_expand_contains_the_whole_rotated_picture(self):
        vf, w, h = build_filter(640, 360, 45, fit=EXPAND)
        self.assertIn("rotate=", vf)
        self.assertEqual((w, h), (708, 708))                                  # (640+360)/√2 → 707.1 → even 708
        self.assertTrue(w % 2 == 0 and h % 2 == 0)

    def test_fill_enlarges_so_no_corner_shows_and_keeps_the_frame_size(self):
        vf, w, h = build_filter(640, 360, 20, fit=FILL)
        self.assertEqual((w, h), (640, 360))
        self.assertIn("scale=", vf)
        # the enlargement factor covers the rotated frame: ≥ cos + (h/w)·sin and ≥ (w/h)·sin + cos
        import math
        import re
        sw = int(re.search(r"scale=(\d+):(\d+)", vf).group(1))
        th = math.radians(20)
        need = max(math.cos(th) + 360 / 640 * math.sin(th), 640 / 360 * math.sin(th) + math.cos(th))
        self.assertGreaterEqual(sw / 640, need - 0.01)

    def test_keep_leaves_the_size_alone(self):
        self.assertEqual(build_filter(641, 361, 30, fit=KEEP)[1:], (642, 362))

    def test_spin_always_uses_the_rotate_filter_with_a_time_term(self):
        vf, w, h = build_filter(640, 360, 0, spin=30)
        self.assertIn("*t)", vf)
        self.assertEqual((w, h), (736, 736))                                  # diagonal of 640×360, even

    def test_fill_colour(self):
        vf, _, _ = build_filter(640, 360, 45, fill="#ff6847")
        self.assertIn("c=0xFF6847", vf)

    def test_fits_are_the_documented_choices(self):
        self.assertEqual(FITS, [EXPAND, FILL, KEEP])


@unittest.skipUnless(HAVE_FFMPEG, "needs ffmpeg + ffprobe")
class Rendering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="vb_rot_"))
        cls.src = cls.tmp / "src.mp4"
        # left half red, right half blue, with audio
        subprocess.run(["ffmpeg", "-y", "-v", "error",
                        "-f", "lavfi", "-i", "color=c=red:s=80x90:r=25:d=1", "-f", "lavfi", "-i", "color=c=blue:s=80x90:r=25:d=1",
                        "-f", "lavfi", "-i", "sine=d=1",
                        "-filter_complex", "[0:v][1:v]hstack[v]", "-map", "[v]", "-map", "2:a", "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(cls.src)], check=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _run(self, *extra):
        out = self.tmp / f"out_{abs(hash(extra))}.mp4"
        r = subprocess.run([sys.executable, "-m", "videobeaux.cli", "-P", "rotate", "-i", str(self.src), "-o", str(out), "-F", *extra],
                           cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout[-500:] + r.stderr[-500:])
        return out

    def _dims(self, p):
        o = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,codec_name,pix_fmt",
                            "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout.strip().split(",")
        return o

    def _px(self, p, x, y):
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           capture_output=True)
        info = self._dims(p)
        codec, W, H = info[0], int(info[1]), int(info[2])
        a = np.frombuffer(r.stdout, np.uint8).reshape(H, W, 3)
        return tuple(int(v) for v in a[y, x])

    def test_upside_down_swaps_the_halves_and_keeps_size(self):
        out = self._run("--angle", "180")
        info = self._dims(out)
        self.assertEqual((int(info[1]), int(info[2])), (160, 90))
        self.assertEqual((info[0], info[3]), ("h264", "yuv420p"))
        r, g, b = self._px(out, 20, 45)                      # was the red left half → now blue on the left
        self.assertGreater(b, 150)
        self.assertLess(r, 100)

    def test_ninety_degrees_changes_the_output_dimensions(self):
        info = self._dims(self._run("--angle", "90"))
        self.assertEqual((int(info[1]), int(info[2])), (90, 160))

    def test_forty_five_grows_the_canvas_with_even_dimensions(self):
        info = self._dims(self._run("--angle", "45"))
        w, h = int(info[1]), int(info[2])
        self.assertTrue(w > 160 and h > 90 and w % 2 == 0 and h % 2 == 0, (w, h))
        # corner is the fill colour (black)
        self.assertLess(max(self._px(self._run("--angle", "45"), 2, 2)), 40)

    def test_fill_has_no_empty_corners(self):
        out = self._run("--angle", "20", "--fit", FILL, "--fill", "#00ff00")
        info = self._dims(out)
        self.assertEqual((int(info[1]), int(info[2])), (160, 90))
        for x, y in ((1, 1), (158, 1), (1, 88), (158, 88)):
            r, g, b = self._px(out, x, y)
            self.assertFalse(g > 200 and r < 60 and b < 60, (x, y, (r, g, b)))

    def test_spin_renders_and_odd_sized_sources_get_even_output(self):
        odd = self.tmp / "odd.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=321x181:r=25:d=1", "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", str(odd)], check=True)
        for extra in (("--angle", "0", "--spin", "45"), ("--angle", "33")):
            out = self.tmp / f"odd_{'_'.join(extra)}.mp4"
            r = subprocess.run([sys.executable, "-m", "videobeaux.cli", "-P", "rotate", "-i", str(odd), "-o", str(out), "-F", *extra],
                               cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout[-400:] + r.stderr[-400:])
            info = self._dims(out)
            self.assertTrue(int(info[1]) % 2 == 0 and int(info[2]) % 2 == 0, info)

    def test_audio_is_kept(self):
        out = self._run("--angle", "90")
        a = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_name", "-of", "csv=p=0", str(out)],
                           capture_output=True, text=True).stdout.strip()
        self.assertEqual(a, "aac")


if __name__ == "__main__":
    unittest.main()
