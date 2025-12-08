# zapruder

## Description
Applies a stylized “Zapruder film” aesthetic inspired by the iconic 1960s 8mm footage.  
The effect simulates historical analog film qualities including jitter, grain, contrast instability, chromatic fading, and hand-held mechanical wobble.

The result resembles degraded archival film transferred from aging physical media.

## Purpose
`zapruder` is designed for creators who want:
- an old-film documentary aesthetic,  
- jittery analog motion reminiscent of early consumer cameras,  
- heavy grain and historical degradation,  
- warm-to-greenish retro color shifts,  
- a single-command tool to invoke archival authenticity.

## How It Works
1. **Film Jitter Simulation**  
   Slight irregular frame-to-frame positional shifts mimic hand-held mechanical cameras.
2. **Grain Injection**  
   Dense analog-style grain overlays the footage.
3. **Contrast and Color Fading**  
   Produces warm, desaturated tones typical of 1960s film stock and old transfers.
4. **Softening & Bloom**  
   Highlights bloom slightly while edges lose digital sharpness.
5. **Encoding**  
   Output is encoded using Videobeaux global CRF, codec, and pixel-format settings.

## Program Template
```bash
videobeaux -P zapruder \
  -i input.mp4 \
  -o output.mp4
```

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
```bash
videobeaux -P zapruder \
  -i myvideo.mp4 \
  -o zapruder_styled.mp4
```

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/user-attachments/assets/cad79483-b21f-43b8-a1cd-91ed8406574a" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Medium-to-high grain source footage blends best with the effect.  
- Extremely dark footage may become muddy due to stacked film noise.  
- High-motion scenes highlight jitter and wobble most effectively.  
- Works as a final stylistic layer or early preprocessing step depending on workflow intention.

## Recommended Usage
- Fake archival footage for narrative or documentary storytelling.  
- Flashback sequences, memory montages, or historical reenactments.  
- Vintage collage art and experimental cinema.  
- Creating “lost media” textures.  
- Combining with `bad_predator`, `nostalgic_stutter`, or `lofi` effects for layered retro realism.

## Quality Tips
- Lower CRF preserves film grain more cleanly.  
- Higher CRF adds compression grit, which can enhance the degraded look.  
- Add `blur_pix` beforehand for softer, more analog edges.  
- Apply LUTs after the effect if you want to preserve the vintage tonal palette.  
- Combine with `reverse` and `speed` for scratched-film temporal irregularity.

