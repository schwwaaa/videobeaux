# videobeaux smoke test — 2026-10-03 20:06

- Source: `/var/folders/5g/9vzjk3hd7h74wwbghn_ts0fm0000gn/T/vb_smoke_src_yw9x27bd/synthetic.mp4` (section 6.0s + 8.0s, downscaled to 640px wide)
- ffmpeg: ffmpeg version 6.0 Copyright (c) 2000-2023 the FFmpeg developers

**100 passed · 0 failed · 0 timed out · 10 skipped** (of 110)

## Color & Look — 28/28 passing

| | program | time | result |
|---|---|---|---|
| ✅ | `bad_predator` | 1.8s | 640x360, 8.0s |
| ✅ | `ball_point_pen` | 0.8s | 640x360, 10.4s |
| ✅ | `cartoon` | 1.4s | 640x360, 8.0s |
| ✅ | `dither` | 1.0s | 640x360, 8.0s |
| ✅ | `duotone` | 1.5s | 640x360, 8.0s |
| ✅ | `gamma_fix` | 0.8s | 640x360, 8.0s |
| ✅ | `halftone` | 0.6s | 640x360, 8.0s |
| ✅ | `kmeans_palette` | 0.8s | 640x360, 8.0s |
| ✅ | `light_snow` | 5.8s | 640x360, 8.0s |
| ✅ | `lut_apply` | 0.3s | 640x360, 8.0s |
| ✅ | `neon_edges` | 0.9s | 640x360, 8.0s |
| ✅ | `night_vision` | 0.4s | 640x360, 8.0s |
| ✅ | `old_film_damage` | 0.4s | 640x360, 8.0s |
| ✅ | `ordered_dither` | 1.3s | 640x360, 8.0s |
| ✅ | `pickle_juice` | 0.3s | 640x360, 8.0s |
| ✅ | `rb_blur` | 0.3s | 640x360, 8.0s |
| ✅ | `rb_blur_pro` | 0.3s | 640x360, 8.0s |
| ✅ | `recalled_sensor` | 0.6s | 640x360, 8.4s |
| ✅ | `recalled_sensor_pro` | 0.4s | 640x360, 9.2s |
| ✅ | `retro_dither` | 0.5s | 640x360, 8.0s |
| ✅ | `septic` | 0.3s | 640x360, 8.0s |
| ✅ | `sketch` | 1.1s | 640x360, 8.0s |
| ✅ | `soapblind` | 21.8s | 640x360, 8.0s |
| ✅ | `steel_wash` | 0.3s | 640x360, 8.0s |
| ✅ | `wbflare` | 0.3s | 640x360, 8.0s |
| ✅ | `wbflare_pro` | 0.3s | 640x360, 8.0s |
| ✅ | `xpiritualism` | 0.8s | 640x360, 8.0s |
| ✅ | `zapruder` | 3.1s | 640x360, 8.0s |

## Cut & Assemble — 6/6 passing

| | program | time | result |
|---|---|---|---|
| ✅ | `concat` | 0.3s | 640x360, 12.0s |
| ✅ | `insert_clip` | 0.4s | 640x360, 12.0s |
| ✅ | `mince` | 0.4s | 640x360, 8.1s |
| ✅ | `qwikchop` | 0.3s | 3 file(s) in result/ |
| ✅ | `trim` | 0.2s | 640x360, 2.0s |
| ✅ | `wipe_transitions` | 0.4s | 640x360, 7.0s |

## Glitch & Corruption — 17/17 passing

| | program | time | result |
|---|---|---|---|
| ✅ | `bad_animation` | 0.6s | 640x360, 8.0s |
| ✅ | `bad_contrast` | 0.8s | 640x360, 8.0s |
| ✅ | `blur_pix` | 0.5s | 640x360, 8.0s |
| ✅ | `chromatic_pulse` | 0.9s | 640x360, 8.0s |
| ✅ | `crossmosh` | 0.3s | 640x360, 12.0s |
| ✅ | `deep_fry` | 0.3s | 640x360, 8.0s |
| ✅ | `digital_boss` | 0.4s | 640x360, 8.0s |
| ✅ | `flow_warp` | 1.2s | 640x360, 8.0s |
| ✅ | `pixel_sort` | 2.9s | 640x360, 8.0s |
| ✅ | `slight_smear` | 0.3s | 640x360, 8.0s |
| ✅ | `splitting` | 0.3s | 640x360, 8.0s |
| ✅ | `splitting_pro` | 0.4s | 640x360, 8.0s |
| ✅ | `twociz` | 0.7s | 640x360, 8.0s |
| ✅ | `twociz_pro` | 0.5s | 640x360, 8.0s |
| ✅ | `vhs_tracking` | 0.4s | 640x360, 8.0s |
| ✅ | `warp` | 1.0s | 640x360, 8.0s |
| ✅ | `xrgb` | 0.4s | 640x360, 8.0s |

## Layout & Overlay — 4/4 passing

| | program | time | result |
|---|---|---|---|
| ✅ | `lagkage` | 0.3s | 640x360, 8.0s |
| ✅ | `stack_2x` | 0.3s | 640x720, 8.0s |
| ✅ | `triptych` | 0.4s | 1920x360, 8.0s |
| ✅ | `watermark` | 0.3s | 640x360, 8.0s |

## Media Tools — 12/14 passing

