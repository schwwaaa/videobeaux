"""Auto Narrate's script timing: script words take the timing of the heard words they match, and the rest are placed between."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from videobeaux.utils.script_align import align_script, pair_words, to_transcript  # noqa: E402


def heard(*words):
    """Vosk-style words, one every half second: heard('hello', 'there') → hello 0–0.5, there 0.5–1."""
    return [{"word": w, "start": i * 0.5, "end": i * 0.5 + 0.5} for i, w in enumerate(words)]


class AlignScript(unittest.TestCase):
    def test_words_heard_exactly_keep_the_script_spelling_and_timing(self):
        words, matched = align_script("hello there friend", heard("hello", "there", "friend"))
        self.assertEqual(matched, 3)
        self.assertEqual([w["text"] for w in words], ["hello", "there", "friend"])
        self.assertEqual([(w["start"], w["end"]) for w in words], [(0.0, 0.5), (0.5, 1.0), (1.0, 1.5)])

    def test_a_misheard_name_takes_the_timing_of_the_word_it_sounds_like(self):
        # Vosk hears "kubernetes" as "cooper netties"; the script's spelling and the neighbours' timing still hold
        words, matched = align_script("deploy kubernetes now", heard("deploy", "cooper", "netties", "now"))
        self.assertEqual(matched, 3)  # deploy, now, and kubernetes ↔ netties; "cooper" is left over
        self.assertEqual([w["text"] for w in words], ["deploy", "kubernetes", "now"])
        self.assertEqual(words[0]["start"], 0.0)
        self.assertEqual(words[2]["start"], 1.5)
        self.assertLessEqual(words[1]["end"], words[2]["start"] + 1e-9)

    def test_a_word_heard_as_something_else_is_placed_between_its_neighbours(self):
        words, matched = align_script("one two three four five", heard("one", "two", "four", "five"))
        self.assertEqual(matched, 4)
        three = words[2]
        self.assertGreaterEqual(three["start"], words[1]["end"] - 1e-9)
        self.assertLessEqual(three["end"], words[3]["start"] + 1e-9)

    def test_extra_heard_words_are_dropped_from_the_result(self):
        words, _ = align_script("go now", heard("uh", "go", "um", "now", "okay"))
        self.assertEqual([w["text"] for w in words], ["go", "now"])
        self.assertEqual(words[1]["start"], 1.5)

    def test_unheard_script_is_spread_over_the_narration_by_length(self):
        words, matched = align_script("aa bbbb", [], duration=6.0)
        self.assertEqual(matched, 0)
        self.assertEqual(words[0]["start"], 0.0)
        self.assertAlmostEqual(words[1]["end"], 6.0, places=2)
        self.assertGreater(words[1]["end"] - words[1]["start"], words[0]["end"] - words[0]["start"])

    def test_timing_never_runs_backwards_and_stays_in_order(self):
        script = "the quick brown fox jumps over the lazy dog"
        words, _ = align_script(script, heard("the", "quik", "brown", "fox", "jumped", "over", "lazy", "dog"), duration=8.0)
        starts = [w["start"] for w in words]
        self.assertEqual(starts, sorted(starts))
        for w in words:
            self.assertLessEqual(w["start"], w["end"])

    def test_punctuation_stays_on_the_word_and_matches_without_it(self):
        words, matched = align_script("Hello, world!", heard("hello", "world"))
        self.assertEqual(matched, 2)
        self.assertEqual([w["text"] for w in words], ["Hello,", "world!"])

    def test_empty_script_gives_no_words(self):
        self.assertEqual(align_script("   ", heard("hi")), ([], 0))


class PairWords(unittest.TestCase):
    def test_pairs_come_back_in_order_and_do_not_cross(self):
        pairs = pair_words(["a", "b", "c"], ["c", "a", "b"])
        self.assertEqual(sorted(pairs), sorted(pairs, key=lambda p: p[0]))
        self.assertLessEqual(len(pairs), 3)
        for (i1, j1, _), (i2, j2, _) in zip(pairs, pairs[1:]):
            self.assertLess(i1, i2)
            self.assertLess(j1, j2)


class Transcript(unittest.TestCase):
    def test_segments_have_the_shape_the_caption_renderer_reads(self):
        words = [{"text": f"w{k}", "start": k * 0.2, "end": k * 0.2 + 0.2} for k in range(30)]
        segments = to_transcript(words)
        self.assertEqual(len(segments), 3)
        first = segments[0]
        self.assertEqual(first["words"][0], {"word": "w0", "start": 0.0, "end": 0.2})
        self.assertEqual(first["start"], 0.0)
        self.assertEqual(first["content"].split()[:2], ["w0", "w1"])


if __name__ == "__main__":
    unittest.main()
