# thumbs

## Description
Generates thumbnails or contact sheets by sampling frames at chosen intervals for previews, galleries, or QC review.

## Purpose
The `thumbs` program creates frame-based preview images from video sources.  
It can generate:
- evenly spaced thumbnails,
- scene-change–based extractions,
- tiled contact sheets,
- annotated or timestamped frames for analysis,  
making it ideal for QC, archives, design references, and preview libraries.

## How It Works
1. **Frame Sampling**  
   Choose between:
   - `fps` sampling (uniform intervals), or  
   - `scene` detection (generate thumbnails where major scene changes occur).
2. **Scene Thresholding**  
   `scene_threshold` determines sensitivity to cuts, edits, or brightness shifts.
3. **Layout & Tiling**  
   - `tile` controls grid layout (e.g., `5x5` contact sheets).  
   - `scale` sets thumbnail size.
4. **Labels & Timestamps**  
   - `timestamps` includes frame timestamps.  
   - `label` adds custom text per thumbnail.
5. **Styling Options**  
   Background color, margins, padding, and font selection allow branding/QC annotation.
6. **Export Options**  
   - Output directory (`outdir`)  
   - Output filename (`outputfile`)  
   - Image format (JPEG/PNG)  
   - JPEG quality control  

## Program Template
    videobeaux -P thumbs \
      -i input.mp4 \
      -o output.mp4 \
      --fps VALUE \
      --scene VALUE \
      --scene_threshold VALUE \
      --tile VALUE \
      --scale VALUE \
      --timestamps VALUE \
      --label VALUE \
      --fontfile VALUE \
      --bg VALUE \
      --margin VALUE \
      --padding VALUE \
      --outdir VALUE \
      --outputfile VALUE \
      --image_format VALUE \
      --jpeg_quality VALUE

## Arguments

- **fps** — Frames per second to sample for thumbnail extraction.  
- **scene** — Enables scene-detection-based thumbnail generation (`true/false`).  
- **scene_threshold** — Sensitivity for detecting scene cuts. Lower = more cuts detected.  
- **tile** — Contact sheet layout (e.g., `4x4`, `6x8`).  
- **scale** — Size of each thumbnail (percentage or pixel dimension).  
- **timestamps** — Adds timestamps onto each thumbnail (`true/false`).  
- **label** — Custom label text rendered onto each frame.  
- **fontfile** — Path to a custom font file for labels.  
- **bg** — Background color for contact sheets (CSS-style hex or color name).  
- **margin** — Outer margin around thumbnails or the full sheet.  
- **padding** — Spacing between individual thumbnails.  
- **outdir** — Directory where generated images will be saved.  
- **outputfile** — Base name for the contact sheet or exported images.  
- **image_format** — Output format (`jpg`, `png`, etc.).  
- **jpeg_quality** — JPEG quality (0–100).

## Real World Example
    videobeaux -P thumbs \
      -i myvideo.mp4 \
      -o thumbs_styled.mp4 \
      --fps 1 \
      --scene false \
      --scene_threshold 0.4 \
      --tile 5x5 \
      --scale 320 \
      --timestamps true \
      --label "Preview Sheet" \
      --fontfile /path/to/font.ttf \
      --bg "#000000" \
      --margin 20 \
      --padding 10 \
      --outdir thumbs_output \
      --outputfile contactsheet \
      --image_format jpg \
      --jpeg_quality 90

## Technical Notes
- Scene detection uses FFmpeg’s `select='gt(scene,threshold)'` filter logic.  
- High `tile` counts produce dense sheets but increase render time.  
- `scale` affects memory usage when generating many thumbnails.  
- Custom fonts must be accessible to ffmpeg’s `drawtext` filter.  
- Using PNG avoids compression artifacts; JPEG is faster & smaller.

## Recommended Usage
- QC review workflows to quickly scan for artifacts.  
- Preview libraries for editors, designers, or curators.  
- Thumbnail generation for apps, web galleries, or dataset creation.  
- Scene-change visualization for film analysis.

## Quality Tips
- For clean contact sheets, use PNG for lossless quality.  
- For large batches, use JPEG (quality 80–90) for faster export.  
- Adjust `scene_threshold` to balance between too many vs. too few scene hits.  
- Use higher `scale` values for detailed thumbnails, smaller for overview sheets.
