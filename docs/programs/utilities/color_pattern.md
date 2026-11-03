# color_pattern

## Description
Makes a video of a solid colour, a gradient, a checkerboard, SMPTE colour bars, a test pattern, an RGB ramp or noise, for as many seconds as you set. With no input video it stands alone: connect it straight to Output. With an input video connected, it can lay the picture over the video or behind it (see Input below).

## Purpose
A plain background, a colour card, a test chart for checking a display or an encode, or a noise source for a glitch chain.

## How It Works
1. **Pattern**
   `Solid colour` fills the frame with `color`. `Gradient (colour to black)` fades from `color` to black across the width. `Checkerboard` alternates `color` and black squares. The bars, test pattern, RGB ramp and noise have their own colours.
2. **Size**
   The same as Convert Dims: a named `preset`, or `custom` with `width` and `height`.
3. **Length and rate**
   `seconds` sets the length and `fps` the frame rate.

## Program Template
```bash
videobeaux -P color_pattern -o background.mp4 --pattern "Solid colour" --color "#0040FF" --seconds 10 --preset 1080p
```

## Input
- **Make a picture** (default): the picture alone, for `seconds`, at the chosen size. Any connected input is ignored.
- **Over the input**: the input video is the background and the picture is laid on top of it, at `opacity`. The output has the input's size, length and sound.
- **Behind the input**: the picture is underneath the input video, at `opacity`. An ordinary video is opaque, so the picture does not show. It shows only where the input is transparent (for example a clip with an alpha channel, such as a ProRes 4444 or a QuickTime Animation file with alpha).

With an input connected, `preset`, `width`, `height`, `seconds` and `fps` are not used.

## Arguments
- **mode**: `Make a picture` (default), `Over the input`, or `Behind the input`.
- **opacity**: how strong the picture is over or behind the input, 0 to 1. Default `1`. Only used with an input.
- **pattern**: `Solid colour` (default), `Gradient (colour to black)`, `Checkerboard`, `SMPTE colour bars`, `SMPTE HD colour bars`, `Test pattern`, `RGB ramp`, `Noise`.
- **color**: hex colour such as `#FF0000`, used by Solid colour, Gradient and Checkerboard. Default `#FF0000`.
- **seconds**: length in seconds, with no input. Default `5`.
- **fps**: frame rate, with no input. Default `30`.
- **preset**, **width**, **height**: the size, as in Convert Dims, with no input. Default `1080p`.

## Presets in the app
The library buttons set a pattern and colour in one click: Colour bars, HD colour bars, Test pattern, Black, White, Red, Green, Blue, Yellow, and Red / black checks.

## Technical Notes
- Measured on a test run: solid red came out as red (252, 0, 0); the gradient ran from red at the left to black at the right; the checkerboard had only 0 and 255 levels; the SMPTE bars had the expected grey and blue.
- Measured on a player that reads the BT.709 tags: white comes out 255, red 254. Over the input at full opacity, a red picture over grey gives red; at half opacity it gives about 190, 64, 63.
- Without an input the output is H.264 with no sound track. With an input, the input's sound is kept.
