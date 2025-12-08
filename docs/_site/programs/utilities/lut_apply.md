# lut_apply

## Description
Applies a 1D or 3D LUT to recolor a video, enabling film-style grading, color transforms, technical conversions, or creative look development.

## Purpose
`lut_apply` integrates LUT-based color grading into Videobeaux pipelines.  
It is useful for:
- applying film emulation looks,
- technical color transforms (LOG → REC.709),
- stylized grades for creative pieces,
- batch processing LUT workflows,
- previewing looks before finishing in a grading suite.

## How It Works
1. **LUT Loading**  
   Loads a `.cube`, `.3dl`, or other LUT file defined by the `lut` parameter.
2. **Interpolation**  
   Chooses how input colors interpolate through the 3D LUT grid (`interp`).
3. **Intensity Blending**  
   `intensity` controls the LUT’s strength—useful for subtle looks or partial grading mixes.
4. **Image Corrections**  
   Optional adjustments for:
   - `brightness`  
   - `contrast`  
   - `saturation`  
   - `gamma`  
   These adjustments apply before or after LUT evaluation depending on implementation.
5. **Output Encoding**  
   Output is encoded with provided pixel format, CRF, preset, and optional audio copy.

## Program Template
    videobeaux -P lut_apply \
      -i input.mp4 \
      -o output.mp4 \
      --outfile VALUE \
      --vcodec VALUE \
      --lut VALUE \
      --interp VALUE \
      --intensity VALUE \
      --brightness VALUE \
      --contrast VALUE \
      --saturation VALUE \
      --gamma VALUE \
      --pix_fmt VALUE \
      --x264_preset VALUE \
      --crf VALUE \
      --copy_audio VALUE

## Arguments

- **outfile** — Output file name for the rendered, LUT-applied video.  
- **vcodec** — Video codec to use (e.g., `libx264`, `libx265`, `prores_ks`).  
- **lut** — Path to the LUT file (.cube, .3dl, etc.).  
- **interp** — LUT interpolation mode (`nearest`, `trilinear`, or other supported methods).  
- **intensity** — Blending amount between original image and LUT-graded image (0.0–1.0).  
- **brightness** — Brightness correction applied pre/post LUT.  
- **contrast** — Contrast adjustment applied in grading pipeline.  
- **saturation** — Saturation control for color richness.  
- **gamma** — Gamma correction applied for tonal shaping.  
- **pix_fmt** — Pixel format (e.g., `yuv420p`, `yuv422p10le`, `rgb24`).  
- **x264_preset** — Encoding speed vs compression preset for libx264.  
- **crf** — Constant Rate Factor controlling output quality.  
- **copy_audio** — Copies audio from source without re-encoding when enabled.

## Real World Example
    videobeaux -P lut_apply \
      -i myvideo.mp4 \
      -o lut_apply_styled.mp4 \
      --outfile EXAMPLE \
      --vcodec EXAMPLE \
      --lut EXAMPLE \
      --interp EXAMPLE \
      --intensity EXAMPLE \
      --brightness EXAMPLE \
      --contrast EXAMPLE \
      --saturation EXAMPLE \
      --gamma EXAMPLE \
      --pix_fmt EXAMPLE \
      --x264_preset EXAMPLE \
      --crf EXAMPLE \
      --copy_audio EXAMPLE

## Technical Notes
- LUTs created for LOG footage require matching input color space before use.  
- Interpolation type affects smoothness—`trilinear` is typically best for high-quality grading.  
- Gamma adjustments can shift midtone density; use subtly for filmic shaping.  
- Blending via `intensity` is ideal for creative fades or adjustable look-dev.  
- Some LUTs clip out-of-gamut colors; test with challenging footage.

## Recommended Usage
- Film emulation workflows and creative looks.  
- Technical transforms (camera LOG → REC.709).  
- Batch applying LUTs for directories of dailies or reference renders.  
- Experimenting with looks before importing into grading applications.

## Quality Tips
- For cinematic grading, keep `intensity` around **0.6–0.85** for balanced results.  
- Always preview LUTs with a variety of footage—some LUTs are extremely contrast-heavy.  
- When color banding appears, switch to a 10-bit pixel format like `yuv422p10le`.  
- Use lower CRF values (14–18) for grading-quality output.  
- Avoid stacking extreme brightness, saturation, and LUT intensity simultaneously to reduce clipping.
