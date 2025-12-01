# triptych — videobeaux Program Documentation

## Overview
`triptych` is a videobeaux module for composing **three video sources** into a unified layout with **independent zoom control**, **symmetry‑safe stacking**, and a flexible **audio mixing system**.

### Supported Features
- **Layouts**
  - `hstack` — 3‑wide horizontal strip  
  - `vstack` — vertical 3‑layer column  
  - `diag` — diagonal composition (top‑left → center → bottom‑right)
- **Independent zoom for all three videos**
- **Safe stacking** using `scale2ref` normalization
- **Audio modes**
  1. audio from video 1  
  2. audio from video 2  
  3. audio from video 3  
  4. mix all three  
  5. mute  
  6. external audio file  
- **Volume control** (`--vol1`, `--vol2`, `--vol3`)
- **CRF / preset control**
- Fully compatible with videobeaux’s global flags like `--force`.

---

## Basic Usage

### Example (horizontal layout)
```bash
videobeaux -P triptych   -i media/base.mp4   -o out/triptych_basic.mp4   --input2 media/faith.mp4   --input3 media/menino.mp4   --layout hstack   --zoom1 1.0 --zoom2 1.0 --zoom3 1.0   --audio-mode 1   --force
```

---

## Arguments

### Required
| Flag | Description |
|------|-------------|
| `-i` | First input video (video 1) |
| `--input2` | Second input video |
| `--input3` | Third input video |
| `-o` | Output video path |

---

## Layout Options
Use:

```
--layout {hstack, vstack, diag}
```

### `hstack`
3 videos arranged left → center → right.  
Heights normalized safely.

### `vstack`
3 videos arranged top → middle → bottom.  
Widths normalized safely.

### `diag`
Diagonal composition:  
- video 1 = background  
- video 2 = centered  
- video 3 = bottom‑right  

---

## Zoom Controls

Each video can be independently scaled:

```
--zoom1 FLOAT   # zoom for video 1
--zoom2 FLOAT   # zoom for video 2
--zoom3 FLOAT   # zoom for video 3
```

- `1.0` = no change  
- `<1.0` = zoom out  
- `>1.0` = zoom in  

---

## Audio Modes

Set using:

```
--audio-mode N
```

### Available Modes

| Mode | Meaning |
|------|---------|
| `1` | Use audio from video 1 |
| `2` | Use audio from video 2 |
| `3` | Use audio from video 3 |
| `4` | Mix all three videos' audio |
| `5` | Mute (no audio track) |
| `6` | Use external audio file |

---

## Volume Controls

Each source has its own multiplier:

```
--vol1 FLOAT
--vol2 FLOAT
--vol3 FLOAT
```

- `1.0` = unity  
- `0.5` = half volume  
- `2.0` = double volume  

---

## External Audio

Used only when:

```
--audio-mode 6
```

Example:

```bash
--audio-mode 6 --audio-external media/music.wav
```

This replaces all video audio.

---

## Encoding Options

### CRF / preset

```
--crf FLOAT           # 18 default
--x264-preset NAME    # medium default
```

Examples: `slow`, `fast`, `veryslow`

---

## Example Set

### Horizontal with mixed audio
```bash
videobeaux -P triptych   -i media/a.mp4   -o out/triptych_mix.mp4   --input2 media/b.mp4   --input3 media/c.mp4   --layout hstack   --zoom1 1.0 --zoom2 1.0 --zoom3 1.0   --audio-mode 4   --vol1 1.0 --vol2 0.5 --vol3 0.3   --force
```

### Diagonal picture‑only
```bash
videobeaux -P triptych   -i media/a.mp4   -o out/triptych_picture_only.mp4   --input2 media/b.mp4   --input3 media/c.mp4   --layout diag   --zoom1 1.3 --zoom2 1.0 --zoom3 1.0   --audio-mode 5   --force
```

### Vertical with external audio
```bash
videobeaux -P triptych   -i media/a.mp4   -o out/triptych_vstack_ext_audio.mp4   --input2 media/b.mp4   --input3 media/c.mp4   --layout vstack   --zoom1 1.0 --zoom2 1.0 --zoom3 1.0   --audio-mode 6   --audio-external media/score.wav   --force
```

---

## Notes

- All stacking uses `scale2ref` to prevent ffmpeg errors.
- All “safe” overlay expressions are used for maximum compatibility.
- Volume is handled **outside** `-filter_complex` except for mix mode.
- Muting never touches the graph (just uses `-an`).

---

## Version
This document corresponds to the **stabilized triptych version** delivered on the latest update.

