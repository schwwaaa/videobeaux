# convert_mux

## Description
Rewraps or converts media streams while copying or re-encoding video/audio.  
Useful for repairing containers, adjusting codecs, changing formats, resolving sync issues, or preparing files for specific platforms or pipelines.

## Purpose
`convert_mux` is Videobeaux’s advanced container/codec remuxing and transcoding utility.  
Compared to the simpler `convert` program, `convert_mux` offers:
- deeper codec configuration,  
- container formatting,  
- bitrate and rate-control management,  
- GOP and frame-rate control,  
- filter pass-through (`vf`),  
- audio stream shaping,  
- curated presets via `--profile`.

This makes it ideal for delivery specifications, pipeline normalization, or technical media prep.

## How It Works
1. **Container Selection (`--format`)**  
   Determines the output container/muxer hint (mp4, mov, webm, matroska, mxf, gif, image2, avi).
2. **Profile-Based Presets (`--profile`)**  
   Selecting a profile automatically applies a curated list of FFmpeg flags (codec, pix_fmt, bitrate/quality, audio format, etc.).
3. **Manual Codecs and Quality**  
   If `--profile` is not used, you can explicitly specify:
   - `--vcodec`, `--acodec`,  
   - `--crf`, `--bitrate`, `--maxrate`, `--bufsize`, `--preset`,  
   - `--pix-fmt`, `--gop`, `-r`, `--vf`, `--tagv`, etc.
4. **Stream Copy Mode**  
   `--copy` bypasses re-encoding and performs a container-level remux where streams are compatible.
5. **FFmpeg Passthrough**  
   Extra arguments after `--` are passed directly to FFmpeg (`ffmpeg_args`).
6. **Execution**  
   A command is built and run through `run_ffmpeg_with_progress`, echoing the FFmpeg command for transparency.

## Program Template
    videobeaux -P convert_mux \
      -i input.mp4 \
      -o output.mp4 \
      --format VALUE \
      --profile VALUE \
      --vcodec VALUE \
      --acodec VALUE \
      --crf VALUE \
      --bitrate VALUE \
      --maxrate VALUE \
      --bufsize VALUE \
      --preset VALUE \
      --profile-v VALUE \
      --level VALUE \
      --pix-fmt VALUE \
      --gop VALUE \
      -r VALUE \
      --vf VALUE \
      --tagv VALUE \
      --abitrate VALUE \
      --ac VALUE \
      --ar VALUE \
      --copy \
      -- FFMPPEG_ARGS...

## Arguments

- **format** — Force container/muxer hint (`mp4`, `mov`, `webm`, `matroska`, `mxf`, `gif`, `image2`, `avi`, etc.).  
- **profile** — Apply a curated preset (see **Available Profiles** below).  
- **vcodec** — Video codec (e.g., `libx264`, `libx265`, `libaom-av1`, `prores_ks`, `dnxhd`, `mpeg2video`, `mpeg4`, `mjpeg`).  
- **acodec** — Audio codec (e.g., `aac`, `libopus`, `libmp3lame`, `mp3`, `pcm_s16le`).  
- **crf** — Constant Rate Factor for quality control (lower = higher quality).  
- **bitrate** — Target video bitrate (e.g., `5M`).  
- **maxrate** — Maximum video bitrate for rate control.  
- **bufsize** — VBV buffer size to pair with `maxrate`.  
- **preset** — Codec speed/efficiency preset (e.g., `ultrafast`, `fast`, `slow`).  
- **profile-v** (`profile_v`) — Video codec profile (e.g., `high`, `main`, `baseline`, or ProRes profile index).  
- **level** — Video level (e.g., `4.1`) for device compatibility.  
- **pix-fmt** (`pix_fmt`) — Pixel format (e.g., `yuv420p`, `yuv422p10le`, `yuva444p10le`).  
- **gop** — GOP/keyframe interval in frames.  
- **-r** — Output frame rate (`30000/1001`, `25`, `24`, etc.).  
- **vf** — Video filtergraph string.  
- **tagv** — Force video FourCC/tag (e.g., `hvc1`).  
- **abitrate** — Audio bitrate (e.g., `192k`).  
- **ac** — Audio channel count (e.g., `2`).  
- **ar** — Audio sample rate (e.g., `48000`).  
- **copy** — When set, stream copy all streams (no re-encode) if compatible.  
- **ffmpeg_args** — Raw arguments after `--` passed directly to FFmpeg.

### Available Profiles

These are the curated `--profile` options defined in the code, with their intent:

- **mp4_h264**  
  H.264 in MP4 for general web/delivery.  
  - `libx264`, `-preset veryfast`, `-crf 18`, `yuv420p`, `+faststart`, AAC 192k stereo.
