# xrgb

## Description
Applies an extreme RGB color treatment that aggressively remixes channel intensity, contrast, and chromatic balance.  
This effect pushes the video into hyper-saturated, unnatural, or neon-driven territory — producing explosive color distortions ideal for glitch, psychedelia, or high-impact stylization.

## Purpose
`xrgb` is designed for creators who want:
- radical RGB manipulation with a single command,  
- intense chromatic shifts far beyond standard grading,  
- neon, glitch, or chemically warped color palettes,  
- an exaggerated look that feels synthetic and electrified,  
- a quick way to break naturalistic color and enter surreal aesthetics.

## How It Works
1. **RGB Channel Rebalancing**  
   Each color channel (R, G, B) is amplified, crushed, or redistributed.
2. **Color Explosion**  
   Standard hues may break apart into aggressively tinted regions.
3. **Chromatic Distortion**  
   Highlights and shadows may shift toward extreme primaries, producing:
   - glowing neon edges  
   - warped color bands  
   - digital-chemical tonality
4. **Encoding**  
   Output is encoded using Videobeaux global settings for codec, CRF, and pixel format.

## Program Template
```bash
videobeaux -P xrgb \
  -i input.mp4 \
  -o output.mp4
```

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
```bash
videobeaux -P xrgb \
  -i myvideo.mp4 \
  -o xrgb_styled.mp4
```

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/user-attachments/assets/c9644cd5-a584-4f0d-ada3-13046e6938a5" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Bright, high-contrast footage produces the most dramatic RGB explosions.  
- Low-saturation footage transforms into hard-edged neon fields.  
- Compression interacts strongly with extreme channel imbalance; high CRF yields noisy rainbowing.  
- Works exceptionally well before glitch modules such as `crossmosh` or `lsd_feedback`.

## Recommended Usage
- Psychedelic music videos.  
- Glitch-art edits requiring aggressive color disruption.  
- Abstract collage or RGB-driven montage.  
- Visualizer loops with electric chromatic energy.  
- Maximalist stylization pipelines that reject naturalistic color.

## Quality Tips
- Lower CRF helps maintain smooth gradients inside extreme color zones.  
- Higher CRF introduces chaotic grain — useful for grunge or noisy RGB corruption.  
- Combine with `slight_smear` for neon-blooming distortion.  
- Apply `blur_pix` afterward for soft neon haze; apply beforehand for sharpened RGB breaks.  
- For a colder palette, chain `steel_wash` after xrgb; for warmer neon, chain `wbflare`.

