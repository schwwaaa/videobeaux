---
layout: default
title: convert_mux
nav_order: 2
---

# convert_mux

## Description

Rewraps or converts media streams while copying or re-encoding video/audio, ideal for fixing containers, codecs, or sync issues.

## Arguments

- `format`
- `profile`
- `vcodec`
- `acodec`
- `crf`
- `bitrate`
- `maxrate`
- `bufsize`
- `preset`
- `profile_v`
- `level`
- `pix_fmt`
- `gop`
- `r`
- `vf`
- `tagv`
- `abitrate`
- `ac`
- `ar`
- `copy`

## Program Template

```bash
videobeaux -P convert_mux -i input.mp4 -o output.mp4 --format VALUE --profile VALUE --vcodec VALUE --acodec VALUE --crf VALUE --bitrate VALUE --maxrate VALUE --bufsize VALUE --preset VALUE --profile_v VALUE --level VALUE --pix_fmt VALUE --gop VALUE --r VALUE --vf VALUE --tagv VALUE --abitrate VALUE --ac VALUE --ar VALUE --copy VALUE
```

## Real World Example

```bash
videobeaux -P convert_mux -i myvideo.mp4 -o convert_mux_styled.mp4 --format EXAMPLE --profile EXAMPLE --vcodec EXAMPLE --acodec EXAMPLE --crf EXAMPLE --bitrate EXAMPLE --maxrate EXAMPLE --bufsize EXAMPLE --preset EXAMPLE --profile_v EXAMPLE --level EXAMPLE --pix_fmt EXAMPLE --gop EXAMPLE --r EXAMPLE --vf EXAMPLE --tagv EXAMPLE --abitrate EXAMPLE --ac EXAMPLE --ar EXAMPLE --copy EXAMPLE
```
