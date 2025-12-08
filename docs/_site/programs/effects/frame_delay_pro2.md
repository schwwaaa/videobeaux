# frame_delay_pro2

## Description
Applies an advanced analytical frame-delay effect that shifts image planes (luma/chroma) independently while applying temporal decay.  
This creates ghost trails, chromatic drifts, smeared movement, and layered motion persistence that evolves across time.

## Purpose
`frame_delay_pro2` is for creators seeking:
- stylized multi-layer temporal drift,  
- independent per-plane delay effects,  
- psychedelic color smearing,  
- glitchy ghost-motion artifacts,  
- experimental video feedback behaviors.

## How It Works
1. **Plane Selection (`--plane`)**  
   The effect can target:
   - luma only,  
   - chroma channels only,  
   - or all combined planes depending on implementation.
2. **Temporal Decay (`--decay`)**  
   The decay parameter controls how strongly old frames persist:
   - Higher decay → longer, more persistent trails  
   - Lower decay → quick falloff and lighter ghosting
3. **Frame Buffering**  
   Past frames are stored and blended forward according to decay rules.
4. **Encoding**  
   Final output is encoded via global Videobeaux settings (codec, CRF, pixel format).

## Program Template
    videobeaux -P frame_delay_pro2 \
      -i input.mp4 \
      -o output.mp4 \
      --decay VALUE \
      --plane VALUE

## Arguments

- **decay** — Controls the strength and longevity of the delay trail. Higher values produce smearier, more persistent echoes.  
- **plane** — Defines which image plane(s) the delay is applied to (e.g., `luma`, `chroma`, or combined modes depending on implementation).

## Real World Example
    videobeaux -P frame_delay_pro2 \
      -i myvideo.mp4 \
      -o frame_delay_pro2_styled.mp4 \
      --decay EXAMPLE \
      --plane EXAMPLE

## Program Output

<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/a88284bc-ca7e-4355-8f95-377434c61d13" type="video/mp4">
  Your browser does not support the video tag.
</video>

<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/acf571e7-7162-413f-80f8-769815093267" type="video/mp4">
  Your browser does not support the video tag.
</video>

<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/f717d419-687b-4cc3-ac07-64f45c763531" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Applying delay to **chroma only** creates psychedelic color trails while keeping shapes sharp.  
- Applying delay to **luma** creates ghost silhouettes without heavy color bleeding.  
- Large decay values can produce painterly smear effects resembling long-exposure photography.  
- Interaction with compression can intensify chromatic distortion.  
- Works well with footage involving movement, light streaks, neon scenes, or high-contrast subjects.

## Recommended Usage
- Music videos needing rhythmic or drifting trail effects.  
- Abstract animations or temporal collage art.  
- Footage where separating luma and chroma drift enhances surrealism.  
- Layered VJ compositions and live performance visuals.  
- Slow, ambient sequences that benefit from temporal echo.

## Quality Tips
- For strong color-drift effects, use `plane=chroma` with moderate decay.  
- For ghost silhouettes, use `plane=luma` with high decay.  
- For clean results, keep CRF low; for gritty smear artifacts, use higher CRF.  
- Combine with `frame_delay_pro1` for multi-layer delay stacks.  
- Chain before heavy color grading if you want grading to affect the echoed trails.

