# twociz

## Description
Applies a distorted, delirious visual effect meant to simulate the hallucinated perspective of a zombie under the fictional TC-1 compound.  
The aesthetic is disoriented, chemically corrupted, semi-conscious, and grotesquely vivid — combining abnormal color shifts, lurching motion, and sensory confusion.

## Purpose
`twociz` is designed for creators who want:
- a surreal, undead, chemically warped visual tone,  
- heavily altered perception aesthetics (swaying, drifting, disoriented),  
- toxic, bruised, unnatural color bleed,  
- a cinematic “drug-trip-from-the-grave” interpretation,  
- a one-command surreal filter requiring no tweaking.

## How It Works
1. **Toxic Color Distortion**  
   Colors skew toward bruised greens, rotting purples, and necrotic yellows — evoking a zombified visual palette.
2. **Hallucinogenic Drift**  
   Subtle geometric warping, temporal wobble, or disproportionate scaling may occur to mimic unstable perception.
3. **Consciousness Fade Simulation**  
   Highlights bloom erratically; shadows collapse unexpectedly, resembling moments of slipping awareness.
4. **Encoding**  
   Output is encoded using global Videobeaux codec settings (CRF, pixel format, preset).

## Program Template
```bash
videobeaux -P twociz \
  -i input.mp4 \
  -o output.mp4
```

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
```bash
videobeaux -P twociz \
  -i myvideo.mp4 \
  -o twociz_styled.mp4
```

## Program Output
_Program output video omitted due to size; see repository for reference clips._

## Technical Notes
- Works extremely well on footage with faces or skin tones, which become grotesquely reinterpreted under the effect.  
- High-contrast movement exaggerates the chemical hallucination look.  
- Compression artifacts interact unpredictably with the warped palette — often desirable for this aesthetic.  
- Stability varies depending on input content: calm scenes look feverish; chaotic scenes look apocalyptic.

## Recommended Usage
- Horror or undead-themed sequences.  
- Music videos requiring surreal, lurching, toxic hallucinations.  
- Psychological visualizations of decay, delirium, intoxication, or inner collapse.  
- Glitch-art or experimental montage with a corrupted-organic tone.  
- Any sequence where a “rotting consciousness POV” enhances storytelling.

## Quality Tips
- Lower CRF yields clearer hallucination layers; higher CRF introduces gritty decay that suits the undead theme.  
- Pair with `septic` for medical-shock surrealism.  
- Combine with `bad_contrast` for a bruised, collapsing palette.  
- Layer with `lsd_feedback` for intensifying delirium loops.  
- Apply before `overexposed_stutter` for a chemically panicked final effect.

