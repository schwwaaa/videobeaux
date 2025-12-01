---
layout: default
title: hash_fingerprint
nav_order: 2
---

# hash_fingerprint

## Description

Creates unique perceptual or checksum-style fingerprints of a video for identification, comparison, or deduplication

## Arguments

- `recursive`
- `exts`
- `file_hashes`
- `stream_hash`
- `framemd5`
- `phash`
- `phash_fps`
- `phash_size`
- `catalog`
- `stream_kind`

## Program Template

```bash
videobeaux -P hash_fingerprint -i input.mp4 -o output.mp4 --recursive VALUE --exts VALUE --file_hashes VALUE --stream_hash VALUE --framemd5 VALUE --phash VALUE --phash_fps VALUE --phash_size VALUE --catalog VALUE --stream_kind VALUE
```

## Real World Example

```bash
videobeaux -P hash_fingerprint -i myvideo.mp4 -o hash_fingerprint_styled.mp4 --recursive EXAMPLE --exts EXAMPLE --file_hashes EXAMPLE --stream_hash EXAMPLE --framemd5 EXAMPLE --phash EXAMPLE --phash_fps EXAMPLE --phash_size EXAMPLE --catalog EXAMPLE --stream_kind EXAMPLE
```
