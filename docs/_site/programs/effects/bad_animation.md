# bad_animation

## Description
Applies a “bad animation” effect to the input video — producing jittery, uneven, low-frame-feeling, or intentionally crude animated motion.  
This effect simulates broken or poorly interpolated animation, often seen in retro cartoons, limited-animation TV shows, or stylized glitch art.

## Purpose
`bad_animation` is designed for artists who want to:
- degrade motion intentionally,  
- create choppy, low-fidelity animated movement,  
- mimic missing-frame aesthetics,  
- produce a stylized “hand-made” or “broken pipeline” feel,  
- add a lo-fi or experimental animation quality to footage.

## How It Works
1. **Frame Manipulation**  
   Frames may be dropped, unevenly held, or reused to break smooth motion.
2. **Temporal Distortion**  
   Motion cadence is intentionally disrupted to create jitter or uneven pacing.
3. **Filtering**  
   The module may use global FFmpeg filter chains (as configured in Videobeaux) to generate texture, flicker, or stutter artifacts.
4. **Encoding**  
   Output is written using global Videobeaux encoding settings (CRF, codec, pixel format, preset, etc.).

## Program Template
    videobeaux -P bad_animation \
      -i input.mp4 \
      -o output.mp4

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
    videobeaux -P bad_animation \
      -i myvideo.mp4 \
      -o bad_animation_styled.mp4

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/user-attachments/assets/1fa8de04-98ef-49f7-9415-616e07210f0e" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- The exact effect depends on Videobeaux global filter configuration and output codec settings.  
- Since this effect manipulates cadence, final output FPS may differ from perceived motion.  
- Best used on footage where stylized motion degradation is desirable.  
- The module performs processing only on video; audio behavior follows global Videobeaux standards.

## Recommended Usage
- Music videos, experimental film, and stylized animation.  
- Retro cartoon emulation or low-budget limited-animation effects.  
- Distortion-based visual art, glitchworks, or datamosh-adjacent styles.  
- Creating intentionally flawed animated loops.

## Quality Tips
- Pair with `frame_interpolate` (ironically) to contrast smooth vs broken motion.  
- Use higher CRF values if you want even more degradation in compression.  
- Combine with `gamma_fix`, `lut_apply`, or `convert_dims` for multi-stage stylization chains.  
- Consider using `chain_builder` to apply bad_animation early in a larger creative pipeline.
