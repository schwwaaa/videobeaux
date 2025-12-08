# splitting_pro

## Description
A precise segmentation tool that slices a source video into reusable chunks based on positional slicing rules.  
`splitting_pro` allows creators to extract vertical or horizontal bands of the frame, enabling compositing, collage workflows, displacement patterns, and region-based editing.

Unlike timeline slicing tools, `splitting_pro` manipulates **spatial** slices of a single frame, carving out portions of the video image for recombination or further processing.

## Purpose
`splitting_pro` is designed for creators who want:
- spatial slicing rather than temporal cutting,  
- vertical or horizontal extraction of visual regions,  
- inputs for collage, displacement, glitch layering, or geometric composition,  
- deterministic cropping that can be repeated across clips,  
- simple region control with only two parameters.

## How It Works
1. **Define Slice Width**  
   The `width` parameter determines how large the slice is (in pixels or proportional units depending on implementation).
2. **Define Slice Position**  
   The `position` parameter determines where the slice begins — allowing sliding-window or fixed-region extraction.
3. **Spatial Cropping**  
   The module extracts that region from every frame, maintaining spatial consistency across the entire clip.
4. **Output Encoding**  
   The slice is encoded using global Videobeaux settings (codec, CRF, pixel format).

## Program Template
```bash
videobeaux -P splitting_pro \
  -i input.mp4 \
  -o output.mp4 \
  --width VALUE \
  --position VALUE
```

## Arguments

- **width** — The thickness of the slice extracted from the frame.  
- **position** — Where the slice begins relative to the frame's coordinate system.

## Real World Example
```bash
videobeaux -P splitting_pro \
  -i myvideo.mp4 \
  -o splitting_pro_styled.mp4 \
  --width EXAMPLE \
  --position EXAMPLE
```

## Program Output
_Program output video not yet linked._

## Technical Notes
- Useful for creating moving-window effects when paired with scrolling modules.  
- To extract a centered region, calculate `position` based on `(frame_size - width) / 2`.  
- Thin slices work well for displacement maps and glitch-strip compositions.  
- Slicing can be directional; depending on implementation, `width` may represent horizontal or vertical dimension.

## Recommended Usage
- Split-screen collage layouts.  
- Creating stripe-based glitch effects.  
- Feeding sliced layers into Lagkage for recombination.  
- Region extraction for stylized cropping, masks, or compositing.  
- Generating displacement textures from narrow video bands.

## Quality Tips
- Lower CRF for sharp edges on the sliced boundary.  
- Higher CRF for grittier, more distorted slices.  
- Pair with `blur_pix` for soft-edge slicing.  
- Combine with `scrolling_pro` to animate the sliced region across time.  
- Apply before LUTs for unified grading of sliced material.