- **mp4_hevc**  
  HEVC/H.265 in MP4 for higher compression at similar quality.  
  - `libx265`, `-preset medium`, `-crf 22`, `-tag:v hvc1`, `yuv420p`, `+faststart`, AAC 192k stereo.
- **mp4_av1**  
  AV1 in MP4 for very efficient modern web delivery.  
  - `libaom-av1`, `-crf 28`, `-b:v 0`, `yuv420p`, `+faststart`, AAC 192k stereo.
- **webm_vp9**  
  VP9-based WebM for web platforms supporting WebM.  
  - `libvpx-vp9`, `-b:v 0`, `-crf 30`, row-mt enabled, `yuv420p`, Opus 160k stereo.
- **webm_av1**  
  AV1 in WebM with Opus audio.  
  - `libaom-av1`, `-crf 32`, `-b:v 0`, `yuv420p`, Opus 160k stereo.
- **prores_422**  
  ProRes 422 mezzanine for professional workflows.  
  - `prores_ks`, `-profile:v 2`, `yuv422p10le`, PCM s16le audio.
- **prores_4444**  
  ProRes 4444 mezzanine with alpha support.  
  - `prores_ks`, `-profile:v 4`, `yuva444p10le`, PCM s24le audio.
- **dnxhr_hq**  
  DNxHR HQ mezzanine for Avid / pro pipelines.  
  - `dnxhd`, `-profile:v dnxhr_hq`, `yuv422p`, PCM s16le audio.
- **mxf_xdcamhd50_1080i59**  
  Broadcast MXF OP1a XDCAM HD 50, 1080i59.94.  
  - `mpeg2video` at 50M CBR, interlaced, top field first, `yuv422p`, PCM s24le 48k stereo, `-f mxf`.
- **lossless_ffv1**  
  FFV1 lossless archival video.  
  - `ffv1` level 3, intra (g=1), slice CRC, PCM s24le audio.
- **gif**  
  GIF export preset (via palettegen/paletteuse pipeline).  
  - Uses `fps=15,scale=iw:-2:flags=lanczos` in a filter_complex chain.
- **png_seq**  
  PNG image sequence output.  
  - `-c:v png`.
- **jpg_seq**  
  JPEG image sequence output.  
  - `-qscale:v 2` (high quality JPEG).
- **mp3_320**  
  Audio-only MP3 at 320 kbps.  
  - `-vn`, `libmp3lame`, `-b:a 320k`.
- **aac_192**  
  Audio-only AAC at 192 kbps.  
  - `-vn`, `aac`, `-b:a 192k`.
- **flac**  
  Audio-only FLAC lossless.  
  - `-vn`, `flac`.
- **avi_mjpeg_fast**  
  AVI with MJPEG video for fast, edit-friendly intermediates.  
  - `mjpeg` with `-q:v 3`, PCM s16le audio.
- **avi_mpeg4_fast**  
  AVI with MPEG-4 video tuned for speed.  
  - `mpeg4`, `-qscale:v 3`, `-bf 0`, `-mbd 0`, MP3 192k audio.

## Real World Example
    videobeaux -P convert_mux \
      -i myvideo.mp4 \
      -o convert_mux_styled.mp4 \
      --format mp4 \
      --profile mp4_h264

## Technical Notes
- Profiles apply **after** basic container inference and can override many manually specified arguments.  
- When output ends with `.mp4`, certain profiles that expect non-MP4 containers (`webm_…`, `mxf_…`, `gif`, etc.) will cause a fail-fast error to avoid confusing FFmpeg errors.  
- `--copy` disables most encoding options and simply remuxes streams when possible.  
- GIF and image-sequence profiles bypass typical video/audio handling and use specialized pipelines.  
- Additional raw FFmpeg flags can be appended after `--` if you need something not exposed via named arguments.

## Recommended Usage
- Preparing web deliverables using `mp4_h264`, `mp4_hevc`, or `mp4_av1`.  
- Making pro intermediates in `prores_422`, `prores_4444`, or `dnxhr_hq` for editing, grading, or VFX.  
- Building broadcast MXF files with `mxf_xdcamhd50_1080i59`.  
- Generating GIFs, PNG/JPEG sequences, or audio-only MP3/AAC/FLAC assets.  
- Using `--copy` to remux without re-encoding when container changes are sufficient.

## Quality Tips
- For H.264/H.265, tune CRF and preset if not relying solely on profiles.  
- Use the ProRes and DNxHR profiles for grading/VFX workflows where multi-gen quality matters.  
- AV1 profiles (`mp4_av1`, `webm_av1`) are slower to encode but very efficient for distribution.  
- For archival, prefer `lossless_ffv1` in Matroska with PCM audio.  
- Always inspect container + codec compatibility for your target platform before finalizing a profile.
