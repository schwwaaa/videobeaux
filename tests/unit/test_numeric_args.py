import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROGRAMS = sorted((ROOT / "videobeaux" / "programs").glob("*.py"))
NUMERIC_HINT = re.compile(r"\b(Try\s+~?\d|between\s+-?\d|Allowed range|range is)\b", re.I)


class StringTypedNumbers(unittest.TestCase):
    def test_numeric_looking_args_are_not_free_text(self):
        """A number typed as text gets no slider/range in the GUI and can crash ffmpeg (twociz_pro similarity=3)."""
        bad = []
        for p in PROGRAMS:
            for m in re.finditer(r'add_argument\(\s*"--([\w-]+)"(.*?)\n\s*\)', p.read_text(encoding="utf-8"), re.S):
                blk = m.group(2)
                if "type=str" in blk and NUMERIC_HINT.search(blk):
                    bad.append(f"{p.name}: --{m.group(1)}")
        self.assertEqual(bad, [])


@unittest.skipUnless(shutil.which("ffmpeg"), "needs ffmpeg")
class OutOfRangeValuesRun(unittest.TestCase):
    def test_twociz_pro_clamps_instead_of_crashing(self):
        with tempfile.TemporaryDirectory() as d:
            src, out = Path(d, "s.mp4"), Path(d, "o.mp4")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=160x120:r=10:d=1", "-c:v", "libx264",
                            "-pix_fmt", "yuv420p", str(src)], check=True)
            r = subprocess.run([sys.executable, "-m", "videobeaux.cli", "-P", "twociz_pro", "-i", str(src), "-o", str(out), "-F",
                                "--radius", "3", "--factor", "3", "--blend", "3", "--similarity", "3"],
                               cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout[-600:] + r.stderr[-600:])
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
