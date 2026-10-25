import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from videobeaux.utils.caption_render import burn_captions


def ns(video, out, transcript, **kw):
    base = dict(input=str(video), output=str(out), force=True, trans_json=str(transcript), font="Anton", font_size=60,
                min_font_size=30, words_per_caption=3, no_uppercase=False, caption_max_width=0.86, caption_max_lines=2,
                active_scale=1.2, vertical_anchor=0.6, primary="#FFFFFF", highlight="#FFE128", outline="#000000",
                stroke_width=6, vcodec="libx264", crf=23, preset="ultrafast")
    base.update(kw)
    return SimpleNamespace(**base)


class BurnCaptions(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.video = self.tmp / "in.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=0x203040:s=320x180:r=12:d=2",
                        "-f", "lavfi", "-i", "sine=d=2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
                        str(self.video)], check=True)
        words = [{"word": w, "start": 0.2 + i * 0.4, "end": 0.55 + i * 0.4} for i, w in enumerate("hello there small world".split())]
        self.tr = self.tmp / "in.json"
        self.tr.write_text(json.dumps([{"content": "hello there small world", "start": 0.2, "end": 1.8, "words": words}]))

    def probe(self, p):
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height", "-of", "json", str(p)],
                           capture_output=True, text=True)
        return json.loads(r.stdout)["streams"]

    def test_burns_without_png_files_and_keeps_size_and_audio(self):
        out = self.tmp / "out.mp4"
        burn_captions(ns(self.video, out, self.tr))
        st = self.probe(out)
        v = [s for s in st if s["codec_type"] == "video"][0]
        self.assertEqual((v["width"], v["height"]), (320, 180))
        self.assertTrue(any(s["codec_type"] == "audio" for s in st))
        self.assertEqual(list(self.tmp.glob("**/*.png")), [])                       # no temporary PNG sequence any more

    def test_captions_actually_change_the_picture(self):
        out = self.tmp / "out.mp4"
        burn_captions(ns(self.video, out, self.tr))
        a, b = self.tmp / "a.png", self.tmp / "b.png"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "0.7", "-i", str(self.video), "-frames:v", "1", str(a)], check=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "0.7", "-i", str(out), "-frames:v", "1", str(b)], check=True)
        self.assertNotEqual(a.read_bytes(), b.read_bytes())

    def test_a_transcript_without_words_is_an_error(self):
        empty = self.tmp / "empty.json"
        empty.write_text("[]")
        with self.assertRaises(ValueError):
            burn_captions(ns(self.video, self.tmp / "x.mp4", empty))


if __name__ == "__main__":
    unittest.main()
