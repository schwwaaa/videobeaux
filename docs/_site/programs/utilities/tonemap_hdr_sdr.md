# tonemap_hdr_sdr

## Description
Converts HDR footage (PQ/HLG) to SDR using tunable tonemapping curves, preserving highlight detail and color accuracy.

## Purpose
Convert HDR content into display-safe SDR while preserving highlight detail, proper color relationships, and controlled contrast.
This module applies filmic or mathematical tonemap curves to ensure smooth highlight rolloff and SDR-safe luminance.

## How It Works
1. **Linearization**  
   HDR content is converted to linear light using:  
   `zscale=transfer=linear:npl=PEAK`
2. **Tonemap Curve Application**  
   The selected operator (`hable`, `mobius`, `reinhard`, or `clip`) is applied via:  
   `tonemap=algo:desat=value`
3. **SDR Color-Space Mapping**  
   After tonemap, the video is explicitly converted to:  
   - BT.709 primaries  
   - BT.709 transfer  
   - BT.709 matrix  
4. **Dithering & Pixel Format**  
   Dithering prevents banding; pixel format ensures compatibility.
5. **Encoding**  
   Output is encoded using libx264 unless overridden.

## Program Template
    videobeaux -P tonemap_hdr_sdr \
      -i input.mp4 \
      -o output.mp4 \
      --outfile VALUE \
      --algo VALUE \
      --desat VALUE \
      --peak VALUE \
      --dither VALUE \
      --pix_fmt VALUE \
      --x264_preset VALUE \
      --crf VALUE \
      --copy_audio VALUE

## Arguments

- **outfile** — Required SDR output file path.  
- **algo** — Tonemap operator (`hable`, `mobius`, `reinhard`, `clip`).  
- **desat** — Highlight desaturation amount (0.0–1.0).  
- **peak** — Nominal HDR peak brightness in nits (e.g., 400, 600, 1000).  
- **dither** — Dithering mode applied during zscale processing.  
- **pix_fmt** — Output pixel format (e.g., `yuv420p`, `yuv422p10le`).  
- **x264_preset** — Encoding speed/quality preset (`slow`, `medium`, `fast`, etc.).  
- **crf** — Constant Rate Factor controlling video quality (lower = higher quality).  
- **copy_audio** — When set, audio is copied instead of re-encoded.

## Real World Example
    videobeaux -P tonemap_hdr_sdr \
      -i myvideo.mp4 \
      -o tonemap_hdr_sdr_styled.mp4 \
      --outfile EXAMPLE \
      --algo EXAMPLE \
      --desat EXAMPLE \
      --peak EXAMPLE \
      --dither EXAMPLE \
      --pix_fmt EXAMPLE \
      --x264_preset EXAMPLE \
      --crf EXAMPLE \
      --copy_audio EXAMPLE

## Technical Notes
- zscale handles linearization and SDR color mapping with high accuracy.
- Explicit BT.709 tagging avoids incorrect interpretation by media players.
- `--peak` significantly affects highlight rolloff; adjust depending on source mastering.  
- Dithering is essential for avoiding banding when outputting 8-bit formats.  
- 10-bit pixel formats increase headroom for gradients and grading workflows.

## Recommended Usage
- Creating SDR masters from HDR originals.
- Preparing high-quality web deliverables (YouTube, Vimeo, TikTok).
- Producing SDR screeners or festival submissions that disallow HDR.
- Generating SDR previews for HDR editing environments.

## Quality Tips
- Use CRF **14–18** for high-quality SDR output.
- `hable` generally provides the best filmic highlight rolloff.
- For oversaturated HDR highlights, increase `--desat` to 0.15–0.35.
- Use **yuv422p10le** when creating grading intermediates.
- Combine with `gamma_fix` for refined SDR brightness/contrast normalization.
