# ball_point_pen

## Description
Applies a ball-point-pen illustration effect to the input video, simulating hand-drawn line textures, monochrome ink shading, and stylized pen-stroke contrast.  
The result evokes sketchbook drawings, technical notebook diagrams, or lo-fi comic-style renderings.

## Purpose
`ball_point_pen` is intended for artists who want to:
- transform footage into a drawn, pen-sketched look,  
- reduce photographic realism while retaining motion,  
- create stylized rotoscope-like results,  
- mimic ink illustrations or doodle-style animation,  
- apply a minimalistic or DIY illustration aesthetic.

## How It Works
1. **Edge Extraction**  
   The effect identifies major contours and turns them into pen-like strokes.
2. **Ink Shading Simulation**  
   Midtones and shadows are reinterpreted as sparse or dense ink hatching.
3. **Monochrome / Limited Palette Rendering**  
   The image is reduced to a pen-like tonal range, often high-contrast and desaturated.
4. **Encoding**  
   The processed frames are written using global Videobeaux output settings (codec, CRF, pixel format).

## Program Template
    videobeaux -P ball_point_pen \
      -i input.mp4 \
      -o output.mp4

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
    videobeaux -P ball_point_pen \
      -i myvideo.mp4 \
      -o ball_point_pen_styled.mp4

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/user-attachments/assets/10e703a5-5036-4c3e-83f6-be04476ad089" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- The final aesthetic depends on global pixel format and compression parameters.  
- Works especially well on footage with strong edges, clean lighting, or high motion.  
- Since the process reduces tonal detail, compression artifacts may become more noticeable — sometimes adding to the hand-drawn look.  
- Best results may come from source footage with minimal noise.

## Recommended Usage
- Rotoscope-style animation sequences.  
- Comic-inspired music videos or narrative interludes.  
- Experimental art filtering where realism is intentionally minimized.  
- Educational or technical visualization with a “diagram” aesthetic.  
- Mixed-media projects combining live-action with hand-drawn elements.

## Quality Tips
- Consider pairing with `convert_dims` (square formats like 1080×1080) for Instagram-style sketch loops.  
- Use a lower CRF (higher quality) to preserve line fidelity.  
- Pair with `gamma_fix` or `lut_apply` before applying the pen effect for clearer edges.  
- Apply final sharpening or embossing in a later step if you want more aggressive pen stroke definition.  
- Rotoscoped motion reads best when frame rate is preserved — avoid additional frame dropping unless stylistically intentional.
