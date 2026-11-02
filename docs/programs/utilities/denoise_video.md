# denoise_video

## Description
Softens the grain and speckle of noisy footage (low light, high ISO) while keeping the edges. Uses ffmpeg's hqdn3d, which smooths within each frame (spatial) and across neighbouring frames (temporal).

## Purpose
Footage shot in dim light, or on a camera pushed to a high ISO, where the grain hides the detail.

## How It Works
1. **Spatial smoothing**
   Neighbouring pixels in the same frame are averaged, where they are close in colour. Edges, which differ a lot, are left alone.
2. **Temporal smoothing**
   Pixels that stay the same from frame to frame are averaged over time, which removes the flicker of grain.
3. **Strength**
   `light` keeps most of the detail. `medium` is a good starting point. `strong` smooths a lot and can look painterly on faces.

## Program Template
```bash
videobeaux -P denoise_video -i input.mp4 -o output.mp4 --strength medium
```

## Arguments
- **strength**: `light`, `medium` (default), or `strong`.

## Real World Example
A night-time clip from a phone, with heavy colour noise in the dark areas:
```bash
videobeaux -P denoise_video -i night_phone.mp4 -o night_smooth.mp4 --strength strong
```

## Technical Notes
- Strong settings soften moving detail, so check the result on faces and text.
- The video is re-encoded as H.264; the audio is copied unchanged.
