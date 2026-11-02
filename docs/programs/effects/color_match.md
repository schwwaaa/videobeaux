# color_match

## Description
Moves the colour of the clip toward a reference clip or still image. The method is Reinhard colour transfer in LAB colour: the average and spread of each channel are moved from the clip's own to the reference's. The colour is measured once, over sampled frames, so the whole clip gets one consistent correction.

## Purpose
Footage from two cameras or two days that should look like one shoot. Or a clip made to match a still you already like.

## How It Works
1. **Measure**
   `samples` frames are read from the clip and from the reference. For each, the mean and spread of each LAB channel are measured.
2. **Transfer**
   Each pixel's lightness and colour are moved from the clip's average to the reference's average, scaled by the ratio of spreads.
3. **Strength**
   `strength` blends the result with the original: 1 is the full match, 0.5 is halfway.

Because the correction is measured once, it does not flicker; but a clip whose scene changes a lot will get a single compromise correction.

## Program Template
```bash
videobeaux -P color_match -i camera_b.mp4 -o camera_b_matched.mp4 --reference camera_a.mp4 --strength 1.0
```

## Arguments
- **reference**: the clip or still image whose colour to match. Connect it on the canvas.
- **strength**: 0 to 1. Default `1.0`.
- **samples**: frames sampled from each video, 3–60. Default `20`.

## Real World Example
Make a warm, late-afternoon shot match a cool, overcast one shot earlier that day:
```bash
videobeaux -P color_match -i warm_pm.mp4 -o warm_pm_matched.mp4 --reference overcast_am.mp4 --strength 0.7
```

## Technical Notes
- Measured on test clips: a warm test colour moved onto a blue reference, landing within 2 levels of the reference at full strength.
- The reference can be a still image: the colour is measured from that one picture.
