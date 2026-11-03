"""
Colour & Pattern (a source program), Convert Dims (optional format and custom size), Stack 2× (length choice), Text Overlay
spin, and the rule that programs don't echo the ffmpeg command. Uses the bundled ffmpeg (gui/resources/ffmpeg) when it is there.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

from videobeaux.utils.frame_pipe import iter_frames, probe_video

ROOT = Path(__file__).resolve().parents[2]
BUNDLED = ROOT / "gui" / "resources" / "ffmpeg"


def _env():
    env = dict(os.environ)
    if BUNDLED.exists():
        env["PATH"] = f"{BUNDLED}{os.pathsep}{env.get('PATH', '')}"
    return env


def _cli(*args):
    result = subprocess.run([sys.executable, "-m", "videobeaux.cli", *args], cwd=ROOT, env=_env(),
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise AssertionError(f"{args[1]} failed:\n{result.stdout[-600:]}\n{result.stderr[-600:]}")
    return result


def _frame(path, idx):
    for i, f in iter_frames(path):
        if i == idx:
            return f
    raise AssertionError(f"no frame {idx} in {path}")


def _white(path, t, rows=slice(0, 360)):
    """The white pixels of a 640x360 frame at time t, inside the given rows (a boolean mask over those rows)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(path), "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, env=_env(), check=True).stdout
    f = np.frombuffer(raw, np.uint8).reshape(360, 640, 3).astype(int)[rows]
    return (f[..., 0] > 200) & (f[..., 1] > 200) & (f[..., 2] > 200)


def _text_angle(path, t, rows=slice(0, 360)):
    """Tilt in degrees of the white text at time t (0 = upright), from the direction its pixels are spread in."""
    ys, xs = np.nonzero(_white(path, t, rows))
    if len(xs) < 80:
        return None                                  # no text there at this time
    xs, ys = xs - xs.mean(), ys - ys.mean()
    return float(np.degrees(0.5 * np.arctan2(2 * (xs * ys).mean(), (xs * xs).mean() - (ys * ys).mean())))


