# crossmosh

## Description
A controlled datamoshing engine that manipulates motion vectors, frame ordering, and predictive compression structures to create stylized glitch-drift distortions.  
Unlike chaotic or accidental datamoshing, `crossmosh` provides intentional control over how macroblocks bleed, drift, smear, or desynchronize across frames.

## Purpose
`crossmosh` is designed for artists who want to:
- create predictable or semi-controlled datamosh effects,  
- push temporal motion-vector corruption while avoiding full-stream collapse,  
- blend A/B sources for hybrid glitch states,  
- generate drifting smear artifacts characteristic of broken P-frames and missing I-frames,  
- build glitch art sequences without external tools or hand-edited GOP destruction.

It is ideal for music videos, experimental film, VJ loops, and any stylized glitch aesthetic.

## How It Works
1. **Input Streams**  
   Two sources may be involved:
   - **primary input** via `-i`  
   - **secondary / cross-input** via `--b_input`  
2. **Predictive Frame Manipulation**  
   The module alters GOP structure, destroys or delays keyframes, or selectively reuses motion vectors from one stream to infect the other.
3. **Mode-Based Behavior**  
   `--mode` defines the style of the mosh:
   - smearing,  
   - drift,  
   - cross-pollination,  
   - decay-driven glitch propagation.
4. **Decay & Blending**  
   - `--decay` controls how long corrupted vectors persist.  
   - `--blend` controls how heavily A and B frames influence each other.
5. **GOP / Codec Control**  
   The choice of codec and GOP size directly impacts artifact shape and stability.

## Program Template
    videobeaux -P crossmosh \
      -i input.mp4 \
      -o output.mp4 \
      --b_input VALUE \
      --outfile VALUE \
      --codec VALUE \
      --qscale VALUE \
      --gop VALUE \
      --keep_temp VALUE \
      --mode VALUE \
      --frames VALUE \
      --decay VALUE \
      --blend VALUE

## Arguments

- **b_input** — Optional secondary video input used for cross-mapping and motion-vector grafting.  
- **outfile** — Output filename created during temporary processing.  
- **codec** — Codec used for mosh-friendly transcoding (e.g., MPEG-4, H.264 with low keyframe frequency).  
- **qscale** — Quantizer scale value; lower = cleaner blocks, higher = more chaotic degradation.  
- **gop** — Keyframe interval. Long GOPs enable long drifting smears; short GOPs reset more frequently.  
- **keep_temp** — If enabled, preserves intermediate files for debugging or reuse.  
- **mode** — Defines the moshing behavior (drift, smear, cross-infect, or other available styles).  
- **frames** — Number of frames to process or extend during the mosh.  
- **decay** — Controls how motion-vector corruption fades or persists.  
- **blend** — Controls mixing strength between A and B inputs during crossmosh operations.

## Real World Example
    videobeaux -P crossmosh \
      -i myvideo.mp4 \
      -o crossmosh_styled.mp4 \
      --b_input EXAMPLE \
      --outfile EXAMPLE \
      --codec EXAMPLE \
      --qscale EXAMPLE \
      --gop EXAMPLE \
      --keep_temp EXAMPLE \
      --mode EXAMPLE \
      --frames EXAMPLE \
      --decay EXAMPLE \
      --blend EXAMPLE

## Program Output
_Program output video not yet linked._

## Technical Notes
- Datamoshing behavior is extremely sensitive to codec and GOP selection — MPEG-4 with long GOPs typically produces more dramatic artifacts.  
- If using a second input (`--b_input`), mismatched resolutions may create unpredictable smear patterns.  
- `qscale` strongly influences macroblock deformation and drift persistence.  
- Temporary files may be required for multi-stage moshing; use `--keep_temp` to preserve them for debugging.  
- Excessive decay or extreme blending may cause full frame collapse — this can be desirable depending on your aesthetic.

## Recommended Usage
- Music videos requiring controlled glitch cascades.  
- VJ loops and live visual sets that leverage drifting corruption.  
- Collage work blending two unrelated videos via motion-vector infection.  
- Experimental films exploring digital decay, compression failure, and structural distortion.

## Quality Tips
- Lower `qscale` (e.g., 2–5) for smoother block smearing; higher (10–20) for chaotic chunking.  
- Longer GOPs (100–300+) produce dramatic streak-based artifacts across many frames.  
- Use `blend` modestly when incorporating a B-source; too high can obliterate A-source contours.  
- For highly controllable decay, adjust both `frames` and `decay` interactively while testing small clips.  
- For sharp outlines within a glitch, pre-process with `gamma_fix` or `lut_apply` before moshing.
