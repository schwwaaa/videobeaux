# splitting

## Description
A simple segmentation utility that divides a video into evenly timed chunks or scene-based fragments for modular editing.  
Unlike `splitting_pro`, which slices **spatial** regions of the frame, `splitting` operates purely in the **time domain**, cutting the clip into temporal sections that can be reused, rearranged, or processed individually.

## Purpose
`splitting` is designed for creators who want:
- evenly sized time slices for procedural editing,  
- modular clip fragments for collage or Lagkage workflows,  
- timed intervals for repeatable pattern-based assembly,  
- simple temporal segmentation with no configuration,  
- consistent chunking for downstream effects or batch operations.

## How It Works
1. **Temporal Chunking**  
   The video is divided into equal-length sections or scene-based fragments depending on internal logic.
2. **Frame-Accurate Slicing**  
   Cuts occur at precise timestamps, ensuring reliable recomposition.
3. **Independent Segment Handling**  
   Segments may be saved, recombined, or used as modular inputs for further editing steps.
4. **Encoding**  
   Output is assembled and encoded using global Videobeaux settings.

## Program Template
```bash
videobeaux -P splitting \
  -i input.mp4 \
  -o output.mp4
```

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
```bash
videobeaux -P splitting \
  -i myvideo.mp4 \
  -o splitting_styled.mp4
```

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/user-attachments/assets/b6c13707-aaa8-416e-9f80-5ca6a386cd0f" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Ideal for building modular editing systems where each temporal block is reused.  
- Works cleanly regardless of resolution, codec, or aspect ratio.  
- Output chunk boundaries depend on internal segmentation logic; exact block timing may vary by implementation.  
- Can be paired with normalization tools if segments will be concatenated later.

## Recommended Usage
- Procedural editing pipelines.  
- Video collage systems that reassemble timelines randomly.  
- Creating modular “building blocks” for generative video art.  
- Preparing assets for Lagkage layouts or multi-layer structures.  
- Segmenting long recordings into manageable sections for stylized processing.

## Quality Tips
- Use lower CRF if you intend to recombine slices later to avoid generational loss.  
- For glitch workflows, higher CRF can introduce desirable texture into cut boundaries.  
- Apply `convert_dims` first if you want uniformity across all segments.  
- Combine with `reverse`, `speed`, or `nostalgic_stutter` to add temporal variation to each slice.  
- Pre-trim your source before splitting to ensure perfect timing alignment.

