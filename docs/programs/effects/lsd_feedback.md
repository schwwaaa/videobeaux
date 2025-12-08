# lsd_feedback

## Description
Applies a psychedelic recursive feedback effect inspired by analog video feedback loops and LSD-style visual hallucination.  
The effect blends delayed frames into the live frame stream, producing spiraling trails, melting motion, neon echoes, and evolving kaleidoscopic distortions.

## Purpose
`lsd_feedback` is designed for creators who want to:
- introduce trippy, hallucinogenic motion smearing,  
- simulate analog CRT feedback loops,  
- create spirals, streaks, or self-replicating visual echoes,  
- build evolving feedback tunnels reminiscent of VHS/CRT experiments,  
- produce psychedelic or surreal video art without patching hardware feedback systems.

## How It Works
1. **Frame Recursion**  
   A portion of each delayed frame is reinjected back into the live image, similar to pointing a camera at a monitor.
2. **Temporal Drift**  
   Past frames influence future frames with increasing distortion as the effect accumulates.
3. **Color Expansion**  
   Depending on implementation, colors may bloom or smear into neon gradients.
4. **Motion Hallucination**  
   The viewer perceives warped, melting, or pulsating motion as feedback compounds over time.
5. **Encoding**  
   Output is written using global Videobeaux settings (codec, pixel format, CRF).

## Program Template
```bash
videobeaux -P lsd_feedback -i input.mp4 -o output.mp4
```

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
```bash
videobeaux -P lsd_feedback \
  -i myvideo.mp4 \
  -o lsd_feedback_styled.mp4
```

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/9653929c-30ad-4c72-81c8-e3777c590783" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Feedback strength increases over time, making long clips more intense than short ones.  
- Works especially well with neon lighting, strong edges, and symmetrical compositions.  
- Compression interacts with feedback recursion — higher CRF values may create chaotic noise patterns.  
- Because feedback accumulates, even subtle parameter changes (in underlying implementation) can produce drastically different visuals.

## Recommended Usage
- Psychedelic music videos, rave visuals, and festival projections.  
- VJ loops with evolving feedback tunnels.  
- Experimental films exploring self-referential distortion.  
- Visualizers for ambient, drone, or improvisational electronic music.  
- Motion graphics sequences requiring surreal deformation.

## Quality Tips
- For smoother feedback gradients, use lower CRF (higher quality).  
- For chaotic glitch spirals, render at higher CRF or degrade using `bad_contrast` afterward.  
- Combine with `frame_delay_pro1` or `frame_delay_pro2` to produce layered temporal echoes.  
- Pre-process with `convert_dims` to square formats (e.g., 1080×1080) for symmetrical feedback structures.  
- Pair with `double_cup` or `ghostee` for dreamlike, syrupy hallucination trails.

