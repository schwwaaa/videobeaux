"""Every program has something to configure; the dry/wet Amount leaves default behaviour untouched and mixes correctly."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from videobeaux.utils.preset_filter import AMOUNT_METADATA, apply_amount  # noqa: E402

HAVE_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
NO_KNOB_ALLOWED = set()

GRAPH = ["ffmpeg", "-i", "in.mp4", "-filter_complex", "[0:v]negate[out_v]", "-map", "[out_v]", "-map", "0:a?", "out.mp4"]


class ApplyAmount(unittest.TestCase):
    def test_full_amount_returns_the_command_untouched(self):
        self.assertEqual(apply_amount(GRAPH, 1.0), GRAPH)
        self.assertEqual(apply_amount(GRAPH, 1), GRAPH)
        self.assertEqual(apply_amount(GRAPH, None), GRAPH)          # unparsable → full effect

    def test_partial_amount_wraps_the_graph_and_keeps_everything_else(self):
        out = apply_amount(GRAPH, 0.25)
        g = out[out.index("-filter_complex") + 1]
        self.assertTrue(g.startswith("[0:v]negate[fx];"))
        self.assertTrue(g.endswith("[out_v]"))
        self.assertIn("blend=all_mode=normal:all_opacity=0.250", g)
        self.assertEqual([t for t in out if t != g], [t for t in GRAPH if t != GRAPH[4]])
        self.assertEqual(g.count("[out_v]"), 1)                      # only the final output keeps the public label

    def test_clamps(self):
        self.assertIn("all_opacity=0.000", apply_amount(GRAPH, -3)[4])
        self.assertEqual(apply_amount(GRAPH, 7), GRAPH)

    def test_plain_vf_chain_becomes_a_graph_with_mapping(self):
        cmd = ["ffmpeg", "-i", "in.mp4", "-vf", "tmix=frames=8", "-crf", "23", "out.mp4"]
        out = apply_amount(cmd, 0.5)
        self.assertNotIn("-vf", out)
        i = out.index("-filter_complex")
        self.assertTrue(out[i + 1].startswith("[0:v]tmix=frames=8[fx];"))
        self.assertEqual(out[i + 2:i + 6], ["-map", "[out_v]", "-map", "0:a?"])
        self.assertEqual(out[-3:], ["-crf", "23", "out.mp4"][-3:])

    def test_unknown_graph_shape_is_left_alone(self):
        cmd = ["ffmpeg", "-i", "a", "-filter_complex", "[0:v]negate[v]", "-map", "[v]", "o.mp4"]
        self.assertEqual(apply_amount(cmd, 0.5), cmd)

    def test_metadata_shape(self):
        m = AMOUNT_METADATA["args"]["amount"]
        self.assertEqual((m["min"], m["max"]), (0, 1))


class EveryProgramHasAKnob(unittest.TestCase):
    def test_discovery_shows_at_least_one_configurable_value_per_program(self):
        out = subprocess.run([sys.executable, str(ROOT / "gui" / "discover_programs.py")], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout
        data = json.loads(out)
        none = []
        for pid, info in data.items():
            if pid in NO_KNOB_ALLOWED:
                continue
            configurable = [a for a in info.get("args", []) if not a.get("hidden") and a.get("type") not in ("file", "video", "folder")]
            if not configurable:
                none.append(pid)
        self.assertEqual(none, [], "give these programs at least one GUI-visible setting")


@unittest.skipUnless(HAVE_FFMPEG, "needs ffmpeg + ffprobe")
class Rendering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="vb_amount_"))
        cls.src = cls.tmp / "src.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=160x90:r=25:d=2", "-f", "lavfi",
                        "-i", "sine=d=2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(cls.src)],
                       check=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _frames(self, path, n=20):
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", "fps=10,scale=80:45,format=gray",
                            "-frames:v", str(n), "-f", "rawvideo", "-"], capture_output=True, check=True)
        a = np.frombuffer(r.stdout, np.uint8)
        k = len(a) // (80 * 45)
        return a[:k * 80 * 45].reshape(k, -1).astype(float)

    def _run(self, prog, amount=None):
        out = self.tmp / f"{prog}_{amount}.mp4"
        cmd = [sys.executable, "-m", "videobeaux.cli", "-P", prog, "-i", str(self.src), "-o", str(out), "-F"]
        if amount is not None:
            cmd += ["--amount", str(amount)]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout[-500:] + r.stderr[-500:])
        self.assertTrue(out.exists() and out.stat().st_size > 0)
        return out

    def test_amount_zero_is_the_source_and_half_is_in_between(self):
        # digital_boss: filter_complex graph · lsd_feedback: plain -vf chain
        for prog in ("digital_boss", "lsd_feedback"):
            with self.subTest(prog=prog):
                src = self._frames(self.src)
                d = {}
                for a in (0, 0.5, None):
                    f = self._frames(self._run(prog, a))
                    n = min(len(src), len(f))
                    d[a] = float(np.abs(f[:n] - src[:n]).mean())
                self.assertLess(d[0], 1.5, d)
                self.assertGreater(d[0.5], d[0] + 1.0, d)
                self.assertGreater(d[None], d[0.5] + 1.0, d)

    def test_reverse_audio_choices(self):
        for choice, want_audio in (("Reversed", True), ("Forward", True), ("Mute", False)):
            with self.subTest(choice=choice):
                out = self.tmp / f"rev_{choice}.mp4"
                r = subprocess.run([sys.executable, "-m", "videobeaux.cli", "-P", "reverse", "-i", str(self.src), "-o", str(out),
                                    "-F", "--audio", choice], cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stdout[-400:] + r.stderr[-400:])
                p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_name",
                                    "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout.strip()
                self.assertEqual(bool(p), want_audio)

    def test_boomerang_loops_lengthen_the_clip(self):
        def dur(path):
            return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                                        capture_output=True, text=True).stdout.strip())
        outs = {}
        for loops in (1, 2):
            out = self.tmp / f"boom_{loops}.mp4"
            r = subprocess.run([sys.executable, "-m", "videobeaux.cli", "-P", "boomerang", "-i", str(self.src), "-o", str(out),
                                "-F", "--loops", str(loops)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout[-400:] + r.stderr[-400:])
            outs[loops] = dur(out)
        self.assertAlmostEqual(outs[2] / outs[1], 2.0, delta=0.15)


if __name__ == "__main__":
    unittest.main()
