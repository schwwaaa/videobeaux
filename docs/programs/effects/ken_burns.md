# ken_burns

## Description
A slow push-in (or pull-out) across the whole clip, like a camera dolly moving over a still photo. The zoom changes in a straight line from the start zoom to the end zoom and closes in on a focus point.

## Purpose
Bringing a still image to life, or adding a slow move to footage that was shot on a locked-off camera.

## How It Works
1. **The zoom**
   The zoom is `start_zoom` at the first frame and `end_zoom` at the last, moving evenly between them. A value of `1` is the whole picture; `2` shows half the width and height.
2. **The focus**
   `focus_x` and `focus_y` (0 to 1) set the point the zoom closes in on: `0.5, 0.5` is the middle, `0, 0` the top-left corner.
3. **Pull-out**
   Set `end_zoom` below `start_zoom` to pull out instead of pushing in. Both values must be 1 or more.

## Program Template
```bash
videobeaux -P ken_burns -i input.mp4 -o output.mp4 --start_zoom 1.0 --end_zoom 1.3 --focus_x 0.5 --focus_y 0.4
```

## Arguments
- **start_zoom**: zoom at the first frame. Default `1.0`.
- **end_zoom**: zoom at the last frame. Default `1.3`.
- **focus_x**: horizontal focus, 0 (left) to 1 (right). Default `0.5`.
- **focus_y**: vertical focus, 0 (top) to 1 (bottom). Default `0.5`.

## Real World Example
A portrait photo made into a 10-second clip, closing in on the face:
```bash
videobeaux -P ken_burns -i portrait_still.mp4 -o portrait_move.mp4 --end_zoom 1.4 --focus_y 0.35
```

## Technical Notes
- The zoom is computed per frame from the clip's frame count, so the speed is even whatever the frame rate.
- The audio is copied unchanged.
