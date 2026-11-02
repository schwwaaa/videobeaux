# clean_plate

## Description
Removes things that move through a locked-off shot: people walking past, cars, a hand reaching in. A clean plate (the empty scene) is built from the per-pixel median of frames sampled across the clip, so anything that passes through is left out of it. Then the moving parts of each frame are replaced with the plate.

## Purpose
A tripod shot of a room, street or stage with someone in the way, or a background you want to use for other effects with nothing moving in it.

## How It Works
1. **The plate**
   `samples` frames are spread across the clip. The median of each pixel across them is the empty scene. Something that moves through a spot for less than half the time is left out of the plate.
2. **The moving parts**
   Each frame is compared with the plate. Pixels that differ by more than `sensitivity` count as moving, with soft edges.
3. **Replace**
   `remove_movers` takes the plate wherever something moves and keeps the original everywhere else. `plate_only` outputs the empty scene for the whole clip.

**Limit:** the camera must not move. Something that stops in one place for most of the clip becomes part of the plate.

## Program Template
```bash
videobeaux -P clean_plate -i tripod_shot.mp4 -o output.mp4 --mode remove_movers --sensitivity 28
```

## Arguments
- **mode**: `remove_movers` (default) or `plate_only`.
- **sensitivity**: how different a pixel must be to count as moving, 4–120. Default `28`. Lower catches more, including noise.
- **samples**: frames sampled for the plate, 5–80. Default `25`.
- **detail**: width the plate and mask are worked out at, then scaled up. Default `960`.

## Real World Example
A street shot with pedestrians crossing in front of a shopfront; keep the shopfront clear:
```bash
videobeaux -P clean_plate -i street_tripod.mp4 -o street_clear.mp4 --samples 40
```

## Technical Notes
- Measured on a test clip: a moving orange box was removed completely in both modes.
- The plate and the mask are worked out at `detail` width, then scaled up to the full frame, so the edges of a removed shape are only as sharp as that width allows.
