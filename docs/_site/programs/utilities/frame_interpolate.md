# frame_interpolate
:contentReference[oaicite:1]{index=1}

## Description
Generates smooth slow-motion or higher-FPS video by creating intermediate frames using motion-compensated interpolation.

## Purpose
`frame_interpolate` creates additional frames between existing frames to produce:
- ultra-smooth slow motion,
- high-FPS versions of footage,
- stabilized motion flow for VR, gaming, or cinematic sequences,
- visually enhanced motion for archival or restoration tasks.

It supports multiple interpolation engines (RIFE, DAIN, FFmpeg Minterpolate), allowing both high-quality deep-learning interpolation and traditional optical-flow methods.

## How It Works
1. **Engine Selection**  
   Choose interpolation backend:
   - `rife` (AI-based, fast, high quality)  
   - `dain` (AI-based, depth-aware interpolation)  
   - `ffmpeg` (classical minterpolate optical flow)
2. **Interpolation Strategy**
   - **fps**: Defines the exact output frame rate.  
   - **multiplier**: Doubles, triples, or otherwise multiplies the existing frame count.
3. **Optical Flow Configuration** (FFmpeg engine)
   - `mi_mode`, `me_mode`, `mc_mode` configure interpolation, motion estimation, and motion compensation logic.
   - `vsbmc` enables virtual scene-based motion compensation.
   - `scd` toggles scene-change detection to prevent warping across hard cuts.
4. **AI Engine Configuration**
   - `rife_bin` and `dain_bin` specify executable paths or binaries for AI interpolation engines.
5. **Encoding**
   Output is encoded using CRF + preset settings, with optional audio copying.

## Program Template
    videobeaux -P frame_interpolate \
      -i input.mp4 \
      -o output.mp4 \
      --outfile VALUE \
      --engine VALUE \
      --fps VALUE \
      --multiplier VALUE \
      --mi_mode VALUE \
      --me_mode VALUE \
      --mc_mode VALUE \
      --vsbmc VALUE \
      --scd VALUE \
      --x264_preset VALUE \
      --crf VALUE \
      --copy_audio VALUE \
      --rife_bin VALUE \
      --dain_bin VALUE

## Arguments

- **outfile** — Output filename for the interpolated result.  
- **engine** — Interpolation engine (`rife`, `dain`, `ffmpeg`).  
- **fps** — Target frames per second for output video.  
- **multiplier** — Multiplies frame count (e.g., 2×, 4×, 8×).  
- **mi_mode** — Minterpolate mode (FFmpeg engine).  
- **me_mode** — Motion estimation algorithm.  
- **mc_mode** — Motion compensation method.  
- **vsbmc** — Enables scene-based motion compensation.  
- **scd** — Scene-change detection toggle.  
- **x264_preset** — Encoder preset for libx264.  
- **crf** — Constant Rate Factor controlling video quality.  
- **copy_audio** — Copies original audio without re-encoding.  
- **rife_bin** — Path to RIFE binary for AI interpolation.  
- **dain_bin** — Path to DAIN binary for AI interpolation.

## Real World Example
    videobeaux -P frame_interpolate \
      -i myvideo.mp4 \
      -o frame_interpolate_styled.mp4 \
      --outfile EXAMPLE \
      --engine EXAMPLE \
      --fps EXAMPLE \
      --multiplier EXAMPLE \
      --mi_mode EXAMPLE \
      --me_mode EXAMPLE \
      --mc_mode EXAMPLE \
      --vsbmc EXAMPLE \
      --scd EXAMPLE \
      --x264_preset EXAMPLE \
      --crf EXAMPLE \
      --copy_audio EXAMPLE \
      --rife_bin EXAMPLE \
      --dain_bin EXAMPLE

## Technical Notes
- AI engines (RIFE/DAIN) generally produce the smoothest and least artifact-prone interpolation.  
- FFmpeg’s `minterpolate` can introduce warping around fast motion or scene cuts—use `scd=true` to reduce artifacts.  
- High multiplier values (4×, 8×) should be paired with AI engines for best results.  
- GPU acceleration may be required for realtime or high-resolution AI interpolation.  
- Audio is not stretched—slow-motion audio must be handled separately if desired.

## Recommended Usage
- Slow-motion cinematic sequences.  
- High-FPS playback for sports, action, and dance footage.  
- Animation smoothing for stylized or experimental outputs.  
- Restoring archival footage to modern frame rates (e.g., 12fps → 24fps).  
- Motion interpolation for VR or interactive displays.

## Quality Tips
- Prefer RIFE for general-purpose high-quality interpolation.  
- Use DAIN when accuracy around depth edges is important.  
- Avoid interpolating across scene cuts; enable `scd`.  
- Start with CRF **16–20**; lower values for grading-quality output.  
- Test different multipliers—sometimes 2× looks more natural than 4×.
