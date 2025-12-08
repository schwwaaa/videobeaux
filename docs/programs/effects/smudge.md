# smudge

## Description
Applies a gentle smudge effect to the video, softening edges and pulling colors slightly across motion paths.  
The result resembles a faint manual smear, as if the image were lightly dragged or brushed while still wet.

## Purpose
`smudge` is designed for creators who want:
- soft, organic distortion without heavy abstraction,  
- a mild “wet paint” or “finger drag” aesthetic,  
- subtle deformation suitable for dreamy or analog-inspired edits,  
- smoothing of harsh edges or digital sharpness,  
- a simple, no-argument effect that can be stacked or used as a finishing texture.

## How It Works
1. **Edge Softening**  
   The filter diffuses detail and blends micro-edges, reducing digital crispness.
2. **Directional Blur/Smear**  
   Motion or tonal boundaries smear slightly, giving the impression of a softly dragged image surface.
3. **Color Bleed**  
   Neighboring pixels influence one another to create subtle spreading of hue.
4. **Encoding**  
   Output is then encoded using Videobeaux global CRF, codec, and pixel-format settings.

## Program Template
```bash
videobeaux -P smudge \
  -i input.mp4 \
  -o output.mp4
```

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
```bash
videobeaux -P smudge \
  -i myvideo.mp4 \
  -o smudge_styled.mp4
```

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/user-attachments/assets/9bb80e0b-bf16-49e7-b4e1-6c0c79b59c32" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Ideal for footage with strong lines or shapes — smudging softens them into painterly contours.  
- Repeated smudging (e.g., applied twice in a chain) can create a watercolor-like wash.  
- Compression artifacts become smoother and less blocky after the smudge effect.  
- Works especially well before color-grading to produce a gentle base texture.

## Recommended Usage
- Dream sequences, surreal atmospheres, or emotional montage.  
- Soft, analog-inspired grading setups.  
- Background layers in collage or Lagkage layouts.  
- Visual art workflows that benefit from painterly distortion.  
- Preprocessing footage before heavy glitch effects to create contrast.

## Quality Tips
- Lower CRF yields smoother, more elegant smudges.  
- Higher CRF adds grit, making the smudge feel more raw or textural.  
- Combine with `slight_smear` for layered organic softness.  
- Use `repainting` afterward for a “hand-redrawn” effect.  
- Upscale with `resize` before smudging if you want especially smooth, flowing distortion.

