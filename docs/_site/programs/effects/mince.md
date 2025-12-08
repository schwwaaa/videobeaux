# mince

## Description
A fast, precise segment extractor and reassembler that slices video into parts and recombines them with frame accuracy.  
`mince` can cut, shuffle, normalize, re-encode, or stitch segments while preserving sync, enabling procedural editing, glitch slicing, and automated timeline reconstruction.

## Purpose
`mince` is designed for creators who want to:
- cut videos into segments deterministically or randomly,  
- shuffle or rearrange cuts with predictable results,  
- normalize segment formats for consistent downstream processing,  
- create procedural micro-edits, stutters, or rhythmic staccato patterns,  
- apply glitch, jump-cut, or timeline–reconstruction workflows at scale,  
- extract or trim clips with high accuracy while choosing how to re-encode.

## How It Works
1. **Mode Selection (`--mode`)**  
   Defines how segments are generated or chosen:
   - deterministic slicing,  
   - random slicing controlled by seed,  
   - engine-based segmentation strategies.
2. **Randomization (`--seed`)**  
   Ensures reproducibility of shuffled or randomized edits.
3. **Engine (`--engine`)**  
   Different engines may determine how cuts are generated (e.g., time-based, detection-based, algorithmic).
4. **Normalization (`--normalize` + related options)**  
   If enabled, each segment is re-encoded using:
   - `norm_vcodec`  
   - `norm_crf`  
   - `norm_preset`  
   ensuring consistent dimensions, codecs, and quality levels.
5. **Reconstruction**  
   Segments are concatenated in the final order (based on engine or mode).
6. **Output Encoding**  
   After assembly, the final output is encoded using user-selected codecs, presets, and flags.

## Program Template
```bash
videobeaux -P mince \
  -i input.mp4 \
  -o output.mp4 \
  --mode VALUE \
  --seed VALUE \
  --engine VALUE \
  --normalize VALUE \
  --size VALUE \
  --fit VALUE \
  --fps VALUE \
  --pixfmt VALUE \
  --ar VALUE \
  --ac VALUE \
  --norm_vcodec VALUE \
  --norm_crf VALUE \
  --norm_preset VALUE \
  --vcodec VALUE \
  --acodec VALUE \
  --crf VALUE \
  --preset VALUE \
  --faststart VALUE \
  --fallback_reencode VALUE \
  --decode_tolerant VALUE \
  --hard_trim VALUE
```

## Arguments

- **mode** — Defines slicing/assembly logic (deterministic, random, pattern-based).  
- **seed** — Ensures reproducible random operations.  
- **engine** — Selects segmentation strategy.  
- **normalize** — Enables re-encoding of each segment for consistency.  
- **size** — Target resolution for normalized clips.  
- **fit** — Fit behavior for scaling (e.g., pad, fill, stretch).  
- **fps** — Override frame rate during normalization.  
- **pixfmt** — Pixel format used in normalized output.  
- **ar** — Audio sample rate.  
- **ac** — Number of audio channels.  
- **norm_vcodec** — Video codec for normalization step.  
- **norm_crf** — CRF quality for normalized clips.  
- **norm_preset** — Encoding speed for normalization.  
- **vcodec** — Codec for final output render.  
- **acodec** — Audio codec for final output.  
- **crf** — CRF for final encoding quality.  
- **preset** — Encoding speed for final output.  
- **faststart** — Enables MP4 faststart flag when applicable.  
- **fallback_reencode** — Re-encode segments if passthrough fails.  
- **decode_tolerant** — Allow lenient decoding of problematic segments.  
- **hard_trim** — Enforce exact cut boundaries rather than safe cutting.

## Real World Example
```bash
videobeaux -P mince \
  -i myvideo.mp4 \
  -o mince_styled.mp4 \
  --mode EXAMPLE \
  --seed EXAMPLE \
  --engine EXAMPLE \
  --normalize EXAMPLE \
  --size EXAMPLE \
  --fit EXAMPLE \
  --fps EXAMPLE \
  --pixfmt EXAMPLE \
  --ar EXAMPLE \
  --ac EXAMPLE \
  --norm_vcodec EXAMPLE \
  --norm_crf EXAMPLE \
  --norm_preset EXAMPLE \
  --vcodec EXAMPLE \
  --acodec EXAMPLE \
  --crf EXAMPLE \
  --preset EXAMPLE \
  --faststart EXAMPLE \
  --fallback_reencode EXAMPLE \
  --decode_tolerant EXAMPLE \
  --hard_trim EXAMPLE
```

## Program Output
_Program output video not yet linked._

## Technical Notes
- `mince` can create either chaotic glitch edits or clean, broadcast-ready trims depending on parameters.  
- Normalization ensures all segments share identical codec and dimensions, avoiding concat failures.  
- Engines may behave differently depending on content—some may be time-based, others content-aware.  
- Overusing hard trimming may create audio pops or stray frames depending on source structure.  
- `fallback_reencode` prevents pipeline breaks when encountering incompatible segments.

## Recommended Usage
- Procedural micro-edits for music videos.  
- Rapid stutter-cut effects.  
- Timeline reordering and random jump edits.  
- Creating equal-length slices for collage systems like Lagkage.  
- Extracting reusable clip banks in normalized formats.

## Quality Tips
- Use a consistent `norm_vcodec` + `norm_crf` to avoid codec mismatch in concat operations.  
- For heavy glitch aesthetics, set high randomness with a fixed seed to remain reproducible.  
- For broadcast-safe trimming, disable randomness and use exact timing with `hard_trim`.  
- Lower CRF and high-quality presets yield smoother normalized segments for recomposition.  
- Use `decode_tolerant` when working with damaged or odd-format inputs.

