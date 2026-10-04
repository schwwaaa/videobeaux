import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

try:
    import cv2  # noqa: F401
    HAVE_CV2 = True
except ImportError:
    HAVE_CV2 = False


@unittest.skipUnless(HAVE_CV2, "needs OpenCV")
class MatteMath(unittest.TestCase):
    def test_onnx_matter_pre_and_post_processing(self):
        import cv2
        import numpy as np
        from videobeaux.utils import bgremove

        class FakeInput:
            name = "input.1"

        class FakeSession:                      # stands in for onnxruntime: left half "subject", right half "background"
            def get_inputs(self):
                return [FakeInput()]

            def run(self, _outs, feed):
                x = feed["input.1"]
                assert x.shape == (1, 3, 320, 320) and x.dtype == np.float32
                out = np.zeros((1, 1, 320, 320), np.float32)
                out[..., :160] = 0.95
                out[..., 160:] = 0.02
                return [out]

        matter = bgremove.OnnxMatter.__new__(bgremove.OnnxMatter)
        matter.sess, matter.input = FakeSession(), "input.1"
        frame = (np.random.default_rng(1).random((180, 240, 3)) * 255).astype(np.uint8)
        m = matter(cv2, frame)
        self.assertEqual(m.shape, (180, 240))
        self.assertGreater(float(m[:, :100].mean()), 0.9)
        self.assertLess(float(m[:, 140:].mean()), 0.1)

    def test_clean_matte_fills_holes_and_keeps_the_largest_blob(self):
        import cv2
        import numpy as np
        from videobeaux.programs.remove_background import clean_matte
        m = np.zeros((100, 100), np.float32)
        m[20:80, 20:80] = 1.0
        m[45:55, 45:55] = 0.0                    # a hole
        m[5:10, 5:10] = 1.0                      # a stray speck
        filled = clean_matte(cv2, m, fill_holes=True)
        self.assertGreater(float(filled[50, 50]), 0.9)
        largest = clean_matte(cv2, m, largest_only=True)
        self.assertLess(float(largest[7, 7]), 0.1)
        self.assertGreater(float(largest[30, 30]), 0.9)
        self.assertLess(float(largest[50, 50]), 0.1)    # holes stay unless asked

    def test_missing_model_gives_a_clear_message(self):
        import os
        import tempfile
        from videobeaux.utils import bgremove
        with tempfile.TemporaryDirectory() as d:
            os.environ["VIDEOBEAUX_MODELS_DIR"] = d
            try:
                with self.assertRaises(SystemExit) as cm:
                    bgremove.OnnxMatter("u2netp")
                self.assertIn("Setup", str(cm.exception))
            finally:
                del os.environ["VIDEOBEAUX_MODELS_DIR"]


@unittest.skipUnless(HAVE_CV2 and shutil.which("ffmpeg"), "needs OpenCV and ffmpeg")
class StaticEngine(unittest.TestCase):
    def test_moving_subject_on_a_static_scene_becomes_the_alpha(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d, "s.mp4")
            subprocess.run(
                ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=320x180:r=12:d=4", "-f", "lavfi", "-i",
                 "color=c=white:s=50x50:r=12:d=4,format=rgba,geq=r='255':g='255':b='255':a='255*lt(hypot(X-25,Y-25),23)'",
                 "-filter_complex", "[0:v][1:v]overlay=x='10+t*60':y=60:format=auto,format=yuv420p", "-c:v", "libx264",
                 "-pix_fmt", "yuv420p", str(src)], check=True)
            out = Path(d, "o.mov")
            r = subprocess.run([sys.executable, "-m", "videobeaux.cli", "-P", "remove_background", "-i", str(src), "-o", str(out),
                                "-F", "--background", "transparent", "--smoothing", "0"], cwd=REPO, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout[-500:] + r.stderr[-500:])
            raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "2", "-i", str(out), "-frames:v", "1", "-vf",
                                  "alphaextract,format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
            alpha = lambda x, y: raw[y * 320 + x]
            self.assertGreater(alpha(10 + 120 + 25, 85), 200)       # disc centre at t = 2 s
            self.assertLess(alpha(20, 20), 20)                      # scene stays transparent


if __name__ == "__main__":
    unittest.main()
