# watermark

## Description
Applies image or text watermarks onto video with configurable positioning, scaling, opacity, and blend style.

## Purpose
The `watermark` program allows creators to apply branding, artist signatures, copyright marks, or aesthetic overlays to video.  
It supports dynamic placement, scaling, opacity control, looping behavior for animated watermarks, and optional spinning for stylized effects.  
This tool is designed for flexible, production-ready watermark rendering in both subtle and bold presentation styles.

## How It Works
1. **Watermark Source**
   The program accepts an image, PNG with alpha, GIF, or video file as a watermark.

2. **Placement Logic**
   The `placement` argument determines anchor position (top-right, center, bottom-left, etc.).  
   `margin` offsets the watermark inward from the edges.

3. **Scaling & Opacity**
   - `scale` adjusts watermark size relative to source video.
   - `opacity` modifies transparency for subtle or strong branding.

4. **Animated Watermarks**
   - `wm_loop` controls GIF/video looping behavior.
   - `ignore_loop` forces continuous playback regardless of embedded loop metadata.

5. **Timing Controls**
   - `start` and `end` define the segment of the video where the watermark appears.

6. **Optional Spin**
   - `spin` applies rotation (slow, medium, fast) for stylistic or meme-style effects.

7. **Encoding**
   - Output is encoded using the specified CRF and x264 preset.

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

## Program Arguments
- `watermark`
- `placement`
- `margin`
- `scale`
- `opacity`
- `spin`
- `start`
- `end`
- `wm_loop`
- `ignore_loop`
- `video_crf`
- `video_preset`

### Argument Details
| Argument | Meaning |
|---------|---------|
| **watermark** | Path to the image or video file used as the watermark. |
| **placement** | Anchor position such as `top-left`, `top-right`, `center`, etc. |
| **margin** | Pixel margin offset from edges (applies to chosen placement). |
| **scale** | Percentage scale relative to the input video resolution. |
| **opacity** | Transparency level for the watermark. |
| **spin** | Optional rotation behavior (`none`, `slow`, etc.). |
| **start** | Timestamp where the watermark begins appearing. |
| **end** | Timestamp where the watermark stops appearing. |
| **wm_loop** | Controls whether animated watermarks loop. |
| **ignore_loop** | Overrides embedded loop metadata for GIF/video. |
| **video_crf** | CRF value determining visual quality vs file size. |
| **video_preset** | Encoder preset controlling speed vs compression. |

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
- PNG or WebP with alpha provides the cleanest transparency.
- Scaling above 40–50% may cause noticeable softness depending on source watermark resolution.
- Animated GIF watermarks can be heavy; consider converting to WebM with alpha.
- Using high `opacity` values (>0.9) can distract from content; typical branding uses 0.35–0.75.
- Spinning watermarks increase render time due to constant re-compositing.

## Recommended Usage
- Applying branding for artist portfolios.
- Subtle corner watermarks for reels or social uploads.
- Bold center overlays for drafts, watermarked screeners, and pre-release emissions.
- Animated watermarking for stylized aesthetics or motion-design-heavy formats.

## Quality Tips
- Use `video_crf 16–20` for high-quality delivery.
- Keep watermark assets at least **2×** the target display resolution for sharp scaling.
- For subtle looks: low opacity, small scale, bottom-right placement.
- For maximal visibility: center placement, moderate opacity, optional spin.
- When using animations, consider optimizing watermark frame rate to 12–18fps for efficiency.
