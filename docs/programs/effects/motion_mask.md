# motion_mask

## Description
Separates what moves from what stands still. The background is learned from the frames so far (OpenCV's MOG2 background subtraction), and anything that differs from it counts as moving. Three looks: a black-and-white mask, the picture with the moving parts tinted, or only the moving parts left on black.

## Purpose
Isolating a person walking through a shot, showing motion for a title sequence, or making a mask to use with other programs.

## How It Works
1. **Learning the background**
   `history` sets how many frames the background is learned from. A longer memory is steadier but slower to forget something that has stopped moving.
2. **Sensitivity**
   `threshold` is how different a pixel must be from the background to count as moving. Lower is more sensitive, and also catches more noise.
3. **The look**
   `mask` gives white where things move. `highlight` keeps the picture and tints the moving parts red. `isolate` keeps only the moving parts.
4. **Invert**
   `--invert` swaps the moving and still parts.

## Program Template
```bash
videobeaux -P motion_mask -i input.mp4 -o output.mp4 --mode mask --history 200 --threshold 16
```

## Arguments
- **mode**: `mask` (default), `highlight`, or `isolate`.
- **history**: frames the background is learned from, 10–1000. Default `200`.
- **threshold**: sensitivity, 4–100. Default `16`.
- **invert**: show what stands still instead of what moves.

## Real World Example
Pulling a walker out of a fixed-camera shot:
```bash
videobeaux -P motion_mask -i doorway.mp4 -o walker_only.mp4 --mode isolate --history 120 --threshold 24
```

## Technical Notes
- The first frames are mostly "moving", because nothing has been learned yet. Give the background a few seconds to settle.
- A camera that moves makes everything move. Use it on footage from a locked-off camera.
