---
layout: default
title: qwikchop
nav_order: 2
---

# qwikchop

## Description

Rapidly slices videos into precise segments based on timecodes or cut lists, optimized for speed and batch operations

## Arguments

- `pieces`
- `recurse`
- `keep_temp`
- `trim_black_front`
- `black_scan`
- `black_thresh`
- `black_pict`
- `edge_pad_pre`
- `edge_pad_post`
- `min_edit`

## Program Template

```bash
videobeaux -P qwikchop -i input.mp4 -o output.mp4 --pieces VALUE --recurse VALUE --keep_temp VALUE --trim_black_front VALUE --black_scan VALUE --black_thresh VALUE --black_pict VALUE --edge_pad_pre VALUE --edge_pad_post VALUE --min_edit VALUE
```

## Real World Example

```bash
videobeaux -P qwikchop -i myvideo.mp4 -o qwikchop_styled.mp4 --pieces EXAMPLE --recurse EXAMPLE --keep_temp EXAMPLE --trim_black_front EXAMPLE --black_scan EXAMPLE --black_thresh EXAMPLE --black_pict EXAMPLE --edge_pad_pre EXAMPLE --edge_pad_post EXAMPLE --min_edit EXAMPLE
```
