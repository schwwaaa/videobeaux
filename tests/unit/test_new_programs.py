"""
The newer programs, each run on a short clip through the CLI, plus the Remove Background → Key Composite handoff.
Uses the bundled ffmpeg (gui/resources/ffmpeg) when it is there, since it has every filter these need.
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from videobeaux.programs.text_overlay import _render_title
from videobeaux.utils.ffmpeg_operations import get_video_duration
from videobeaux.utils.frame_pipe import iter_frames

ROOT = Path(__file__).resolve().parents[2]
BUNDLED = ROOT / "gui" / "resources" / "ffmpeg"


def _env():
    env = dict(os.environ)
    if BUNDLED.exists():
        env["PATH"] = f"{BUNDLED}{os.pathsep}{env.get('PATH', '')}"
    return env


def _ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *args], check=True, env=_env())


def _run(program, src, out, *extra):
    result = subprocess.run(
        [sys.executable, "-m", "videobeaux.cli", "-P", program, "-i", str(src), "-o", str(out), "-F", *extra],
        cwd=ROOT, env=_env(), capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise AssertionError(f"{program} failed:\n{result.stdout[-600:]}\n{result.stderr[-600:]}")
    return Path(out)


class TextOverlaySize(unittest.TestCase):
    def test_long_text_wraps_at_the_same_size_instead_of_shrinking(self):
        with tempfile.TemporaryDirectory() as d:
            one, many = Path(d) / "one.png", Path(d) / "many.png"
            _render_title("Hello", "Arial", 76, "#FFFFFF", "#000000", 1280, 720, one)
            _render_title("This is a much longer title that has to wrap onto several lines at the same font size",
                          "Arial", 76, "#FFFFFF", "#000000", 1280, 720, many)
            line = int(76 * 1.2)                       # the line pitch at 76 px
            with Image.open(many) as big, Image.open(one) as small:
                extra = big.height - small.height
            self.assertGreater(extra, 0)
            self.assertEqual(extra % line, 0, "a longer title should add whole lines at the same pitch")


class NewPrograms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        d = Path(cls._tmp.name)
        cls.d = d
        cls.clip = d / "clip.mp4"
        _ffmpeg("-f", "lavfi", "-i", "testsrc2=size=320x240:rate=25",
                "-f", "lavfi", "-i", "sine=f=440:sample_rate=48000", "-t", "2",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(cls.clip))
        cls.silent = d / "silent.mp4"
        _ffmpeg("-f", "lavfi", "-i", "testsrc2=size=320x240:rate=25", "-t", "2",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", str(cls.silent))
        cls.srt = d / "it's a test.srt"
        cls.srt.write_text("1\n00:00:00,200 --> 00:00:01,500\nHello there\n\n", encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def assertSameLength(self, out):
        self.assertAlmostEqual(get_video_duration(str(out)), get_video_duration(str(self.clip)), delta=0.3)

    def test_audio_visualizer_bars_full_frame(self):
        self.assertSameLength(_run("audio_visualizer", self.clip, self.d / "av.mp4", "--style", "bars", "--position", "full"))

    def test_audio_visualizer_wave_strip(self):
        self.assertSameLength(_run("audio_visualizer", self.clip, self.d / "avw.mp4", "--style", "wave", "--position", "top"))

    def test_audio_visualizer_needs_audio(self):
        with self.assertRaises(AssertionError):
            _run("audio_visualizer", self.silent, self.d / "av_none.mp4")

    def test_ken_burns(self):
        self.assertSameLength(_run("ken_burns", self.clip, self.d / "kb.mp4", "--end_zoom", "1.5", "--focus_x", "0.2"))

    def test_loudness_normalize(self):
        self.assertSameLength(_run("loudness_normalize", self.clip, self.d / "ln.mp4", "--target", "-16"))

    def test_audio_denoise(self):
        self.assertSameLength(_run("audio_denoise", self.clip, self.d / "ad.mp4", "--reduction", "10"))

    def test_deinterlace(self):
        self.assertSameLength(_run("deinterlace", self.clip, self.d / "di.mp4", "--method", "bwdif"))

    def test_denoise_video(self):
        self.assertSameLength(_run("denoise_video", self.clip, self.d / "dn.mp4", "--strength", "strong"))

    def test_lens_correct(self):
        self.assertSameLength(_run("lens_correct", self.clip, self.d / "lc.mp4", "--k1", "-0.2"))

    def test_local_contrast(self):
        self.assertSameLength(_run("local_contrast", self.clip, self.d / "lcn.mp4", "--clip", "2", "--tiles", "8"))

    def test_motion_mask(self):
        self.assertSameLength(_run("motion_mask", self.clip, self.d / "mm.mp4", "--mode", "isolate"))

    def test_subtitle_burn_accepts_an_awkward_file_name(self):
        out = _run("subtitle_burn", self.clip, self.d / "sub.mp4", "--srt", str(self.srt), "--position", "top")
        self.assertSameLength(out)

    def test_pixel_sort_with_the_new_options(self):
        self.assertSameLength(_run("pixel_sort", self.clip, self.d / "ps.mp4", "--sort_by", "hue", "--min_run", "4",
                                   "--mix", "0.8", "--select", "darker"))


class KeyComposite(unittest.TestCase):
    def test_matte_subject_is_kept_and_the_rest_takes_the_background(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            source, matte = d / "red.mp4", d / "matte.mp4"
            _ffmpeg("-f", "lavfi", "-i", "color=c=red:s=320x240:d=1:r=25", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(source))
            # white disc on black: white = keep
            _ffmpeg("-f", "lavfi", "-i", "color=c=black:s=320x240:d=1:r=25,"
                    "geq=lum='if(lt(hypot(X-160,Y-120),50),255,0)':cb=128:cr=128",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(matte))
            out = _run("key_composite", source, d / "kc.mp4", "--matte", str(matte),
                       "--background", "color", "--bg_color", "#00FF00")
            frames = iter_frames(out)
            _, frame = next(frames)
            frames.close()
            centre, corner = frame[120, 160].astype(int), frame[5, 5].astype(int)
            self.assertTrue(centre[0] > 180 and centre[1] < 80, f"subject should stay red, got {centre}")
            self.assertTrue(corner[1] > 180 and corner[0] < 80, f"background should be green, got {corner}")


if __name__ == "__main__":
    unittest.main()
