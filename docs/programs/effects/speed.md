# speed

## Description
Changes the playback speed of the input video and audio simultaneously.  
This module is useful for slow motion, fast motion, timelapse, rhythmic edits, and any effect requiring temporal compression or expansion.

## Purpose
`speed` is designed for creators who want to:
- increase or decrease playback speed uniformly,  
- generate slow-motion or fast-motion stylization,  
- build rhythmic visual edits synced to music,  
- create timelapse effects without external tools,  
- maintain audio pitch relationship unless later reprocessed.

## How It Works
1. **Timebase Adjustment**  
   Video frames are retimed according to the provided speed factor.
2. **Audio Resampling**  
   Audio is also sped up or slowed down to match the new video duration.
3. **Encoding**  
   The resulting retimed clip is encoded using global Videobeaux settings (codec, CRF, pixel format).

### Notes  
- Speed values **greater than 1.0** = faster playback.  
- Speed values **less than 1.0** = slower playback.  

## Program Template
```bash
videobeaux -P speed \
  -i input.mp4 \
  -o output.mp4 \
  --speed_factor VALUE
```

## Arguments

- **speed_factor** — Multiplier for playback speed.  
  - `0.5` → half-speed (slow motion)  
  - `2.0` → double-speed (fast motion)  
  - `0.25` → quarter-speed  
  - `4.0` → 4× speed

## Real World Example
```bash
videobeaux -P speed \
  -i myvideo.mp4 \
  -o speed_styled.mp4 \
  --speed_factor EXAMPLE
```

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/c27efdb1-ae81-4d8d-a153-de6294b7fedf" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Audio pitch will shift unless processed later with an external pitch-correction tool.  
- High speed factors may expose motion judder depending on frame rate.  
- Very slow speeds may require additional interpolation if smooth motion is desired (use `frame_interpolate` first).  
- Retime operations do not introduce new frames; they only alter timing unless combined with interpolation.

## Recommended Usage
- Music video edits synced to rhythmic patterns.  
- Timelapse creation.  
- Slow-motion mood sequences.  
- Fast-motion montage, humor, or surreal pacing.  
- Preprocessing before LUTs or effects when timing matters.

## Quality Tips
- For the cleanest slow motion, run `frame_interpolate` before `speed` to create missing frames.  
- Use lower CRF for crisp motion edges when speeding up footage.  
- Use higher CRF for intentionally grittier motion artifacts.  
- Pair with `looper_pro` for smooth motion loops.  
- Combine with `nostalgic_stutter` or `bad_animation` for stylized cadence distortion.

