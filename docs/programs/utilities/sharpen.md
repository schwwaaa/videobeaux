# sharpen

## Description
Crisps up soft footage. Two methods: `unsharp` (classic edge sharpening over a chosen detail size) and `cas` (contrast-adaptive sharpening, which adds detail where the picture is soft and leaves crisp edges alone). The colour is not changed.

## Purpose
Old tape transfers, upscaled footage, and anything that looks a little soft after a resize, compression, or a shaky lens.

## How It Works
1. **unsharp**
   The picture is blurred over `radius` pixels, the difference from the original is measured, and that difference is added back, scaled by `amount`. Only the luminance is sharpened; the chroma is left alone so there are no coloured halos.
2. **cas**
   Sharpens with the strength of `amount` (scaled to ffmpeg's 0–1 range), applied more where the local contrast is low.
3. **Encoding**
   The video is re-encoded as H.264 and the audio is copied unchanged.

## Program Template
```bash
videobeaux -P sharpen -i input.mp4 -o output.mp4 --mode unsharp --amount 0.8 --radius 5
```

## Arguments
- **mode**: `unsharp` (default) or `cas`.
- **amount**: 0 to 3. Default `0.8`. Above about 1.5, halos show around edges.
- **radius**: detail size in pixels for `unsharp`, 3–13, odd numbers. Default `5`.

## Real World Example
A soft phone recording that looks blurry on a big screen:
```bash
videobeaux -P sharpen -i phone_soft.mp4 -o phone_crisp.mp4 --mode cas --amount 1.0
```

## Technical Notes
- Sharpening also brings out noise and compression blocks. Run Denoise Video first if the picture is grainy.
- Measured on a test clip: edge contrast rose from about 1140 to 2900 (unsharp, amount 1.2) and to about 1870 (cas, amount 1.5).
