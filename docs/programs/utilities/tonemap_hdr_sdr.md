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

## Program Arguments
- `outfile`
- `algo`
- `desat`
- `peak`
- `dither`
- `pix_fmt`
- `x264_preset`
- `crf`
- `copy_audio`

### Argument Details
| Argument | Meaning |
|---------|---------|
| **outfile** | Required SDR output file path. |
| **algo** | Tonemap operator (`hable`, `mobius`, `reinhard`, `clip`). |
| **desat** | Highlight desaturation (0.0–1.0). |
| **peak** | HDR nominal peak (nits). |
| **dither** | Gradient dithering mode. |
| **pix_fmt** | Output pixel format (e.g., yuv420p). |
| **x264_preset** | Encoding speed/quality preset. |
| **crf** | CRF for video quality. |
| **copy_audio** | If set, audio is not re-encoded. |

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
- Uses zscale for color management & linearization.
- Explicit BT.709 tagging ensures consistent SDR playback.
- `--peak` controls linearization; typical values: 400–1000 nits.
- Dithering recommended for gradient-heavy content.
- 10-bit pixel formats improve compositing pipelines.

## Recommended Usage
- Creating SDR masters from HDR originals.
- Preparing web deliverables (YouTube, Vimeo, TikTok).
- Delivering SDR-safe versions for clients or broadcast.
- Generating SDR previews for HDR workflows.

## Quality Tips
- Use CRF **14–18** for high quality.
- `hable` is the most natural filmic curve.
- Increase `--desat` (0.15–0.35) for oversaturated HDR highlights.
- Prefer **yuv422p10le** when creating editing intermediates.
- Combine with **gamma_fix** for refined SDR brightness normalization.
