# scrolling
:contentReference[oaicite:1]{index=1}

## Description
Applies a continuous scrolling motion to the video by shifting the image over time in a single direction.  
Unlike `scrolling_pro`, which allows multi-axis control, this module provides a simple, fixed-direction scroll effect — ideal for lightweight motion or ambient looping.

## Purpose
`scrolling` is designed for creators who want:
- a minimal, no-parameter scroll effect,  
- subtle ambient motion for backgrounds or textures,  
- lightweight directional drift without configuration,  
- simple kinetic movement for loops or collage layers,  
- predictable, consistent scroll behavior.

## How It Works
1. **Directional Motion**  
   The video image is translated across the frame at a fixed rate and direction.
2. **Wraparound Behavior**  
   Pixels exiting one side of the frame re-enter from the opposite side, producing an infinite-scroll illusion.
3. **Fixed Parameters**  
   Since the module has no program-specific arguments, its scroll speed and direction are predetermined.
4. **Encoding**  
   Output is encoded using global Videobeaux CRF, codec, and pixel-format settings.

## Program Template
```bash
videobeaux -P scrolling -i input.mp4 -o output.mp4
```

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
```bash
videobeaux -P scrolling \
  -i myvideo.mp4 \
  -o scrolling_styled.mp4
```

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/4cdebccc-8519-45c6-aded-089db73d20d2" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Because scroll speed is fixed, this module is ideal for simple kinetic backgrounds.  
- Looping behavior depends on footage content; pattern-like textures loop more seamlessly.  
- Best used when a uniform directional drift is desired without fine-tuning.  
- Works cleanly at any resolution or aspect ratio.

## Recommended Usage
- Ambient looping textures for projection or VJ systems.  
- Background drift behind titles, overlays, or motion graphics.  
- Simple motion injection for collage edits.  
- Use in batch workflows where consistent, automated scroll is needed.

## Quality Tips
- Lower CRF produces smoother scrolling with fewer compression artifacts.  
- Slight pre-blur (e.g., via `blur_pix`) can reduce visible seams in detailed footage.  
- Pair with `lsd_feedback` for evolving drifting effects.  
- Combine with `overexposed_stutter` or `nostalgic_stutter` for stylized motion disruption.  
- Use `convert_dims` beforehand if preparing platform-specific scrolling backgrounds.