class Fixes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.d = Path(cls._tmp.name)
        cls.clip = cls.d / "clip.mp4"
        cls.two = cls.d / "two.mp4"
        cls.four = cls.d / "four.mp4"
        ff = ["ffmpeg", "-y", "-v", "error"]
        subprocess.run(ff + ["-f", "lavfi", "-i", "testsrc2=size=640x480:rate=25", "-f", "lavfi", "-i",
                             "sine=f=440:sample_rate=48000", "-t", "4", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                             "-c:a", "aac", str(cls.clip)], check=True, env=_env())
        subprocess.run(ff + ["-f", "lavfi", "-i", "testsrc2=size=320x240:rate=25", "-t", "2", "-c:v", "libx264",
                             "-pix_fmt", "yuv420p", str(cls.two)], check=True, env=_env())
        subprocess.run(ff + ["-f", "lavfi", "-i", "testsrc2=size=320x240:rate=25", "-f", "lavfi", "-i",
                             "sine=f=220:sample_rate=48000", "-t", "4", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                             "-c:a", "aac", str(cls.four)], check=True, env=_env())
        cls.blue_still = cls.d / "blue.mp4"      # plain blue, so white text is easy to find in the picture
        subprocess.run(ff + ["-f", "lavfi", "-i", "color=c=0x204080:s=640x360:r=25", "-t", "3", "-c:v", "libx264",
                             "-pix_fmt", "yuv420p", str(cls.blue_still)], check=True, env=_env())

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_solid_colour_is_the_chosen_colour(self):
        out = self.d / "solid.mp4"
        _cli("-P", "color_pattern", "-o", str(out), "-F", "--pattern", "Solid colour", "--color", "#00FF00",
             "--seconds", "1", "--preset", "480p")
        f = _frame(out, 5)
        self.assertEqual(f.shape[:2], (480, 640))
        centre = f[200:280, 300:340].reshape(-1, 3).mean(0)
        self.assertGreater(centre[1], 230)
        self.assertLess(centre[0] + centre[2], 40)

    def test_gradient_runs_from_colour_to_black(self):
        out = self.d / "gradient.mp4"
        _cli("-P", "color_pattern", "-o", str(out), "-F", "--pattern", "Gradient (colour to black)",
             "--color", "#FF0000", "--seconds", "1", "--preset", "480p")
        f = _frame(out, 5)
        left = f[200:280, 0:20].reshape(-1, 3).mean(0)
        right = f[200:280, 620:640].reshape(-1, 3).mean(0)
        self.assertGreater(left[0], 200)
        self.assertLess(right[0], 30)

    def test_colour_pattern_length_follows_seconds(self):
        out = self.d / "length.mp4"
        _cli("-P", "color_pattern", "-o", str(out), "-F", "--pattern", "Test pattern", "--seconds", "2.5",
             "--width", "320", "--height", "240")
        self.assertAlmostEqual(probe_video(str(out)).duration, 2.5, delta=0.1)

    def test_convert_dims_custom_size_needs_no_output_format(self):
        out = self.d / "custom"                  # no extension, no --output-format
        _cli("-P", "convert_dims", "-i", str(self.clip), "-o", str(out), "-F", "--preset", "custom",
             "--width", "320", "--height", "181", "--mode", "stretch")
        info = probe_video(str(self.d / "custom.mp4"))
        self.assertEqual((info.width, info.height), (320, 180))   # 181 rounds down to even

    def test_convert_dims_preset_alone_still_works(self):
        out = self.d / "preset.mp4"
        _cli("-P", "convert_dims", "-i", str(self.clip), "-o", str(out), "-F", "--preset", "480p")
        info = probe_video(str(out))
        self.assertEqual((info.width, info.height), (640, 480))

    def test_stack_duration_choice(self):
        expect = {"Longest": 4.0, "Top video": 2.0, "Bottom video": 4.0}
        for choice, seconds in expect.items():
            out = self.d / f"stack_{choice.split()[0]}.mp4"
            _cli("-P", "stack_2x", "-i", str(self.two), "-o", str(out), "-F", "--input2", str(self.four),
                 "--duration", choice)
            self.assertAlmostEqual(probe_video(str(out)).duration, seconds, delta=0.1, msg=choice)

    def test_text_overlay_accepts_spin(self):
        out = self.d / "title.mp4"
        _cli("-P", "text_overlay", "-i", str(self.clip), "-o", str(out), "-F", "--text", "Hello", "--spin", "30")
        self.assertTrue(out.exists())

    def test_white_stays_white_when_played_back(self):
        out = self.d / "white.mp4"
        _cli("-P", "color_pattern", "-o", str(out), "-F", "--pattern", "Solid colour", "--color", "#FFFFFF",
             "--seconds", "0.5", "--width", "320", "--height", "180")
        # Decoded the way a player that reads the BT.709 tags does it.
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(out), "-frames:v", "1", "-vf",
                              "scale=in_color_matrix=bt709:in_range=tv:out_range=full:flags=accurate_rnd+full_chroma_int",
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, env=_env(), check=True).stdout
        pixels = np.frombuffer(raw, np.uint8)
        self.assertTrue((pixels >= 254).all(), f"white came out as {pixels[:3]}")

    def test_wobble_swings_out_back_through_upright_and_the_other_way(self):
        out = self.d / "wobble.mp4"
        _cli("-P", "text_overlay", "-i", str(self.blue_still), "-o", str(out), "-F", "--text", "HELLO",
             "--font_size", "90", "--placement", "center", "--wobble", "30", "--wobble_period", "2")
        upright = _text_angle(out, 1.0)          # half a period: back to upright
        one_side = _text_angle(out, 0.5)         # quarter period: out to one side
        other_side = _text_angle(out, 1.5)       # three quarters: out to the other side
        self.assertLess(abs(upright), 5)
        self.assertGreater(one_side, 15)
        self.assertLess(other_side, -15)
        self.assertAlmostEqual(one_side, -other_side, delta=5)

    def test_spin_actually_turns_a_still_image(self):
        out = self.d / "spin.mp4"
        _cli("-P", "text_overlay", "-i", str(self.blue_still), "-o", str(out), "-F", "--text", "HELLO",
             "--font_size", "90", "--placement", "center", "--spin", "45")
        self.assertLess(abs(_text_angle(out, 0.0)), 5)
        self.assertGreater(_text_angle(out, 1.0), 25)   # 45 degrees a second

    def test_lagkage_text_layer_has_a_time_window_and_spins_from_its_start(self):
        layout = self.d / "lagkage_spin.json"
        layout.write_text(json.dumps({"sequence_direction": "forward", "layers": [
            {"layer_number": 1, "type": "text", "text": "SPIN", "size": 40, "height_pct": 20, "mode": "free",
             "pos_x_pct": 10, "pos_y_pct": 5, "text_size": 14, "color": "#FFFFFF", "outline_color": "#000000",
             "start": 1, "end": 2.5, "spin": 45, "opacity": 1}]}))
        out = self.d / "lagkage_spin.mp4"
        _cli("-P", "lagkage", "-i", str(self.blue_still), "-o", str(out), "-F", "--layout-json", str(layout))
        self.assertAlmostEqual(probe_video(str(out)).duration, 3.0, delta=0.1)   # the base video's length, not longer
        top = slice(0, 130)
        self.assertIsNone(_text_angle(out, 0.5, top))                          # not yet
        self.assertIsNone(_text_angle(out, 2.9, top))                          # gone after its end
        self.assertAlmostEqual(_text_angle(out, 2.0, top), 45, delta=10)       # one second in: 45 degrees

    def test_lagkage_wobble_swings_both_ways_through_upright(self):
        layout = self.d / "lagkage_wobble.json"
        layout.write_text(json.dumps({"sequence_direction": "forward", "layers": [
            {"layer_number": 1, "type": "text", "text": "WOBBLE", "size": 50, "height_pct": 20, "mode": "free",
             "pos_x_pct": 25, "pos_y_pct": 65, "text_size": 14, "color": "#FFFFFF", "outline_color": "#000000",
             "wobble": 30, "wobble_period": 2, "opacity": 1}]}))
        out = self.d / "lagkage_wobble.mp4"
        _cli("-P", "lagkage", "-i", str(self.blue_still), "-o", str(out), "-F", "--layout-json", str(layout))
        bottom = slice(220, 330)
        self.assertLess(abs(_text_angle(out, 1.0, bottom)), 5)                 # back to upright at half a period
        self.assertGreater(_text_angle(out, 0.5, bottom), 15)                  # out to one side
        self.assertLess(_text_angle(out, 1.5, bottom), -15)                    # out to the other side

    def test_color_over_the_input_keeps_sound_and_lays_the_picture_on_top(self):
        out = self.d / "over.mp4"
        _cli("-P", "color_pattern", "-i", str(self.clip), "-o", str(out), "-F", "--mode", "Over the input",
             "--pattern", "Solid colour", "--color", "#FF0000", "--opacity", "1")
        info = probe_video(str(out))
        self.assertAlmostEqual(info.duration, 4.0, delta=0.1)                 # the input's length
        self.assertEqual((info.width, info.height), (640, 480))              # the input's size
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(out), "-frames:v", "1", "-vf",
                              "scale=in_color_matrix=bt709:in_range=tv:out_range=full:flags=accurate_rnd+full_chroma_int,"
                              "crop=1:1:320:240", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True, env=_env(), check=True).stdout
        red, green, blue = np.frombuffer(raw, np.uint8)[:3].astype(int)
        self.assertGreater(red, 240)
        self.assertLess(green + blue, 30)
        audio = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_type",
                                "-of", "csv=p=0", str(out)], capture_output=True, text=True, env=_env()).stdout
        self.assertIn("audio", audio)

    def test_no_program_echoes_the_ffmpeg_command(self):
        pattern = re.compile(r'^\s*print\((\"↪|\" ?\.join\(f\'"\{arg\}"\')', re.MULTILINE)
        for path in (ROOT / "videobeaux" / "programs").glob("*.py"):
            self.assertIsNone(pattern.search(path.read_text(encoding="utf-8")), path.name)


if __name__ == "__main__":
    unittest.main()
