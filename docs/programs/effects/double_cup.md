# double_cup
:contentReference[oaicite:1]{index=1}

## Description
Applies a syrupy, slowed, woozy audiovisual effect reminiscent of “purple drank” aesthetics.  
The look emphasizes heavy color bleeding, slowed-feeling motion, chromatic haze, and a dreamlike viscosity often associated with chopped-and-screwed culture or psychedelic video distortion.

## Purpose
`double_cup` is ideal for creators who want to:
- introduce trippy, codeine-inspired visual atmosphere,  
- slow or drag the *feeling* of motion without modifying frame rate,  
- add soft-focus color diffusion with deep purples and magentas,  
- evoke vaporwave, cloud-rap, chopped/screwed, or intoxicated digital moods,  
- distort clarity into a smeared, syrup-soaked texture.

## How It Works
1. **Color Drenching**  
   Highlights and midtones are pushed toward purple, pink, and magenta tones.
2. **Soft Haze / Bloom**  
   The image takes on a velvety, low-contrast haze that reduces sharp edges.
3. **Viscous Motion Sensation**  
   Motion may *feel* slower due to subtle temporal diffusion and blending, even if FPS remains constant.
4. **Contrast Flattening**  
   Dark areas may lift while bright areas smear into a syrup-glow.
5. **Encoding**  
   Output is written using global Videobeaux codec and quality settings.

## Program Template
    videobeaux -P double_cup \
      -i input.mp4 \
      -o output.mp4

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
    videobeaux -P double_cup \
      -i myvideo.mp4 \
      -o double_cup_styled.mp4

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/83d30a18-40d1-42e4-aff3-dbd50d67a7d1" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- The effect pairs best with footage containing midtone gradients or neon lighting.  
- Compression interacts strongly with this aesthetic — higher CRF values intensify smearing and color wash.  
- Strong purples and pinks may clip if global gamma settings are aggressive; consider pre-processing with `gamma_fix`.  
- Works especially well in music video contexts.

## Recommended Usage
- Vaporwave, cloud rap, chopped-and-screwed visuals.  
- Psychedelic edits and dream-sequence overlays.  
- Live VJ loops and projection-mapped environments.  
- Mood-setting transitions between high-energy and slow-motion scenes.

## Quality Tips
- Use a lower CRF (higher quality) to retain smooth haze gradients.  
- Combine with `blur_pix` or `bad_contrast` for more degraded, syrup-soaked textures.  
- For extreme purple saturation, apply `lut_apply` with a magenta-heavy LUT before this effect.  
- If the image feels too dark, pair with `gamma_fix` for lifted midtones before applying `double_cup`.
