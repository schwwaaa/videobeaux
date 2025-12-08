# gamma_fix
:contentReference[oaicite:1]{index=1}

## Description
Normalizes gamma, brightness, and exposure levels for broadcast-safe or web-safe consistency across diverse footage.

## Purpose
`gamma_fix` is designed to correct inconsistent exposure, contrast, and gamma shifts that often appear when mixing footage from multiple cameras, phones, archives, or lighting conditions.  
It provides predictable luminance normalization suitable for:
- web delivery,
- broadcast pipelines,
- archival stabilization,
- color prep before LUTs or grading.

## How It Works
1. **Luma Analysis**  
   The program evaluates input brightness and computes adjustments toward `target_yavg`.
2. **Contrast Shaping**  
   `min_contrast` and `max_contrast` constrain the allowed contrast stretch, preventing overcorrection.
3. **Gamma Adjustment**  
   A user-specified gamma curve can brighten or darken midtones without clipping shadows or highlights.
4. **Saturation Shaping**  
   `sat` provides global saturation control to compensate for washed-out or overly vivid sources.
5. **Legalization**  
   When enabled, `legalize` ensures output luminance stays within broadcast-safe IRE ranges.
6. **Encoding**  
   Output is encoded using the selected codec, preset, and CRF.

## Program Template
    videobeaux -P gamma_fix \
      -i input.mp4 \
      -o output.mp4 \
      --target_yavg VALUE \
      --min_contrast VALUE \
      --max_contrast VALUE \
      --gamma VALUE \
      --sat VALUE \
      --legalize VALUE \
      --vcodec VALUE \
      --crf VALUE \
      --preset VALUE \
      --acodec VALUE \
      --ab VALUE

## Arguments

- **target_yavg** — Target brightness (luma average) to normalize toward.  
- **min_contrast** — Minimum allowed contrast level after adjustment.  
- **max_contrast** — Maximum allowed contrast level after adjustment.  
- **gamma** — Gamma correction multiplier for shaping midtones.  
- **sat** — Saturation adjustment factor.  
- **legalize** — Ensures output levels conform to broadcast-safe luminance ranges.  
- **vcodec** — Video codec to use for output (e.g., `libx264`).  
- **crf** — Constant Rate Factor controlling video quality.  
- **preset** — Encoding speed/quality preset.  
- **acodec** — Audio codec.  
- **ab** — Audio bitrate.

## Real World Example
    videobeaux -P gamma_fix \
      -i myvideo.mp4 \
      -o gamma_fix_styled.mp4 \
      --target_yavg EXAMPLE \
      --min_contrast EXAMPLE \
      --max_contrast EXAMPLE \
      --gamma EXAMPLE \
      --sat EXAMPLE \
      --legalize EXAMPLE \
      --vcodec EXAMPLE \
      --crf EXAMPLE \
      --preset EXAMPLE \
      --acodec EXAMPLE \
      --ab EXAMPLE

## Technical Notes
- Gamma correction subtly adjusts midtone brightness without flattening highlights.  
- Luma averaging helps normalize footage from mixed sources with inconsistent exposure.  
- Excessive contrast stretching may introduce noise—use moderate ranges for natural results.  
- Broadcast-safe legalization prevents clipped peaks in deliverables meant for TV or streaming platforms.  
- Saturation adjustments apply globally; fine-grained color correction should be done in grading tools.

## Recommended Usage
- Normalizing multi-camera footage before editing.  
- Preparing consistent brightness for LUT workflows or grading.  
- Fixing underexposed or flat-looking archive material.  
- Making levels compliant for broadcast delivery requirements.

## Quality Tips
- Start with small gamma adjustments for natural tonal shifts.  
- Set `target_yavg` close to typical mid-gray values (around 40–55% normalized luma).  
- Use moderate `sat` boosts (1.05–1.15) to avoid color clipping.  
- Lower CRF (14–18) retains quality when making heavy tonal corrections.  
- Always inspect waveform before and after applying legalization.
