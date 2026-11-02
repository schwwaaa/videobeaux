"""Pause markers and the start delay in Auto Narrate: the script split, and the narration joined with its silence."""
import subprocess
import tempfile
import unittest
from pathlib import Path

from videobeaux.programs.auto_narrate import PAUSE_RE, _join_narration, split_script
from videobeaux.utils.ffmpeg_operations import get_video_duration


def _tone(path, seconds):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-t", str(seconds), "-i", "sine=f=440:r=24000",
                    "-c:a", "pcm_s16le", str(path)], check=True)


class SplitScript(unittest.TestCase):
    def test_pauses_split_the_script_in_order(self):
        items = split_script("hello, welcome. <<p:2>> this explains. <<p:10>> thanks a lot. ")
        self.assertEqual(items, [
            ("text", "hello, welcome."), ("pause", 2.0), ("text", "this explains."),
            ("pause", 10.0), ("text", "thanks a lot."),
        ])

    def test_start_delay_comes_first_and_zero_pauses_are_dropped(self):
        items = split_script("one <<p:0>> two", start_delay=1.5)
        self.assertEqual(items, [("pause", 1.5), ("text", "one"), ("text", "two")])

    def test_decimals_with_and_without_a_leading_zero(self):
        self.assertEqual(split_script("a <<p:.5>> b")[1], ("pause", 0.5))
        self.assertEqual(split_script("a <<p:0.5>> b")[1], ("pause", 0.5))
        self.assertEqual(split_script("a <<p:1.25>> b")[1], ("pause", 1.25))

    def test_spaced_marker(self):
        self.assertEqual(split_script("a <<  p : 0.5 >> b")[1], ("pause", 0.5))

    def test_only_pauses_leaves_nothing_to_say(self):
        items = split_script("<<p:2>>")
        self.assertFalse(any(kind == "text" for kind, _ in items))

    def test_unknown_marker_is_refused(self):
        with self.assertRaises(SystemExit):
            split_script("hello <<pauze:2>> there")

    def test_old_pause_spelling_is_refused(self):
        with self.assertRaises(SystemExit):
            split_script("hello <<pause:2>> there")

    def test_marker_regex_needs_seconds(self):
        self.assertIsNone(PAUSE_RE.fullmatch("<<p>>"))
        self.assertIsNone(PAUSE_RE.fullmatch("<<p:>>"))


class JoinNarration(unittest.TestCase):
    def test_joined_length_is_speech_plus_every_pause(self):
        items = [("pause", 1.5), ("text", "one"), ("pause", 2.0), ("text", "two"), ("pause", 3.0), ("text", "three")]
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)

            def speak(text_file, wav):
                _tone(wav, 1.0)   # every spoken part is exactly one second

            out = _join_narration(items, tmp, speak)
            self.assertAlmostEqual(get_video_duration(str(out)), 1.5 + 1 + 2 + 1 + 3 + 1, delta=0.1)

    def test_single_text_part_is_returned_as_is(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)

            def speak(text_file, wav):
                _tone(wav, 2.0)

            out = _join_narration([("text", "just this")], tmp, speak)
            self.assertEqual(out.name, "part_000.wav")


if __name__ == "__main__":
    unittest.main()
