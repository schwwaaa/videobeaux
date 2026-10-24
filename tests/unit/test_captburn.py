import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from videobeaux.programs import captburn


def args(video, **kw):
    return SimpleNamespace(input=str(video), output=str(video.with_name("out.mp4")), force=True, stt_model=None, trans_json=None, **kw)


class TranscriptResolution(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.video = self.tmp / "clip.mp4"
        self.video.write_bytes(b"x")

    def test_existing_sidecar_is_used_without_a_model(self):
        sidecar = self.tmp / "clip.json"
        sidecar.write_text(json.dumps([{"content": "hi", "start": 0, "end": 1}]))
        self.assertEqual(captburn._transcript_for(args(self.video)), sidecar)

    def test_explicit_transcript_wins_over_the_sidecar(self):
        (self.tmp / "clip.json").write_text("[]")
        mine = self.tmp / "mine.json"
        mine.write_text("[]")
        a = args(self.video)
        a.trans_json = str(mine)
        self.assertEqual(captburn._transcript_for(a), mine)

    def test_no_transcript_and_no_model_says_what_to_do(self):
        with self.assertRaises(SystemExit) as cm:
            captburn._transcript_for(args(self.video))
        self.assertIn("Vosk Model", str(cm.exception))

    def test_missing_transcript_is_made_with_vosk_and_saved_next_to_the_clip(self):
        model = self.tmp / "model"
        model.mkdir()

        def fake(input_video, model_path, json_path, emit_txt, overwrite):
            json_path.write_text(json.dumps([{"content": "hello", "start": 0, "end": 1, "words": []}]))

        a = args(self.video)
        a.stt_model = str(model)
        with mock.patch("videobeaux.programs.transcraibe.transcribe_single", side_effect=fake) as m:
            got = captburn._transcript_for(a)
        self.assertEqual(got, self.tmp / "clip.json")
        self.assertEqual(m.call_args.kwargs["model_path"], model)
        self.assertFalse(m.call_args.kwargs["overwrite"])

    def test_silent_clip_reports_nothing_to_caption(self):
        model = self.tmp / "model"
        model.mkdir()
        a = args(self.video)
        a.stt_model = str(model)
        with mock.patch("videobeaux.programs.transcraibe.transcribe_single", side_effect=lambda **k: None):
            with self.assertRaises(SystemExit) as cm:
                captburn._transcript_for(a)
        self.assertIn("nothing to caption", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
