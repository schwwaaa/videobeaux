# subtitle_burn

## Description
Burns an `.srt` subtitle file into the picture, styled: the font, size, text and outline colours, and where the subtitles sit. Uses ffmpeg's subtitles filter, which is built on libass.

## Purpose
Subtitles for a video that will be posted somewhere that does not take a separate subtitle track, such as social media.

## How It Works
1. **The file**
   `srt` is the subtitle file. Its timings are read from the file, so no timing is set in the program.
2. **Style**
   `font` is an installed font name. `font_size` is in pixels. `primary_color` is the text, and `outline_color` and `outline` set the border.
3. **Position**
   `position` is `bottom` (default), `middle`, or `top`. `margin` is the distance from the top or bottom edge.
4. **Encoding**
   The video is re-encoded as H.264. The audio is copied unchanged.

Captburn makes captions from the speech itself. Use this program when you already have the subtitle file.

## Program Template
```bash
videobeaux -P subtitle_burn -i input.mp4 -o output.mp4 --srt subtitles.srt --position bottom --font_size 40
```

## Arguments
- **srt**: the `.srt` subtitle file.
- **font**: an installed font name. Default `Arial`.
- **font_size**: size in pixels. Default `24`.
- **primary_color**: text colour. Default `#FFFFFF`.
- **outline_color**: outline colour. Default `#000000`.
- **outline**: outline width in pixels, 0–6. Default `2`.
- **position**: `bottom`, `middle`, or `top`. Default `bottom`.
- **margin**: distance from the top or bottom edge in pixels. Default `30`.

## Real World Example
Burning English subtitles into a foreign-language clip, in yellow with a heavy outline:
```bash
videobeaux -P subtitle_burn -i clip_fr.mp4 -o clip_en.mp4 --srt clip_en.srt --primary_color "#FFE500" --outline 3 --font_size 44
```

## Technical Notes
- The file name can contain spaces or apostrophes; the program copies the file to a temporary folder first.
- The font must be installed on the computer doing the rendering.
