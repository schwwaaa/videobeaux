import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

HAVE_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


class Geometry(unittest.TestCase):
    def test_quad_cells_are_even_and_inside_the_frame(self):
        from videobeaux.programs.quad_split import LAYOUTS, cells
        for layout in LAYOUTS:
            rects = cells(layout, 1280, 720, 6)
            self.assertEqual(len(rects), {"2x2 grid": 4, "side by side (2)": 2, "stacked (2)": 2, "1 big + 3 small": 4}[layout])
            for x, y, w, h in rects:
                self.assertTrue(all(v % 2 == 0 for v in (x, y, w, h)), (layout, (x, y, w, h)))
                self.assertLessEqual(x + w, 1280)
                self.assertLessEqual(y + h, 720)

    def test_pip_positions(self):
        from videobeaux.programs.picture_in_picture import overlay_position
        self.assertEqual(overlay_position("top left", 5, 0, 0)[0], "main_w*0.0500")
        self.assertIn("overlay_w", overlay_position("bottom right", 5, 0, 0)[0])
        self.assertIn("0.2500", overlay_position("custom", 5, 25, 75)[0])

    def test_flash_times_parse(self):
        from videobeaux.programs.fade_flash import parse_times
        self.assertEqual(parse_times("1.5, 4;6.25"), [1.5, 4.0, 6.25])
        with self.assertRaises(SystemExit):
            parse_times("soon")

    def test_proc_amp_filter(self):
        import argparse
        from videobeaux.programs import proc_amp
        p = argparse.ArgumentParser()
        proc_amp.register_arguments(p)
        f = proc_amp.build_filter(p.parse_args(["--black_level", "0.1", "--white_level", "0.9", "--temperature", "5000"]))
        self.assertIn("colorlevels=rimin=0.1", f)
        self.assertIn("colortemperature=temperature=5000", f)


class ColorPass(unittest.TestCase):
    def test_keeps_the_color_and_grays_the_rest(self):
        try:
            import cv2
        except ImportError:
            self.skipTest("needs OpenCV")
        import numpy as np
        from videobeaux.programs.color_pass import color_pass_frame
        img = np.zeros((20, 40, 3), np.uint8)
        img[:, :20] = (255, 0, 0)       # red
        img[:, 20:] = (0, 0, 255)       # blue
        out = color_pass_frame(cv2, img, 0.0, 30.0, 20.0, 0.15, 1.0, 1.0, True)
        self.assertGreater(int(out[10, 5, 0]), 240)                       # red stays red
        self.assertLess(int(out[10, 5, 2]), 15)
        self.assertLess(int(np.ptp(out[10, 30])), 3)                      # blue became gray
        inv = color_pass_frame(cv2, img, 0.0, 30.0, 20.0, 0.15, 1.0, 1.0, False)
        self.assertLess(int(np.ptp(inv[10, 5])), 3)                       # red removed
        self.assertGreater(int(inv[10, 30, 2]), 240)


