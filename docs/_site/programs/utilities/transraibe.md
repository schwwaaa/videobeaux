# transraibe

## Description
AI-based transcription tool for converting spoken audio within video files into text using configurable speech-to-text models.

## Purpose
`transraibe` provides automated transcription capabilities inside the videobeaux workflow.  
It enables creators to generate subtitles, caption files, analysis transcripts, or searchable text from any video containing dialogue or narration.  
The tool is optimized for quick turnaround and supports multiple STT (speech-to-text) model options.

## How It Works
1. **Model Selection**  
   You choose the speech-to-text engine via `--stt_model`.
2. **Audio Extraction**  
   The program extracts the audio track from the input video.
3. **Transcription Stage**  
   The extracted audio is processed using the selected model, producing text output.
4. **Encoding & Output**  
   The final transcription is embedded or exported depending on the videobeaux pipelines you pair with it (captburn, metadata storage, etc.).
   
## Program Template
    videobeaux -P transraibe \
      -i input.mp4 \
      -o output.mp4 \
      --stt_model VALUE

## Arguments

- **stt_model** — Speech-to-text model used for transcription (e.g., whisper-small, whisper-medium, whisper-large, or any model supported by your environment).

## Real World Example
    videobeaux -P transraibe \
      -i myvideo.mp4 \
      -o transraibe_styled.mp4 \
      --stt_model whisper-medium

## Technical Notes
- The accuracy of transcription depends heavily on the `stt_model` chosen.  
- Larger models produce better understanding of accents, noisy audio, and complex phrasing, but require more resources.  
- The input audio is automatically normalized and extracted before processing.  
- Output format compatibility (SRT, VTT, raw text) may depend on additional videobeaux tooling layered on top of transraibe.

## Recommended Usage
- Generating transcript files for interviews, podcasts, and voice-driven content.  
- Preparing subtitle text for later burning (via captburn).  
- Producing searchable metadata for archival or indexing systems.  
- Replacing manual transcription workflows in post-production.

## Quality Tips
- Use higher-tier models (e.g., whisper-large) for best accuracy on challenging audio.  
- For clean studio audio, smaller models are often sufficient and much faster.  
- If the transcription seems off, pre-clean audio (denoise, normalize) before running transraibe.  
- Consider pairing with captburn to immediately generate styled subtitles.
