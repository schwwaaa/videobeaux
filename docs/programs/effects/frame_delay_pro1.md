# frame_delay_pro1

## Description
Applies an advanced frame-delay effect using a customizable number of delayed frames and weighted blending.  
This produces echoing motion trails, temporal smearing, ghosted motion artifacts, and stylized feedback-like delay effects.

## Purpose
`frame_delay_pro1` is designed for creators who want:
- multi-frame echo trails,  
- weighted motion smears,  
- ghosting and afterimage effects,  
- rhythmic temporal pulses,  
- experimental or abstract motion distortion.

## How It Works
1. **Frame Buffering**  
   A buffer of past frames is maintained according to `frame_quantity`.
2. **Weighted Blending**  
   `frame_weights` determines how strongly each delayed frame contributes to the output.  
   - Higher weights = stronger visibility  
   - Lower weights = subtle fading trails
3. **Temporal Synthesis**  
   The module blends the weighted frames to create:
   - motion smears  
   - streaking  
   - ghost trails  
   - rhythmic pulses resembling analog video feedback
4. **Encoding**  
   Output is written using global Videobeaux settings (codec, CRF, pixel format).

## Program Template
    videobeaux -P frame_delay_pro1 \
      -i input.mp4 \
      -o output.mp4 \
      --frame_quantity VALUE \
      --frame_weights VALUE

## Arguments

- **frame_quantity** — Number of delayed frames to include in the temporal buffer. Larger values produce longer trails or more complex smears.  
- **frame_weights** — Comma-separated list of blend weights (e.g., `1,0.8,0.5,0.2`).  
  The number of weights should match `frame_quantity`, and values determine the intensity of each delay layer.

## Real World Example
    videobeaux -P frame_delay_pro1 \
      -i myvideo.mp4 \
      -o frame_delay_pro1_styled.mp4 \
      --frame_quantity EXAMPLE \
      --frame_weights EXAMPLE

## Program Output

<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/871ccdb9-ae2b-46e1-8b0f-0514eb92e1aa" type="video/mp4">
  Your browser does not support the video tag.
</video>

<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/0a727474-25cf-42ab-a717-583e12b4a04d" type="video/mp4">
  Your browser does not support the video tag.
</video>

<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/5ab60f24-b4e2-4e0e-abc0-cfab62e09cda" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Weight values can exceed 1.0 for extreme ghosting or bloom-like smearing.  
- Uneven or irregular weight lists produce unpredictable but interesting temporal textures.  
- Using very high `frame_quantity` may increase render time depending on resolution and codec.  
- Works exceptionally well on footage with fast motion, strobing lights, or repetitive movement patterns.

## Recommended Usage
- Music video trails and rhythmic pulse effects.  
- Rotoscoped animations requiring smeared or echoed movement.  
- Live VJ feedback systems and performance visuals.  
- Psychedelic edits and temporal collage art.  
- Slow-motion sequences where motion trails add emotional or surreal tone.

## Quality Tips
- Normalize weights so the sum stays below ~2.0 if you want clean blending without clipping.  
- Use descending weights (e.g., `1,0.8,0.6,0.4`) for smooth decays.  
- Use chaotic weights (e.g., `1,0,1,0.2`) for glitchy motion inconsistencies.  
- Combine with `double_cup` or `bad_animation` for hallucination-like layered visuals.  
- Pair with a clean source and low CRF to preserve subtle trail gradations.