| | program | time | result |
|---|---|---|---|
| ✅ | `convert_dims` | 0.3s | 640x480, 8.0s |
| ✅ | `convert_mux` | 0.2s | 640x360, 8.0s |
| ⏭️ | `download_yt` | 0.0s | needs network + a real YouTube URL as -i |
| ✅ | `extract_frames` | 0.1s | 8 file(s) in result/ |
| ✅ | `extract_sound` | 0.1s | 8.0s audio |
| ✅ | `hash_fingerprint` | 0.1s | 196 bytes JSON |
| ✅ | `media_info` | 0.1s | 838 bytes JSON |
| ✅ | `meta_extraction` | 0.1s | 1917 bytes JSON |
| ✅ | `resize` | 0.2s | 320x180, 8.0s |
| ✅ | `shortify` | 1.7s | 1080x1920, 8.0s |
| ✅ | `stabilize` | 0.7s | 640x360, 8.0s |
| ✅ | `subs_convert` | 0.1s | 104 bytes |
| ✅ | `thumbs` | 0.1s | 996x390 image |
| ⏭️ | `tonemap_hdr_sdr` | 0.0s | could not build the synthetic HDR clip |

## Speech & Captions — 4/9 passing

| | program | time | result |
|---|---|---|---|
| ✅ | `auto_narrate` | 6.4s | 640x360, 8.0s |
| ✅ | `captburn` | 0.3s | 640x360, 8.0s |
| ⏭️ | `grep_supercut` | 0.0s | the built-in synthetic clip has no speech — pass --source with a clip of someone talking |
| ✅ | `kinetic_captions` | 0.6s | 640x360, 8.0s |
| ⏭️ | `ngrams` | 0.0s | the built-in synthetic clip has no speech — pass --source with a clip of someone talking |
| ⏭️ | `qwikchop_deluxe` | 0.0s | the built-in synthetic clip has no speech — pass --source with a clip of someone talking |
| ⏭️ | `silence_xtraction` | 0.0s | the built-in synthetic clip has no speech — pass --source with a clip of someone talking |
| ✅ | `transcraibe` | 2.3s | 133 bytes JSON |
| ⏭️ | `word_xtraction_vad` | 0.0s | the built-in synthetic clip has no speech — pass --source with a clip of someone talking |

## Time & Motion — 13/13 passing

| | program | time | result |
|---|---|---|---|
| ✅ | `boomerang` | 0.5s | 640x360, 16.0s |
| ✅ | `broken_scroll` | 0.7s | 640x360, 8.0s |
| ✅ | `frame_interpolate` | 5.7s | 640x360, 8.0s |
| ✅ | `freeze_punch` | 0.4s | 640x360, 9.4s |
| ✅ | `looper_pro` | 0.2s | 640x360, 9.9s |
| ✅ | `nostalgic_stutter` | 0.3s | 640x360, 8.0s |
| ✅ | `overexposed_stutter` | 0.3s | 640x360, 8.0s |
| ✅ | `reverse` | 0.2s | 640x360, 8.0s |
| ✅ | `scrolling_pro` | 0.3s | 640x360, 8.0s |
| ✅ | `speed` | 0.2s | 640x360, 5.4s |
| ✅ | `strobe_cut` | 0.3s | 640x360, 8.0s |
| ✅ | `stutter_pro` | 0.2s | 640x360, 8.0s |
| ✅ | `time_ramp` | 0.3s | 640x360, 8.0s |

## Trails & Echoes — 11/11 passing

| | program | time | result |
|---|---|---|---|
| ✅ | `double_cup` | 0.9s | 640x360, 8.0s |
| ✅ | `fever` | 0.5s | 640x360, 8.0s |
| ✅ | `frame_delay_pro1` | 0.3s | 640x360, 8.0s |
| ✅ | `frame_delay_pro2` | 0.2s | 640x360, 8.0s |
| ✅ | `ghostee` | 0.4s | 640x360, 8.0s |
| ✅ | `lsd_feedback` | 0.4s | 640x360, 8.0s |
| ✅ | `lsd_feedback_pro` | 0.4s | 640x360, 8.0s |
| ✅ | `mirror_delay` | 0.3s | 640x360, 8.0s |
| ✅ | `repainting` | 0.8s | 640x360, 8.0s |
| ✅ | `smudge` | 0.6s | 640x360, 9.0s |
| ✅ | `t1000` | 1.7s | 640x360, 8.0s |

## Uncategorized — 3/3 passing

| | program | time | result |
|---|---|---|---|
| ✅ | `chain_builder` | 0.6s | 640x360, 16.0s |
| ✅ | `chain_builder_pro` | 0.5s | 640x360, 16.0s |
| ✅ | `convert` | 0.3s | 640x360, 8.0s |

## Vision & Tracking — 2/5 passing

| | program | time | result |
|---|---|---|---|
| ⏭️ | `face_follow` | 0.0s | the built-in synthetic clip has no faces — pass --source with a clip of a person |
| ⏭️ | `face_redact` | 0.0s | the built-in synthetic clip has no faces — pass --source with a clip of a person |
| ⏭️ | `face_track` | 0.0s | the built-in synthetic clip has no faces — pass --source with a clip of a person |
| ✅ | `feature_trails` | 0.8s | 640x360, 8.0s |
| ✅ | `motion_ghost` | 1.3s | 640x360, 8.0s |
