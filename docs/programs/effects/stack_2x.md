# stack_2x

## Description
Stacks two videos **vertically** (one on top of the other) while preserving the original orientation and aspect ratio of each source.  
This module creates a clean two-layer composite, useful for comparison videos, collage work, diptychs, and multi-view layouts.

## Purpose
`stack_2x` is designed for creators who want:
- a simple vertical two-video layout,  
- a clean and deterministic stacking tool with minimal configuration,  
- a fast way to create split-screen or comparison visuals,  
- diptych or layered collage structures,  
- multi-camera or multi-source presentations.

## How It Works
1. **Load Primary Input**  
   The global input (`-i input.mp4`) forms the top (or first) layer.
2. **Load Secondary Input**  
   The `--input2` path loads the second video, which becomes the bottom layer.
3. **Vertical Stacking**  
   The two frames are aligned vertically using FFmpeg’s stacking filters.  
   No rotation, flipping, or aspect correction is applied unless done elsewhere in the chain.
4. **Encoding**  
   The resulting double-height composite is encoded using the global Videobeaux settings (CRF, codec, pixel format).

## Program Template
```bash
videobeaux -P stack_2x \
  -i input.mp4 \
  -o output.mp4 \
  --input2 VALUE
```

## Arguments

- **input2** — Path to the second video file to place beneath the primary input.
- **duration** — Which video sets the length of the output: `Longest` (default; the shorter one holds its last frame), `Top video`, or `Bottom video` (the output stops when that video stops, and the other is cut to match).
- **audio** — Which sound is kept: `Top video`, `Bottom video`, `Mix both` (the two played together at equal level), or `Silent`.
- **fit** — How the bottom video is fitted to the top one's width: keep the whole picture with bars, fill and crop, or stretch.
- **gap** — Black gap between the two videos, in pixels.

**Speed:** the encode is the slow part. A large top video makes a tall, large output: a 4K 60 fps top clip plus a 720p bottom ran at about 0.7× realtime on a test Mac, while 1080p and 720p ran at 4–5×.

## Real World Example
```bash
videobeaux -P stack_2x \
  -i myvideo.mp4 \
  -o stack_2x_styled.mp4 \
  --input2 EXAMPLE
```

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/6f244aba-e741-46c9-9863-7fc43527a8d6" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Both videos should ideally share the same width; otherwise, FFmpeg will auto-scale or pad depending on filter rules.  
- Stacked output height = sum of both video heights.  
- Audio is typically taken from the primary input unless modified elsewhere in the pipeline.  
- Works well in workflows where temporal sync matters (side-by-side camera takes, A/B comparison, performance studies).  
- For mismatched aspect ratios, consider preprocessing via `convert_dims` or `resize`.

## Recommended Usage
- A/B comparison videos.  
- Performance or rehearsal footage with two simultaneous takes.  
- Collage art that arranges multiple perspectives vertically.  
- Multi-layer stacks inside Lagkage.  
- Vertical diptych compositions for experimental film or social formats.

## Quality Tips
- The cleaner the scaling match between the two videos, the sharper the final composite.  
- Use lower CRF for crisp splits with sharp geometry.  
- To harmonize color or lighting between the two clips, apply grading (`lut_apply`, `gamma_fix`) before stacking.  
- Combine with `stack_3x` or other stacking modules for multi-row layouts.  
- Use `resize` to unify widths before stacking for the most predictable results.

