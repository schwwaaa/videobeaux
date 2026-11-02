# local_contrast

## Description
CLAHE (contrast-limited adaptive histogram equalisation). The contrast is equalised in small patches of the picture, so a dark corner and a bright sky can both show detail at once. Only the lightness changes; the colours stay as they are.

## Purpose
Flat, hazy or badly lit footage, where a global brightness change would wash out either the shadows or the highlights.

## How It Works
1. **Lightness only**
   The picture is converted to LAB colour, the L (lightness) channel is equalised, and the picture is converted back.
2. **Patches**
   `tiles` sets how many patches the picture is split into across. Each patch gets its own contrast curve, and the patches are blended so no edges show.
3. **Clip limit**
   `clip` caps how steeply the contrast can grow in one patch. Higher values give more punch and more grain.

## Program Template
```bash
videobeaux -P local_contrast -i input.mp4 -o output.mp4 --clip 2.0 --tiles 8
```

## Arguments
- **clip**: clip limit, 0.5–8. Default `2.0`.
- **tiles**: patches across the picture, 2–32. Default `8`.

## Real World Example
A night street shot where the lamp-lit faces are lost in the dark:
```bash
videobeaux -P local_contrast -i street_night.mp4 -o street_detail.mp4 --clip 3 --tiles 12
```

## Technical Notes
- Frame by frame with OpenCV, so a long 4K clip takes a while. Use Speed or Resize first if you only need a smaller result.
- The audio is copied unchanged.
