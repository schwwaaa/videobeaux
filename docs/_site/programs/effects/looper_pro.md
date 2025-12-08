# looper_pro

## Description
Creates a professional looping effect by selecting a region of frames and replaying them in a seamless or stylized loop.  
`looper_pro` allows the user to choose which part of a video becomes a loop, enabling rhythmic repetition, GIF-like behavior, or precisely timed visual cycles.

## Purpose
`looper_pro` is intended for creators who want to:
- loop a specific segment of a clip cleanly,  
- create infinitely repeating video moments,  
- build rhythmic or hypnotic playback sequences,  
- generate raw loop assets for VJ systems or social loops,  
- prepare seamless animations for montage or collage workflows.

## How It Works
1. **Frame Region Selection**  
   Internally selects frames based on:
   - detected cadence,  
   - frame count,  
   - optional start and end logic defined by the program version.
2. **Loop Construction**  
   The selected block is repeated a specified number of cycles or for the full video duration.
3. **Seam Handling**  
   Basic smoothing or overlap blending may be used to reduce visible jumps at the start/end of each loop (implementation dependent).
4. **Encoding**  
   Output uses global Videobeaux settings (codec, CRF, pixel format, preset).

## Program Template
```bash
videobeaux -P looper_pro \
  -i input.mp4 \
  -o output.mp4
```

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
```bash
videobeaux -P looper_pro \
  -i myvideo.mp4 \
  -o looper_pro_styled.mp4
```

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/01090d49-8626-4fc0-b55c-807d100a78fa" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Works best when source footage includes repeating or rhythmic motion.  
- Compression artifacts may accumulate across loop boundaries; use lower CRF if loop clarity is important.  
- Shorter loops feel more “GIF-like,” while longer loops create subtle ambient motion ideal for installations.  
- Loop start point may be governed by internal heuristics or user version behavior.

## Recommended Usage
- Ambient loops for projection mapping or VJ sets.  
- Social-media loops where infinitely repeating visuals are desirable.  
- Narrative interludes or transitions requiring rhythmic repetition.  
- Motion-design elements for collage compositions or layered Lagkage outputs.

## Quality Tips
- Pre-process with `convert_dims` for perfectly square or vertical loop assets.  
- Use `gamma_fix` beforehand to stabilize tonal values across loop boundaries.  
- Pair with `double_cup` or `ghostee` for dreamy, flowing loop aesthetics.  
- For a more extreme perturbation, run `looper_pro` before `crossmosh` or `bad_animation` to break the loop structure artistically.

