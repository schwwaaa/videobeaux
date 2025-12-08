# bad_contrast

## Description
Applies a “bad contrast” visual effect to the video, intentionally degrading tonal balance, highlight rolloff, shadow separation, and midtone neutrality.  
The result simulates low-quality analog transfers, misconfigured broadcast equipment, degraded VHS dubs, or broken grading pipelines.

## Purpose
`bad_contrast` exists as a lightweight, stylized degradation tool for artists who want to:
- introduce tonal instability or harsh contrast,  
- mimic analog-era video duplication artifacts,  
- add mood through blown-out highlights or crushed shadows,  
- create an intentionally incorrect exposure/contrast aesthetic,  
- emphasize “bad video” texture in music videos, glitch art, or experimental film.

## How It Works
1. **Contrast Manipulation**  
   The module applies an internally defined filter chain that exaggerates or distorts normal contrast response.
2. **Highlight / Shadow Distortion**  
   Highlights may appear clipped or harsh; shadows may compress or posterize.
3. **Midtone Bias**  
   The effect may introduce incorrect gamma or uneven tonal mapping to create a “broken” look.
4. **Encoding**  
   Final output uses global Videobeaux codec, pixel format, and CRF settings.

## Program Template
    videobeaux -P bad_contrast \
      -i input.mp4 \
      -o output.mp4

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
    videobeaux -P bad_contrast \
      -i myvideo.mp4 \
      -o bad_contrast_styled.mp4

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/9ba59b08-79a8-4a09-8b18-c0fe90a6c5e2" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- The exact look depends partly on global Videobeaux encoding settings.  
- Output may exhibit blown-out whites, crushed blacks, or tonal banding.  
- Not intended for corrective workflows — this is a purely stylistic degradation.  
- Works particularly well on motion-heavy or color-rich footage.  
- As with all destructive effects, applying `bad_contrast` early in a pipeline will influence all later operations.

## Recommended Usage
- Broken-TV or analog-digital hybrid aesthetics.  
- Glitch art, experimental cinema, and abstract video installations.  
- Distressing otherwise clean digital footage.  
- Music videos seeking stylized degradation.  
- As an “imperfection layer” paired with other Videobeaux modules (e.g., `bad_animation`, `hash_fingerprint`).

## Quality Tips
- Apply at the end of a chain to maximize visible distortion.  
- Pair with lower CRF values if you want compression artifacts to interact with tonal distortion.  
- Use on footage with clear highlight/shadow separation for the strongest effect.  
- Combine with LUTs or `lut_apply` to push contrast into more extreme color spaces.  
- For a VHS-like aesthetic, consider pairing with `bad_contrast` + `convert_dims` (480p or 720hd presets).
