#!/bin/zsh
# Retake the website's app screenshots (<website clone>/site/shots/canvas, step1, step2, step3) from the real UI.
# The clone is ../videobeaux-website, or set VB_SITE_DIR.
#   tools/site-harness/shots.sh            # needs: the project's venv, gui/node_modules (npm install in gui/), ffmpeg, and
#                                           Brave/Chrome/Chromium (set BROWSER_BIN to use a specific one)
# What it does: starts the renderer with a stubbed Electron bridge (vite, port 5199), loads the demo canvases in ws/*.json,
# takes headless screenshots at 2×, crops/encodes them to WebP into site/shots/.
set -e
HERE=${0:A:h}; ROOT=${HERE:h:h}; SITE=${VB_SITE_DIR:-$ROOT/../videobeaux-website}; OUT=$SITE/site/shots; TMP=$(mktemp -d)
[ -f "$SITE/index.html" ] || { echo "No website clone at $SITE — set VB_SITE_DIR"; exit 1; }
mkdir -p "$OUT"
BROWSER=${BROWSER_BIN:-}
for b in "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" "/Applications/Chromium.app/Contents/MacOS/Chromium" $(command -v google-chrome chromium chromium-browser 2>/dev/null); do
  [ -z "$BROWSER" ] && [ -x "$b" ] && BROWSER=$b
done
[ -x "$BROWSER" ] || { echo "No Chromium-based browser found — set BROWSER_BIN"; exit 1; }
FF=${FFMPEG:-$(command -v ffmpeg || echo $ROOT/gui/resources/ffmpeg/ffmpeg)}

( cd $ROOT && venv/bin/python gui/discover_programs.py > $HERE/programs.json && venv/bin/python -m videobeaux.utils.fonts --json > $HERE/fonts.json )
( cd $HERE && node $ROOT/gui/node_modules/vite/bin/vite.js --config $HERE/vite.config.mjs > $TMP/vite.log 2>&1 ) &
VITE=$!; trap "kill $VITE 2>/dev/null; rm -rf $TMP" EXIT
for i in {1..40}; do curl -s -o /dev/null http://localhost:5199/ && break; sleep .5; done

# shot <name> <query> <width> <height>   (budget in ms of virtual time via BUDGET)
shot() { "$BROWSER" --headless=new --disable-gpu --hide-scrollbars --window-size=$3,$4 --force-device-scale-factor=2 \
           --virtual-time-budget=${BUDGET:-15000} --screenshot=$TMP/$1.png "http://localhost:5199/?$2" >/dev/null 2>&1; }
# enc <name> <crop or ""> <width> <outfile>
enc() { $FF -y -v error -i $TMP/$1.png -vf "${2:+crop=$2,}scale=$3:-1:flags=lanczos" -c:v libwebp -quality 84 -compression_level 6 $OUT/$4.webp; echo "✓ $4"; }

shot canvas "demo=canvas&run=1&keys=j,b&keyat=6000" 1260 700;                     enc canvas "" 2200 canvas
shot step1  "demo=canvas&keys=j&keyat=1500" 1260 700;                             enc step1 "1100:611:0:150" 1400 step1
shot step2  "demo=wired&look=signatures&keys=b,j&keyat=1500" 1260 700;            enc step2 "" 1400 step2
BUDGET=3300 shot step3 "demo=canvas&run=1" 1260 700;                              enc step3 "2520:1400:480:0" 1400 step3
