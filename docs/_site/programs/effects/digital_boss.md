# digital_boss

## Description
Applies a “busted Game Boy–style digital boss” effect to the video — producing harsh bitmap artifacts, limited 8-bit tonal mapping, flicker, false edges, and unstable block transitions reminiscent of corrupted handheld-console graphics.  
The effect aims to evoke a glitched, retro, boss-fight visual language.

## Purpose
`digital_boss` is intended for creators who want to:
- simulate broken handheld-console graphics,  
- add 8-bit or pseudo-Game-Boy stylistic decay,  
- impose limited palettes, blocky edges, or sprite-like motion,  
- create glitchy boss-battle ambience,  
- stylize footage for music videos, live visuals, or retro-digital art.

## How It Works
1. **Palette Reduction**  
   The image is remapped into a restricted tonal palette similar to classic handheld consoles.
2. **Block Artifacting**  
   Block-based distortions mimic corrupted tiles or unstable frame buffer graphics.
3. **Edge Reinforcement**  
   Contours are emphasized in a way similar to sprite outlines or tile boundaries.
4. **Temporal Instability**  
   Slight flicker or jitter introduces the feel of a malfunctioning digital system.
5. **Encoding**  
   Output uses global Videobeaux encoding settings (codec, CRF, pixel format, presets).

## Program Template
    videobeaux -P digital_boss \
      -i input.mp4 \
      -o output.mp4

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
    videobeaux -P digital_boss \
      -i myvideo.mp4 \
      -o digital_boss_styled.mp4

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/user-attachments/assets/23958066-f384-4801-9d91-5b2df6081a31" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Compression interacts strongly with this effect — higher CRF may enhance the gritty retro look.  
- Because the effect uses hard palette steps, gradients may posterize or flicker dramatically.  
- Best used on footage with strong shapes, characters, or silhouettes.  
- High-motion content will exaggerate jitter and tile instability.

## Recommended Usage
- Retro boss-fight sequences or video-game-themed edits.  
- Concert visuals or projection loops with digital-grunge aesthetics.  
- Glitch-art animation, collage, and experimental video.  
- Stylized narrative inserts to break realism.  
- Layering with `bad_predator`, `blur_pix`, or `hash_fingerprint` for extreme digital corruption.

## Quality Tips
- Lower CRF (higher quality) preserves cleaner tile boundaries; higher CRF increases noisy decay.  
- Combine with `convert_dims` to produce Game-Boy-like square aspect ratios.  
- Pre-apply `gamma_fix` for more even tonal distribution before palette reduction.  
- If the effect feels too clean, pair with `bad_animation` for extra jitter or cadence disruption.  
- Chain before heavy compression if you want the compression to participate in the aesthetic.
