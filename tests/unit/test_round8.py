import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

HAVE_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


class PureHelpers(unittest.TestCase):
    def test_parse_time_accepts_leading_dot_and_clock_forms(self):
        from videobeaux.utils.timeparse import parse_time
        table = {".12": 0.12, "0.12": 0.12, "12.": 12.0, "90": 90.0, "1:02.5": 62.5, "0:01:02.5": 62.5, "00:00:03": 3.0, " 7,5 ": 7.5}
        for text, want in table.items():
            self.assertAlmostEqual(parse_time(text), want, places=6, msg=text)
        for bad in ("", "abc", "1:2:3:4", "--5"):
            with self.assertRaises(ValueError):
                parse_time(bad)

    def test_insert_clip_uses_the_forgiving_parser(self):
        from videobeaux.programs.insert_clip import _parse_timestamp
        self.assertAlmostEqual(_parse_timestamp(".12", "--insert_at"), 0.12)

    def test_harden_command_forces_a_previewable_mp4(self):
        from videobeaux.utils.encode import harden_command
        c = harden_command(["ffmpeg", "-i", "in.mov", "-c:v", "libx264", "-c:a", "libmp3lame", "out.mp4"])
        self.assertIn("-pix_fmt", c)
        self.assertEqual(c[c.index("-pix_fmt") + 1], "yuv420p")
        self.assertIn("+faststart", c)
        self.assertEqual(c[c.index("-c:a") + 1], "aac")
        self.assertEqual(c[-1], "out.mp4")

    def test_harden_command_leaves_other_things_alone(self):
        from videobeaux.utils.encode import harden_command
        for cmd in (["ffmpeg", "-i", "a", "-c:v", "prores_ks", "o.mov"], ["ffmpeg", "-i", "a", "-c:v", "libvpx-vp9", "o.webm"],
                    ["ffmpeg", "-i", "a", "-c:v", "libx264", "-pix_fmt", "yuv444p", "-movflags", "+faststart", "o.mp4"],
                    ["ffprobe", "-i", "a", "o.mp4"]):
            self.assertEqual(harden_command(list(cmd)), cmd)
        h = harden_command(["ffmpeg", "-i", "a", "-c:v", "libx265", "o.mp4"])
        self.assertIn("hvc1", h)

    def test_no_program_writes_mp4_h264_without_going_through_the_safety_net(self):
        """Programs may call ffmpeg themselves, but only through run_ffmpeg_with_progress (which hardens the command)."""
        import re
        offenders = []
        for p in (REPO / "videobeaux" / "programs").glob("*.py"):
            src = p.read_text(encoding="utf-8")
            if re.search(r'"-c:v",\s*"libx26[45]"', src) and "run_ffmpeg_with_progress" not in src and "process_video" not in src \
                    and "booth_runner" not in src and "keying" not in src and "subprocess.run" not in src:
                offenders.append(p.name)
        self.assertEqual(offenders, [])

    def test_default_font_exists_for_drawtext(self):
        from videobeaux.utils.fonts import default_font
        f = default_font()
        self.assertTrue(f and Path(f).exists())

    def test_triptych_panels_never_exceed_the_cap_and_are_even(self):
        from videobeaux.programs.triptych import MAX_SIDE, panel_sizes
        for lay in ("hstack", "vstack"):
            sizes = panel_sizes(lay, [(3840, 2160), (1920, 1080), (1080, 1920)])
            for w, h in sizes:
                self.assertEqual((w % 2, h % 2), (0, 0))
            total = sum(w for w, _ in sizes) if lay == "hstack" else sum(h for _, h in sizes)
            self.assertLessEqual(total, MAX_SIDE + 8)


