# septic

## Description
Applies an intense, distressed visual filter inspired by the physiological collapse associated with septic shock.  
The effect evokes instability, discoloration, plunging contrast, erratic tonal shifts, and an overall sense of visual “failing systems.”

This is a highly stylized effect — not medically literal — meant to express emotional, cinematic, or abstract interpretations of systemic breakdown.

## Purpose
`septic` is designed for creators who want:
- a dramatic “body shutting down” visual metaphor,  
- sickly color shifts, muddied gradients, and collapsing tonal structure,  
- unstable fluctuations reminiscent of fading consciousness or shock waves,  
- aggressive, unsettling distortions appropriate for horror, glitch, or psychological edits,  
- a simple one-command filter with no parameters to tune.

## How It Works
1. **Color Degradation**  
   The filter pushes hues toward bruised greens, greys, and yellows — evoking the palette of medical distress.
2. **Contrast Collapse**  
   Highlights and shadows may buckle inward, causing the image to dim, lose clarity, or appear “fading out.”
3. **Instability Simulation**  
   Subtle flicker, tonal oscillation, or jitter may appear to represent instability and bodily failure.
4. **Encoding**  
   Output is encoded using global Videobeaux settings, ensuring consistent quality across pipelines.

## Program Template
```bash
videobeaux -P septic -i input.mp4 -o output.mp4
```

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
```bash
videobeaux -P septic \
  -i myvideo.mp4 \
  -o septic_styled.mp4
```

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/user-attachments/assets/25f65267-60fa-421a-aaf3-02918844a488" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Midtones become heavily stressed; this is where the “shock” look is strongest.  
- Faces and skin tones distort dramatically, increasing the unsettling aesthetic.  
- High-contrast footage produces more severe tonal collapse.  
- Works equally well on clean digital footage and degraded sources.

## Recommended Usage
- Horror sequences and psychological thrillers.  
- Music videos with themes of collapse, breakdown, or emotional overload.  
- Glitch-art or experimental montage.  
- Narrative moments symbolizing fear, trauma, disorientation, or medical crisis.  
- Visual metaphors for systems failure in abstract cinema.

## Quality Tips
- Use lower CRF to maintain detail in distressed textures.  
- Use higher CRF if you want smeared, grimy collapse artifacts.  
- Combine with `bad_contrast` for deeper shadows and harsher tonal decay.  
- Stack with `overexposed_stutter` for panic-attack visual rhythms.  
- Apply before `lut_apply` if you want a uniform sickly wash; apply after if you want the LUT to warp the septic palette.

