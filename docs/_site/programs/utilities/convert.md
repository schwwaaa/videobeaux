# convert
:contentReference[oaicite:1]{index=1}

## Description
Performs a simple video file conversion using global Videobeaux encoding settings.  
Useful for remuxing, transcoding, codec changes, rewrapping containers, or generating standardized media versions.

## Purpose
`convert` exists as a lightweight, universal tool for turning one media container or codec into another.  
This is ideal for:
- converting incompatible formats into editing-friendly files,  
- rewrapping media without re-encoding,  
- transcoding to delivery-safe formats,  
- preparing videos for downstream Videobeaux programs,  
- batch normalization of mixed-file libraries.

## How It Works
1. **Input Decoding**  
   The source file is decoded as needed, depending on global codec options.
2. **Re-encode or Stream Copy**  
   - If no codec is specified, Videobeaux uses its global defaults.  
   - If codecs are set globally (`vcodec`, `acodec`), `convert` applies them here.  
   - If settings allow stream copy, the video may be remuxed without re-encoding.
3. **Output Writing**  
   The converted or rewrapped video is written to the path specified via `-o`.
4. **No Additional Logic**  
   This program intentionally provides a pure conversion operation, without filtering or modification.

## Program Template
    videobeaux -P convert \
      -i input.mp4 \
      -o output.mp4

## Arguments
- *(No program-specific arguments — this module relies entirely on Videobeaux global encoding settings.)*

## Real World Example
    videobeaux -P convert \
      -i myvideo.mp4 \
      -o convert_styled.mp4

## Technical Notes
- Rewrapping (e.g., MKV → MP4) is extremely fast when using stream copy.  
- Full transcoding (e.g., H.264 → ProRes, AAC → WAV) depends on global audio/video codec settings.  
- File size and transcoding time are directly impacted by CRF, bitrate, and preset settings.  
- Useful for generating clean, uniform input files before applying more complex Videobeaux processes.

## Recommended Usage
- Normalizing transcoded footage from varied sources.  
- Preparing content for editing systems that dislike certain containers/codecs.  
- Creating proxy versions for offline workflows.  
- Converting videos to universally compatible formats for distribution, archive, or broadcast.

## Quality Tips
- Use a low CRF (14–18) for high-quality archival intermediates.  
- If the goal is speed, choose faster presets (e.g., `faster`, `fast`).  
- For maximum compatibility, output H.264 + AAC in MP4.  
- For high-end workflows, output ProRes or another mezzanine codec.  
- Always verify that audio channel layouts survive the conversion correctly.
