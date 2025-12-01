---
layout: default
title: gamma_fix
nav_order: 2
---

# gamma_fix

## Description

Normalizes gamma, brightness, and exposure levels for broadcast-safe or web-safe consistency across diverse footage

## Arguments

- `target_yavg`
- `min_contrast`
- `max_contrast`
- `gamma`
- `sat`
- `legalize`
- `vcodec`
- `crf`
- `preset`
- `acodec`
- `ab`

## Program Template

```bash
videobeaux -P gamma_fix -i input.mp4 -o output.mp4 --target_yavg VALUE --min_contrast VALUE --max_contrast VALUE --gamma VALUE --sat VALUE --legalize VALUE --vcodec VALUE --crf VALUE --preset VALUE --acodec VALUE --ab VALUE
```

## Real World Example

```bash
videobeaux -P gamma_fix -i myvideo.mp4 -o gamma_fix_styled.mp4 --target_yavg EXAMPLE --min_contrast EXAMPLE --max_contrast EXAMPLE --gamma EXAMPLE --sat EXAMPLE --legalize EXAMPLE --vcodec EXAMPLE --crf EXAMPLE --preset EXAMPLE --acodec EXAMPLE --ab EXAMPLE
```
