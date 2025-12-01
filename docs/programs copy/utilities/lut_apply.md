# lut_apply

## Description

Applies a 3D or 1D LUT file to recolor a video, enabling film-style grading, color transforms, or creative look development

## Arguments

- `outfile`
- `vcodec`
- `lut`
- `interp`
- `intensity`
- `brightness`
- `contrast`
- `saturation`
- `gamma`
- `pix_fmt`
- `x264_preset`
- `crf`
- `copy_audio`

## Program Template

```bash
videobeaux -P lut_apply -i input.mp4 -o output.mp4 --outfile VALUE --vcodec VALUE --lut VALUE --interp VALUE --intensity VALUE --brightness VALUE --contrast VALUE --saturation VALUE --gamma VALUE --pix_fmt VALUE --x264_preset VALUE --crf VALUE --copy_audio VALUE
```

## Real World Example

```bash
videobeaux -P lut_apply -i myvideo.mp4 -o lut_apply_styled.mp4 --outfile EXAMPLE --vcodec EXAMPLE --lut EXAMPLE --interp EXAMPLE --intensity EXAMPLE --brightness EXAMPLE --contrast EXAMPLE --saturation EXAMPLE --gamma EXAMPLE --pix_fmt EXAMPLE --x264_preset EXAMPLE --crf EXAMPLE --copy_audio EXAMPLE
```
