# loudness_normalize

## Description
Evens out how loud the sound is. The audio is brought to a target loudness, measured in LUFS (the EBU R128 standard), with a true-peak ceiling, so quiet clips and loud clips land at the same level.

## Purpose
Clips from different cameras and phones sit at different volumes. Normalising them makes a set of videos play at a consistent level.

## How It Works
1. **Target loudness**
   `target` is the average loudness to aim for. `-16 LUFS` is the usual level for online video and podcasts; `-23 LUFS` is the broadcast standard.
2. **Peak ceiling**
   `true_peak` is the loudest peak allowed after normalising. `-1.5` leaves headroom so the sound cannot clip.
3. **Loudness range**
   `lra` is how much the loudness may vary across the clip. A smaller range is more even but can sound squashed.
4. **Picture and sound**
   The picture is copied untouched. The audio is re-encoded as AAC at 48 kHz.

## Program Template
```bash
videobeaux -P loudness_normalize -i input.mp4 -o output.mp4 --target -16 --true_peak -1.5
```

## Arguments
- **target**: target loudness in LUFS. Default `-16`.
- **true_peak**: peak ceiling in dBTP. Default `-1.5`.
- **lra**: loudness range in LU. Default `11`.

## Real World Example
A quiet interview and a loud b-roll clip, both brought to podcast level before editing together:
```bash
videobeaux -P loudness_normalize -i interview.mp4 -o interview_level.mp4 --target -16
```

## Technical Notes
- This is single-pass normalisation. Very dynamic material can sound pumped; a larger `lra` relaxes that.
- A clip with no audio stops with a message.
