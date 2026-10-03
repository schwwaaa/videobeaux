# watermark

## Description
Applies an image watermark or general-purpose image overlay onto video, with configurable positioning, sizing, opacity, and spin. As of this merge, `watermark` absorbs everything the former `overlay_img_pro` program did (9-point placement grid, custom pixel/expression position, exact pixel sizing) — that program has been retired.

## Purpose
The `watermark` program allows creators to apply branding, artist signatures, copyright marks, or precisely-placed graphic overlays to video.  
It supports a 9-point placement grid or a fully custom X/Y position, scaling relative to the source image or exact pixel dimensions, opacity control, looping behavior for animated watermarks, and optional spinning for stylized effects.  
This tool covers both subtle branding use (small, semi-transparent, faded in/out) and precise compositing use (exact placement and size for logos, lower-thirds, or layered graphics).

## How It Works
1. **Watermark/Overlay Source**  
   Accepts PNG (with alpha), static images, or GIFs as the overlay image.
2. **Placement Logic**  
   - `placement` sets anchor position — `top-left`, `top-center`, `top-right`, `center-left`, `center`, `center-right`, `bottom-left`, `bottom-center`, `bottom-right`, or `custom`.  
   - `margin` offsets the overlay inward from edges (ignored for `center*` placements and `custom`).  
   - `custom` placement uses `x_pos`/`y_pos` directly — pixels or an ffmpeg expression — for exact control.
3. **Sizing & Opacity**  
   - `scale` sizes the overlay relative to its own intrinsic width (`iw*scale`).  
   - `width`/`height` override `scale` with exact pixel dimensions when set (use `-1` on either to preserve aspect ratio).  
   - `opacity` controls transparency for subtle or strong branding.
4. **Animated Watermarks**  
   - `wm-loop` determines whether GIF watermarks loop.  
   - `ignore-loop` overrides embedded GIF loop metadata for continuous playback.
5. **Timing Controls**  
   - `start` and `end` specify when the overlay appears (0/unset `end` means until the end of the clip).
6. **Optional Spin**  
   - `spin` rotates the overlay continuously, in degrees per second (0 = no rotation).
7. **Encoding**  
   Output uses the provided CRF and preset options for consistent quality.

## Program Template
    videobeaux -P watermark \
      -i input.mp4 \
      -o output.mp4 \
      --watermark VALUE \
      --placement VALUE \
      --margin VALUE \
      --x_pos VALUE \
      --y_pos VALUE \
      --scale VALUE \
      --width VALUE \
      --height VALUE \
      --opacity VALUE \
      --spin VALUE \
      --start VALUE \
      --end VALUE \
      --wm-loop VALUE \
      --ignore-loop \
      --video-crf VALUE \
      --video-preset VALUE

## Arguments

- **watermark** — Path to the watermark/overlay image (PNG/JPG/GIF).  
- **placement** — Anchor location (9-point grid, or `custom`).  
- **margin** — Pixel offset from edges, applied to edge/corner placements.  
- **x_pos** / **y_pos** — Pixels or an ffmpeg expression; only used when `--placement custom`.  
- **scale** — Overlay size relative to its own intrinsic width (`iw*scale`). Ignored if `width`/`height` is set.  
- **width** / **height** — Exact pixel dimensions; overrides `scale` when either is set (`-1` preserves aspect ratio).  
- **opacity** — Transparency level (0.0–1.0).  
- **spin** — Rotation speed in degrees per second (0 = no rotation).  
- **start** — Timestamp when the overlay begins appearing.  
- **end** — Timestamp when the overlay stops appearing (0 = until the end).  
- **wm-loop** — Controls looping behavior of animated (GIF) watermarks.  
- **ignore-loop** — Forces continuous play, overriding GIF loop metadata.  
- **video-crf** — CRF controlling overall visual quality.  
- **video-preset** — Encoder preset adjusting render speed vs. compression.

## Real World Example
    videobeaux -P watermark \
      -i myvideo.mp4 \
      -o watermark_styled.mp4 \
      --watermark logo.png \
      --placement bottom-right \
      --margin 48 \
      --scale 0.22 \
      --opacity 0.85 \
      --spin 0 \
      --start 0 \
      --end 0 \
      --video-crf 18 \
      --video-preset medium

### Precise-placement example (replaces the old overlay_img_pro use case)
    videobeaux -P watermark \
      -i myvideo.mp4 \
      -o overlay_styled.mp4 \
      --watermark logo.png \
      --placement custom \
      --x_pos 100 \
      --y_pos 50 \
      --width 200 \
      --height -1 \
      --opacity 1.0

## Technical Notes
- PNG with alpha produces the cleanest transparency.  
- Scaling above 40–50% may reveal softness depending on overlay resolution.  
- GIFs can be heavy; consider converting animated watermarks to WebM.  
- High opacity (>0.9) can dominate imagery; branding often prefers 0.35–0.75.  
- Spinning overlays increase rendering time due to per-frame transformations.  
- `width`/`height` take priority over `scale` whenever either is set — leave both unset to use `scale`.

## Recommended Usage
- Artist signatures, branding marks, portfolio reels.  
- Subtle watermarks for social media videos.  
- Bold center overlays for drafts, screeners, and pre-release content.  
- Animated or stylized overlays for creative/motion-design aesthetics.  
- Precisely-placed logos, lower-thirds, or graphic elements needing exact pixel coordinates and size.

## Quality Tips
- Use CRF **16–20** for high-quality, lightweight renders.  
- Keep watermark assets at **2× resolution** for sharp results after scaling.  
- For subtle looks: lower opacity, small scale, bottom-right placement.  
- For strong visibility: center placement, moderate opacity, optional spin.  
- Animated overlays work best at ~12–18fps to optimize encoding performance.
