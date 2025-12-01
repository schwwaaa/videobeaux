# thumbs

## Description

Generates thumbnails or contact sheets by sampling frames at chosen intervals for previews, galleries, or QC review

## Arguments

- `fps`
- `scene`
- `scene_threshold`
- `tile`
- `scale`
- `timestamps`
- `label`
- `fontfile`
- `bg`
- `margin`
- `padding`
- `outdir`
- `outputfile`
- `image_format`
- `jpeg_quality`

## Program Template

```bash
videobeaux -P thumbs -i input.mp4 -o output.mp4 --fps VALUE --scene VALUE --scene_threshold VALUE --tile VALUE --scale VALUE --timestamps VALUE --label VALUE --fontfile VALUE --bg VALUE --margin VALUE --padding VALUE --outdir VALUE --outputfile VALUE --image_format VALUE --jpeg_quality VALUE
```

## Real World Example

```bash
videobeaux -P thumbs -i myvideo.mp4 -o thumbs_styled.mp4 --fps EXAMPLE --scene EXAMPLE --scene_threshold EXAMPLE --tile EXAMPLE --scale EXAMPLE --timestamps EXAMPLE --label EXAMPLE --fontfile EXAMPLE --bg EXAMPLE --margin EXAMPLE --padding EXAMPLE --outdir EXAMPLE --outputfile EXAMPLE --image_format EXAMPLE --jpeg_quality EXAMPLE
```
