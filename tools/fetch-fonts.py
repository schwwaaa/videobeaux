#!/usr/bin/env python3
"""
Download the open-licensed caption fonts bundled with Videobeaux into videobeaux/assets/fonts/ (+ their licence texts and a
SOURCES.txt with the exact URL and SHA-256 of every file), pinned to one commit of github.com/google/fonts.

    python tools/fetch-fonts.py          # fetch anything missing
    python tools/fetch-fonts.py --force  # re-download everything

All fonts are SIL OFL 1.1 or Apache 2.0 (both allow bundling and redistribution, including in a commercial app, as long as the
licence text travels with the fonts — the files in assets/fonts/licenses/ do). Add a font = add a line to FONTS and re-run.
"""
import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

COMMIT = "e7db6ca603fd4862010383ff17ffd6cc4ffac1c0"
BASE = f"https://raw.githubusercontent.com/google/fonts/{COMMIT}"
DEST = Path(__file__).resolve().parents[1] / "videobeaux" / "assets" / "fonts"

# (licence folder, family folder, [file stems])
FONTS = [
    ("ofl", "anton", ["Anton-Regular"]),
    ("ofl", "bebasneue", ["BebasNeue-Regular"]),
    ("ofl", "bangers", ["Bangers-Regular"]),
    ("ofl", "lilitaone", ["LilitaOne-Regular"]),
    ("ofl", "righteous", ["Righteous-Regular"]),
    ("ofl", "bungee", ["Bungee-Regular"]),
    ("ofl", "archivoblack", ["ArchivoBlack-Regular"]),
    ("ofl", "titanone", ["TitanOne-Regular"]),
    ("ofl", "paytoneone", ["PaytoneOne-Regular"]),
    ("ofl", "bowlbyone", ["BowlbyOne-Regular"]),
    ("ofl", "passionone", ["PassionOne-Black"]),
    ("ofl", "staatliches", ["Staatliches-Regular"]),
    ("ofl", "fugazone", ["FugazOne-Regular"]),
    ("ofl", "blackopsone", ["BlackOpsOne-Regular"]),
    ("ofl", "abrilfatface", ["AbrilFatface-Regular"]),
    ("ofl", "shrikhand", ["Shrikhand-Regular"]),
    ("ofl", "pacifico", ["Pacifico-Regular"]),
    ("ofl", "lobster", ["Lobster-Regular"]),
    ("ofl", "caveatbrush", ["CaveatBrush-Regular"]),
    ("ofl", "patrickhand", ["PatrickHand-Regular"]),
    ("ofl", "monoton", ["Monoton-Regular"]),
    ("ofl", "rubikmonoone", ["RubikMonoOne-Regular"]),
    ("ofl", "pressstart2p", ["PressStart2P-Regular"]),
    ("ofl", "vt323", ["VT323-Regular"]),
    ("ofl", "ibmplexmono", ["IBMPlexMono-Regular", "IBMPlexMono-Bold"]),
    ("ofl", "atkinsonhyperlegible", ["AtkinsonHyperlegible-Regular", "AtkinsonHyperlegible-Bold"]),
    ("ofl", "lato", ["Lato-Regular", "Lato-Bold", "Lato-Black"]),
    ("apache", "permanentmarker", ["PermanentMarker-Regular"]),
    ("apache", "luckiestguy", ["LuckiestGuy-Regular"]),
    ("apache", "specialelite", ["SpecialElite-Regular"]),
    ("apache", "chewy", ["Chewy-Regular"]),
]


def get(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    (DEST / "licenses").mkdir(parents=True, exist_ok=True)
    lines, failed = [f"Fonts from https://github.com/google/fonts at commit {COMMIT}", ""], []
    for lic, fam, stems in FONTS:
        lic_name = "OFL" if lic == "ofl" else "LICENSE"
        lic_file = DEST / "licenses" / f"{fam}-{'OFL' if lic == 'ofl' else 'Apache-2.0'}.txt"
        if a.force or not lic_file.exists():
            try:
                lic_file.write_bytes(get(f"{BASE}/{lic}/{fam}/{lic_name}.txt"))
            except Exception as e:                      # some families ship the licence under a different name
                failed.append(f"{fam} licence: {e}")
        for stem in stems:
            f = DEST / f"{stem}.ttf"
            url = f"{BASE}/{lic}/{fam}/{stem}.ttf"
            if a.force or not f.exists():
                try:
                    f.write_bytes(get(url))
                    print("✓", f.name)
                except Exception as e:
                    failed.append(f"{stem}: {e}")
                    continue
            lines.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}  {url}  ({'SIL OFL 1.1' if lic == 'ofl' else 'Apache 2.0'})")
    (DEST / "SOURCES.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if failed:
        print("✗ failed:\n  " + "\n  ".join(failed))
        return 1
    print(f"✅ {len(FONTS)} families → {DEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
