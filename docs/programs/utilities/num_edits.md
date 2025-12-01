# num_edits

## Description

Analyzes a timeline or cut structure to count edits, transitions, or shot boundaries for editorial statistics or QC

## Arguments

- `count`

## Program Template

```bash
videobeaux -P num_edits -i input.mp4 -o output.mp4 --count VALUE
```

## Real World Example

```bash
videobeaux -P num_edits -i myvideo.mp4 -o num_edits_styled.mp4 --count EXAMPLE
```
