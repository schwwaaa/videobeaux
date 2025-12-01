# wipe_transitions

## Description

Creates directional wipe transitions between clips using customizable timing, edge softness, and motion orientation

## Arguments

- `input1`
- `input2`
- `output_format`
- `preset`
- `duration`
- `offset`

## Program Template

```bash
videobeaux -P wipe_transitions -i input.mp4 -o output.mp4 --input1 VALUE --input2 VALUE --output_format VALUE --preset VALUE --duration VALUE --offset VALUE
```

## Real World Example

```bash
videobeaux -P wipe_transitions -i myvideo.mp4 -o wipe_transitions_styled.mp4 --input1 EXAMPLE --input2 EXAMPLE --output_format EXAMPLE --preset EXAMPLE --duration EXAMPLE --offset EXAMPLE
```
