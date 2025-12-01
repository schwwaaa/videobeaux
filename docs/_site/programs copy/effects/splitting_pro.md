# splitting_pro

## Description

Precise segmentation tool that slices a source video into reusable chunks based on time, count, or scene-style rules for downstream editing and recombination.

## Arguments

- `width`
- `position`

## Program Template

```bash
videobeaux -P splitting_pro -i input.mp4 -o output.mp4 --width VALUE --position VALUE
```

## Real World Example

```bash
videobeaux -P splitting_pro -i myvideo.mp4 -o splitting_pro_styled.mp4 --width EXAMPLE --position EXAMPLE
```

## Program Output

[Program output video](https://github.com/schwwaaa/videobeaux/assets/7625379/65403294-3e34-4ff8-816a-5de7c80c811d)
