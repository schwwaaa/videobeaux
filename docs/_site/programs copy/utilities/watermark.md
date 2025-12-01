# watermark

## Description

Applies image or text watermarks onto video with configurable positioning, scaling, opacity, and blend style

## Arguments

- `watermark`
- `placement`
- `margin`
- `scale`
- `opacity`
- `spin`
- `start`
- `end`
- `wm_loop`
- `ignore_loop`
- `video_crf`
- `video_preset`

## Program Template

```bash
videobeaux -P watermark -i input.mp4 -o output.mp4 --watermark VALUE --placement VALUE --margin VALUE --scale VALUE --opacity VALUE --spin VALUE --start VALUE --end VALUE --wm_loop VALUE --ignore_loop VALUE --video_crf VALUE --video_preset VALUE
```

## Real World Example

```bash
videobeaux -P watermark -i myvideo.mp4 -o watermark_styled.mp4 --watermark EXAMPLE --placement EXAMPLE --margin EXAMPLE --scale EXAMPLE --opacity EXAMPLE --spin EXAMPLE --start EXAMPLE --end EXAMPLE --wm_loop EXAMPLE --ignore_loop EXAMPLE --video_crf EXAMPLE --video_preset EXAMPLE
```
