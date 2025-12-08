# resize

## Description
Resizes the dimensions of a video to a specified width and height.  
This module performs a direct scale transformation, producing clean, predictable results for platform formatting, layout prep, or visual uniformity.

## Purpose
`resize` is designed for creators who want to:
- convert videos into specific resolution targets,  
- prepare assets for social platforms (square, vertical, widescreen),  
- normalize input dimensions before compositing in Lagkage,  
- upscale or downscale footage with direct pixel precision,  
- create clean formatting pipelines without aspect-ratio tricks.

## How It Works
1. **Dimension Override**  
   The user specifies:
   - `new_width`  
   - `new_height`
2. **Scaling Filter**  
   FFmpeg’s scaler processes each frame to the requested resolution.
3. **Output Encoding**  
   The final resized image is encoded using global Videobeaux settings (CRF, codec, pixel format, preset).

## Program Template
```bash
videobeaux -P resize -i input.mp4 -o output.mp4 --new_height VALUE --new_width VALUE
```

## Arguments

- **new_height** — Target output height in pixels.  
- **new_width** — Target output width in pixels.

## Real World Example
```bash
videobeaux -P resize \
  -i myvideo.mp4 \
  -o resize_styled.mp4 \
  --new_height EXAMPLE \
  --new_width EXAMPLE
```

## Program Output
_Program output video not yet linked._

## Technical Notes
- This module **does not** enforce aspect-ratio preservation.  
- If the provided width and height do not match the original aspect ratio, the result will be stretched or squished — which may be desirable for stylized distortion.  
- For clean upscaling, combine with high-quality pixel formats (e.g., yuv444p or 10-bit formats) if your pipeline supports them.  
- Works well as a preprocessing step for LUTs, Lagkage, overlays, or dimension-specific delivery outputs.

## Recommended Usage
- Creating platform-targeted versions:  
  - 1080×1920 (reels/stories/shorts)  
  - 1080×1080 (square grid formats)  
  - 1920×1080 (landscape)  
- Normalizing assets before multi-layer compositing.  
- Preparing clips for generative art pipelines where exact sizes matter.  
- Upscaling stylized effects (e.g., painterly, glitch, smear) for high-res exports.

## Quality Tips
- For crisp results, resize **before** applying heavy effects and grading.  
- For a degraded or lo-fi look, resize **after**, which amplifies artifacts.  
- Use exact values that match your layout or platform’s requirements.  
- Pair with `convert_dims` when you want aspect-ratio intelligence; use `resize` when you want exact pixel control.  
- For upscaling beyond 2×, consider preprocessing with `gamma_fix` or `tonemap_hdr_sdr` to stabilize tonal fidelity before scaling.

