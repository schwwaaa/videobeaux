import os
import tempfile
import unittest
from pathlib import Path

from videobeaux.utils import fonts

ASSETS = Path(fonts.__file__).resolve().parents[1] / "assets" / "fonts"


class FontCatalog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["VIDEOBEAUX_CACHE_DIR"] = tempfile.mkdtemp()
        fonts._catalog_cache = None
        cls.cat = fonts.font_catalog(refresh=True)

    def test_bundled_fonts_come_first_and_files_exist(self):
        bundled = [e for e in self.cat if e["bundled"]]
        self.assertGreaterEqual(len(bundled), 25)
        self.assertTrue(all(e["bundled"] for e in self.cat[:len(bundled)]))
        for e in bundled:
            self.assertTrue(Path(e["regular"]).exists(), e["family"])
            self.assertTrue(str(Path(e["regular"]).parent) == str(ASSETS), e["family"])
        names = {e["family"] for e in bundled}
        for want in ("Anton", "Bebas Neue", "Bangers", "DejaVu Sans", "Atkinson Hyperlegible", "Lato"):
            self.assertIn(want, names)

    def test_no_hidden_system_fonts_or_duplicates(self):
        self.assertFalse([e["family"] for e in self.cat if e["family"].startswith(".")])
        fams = [e["family"].lower() for e in self.cat]
        self.assertEqual(len(fams), len(set(fams)))

    def test_every_bundled_font_has_a_licence_text(self):
        lic = {p.name.split("-")[0] for p in (ASSETS / "licenses").glob("*.txt")}
        ttfs = {p.name.split("-")[0].lower() for p in ASSETS.glob("*.ttf") if not p.name.startswith("DejaVu")}
        self.assertTrue(ttfs <= {x.lower() for x in lic}, ttfs - {x.lower() for x in lic})

    def test_resolve_by_name_path_and_fallback(self):
        anton = fonts.resolve_font("Anton")
        self.assertTrue(anton and anton.endswith("Anton-Regular.ttf"))
        self.assertEqual(fonts.resolve_font("anton"), anton)                                   # case-insensitive
        self.assertTrue(fonts.resolve_font("Atkinson Hyperlegible", bold=True).endswith("AtkinsonHyperlegible-Bold.ttf"))
        self.assertTrue(fonts.resolve_font("Atkinson Hyperlegible", bold=False).endswith("AtkinsonHyperlegible-Regular.ttf"))
        self.assertEqual(fonts.resolve_font(anton), anton)                                     # a path passes straight through
        self.assertTrue(fonts.resolve_font("No Such Font Anywhere"))                           # falls back to DejaVu, never None
        self.assertTrue(fonts.resolve_font(None))


if __name__ == "__main__":
    unittest.main()
