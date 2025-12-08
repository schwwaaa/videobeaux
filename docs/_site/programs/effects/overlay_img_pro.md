# overlay_img_pro

## Description
Overlays an external image onto the input video with explicit control over image position and dimensions.  
`overlay_img_pro` allows precise placement, scaling, and compositing of static images (PNG, JPG, etc.) on top of a video layer.

## Purpose
`overlay_img_pro` is intended for creators who want to:
- add logos, watermarks, stickers, UI elements, or graphic marks,  
- precisely place images using pixel coordinates,  
- scale images to specific dimensions for uniform branding,  
- composite image layers as part of a stylized or functional pipeline,  
- automate graphic overlays without using a traditional editor.

## How It Works
1. **Image Loading**  
   The external image defined by `--overlay_img` is loaded into the FFmpeg filtergraph.
2. **Scaling**  
   The image is resized to the dimensions specified by:
   - `img_width`  
   - `img_height`
3. **Positioning**  
   The overlay image is placed at:
   - `x_pos` (horizontal placement)  
   - `y_pos` (vertical placement)
4. **Compositing**  
   The resized and positioned image is blended over the source video.
5. **Encoding**  
   Final output is encoded using global Videobeaux codec, pixel-format, and CRF settings.

## Program Template
```bash
videobeaux -P overlay_img_pro \
  -i input.mp4 \
  -o output.mp4 \
  --overlay_img VALUE \
  --x_pos VALUE \
  --y_pos VALUE \
  --img_height VALUE \
  --img_width VALUE
```

## Arguments

- **overlay_img** — Path to the image to overlay (PNG, JPG, etc.).  
- **x_pos** — Horizontal position of the top-left corner of the overlay (in pixels).  
- **y_pos** — Vertical position of the top-left corner of the overlay (in pixels).  
- **img_height** — Height of the overlay image after scaling.  
- **img_width** — Width of the overlay image after scaling.

## Real World Example
```bash
videobeaux -P overlay_img_pro \
  -i myvideo.mp4 \
  -o overlay_img_pro_styled.mp4 \
  --overlay_img EXAMPLE \
  --x_pos EXAMPLE \
  --y_pos EXAMPLE \
  --img_height EXAMPLE \
  --img_width EXAMPLE
```

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/3932d910-b898-4ed7-ba3a-288a708c0d83" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- PNG images with alpha channels will respect transparency automatically.  
- Extremely large overlays may impact performance or produce scaling artifacts.  
- For best results, use high-resolution images when scaling down rather than up.  
- The overlay is applied top-left–anchored; centering must be done manually using math for `x_pos` / `y_pos`.  
- Works on any resolution or aspect ratio, including portrait, square, and ultrawide.

## Recommended Usage
- Watermarks, logos, and branding elements.  
- Titles or lower-third graphics generated externally.  
- UI overlays for mockups or stylized edits.  
- Layer-based collage compositions when combined with other Videobeaux programs.  
- Automated batch rendering where graphics must appear in consistent positions.

## Quality Tips
- Pre-scale the external image to your target size to avoid unnecessary interpolation.  
- Use PNG for overlays requiring clean edges or transparency.  
- Combine with `convert_dims` beforehand to ensure predictable placement on varying aspect ratios.  
- For multi-image overlays, use `lagkage` instead for complex composite pipelines.  
- Lower CRF values keep overlay edges crisp after encoding.

