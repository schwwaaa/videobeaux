# meta_extraction

## Description

Extracts detailed metadata—including codecs, bitrates, dimensions, color info, and stream structure—from any media file

## Arguments

- `outputfile`
- `sample_frames`
- `sample_stride`
- `sample_limit`
- `blackdetect`
- `black_pic_th`
- `black_dur_min`
- `loudness`

## Program Template

```bash
videobeaux -P meta_extraction -i input.mp4 -o output.mp4 --outputfile VALUE --sample_frames VALUE --sample_stride VALUE --sample_limit VALUE --blackdetect VALUE --black_pic_th VALUE --black_dur_min VALUE --loudness VALUE
```

## Real World Example

```bash
videobeaux -P meta_extraction -i myvideo.mp4 -o meta_extraction_styled.mp4 --outputfile EXAMPLE --sample_frames EXAMPLE --sample_stride EXAMPLE --sample_limit EXAMPLE --blackdetect EXAMPLE --black_pic_th EXAMPLE --black_dur_min EXAMPLE --loudness EXAMPLE
```
