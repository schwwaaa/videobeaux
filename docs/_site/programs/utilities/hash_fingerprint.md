# hash_fingerprint
:contentReference[oaicite:0]{index=0}

## Description
Creates unique fingerprints of video files using checksums, perceptual hashing, or frame-level hashing.  
Useful for deduplication, archival identification, similarity matching, and database cataloging.

## Purpose
`hash_fingerprint` allows Videobeaux users to generate machine-identifiable signatures from media files.  
This supports:
- duplicate detection,  
- content-based indexing,  
- frame-level comparison,  
- large-scale archival workflows,  
- catalog metadata generation,  
- cross-system verification of assets.

## How It Works
1. **File System Scanning**  
   - `recursive` allows walking entire folder trees.  
   - `exts` restricts scanning to specific file types.
2. **Hash Types**  
   The tool can generate several forms of fingerprints:
   - **file_hashes** → whole-file digests (MD5, SHA1, etc.)  
   - **stream_hash** → stream-level checksums from container metadata  
   - **framemd5** → per-frame MD5s for high-precision comparison  
   - **phash** → perceptual hash used for similarity matching rather than byte-exact comparison
3. **Perceptual Hashing Controls**  
   - `phash_fps` determines how many frames per second are sampled.  
   - `phash_size` sets the resolution of the perceptual hash grid.
4. **Catalog Output**  
   A fingerprint catalog can be generated for long-term storage, search systems, or dataset builds.
5. **Stream Selection**  
   `stream_kind` allows selecting video/audio/subtitle streams depending on the hashing method.

## Program Template
    videobeaux -P hash_fingerprint \
      -i input.mp4 \
      -o output.mp4 \
      --recursive VALUE \
      --exts VALUE \
      --file_hashes VALUE \
      --stream_hash VALUE \
      --framemd5 VALUE \
      --phash VALUE \
      --phash_fps VALUE \
      --phash_size VALUE \
      --catalog VALUE \
      --stream_kind VALUE

## Arguments

- **recursive** — Enables recursive folder scanning for batch fingerprinting.  
- **exts** — Comma-separated extensions to include (e.g., `mp4,mov,mkv`).  
- **file_hashes** — Generates byte-level file digests for exact-match identification.  
- **stream_hash** — Computes hash digests for individual media streams.  
- **framemd5** — Produces an MD5 hash for every decoded frame; extremely precise but large.  
- **phash** — Enables perceptual hashing for similarity comparisons.  
- **phash_fps** — Number of frames per second to sample for phash generation.  
- **phash_size** — Resolution of the phash grid (larger = more detail).  
- **catalog** — Outputs results into a catalog file for later lookup or indexing.  
- **stream_kind** — Specifies which stream type to fingerprint (e.g., `v`, `a`, `s`).

## Real World Example
    videobeaux -P hash_fingerprint \
      -i myvideo.mp4 \
      -o hash_fingerprint_styled.mp4 \
      --recursive false \
      --exts mp4,mov \
      --file_hashes true \
      --stream_hash true \
      --framemd5 false \
      --phash true \
      --phash_fps 1 \
      --phash_size 32 \
      --catalog true \
      --stream_kind v

## Technical Notes
- File hashes ensure perfect binary-level identification, but cannot detect visually similar variants.  
- Perceptual hashing (`phash`) is ideal for detecting duplicates that differ by transcoding, compression, or scaling.  
- `framemd5` is extremely accurate but produces large files; best for forensic comparison.  
- Catalog files allow large-scale search across thousands of items.  
- Adjust `phash_fps` and `phash_size` to balance between accuracy and performance.

## Recommended Usage
- Archival fingerprinting for media libraries.  
- Deduplication of large video collections.  
- Detecting alternate encodes of the same content.  
- Forensic verification and tamper detection.  
- Preparing similarity datasets for AI/ML workflows.

## Quality Tips
- Use `phash_fps=1–3` for good coverage without heavy overhead.  
- Higher `phash_size` (e.g., 32–64) improves discrimination of similar videos.  
- Use `framemd5` only when exact frame-level matching is required.  
- Always include `catalog=true` for batch processing or long-term reference.
