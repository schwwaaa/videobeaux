# ghostee

## Description
Applies a soft, subtle ghosting effect to the video by blending frames over time.  
This creates a trailing, dreamy afterimage that lightly smears motion and adds a supernatural or ethereal visual mood.

## Purpose
`ghostee` is designed for artists who want:
- a gentle afterimage effect instead of heavy motion smearing,  
- soft motion trails without strong distortion,  
- a dreamy, floating, or spectral visual tone,  
- an atmospheric layer for music videos and ambient visuals,  
- a minimal, elegant ghost effect that doesn’t overwhelm the footage.

## How It Works
1. **Frame Blending**  
   Consecutive frames are blended with diminishing influence, producing a light optical-ghost effect.
2. **Subtle Persistence**  
   Motion appears to leave a soft residue rather than a strong smear or echo.
3. **Minimal Contrast Disruption**  
   Highlights, shadows, and midtones maintain structure—only motion is affected.
4. **Encoding**  
   Output uses global Videobeaux codec settings (CRF, pixel format, preset).

## Program Template
    videobeaux -P ghostee \
      -i input.mp4 \
      -o output.mp4

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
    videobeaux -P ghostee \
      -i myvideo.mp4 \
      -o ghostee_styled.mp4

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/user-attachments/assets/87c8b569-5165-485d-ae09-7a8bbbe74051" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Produces mild persistence, unlike `frame_delay_pro1` or `frame_delay_pro2`, which provide more extreme temporal manipulation.  
- Works especially well on slow-motion or atmospheric footage.  
- Compression settings influence ghost smoothness—higher CRF may increase noise within the trail.  
- High-motion shots will produce noticeable yet still delicate ghost trails.

## Recommended Usage
- Dreamlike music videos or ambient visualizers.  
- Supernatural, memory-like, or nostalgic sequences.  
- Layered VJ and projection-mapped installations.  
- Subtle aesthetic enhancement for drone shots or slow pans.  
- Mixing into a visual chain with stronger distortions for hybrid textures.

## Quality Tips
- For smoother trails, lower CRF to reduce compression breakup.  
- Combine with `double_cup` for syrupy dream visuals.  
- Pair with `blur_pix` to soften structure while keeping ghost trails intact.  
- For more pronounced trails, run `ghostee` multiple times or chain with `frame_delay_pro1`.  
- Use on well-lit footage for cleanest ghost silhouettes.

