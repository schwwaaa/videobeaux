"""Face Swap: landmark alignment, the three modes, and an honest summary when nothing could be swapped."""
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

try:
    import cv2
    from videobeaux.utils import booth_filters as bf
except SystemExit:           # OpenCV missing
    cv2 = None


def _lm(cx, cy, d=40.0, rot=0.0):
    """Five landmarks of a face centred at (cx, cy) with eye distance d."""
    pts = np.float32([[-0.5, -0.2], [0.5, -0.2], [0.0, 0.25], [-0.32, 0.6], [0.32, 0.6]]) * d
    c, s = np.cos(rot), np.sin(rot)
    pts = pts @ np.float32([[c, s], [-s, c]])
    return pts + np.float32([cx, cy])


def _box(pts):
    x0, y0 = pts.min(0)
    x1, y1 = pts.max(0)
    return (float(x0 - 8), float(y0 - 20), float(x1 - x0 + 16), float(y1 - y0 + 30))


@unittest.skipIf(cv2 is None, "OpenCV not installed")
class FaceSwap(unittest.TestCase):
    def _frame(self):
        img = np.full((240, 400, 3), 90, np.uint8)
        img[60:140, 40:140] = (30, 60, 200)        # "face A": reddish
        img[60:140, 260:360] = (200, 90, 20)       # "face B": bluish
        return img

    def _ctx(self, faces):
        return bf.Ctx(faces=[_box(p) for p in faces], landmarks=faces)

    def test_alignment_moves_the_source_face_onto_the_target(self):
        img = self._frame()
        a, b = _lm(90, 100), _lm(310, 100)
        out = img.copy()
        bf._swap_into(out, img, a, b, softness=0.02, match=0.0)
        self.assertLess(np.abs(out[100, 310].astype(int) - img[100, 90].astype(int)).max(), 30)   # B's centre now A's colour
        self.assertTrue((out[10:40, 10:60] == img[10:40, 10:60]).all())                          # far away: untouched

    def test_swap_two_exchanges_both_faces(self):
        img = self._frame()
        a, b = _lm(90, 100), _lm(310, 100)
        fn = bf.make_face_swap(0.02, bf.FACE_SWAP_MODES[0], None, 0.0)
        out = fn(img, self._ctx([a, b]))
        self.assertLess(np.abs(out[100, 90].astype(int) - img[100, 310].astype(int)).max(), 30)
        self.assertLess(np.abs(out[100, 310].astype(int) - img[100, 90].astype(int)).max(), 30)
        self.assertIn("2 or more in 1 of 1", fn.summary())

    def test_one_face_is_left_alone_and_the_summary_says_why(self):
        img = self._frame()
        fn = bf.make_face_swap(0.06, bf.FACE_SWAP_MODES[0], None, 0.85)
        out = fn(img, self._ctx([_lm(90, 100)]))
        self.assertTrue((out == img).all())
        s = fn.summary()
        self.assertIn("Nothing was swapped", s)
        self.assertIn("Photo onto every face", s)

    def test_biggest_face_onto_the_others(self):
        img = self._frame()
        big, small = _lm(90, 100, d=50), _lm(310, 100, d=30)
        fn = bf.make_face_swap(0.02, bf.FACE_SWAP_MODES[1], None, 0.0)
        out = fn(img, self._ctx([small, big]))
        self.assertLess(np.abs(out[100, 310].astype(int) - img[100, 90].astype(int)).max(), 30)   # small now shows big's face
        self.assertTrue((out[100, 90] == img[100, 90]).all())                                      # big untouched

    def test_photo_mode_works_with_one_face_and_needs_a_photo(self):
        img = self._frame()
        with self.assertRaises(SystemExit):
            bf.make_face_swap(0.06, bf.FACE_SWAP_MODES[2], None, 0.85)
        with tempfile.TemporaryDirectory() as d:
            photo = Path(d) / "face.png"
            cv2.imwrite(str(photo), np.full((120, 100, 3), (10, 200, 10), np.uint8))   # plain green "face"
            fn = bf.make_face_swap(0.02, bf.FACE_SWAP_MODES[2], str(photo), 0.0)
            out = fn(img, self._ctx([_lm(90, 100)]))
        self.assertGreater(out[100, 90, 1], 150)                                         # green pasted on the face
        self.assertTrue((out[10:40, 200:300] == img[10:40, 200:300]).all())

    def test_tracker_keeps_landmarks(self):
        from videobeaux.utils.face_tracking import Track
        t = Track(1, 0, 0, 10, 10, lm=np.zeros((5, 2), np.float32))
        self.assertEqual(t.lm.shape, (5, 2))


if __name__ == "__main__":
    unittest.main()
