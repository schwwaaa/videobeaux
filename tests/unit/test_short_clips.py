"""Effects with a time window must survive short clips: same frame count, never "sound but no picture"."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

HAVE_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))

# programs that look several frames back/ahead (tmedian / amplify / tmix …) — each must give back every frame it was given
WINDOWED = ["t1000", "ghostee", "twociz", "zapruder", "fever", "digital_boss", "smudge", "recalled_sensor", "broken_scroll"]


def frames(path, stream="v:0"):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", stream, "-count_packets", "-show_entries",
                        "stream=nb_read_packets", "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    out = r.stdout.strip()
    return int(out) if out.isdigit() else 0


@unittest.skipUnless(HAVE_FFMPEG, "needs ffmpeg + ffprobe")
class ShortClips(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="vb_short_"))
        cls.clips = {}
        for name, secs in (("tiny", 0.25), ("short", 2.2)):
            p = cls.tmp / f"{name}.mp4"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc2=s=160x90:r=24:d={secs}", "-f", "lavfi",
                            "-i", f"sine=d={secs}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(p)],
                           check=True)
            cls.clips[name] = p

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _run(self, prog, clip, *extra):
        out = self.tmp / f"{prog}_{clip.stem}_{'_'.join(extra) or 'default'}.mp4"
        r = subprocess.run([sys.executable, "-m", "videobeaux.cli", "-P", prog, "-i", str(clip), "-o", str(out), "-F", *extra],
                           cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, f"{prog}: " + (r.stdout + r.stderr)[-400:])
        return out

    def test_windowed_effects_keep_every_frame_even_on_tiny_clips(self):
        for prog in WINDOWED:
            for name, clip in self.clips.items():
                with self.subTest(prog=prog, clip=name):
                    n_in = frames(clip)
                    out = self._run(prog, clip)
                    n_out = frames(out)
                    self.assertGreater(n_out, 0, f"{prog} gave no picture on a {n_in}-frame clip")
                    self.assertGreaterEqual(n_out, n_in, f"{prog} lost frames: {n_in} → {n_out}")

    def test_chain_through_t1000_survives_a_short_clip(self):
        # the failing layout: LSD Feedback → T-1000 → VHS Tracking, on a 2.2 s clip
        a = self._run("lsd_feedback", self.clips["short"], "--amount", "0.75")
        b = self._run("t1000", a, "--amount", "0.8")
        c = self._run("vhs_tracking", b)
        self.assertEqual(frames(c), frames(self.clips["short"]))

    def test_a_step_that_swallows_the_picture_is_reported_at_that_step(self):
        from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
        clip = self.clips["short"]
        out = self.tmp / "swallowed.mp4"
        cmd = ["ffmpeg", "-y", "-i", str(clip), "-filter_complex", "[0:v]tmedian=radius=40[out_v]", "-map", "[out_v]",
               "-map", "0:a?", str(out)]
        with self.assertRaises(RuntimeError) as cm:
            run_ffmpeg_with_progress(cmd, str(clip), str(out))
        self.assertIn("no picture", str(cm.exception))


if __name__ == "__main__":
    unittest.main()


class T1000Graph(unittest.TestCase):
    def test_working_size_and_scaled_shifts(self):
        from videobeaux.programs.t1000 import build_graph
        g, work = build_graph(1920, 1080, 540)
        self.assertEqual(work, (960, 540))
        self.assertTrue(g.startswith("[0:v]scale=960:540:flags=area,tpad="))
        self.assertTrue(g.endswith("scale=1920:1080:flags=bicubic[out_v]"))
        self.assertIn("rh=-1", g)                              # -2 px at 1080p → -1 px at 540p
        self.assertIn("ah=-6", g)                              # -12 px → -6 px
        g, work = build_graph(1280, 720, 0)                    # 0 = full size: no scaling, original offsets
        self.assertIsNone(work)
        self.assertNotIn("scale=", g)
        self.assertIn("ah=-12", g)
        g, work = build_graph(640, 360, 540)                   # already smaller than the working size: untouched
        self.assertIsNone(work)

    def test_odd_sizes_scale_back_to_even(self):
        from videobeaux.programs.t1000 import build_graph
        g, work = build_graph(1281, 721, 360)
        self.assertTrue(all(v % 2 == 0 for v in work))
        self.assertIn("scale=1280:720:flags=bicubic", g)
