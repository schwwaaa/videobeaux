"""Speed: from 0.05× to 100×, audio chained through atempo, mute, and smooth slow-motion."""
import math
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from videobeaux.programs.speed import atempo_chain, build_filtergraph, MIN_SPEED, MAX_SPEED  # noqa: E402

HAVE_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


class Chain(unittest.TestCase):
    def test_every_stage_is_within_atempos_limits_and_the_product_is_the_factor(self):
        for f in (0.05, 0.1, 0.2, 0.25, 0.3, 0.49, 0.5, 0.75, 1, 1.5, 2, 8, 99, 100):
            stages = atempo_chain(f)
            self.assertTrue(all(0.5 <= s <= 100 for s in stages), (f, stages))
            self.assertAlmostEqual(math.prod(stages), f, places=6, msg=str(f))

    def test_one_tenth_is_three_halvings_and_a_remainder(self):
        self.assertEqual(atempo_chain(0.1), [0.5, 0.5, 0.5, 0.8])

    def test_graph_shapes(self):
        g = build_filtergraph(0.1)
        self.assertIn("setpts=PTS/0.100000[v]", g)
        self.assertIn("atempo=0.500000,atempo=0.500000,atempo=0.500000,atempo=0.800000[a]", g)
        self.assertNotIn("[0:a]", build_filtergraph(0.1, audio=False))
        self.assertIn("minterpolate=fps=24.000", build_filtergraph(0.25, fps=24, smooth=True))
        self.assertNotIn("minterpolate", build_filtergraph(2, fps=24, smooth=True))        # only when slowing down

    def test_limits_match_the_gui_range(self):
        self.assertEqual((MIN_SPEED, MAX_SPEED), (0.05, 100.0))


@unittest.skipUnless(HAVE_FFMPEG, "needs ffmpeg + ffprobe")
class Rendering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="vb_speed_"))
        cls.src = cls.tmp / "src.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=160x90:r=24:d=1", "-f", "lavfi", "-i", "sine=d=1",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(cls.src)], check=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _run(self, *extra):
        out = self.tmp / f"o_{abs(hash(extra))}.mp4"
        r = subprocess.run([sys.executable, "-m", "videobeaux.cli", "-P", "speed", "-i", str(self.src), "-o", str(out), "-F", *extra],
                           cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout[-400:] + r.stderr[-400:])
        return out

    def _dur(self, path, stream):
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", stream, "-show_entries", "stream=duration", "-of", "csv=p=0", str(path)],
                           capture_output=True, text=True).stdout.strip()
        return float(r) if r else 0.0

    def test_ultra_slow_is_ten_times_longer_with_matching_audio(self):
        out = self._run("--speed_factor", "0.1")
        self.assertAlmostEqual(self._dur(out, "v"), 10.0, delta=0.5)
        self.assertAlmostEqual(self._dur(out, "a"), 10.0, delta=0.6)

    def test_normal_and_fast_still_work(self):
        self.assertAlmostEqual(self._dur(self._run("--speed_factor", "2"), "v"), 0.5, delta=0.1)
        self.assertAlmostEqual(self._dur(self._run("--speed_factor", "0.5"), "v"), 2.0, delta=0.2)

    def test_mute_drops_the_audio_stream(self):
        out = self._run("--speed_factor", "0.25", "--audio", "Mute")
        self.assertEqual(self._dur(out, "a"), 0.0)
        self.assertAlmostEqual(self._dur(out, "v"), 4.0, delta=0.3)

    def test_smooth_slow_motion_renders(self):
        out = self._run("--speed_factor", "0.5", "--smooth")
        self.assertAlmostEqual(self._dur(out, "v"), 2.0, delta=0.3)

    def test_out_of_range_is_refused(self):
        r = subprocess.run([sys.executable, "-m", "videobeaux.cli", "-P", "speed", "-i", str(self.src), "-o", str(self.tmp / "x.mp4"), "-F",
                            "--speed_factor", "0.01"], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
