# slight_smear

## Description
Applies a subtle RGB smear effect, gently shifting and bleeding color channels to create a soft distortion.  
The look resembles mild chromatic drift, analog smudge, or a barely-there color echo — perfect for adding texture without overwhelming the original image.

## Purpose
`slight_smear` is designed for creators who want:
- gentle color separation without strong glitch artifacts,  
- soft smearing suitable for dreamy or nostalgic aesthetics,  
- analog-feeling color drift reminiscent of old CRT or lens aberration,  
- a lightweight effect that enhances motion without heavy distortion,  
- a minimal, no-argument filter that always behaves consistently.

## How It Works
1. **RGB Channel Offset**  
   Red, green, and blue channels are shifted by micro-amounts, producing a soft separation.
2. **Low-Intensity Smear**  
   Instead of fully duplicating edges, the smear gently blooms color outward.
3. **Motion Enhancement**  
   Moving subjects gain soft trails, giving the impression of mild persistence.
4. **Encoding**  
   The final output is encoded using global Videobeaux CRF, codec, and pixel format.

## Program Template
```bash
videobeaux -P slight_smear \
  -i input.mp4 \
  -o output.mp4
```

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
```bash
videobeaux -P slight_smear \
  -i myvideo.mp4 \
  -o slight_smear_styled.mp4
```

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/a7bca4c5-46b5-4b51-a827-6b8137d0117d" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Because the smear is subtle, it works well even on footage with delicate details.  
- High-contrast edges reveal the effect most clearly.  
- Compression can either soften or exaggerate the smear depending on CRF.  
- Suitable as a pre-effect before heavier glitch or temporal filters.

## Recommended Usage
- Music videos needing gentle stylistic color bloom.  
- Dreamy ambience sequences and soft-focus aesthetics.  
- Collage art where slight distortion adds cohesion.  
- Retro or analog-inspired edits without heavy degradation.  
- As a smoothing layer before applying `lsd_feedback`, `crossmosh`, or `double_cup`.

## Quality Tips
- Lower CRF gives cleaner, smoother smear edges.  
- Higher CRF makes the smear grainier and more textured.  
- Combine with `gamma_fix` beforehand for more stable channel balancing.  
- Add `blur_pix` afterward for a painterly, soft-focus expansion.  
- Use `convert_dims` before smearing if resizing footage for a platform-specific format.

