# repainting

## Description
Applies an artistic “repainted” effect that makes each frame appear as if it has been smeared, redrawn, or blurred by an alcohol-washed brush.  
The result resembles wet ink, soft smudging, streaked pigment, or repeated overpainting — giving the footage a tactile, analog, hand-altered feel.

## Purpose
`repainting` is designed for creators who want:
- a painterly, reworked, or smeared aesthetic,  
- a hand-drawn or alcohol-wet look without using frame-by-frame animation,  
- soft organic distortion that feels handmade rather than digital,  
- degraded yet artistic texture for music videos or collage,  
- a simple effect that produces expressive motion smearing.

## How It Works
1. **Frame Reinterpretation**  
   Each frame is processed as if it were being redrawn or wiped over with semi-wet pigment.
2. **Smudge + Alcohol-Wash Simulation**  
   Highlights bloom, shadows soften, and edges blur as if dissolved by solvent.
3. **Temporal Softening**  
   Minor streaks or trailing may appear due to repeated repainting across frames.
4. **Encoding**  
   Output is encoded using global Videobeaux settings (codec, CRF, pixel format).

## Program Template
```bash
videobeaux -P repainting -i input.mp4 -o output.mp4
```

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
```bash
videobeaux -P repainting \
  -i myvideo.mp4 \
  -o repainting_styled.mp4
```

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/user-attachments/assets/1770144d-4448-4719-8ef3-e44b720ec857" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Works especially well on footage with bold shapes, faces, or brush-like motion paths.  
- High-contrast imagery yields more pronounced smearing.  
- Compression may increase the “wet paint” feel by interacting with soft, blended regions.  
- Repainting is non-destructive in timing — cadence stays intact even while textures distort.

## Recommended Usage
- Abstract or painterly music videos.  
- Alcohol-ink inspired motion design.  
- Narrative moments needing dreamlike or smeared transitions.  
- Experimental cinema and visual collage.  
- Live VJ loops that benefit from organic, evolving texture.

## Quality Tips
- Lower CRF values maintain smooth, fluid repainted strokes.  
- Higher CRF adds grit, giving the effect a rougher, stained appearance.  
- Combine with `double_cup` for a liquified wash; combine with `blur_pix` for soft surface blending.  
- Apply before LUTs if you want the grade to unify the smear colors; apply after LUTs if you want the smear to distort the grade itself.  
- Up-scaling beforehand using `convert_dims` can produce smoother brush-like textures.

