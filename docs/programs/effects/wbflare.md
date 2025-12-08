# wbflare

## Description
Applies a blown-out white-balance flare that washes the frame in bright, overexposed warmth.  
The effect simulates a camera whose white balance has catastrophically failed, producing harsh brightness spikes, color melt, and an unstable exposure cast.

## Purpose
`wbflare` is designed for creators who want:
- intense, flared overexposure resembling broken auto-WB,  
- cinematic whiteouts and warm, blooming flare pulses,  
- chaotic light wash reminiscent of damaged DSLR sensors,  
- a stylized flare aesthetic for music videos, montage, or collage,  
- a single-command solution with no configuration required.

## How It Works
1. **White Balance Miscalibration Simulation**  
   The image is shifted toward overly warm, blown-out values.
2. **Flare Bloom**  
   Bright areas bloom outward aggressively, swallowing surrounding detail.
3. **Exposure Push**  
   Midtones and highlights ascend toward near-white, creating clip-heavy transitions.
4. **Encoding**  
   Output is encoded using Videobeaux global CRF, codec, and pixel-format settings.

## Program Template
```bash
videobeaux -P wbflare \
  -i input.mp4 \
  -o output.mp4
```

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
```bash
videobeaux -P wbflare \
  -i myvideo.mp4 \
  -o wbflare_styled.mp4
```

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/user-attachments/assets/e2a5f065-163e-4bb9-8fd3-1edbfbdbab2a" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Flare intensity is influenced by scene brightness—high-key footage becomes extremely washed out.  
- Skin tones may lose detail entirely as white balance collapses.  
- Compression interacts strongly with blown highlights; higher CRF introduces chaotic flare grit.  
- Works well as a transition or emotional accent, especially during musical peaks.

## Recommended Usage
- Music-video chorus drops or emotional surges.  
- Stylized whiteouts in experimental film or collage.  
- Dreamlike or transcendental sequences.  
- Grungy digital “camera malfunction” aesthetics.  
- Transitional flare blasts between scenes.

## Quality Tips
- Lower CRF preserves cleaner bloom gradients.  
- Higher CRF produces gritty, noisy flare textures.  
- Pair with `overexposed_stutter` for extreme blown-out instability.  
- Combine with `bad_contrast` to deepen shadows beneath the flare.  
- Apply before LUTs for LUT-reactive highlights; apply after LUTs for a uniform whiteout.

