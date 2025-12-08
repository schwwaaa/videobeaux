# stutter_pro

## Description
Applies a customizable frame-stutter effect where playback cadence is intentionally disrupted according to a user-defined stutter intensity.  
`stutter_pro` offers far more control than the simpler `nostalgic_stutter` or `overexposed_stutter` modules, allowing the editor to tune how aggressively the timeline “hiccups.”

## Purpose
`stutter_pro` is designed for creators who want:
- precise and adjustable frame stuttering,  
- rhythmic or tempo-based visual cadence disruption,  
- glitch-style jitter that can be subtle or extreme,  
- stylized motion breakdowns for music videos or experimental edits,  
- deterministic stutter behavior tied to a single argument.

## How It Works
1. **Frame Retention / Skipping**  
   Based on the `stutter` value, certain frames are duplicated or dropped.
2. **Pattern Generation**  
   The effect may repeat, hold, or jitter frames depending on stutter intensity.
3. **Temporal Distortion**  
   Motion becomes erratic, producing:
   - choppy sequences,  
   - step-motion effects,  
   - rhythmic pulse-style stutters.

4. **Encoding**  
   Output is encoded using Videobeaux global codec, pixel format, and CRF settings.

## Program Template
```bash
videobeaux -P stutter_pro \
  -i input.mp4 \
  -o output.mp4 \
  --stutter VALUE
```

## Arguments

- **stutter** — Controls the intensity of the effect.  
  Higher values produce more extreme frame skipping / duplication.

## Real World Example
```bash
videobeaux -P stutter_pro \
  -i myvideo.mp4 \
  -o stutter_pro_styled.mp4 \
  --stutter EXAMPLE
```

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/03e234fb-d0fe-4d72-a11c-dff1bc59fa83" type="video/mp4">
  Your browser does not support the video tag.
</video>

<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/e6d8c14a-9f20-4365-bb1f-5f473289a855" type="video/mp4">
  Your browser does not support the video tag.
</video>

<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/864835ba-dc9d-4392-aa77-2cc062e2b700" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- High stutter values can dramatically change perceived rhythm and pacing.  
- Ideal for matching beat-synchronized edits by dialing stutter to musical subdivisions.  
- Heavy stuttering may result in harsh judder depending on the source frame rate.  
- Works well when paired with effects that react to cadence disruption, like `lsd_feedback`.

## Recommended Usage
- Music videos requiring beat-sync visual pulses.  
- Experimental collage sequences with mechanical or robotic movement.  
- Hyper-stylized glitch breakdowns.  
- Rapid-cut montage moments needing added temporal chaos.  
- Loop creation when combined with `reverse` or `looper_pro`.

## Quality Tips
- Lower CRF retains crisp edges through stutter jumps.  
- Slight blur (`blur_pix`) can soften the harshness for dreamy styles.  
- Combine with `overexposed_stutter` for chaotic shockwave motion.  
- Use `speed` together with stutter to build complex rhythmic motion systems.  
- Preprocess with `frame_interpolate` if you want smoother slow-motion stutter artifacts.

