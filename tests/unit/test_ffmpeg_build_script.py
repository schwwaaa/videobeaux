"""tools/ffmpeg-build/build-macos.sh must cope with the *relative* --work that `npm run ffmpeg:local` passes."""
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "ffmpeg-build" / "build-macos.sh"


class BuildScriptPaths(unittest.TestCase):
    def _paths(self, cwd, work):
        r = subprocess.run(["bash", str(SCRIPT), "--work", work, "--print-paths"], cwd=cwd, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return dict(line.split("=", 1) for line in r.stdout.splitlines() if "=" in line and line.split("=")[0] in ("WORK", "PREFIX", "DIST"))

    def test_relative_work_dir_becomes_absolute(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._paths(d, ".ffmpeg-build")                 # exactly what the npm script passes
            for k, v in p.items():
                self.assertTrue(v.startswith("/"), f"{k} is not absolute: {v}")
            self.assertTrue(p["PREFIX"].endswith("/.ffmpeg-build/prefix"))
            self.assertEqual(Path(p["DIST"]).parent, Path(p["WORK"]))
            self.assertTrue((Path(d) / ".ffmpeg-build").is_dir())

    def test_nested_and_dotted_relative_paths(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "gui").mkdir()
            p = self._paths(Path(d) / "gui", "../out/work")
            self.assertEqual(Path(p["WORK"]).resolve(), (Path(d) / "out" / "work").resolve())
            self.assertTrue(p["PREFIX"].startswith("/"))

    def test_path_is_resolved_before_any_folder_is_derived(self):
        text = SCRIPT.read_text()
        resolve = text.index('WORK="$(cd "$WORK" && pwd)"')
        self.assertLess(resolve, text.index('PREFIX="$WORK/prefix"'))
        self.assertLess(resolve, text.index('export PATH="$PREFIX/bin'))

    def test_no_nonfree_flag_in_the_configure_line(self):
        self.assertNotIn("--enable-nonfree\\", SCRIPT.read_text().replace(" ", ""))
        self.assertNotRegex(SCRIPT.read_text().split("./configure")[-1].split("&& make")[0], r"--enable-nonfree")


if __name__ == "__main__":
    unittest.main()
