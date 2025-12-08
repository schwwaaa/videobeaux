# recalled_sensor

## Description
Simulates the look of a malfunctioning digital camera sensor that is defective, failing, or subject to an official recall.  
This effect introduces corrupted rows, unstable color channels, dead-pixel clusters, exposure tearing, and chaotic image instability — mimicking catastrophic sensor failure.

## Purpose
`recalled_sensor` is designed for creators who want:
- the aesthetics of a physically damaged or overheating sensor,  
- horizontal tearing, line corruption, or rolling-shutter breakage,  
- dead-pixel patterns, color-channel misalignment, or gritty digital decay,  
- an aggressive technical-failure look appropriate for glitch, horror, sci-fi, or surveillance themes,  
- unpredictable, chaotic motion artifacts that cannot be achieved through normal grading.

## How It Works
1. **Simulated Sensor Row Failure**  
   Horizontal lines may break, misalign, repeat, or shift.
2. **Color-Channel Corruption**  
   Red, green, and blue channels may desynchronize or flicker independently.
3. **Dead Pixel Noise Injection**  
   Bright or dark pixel speckles mimic sensor element burnouts.
4. **Rolling-Shutter Breakdown**  
   Temporal distortions produce jittering horizontal bands or broken scanlines.
5. **Encoding**  
   Output is encoded using global Videobeaux settings for codec, CRF, and pixel format.

## Program Template
```bash
videobeaux -P recalled_sensor -i input.mp4 -o output.mp4
```

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
```bash
videobeaux -P recalled_sensor \
  -i myvideo.mp4 \
  -o recalled_sensor_styled.mp4
```

## Program Output
_Program output video omitted due to size; see repository for reference clips._

## Technical Notes
- High-motion scenes produce more dramatic tearing because of simulated rolling-shutter corruption.  
- Bright surfaces intensify dead-pixel bloom and channel misalignment.  
- Compression interacts strongly with corrupted scanlines — higher CRF will exaggerate the effect.  
- Because the distortion emulates hardware malfunction rather than pure software effect, the results may appear chaotic and non-repetitive.  
- Works with any resolution but is most convincing at HD or higher due to visible pixel-grid patterns.

## Recommended Usage
- Horror, sci-fi, or techno-thriller sequences involving malfunctioning equipment.  
- Glitch art and experimental cinema exploring digital decay.  
- Surveillance or found-footage aesthetics that require broken-camera realism.  
- Transitions where catastrophic failure is used as a visual punctuation.  
- Layering beneath `crossmosh` or `overexposed_stutter` for extreme destruction.

## Quality Tips
- Lower CRF if you want crisp corrupted lines; higher CRF if you prefer smearing and noise.  
- Pair with `bad_contrast` for harsher tonal collapse.  
- Combine with `lsd_feedback` or `frame_delay_pro2` to create evolving sensor meltdown effects.  
- If the clip is too bright, pre-process with `gamma_fix` to avoid overwhelming bloom in the corrupted channels.  
- For realistic malfunction aesthetics, leave the effect unchained; for surreal results, chain with other distortive modules.

