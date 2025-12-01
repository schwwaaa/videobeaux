# lagkage

## Description

A JSON-driven multilayer video compositor that stacks, positions, resizes, and mixes multiple media sources into one unified output

## Arguments

- `layout_json`
- `sequence_direction`
- `audio_mode`
- `audio_src`

## Program Template

```bash
videobeaux -P lagkage -i input.mp4 -o output.mp4 --layout_json VALUE --sequence_direction VALUE --audio_mode VALUE --audio_src VALUE
```

## Real World Example

```bash
videobeaux -P lagkage -i myvideo.mp4 -o lagkage_styled.mp4 --layout_json EXAMPLE --sequence_direction EXAMPLE --audio_mode EXAMPLE --audio_src EXAMPLE
```

## Program Output

[Program output video](https://github.com/schwwaaa/videobeaux/assets/7625379/65403294-3e34-4ff8-816a-5de7c80c811d)
