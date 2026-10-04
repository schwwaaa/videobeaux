import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "needs ffmpeg")
class FramePipeColour(unittest.TestCase):
    def test_roundtrip_keeps_colours_and_tags_bt709(self):
        import numpy as np
        from videobeaux.utils.frame_pipe import process_video

        with tempfile.TemporaryDirectory() as d:
            src, out = Path(d, "src.mp4"), Path(d, "out.mp4")
            subprocess.run(
                ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                 "color=c=0x28B43C:s=320x240:d=1,format=rgb24,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
                 "-c:v", "libx264", "-colorspace", "bt709", "-color_primaries", "bt709",
                 "-color_trc", "bt709", "-color_range", "tv", str(src)], check=True)
            process_video(src, out, lambda f, i, t: f, force=True)
            raw = subprocess.run(
                ["ffmpeg", "-v", "error", "-i", str(out), "-vf",
                 "scale=in_color_matrix=bt709:in_range=tv,format=rgb24", "-frames:v", "1", "-f", "rawvideo", "-"],
                capture_output=True, check=True).stdout
            px = np.frombuffer(raw, np.uint8).reshape(240, 320, 3)[100, 100].astype(int)
            self.assertLessEqual(int(np.abs(px - [40, 180, 60]).max()), 8, px)
            tags = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "stream=color_space,color_transfer,color_primaries",
                 "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout.strip()
            self.assertEqual(tags, "bt709,bt709,bt709")


if __name__ == "__main__":
    unittest.main()
