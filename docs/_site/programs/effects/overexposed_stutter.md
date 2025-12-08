# overexposed_stutter

## Description
Applies a harsh overexposure flicker combined with stuttering frame cadence, producing an aggressive “corrupted camera” aesthetic.  
The effect mimics the look of damaged digital sensors, broken shutter timing, blown-out highlights, and unstable frame playback.

## Purpose
`overexposed_stutter` is designed for creators who want to:
- simulate digital corruption or overheating camera behavior,  
- create bright white flickers, blown midtones, and clipped highlights,  
- introduce abrupt stutters and dropped-frame jitter,  
- evoke glitchy, broken-device energy,  
- intensify chaos in music videos, experimental film, or montage sequences.

## How It Works
1. **Frame Stutter Injection**  
   The module duplicates, skips, or reorders frames to break cadence and produce jitter.
2. **Overexposure Simulation**  
   Frames are pushed into blown-out white values, simulating:
   - auto-exposure failure,  
   - sensor overload,  
   - corrupted RAW data,  
   - abrupt exposure spikes.
3. **Temporal–Exposure Interplay**  
   The stuttered cadence emphasizes the brightness spikes, giving the impression of a malfunctioning recording pipeline.
4. **Encoding**  
   Final output is encoded with global Videobeaux CRF, preset, and pixel-format settings.

## Program Template
```bash
videobeaux -P overexposed_stutter -i input.mp4 -o output.mp4
```

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
```bash
videobeaux -P overexposed_stutter \
  -i myvideo.mp4 \
  -o overexposed_stutter_styled.mp4
```

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/f7250a1e-3cf5-4826-977a-a5a18b231ddb" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Overexposure may cause highlight clipping; this is intentional.  
- Compression artifacts in bright regions may create additional glitch patterns.  
- Works best on footage with motion, edges, or textured surfaces — flat scenes produce milder results.  
- Aggressive stuttering may make some edits feel chaotic or disorienting (by design).

## Recommended Usage
- High-energy glitch sequences in music videos.  
- Horror, sci-fi, or techno-thriller aesthetics involving corrupted vision.  
- Fast-cut montage transitions.  
- Breakdowns, drops, or rhythmic sync moments in audio-reactive visuals.  
- Distressing clean footage before applying additional filters in a pipeline.

## Quality Tips
- Lower CRF retains clean white clipping; higher CRF adds noisy bloom-like grit.  
- Combine with `bad_contrast` to push black levels down while highlights blow out.  
- Pair with `frame_delay_pro1` for aggressive echo + stutter hybrids.  
- Apply after `convert_dims` if targeting square or portrait loop formats.  
- For extreme looks, chain with `lsd_feedback` or `digital_boss`.

