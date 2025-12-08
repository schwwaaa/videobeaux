# scrolling_pro
:contentReference[oaicite:1]{index=1}

## Description
Applies a continuous scrolling effect to the video, allowing the image to move horizontally, vertically, or in both directions simultaneously.  
This module is ideal for generating drifting motion, conveyor-like movement, kinetic wallpaper loops, and directional flow effects.

## Purpose
`scrolling_pro` is designed for creators who want:
- seamless directional movement for loops or backgrounds,  
- kinetic motion overlays in collage or compositing workflows,  
- horizontal, vertical, or diagonal drifting of footage,  
- a simple way to generate infinite-scroll–style visuals,  
- controllable speed for gentle drift or aggressive motion.

## How It Works
1. **Coordinate Translation**  
   Each frame is shifted on the X and/or Y axis according to the defined scroll speeds.
2. **Continuous Wraparound**  
   As the image scrolls, pixels exiting one side re-enter from the opposite side, creating an infinite looping illusion.
3. **Directional Combination**  
   Horizontal and vertical speeds can be combined, creating diagonal or complex drift patterns.
4. **Encoding**  
   Output is then encoded using Videobeaux global settings (codec, CRF, pixel format).

## Program Template
```bash
videobeaux -P scrolling_pro \
  -i input.mp4 \
  -o output.mp4 \
  --horiz_speed VALUE \
  --vert_speed VALUE
```

## Arguments

- **horiz_speed** — Horizontal scrolling speed. Positive = scroll right; negative = scroll left.  
- **vert_speed** — Vertical scrolling speed. Positive = scroll down; negative = scroll up.

## Real World Example
```bash
videobeaux -P scrolling_pro \
  -i myvideo.mp4 \
  -o scrolling_pro_styled.mp4 \
  --horiz_speed EXAMPLE \
  --vert_speed EXAMPLE
```

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/e84cfb49-f72d-449e-833a-0271903704f4" type="video/mp4">
  Your browser does not support the video tag.
</video>

<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/19c6eef1-2bc0-4d84-b531-55f9ca07a912" type="video/mp4">
  Your browser does not support the video tag.
</video>

<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/4a4272de-e074-4e37-8c2d-a282f2d8be57" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Large scroll speeds may produce rapid motion suitable for glitch or kinetic graphics.  
- Small scroll speeds create subtle drifting backgrounds or ambient wallpaper loops.  
- Because wraparound is seamless, the effect is ideal for loops when combined with `looper_pro`.  
- Diagonal motion is achieved when both speeds are non-zero.  
- Higher-resolution footage yields smoother scroll texture, especially for slow motion.

## Recommended Usage
- VJ loops and projection mapping backgrounds.  
- Infinite-scroll ambience for installations or screensavers.  
- Graphic overlays behind text or UI elements.  
- Creating drifting collage components inside Lagkage layouts.  
- Building kinetic transitions between scenes.

## Quality Tips
- Use lower CRF for cleaner scroll edges, especially with detailed textures.  
- Slight blur (e.g., via `blur_pix`) before scrolling can remove hard seams in loop textures.  
- Combine with `double_cup` or `lsd_feedback` for trippy drifting effects.  
- Slow speeds often look more cinematic; fast speeds suit glitch or techno edits.  
- Apply `convert_dims` first if you need scroll-safe aspect ratios for looping platforms.

