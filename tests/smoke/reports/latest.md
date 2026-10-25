# videobeaux smoke test — 2026-10-25 02:05

- Source: `/var/folders/5g/9vzjk3hd7h74wwbghn_ts0fm0000gn/T/vb_smoke_src_pbmr4n_g/synthetic.mp4` (section 6.0s + 8.0s, downscaled to 640px wide)
- ffmpeg: ffmpeg version 9.0.1 Copyright (c) 2000-2026 the FFmpeg developers

**2 passed · 0 failed · 0 timed out · 1 skipped** (of 3)

## Color & Look — 2/2 passing

| | program | time | result |
|---|---|---|---|
| ✅ | `bad_predator` | 1.0s | 640x360, 8.4s |
| ✅ | `duotone` | 1.4s | 640x360, 8.0s |

## Speech & Captions — 0/1 passing

| | program | time | result |
|---|---|---|---|
| ⏭️ | `captburn` | 0.0s | needs a transcript (transcraibe must pass first) |
