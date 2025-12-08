# nostalgic_stutter

## Description
Applies a retro, analog-inspired frame-stutter effect reminiscent of corrupted home movies, aging videotape playback, or dropped-frame digital artifacts.  
`nostalgic_stutter` intentionally disrupts cadence to evoke glitchy playback, uneven frame advancement, or mechanical jitter from vintage camcorders.

## Purpose
`nostalgic_stutter` is designed for creators who want to:
- recreate the feel of deteriorating VHS or Hi8 footage,  
- add jittery temporal artifacts to modern footage,  
- evoke “memory footage” aesthetics,  
- simulate dropped frames or unstable playback,  
- build nostalgic glitch energy into cuts, transitions, or loops.

## How It Works
1. **Cadence Disruption**  
   The module duplicates, skips, or replays frames to break smooth motion.
2. **Irregular Frame Rhythm**  
   The visual tempo becomes unpredictable, simulating:
   - dropped frames,  
   - slight temporal hiccups,  
   - uneven tape playback.
3. **Analog Wear Simulation**  
   Visual timing irregularities mimic mechanical imperfections in older recording hardware.
4. **Encoding**  
   Output is written using global Videobeaux codec and quality settings.

## Program Template
```bash
videobeaux -P nostalgic_stutter \
  -i input.mp4 \
  -o output.mp4
```

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
```bash
videobeaux -P nostalgic_stutter \
  -i myvideo.mp4 \
  -o nostalgic_stutter_styled.mp4
```

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/3cef37d9-093f-4bd9-850c-4b163e8a3e01" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Best applied to footage with visible movement; minimal motion yields minimal stutter effect.  
- Compression artifacts may amplify the “retro glitch” feeling, especially at higher CRF.  
- Sequences with panning, walking, or motion across diagonals exhibit the strongest nostalgic distortions.  
- Works consistently at any resolution; scaling before or after does not break the effect.

## Recommended Usage
- Vintage-style edits or memory sequences.  
- Music videos needing lo-fi temporal distortion.  
- Glitch-montage transitions and staccato cuts.  
- Found-footage aesthetics, home-video recreations, or archival simulation.  
- Social-media loops aiming for an intentionally imperfect vibe.

## Quality Tips
- Lower CRF retains clarity while still allowing stutter artifacts to read cleanly.  
- Higher CRF adds noise that can enhance the “old tape” feel.  
- Combine with `bad_contrast` or `double_cup` for stylized aging or dreamy deterioration.  
- For heavier cadence destruction, stack with `bad_animation` or `frame_delay_pro1`.  
- Use `convert_dims` beforehand if building platform-specific loops (square, reels, stories).