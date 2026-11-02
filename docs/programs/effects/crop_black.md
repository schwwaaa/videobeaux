# crop_black

## Description
Finds black bars on the top and bottom (letterbox) or the sides (pillarbox), crops them away, and scales the picture to the nearest standard frame size.

## Purpose
`crop_black` is for creators who want to:
- remove letterbox bars from a film or a screen recording,
- clean up a clip with black borders before layering it with other footage,
- get a standard output size without measuring the picture by hand.

## How It Works
1. **Finding the picture**
   ffmpeg's `cropdetect` reads two frames a second and reports the picture box in each one. The box most frames agree on is taken as the picture. Frames are judged one at a time, so a fade to black does not move the result.
2. **Black threshold**
   `threshold` (0–255) sets how dark a pixel must be to count as black. Raise it when the bars are dark grey rather than pure black.
3. **Standard size**
   The picture is scaled to the standard frame size closest in shape (for example 1920×1080 for 16:9, 1920×800 for a 2.4:1 film, 1080×1920 for portrait). The picture fills that frame and any small overflow is trimmed, so no black bars come back.
4. **Keep size**
   With `keep_size` on, the picture stays at the size it was cropped to, rounded to even numbers.
5. **No bars**
   If the clip has no bars, the video is copied unchanged.

## Program Template
```bash
videobeaux -P crop_black -i input.mp4 -o output.mp4 --threshold VALUE --keep_size
```

## Arguments

- **threshold** — How dark a pixel must be to count as black, 0–255. Default 24.  
- **keep_size** — Keep the cropped size instead of scaling to a standard frame size.

## Real World Example
```bash
videobeaux -P crop_black \
  -i film_letterboxed.mp4 \
  -o film_cropped.mp4
```

## Technical Notes
- The crop is the same for the whole clip. Bars that change size partway through are not followed.  
- Scaling to a standard size can enlarge a small picture. Turn on `keep_size` to avoid that.  
- Audio is copied unchanged.
