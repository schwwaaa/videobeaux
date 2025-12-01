# subs_convert

## Description

Converts subtitle files between formats (e.g., SRT, VTT, ASS), preserving timing, text, and style metadata

## Arguments

- `list`
- `indexes`
- `langs`
- `all`
- `forced_only`
- `exclude_hi`
- `format`
- `outdir`
- `outputfile`
- `time_shift`

## Program Template

```bash
videobeaux -P subs_convert -i input.mp4 -o output.mp4 --list VALUE --indexes VALUE --langs VALUE --all VALUE --forced_only VALUE --exclude_hi VALUE --format VALUE --outdir VALUE --outputfile VALUE --time_shift VALUE
```

## Real World Example

```bash
videobeaux -P subs_convert -i myvideo.mp4 -o subs_convert_styled.mp4 --list EXAMPLE --indexes EXAMPLE --langs EXAMPLE --all EXAMPLE --forced_only EXAMPLE --exclude_hi EXAMPLE --format EXAMPLE --outdir EXAMPLE --outputfile EXAMPLE --time_shift EXAMPLE
```
