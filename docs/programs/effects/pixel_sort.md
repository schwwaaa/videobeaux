# pixel_sort

## Description
Glitch-art pixel sorting. Inside each row (or column) of the picture, the pixels that pass a test are sorted by a value, so they smear into long streaks.

## Purpose
The classic sorted-streak look: bright skies that melt into bars, or shadows that stretch into colour.

## How It Works
1. **Pick the pixels**
   A pixel is picked when its brightness is above `threshold` (or below it, with `select = darker`). Pixels that are not picked never move.
2. **Find the streaks**
   Consecutive picked pixels in a row form a streak. A streak never crosses to the next row, and `min_run` drops streaks shorter than a set length.
3. **Sort each streak**
   Each streak is reordered by `sort_by`: `brightness` (the default), `hue`, `saturation`, or one colour channel. `order` = `ascending` runs from low to high, so the streak gets brighter to the right; `descending` is the reverse.
4. **Mix**
   `mix` blends the sorted picture back over the original: 1 is fully sorted, 0.5 halfway.

**Auto threshold:** with no `threshold`, each frame's own brightness sets it so about 60% of the picture is picked. The threshold eases from frame to frame so the streaks do not flicker. On a bright frame this sorts most of the sky; lower the share by setting `threshold` by hand.

## Program Template
```bash
videobeaux -P pixel_sort -i input.mp4 -o output.mp4 --threshold 150 --sort_by hue --min_run 12
```

## Arguments
- **threshold**: brightness 0–255 that separates picked from not picked. Empty = automatic.
- **select**: `brighter` (default) or `darker`.
- **sort_by**: `brightness` (default), `hue`, `saturation`, `red`, `green`, `blue`.
- **order**: `ascending` (default) or `descending`.
- **vertical**: sort down the columns instead of across the rows.
- **min_run**: shortest streak that gets sorted, in pixels. Default `1` (everything picked). `8`–`30` keeps only the long streaks.
- **mix**: 0 to 1. Default `1.0`.
- **max_width**: sort at this width, then scale back up. Speeds up 4K footage.

## Real World Example
Long dark streaks through the shadows only, leaving the highlights alone:
```bash
videobeaux -P pixel_sort -i night_city.mp4 -o night_streaks.mp4 --select darker --threshold 80 --min_run 20 --order descending
```

## Technical Notes
- Each frame is processed on its own, so the effect is slow on long 4K clips. Set `max_width` to 1280 or so to speed it up.
- Hue and saturation sorting use OpenCV's colour conversion.
