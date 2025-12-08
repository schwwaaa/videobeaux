# qwikchop

## Description
Rapidly slices videos into precise segments based on timecodes or cut lists, optimized for speed and batch operations.

## Purpose
`qwikchop` is built for extremely fast segment extraction, allowing you to cut a video into many pieces without re-encoding.  
It supports:
- cut lists,
- recursive directory processing,
- black-frame trimming,
- segment cleanup rules,  
making it ideal for large workflows like commercial removal, archive splitting, and automated editing pipelines.

## How It Works
1. **Piece Definition**  
   The `pieces` argument defines cut points—either explicit timecodes or references to external lists.
2. **Recursive Mode**  
   If `recurse` is enabled, the tool processes all media files inside a directory tree.
3. **Black Frame Detection**  
   - `trim_black_front` removes silent/black leader.  
   - `black_scan`, `black_thresh`, and `black_pict` tune detection sensitivity.
4. **Padding Controls**  
   - `edge_pad_pre` and `edge_pad_post` adjust segment timing to avoid cutting too close to transitions.
5. **Minimum Edit Length**  
   `min_edit` prevents creation of fragment edits that are too short to be meaningful.
6. **Output**  
   Segments are exported into the destination directory with predictable sequential naming.

## Program Template
    videobeaux -P qwikchop \
      -i input.mp4 \
      -o output.mp4 \
      --pieces VALUE \
      --recurse VALUE \
      --keep_temp VALUE \
      --trim_black_front VALUE \
      --black_scan VALUE \
      --black_thresh VALUE \
      --black_pict VALUE \
      --edge_pad_pre VALUE \
      --edge_pad_post VALUE \
      --min_edit VALUE

## Arguments

- **pieces** — Defines segment boundaries; may be timecodes or an external list.  
- **recurse** — Enables directory recursion for batch processing.  
- **keep_temp** — When true, preserves intermediate working files.  
- **trim_black_front** — Removes black/silent leader at beginning.  
- **black_scan** — Duration scanned for determining black-frame presence.  
- **black_thresh** — Threshold used to classify frames as black.  
- **black_pict** — Pictorial threshold for more advanced black-frame evaluation.  
- **edge_pad_pre** — Time (seconds) added before segment boundaries.  
- **edge_pad_post** — Time (seconds) added after segment boundaries.  
- **min_edit** — Minimum allowed edit duration; prevents overly short segments.

## Real World Example
    videobeaux -P qwikchop \
      -i myvideo.mp4 \
      -o qwikchop_styled.mp4 \
      --pieces EXAMPLE \
      --recurse false \
      --keep_temp false \
      --trim_black_front true \
      --black_scan 0.5 \
      --black_thresh 0.10 \
      --black_pict 0.10 \
      --edge_pad_pre 0.25 \
      --edge_pad_post 0.25 \
      --min_edit 1.0

## Technical Notes
- Segmenting is performed without re-encoding, making it extremely fast.  
- Black trimming uses FFmpeg’s blackdetect logic; thresholds may require tuning based on source material.  
- `edge_pad_pre` and `edge_pad_post` are helpful for avoiding letterboxing artifacts or abrupt audio cuts.  
- Very small values for `min_edit` may create unusable micro-clips.

## Recommended Usage
- Cutting commercials or interstitials from broadcast recordings.  
- Building structured archives from long-form footage.  
- Automatically splitting lecture or surveillance videos into events.  
- Preparing clips for machine-learning datasets.

## Quality Tips
- Increase `edge_pad_pre/post` slightly to avoid accidental content clipping.  
- Adjust `black_thresh` based on the luminance characteristics of your footage.  
- Use recursive mode (`recurse=true`) when processing large folder trees.  
- Keep `min_edit` above 0.5–1.0 seconds for stable outputs.
