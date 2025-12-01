---
layout: default
title: tonemap_hdr_sdr
nav_order: 2
---

# tonemap_hdr_sdr

## Description

Converts HDR footage (PQ/HLG) to SDR using tunable tonemapping curves, preserving highlight detail and color accuracy

## Arguments

- `outfile`
- `algo`
- `desat`
- `peak`
- `dither`
- `pix_fmt`
- `x264_preset`
- `crf`
- `copy_audio`

## Program Template

```bash
videobeaux -P tonemap_hdr_sdr -i input.mp4 -o output.mp4 --outfile VALUE --algo VALUE --desat VALUE --peak VALUE --dither VALUE --pix_fmt VALUE --x264_preset VALUE --crf VALUE --copy_audio VALUE
```

## Real World Example

```bash
videobeaux -P tonemap_hdr_sdr -i myvideo.mp4 -o tonemap_hdr_sdr_styled.mp4 --outfile EXAMPLE --algo EXAMPLE --desat EXAMPLE --peak EXAMPLE --dither EXAMPLE --pix_fmt EXAMPLE --x264_preset EXAMPLE --crf EXAMPLE --copy_audio EXAMPLE
```
