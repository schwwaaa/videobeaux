# extract_sound
:contentReference[oaicite:1]{index=1}

## Description
Extracts the audio track from a video file and saves it as a standalone audio file, preserving quality and format.  
Useful for sound design, transcription workflows, remixing, archival storage, or preparing audio-only deliverables.

## Purpose
`extract_sound` allows creators to quickly isolate the audio component of any media file.  
This is ideal for:
- podcasts derived from video interviews,  
- music extraction for editing or remixing,  
- voice-over capture,  
- archival audio preparation,  
- preprocessing audio for tools like transcription or captioning.

## How It Works
1. **Stream Selection**  
   The tool identifies the primary audio stream from the input file.
2. **Direct Copy or Re-encode**  
   Depending on videobeaux global flags, audio is either:
   - copied without re-encoding for perfect fidelity, or  
   - encoded with the user-specified audio codec and bitrate.
3. **Output Rendering**  
   The extracted audio is written to the output file specified with `-o`.
4. **No Video Processing**  
   Video streams are ignored; only the audio track is saved.

## Program Template
    videobeaux -P extract_sound \
      -i input.mp4 \
      -o output.mp4

## Arguments
- *(No program-specific arguments — this tool relies entirely on global videobeaux audio settings such as codec, bitrate, and container format.)*

## Real World Example
    videobeaux -P extract_sound \
      -i myvideo.mp4 \
      -o extract_sound_styled.mp4

## Technical Notes
- The output file extension determines the final audio container (e.g., `.mp3`, `.wav`, `.aac`).  
- If no re-encode options are given, videobeaux may default to stream copy.  
- Multi-track audio is not mixed—typically the first audio stream is extracted unless overridden globally.  
- Useful for batch pipelines when paired with folder recursion or metadata extraction.

## Recommended Usage
- Extracting dialogue or interviews for transcription.  
- Creating podcast audio from filmed sessions.  
- Pulling music or SFX layers from video renders.  
- Archival workflows where audio must be stored separately.

## Quality Tips
- Use `.wav` for lossless extraction.  
- Use `.aac` or `.mp3` for lightweight distribution formats.  
- If audio is distorted or clipped, normalize or limit in a separate audio-processing step.  
- When exporting from mixed sources, ensure consistent bitrate settings to avoid quality mismatches.
