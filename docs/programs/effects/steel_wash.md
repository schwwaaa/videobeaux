# steel_wash

## Description
Applies a cool steel-blue wash across the entire video image.  
The effect evokes the feel of industrial lighting, cold metal surfaces, or desaturated cinematic palettes often seen in sci-fi, dystopian, and neo-noir aesthetics.

## Purpose
`steel_wash` is designed for creators who want:
- a clean, cool-toned chromatic shift,  
- a desaturated metallic aesthetic,  
- a simple and reliable grading filter with no parameters,  
- a cohesive blue wash to unify mismatched footage,  
- a subtle but distinctive look that enhances atmosphere and mood.

## How It Works
1. **Global Blue Bias**  
   Shadows, midtones, and highlights are shifted toward cold steel-blue coloration.
2. **Desaturation Layer**  
   Other hues are reduced, allowing the steel tone to dominate.
3. **Contrast Conditioning**  
   Mild tonal shaping prevents the image from becoming flat while maintaining the cold aesthetic.
4. **Encoding**  
   Final output is encoded using global Videobeaux codec, CRF, and pixel-format settings.

## Program Template
```bash
videobeaux -P steel_wash \
  -i input.mp4 \
  -o output.mp4
```

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
```bash
videobeaux -P steel_wash \
  -i myvideo.mp4 \
  -o steel_wash_styled.mp4
```

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/eea99448-9352-48f1-a1ec-b2cac6ad056d" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Works particularly well with nighttime, industrial, mechanical, or urban footage.  
- Skin tones take on a stylized, pale-blue cast — ideal for sci-fi or dystopian moods.  
- High-saturation footage will be subdued; low-saturation footage becomes more cohesive.  
- Compression interacts minimally with the wash due to its uniformity.

## Recommended Usage
- Neo-noir or cyberpunk scenes.  
- Cold, metallic grading for music videos.  
- Industrial montage or mechanical close-ups.  
- Consistent color unification before collage or Lagkage layouts.  
- Atmospheric shifting before applying more intense glitch effects.

## Quality Tips
- Lower CRF preserves subtle gradients in blue-toned areas.  
- Higher CRF introduces grit that enhances industrial textures.  
- Combine with `bad_contrast` for harsher, high-impact steel tones.  
- Pair with `ghostee` or `slight_smear` for dreamy industrial softness.  
- Apply before LUTs to let your LUT react to the steel wash; apply after to preserve LUT integrity.

