# audio_denoise

## Description
Takes hiss and hum out of speech. A high-pass filter removes low rumble below the voice, then ffmpeg's FFT denoiser (afftdn) lowers the background noise it finds. The picture is copied untouched.

## Purpose
Recordings made in a room with a fan, a laptop, or a noisy microphone preamp.

## How It Works
1. **Rumble**
   `highpass` cuts everything below that frequency in hertz. Human speech sits mostly above about 80 Hz, so this clears hum and handling noise without thinning the voice. `0` turns it off.
2. **Denoiser**
   `noise_floor` is the level of the background noise, in dB. `reduction` is how far that noise is pushed down, in dB.
3. **Picture**
   The video is copied with no re-encode.

## Program Template
```bash
videobeaux -P audio_denoise -i input.mp4 -o output.mp4 --reduction 12 --noise_floor -25 --highpass 80
```

## Arguments
- **reduction**: how far the noise is reduced, 0–40 dB. Default `12`.
- **noise_floor**: the background-noise level, −80 to −20 dB. Default `-25`.
- **highpass**: rumble cut-off in Hz, 0 for off. Default `80`.

## Real World Example
A phone interview with a fan running in the room:
```bash
videobeaux -P audio_denoise -i phone_interview.mp4 -o interview_clean.mp4 --reduction 18 --highpass 120
```

## Technical Notes
- Too much reduction makes voices sound watery. Start at 12 dB and move up while listening.
- Run this before Loudness Normalize so the level is set on the cleaned sound.
