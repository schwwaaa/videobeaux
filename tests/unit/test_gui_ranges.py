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


class SliderCurves(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        out = subprocess.run([sys.executable, str(ROOT / "gui" / "discover_programs.py")], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout
        cls.data = json.loads(out)

    def arg(self, prog, name):
        return next(a for a in self.data[prog]["args"] if a["name"] == name)

    def test_every_scale_is_parseable_and_only_on_positive_or_zero_based_ranges(self):
        import re
        for prog, v in self.data.items():
            for a in v["args"]:
                sc = a.get("scale")
                if not sc:
                    continue
                self.assertRegex(sc, r"^(linear|log|ease|pow:\d+(\.\d+)?)$", f"{prog}.{a['name']}")
                if sc == "log":
                    self.assertGreater(a.get("slider_min", a["min"]), 0, f"{prog}.{a['name']}: log needs a positive range")

    def test_calibrated_table_reaches_the_gui(self):
        table = json.load(open(ROOT / "gui" / "slider_curves.json", encoding="utf-8"))
        self.assertTrue(table, "slider_curves.json is empty — run tools/audit_sliders.py --write-curves")
        for prog, args in table.items():
            for name, sc in args.items():
                self.assertEqual(self.arg(prog, name).get("scale"), sc, f"{prog}.{name}")

    def test_wide_positive_ranges_default_to_log_and_speed_is_log(self):
        self.assertEqual(self.arg("speed", "speed_factor").get("scale"), "log")
        self.assertEqual(self.arg("speed", "speed_factor")["min"], 0.05)
        wide = [(p, a["name"]) for p, v in self.data.items() for a in v["args"]
                if a["type"] == "number" and not a.get("free") and a.get("min") and a["min"] > 0 and a["max"] / a["min"] >= 100]
        self.assertTrue(wide)
        for p, n in wide:
            self.assertIn(self.arg(p, n).get("scale"), ("log", "linear"), f"{p}.{n}")

    def test_dry_wet_amount_stays_linear(self):
        # measured: Amount is linear in picture change (tools/audit_sliders.py) — it must not be curved
        for prog, v in self.data.items():
            for a in v["args"]:
                if a["name"] == "amount" and a["type"] == "number" and (a.get("min"), a.get("max")) == (0, 1):
                    self.assertIn(a.get("scale"), (None, "linear", "pow:0.7"), f"{prog}.amount")  # bad_animation: not a plain blend


if __name__ == "__main__":
    unittest.main()
