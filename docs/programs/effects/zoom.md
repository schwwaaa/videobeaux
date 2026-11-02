# zoom

## Description
Zooms in by a percentage toward a point you choose. The frame keeps its size: the picture is cropped around the focus point and scaled back up to the full frame.

## Purpose
`zoom` is for creators who want to:
- push in on a subject for emphasis, a punch-in, or a reaction shot,
- recentre a shot that was framed too wide,
- get a quick digital push-in without changing the output format.

## How It Works
1. **Zoom amount**
   `zoom` is a percentage: `100` = no zoom, `150` = 1.5× closer, `200` = twice as close.
2. **Focus point**
   `focus_x` and `focus_y` are percentages across the frame: `0` = left or top edge, `50` = centre, `100` = right or bottom edge.
3. **Crop and scale**
   The crop window is the frame divided by the zoom, centred on the focus point. It stays inside the frame, so a focus near an edge zooms toward that edge instead of past it. The window is then scaled back to the frame size.
4. **Encoding**
   Video is encoded as H.264 with CRF 18. Audio is copied unchanged.

## Program Template
```bash
videobeaux -P zoom -i input.mp4 -o output.mp4 --zoom VALUE --focus_x VALUE --focus_y VALUE
```

## Arguments

- **zoom** — Zoom as a percentage (100 = no zoom). Default 150.  
- **focus_x** — Horizontal focus point, 0–100. Default 50.  
- **focus_y** — Vertical focus point, 0–100. Default 50.

## Real World Example
```bash
videobeaux -P zoom \
  -i interview.mp4 \
  -o interview_punch_in.mp4 \
  --zoom 180 --focus_x 42 --focus_y 35
```

## Technical Notes
- The zoom is fixed for the whole clip. It does not follow a subject; use `face_follow` for a moving reframe.  
- The output has the same size as the input, so zooming in softens the picture: a 200% zoom shows a quarter of the original pixels.  
- A zoom below 100 is refused: the program only zooms in.
