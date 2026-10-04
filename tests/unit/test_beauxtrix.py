import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def _gains(**kw):
    base = {m: [1.0, 0.0, 0.0, 0.0] for m in "rgb"}
    for m, v in kw.items():
        base[m] = v
    return base


ZERO = {m: 0.0 for m in "rgb"}
SUM = {m: "sum" for m in "rgb"}
ABS = {m: "absolute" for m in "rgb"}


class MatrixMath(unittest.TestCase):
    def setUp(self):
        import numpy as np
        rng = np.random.default_rng(3)
        self.np = np
        self.a = (rng.random((60, 80, 3)) * 255).astype(np.uint8)
        self.b = (rng.random((60, 80, 3)) * 255).astype(np.uint8)

    def mix(self, gains, biases=ZERO, outs=SUM, luma=False, srcs=None, limiter="hard"):
        from videobeaux.programs.beauxtrix import matrix_mix
        srcs = srcs or [self.a, self.b, self.a, self.a]
        return matrix_mix(srcs, gains, biases, outs, luma_mode=luma, limiter=limiter)

    def test_identity_returns_the_input(self):
        out = self.mix(_gains())
        self.assertLessEqual(int(abs(out.astype(int) - self.a.astype(int)).max()), 1)

    def test_difference_of_identical_clips_is_black(self):
        g = {m: [1.0, -1.0, 0.0, 0.0] for m in "rgb"}
        out = self.mix(g, outs=ABS, srcs=[self.a, self.a, self.a, self.a])
        self.assertEqual(int(out.max()), 0)

    def test_absolute_difference_is_symmetric(self):
        g = {m: [1.0, -1.0, 0.0, 0.0] for m in "rgb"}
        ab = self.mix(g, outs=ABS, srcs=[self.a, self.b, self.a, self.a])
        ba = self.mix(g, outs=ABS, srcs=[self.b, self.a, self.a, self.a])
        self.assertLessEqual(int(abs(ab.astype(int) - ba.astype(int)).max()), 1)

    def test_solarize_curve(self):
        np = self.np
        ramp = np.tile(np.arange(256, dtype=np.uint8), (4, 1))[..., None].repeat(3, 2)
        g = {m: [2.0, 0.0, 0.0, 0.0] for m in "rgb"}
        out = self.mix(g, biases={m: -1.0 for m in "rgb"}, outs=ABS, srcs=[ramp] * 4)
        row = out[0, :, 0].astype(int)
        self.assertLessEqual(row[128], 3)              # mid-gray folds to black
        self.assertGreaterEqual(row[0], 250)           # black and white both come out bright
        self.assertGreaterEqual(row[255], 250)

    def test_negative(self):
        g = {m: [-1.0, 0.0, 0.0, 0.0] for m in "rgb"}
        out = self.mix(g, biases={m: 1.0 for m in "rgb"})
        self.assertLessEqual(int(abs(out.astype(int) - (255 - self.a.astype(int))).max()), 1)

    def test_luma_mode_is_gray_and_channel_mode_keeps_color(self):
        gray = self.mix(_gains(), luma=True)
        self.assertEqual(int(abs(gray[..., 0].astype(int) - gray[..., 1].astype(int)).max()), 0)
        color = self.mix(_gains(), luma=False)
        self.assertGreater(int(abs(color[..., 0].astype(int) - color[..., 1].astype(int)).max()), 10)

    def test_soft_limiter_is_bounded_and_monotonic(self):
        from videobeaux.programs.beauxtrix import soft_limit
        y = self.np.linspace(-3, 3, 601, dtype=self.np.float32)
        s = soft_limit(y)
        self.assertLessEqual(float(abs(s).max()), 1.0001)
        self.assertTrue((self.np.diff(s) >= -1e-6).all())


@unittest.skipUnless(shutil.which("ffmpeg"), "needs ffmpeg")
class Render(unittest.TestCase):
    def test_two_inputs_difference_preset_renders_black_for_identical_clips(self):
        import numpy as np
        with tempfile.TemporaryDirectory() as d:
            src = Path(d, "s.mp4")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=160x120:r=10:d=1", "-c:v", "libx264",
                            "-pix_fmt", "yuv420p", str(src)], check=True)
            out = Path(d, "o.mp4")
            args = []
            for m in "rgb":
                args += [f"--{m}_a", "1", f"--{m}_b", "-1", f"--{m}_out", "absolute"]
            r = subprocess.run([sys.executable, "-m", "videobeaux.cli", "-P", "beauxtrix", "-i", str(src), "--input2", str(src),
                                "-o", str(out), "-F", *args], cwd=REPO, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout[-500:] + r.stderr[-500:])
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(out), "-frames:v", "1", "-vf", "format=gray", "-f", "rawvideo", "-"],
                                 capture_output=True, check=True).stdout
            self.assertLess(float(np.frombuffer(raw, np.uint8).mean()), 24)       # limited-range black ≈ 16

    def test_single_input_works_without_extras(self):
        with tempfile.TemporaryDirectory() as d:
            src, out = Path(d, "s.mp4"), Path(d, "o.mp4")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=160x120:r=10:d=1", "-c:v", "libx264",
                            "-pix_fmt", "yuv420p", str(src)], check=True)
            r = subprocess.run([sys.executable, "-m", "videobeaux.cli", "-P", "beauxtrix", "-i", str(src), "-o", str(out), "-F"],
                               cwd=REPO, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout[-500:] + r.stderr[-500:])


if __name__ == "__main__":
    unittest.main()
