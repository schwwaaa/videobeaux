# bad_predator

## Description
Applies a stylized “bad Predator heat vision” effect to the input video.  
This intentionally degraded thermal-vision look mimics the broken or low-budget interpretation of the thermal-view used in the *Predator* films — surreal color distortion, thermal-like banding, exaggerated edge detection, and unstable gradients.

## Purpose
`bad_predator` is designed for creators who want to:
- add a faux–heat vision aesthetic,  
- produce psychedelic or thermal-like color distortions,  
- disrupt realism with genre-coded VFX,  
- introduce mood, abstraction, or sci-fi ambience,  
- create an intentionally *wrong* or glitchy interpretation of cinematic thermal vision.

## How It Works
1. **Thermal Color Remapping**  
   The video is transformed into an artificial temperature-based palette, often with exaggerated reds, blues, greens, and neon ranges.
2. **Edge Boosting & Gradient Distortion**  
   Edges may “glow,” flatten, or warp, imitating digital thermal sensors or corrupted color channels.
3. **Contrast Folding**  
   Shadows and highlights are redistributed into stylized color bins rather than natural brightness patterns.
4. **Encoding**  
   Output is encoded using global Videobeaux settings (codec, CRF, pixel format).

## Program Template
    videobeaux -P bad_predator \
      -i input.mp4 \
      -o output.mp4

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
    videobeaux -P bad_predator \
      -i myvideo.mp4 \
      -o bad_predator_styled.mp4

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/0968ad50-cc97-4336-938f-01b47d86a7bd" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- The effect is purely stylistic — not physically accurate thermal imaging.  
- Works best on footage with strong silhouettes or motion, where thermal-emulated contrast is most visible.  
- If the global pixel format is set to low bit depth (e.g., 8-bit), banding interacts strongly with the effect, enhancing the “bad thermal” look.  
- Use `chain_builder` to combine with other stylized processes for multi-layer sci-fi or horror visuals.

## Recommended Usage
- Music videos, experimental film, and glitch-aesthetic sequences.  
- Sci-fi projects referencing Predator-style heat vision.  
- Stylized surveillance overlays or false-sensor aesthetics.  
- Abstract color grading for live visuals or performance art.

## Quality Tips
- Apply before compression-heavy steps to preserve the color distortions.  
- Combine with `bad_contrast`, `hash_fingerprint`, or `bad_animation` for a fully degraded sensory aesthetic.  
- Use lower CRF values to avoid washing out the neon tonal ranges.  
- Consider pairing with `gamma_fix` to stabilize midtone visibility before applying the effect.
