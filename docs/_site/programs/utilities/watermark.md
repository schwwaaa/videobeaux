# watermark

## Description
Applies image or text watermarks onto video with configurable positioning, scaling, opacity, and blend style.

## Purpose
The `watermark` program allows creators to apply branding, artist signatures, copyright marks, or aesthetic overlays to video.  
It supports dynamic placement, scaling, opacity control, looping behavior for animated watermarks, and optional spinning for stylized effects.  
This tool is designed for flexible, production-ready watermark rendering in both subtle and bold presentation styles.

## How It Works
1. **Watermark Source**  
   Accepts PNG (with alpha), static images, GIFs, or video files as the watermark.
2. **Placement Logic**  
   - `placement` sets anchor position (`top-left`, `top-right`, `center`, etc.).  
   - `margin` offsets the watermark inward from edges.
3. **Scaling & Opacity**  
   - `scale` determines size relative to the input video.  
   - `opacity` controls transparency for subtle or strong branding.
4. **Animated Watermarks**  
   - `wm_loop` determines whether GIF/video watermarks loop.  
   - `ignore_loop` overrides embedded loop metadata for continuous playback.
5. **Timing Controls**  
   - `start` and `end` specify when the watermark appears.
6. **Optional Spin**  
   - `spin` rotates the watermark (`none`, `slow`, `medium`, `fast`).
7. **Encoding**  
   Output uses the provided CRF and preset options for consistent quality.

## Program Template
    videobeaux -P watermark \
      -i input.mp4 \
      -o output.mp4 \
      --watermark VALUE \
      --placement VALUE \
      --margin VALUE \
      --scale VALUE \
      --opacity VALUE \
      --spin VALUE \
      --start VALUE \
      --end VALUE \
      --wm_loop VALUE \
      --ignore_loop VALUE \
      --video_crf VALUE \
      --video_preset VALUE

## Arguments

- **watermark** — Path to the watermark image/video file.  
- **placement** — Anchor location (`top-left`, `top-right`, `center`, etc.).  
- **margin** — Pixel offset from edges, applied to chosen placement.  
- **scale** — Watermark size as a percentage of video resolution.  
- **opacity** — Transparency level (0.0–1.0).  
- **spin** — Rotation behavior (`none`, `slow`, etc.).  
- **start** — Timestamp when watermark begins appearing.  
- **end** — Timestamp when watermark stops appearing.  
- **wm_loop** — Controls looping behavior of animated watermarks.  
- **ignore_loop** — Forces continuous play, overriding GIF/video loop metadata.  
- **video_crf** — CRF controlling overall visual quality.  
- **video_preset** — Encoder preset adjusting render speed vs. compression.

## Real World Example
    videobeaux -P watermark \
      -i myvideo.mp4 \
      -o watermark_styled.mp4 \
      --watermark logo.png \
      --placement bottom-right \
      --margin 48 \
      --scale 22 \
      --opacity 0.85 \
      --spin none \
      --start 0 \
      --end 99999 \
      --wm_loop true \
      --ignore_loop false \
      --video_crf 18 \
      --video_preset medium

## Technical Notes
- PNG or WebP with alpha produces the cleanest transparency.  
- Scaling above 40–50% may reveal softness depending on watermark resolution.  
- GIFs can be heavy; consider converting animated watermarks to WebM.  
- High opacity (>0.9) can dominate imagery; branding often prefers 0.35–0.75.  
- Spinning overlays increase rendering time due to per-frame transformations.

## Recommended Usage
- Artist signatures, branding marks, portfolio reels.  
- Subtle watermarks for social media videos.  
- Bold center overlays for drafts, screeners, and pre-release content.  
- Animated or stylized overlays for creative/motion-design aesthetics.

## Quality Tips
- Use CRF **16–20** for high-quality, lightweight renders.  
- Keep watermark assets at **2× resolution** for sharp results after scaling.  
- For subtle looks: lower opacity, small scale, bottom-right placement.  
- For strong visibility: center placement, moderate opacity, optional spin.  
- Animated overlays work best at ~12–18fps to optimize encoding performance.
