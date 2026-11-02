# audio_visualizer

## Description
Draws the sound over the picture: a waveform line, or a spectrum of bars, in a strip along the bottom or top of the frame, or across the whole picture.

## Purpose
Music clips, podcast videos and audiograms: the sound becomes visible without a separate editor.

## How It Works
1. **The drawing**
   `wave` draws the waveform as a centred line that follows the loudness. `bars` draws the spectrum: one bar per band of pitches, on a logarithmic scale so the low end is not squashed.
2. **The strip**
   `position` is `bottom`, `top` or `full`. For a strip, `height` is a percentage of the frame height (5–100). For `full` the drawing covers the picture.
3. **Opacity**
   The drawing's black background is made transparent, and `opacity` sets how solid the line or bars are.
4. **Encoding**
   The video is re-encoded as H.264 and the audio as AAC at 192 kbit/s.

## Program Template
```bash
videobeaux -P audio_visualizer -i input.mp4 -o output.mp4 --style wave --position bottom --height 20
```

## Arguments
- **style**: `wave` (default) or `bars`.
- **position**: `bottom` (default), `top`, or `full`.
- **height**: strip height as a percent of the frame, 5–100. Default `20`. Ignored for `full`.
- **color**: colour of the line or bars. Default `#FFFFFF`.
- **opacity**: 0 to 1. Default `0.9`.

## Real World Example
```bash
videobeaux -P audio_visualizer -i podcast_clip.mp4 -o podcast_wave.mp4 \
  --style bars --position bottom --height 25 --color "#FF8800"
```

## Technical Notes
- The video needs an audio track. A clip with no sound stops with a message.
- The drawing is sized to the video, so a 4K clip gets a 4K strip.
