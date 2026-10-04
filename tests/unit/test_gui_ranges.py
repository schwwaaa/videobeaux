import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class NumberArgRanges(unittest.TestCase):
    def test_every_visible_number_arg_has_a_range_or_is_marked_free(self):
        out = subprocess.run([sys.executable, str(ROOT / "gui" / "discover_programs.py")], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout
        data = json.loads(out)
        bad = [f"{p}.{a['name']}" for p, v in data.items() for a in v["args"]
               if a["type"] == "number" and not a.get("hidden") and not a.get("free")
               and (a.get("min") is None or a.get("max") is None)]
        self.assertEqual(bad, [], "add GUI_METADATA min/max (or an entry in gui/arg_ranges.py) for these")
        self.assertEqual([k for k, v in data.items() if v.get("error")], [])

    def test_ranges_table_is_sane(self):
        sys.path.insert(0, str(ROOT / "gui"))
        from arg_ranges import RANGES
        for prog, args in RANGES.items():
            for name, rng in args.items():
                if rng is not None:
                    self.assertLess(rng[0], rng[1], f"{prog}.{name}")


if __name__ == "__main__":
    unittest.main()
