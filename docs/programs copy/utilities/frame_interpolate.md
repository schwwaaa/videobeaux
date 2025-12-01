# frame_interpolate

## Description

Generates smooth slow-motion or higher-FPS video by creating intermediate frames using motion-compensated interpolation

## Arguments

- `outfile`
- `engine`
- `fps`
- `multiplier`
- `mi_mode`
- `me_mode`
- `mc_mode`
- `vsbmc`
- `scd`
- `x264_preset`
- `crf`
- `copy_audio`
- `rife_bin`
- `dain_bin`

## Program Template

```bash
videobeaux -P frame_interpolate -i input.mp4 -o output.mp4 --outfile VALUE --engine VALUE --fps VALUE --multiplier VALUE --mi_mode VALUE --me_mode VALUE --mc_mode VALUE --vsbmc VALUE --scd VALUE --x264_preset VALUE --crf VALUE --copy_audio VALUE --rife_bin VALUE --dain_bin VALUE
```

## Real World Example

```bash
videobeaux -P frame_interpolate -i myvideo.mp4 -o frame_interpolate_styled.mp4 --outfile EXAMPLE --engine EXAMPLE --fps EXAMPLE --multiplier EXAMPLE --mi_mode EXAMPLE --me_mode EXAMPLE --mc_mode EXAMPLE --vsbmc EXAMPLE --scd EXAMPLE --x264_preset EXAMPLE --crf EXAMPLE --copy_audio EXAMPLE --rife_bin EXAMPLE --dain_bin EXAMPLE
```
