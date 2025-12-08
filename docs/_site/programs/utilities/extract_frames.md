# extract_frames
:contentReference[oaicite:1]{index=1}

## Description
Extracts individual frames from a video file and saves them as image files (typically PNG).  
Ideal for analysis, archival, animation workflows, visual debugging, and creating frame-based artwork.

## Purpose
`extract_frames` gives creators a fast and predictable way to output every frame (or selected frames via global videobeaux options) as standalone image files.  
This is useful for:
- animation and rotoscoping workflows,  
- ML dataset preparation,  
- glitch-art and frame-painting processes,  
- shot-by-shot inspection or QC,  
- archival still-frame extraction.

## How It Works
1. **Frame Decoding**  
   Video frames are decoded sequentially.
2. **Image Export**  
   Each frame is exported as its own image file using the globally configured pixel format and image output settings.
3. **Naming Convention**  
   Frames are typically numbered sequentially (e.g., `000001.png`, `000002.png`, etc.), depending on videobeaux output rules.
4. **Output Directory**  
   The destination directory is defined by global videobeaux settings (`--outfile`, mapping rules, etc.).

## Program Template
    videobeaux -P extract_frames \
      -i input.mp4 \
      -o output.mp4

## Arguments
- *(No program-specific arguments — this tool relies entirely on global videobeaux settings such as image format, numbering, and frame selection.)*

## Real World Example
    videobeaux -P extract_frames \
      -i myvideo.mp4 \
      -o extract_frames_styled.mp4

## Technical Notes
- PNG is the default format due to lossless quality, but other formats may be used depending on global configuration.  
- Large videos may produce thousands of frames; ensure adequate disk space.  
- Frame extraction is decode-limited — higher-resolution videos take longer per frame.  
- If frames are dropped or duplicated in the source video stream, extraction will preserve exactly what the decoder receives.  
- Good for use ahead of per-frame manipulation tools, compositing, or generative workflows.

## Recommended Usage
- Creating frame sequences for animation, compositing, or painting.  
- Building datasets for computer vision or machine learning.  
- Inspecting motion continuity, exposure behavior, or compression artifacts.  
- Generating image sequences for later re-import into editing or FX tools.

## Quality Tips
- Use PNG for archival quality; JPG for lightweight previews.  
- If color accuracy is critical, set a high-bit-depth pixel format globally (e.g., `rgb48le`).  
- Use SSD storage for significantly faster write speeds on large sequences.  
- When extracting for VFX, ensure your project frame rate matches the video’s native frame rate to avoid timing mismatch.
