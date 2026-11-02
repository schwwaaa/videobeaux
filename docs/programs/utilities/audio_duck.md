# audio_duck

## Description
Lowers a music bed whenever the clip's own sound is speaking. The clip's audio is the voice; the music you connect is turned down under it by a sidechain compressor, then the two are mixed. The picture is copied unchanged.

## Purpose
Narration or dialogue sitting on top of background music, where the music has to get out of the way of the words.

## How It Works
1. **Speech detection**
   The clip's audio is the sidechain: whenever its level passes `threshold_db`, the music is compressed.
2. **Duck amount**
   `ratio` sets how hard the music is pulled down while the voice is over `threshold_db`. A ratio of 6 dropped a steady music tone by about 26 dB in a test with a loud voice.
3. **Release**
   `release_ms` is how long the music takes to come back up after the voice stops.
4. **Mix**
   The music is first set to `music_db`, then mixed under the voice. The output is as long as the clip, and the music loops if it is shorter.

## Program Template
```bash
videobeaux -P audio_duck -i narration_clip.mp4 -o output.mp4 --music bed.mp3 --threshold_db -35 --ratio 6
```

## Arguments
- **music**: the music file (any video or audio). Connect it on the canvas.
- **threshold_db**: speech level that triggers ducking, −60 to −10. Default `-35`. For quiet narration, use a lower number.
- **ratio**: how hard the music is ducked, 1–20. Default `6`.
- **release_ms**: milliseconds for the music to return, 50–2000. Default `400`.
- **music_db**: music level before ducking. Default `-6`.

## Real World Example
A quiet interview with a light music bed under it:
```bash
videobeaux -P audio_duck -i interview.mp4 -o interview_bed.mp4 --music light_bed.wav --threshold_db -45 --ratio 4 --music_db -12
```

## Technical Notes
- Measured on a test clip: a 220 Hz music tone dropped about 26 dB while a 440 Hz voice spoke, then came back after the voice stopped.
- The clip needs an audio track, because the voice is what triggers the ducking.
