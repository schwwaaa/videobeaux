"""
Sharpen, Audio Duck, Clean Plate and Color Match, each run on a short synthetic clip and checked numerically.
Uses the bundled ffmpeg (gui/resources/ffmpeg) when it is there.
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

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


def _frames(path, wanted):
    wanted = set(wanted)
    found = {}
    frames = iter_frames(path)
    for i, f in frames:
        if i in wanted:
            found[i] = f
        if len(found) == len(wanted):
            break
    frames.close()
    return found


def _audio(path):
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-f", "f32le", "-ac", "1", "-ar", "48000", "-"],
                         capture_output=True, env=_env()).stdout
    return np.frombuffer(out, dtype=np.float32)


def _tone_at(x, t0, t1, hz):
    seg = x[int(t0 * 48000):int(t1 * 48000)]
    spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
    freqs = np.fft.rfftfreq(len(seg), 1 / 48000)
    k = int(np.argmin(np.abs(freqs - hz)))
    return float(spec[max(0, k - 3):k + 4].max())


class Fixes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        d = Path(cls._tmp.name)
        cls.d = d
        cls.voice = d / "voice.mp4"       # 440 Hz "speech" for 1 s, silence for 1 s, repeated
        _ffmpeg("-f", "lavfi", "-i", "testsrc2=size=320x240:rate=25",
                "-f", "lavfi", "-i", "aevalsrc='0.5*sin(2*PI*440*t)*lt(mod(t,2),1)':s=48000", "-t", "6",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(cls.voice))
        cls.music = d / "music.mp4"       # 220 Hz bed
        _ffmpeg("-f", "lavfi", "-i", "color=c=0x808080:s=320x240:r=25",
                "-f", "lavfi", "-i", "sine=f=220:sample_rate=48000", "-t", "6",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(cls.music))
        cls.subject = d / "subject.mp4"   # static blue scene with an orange box sliding across it
        _ffmpeg("-f", "lavfi", "-i", "color=c=0x204080:s=320x240:r=25",
                "-f", "lavfi", "-i", "color=c=0xFFA500:s=60x80:r=25",
                "-filter_complex", "[0:v][1:v]overlay=x='20+t*60':y=80:shortest=1", "-t", "3",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", str(cls.subject))
        cls.warm = d / "warm.mp4"
        _ffmpeg("-f", "lavfi", "-i", "color=c=0x806040:s=320x240:d=3:r=25", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(cls.warm))
        cls.blue = d / "blue.mp4"
        _ffmpeg("-f", "lavfi", "-i", "color=c=0x0040ff:s=320x240:d=2:r=25", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(cls.blue))

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_sharpen_raises_edge_contrast(self):
        out = _run("sharpen", self.voice, self.d / "sharp.mp4", "--amount", "1.2")
        import cv2

        def edge_var(path):
            frame = _frames(path, [10])[10]
            return float(cv2.Laplacian(cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY), cv2.CV_64F).var())

        self.assertGreater(edge_var(out), edge_var(self.voice) * 1.5)

    def test_audio_duck_drops_music_while_speech_plays(self):
        out = _run("audio_duck", self.voice, self.d / "duck.mp4", "--music", str(self.music), "--music_db", "-6")
        ducked = _audio(out)
        bed = _audio(self.music)
        during = _tone_at(ducked, 0.2, 0.8, 220) / max(_tone_at(bed, 0.2, 0.8, 220), 1e-9)
        # speech is on 0-1 s, 2-3 s, 4-5 s; 1.6-1.95 s is after the voice stopped and the 400 ms release has begun
        after = _tone_at(ducked, 1.6, 1.95, 220) / max(_tone_at(bed, 1.6, 1.95, 220), 1e-9)
        self.assertLess(during, 0.2, "music should be well down under speech")
        self.assertGreater(after, during * 2, "music should come back once speech stops")

    def test_clean_plate_removes_the_moving_box(self):
        def orange(f):
            r, g, b = f[..., 0].astype(int), f[..., 1].astype(int), f[..., 2].astype(int)
            return int(((r > 200) & (g > 120) & (g < 200) & (b < 90)).sum())

        out = _run("clean_plate", self.subject, self.d / "plate.mp4")
        self.assertGreater(orange(_frames(self.subject, [25])[25]), 1000)
        self.assertEqual(orange(_frames(out, [25])[25]), 0)
        plate_only = _run("clean_plate", self.subject, self.d / "plate_only.mp4", "--mode", "plate_only")
        self.assertEqual(orange(_frames(plate_only, [25])[25]), 0)

    def test_color_match_moves_the_colour_to_the_reference(self):
        out = _run("color_match", self.warm, self.d / "matched.mp4", "--reference", str(self.blue), "--strength", "1.0")
        before = _frames(self.warm, [10])[10].reshape(-1, 3).mean(0)
        after = _frames(out, [10])[10].reshape(-1, 3).mean(0)
        ref = _frames(self.blue, [10])[10].reshape(-1, 3).mean(0)
        self.assertLess(np.abs(after - ref).mean(), np.abs(before - ref).mean() / 4)


if __name__ == "__main__":
    unittest.main()
