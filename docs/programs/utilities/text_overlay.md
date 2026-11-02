# text_overlay

## Description
A simple titler: a block of text laid over the video. The font and colours are the same as Auto Narrate's captions, and the placement and timing are the same as Watermark's.

## Purpose
Titles, lower thirds, a name card or a line of context over a clip, without making an image first.

## How It Works
1. **The text**
   The text is drawn into a transparent image with the caption font and a coloured outline, at exactly the `font_size` you set. Lines wrap to 86% of the frame width. The size never changes with the amount of text: a long title just takes more lines. If the block is taller than the frame, a warning is printed and the top or bottom is cut off.
2. **Placement**
   `placement` is one of the nine grid positions (`top-left` … `bottom-right`, with `bottom-center` as the default) or `custom`. With `custom`, `x_pos` and `y_pos` take pixels or an ffmpeg expression. `margin` is the distance from the edges.
3. **Timing**
   `start` (Appear at) and `end` (Disappear at) take seconds or a timestamp. `0` for `end` means the text stays to the end of the video.
4. **Encoding**
   The overlay is applied by the watermark program, so the output is H.264 with the audio copied unchanged.

## Program Template
```bash
videobeaux -P text_overlay -i input.mp4 -o output.mp4 --text "Your title" --placement VALUE --start VALUE --end VALUE
```

## Arguments
- **text**: the text to show. A new line in the text starts a new line on screen.
- **font**: a font name or the path to a `.ttf`/`.otf` file. Default `Arial`.
- **font_size**: size in px, the same for every title whatever its length. Default `76`.
- **primary_color**: text colour. Default `#FFFFFF`.
- **outline_color**: outline colour. Default `#000000`.
- **placement**, **margin**, **x_pos**, **y_pos**: where the text sits (see How It Works).
- **opacity**: 0 to 1. Default `1.0`.
- **start**, **end**: when the text appears and goes away.

## Real World Example
```bash
videobeaux -P text_overlay -i interview.mp4 -o interview_titled.mp4 \
  --text "Dana Ruiz, field researcher" --placement bottom-left --margin 48 \
  --start 3 --end 9
```

## Technical Notes
- `font_size` is in pixels of the video as it is, so the same 76 px title looks smaller on a 4K frame than on a 720p one. For 4K, raise `font_size` (about 2–3× the 1080p value).
- Highlight colour and the kinetic word effect belong to Auto Narrate's captions and are not part of this program.
