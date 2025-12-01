# silence_extraction

## Description

Extracting the silence out of a video file

## Arguments

- `min_d`
- `max_d`
- `adjuster`

## Program Template

```bash
videobeaux -P silence_extraction -i input.mp4 -o output.mp4 --min_d VALUE --max_d VALUE --adjuster VALUE
```

## Real World Example

```bash
videobeaux -P silence_extraction -i myvideo.mp4 -o silence_extraction_styled.mp4 --min_d EXAMPLE --max_d EXAMPLE --adjuster EXAMPLE
```
