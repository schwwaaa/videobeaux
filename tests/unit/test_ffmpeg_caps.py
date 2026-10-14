"""ffmpeg capability helpers: parsing, friendly errors, and the shared requirements file."""
import json
import shutil
import sys
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from videobeaux.utils import ffmpeg_caps as caps  # noqa: E402

LISTING_NEW = """Filters:
  T.. = Timeline support
  .S. = Slice threading
 ------
 TS aap               AA->A      Apply Affine Projection algorithm to first audio stream.
 .. drawtext          V->V       Draw text.
"""
LISTING_OLD = " T.C drawtext          V->V       Draw text.\n .S. zscale V->V Scale.\n"
ENCODERS = """Encoders:
 V..... = Video
 ------
 V....D libx264              libx264 H.264
 A....D aac                  AAC
"""


def _fake(**over):
    base = {"binary": "ffmpeg", "found": True, "version": "9.9", "license": "gpl",
            "encoders": {"libx264", "aac"}, "decoders": set(), "filters": set()}
    base.update(over)
    return base


class Caps(unittest.TestCase):
    def test_names_handles_ffmpeg7_and_9_filter_tables_and_skips_legend(self):
        self.assertEqual(caps._names(LISTING_NEW), {"aap", "drawtext"})
        self.assertEqual(caps._names(LISTING_OLD), {"drawtext", "zscale"})
        self.assertEqual(caps._names(ENCODERS), {"libx264", "aac"})

    def test_requirements_file_is_valid(self):
        feats = caps.requirements()
        ids = [f["id"] for f in feats]
        self.assertEqual(len(ids), len(set(ids)))
        for f in feats:
            self.assertIn(f["kind"], ("encoder", "decoder", "filter"))
            self.assertTrue(isinstance(f["any"], list) and f["any"])
            self.assertIsInstance(f["required"], bool)
        required = {f["id"] for f in feats if f["required"]}
        self.assertTrue({"text", "subtitles", "hdr"} <= required)   # what the GUI used to hard-code
        self.assertTrue(json.loads(Path(caps._REQ_FILE).read_text())["features"])

    def test_encoders_in_command_ignores_decoder_options_and_copy(self):
        cmd = ["ffmpeg", "-c:v", "libdav1d", "-i", "in.mkv", "-c:v", "libsvtav1", "-c:a", "copy", "-c:s", "mov_text", "out.mp4"]
        self.assertEqual(caps.encoders_in_command(cmd), ["libsvtav1", "mov_text"])
        self.assertEqual(caps.encoders_in_command(["ffmpeg", "-i", "a", "-an", "-c", "copy", "o.mp4"]), [])

    def test_check_command_gives_a_sentence_for_a_missing_encoder(self):
        with mock.patch.object(caps, "inspect", lambda binary="ffmpeg": _fake()):
            msg = caps.check_command(["ffmpeg", "-i", "a.mp4", "-c:v", "libsvtav1", "out.mp4"])
            self.assertTrue(msg and "AV1" in msg and "libsvtav1" in msg and "Repair" in msg, msg)
            self.assertIsNone(caps.check_command(["ffmpeg", "-i", "a.mp4", "-c:v", "libx264", "out.mp4"]))
            self.assertIsNone(caps.check_command(["not-ffmpeg", "-c:v", "nothing"]))

    def test_unknown_binary_never_blocks(self):
        with mock.patch.object(caps, "inspect", lambda binary="ffmpeg": _fake(found=False, encoders=set(), version=None)):
            self.assertIsNone(caps.check_command(["ffmpeg", "-i", "a", "-c:v", "libsvtav1", "o.mp4"]))

    @unittest.skipUnless(shutil.which("ffmpeg"), "no ffmpeg on PATH")
    def test_report_on_real_ffmpeg_is_consistent(self):
        caps.inspect.cache_clear()
        rep = caps.report("ffmpeg")
        self.assertTrue(rep["found"])
        self.assertIn(rep["license"], ("gpl", "lgpl", "nonfree"))
        self.assertFalse(set(rep["missing_required"]) & set(rep["missing_optional"]))


if __name__ == "__main__":
    unittest.main()
