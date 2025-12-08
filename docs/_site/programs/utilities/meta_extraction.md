# meta_extraction

## Description
Extracts detailed metadata—such as codecs, bitrates, dimensions, color information, loudness, black-frame metrics, and stream structure—from any media file.

## Purpose
`meta_extraction` is designed to provide deep insight into media characteristics for:
- archival workflows,
- QC diagnostics,
- automated processing pipelines,
- research or analytics tasks,
- downstream editing or transcoding decisions.

It can scan frames, detect black segments, analyze loudness, and output structured metadata for additional tools.

## How It Works
1. **Stream Inspection**  
   Reads the container and stream-level metadata (codec, resolution, color space, duration, bitrates, etc.).
2. **Frame Sampling**  
   - `sample_frames` sets how many frames to analyze.  
   - `sample_stride` controls spacing between sampled frames.  
   - `sample_limit` prevents excessive scanning on long videos.
3. **Black Frame Detection**  
   If enabled, black detection evaluates frames for luminance thresholds.  
   - `black_pic_th` tunes sensitivity.  
   - `black_dur_min` sets minimum black duration to report.  
   - `blackdetect` toggles the feature.
4. **Loudness Analysis**  
   When enabled, checks LU, LRA, and peak values for broadcast loudness compliance.
5. **Output**  
   Metadata is written to a structured file (JSON or text depending on implementation).

## Program Template
    videobeaux -P meta_extraction \
      -i input.mp4 \
      -o output.mp4 \
      --outputfile VALUE \
      --sample_frames VALUE \
      --sample_stride VALUE \
      --sample_limit VALUE \
      --blackdetect VALUE \
      --black_pic_th VALUE \
      --black_dur_min VALUE \
      --loudness VALUE

## Arguments

- **outputfile** — Name of the metadata output file produced by the scan.  
- **sample_frames** — Total number of frames to sample for inspection.  
- **sample_stride** — Number of frames skipped between each analyzed frame.  
- **sample_limit** — Maximum frame count allowed during sampling.  
- **blackdetect** — Enables detection of black frames and black segments.  
- **black_pic_th** — Pixel-level threshold for determining whether a frame is considered black.  
- **black_dur_min** — Minimum duration (seconds) of black required to register as a black segment.  
- **loudness** — Enables loudness analysis (LUFS, LRA, true peak).

## Real World Example
    videobeaux -P meta_extraction \
      -i myvideo.mp4 \
      -o meta_extraction_styled.mp4 \
      --outputfile EXAMPLE \
      --sample_frames EXAMPLE \
      --sample_stride EXAMPLE \
      --sample_limit EXAMPLE \
      --blackdetect EXAMPLE \
      --black_pic_th EXAMPLE \
      --black_dur_min EXAMPLE \
      --loudness EXAMPLE

## Technical Notes
- Metadata extraction is extremely fast because only sampled frames are examined.  
- Excessive `sample_frames` or low `sample_stride` may increase scan time.  
- Black detection is luminance-based; noisy or low-light footage may require adjusted thresholds.  
- Loudness metrics follow broadcast-standard measurement curves.  
- Great for building metadata catalogs or dashboards.

## Recommended Usage
- Preflight analysis before encoding or delivery.  
- QC checks for broadcast, festival, or archival compliance.  
- Automated pipelines needing structural insight into media files.  
- Generating metadata for UI previews, asset managers, or machine-learning datasets.

## Quality Tips
- Use `black_pic_th` between **0.05–0.10** for most SDR footage.  
- Increase `sample_stride` to speed up scans on long files.  
- Keep `sample_limit` reasonable to avoid unnecessary overhead.  
- Enable `loudness` for interview, dialog, or broadcast deliverables.