@unittest.skipUnless(HAVE_FFMPEG, "needs ffmpeg")
class Rendering(unittest.TestCase):
    def _clip(self, d, name, color, size="160x120", seconds=2):
        p = Path(d, name)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c={color}:s={size}:r=12:d={seconds}",
                        "-f", "lavfi", "-i", f"sine=d={seconds}", "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", str(p)], check=True)
        return p

    def _run(self, prog, *args):
        r = subprocess.run([sys.executable, "-m", "videobeaux.cli", "-P", prog, *args], cwd=REPO, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout[-500:] + r.stderr[-500:])

    def _px(self, path, x, y, t=0.5, w=160):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(path), "-frames:v", "1", "-vf",
                              "scale=in_color_matrix=bt709:in_range=tv,format=rgb24", "-f", "rawvideo", "-"],
                             capture_output=True, check=True).stdout
        i = (y * w + x) * 3
        return tuple(raw[i:i + 3])

    def test_picture_in_picture_places_the_inset(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = self._clip(d, "a.mp4", "red"), self._clip(d, "b.mp4", "blue")
            out = Path(d, "o.mp4")
            self._run("picture_in_picture", "-i", str(a), "--input2", str(b), "-o", str(out), "-F", "--position", "bottom right")
            r, g, bl = self._px(out, 140, 105)
            self.assertGreater(bl, 200)
            self.assertLess(r, 60)
            self.assertGreater(self._px(out, 10, 10)[0], 200)

    def test_quad_split_corners(self):
        with tempfile.TemporaryDirectory() as d:
            clips = [self._clip(d, f"{n}.mp4", c) for n, c in zip("abcd", ("red", "blue", "lime", "yellow"))]
            out = Path(d, "o.mp4")
            self._run("quad_split", "-i", str(clips[0]), "--input2", str(clips[1]), "--input3", str(clips[2]),
                      "--input4", str(clips[3]), "-o", str(out), "-F")
            tl, tr, bl, br = self._px(out, 10, 10), self._px(out, 150, 10), self._px(out, 10, 110), self._px(out, 150, 110)
            self.assertGreater(tl[0], 200); self.assertLess(tl[2], 60)          # red
            self.assertGreater(tr[2], 200); self.assertLess(tr[0], 60)          # blue
            self.assertGreater(bl[1], 200); self.assertLess(bl[0], 60)          # green
            self.assertGreater(br[0], 200); self.assertGreater(br[1], 200)      # yellow

    def test_fade_in_starts_black_and_flash_is_bright(self):
        with tempfile.TemporaryDirectory() as d:
            a = self._clip(d, "a.mp4", "gray", seconds=3)
            out = Path(d, "o.mp4")
            self._run("fade_flash", "-i", str(a), "-o", str(out), "-F", "--fade_in", "1", "--fade_out", "0",
                      "--flash_times", "1.5", "--flash_style", "hard (on/off)")
            self.assertLess(max(self._px(out, 80, 60, t=0.0)), 40)
            self.assertGreater(min(self._px(out, 80, 60, t=1.6)), 220)
            self.assertAlmostEqual(self._px(out, 80, 60, t=2.5)[0], 128, delta=12)

    def test_freeze_frame_modes(self):
        import numpy as np
        with tempfile.TemporaryDirectory() as d:
            src = Path(d, "s.mp4")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=160x120:r=12:d=4", "-c:v", "libx264",
                            "-pix_fmt", "yuv420p", str(src)], check=True)
            for mode, frames in (("hold in place (same length)", 48), ("insert (clip gets longer)", 60)):
                out = Path(d, "o.mp4")
                self._run("freeze_frame", "-i", str(src), "-o", str(out), "-F", "--at", "1", "--length", "1", "--mode", mode)
                raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(out), "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                                     capture_output=True, check=True).stdout
                a = np.frombuffer(raw, np.uint8).reshape(-1, 120, 160).astype(float)
                self.assertEqual(len(a), frames, mode)
                diffs = np.abs(np.diff(a, axis=0)).mean(axis=(1, 2))
                self.assertGreaterEqual(int((diffs < 0.6).sum()), 10, mode)       # a run of still frames

    def test_strobe_hold_repeats_frames(self):
        import numpy as np
        with tempfile.TemporaryDirectory() as d:
            src = Path(d, "s.mp4")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=160x120:r=12:d=2", "-c:v", "libx264",
                            "-pix_fmt", "yuv420p", str(src)], check=True)
            out = Path(d, "o.mp4")
            self._run("strobe_hold", "-i", str(src), "-o", str(out), "-F", "--hold", "4")
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(out), "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                                 capture_output=True, check=True).stdout
            a = np.frombuffer(raw, np.uint8).reshape(-1, 120, 160).astype(float)
            diffs = np.abs(np.diff(a, axis=0)).mean(axis=(1, 2))
            self.assertGreaterEqual(int((diffs < 0.8).sum()), len(diffs) * 0.6)   # ~3 of every 4 steps are still


if __name__ == "__main__":
    unittest.main()
