
# captburn — Vintage Titler‑Style Caption Burner (V0 baseline + fixes)

**captburn** is a single‑file Python CLI that converts transcript JSON into ASS subtitles and **burns** them into a video using FFmpeg/libass. Think of it like a **vintage title machine** for pop‑on/paint‑on/roll‑up captions — with precise alignment, pixel‑true XY, rotation, margins, and full styling.

> This README documents the current baseline (**V0 + surgical fixes**):
> - Correct **ASS Style field ordering** (adds the missing *Angle* slot) so alignment/margins work reliably.
> - **PlayResX/PlayResY = actual video size** (via `ffprobe`) so `--x/--y` and `--move` use **real pixels**.
> - **Event‑level alignment** (`\anN`) is injected for bullet‑proof placement even on picky renderers.

---

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Transcript JSON Format](#transcript-json-format)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
  - [Alignment (ASS 1–9)](#alignment-ass-1-9)
  - [Pixel‑true XY and Motion](#pixel-true-xy-and-motion)
  - [Styles and Colors](#styles-and-colors)
- [CLI Reference](#cli-reference)
  - [Input / Output](#input--output)
  - [Caption Styles](#caption-styles)
  - [Positioning](#positioning)
  - [Styling / Typography](#styling--typography)
  - [Script Resolution](#script-resolution)
  - [Encoding](#encoding)
- [Feature Table (Flags & Examples)](#feature-table-flags--examples)
- [Examples](#examples)
- [Capton JSON (Save/Reload Captions)](#capton-json-savereload-captions)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [License](#license)

---

## Requirements

- **Python 3.9+**
- **FFmpeg** compiled with **libass** (burning ASS subtitles)
- **ffprobe** (to read video width/height)
- A transcript JSON file (see format below)

Verify:
```bash
ffmpeg -version
ffprobe -version
python --version
```

---

## Installation

This is a single file CLI. Place `captburn.py` anywhere on your system and run it with Python.

Optional: make it executable on macOS/Linux
```bash
chmod +x captburn.py
./captburn.py -h
```

---

## Transcript JSON Format

captburn accepts either:
- A **list** of segment dicts: `[{"start":0.0,"end":2.1,"text":"..."}, ...]`
- Or an object with a top-level `segments` array: `{"segments":[ ... ]}`

**Segment fields**:
- `start` (float seconds)
- `end` (float seconds)
- `text` (string) or `content` (string)
- Optional `words`: list of `{ "text" (or "word"), "start", "end" }` used by **paint‑on**/**roll‑up**

If no `words` are present, captburn **derives** per‑word timings by evenly splitting segment duration.

---

## Quick Start

Pop‑on captions at bottom‑center (classic subs):
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style popon --align 2 --margin-v 100
```

Word‑reveal (paint‑on) at bottom‑center:
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style painton --align 2 --margin-v 110
```

Roll‑up (2 lines), bottom‑center:
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style rollup   --align 2 --margin-v 120 --rollup-lines 2 --words-per-line 7
```

XY exact placement (pixel‑true; requires correct anchor, see below):
```bash
# Place center of text at (640,360) on a 1280x720 video:
python captburn.py -i testfile.mp4 -t testfile.json --style popon --x 640 --y 360 --align 5
```

---

## Core Concepts

### Alignment (ASS 1–9)

ASS alignment numbers (and captburn’s `--align`) map like this:

|   | Left | Center | Right |
|---|------|--------|-------|
| **Top**    | 7 | 8 | 9 |
| **Middle** | 4 | 5 | 6 |
| **Bottom** | 1 | 2 | 3 |

> captburn also injects `\anN` into each dialogue line to enforce alignment at the **event** level.

### Pixel‑true XY and Motion

- capburn writes **PlayResX/PlayResY = video width/height** (via `ffprobe`).
- `--x/--y` (and `--move`) operate in **real video pixels**.
- The **anchor point** for `(x,y)` is defined by **`--align`**:
  - TL=7, TC=8, TR=9; ML=4, MC=5, MR=6; BL=1, BC=2, BR=3.

### Styles and Colors

- Font family, size, bold/italic, outline, shadow, opaque background box, margins.
- ASS colors use **BGR + alpha** internally; captburn accepts `#RRGGBB` and converts for you.
- `--border-style 1` (outline + shadow), `3` (opaque box).

---

## CLI Reference

Run `python captburn.py -h` to view all flags. Key groups are summarized below.

### Input / Output

- `-i, --input <path>` — input video
- `--in-dir <dir>` — process all videos in a directory (recursive)
- `-t, --trans-json <path>` — transcript JSON (if omitted, captburn tries `<video>.json`)
- `--capton <path>` — use existing **capton** JSON to render (skips transcript parsing)
- `--out-dir <dir>` — output directory (default: `out/`)

### Caption Styles

- `--style {popon|painton|rollup}`  
  - **popon**: sentences/segments appear as blocks
  - **painton**: word‑reveal (karaoke `\k` per word)
  - **rollup**: sliding window of N lines
- `--rollup-lines <int>` — window size (default: 2)
- `--words-per-line <int>` — for roll‑up line breaks (default: 6)

### Positioning

- `--align <1..9>` — ASS alignment (see grid above)
- **Margins**: `--margin-l`, `--margin-r`, `--margin-v` (pixels)
- **Exact XY**: `--x <px> --y <px>` — use with the right **`--align`** (anchor) for predictable results
- **Motion**: `--move x1,y1,x2,y2,t1ms,t2ms` (ASS `\move`)

### Styling / Typography

- `--font "<name>"` (e.g., `"Baskerville"`, `"Helvetica"`, `"Source Sans 3"`)
- `--font-size <px>` (integer; pixel size in PlayRes space)
- `--bold`, `--italic`
- `--primary "#RRGGBB"` — text color
- `--outline "#RRGGBB"`, `--outline-width <px>`
- `--shadow <px>`
- `--back "#RRGGBB"`, `--back-opacity <0..1>`, `--border-style {1|3}`
- `--scale-x <percent>`, `--scale-y <percent>` — horizontal/vertical scaling of glyphs
- `--spacing <float>` — character spacing
- `--rotate <deg>` — rotation (ASS `\frz`) applied per event

### Script Resolution

- PlayRes is set **automatically** to video width/height (via `ffprobe`).
- If probing fails, captburn falls back to **1920x1080**.

### Encoding

- `--vcodec <codec>` (default: `libx264`)
- `--crf <int>` (default: 18)
- `--preset <str>` (default: `medium`)
- Audio is stream‑copied by default.

---

## Feature Table (Flags & Examples)

| Feature | Flag(s) | Description | Example |
|---|---|---|---|
| Input video | `-i, --input` | Path to input video file | `-i testfile.mp4` |
| Batch directory | `--in-dir` | Recursively process all videos in a directory | `--in-dir ./videos` |
| Transcript JSON | `-t, --trans-json` | Transcript file (or `<video>.json`) | `-t testfile.json` |
| Use existing capton | `--capton` | Load pre‑built events/styles from JSON | `--capton my.capton.json` |
| Output directory | `--out-dir` | Where outputs are written | `--out-dir out` |
| Caption style | `--style` | `popon`, `painton`, or `rollup` | `--style popon` |
| Roll‑up lines | `--rollup-lines` | Visible line window for roll‑up | `--rollup-lines 2` |
| Words per line | `--words-per-line` | Roll‑up line wrap threshold | `--words-per-line 7` |
| Alignment | `--align` | ASS anchor point 1..9 | `--align 2` |
| Margins | `--margin-l/-r/-v` | Pixel margins | `--margin-v 100` |
| Exact XY placement | `--x, --y` | Pixel‑true position (anchor = `--align`) | `--x 640 --y 360 --align 5` |
| Motion | `--move` | `x1,y1,x2,y2,t1ms,t2ms` | `--move 640,620,640,420,0,1500` |
| Font family | `--font` | Typeface name | `--font "Baskerville"` |
| Font size | `--font-size` | Pixel size in PlayRes space | `--font-size 36` |
| Weight/style | `--bold`, `--italic` | Bold/Italic toggles | `--italic` |
| Text color | `--primary` | `#RRGGBB` | `--primary "#FFFFFF"` |
| Outline | `--outline`, `--outline-width` | Outline color/width | `--outline "#000" --outline-width 2` |
| Shadow | `--shadow` | Drop shadow strength | `--shadow 3` |
| Opaque box | `--border-style 3`, `--back`, `--back-opacity` | Boxed captions | `--border-style 3 --back "#000" --back-opacity 0.8` |
| Glyph scale | `--scale-x`, `--scale-y` | Stretch/shrink text | `--scale-x 85` |
| Letter spacing | `--spacing` | Character spacing | `--spacing 4` |
| Rotation | `--rotate` | Degrees (ASS `\frz`) | `--rotate -1.2` |
| Video codec | `--vcodec` | e.g., `libx264` | `--vcodec libx264` |
| CRF | `--crf` | Quality, lower = higher quality | `--crf 18` |
| Preset | `--preset` | Encode speed/efficiency | `--preset medium` |

---

## Examples

Film dialogue (bottom‑center, small serif, clean):
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style popon   --align 2 --font "Baskerville" --italic --font-size 36   --primary "#FFFFFF" --outline "#000000" --outline-width 2 --margin-v 90
```

Top‑right film caption (Baskerville example):
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style popon   --align 9 --font "Baskerville" --italic --shadow 3   --primary "#FFFFFF" --outline "#202020" --outline-width 1   --margin-r 80 --margin-v 100
```

XY exact center (1280×720):
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style popon   --x 640 --y 360 --align 5
```

Motion drift upward (bottom‑center → higher) over 1.5s:
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style popon   --move 640,620,640,420,0,1500 --align 2
```

Paint‑on (word reveal) top‑center:
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style painton   --align 8 --font "Source Sans 3" --font-size 34 --outline "#000000"   --outline-width 2 --margin-v 90
```

Roll‑up (2 lines), bottom‑center:
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style rollup   --align 2 --margin-v 120 --rollup-lines 2 --words-per-line 7
```

Rotation tilt (film subtlety):
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style popon   --align 2 --rotate -1.2 --font "Source Sans 3" --font-size 40   --outline "#000000" --outline-width 2 --margin-v 100
```

---

## Capton JSON (Save/Reload Captions)

Every run writes a **capton JSON** alongside outputs:
- `<video>.captburn.json` — includes `style` and all `events` (with times, text, and any pos/move).
- You can feed this back with `--capton` to **re-burn** quickly without re-parsing transcripts.

Fields:
- `version` — schema version
- `style` — full style settings (font, colors, margins, alignment, etc.)
- `events[]` — list of `{ start, end, text, pos?, move? }`

---

## Troubleshooting

- **Alignment looks wrong / everything bottom‑left**  
  Ensure you’re on this fixed build (Style field order includes **Angle**). We also inject `\anN` on each event to force alignment.

- **XY isn’t landing where I expect**  
  Remember `--align` sets the **anchor** for `(x,y)`. For center anchor use `--align 5`, for top‑left use `--align 7`, etc.

- **Fonts look huge/small compared to expectations**  
  Font sizes are in **PlayRes pixels**. Since PlayRes = video size, `--font-size` scales with resolution. Adjust size accordingly.

- **ffprobe missing**  
  Install FFmpeg (includes `ffprobe`) and ensure it’s on your PATH.

- **ASS not burned / filter errors**  
  We try `-vf ass=...` then fall back to `-vf subtitles=...`. Ensure FFmpeg is compiled with libass.

---

## FAQ

**Q: Can I add per‑event rotation or colors?**  
A: Yes by extending event tags (e.g., `\frz`, `\c`) in code. Current CLI applies rotation uniformly via `--rotate`.

**Q: Does captburn support SRT/VTT?**  
A: Not directly — captburn writes **ASS** to leverage advanced styling and karaoke (`\k`) for paint‑on.

**Q: Can I generate only the ASS without burning?**  
A: Yes — just run and keep the generated `*.captburn.ass` in the output folder. You can use it independently with FFmpeg or media players.

---

## License

© 2025. Provided as‑is, no warranty. Use at your own risk.
