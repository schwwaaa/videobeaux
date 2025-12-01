---
layout: default
title: captburn
nav_order: 2
---

# captburn

## Description

Burns subtitles, captions, or transcript text directly into the video with precise styling, timing, and layout control

## Arguments

- `caption`
- `style`
- `rollup_lines`
- `words_per_line`
- `font`
- `font_size`
- `bold`
- `italic`
- `primary`
- `outline`
- `outline_width`
- `shadow`
- `back`
- `back_opacity`
- `scale_x`
- `scale_y`
- `spacing`
- `rotate`
- `margin_l`
- `margin_r`
- `margin_v`
- `align`
- `border_style`
- `x`
- `y`
- `move`
- `vcodec`
- `crf`
- `preset`

## Program Template

```bash
videobeaux -P captburn -i input.mp4 -o output.mp4 --caption VALUE --style VALUE --rollup_lines VALUE --words_per_line VALUE --font VALUE --font_size VALUE --bold VALUE --italic VALUE --primary VALUE --outline VALUE --outline_width VALUE --shadow VALUE --back VALUE --back_opacity VALUE --scale_x VALUE --scale_y VALUE --spacing VALUE --rotate VALUE --margin_l VALUE --margin_r VALUE --margin_v VALUE --align VALUE --border_style VALUE --x VALUE --y VALUE --move VALUE --vcodec VALUE --crf VALUE --preset VALUE
```

## Real World Example

```bash
videobeaux -P captburn -i myvideo.mp4 -o captburn_styled.mp4 --caption EXAMPLE --style EXAMPLE --rollup_lines EXAMPLE --words_per_line EXAMPLE --font EXAMPLE --font_size EXAMPLE --bold EXAMPLE --italic EXAMPLE --primary EXAMPLE --outline EXAMPLE --outline_width EXAMPLE --shadow EXAMPLE --back EXAMPLE --back_opacity EXAMPLE --scale_x EXAMPLE --scale_y EXAMPLE --spacing EXAMPLE --rotate EXAMPLE --margin_l EXAMPLE --margin_r EXAMPLE --margin_v EXAMPLE --align EXAMPLE --border_style EXAMPLE --x EXAMPLE --y EXAMPLE --move EXAMPLE --vcodec EXAMPLE --crf EXAMPLE --preset EXAMPLE
```
