# mirror_delay

## Description
Applies a mirrored frame-delay effect, blending temporal echoes with reflective symmetry.  
The result combines soft motion trailing with a mirrored duplication of the frame, creating hypnotic, kaleidoscopic, or hall-of-mirrors–style distortion.

## Purpose
`mirror_delay` is ideal for artists who want:
- reflective, symmetrical echo patterns,  
- hypnotic mirrored smearing,  
- abstract duplication of movement,  
- dreamy motion persistence combined with geometric balance,  
- a lightweight but visually striking temporal effect.

## How It Works
1. **Frame Delay**  
   Internal buffering creates a trailing echo that blends previous frames into the current one.
2. **Geometric Mirroring**  
   The image is mirrored horizontally, vertically, or both (depending on implementation), creating:
   - bilateral symmetry,  
   - twin-image structures,  
   - kaleidoscopic reflections.
3. **Temporal + Spatial Fusion**  
   The mirrored image and the delayed frame blend together, producing surreal flowing reflections.
4. **Encoding**  
   The final composite is encoded with global Videobeaux settings (CRF, codec, pixel format).

## Program Template
```bash
videobeaux -P mirror_delay \
  -i input.mp4 \
  -o output.mp4
```

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
```bash
videobeaux -P mirror_delay \
  -i myvideo.mp4 \
  -o mirror_delay_styled.mp4
```

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/a3dea5c6-03a6-4f65-951d-211f50457b63" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Works well with centered subjects or footage containing strong motion vectors.  
- Mirroring combined with delay often creates geometric rhythm or pulse-like visual structure.  
- Compression artifacts can become symmetrical as well, adding to the aesthetic.  
- Bright edges and neon lights produce the most pronounced mirror-delay trails.

## Recommended Usage
- Music videos with mirrored choreography or symmetrical staging.  
- Psychedelic pieces needing a dreamlike reflective effect.  
- Ambient loops and visualizations requiring geometric repetition.  
- Projection-mapping and VJ sets where mirrored imagery reacts well to space.  
- Combining with `frame_delay_pro1` or `lsd_feedback` for layered temporal abstraction.

## Quality Tips
- For smoother trails, lower CRF (higher quality).  
- For glitchier mirrored buildup, render with a higher CRF.  
- Pair with `convert_dims` to square or portrait layouts for perfect symmetry.  
- Combine with `ghostee` for soft spectral reflection trails.  
- Run *before* a LUT (`lut_apply`) if you want the color grade to affect both halves identically.

