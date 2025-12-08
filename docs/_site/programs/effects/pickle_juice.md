# pickle_juice

## Description
Applies a stylized color-treatment effect that makes the video appear as if it were “dipped in pickle juice.”  
This look often includes green-tinted washes, acidic highlights, sour midtone shifts, and a brined, stained aesthetic reminiscent of aged film submerged in an odd chemical bath.

## Purpose
`pickle_juice` is designed for creators who want:
- green, brined, or chemically-tinted color distortion,  
- a dirty, acidic film-wash effect,  
- moody or surreal grading without using LUTs,  
- stylized discoloration for music videos, collage art, or experimental edits,  
- an instantly recognizable “soured” treatment that feels organic and gritty.

## How It Works
1. **Color Shifting**  
   The effect pushes hues toward:
   - greenish brine,  
   - yellow-acid midtones,  
   - desaturated shadows.
2. **Highlight Contamination**  
   Bright regions may take on a pickled glow, exaggerating chemical staining.
3. **Tonal Warping**
   Midtones may twist or invert subtly to enhance the brined aesthetic.
4. **Encoding**  
   Output is encoded using global Videobeaux parameters (CRF, codec, pixel format).

## Program Template
```bash
videobeaux -P pickle_juice \
  -i input.mp4 \
  -o output.mp4
```

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
```bash
videobeaux -P pickle_juice \
  -i myvideo.mp4 \
  -o pickle_juice_styled.mp4
```

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/387bfff5-fbdd-423d-b482-8ab4d5ce744f" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Green-heavy color channels may clip differently depending on global gamma or LUTs applied earlier in the chain.  
- Compression artifacts may take on a greenish tint, especially at higher CRF values.  
- Works very well on brightly lit footage, where the “pickle wash” becomes more obvious.  
- The effect’s strength may vary depending on the source’s saturation and dynamic range.

## Recommended Usage
- Stylized music videos seeking gritty, acidic toning.  
- Collage-style edits where each clip has a unique chemical wash.  
- VHS-simulation workflows combined with `bad_contrast` or `nostalgic_stutter`.  
- Color-driven experimental cinematography.  
- Thematic sequences that benefit from a “soured,” off-kilter look.

## Quality Tips
- Use lower CRF values to keep the color warping clean and smooth.  
- Use higher CRF if you want noisy, grainy, stained artifacts.  
- Pair with `gamma_fix` before applying for more consistent pickle coloration across the image.  
- Combine with `blur_pix` for a soft, brined haze effect.  
- Apply after `convert_dims` if producing platform-specific versions (square, reels, etc.).

