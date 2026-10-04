import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


class Graphs(unittest.TestCase):
    def test_layer_blend_graph(self):
        from videobeaux.programs.layer_blend import build_graph
        g = build_graph("color burn", 0.75, 0.25, "cover", 640, 360, 24.0, "A (B loops if shorter)", 5.0, 3.0)
        self.assertIn("all_mode=burn", g)
        self.assertIn("clip(A*0.7500+B*0.2500,0,255)", g)
        self.assertIn("crop=640:360", g)

    def test_audio_graph_modes(self):
        from videobeaux.utils.audio_pick import build_graph
        self.assertIn("[0:a]", build_graph("a", 2.0, 0.0, 5.0))
        self.assertNotIn("[1:a]", build_graph("a", 2.0, 0.0, 5.0))
        self.assertNotIn("[0:a]", build_graph("b", 2.0, 0.0, 5.0))
        self.assertIn("adelay=2000|2000", build_graph("b", 2.0, 2.0, 5.0))
        both = build_graph("both", 2.0, 0.0, 5.0)
        self.assertIn("amix=inputs=2", both)
        self.assertIn("apad=whole_dur=5.000[a2]", both)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "needs ffmpeg")
class Rendering(unittest.TestCase):
    def _clip(self, d, name, color, seconds):
        p = Path(d, name)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c={color}:s=64x64:r=10:d={seconds}",
                        "-f", "lavfi", "-i", "sine=d=%s" % seconds, "-shortest", "-c:v", "libx264", "-crf", "0",
                        "-pix_fmt", "yuv444p", "-c:a", "aac", str(p)], check=True)
        return p

    def _run(self, prog, *args):
        r = subprocess.run([sys.executable, "-m", "videobeaux.cli", "-P", prog, *args], cwd=REPO,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout[-500:] + r.stderr[-500:])

    def test_normal_mode_75_25_is_a_weighted_mix(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = self._clip(d, "a.mp4", "0xC86428", 1), self._clip(d, "b.mp4", "0x28A0DC", 1)
            out = Path(d, "o.mp4")
            self._run("layer_blend", "-i", str(a), "--input2", str(b), "-o", str(out), "-F", "--crf", "0")
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(out), "-vf",
                                  "scale=in_color_matrix=bt709:in_range=tv,format=rgb24", "-frames:v", "1",
                                  "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
            px = tuple(raw[32 * 64 * 3 + 32 * 3: 32 * 64 * 3 + 32 * 3 + 3])
            for got, want in zip(px, (160, 115, 85)):
                self.assertLessEqual(abs(got - want), 4, px)

    def test_length_and_audio_options(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = self._clip(d, "a.mp4", "red", 1), self._clip(d, "b.mp4", "blue", 2)
            out = Path(d, "o.mp4")
            self._run("layer_blend", "-i", str(a), "--input2", str(b), "-o", str(out), "-F", "--length", "longest",
                      "--audio", "B")
            info = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration",
                                   "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout
            self.assertIn("video,2.0", info)
            self.assertIn("audio,2.0", info)
            self._run("layer_blend", "-i", str(a), "--input2", str(b), "-o", str(out), "-F", "--audio", "Silent")
            info = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0",
                                   str(out)], capture_output=True, text=True).stdout
            self.assertNotIn("audio", info)


if __name__ == "__main__":
    unittest.main()
