# num_edits

## Description
Analyzes a timeline or cut structure to count edits, transitions, or shot boundaries for editorial statistics, QC, or structural analysis.

## Purpose
`num_edits` provides fast editorial metrics by identifying the number of cuts, transitions, or shot boundaries in a video.  
This helps with:
- QC validation,
- editorial pacing analysis,
- archive metadata generation,
- automated editing metrics,
- machine-learning dataset preparation.

## How It Works
1. **Shot Boundary Detection**  
   Uses visual or luminance-based thresholds to detect edits between shots.
2. **Event Counting**  
   Each boundary event increments the edit count.
3. **Reporting**  
   The final count is embedded or returned based on videobeaux pipeline logic.
4. **Speed-Optimized**  
   Designed for rapid scanning across long-form footage or batch libraries.

## Program Template
    videobeaux -P num_edits \
      -i input.mp4 \
      -o output.mp4 \
      --count VALUE

## Arguments

- **count** — Enables or configures the edit-counting logic. Usually `true` or a mode such as `basic` vs `detailed` depending on implementation.

## Real World Example
    videobeaux -P num_edits \
      -i myvideo.mp4 \
      -o num_edits_styled.mp4 \
      --count true

## Technical Notes
- Detection may use pixel-wise difference, histogram deltas, or scene-change detection filters under the hood.  
- Thresholds vary with footage type; high-motion sequences may generate more detected edits.  
- The tool does not modify video; it only analyzes structure.  
- Useful in workflows that require edit-density analytics or QC verification.

## Recommended Usage
- Counting edits in commercials, music videos, or high-cut-rate content.  
- Generating metadata for cataloging systems or research datasets.  
- Automated QC workflows to detect unexpected edit patterns.  
- Comparing pacing between cuts or across versions of an edit.

## Quality Tips
- Use higher thresholds for shaky or handheld footage to avoid false positives.  
- Use lower thresholds when analyzing animation or motion-poor material.  
- For statistical studies, run the tool consistently with identical settings across all sources.
