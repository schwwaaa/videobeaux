# download_yt
:contentReference[oaicite:1]{index=1}

## Description
Downloads or rips video and audio content from YouTube (or other compatible platforms) and prepares it for processing inside Videobeaux workflows.

## Purpose
`download_yt` is a quick-ingest utility that brings online source media into your local Videobeaux environment.  
This is useful when you need:
- reference clips for editing or remixing,  
- footage for analysis or research,  
- material for glitch, collage, or experimental video art,  
- assets for transformation inside other Videobeaux programs.

## How It Works
1. **URL Retrieval**  
   Videobeaux (via external download tools) fetches the highest-available quality or a configured preferred resolution/format.
2. **Muxing & Cleanup**  
   Audio and video streams are combined into a standardized container suitable for immediate downstream processing.
3. **Global Output Handling**  
   Because `download_yt` has no program-specific arguments, all settings (filename, codecs, mapping, etc.) follow Videobeaux global defaults.
4. **Output**  
   The resulting video file is written to the path specified with `-o`.

## Program Template
    videobeaux -P download_yt \
      -i input.mp4 \
      -o output.mp4

## Arguments
- *(No program-specific arguments — this program relies entirely on global Videobeaux input/output configuration and downloader behavior.)*

## Real World Example
    videobeaux -P download_yt \
      -i myvideo.mp4 \
      -o download_yt_styled.mp4

## Technical Notes
- Quality of the downloaded media depends on what the source service provides (YouTube DASH streams, format variants, etc.).  
- If separate audio/video streams are delivered by the platform, Videobeaux muxes them into a single file.  
- Output format is determined by your global settings — typically MP4 unless changed.  
- For archival purposes, consider remuxing into MKV to preserve metadata.

## Recommended Usage
- Bringing online clips into your Videobeaux workflow for editing, glitching, or processing.  
- Preparing material for LUT application, tonemapping, interpolation, or compositing.  
- Rapid prototyping of creative projects using found or reference footage.  
- Downloading assets for offline study or frame-by-frame analysis.

## Quality Tips
- Always inspect resolution and bitrate of the downloaded file before high-end processing.  
- If audio quality matters, check whether the source provides separate high-quality audio tracks.  
- Consider transcoding to a mezzanine codec (e.g., ProRes) for grading or VFX workflows.  
- Large downloads benefit from using SSD storage to avoid bottlenecks.
