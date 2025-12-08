# soapblind

## Description
Applies a hazy, washed-over film that resembles the visual blur of “soap-blinded eyes” — a foggy, filmy distortion that softens detail and reduces clarity.  
The result is a dreamy, smeared, low-contrast haze that feels like staring through suds, steam, or a semi-opaque membrane.

## Purpose
`soapblind` is designed for creators who want:
- soft-focus blur with a filmy, washed texture,  
- low-clarity visuals that feel dreamy, obscured, or emotional,  
- stylized haze for music videos, collage, or narrative sequences,  
- an immediate, no-argument atmospheric filter,  
- a diffused look that smooths harsh details and glazes the frame.

## How It Works
1. **Surface Diffusion**  
   A hazy overlay softens micro-contrast and reduces sharpness.
2. **Fog-Like Bloom**  
   Highlights bloom outward, mimicking fogged or soap-smeared vision.
3. **Clarity Reduction**  
   Noise, edges, and fine detail are blurred to create a dreamlike veil.
4. **Encoding**  
   The final treated video is encoded with global Videobeaux settings (codec, CRF, pixel format).

## Program Template
```bash
videobeaux -P soapblind \
  -i input.mp4 \
  -o output.mp4
```

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
```bash
videobeaux -P soapblind \
  -i myvideo.mp4 \
  -o soapblind_styled.mp4
```

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/user-attachments/assets/28070fe5-52cd-42c9-93b7-a417c83add2d" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Smooth surfaces and skin tones take especially well to the soapblind look.  
- High-contrast footage will soften dramatically as edges blur.  
- Compression can make fogginess appear more pronounced at higher CRF levels.  
- Works as a gentler alternative to heavy blur filters.

## Recommended Usage
- Emotional, melancholic, or introspective scenes.  
- Dream sequences or memory dissolves.  
- Music videos needing soft glaze or atmospheric haze.  
- Preprocessing for collage pieces to unify mismatched clips.  
- Creating softness before applying glitch or distortion filters.

## Quality Tips
- Lower CRF yields velvety, smooth haze.  
- Higher CRF introduces gritty texture into the fog.  
- Combine with `slight_smear` for a double-soft aesthetic.  
- Pair with `repainting` for painterly, softened brushlike visuals.  
- Use before LUTs if you want the softness baked into the grade; use after if you want LUTs to remain crisp.

