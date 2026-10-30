import io
import re
import unittest
from contextlib import redirect_stderr

from videobeaux.programs import transcraibe

# the desktop app's own pattern for a progress line (gui/src/main/index.js STAT_LINE_RE) and the one the renderer reads for the position
APP_STAT_LINE = re.compile(r"\btime=\s*\d+:\d+:\d+")
APP_POSITION = re.compile(r"time=\s*(\d+):(\d+):(\d+\.\d+)")
APP_SPEED = re.compile(r"speed=\s*([\d.]+)x")


class TranscribeProgress(unittest.TestCase):
    def test_progress_line_is_read_by_the_app_as_a_progress_bar_update(self):
        buf = io.StringIO()
        with redirect_stderr(buf):
            transcraibe._report_progress(75.5, 30.0)
        line = buf.getvalue().strip()
        self.assertRegex(line, APP_STAT_LINE)
        h, m, s = APP_POSITION.search(line).groups()
        self.assertEqual(int(h) * 3600 + int(m) * 60 + float(s), 75.5)
        self.assertEqual(float(APP_SPEED.search(line).group(1)), 2.5)

    def test_speed_is_zero_before_any_time_has_passed(self):
        buf = io.StringIO()
        with redirect_stderr(buf):
            transcraibe._report_progress(3.0, 0.0)
        self.assertIn("speed=0.0x", buf.getvalue())

    def test_unreadable_duration_is_zero_not_an_error(self):
        self.assertEqual(transcraibe._media_duration(__file__ + ".does-not-exist"), 0.0)


if __name__ == "__main__":
    unittest.main()
