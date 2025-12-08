# subs_convert

## Description
Converts subtitle files between formats (e.g., SRT, VTT, ASS) while preserving timing, text, and (where possible) style metadata.

## Purpose
The `subs_convert` program standardizes subtitle workflows by:
- Listing available subtitle tracks in a media file.
- Extracting specific subtitle tracks by index or language.
- Converting them to a desired output format.
- Optionally cleaning or shifting them in time.

It is especially helpful when preparing subtitles for caption-burning, translations, or multi-version deliverables.

## How It Works
1. **Input Inspection**  
   Reads subtitle streams from the input media file (or compatible subtitle sources).
2. **Track Selection**  
   - `list` shows all available subtitle tracks with indices and metadata.  
   - `indexes` selects specific tracks by index.  
   - `langs` filters tracks by language codes (e.g., `eng`, `spa`).  
   - `all` overrides filters and selects every subtitle track.
3. **Filtering & Cleaning**  
   - `forced_only` restricts output to forced subtitles only (e.g., foreign-language dialogue).  
   - `exclude_hi` strips hearing-impaired (HI) descriptors like sound effects or music tags.
4. **Format Conversion**  
   Converts the selected tracks into the requested output format (SRT, VTT, ASS, etc.).
5. **Timing Adjustment**  
   Applies an optional `time_shift` so subtitles can be nudged earlier or later to stay in sync.
6. **Output Writing**  
   Writes one or more subtitle files to an output directory or a specific `outputfile` path.

## Program Template
    videobeaux -P subs_convert \
      -i input.mp4 \
      -o output.mp4 \
      --list VALUE \
      --indexes VALUE \
      --langs VALUE \
      --all VALUE \
      --forced_only VALUE \
      --exclude_hi VALUE \
      --format VALUE \
      --outdir VALUE \
      --outputfile VALUE \
      --time_shift VALUE

## Arguments

- **list** — List all subtitle tracks in the input with indexes, languages, and basic metadata. Useful as a first step to see what is available.  
- **indexes** — One or more subtitle track indexes to extract/convert (e.g., `0`, `1,2`). Accepts a comma-separated list.  
- **langs** — Filter tracks by language codes (e.g., `eng`, `spa`). Accepts one or more languages, usually as a comma-separated list, depending on implementation.  
- **all** — Select all subtitle tracks, ignoring `indexes` and `langs` filters.  
- **forced_only** — Restrict output to subtitle events marked as “forced” (e.g., foreign-language dialogue or plot-critical on-screen text).  
- **exclude_hi** — Attempt to remove hearing-impaired (HI) descriptors such as `[MUSIC]`, `(LAUGHTER)`, and other non-dialogue notes.  
- **format** — Output format for converted subtitles, such as `srt`, `vtt`, or `ass`. The exact set of valid formats depends on the underlying subtitle tooling.  
- **outdir** — Directory where the converted subtitle files should be written. Filenames are usually derived from the input and track metadata.  
- **outputfile** — Explicit path and filename for the converted subtitle file when you only want a single, known output file location.  
- **time_shift** — Apply a timing offset to all subtitle cues. Positive values delay subtitles; negative values make them appear earlier (e.g., `-0.25` shifts cues 250ms earlier).  

## Real World Example
    videobeaux -P subs_convert \
      -i documentary.mp4 \
      -o documentary_fixed.mp4 \
      --langs eng \
      --exclude_hi \
      --format vtt \
      --time_shift -0.25 \
      --outdir subs_output

## Technical Notes
- `list` is often used alone to inspect subtitle tracks before running a full conversion.  
- If both `indexes` and `langs` are provided, explicit `indexes` typically take priority.  
- `all` supersedes both `indexes` and `langs`, ensuring every subtitle track is processed.  
- `time_shift` expects a value in seconds and can be fractional for fine-grained adjustment.  
- Some formats (like ASS) support styling; preservation depends on how much style data exists in the source.

## Recommended Usage
- Start with `list` to discover track indices and language tags.  
- Use `langs` when targeting a specific language for translation or distribution.  
- Use `exclude_hi` for clean, dialogue-only subtitle deliveries.  
- Use `format ass` when preparing styled subtitles for tools like `captburn`.  
- Use `time_shift` after trimming or re-cutting your video to quickly re-align subtitles without manual editing.