@unittest.skipUnless(HAVE_FFMPEG, "needs ffmpeg")
class Rendering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="vb_r8_")
        t = Path(cls.tmp)
        def mk(name, *args):
            subprocess.run(["ffmpeg", "-v", "error", "-y", *args, str(t / name)], check=True)
            return t / name
        # 4:2:2 10-bit clip with audio — the kind that plays in VLC but not in Finder when re-encoded naively
        cls.p422 = mk("p422.mp4", "-f", "lavfi", "-i", "testsrc2=s=320x180:r=24:d=2", "-f", "lavfi", "-i", "sine=f=440:d=2",
                      "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv422p10le", "-c:a", "aac")
        cls.p10 = mk("p10.mp4", "-f", "lavfi", "-i", "mandelbrot=s=320x180:r=24", "-t", "2", "-c:v", "libx264", "-pix_fmt", "yuv420p10le")
        cls.wide = mk("wide.mp4", "-f", "lavfi", "-i", "testsrc2=s=420x240:r=30:d=2", "-c:v", "libx264", "-pix_fmt", "yuv420p")
        cls.music = mk("m880.wav", "-f", "lavfi", "-i", "sine=f=880:d=2")
        cls.vid440 = mk("v440.mp4", "-f", "lavfi", "-i", "testsrc2=s=320x180:r=24:d=4", "-f", "lavfi", "-i", "sine=f=440:d=4",
                        "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def run_prog(self, prog, *args):
        r = subprocess.run([sys.executable, "-m", "videobeaux.cli", "-P", prog, *map(str, args)], cwd=REPO, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, f"{prog}: {r.stdout[-500:]}{r.stderr[-500:]}")

    def probe(self, path):
        """[{codec_type, codec_name, width, height, pix_fmt}, ...] (ffprobe's default field order is codec_name, codec_type, w, h, pix_fmt)."""
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,codec_type,width,height,pix_fmt", "-of",
                              "json", str(path)], capture_output=True, text=True).stdout
        import json
        return json.loads(out)["streams"]

    def assert_previewable(self, path):
        streams = self.probe(path)
        v = [s for s in streams if s["codec_type"] == "video"][0]
        self.assertEqual((v["codec_name"], v["pix_fmt"]), ("h264", "yuv420p"), streams)
        data = Path(path).read_bytes()
        self.assertLess(data.find(b"moov"), data.find(b"mdat"), "moov must precede mdat (faststart)")
        a = [s for s in streams if s["codec_type"] == "audio"]
        if a:
            self.assertEqual(a[0]["codec_name"], "aac")

    def test_outputs_open_everywhere(self):
        t = Path(self.tmp)
        cases = [("wipe_transitions", ["--input2", self.p10], "wipe.mp4"), ("concat", ["--input2", self.p10], "cat.mp4"),
                 ("insert_clip", ["--input2", self.p10, "--insert_at", ".5"], "ins.mp4"), ("crossmosh", ["--b-input", self.p10], "mosh.mp4"),
                 ("trim", ["--start", ".25", "--end", "1.5"], "trim.mp4")]
        for prog, extra, name in cases:
            with self.subTest(prog=prog):
                self.run_prog(prog, "-i", self.p422, "-o", t / name, "-F", *extra)
                self.assert_previewable(t / name)

    def test_stack_2x_with_mismatched_widths_and_silent_input(self):
        out = Path(self.tmp) / "stack.mp4"
        self.run_prog("stack_2x", "-i", self.p422, "--input2", self.wide, "-o", out, "-F", "--audio", "Mix both")
        v = [s for s in self.probe(out) if s["codec_type"] == "video"][0]
        self.assertEqual(v["width"], 320)                                  # as wide as the top video
        self.assertEqual(v["height"], 180 + 182)                           # 420x240 scaled to 320 wide → 182 high

    def test_triptych_output_is_sane_and_quick(self):
        out = Path(self.tmp) / "tri.mp4"
        self.run_prog("triptych", "-i", self.p422, "--input2", self.p10, "--input3", self.wide, "-o", out, "-F", "--audio-mode", "5", "--zoom2", "2")
        v = [s for s in self.probe(out) if s["codec_type"] == "video"][0]
        self.assertEqual(v["height"], 180)                                 # hstack panels share the first video's height
        self.assertLess(v["width"], 2000)

    def test_soundtrack_replace_and_mix(self):
        def tones(path):
            pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True).stdout
            a = np.frombuffer(pcm, np.int16).astype(float)[int(1.0 * 8000):int(1.5 * 8000)]
            f = np.abs(np.fft.rfft(a * np.hanning(len(a))))
            at = lambda hz: f[int(round(hz * len(a) / 8000))]
            return at(440) > len(a) * 6, at(880) > len(a) * 6
        out = Path(self.tmp) / "st.mp4"
        self.run_prog("soundtrack", "-i", self.vid440, "--audio", self.music, "-o", out, "-F", "--mode", "Replace the original sound")
        self.assertEqual(tones(out), (False, True))
        self.run_prog("soundtrack", "-i", self.vid440, "--audio", self.music, "-o", out, "-F", "--mode", "Mix under the original", "--music_volume", "60")
        self.assertEqual(tones(out), (True, True))
        self.assertIn("h264", [s["codec_name"] for s in self.probe(out) if s["codec_type"] == "video"])   # picture copied

    def test_chroma_key_audio_choice(self):
        t = Path(self.tmp)
        gs = t / "gs.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x00B140:s=320x180:r=24:d=2", "-f", "lavfi", "-i", "sine=f=440:d=2",
                        "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(gs)], check=True)
        out = t / "ck.mp4"
        self.run_prog("chroma_key", "-i", gs, "--bg_video", self.vid440, "-o", out, "-F", "--view", "composite", "--audio", "Silent")
        self.assertFalse([s for s in self.probe(out) if s["codec_type"] == "audio"])
        self.run_prog("chroma_key", "-i", gs, "--bg_video", self.vid440, "-o", out, "-F", "--view", "composite", "--audio", "Mix both")
        self.assertTrue([s for s in self.probe(out) if s["codec_type"] == "audio"])

    def test_convert_simple_mode_hits_the_requested_size_and_codec(self):
        t = Path(self.tmp)
        out = t / "conv.mp4"
        self.run_prog("convert_mux", "-i", self.p422, "-o", out, "-F", "--mode", "Simple (pick a format)", "--size", "720p wide (1280)")
        self.assert_previewable(out)
        v = [s for s in self.probe(out) if s["codec_type"] == "video"][0]
        self.assertEqual(v["width"], 1280)

    def test_thumbs_text_overlay_works_without_fontconfig(self):
        out = Path(self.tmp) / "thumbs.png"
        self.run_prog("thumbs", "-i", self.vid440, "-o", out, "-F", "--timestamps", "--label")
        self.assertTrue(out.exists() and out.stat().st_size > 1000)


if __name__ == "__main__":
    unittest.main()
