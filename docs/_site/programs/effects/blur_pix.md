# blur_pix

## Description
Applies a pixelated blur effect to the input video, producing a blocky, low-resolution softening reminiscent of censored footage, retro 8-bit graphics, or lo-fi compression artifacts.  
This effect blends coarse pixelation with smooth blur, creating a stylized, abstracted visual aesthetic.

## Purpose
`blur_pix` is designed for artists who want to:
- intentionally degrade detail in a stylized way,  
- anonymize or obscure shapes without traditional Gaussian blur,  
- evoke retro-game pixelation,  
- add a surreal soft-block look to motion and texture,  
- produce a hybrid blur–pixelation effect ideal for glitch, collage, or experimental works.

Because the module has **no program-specific arguments**, it is simple to use and highly compatible with all Videobeaux pipelines.

## How It Works
1. **Pixel Block Generation**  
   The input frame is reduced to coarse pixel clusters using an internal scaling or mosaic-based algorithm.
2. **Softening Pass**  
   A smoothing filter blends block edges to create a soft, dreamy, broken-resolution aesthetic.
3. **Unified Blur-Pixel Layer**  
   The combined effect emphasizes abstraction over clarity, often producing painterly motion.
4. **Encoding**  
   The final output is encoded using global Videobeaux codec settings (CRF, preset, pixel format, etc.).

## Program Template
    videobeaux -P blur_pix \
      -i input.mp4 \
      -o output.mp4

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
    videobeaux -P blur_pix \
      -i myvideo.mp4 \
      -o blur_pix_styled.mp4

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/65403294-3e34-4ff8-816a-5de7c80c811d" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Pixelated blur behaves differently from Gaussian or box blur — detail is removed structurally, not just softened.  
- Compression interacts strongly with this effect, sometimes enhancing the aesthetic.  
- Works consistently regardless of resolution, though higher-resolution source footage yields more visible block abstraction.  
- Global Videobeaux settings (CRF, pixel format) can shift how “clean” or “dirty” the blocks appear.

## Recommended Usage
- Music videos needing stylized abstraction.  
- Identity-obscuring or anonymization with artistic flair.  
- Retro-inspired or video-game-like sequences.  
- Experimental cinema, collage art, and painterly motion effects.  
- Background layers in VJ, projection, or live visual systems.

## Quality Tips
- Lower CRF (higher quality) preserves cleaner block edges.  
- Higher CRF increases compression noise — sometimes desirable for a gritty aesthetic.  
- Pair with `hash_fingerprint` or `bad_contrast` to stack analog/digital degradation.  
- Combine with `convert_dims` (square or portrait presets) for platform-optimized stylized loops.  
- Pre-processing with `gamma_fix` can improve highlight/midtone visibility inside blocky regions.
