import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _has(filter_name):
    if not shutil.which("ffmpeg"):
        return False
    out = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    return any(len(p) > 1 and p[1] == filter_name for p in (ln.split() for ln in out.splitlines()))


@unittest.skipUnless(_has("chromakey") and _has("lumakey") and _has("despill"), "needs ffmpeg with chromakey/lumakey/despill")
class Keying(unittest.TestCase):
    def _make_clip(self, d, bg):
        path = Path(d, f"{bg.strip('#')}.mp4")
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c={bg}:s=320x180:r=12:d=1",
             "-f", "lavfi", "-i", "color=c=0xCC3322:s=80x80:r=12:d=1",
             "-filter_complex", "[0][1]overlay=120:50,format=yuv420p", "-c:v", "libx264", str(path)], check=True)
        return path

    def _run(self, prog, clip, out, *extra):
        r = subprocess.run([sys.executable, "-m", "videobeaux.cli", "-P", prog, "-i", str(clip), "-o", str(out), "-F", *extra],
                           cwd=REPO, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout[-600:] + r.stderr[-600:])

    def _alpha(self, path):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", "alphaextract,format=gray",
                              "-frames:v", "1", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
        return lambda x, y: raw[y * 320 + x]

    def test_chroma_key_makes_screen_transparent_and_keeps_subject(self):
        with tempfile.TemporaryDirectory() as d:
            clip = self._make_clip(d, "0x00B140")
            out = Path(d, "out.mov")
            self._run("chroma_key", clip, out, "--background", "transparent")
            a = self._alpha(out)
            self.assertLess(a(10, 10), 10)       # screen → transparent
            self.assertGreater(a(160, 90), 240)  # subject → opaque

    def test_luma_key_removes_black(self):
        with tempfile.TemporaryDirectory() as d:
            clip = self._make_clip(d, "black")
            out = Path(d, "out.mov")
            self._run("luma_key", clip, out, "--background", "transparent", "--key", "dark")
            a = self._alpha(out)
            self.assertLess(a(10, 10), 10)
            self.assertGreater(a(160, 90), 240)

    def test_transparent_to_mp4_is_a_clear_error(self):
        with tempfile.TemporaryDirectory() as d:
            clip = self._make_clip(d, "0x00B140")
            r = subprocess.run([sys.executable, "-m", "videobeaux.cli", "-P", "chroma_key", "-i", str(clip), "-o",
                                str(Path(d, "x.mp4")), "-F", "--background", "transparent"],
                               cwd=REPO, capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("WEBM", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
