import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "needs ffmpeg")
class CrossmoshAudio(unittest.TestCase):
    def _clip(self, d, name, hz, seconds):
        p = Path(d, name)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc2=s=160x120:r=24:d={seconds}",
                        "-f", "lavfi", "-i", f"sine=f={hz}:d={seconds}", "-shortest", "-c:v", "libx264",
                        "-c:a", "aac", str(p)], check=True)
        return p

    def _tones(self, path, times):
        import numpy as np
        pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "8000", "-f", "s16le", "-"],
                             capture_output=True, check=True).stdout
        a = np.frombuffer(pcm, np.int16).astype(float)
        out = []
        for t in times:
            seg = a[int(t * 8000): int((t + 0.4) * 8000)]
            if len(seg) < 400 or np.abs(seg).max() < 200:
                out.append(0)
                continue
            f = np.fft.rfft(seg * np.hanning(len(seg)))
            out.append(int(np.argmax(np.abs(f)) * 8000 / len(seg)))
        return out

    def test_audio_choices(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = self._clip(d, "a.mp4", 440, 2), self._clip(d, "b.mp4", 880, 3)
            expect = {                                 # tone at t = 0.5 s (A's part) and 3.0 s (B's part)
                "A then B (follows the picture)": [440, 880],
                "A only": [440, 0],
                "B only (after A)": [0, 880],
                "Silent": None,
            }
            for choice, want in expect.items():
                out = Path(d, "o.avi")
                r = subprocess.run([sys.executable, "-m", "videobeaux.cli", "-P", "crossmosh", "-i", str(a), "--b-input",
                                    str(b), "-o", str(out), "-F", "--audio", choice], cwd=REPO, capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stdout[-400:] + r.stderr[-400:])
                if want is None:
                    streams = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of",
                                              "csv=p=0", str(out)], capture_output=True, text=True).stdout
                    self.assertNotIn("audio", streams)
                else:
                    self.assertEqual(self._tones(out, [0.5, 3.0]), want, choice)


if __name__ == "__main__":
    unittest.main()
