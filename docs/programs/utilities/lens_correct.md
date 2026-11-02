# lens_correct

## Description
Straightens the bend of a wide-angle or action-camera lens. Barrel distortion (straight edges bowing outward, common on wide lenses) and pincushion distortion (edges pinched inward) are both corrected with ffmpeg's lenscorrection filter.

## Purpose
Action-camera and phone wide-angle footage where the horizon or building edges curve.

## How It Works
1. **k1**
   The main correction. A negative value removes barrel bulge; a positive value removes pincushion. The further from zero, the stronger the correction.
2. **k2**
   A finer correction for the far edges. Set it after k1.
3. **Picture**
   The correction is applied to every frame; the audio is copied unchanged.

Start with `k1` around `-0.2` for an action camera, then check a straight edge near the frame's corner and adjust.

## Program Template
```bash
videobeaux -P lens_correct -i input.mp4 -o output.mp4 --k1 -0.2 --k2 0
```

## Arguments
- **k1**: main correction, −0.5 to 0.5. Default `-0.2`.
- **k2**: fine correction, −0.5 to 0.5. Default `0`.

## Real World Example
A bodycam-style clip where the doorframes bow outward:
```bash
videobeaux -P lens_correct -i action_cam.mp4 -o action_straight.mp4 --k1 -0.28 --k2 0.02
```

## Technical Notes
- Correcting too far bends the picture the other way. Look at a straight line near the edge while you adjust.
- The frame keeps its size: the picture is reshaped inside it, and the output is the same width and height as the input.
