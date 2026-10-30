# videobeaux smoke test — 2026-10-29 21:04

- Source: `/var/folders/5g/9vzjk3hd7h74wwbghn_ts0fm0000gn/T/vb_smoke_src_ewi1uh80/synthetic.mp4` (section 6.0s + 8.0s, downscaled to 640px wide)
- ffmpeg: ffmpeg version 9.0.1 Copyright (c) 2000-2026 the FFmpeg developers

**2 passed · 0 failed · 0 timed out · 2 skipped** (of 4)

## Speech & Captions — 2/4 passing

| | program | time | result |
|---|---|---|---|
| ✅ | `captburn` | 0.3s | 640x360, 8.0s |
| ⏭️ | `ngrams` | 0.0s | the built-in synthetic clip has no speech — pass --source with a clip of someone talking |
| ⏭️ | `silence_xtraction` | 0.0s | the built-in synthetic clip has no speech — pass --source with a clip of someone talking |
| ✅ | `transcraibe` | 2.8s | 133 bytes JSON |
