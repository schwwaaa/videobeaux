# Slider response audit

How much the picture changes at 0 / 25 / 50 / 75 / 100 % of each slider (linear slider position → value, as shipped before the curves).
Curves are only written for **trusted** rows (✔): non-negative range, fit not pinned at its limits.

`s50` = share of the strongest effect reached at half-way. **late** < 0.20 · slow < 0.35 · even 0.35–0.65 · fast ≤ 0.80 · **early** > 0.80 · flat = no visible change.

**even: 125 · flat: 88 · early: 80 · varies: 29 · fast: 26 · error: 19 · late: 14 · slow: 9**

| program | slider | range | default | s25 | s50 | s75 | class | suggested curve |
|---|---|---|---|---|---|---|---|---|
| ascii_art | edges | 0…1 | 0.0 | 0.34 | 0.59 | 0.84 | even |  |
| auto_narrate | duration | 5…300 | 30.0 |  |  |  | flat |  |
| auto_narrate | font_size | 12…200 | 76 | 0.36 | 0.90 | 0.99 | early | pow:1.65 ✔ |
| auto_narrate | original_volume | 0…1 | 0.2 |  |  |  | flat |  |
| auto_narrate | voice_speed | 0.5…2 | 1.0 | 0.81 | 0.87 | 0.99 | early | pow:3 |
| bad_animation | amount | 0…1 | 1.0 | 0.16 | 0.31 | 0.47 | slow | pow:0.7 ✔ |
| bad_contrast | amount | 0…1 | 1.0 | 0.30 | 0.60 | 0.81 | even |  |
| ball_point_pen | amount | 0…1 | 1.0 | 0.31 | 0.54 | 0.77 | even |  |
| beauxtrix | b_a | -2…2 | 1.0 | 0.00 | 0.00 | 0.92 | late | pow:0.35 |
| beauxtrix | b_b | -2…2 | 0.0 | 0.02 | 0.87 | 0.99 | early | pow:0.44 |
| beauxtrix | b_bias | -1…1 | 0.0 | 0.25 | 0.48 | 0.78 | even |  |
| beauxtrix | b_c | -2…2 | 0.0 | 0.00 | 0.91 | 0.99 | early | pow:0.35 |
| beauxtrix | b_d | -2…2 | 0.0 | 0.00 | 0.91 | 0.99 | early | pow:0.35 |
| beauxtrix | g_a | -2…2 | 1.0 | 0.00 | 0.00 | 0.92 | late | pow:0.35 |
| beauxtrix | g_b | -2…2 | 0.0 | 0.02 | 0.88 | 0.99 | early | pow:0.43 |
| beauxtrix | g_bias | -1…1 | 0.0 | 0.25 | 0.50 | 0.78 | even |  |
| beauxtrix | g_c | -2…2 | 0.0 | 0.00 | 0.91 | 0.99 | early | pow:0.35 |
| beauxtrix | g_d | -2…2 | 0.0 | 0.00 | 0.91 | 0.99 | early | pow:0.35 |
| beauxtrix | r_a | -2…2 | 1.0 | 0.02 | 0.15 | 1.00 | varies |  |
| beauxtrix | r_bias | -1…1 | 0.0 | 0.48 | 1.00 | 0.51 | varies |  |
| beauxtrix | r_c | -2…2 | 0.0 | 0.13 | 1.00 | 0.10 | varies |  |
| beauxtrix | r_d | -2…2 | 0.0 | 0.13 | 1.00 | 0.10 | varies |  |
| black_white | amount | 0…1 | 1.0 | 0.25 | 0.50 | 0.75 | even |  |
| black_white | contrast | 0.5…8 | 2.5 | 0.51 | 0.72 | 0.87 | fast | pow:2.06 ✔ |
| black_white | grain | 0…1 | 0.0 | 0.24 | 0.45 | 0.69 | even |  |
| blueprint | amount | 0…1 | 1.0 | 0.25 | 0.50 | 0.75 | even |  |
| blueprint | sensitivity | 0…1 | 0.5 | 0.15 | 0.36 | 0.73 | even |  |
| blur_pix | amount | 0…1 | 1.0 | 0.26 | 0.50 | 0.75 | even |  |
| boomerang | loops | 1…6 | 1 |  |  |  | flat |  |
| broken_scroll | amount | 0…1 | 1.0 | 0.26 | 0.51 | 0.77 | even |  |
| cartoon | edge_size | 3…21 | 9 | 0.41 | 0.62 | 0.83 | even |  |
| cartoon | edge_strength | 1…15 | 4 | 0.55 | 0.74 | 0.95 | fast | pow:2.35 ✔ |
| cartoon | levels | 2…16 | 6 | 0.83 | 0.92 | 0.96 | early | pow:3 |
| cartoon | saturation | 0…3 | 1.25 | 0.68 | 0.99 | 1.00 | early | pow:3 |
| cartoon | smooth | 1…15 | 3 |  |  |  | flat |  |
| chroma_key | blend | 0…1 | 0.05 | 0.60 | 0.86 | 0.95 | early | pow:3 |
| chroma_key | feather | 0…10 | 1.0 |  |  |  | flat |  |
| chroma_key | shrink | 0…10 | 1 | 0.31 | 0.58 | 0.83 | even |  |
| chroma_key | similarity | 0.01…1 | 0.15 | 0.70 | 1.00 | 1.00 | early | log ✔ |
| chroma_key | spill | 0…1 | 0.3 |  |  |  | flat |  |
| chromatic_pulse | amount | 0…30 | 6.0 | 0.29 | 0.56 | 0.79 | even |  |
| chromatic_pulse | speed | 0…10 | 2.0 | 0.95 | 0.96 | 0.98 | early | pow:3 |
| color_pass | boost | 0…3 | 1.0 | 0.79 | 0.95 | 0.98 | early | pow:3 |
| color_pass | desaturate | 0…1 | 1.0 | 0.27 | 0.50 | 0.74 | even |  |
| color_pass | min_saturation | 0…1 | 0.15 |  |  |  | flat |  |
| color_pass | range | 1…180 | 30.0 | 0.12 | 0.39 | 0.79 | even |  |
| color_pass | softness | 0…90 | 20.0 | 0.02 | 0.48 | 0.81 | even |  |
| concat | crossfade | 0…10 | 0.0 |  |  |  | error |  |
| concat | gap | 0…10 | 0.0 |  |  |  | flat |  |
| crossmosh | decay | 0…1 | 0.9 |  |  |  | flat |  |
| crossmosh | frames | 2…60 | 9 |  |  |  | flat |  |
| crt_monitor | amount | 0…1 | 1.0 | 0.25 | 0.51 | 0.75 | even |  |
| crt_monitor | curvature | 0…0.4 | 0.1 | 0.48 | 0.72 | 0.88 | fast | pow:1.94 ✔ |
| crt_monitor | glow | 0…1 | 0.3 | 0.54 | 0.83 | 0.94 | early | pow:2.46 ✔ |
| crt_monitor | mask | 0…0.8 | 0.28 | 0.10 | 0.24 | 0.60 | slow | pow:0.58 ✔ |
| crt_monitor | scanlines | 0…1 | 0.45 | 0.08 | 0.34 | 0.67 | slow | pow:0.57 ✔ |
| deep_fry | intensity | 0…1 | 1.0 | 0.37 | 0.65 | 0.83 | fast | pow:1.45 ✔ |
| digital_boss | amount | 0…1 | 1.0 | 0.25 | 0.50 | 0.75 | even |  |
| dither | bayer_scale | 0…5 | 3 |  |  |  | flat |  |
| double_cup | amount | 0…1 | 1.0 | 0.25 | 0.51 | 0.76 | even |  |
| emboss | amount | 0…1 | 1.0 | 0.26 | 0.50 | 0.75 | even |  |
| emboss | angle | 0…360 | 135.0 | 0.70 | 1.00 | 0.68 | varies |  |
| emboss | strength | 0…4 | 1.0 | 0.75 | 0.88 | 0.95 | early | pow:3 |
| face_swap | amount | 0…1 | 1.0 |  |  |  | flat |  |
| face_swap | match | 0…1 | 0.85 |  |  |  | flat |  |
| face_swap | softness | 0…0.3 | 0.06 |  |  |  | flat |  |
| face_warp | amount | 0…1 | 1.0 |  |  |  | flat |  |
| face_warp | size | 0.5…2 | 1.0 |  |  |  | flat |  |
| face_warp | strength | 0…2 | 1.0 |  |  |  | flat |  |
| fade_flash | fade_in | 0…60 | 1.0 | 0.99 | 0.99 | 1.00 | early | pow:3 |
| fade_flash | fade_out | 0…60 | 1.0 | 1.00 | 0.50 | 0.32 | varies |  |
| fade_flash | flash_length | 0.04…5 | 0.25 |  |  |  | flat |  |
| feature_trails | dim | 0…1 | 0.45 | 0.25 | 0.50 | 0.75 | even |  |
| feature_trails | link_distance | 0…0.5 | 0.12 | 0.73 | 0.89 | 0.96 | early | pow:3 |
| feature_trails | points | 10…500 | 140 | 0.68 | 1.00 | 1.00 | early | pow:3 |
| feature_trails | trail_length | 2…60 | 10 | 0.89 | 1.00 | 1.00 | early | pow:3 |
| feedback_loop | decay | 0…1 | 0.7 | 0.05 | 0.14 | 0.34 | late | pow:0.43 ✔ |
| feedback_loop | hue_shift | -45…45 | 4.0 | 0.10 | 0.81 | 0.98 | early | pow:0.74 |
| feedback_loop | rotate | -30…30 | 1.0 | 0.41 | 1.00 | 0.78 | varies |  |
| feedback_loop | shift_x | -100…100 | 0.0 | 0.27 | 1.00 | 0.77 | varies |  |
| feedback_loop | shift_y | -100…100 | 0.0 | 0.71 | 0.92 | 1.00 | early | pow:3 |
| feedback_loop | threshold | 0…255 | 90 |  |  |  | flat |  |
| feedback_loop | zoom | -20…20 | 2.0 | 0.31 | 0.65 | 0.87 | even |  |
| fever | amount | 0…1 | 1.0 |  |  |  | flat |  |
| flow_warp | flow_width | 96…1280 | 320 | 0.99 | 1.00 | 1.00 | early | pow:3 |
| flow_warp | persistence | 0…1 | 0.9 | 0.17 | 0.31 | 0.47 | slow | pow:0.7 ✔ |
| flow_warp | strength | 0…15 | 3.0 | 0.66 | 0.75 | 0.86 | fast | pow:3 |
| frame_interpolate | slow_motion | 1…16 | 1.0 | 0.97 | 0.98 | 1.00 | early | pow:3 |
| freeze_punch | count | 1…20 | 4 |  |  |  | flat |  |
| freeze_punch | freeze_duration | 0.05…5 | 0.4 | 1.00 | 1.00 | 1.00 | early | log |
| freeze_punch | min_gap | 0…30 | 3.0 |  |  |  | flat |  |
| freeze_punch | scan_window | 0.1…5 | 0.5 | 0.98 | 1.00 | 1.00 | early | pow:3 |
| gamma_fix | gamma | 0.3…3 | 1.0 | 0.51 | 0.77 | 0.91 | fast | pow:2.2 ✔ |
| gamma_fix | max-contrast | 1…3 | 1.35 |  |  |  | flat |  |
| gamma_fix | min-contrast | 0.5…1.5 | 0.8 |  |  |  | flat |  |
| gamma_fix | sat | 0…3 | 1.0 |  |  |  | flat |  |
| gamma_fix | target-yavg | 16…235 | 64.0 |  |  |  | flat |  |
| ghostee | amount | 0…1 | 1.0 | 0.48 | 0.63 | 0.81 | even |  |
| glitch_tear | amount | 0…1 | 1.0 | 0.26 | 0.51 | 0.77 | even |  |
| glitch_tear | intensity | 0…1 | 0.5 | 0.30 | 0.71 | 0.80 | fast | pow:1.27 ✔ |
| glitch_tear | rgb_shift | 0…40 | 9 | 0.51 | 0.65 | 0.76 | fast | pow:1.89 ✔ |
| glitch_tear | tears | 0…16 | 4 | 0.32 | 0.62 | 0.83 | even |  |
| halftone | cell_size | 2…40 | 8 | 0.62 | 0.87 | 0.94 | early | pow:3 |
| hash_fingerprint | phash-fps | 0.1…10 | 0.5 |  |  |  | error |  |
| hash_fingerprint | phash-size | 4…32 | 8 |  |  |  | error |  |
| hue_cycle | amount | 0…1 | 1.0 | 0.24 | 0.49 | 0.75 | even |  |
| hue_cycle | speed | -360…360 | 60.0 | 0.79 | 1.00 | 0.83 | early |  |
| infrared | amount | 0…1 | 1.0 | 0.25 | 0.50 | 0.75 | even |  |
| infrared | saturation | 0…3 | 1.5 | 0.70 | 0.99 | 1.00 | early | pow:3 |
| insert_clip | entry_duration | 0…10 | 0.5 |  |  |  | error |  |
| insert_clip | exit_duration | 0…10 | 0.5 |  |  |  | error |  |
| key_feedback | decay | 0…0.99 | 0.9 | 0.03 | 0.08 | 0.21 | late | pow:0.35 |
| key_feedback | fb_high | 0…1 | 1.0 | 0.01 | 0.03 | 0.83 | late | pow:0.35 |
| key_feedback | fb_low | 0…1 | 0.15 | 0.16 | 0.53 | 0.98 | even |  |
| key_feedback | fb_similarity | 0.02…1 | 0.3 |  |  |  | flat |  |
| key_feedback | fb_soft | 0…0.5 | 0.1 | 0.17 | 0.39 | 0.68 | even |  |
| key_feedback | hue_shift | -45…45 | 4.0 | 0.42 | 1.00 | 0.28 | varies |  |
| key_feedback | insert_high | 0…1 | 1.0 | 0.00 | 0.00 | 0.97 | late | pow:0.35 |
| key_feedback | insert_low | 0…1 | 0.5 | 0.00 | 0.00 | 0.87 | late | pow:0.35 |
| key_feedback | insert_similarity | 0.02…1 | 0.3 | 0.01 | 0.01 | 0.06 | late | pow:0.35 |
| key_feedback | insert_soft | 0…0.5 | 0.1 | 0.08 | 0.20 | 0.37 | slow | pow:0.51 ✔ |
| key_feedback | rotate | -30…30 | 1.0 | 0.44 | 1.00 | 0.66 | varies |  |
| key_feedback | shift_x | -100…100 | 0.0 | 0.05 | 0.21 | 0.86 | slow | pow:0.48 |
| key_feedback | shift_y | -100…100 | 0.0 | 0.20 | 0.62 | 0.90 | even |  |
| key_feedback | zoom | -20…20 | 1.5 | 0.14 | 0.43 | 0.92 | even |  |
| kmeans_palette | pixel_size | 1…16 | 1 | 0.42 | 0.70 | 0.95 | fast | pow:1.7 ✔ |
| kmeans_palette | refresh | 1…120 | 24 | 1.00 | 1.00 | 1.00 | early |  |
| layer_blend | opacity_a | 0…100 | 75.0 | 0.25 | 0.50 | 0.76 | even |  |
| layer_blend | opacity_b | 0…100 | 25.0 | 0.34 | 0.59 | 0.81 | even |  |
| led_wall | amount | 0…1 | 1.0 | 0.25 | 0.50 | 0.75 | even |  |
| led_wall | brightness | 0.5…2 | 1.15 | 0.54 | 0.82 | 0.93 | early | pow:2.47 ✔ |
| led_wall | cell | 3…60 | 10 | 0.54 | 0.72 | 0.94 | fast | pow:2.26 ✔ |
| led_wall | dot | 0.3…1.3 | 1.0 | 0.14 | 0.36 | 0.66 | even |  |
| light_snow | amount | 0…1 | 1.0 | 0.24 | 0.49 | 0.75 | even |  |
| little_planet | amount | 0…1 | 1.0 | 0.25 | 0.50 | 0.75 | even |  |
| little_planet | curve | 0.3…2 | 0.8 | 0.51 | 0.76 | 0.92 | fast | pow:2.14 ✔ |
| little_planet | spin | -180…180 | 0.0 | 1.00 | 0.93 | 0.92 | early |  |
| lomo | amount | 0…1 | 1.0 | 0.25 | 0.50 | 0.75 | even |  |
| lomo | contrast | 0.4…2 | 1.0 |  |  |  | flat |  |
| lomo | saturation | 0…2.5 | 1.0 | 0.62 | 0.99 | 1.00 | early | pow:3 |
| lomo | vignette | 0…1.2 | 0.65 | 0.16 | 0.53 | 0.82 | even |  |
| long_exposure | amount | 0…1 | 1.0 | 0.25 | 0.50 | 0.75 | even |  |
| long_exposure | persistence | 0…0.99 | 0.85 | 0.16 | 0.33 | 0.58 | slow | pow:0.72 ✔ |
| lsd_feedback | amount | 0…1 | 1.0 | 0.28 | 0.54 | 0.81 | even |  |
| luma_key | feather | 0…10 | 1.0 | 0.21 | 0.48 | 0.76 | even |  |
| luma_key | shrink | 0…10 | 1 | 0.21 | 0.52 | 0.82 | even |  |
| luma_key | softness | 0…1 | 0.08 | 0.09 | 0.42 | 0.80 | even |  |
| luma_key | threshold | 0…1 | 0.5 |  |  |  | flat |  |
| lut_apply | brightness | -1…1 | 0.0 | 0.07 | 0.50 | 0.93 | even |  |
| lut_apply | contrast | 0…3 | 1.0 | 0.40 | 0.75 | 0.91 | fast | pow:1.67 ✔ |
| lut_apply | gamma | 0.1…3 | 1.0 | 0.52 | 0.78 | 0.92 | fast | pow:2.24 ✔ |
| lut_apply | saturation | 0…3 | 1.0 |  |  |  | flat |  |
| meta_extraction | black-dur-min | 0…5 | 0.1 |  |  |  | error |  |
| meta_extraction | black-pic-th | 0…1 | 0.1 |  |  |  | error |  |
| meta_extraction | sample-limit | 10…2000 | 200 |  |  |  | error |  |
| meta_extraction | sample-stride | 0.1…10 | 0.5 |  |  |  | error |  |
| mince | ac | 1…8 | 2 |  |  |  | flat |  |
| mince | ar | 8000…96000 | 48000 |  |  |  | error |  |
| mirror_delay | amount | 0…1 | 1.0 | 0.25 | 0.50 | 0.74 | even |  |
| motion_ghost | decay | 0…1 | 0.92 | 0.06 | 0.14 | 0.27 | late | pow:0.45 ✔ |
| motion_ghost | dim | 0…1 | 0.35 | 0.31 | 0.61 | 0.88 | even |  |
| motion_ghost | sensitivity | 0…1 | 0.5 | 0.24 | 0.42 | 0.64 | even |  |
| negative | amount | 0…1 | 1.0 | 0.25 | 0.50 | 0.75 | even |  |
| neon_edges | dim | 0…1 | 0.25 | 0.25 | 0.51 | 0.76 | even |  |
| neon_edges | glow | 0…50 | 12 | 0.86 | 0.95 | 0.97 | early | pow:3 |
| neon_edges | sensitivity | 0…1 | 0.7 | 0.25 | 0.44 | 0.66 | even |  |
| neon_edges | thickness | 1…10 | 2 | 0.35 | 0.70 | 0.86 | fast | pow:1.41 ✔ |
| night_vision | brightness | -0.5…0.5 | 0.05 | 0.19 | 0.47 | 0.76 | even |  |
| night_vision | grain | 0…60 | 18 | 0.32 | 0.47 | 0.79 | even |  |
| nostalgic_stutter | amount | 0…1 | 1.0 | 0.28 | 0.50 | 0.75 | even |  |
| oil_paint | amount | 0…1 | 1.0 | 0.26 | 0.47 | 0.76 | even |  |
| oil_paint | brush | 5…100 | 40.0 |  |  |  | flat |  |
| oil_paint | levels | 2…64 | 24 | 0.92 | 0.06 | 1.00 | varies |  |
| oil_paint | relief | 0…1 | 0.35 | 0.33 | 0.60 | 0.81 | even |  |
| old_film_damage | intensity | 0…1 | 1.0 | 0.17 | 0.64 | 0.72 | even |  |
| ordered_dither | levels | 2…16 | 2 |  |  |  | flat |  |
| ordered_dither | pixel_size | 1…16 | 2 | 0.34 | 0.58 | 0.83 | even |  |
| ordered_dither | strength | 0…1 | 1.0 | 0.23 | 0.71 | 0.87 | fast |  |
| overexposed_stutter | amount | 0…1 | 1.0 | 0.32 | 0.63 | 0.89 | even |  |
| photobooth | amount | 0…1 | 1.0 | 0.24 | 0.50 | 0.74 | even |  |
| pickle_juice | amount | 0…1 | 1.0 | 0.28 | 0.51 | 0.73 | even |  |
| picture_in_picture | border | 0…40 | 4 | 0.27 | 0.51 | 0.75 | even |  |
| picture_in_picture | margin | 0…30 | 3.0 | 0.70 | 0.89 | 1.00 | early | pow:3 |
| picture_in_picture | opacity | 0…100 | 100.0 | 0.26 | 0.50 | 0.75 | even |  |
| picture_in_picture | size | 5…100 | 30.0 | 0.23 | 0.78 | 1.00 | varies |  |
| picture_in_picture | x | 0…100 | 50.0 |  |  |  | flat |  |
| picture_in_picture | y | 0…100 | 50.0 |  |  |  | flat |  |
| pixel_sort | max_width | 0…4096 | 0 |  |  |  | flat |  |
| pixel_sort | threshold | 0…255 | None | 0.04 | 0.99 | 1.00 | early | pow:0.58 |
| pixelate | amount | 0…1 | 1.0 | 0.25 | 0.50 | 0.75 | even |  |
| pixelate | block | 2…200 | 16 | 0.10 | 0.12 | 0.54 | late | pow:0.51 |
| pop_art | amount | 0…1 | 1.0 | 0.25 | 0.50 | 0.75 | even |  |
| pop_art | high | 1…255 | 170 | 0.10 | 1.00 | 0.89 | early |  |
| pop_art | low | 0…254 | 90 | 0.18 | 0.50 | 1.00 | even |  |
| pop_art | palette | 0…3 | 0 |  |  |  | flat |  |
| posterize | amount | 0…1 | 1.0 | 0.22 | 0.35 | 0.74 | even |  |
| posterize | levels | 2…16 | 4 | 0.91 | 1.00 | 0.99 | early | pow:3 |
| proc_amp | black_level | 0…0.5 | 0.0 | 0.30 | 0.51 | 0.70 | even |  |
| proc_amp | brightness | -1…1 | 0.0 | 0.12 | 0.49 | 0.87 | even |  |
| proc_amp | contrast | 0…3 | 1.0 | 0.60 | 0.87 | 0.95 | early | pow:3 |
| proc_amp | gamma | 0.1…3 | 1.0 | 0.57 | 0.79 | 0.92 | fast | pow:2.59 ✔ |
| proc_amp | hue | -180…180 | 0.0 | 0.83 | 1.00 | 0.34 | varies |  |
| proc_amp | saturation | 0…3 | 1.0 | 0.76 | 1.00 | 0.85 | early |  |
| proc_amp | temperature | 2000…12000 | 6500.0 | 0.76 | 1.00 | 0.80 | varies |  |
| proc_amp | white_level | 0.5…1 | 1.0 | 0.24 | 0.46 | 0.66 | even |  |
| quad_split | gap | 0…60 | 4 | 0.34 | 0.61 | 0.79 | even |  |
| qwikchop | black-pict | 0…1 | 0.1 |  |  |  | error |  |
| qwikchop | black-scan | 0.05…2 | 0.25 |  |  |  | error |  |
| qwikchop | black-thresh | 0…1 | 0.1 |  |  |  | error |  |
| qwikchop | edge-pad-post | 0…0.5 | 0.02 |  |  |  | error |  |
| qwikchop | edge-pad-pre | 0…0.5 | 0.03 |  |  |  | error |  |
| qwikchop | min-edit | 0.05…5 | 0.2 |  |  |  | error |  |
| rb_blur | amount | 0…1 | 1.0 | 0.26 | 0.52 | 0.76 | even |  |
| recalled_sensor | amount | 0…1 | 1.0 | 0.28 | 0.55 | 0.81 | even |  |
| remove_background | feather | 0…10 | 1.0 | 0.21 | 0.50 | 0.77 | even |  |
| remove_background | sensitivity | 2…120 | 28.0 | 0.59 | 0.78 | 0.90 | fast | pow:2.63 ✔ |
| remove_background | shrink | 0…10 | 1 | 0.35 | 0.70 | 0.94 | fast | pow:1.45 |
| remove_background | softness | 0.02…1 | 0.25 |  |  |  | flat |  |
| remove_background | threshold | 0…1 | 0.5 |  |  |  | flat |  |
| repainting | amount | 0…1 | 1.0 | 0.24 | 0.50 | 0.74 | even |  |
| retro_dither | bayer_scale | 0…5 | 3 |  |  |  | flat |  |
| retro_dither | brightness | -0.5…0.5 | 0.0 | 0.65 | 0.75 | 0.81 | fast | pow:2.92 |
| retro_dither | contrast | 0.5…2 | 1.2 | 0.46 | 0.78 | 0.94 | fast | pow:1.95 ✔ |
| retro_dither | pixel_size | 1…16 | 2 | 0.41 | 0.62 | 0.88 | even |  |
| rgb_time_split | amount | 0…1 | 1.0 | 0.25 | 0.50 | 0.75 | even |  |
| rgb_time_split | delay_blue | 0…60 | 18 |  |  |  | flat |  |
| rgb_time_split | delay_green | 0…60 | 9 | 0.99 | 1.00 | 1.00 | early | pow:3 |
| rotate | angle | -180…180 | 180.0 | 0.60 | 1.00 | 0.60 | varies |  |
| rotate | spin | -360…360 | 0.0 | 0.49 | 1.00 | 0.50 | varies |  |
| sepia | amount | 0…1 | 1.0 | 0.25 | 0.50 | 0.75 | even |  |
| septic | amount | 0…1 | 1.0 | 0.30 | 0.53 | 0.77 | even |  |
| shape_synth | a_curve | -4…4 | 0.0 |  |  |  | flat |  |
| shape_synth | a_drift_x | -2…2 | 0.0 | 0.79 | 1.00 | 0.96 | early | pow:3 |
| shape_synth | a_drift_y | -2…2 | 0.0 | 0.66 | 1.00 | 0.94 | early |  |
| shape_synth | a_rotate | -180…180 | 0.0 |  |  |  | flat |  |
| shape_synth | a_size | 0.05…2.0 | 0.6 | 0.46 | 0.89 | 1.00 | varies |  |
| shape_synth | a_softness | 0…1 | 0.08 | 0.16 | 0.43 | 0.72 | even |  |
| shape_synth | a_spin | -360…360 | 0.0 |  |  |  | flat |  |
| shape_synth | a_stretch_x | 0.2…5 | 1.0 | 0.63 | 1.00 | 0.96 | early | pow:3 |
| shape_synth | a_stretch_y | 0.2…5 | 1.0 | 1.00 | 0.80 | 0.72 | varies |  |
| shape_synth | a_x | -2…2 | 0.0 | 0.65 | 1.00 | 0.76 | varies |  |
| shape_synth | a_y | -1.5…1.5 | 0.0 | 0.65 | 1.00 | 0.68 | varies |  |
| shape_synth | b_curve | -4…4 | 0.0 |  |  |  | flat |  |
| shape_synth | b_drift_x | -2…2 | 0.0 | 0.66 | 1.00 | 0.95 | early | pow:3 |
| shape_synth | b_drift_y | -2…2 | 0.0 | 0.73 | 1.00 | 1.00 | varies |  |
| shape_synth | b_fold | 1…12 | 1 | 1.00 | 0.97 | 0.96 | early | pow:3 |
| shape_synth | b_rotate | -180…180 | 0.0 |  |  |  | flat |  |
| shape_synth | b_size | 0.05…2.0 | 0.4 | 0.14 | 0.44 | 0.74 | even |  |
| shape_synth | b_softness | 0…1 | 0.08 | 0.22 | 0.48 | 0.74 | even |  |
| shape_synth | b_spin | -360…360 | 0.0 | 0.91 | 0.93 | 1.00 | varies |  |
| shape_synth | b_stretch_x | 0.2…5 | 1.0 | 0.34 | 0.59 | 0.80 | even |  |
| shape_synth | b_stretch_y | 0.2…5 | 1.0 | 0.35 | 0.68 | 0.89 | fast | pow:1.42 |
| shape_synth | b_x | -2…2 | 0.0 | 0.42 | 1.00 | 0.73 | varies |  |
| shape_synth | b_y | -1.5…1.5 | 0.0 | 0.89 | 1.00 | 0.83 | varies |  |
| shape_synth | feather | 0…10 | 1.0 |  |  |  | flat |  |
| shape_synth | opacity | 0…1 | 0.9 | 0.25 | 0.50 | 0.75 | even |  |
| shape_synth | shrink | 0…10 | 1 |  |  |  | flat |  |
| shape_synth | warp | 0…1 | 0.3 |  |  |  | flat |  |
| shortify | blur-sigma | 0…60 | 20.0 | 0.23 | 0.51 | 0.77 | even |  |
| sketch | range | 0…1 | 0.3 | 1.00 | 1.00 | 1.00 | early |  |
| sketch | shade | 0…0.2 | 0.05 | 0.97 | 0.99 | 0.99 | early | pow:3 |
| sketch | spatial | 10…200 | 60.0 | 0.91 | 0.97 | 0.99 | early | pow:3 |
| sketch | work_scale | 0.1…1 | 0.5 | 0.78 | 0.90 | 0.96 | early | pow:3 |
| slight_smear | amount | 0…1 | 1.0 | 0.28 | 0.51 | 0.75 | even |  |
| slit_scan | amount | 0…1 | 1.0 | 0.25 | 0.50 | 0.75 | even |  |
| slit_scan | bands | 8…200 | 48 |  |  |  | flat |  |
| slit_scan | depth | 4…120 | 48 | 0.96 | 0.99 | 0.99 | early | pow:3 |
| smudge | amount | 0…1 | 1.0 | 0.27 | 0.52 | 0.76 | even |  |
| soapblind | amount | 0…1 | 1.0 | 0.25 | 0.50 | 0.75 | even |  |
| solarize | amount | 0…1 | 1.0 | 0.25 | 0.50 | 0.75 | even |  |
| solarize | threshold | 1…254 | 128 | 0.06 | 0.07 | 0.07 | late | pow:0.38 |
| soundtrack | duck_amount | 1…20 | 8.0 |  |  |  | flat |  |
| soundtrack | fade_in | 0…30 | 0.0 |  |  |  | flat |  |
| soundtrack | music_volume | 0…200 | 100.0 |  |  |  | flat |  |
| soundtrack | original_volume | 0…200 | 100.0 |  |  |  | flat |  |
| soundtrack | start | 0…3600 | 0.0 |  |  |  | flat |  |
| soundtrack | trim_start | 0…3600 | 0.0 |  |  |  | flat |  |
| splitting | amount | 0…1 | 1.0 | 0.26 | 0.47 | 0.75 | even |  |
| stabilize | analysis_width | 160…1280 | 480 | 0.75 | 1.00 | 1.00 | early | pow:3 |
| stabilize | smoothness | 1…120 | 30 | 0.81 | 0.93 | 0.98 | early | log ✔ |
| stabilize | zoom | 1…1.5 | 1.06 | 0.41 | 0.64 | 0.84 | even |  |
| stack_2x | gap | 0…80 | 0 | 0.35 | 0.62 | 0.84 | even |  |
| stackadelic | complex_amount | 0…1 | 0.2 |  |  |  | flat |  |
| stackadelic | feather | 0…10 | 1.0 |  |  |  | flat |  |
| stackadelic | l1_bottom | 0…100 | 65 | 0.27 | 0.51 | 0.76 | even |  |
| stackadelic | l1_left | 0…100 | 35 | 0.20 | 0.55 | 0.76 | even |  |
| stackadelic | l1_opacity | 0…1 | 1.0 | 0.25 | 0.50 | 0.75 | even |  |
| stackadelic | l1_ratio | 0.25…4 | 1.0 | 0.84 | 0.94 | 0.98 | early | pow:3 |
| stackadelic | l1_right | 0…100 | 65 | 0.20 | 0.54 | 0.76 | even |  |
| stackadelic | l1_rotate | -180…180 | 0.0 | 1.00 | 0.00 | 1.00 | varies |  |
| stackadelic | l1_size | 0.1…3 | 1.0 | 0.10 | 0.31 | 0.57 | slow | pow:0.6 |
| stackadelic | l1_softness | 0…0.5 | 0.03 | 0.18 | 0.44 | 0.73 | even |  |
| stackadelic | l1_tiles | 1…12 | 1 | 0.96 | 0.96 | 0.97 | early | pow:3 |
| stackadelic | l1_top | 0…100 | 35 | 0.27 | 0.52 | 0.76 | even |  |
| stackadelic | l2_bottom | 0…100 | 78 | 0.16 | 0.34 | 0.58 | slow | pow:0.72 |
| stackadelic | l2_left | 0…100 | 22 | 0.47 | 0.69 | 0.79 | fast | pow:1.8 |
| stackadelic | l2_ratio | 0.25…4 | 1.0 | 0.56 | 0.83 | 1.00 | early | pow:2.64 |
| stackadelic | l2_right | 0…100 | 78 | 0.45 | 0.68 | 0.78 | fast | pow:1.74 |
| stackadelic | l2_rotate | -180…180 | 0.0 | 1.00 | 0.00 | 1.00 | varies |  |
| stackadelic | l2_size | 0.1…3 | 1.0 | 0.12 | 0.71 | 1.00 | fast |  |
| stackadelic | l2_softness | 0…0.5 | 0.03 |  |  |  | flat |  |
| stackadelic | l2_tiles | 1…12 | 1 | 1.00 | 0.79 | 0.90 | varies |  |
| stackadelic | l2_top | 0…100 | 22 | 0.18 | 0.35 | 0.59 | even |  |
| stackadelic | l3_bottom | 0…100 | 92 |  |  |  | flat |  |
| stackadelic | l3_left | 0…100 | 8 |  |  |  | flat |  |
| stackadelic | l3_opacity | 0…1 | 0.0 | 0.25 | 0.50 | 0.75 | even |  |
| stackadelic | l3_ratio | 0.25…4 | 1.0 |  |  |  | flat |  |
| stackadelic | l3_right | 0…100 | 92 |  |  |  | flat |  |
| stackadelic | l3_rotate | -180…180 | 0.0 |  |  |  | flat |  |
| stackadelic | l3_size | 0.1…3 | 1.0 |  |  |  | flat |  |
| stackadelic | l3_softness | 0…0.5 | 0.03 |  |  |  | flat |  |
| stackadelic | l3_tiles | 1…12 | 1 |  |  |  | flat |  |
| stackadelic | l3_top | 0…100 | 8 |  |  |  | flat |  |
| stackadelic | shrink | 0…10 | 1 |  |  |  | flat |  |
| steel_wash | amount | 0…1 | 1.0 | 0.31 | 0.53 | 0.77 | even |  |
| strobe_cut | flash_duration | 0.01…2 | 0.05 | 1.00 | 1.00 | 1.00 | early |  |
| strobe_cut | period | 0.05…10 | 0.5 | 1.00 | 1.00 | 1.00 | early |  |
| strobe_hold | blink | 0…100 | 0.0 | 0.00 | 0.00 | 1.00 | late | pow:0.35 |
| strobe_hold | hold | 1…60 | 4 | 0.90 | 1.00 | 1.00 | early | pow:3 |
| subs_convert | time-shift | -60…60 | 0.0 |  |  |  | error |  |
| t1000 | amount | 0…1 | 1.0 | 0.27 | 0.51 | 0.76 | even |  |
| thermal | amount | 0…1 | 1.0 | 0.25 | 0.50 | 0.76 | even |  |
| thumbs | jpeg-quality | 1…31 | 3 |  |  |  | flat |  |
| thumbs | margin | 0…100 | 12 | 0.43 | 0.70 | 0.89 | fast | pow:1.7 |
| thumbs | padding | 0…100 | 6 |  |  |  | error |  |
| thumbs | scene-threshold | 0…1 | 0.4 |  |  |  | flat |  |
| time_ramp | end_factor | 0.1…8 | 2.0 | 0.99 | 1.00 | 0.88 | early |  |
| time_ramp | start_factor | 0.1…8 | 0.5 | 1.00 | 1.00 | 1.00 | early | pow:3 |
| time_ramp | steps | 2…30 | 6 | 0.55 | 0.55 | 0.81 | even |  |
| tonemap_hdr_sdr | desat | 0…1 | 0.0 | 1.00 | 0.87 | 0.70 | early |  |
| tonemap_hdr_sdr | peak | 100…10000 | 1000.0 | 0.95 | 0.98 | 1.00 | early | log ✔ |
| topobeaux | amount | 0…1 | 0.8 |  |  |  | flat |  |
| topobeaux | bands | 2…6 | 5 | 0.80 | 1.00 | 0.87 | early |  |
| topobeaux | dim | 0…1 | 0.4 |  |  |  | flat |  |
| topobeaux | feather | 0…10 | 1.0 |  |  |  | flat |  |
| topobeaux | line_width | 1…12 | 2 |  |  |  | flat |  |
| topobeaux | scan_depth | 0…0.5 | 0.15 |  |  |  | flat |  |
| topobeaux | scan_speed | 0…4 | 0.0 | 0.94 | 1.00 | 0.93 | early |  |
| topobeaux | shrink | 0…10 | 1 |  |  |  | flat |  |
| topobeaux | softness | 0…0.5 | 0.0 | 0.35 | 0.54 | 0.79 | even |  |
| triptych | panel_size | 0…4320 | 0 | 0.01 | 1.00 | 1.00 | early | pow:0.38 |
| triptych | vol1 | 0…2 | 1.0 |  |  |  | flat |  |
| triptych | vol2 | 0…2 | 1.0 |  |  |  | flat |  |
| triptych | vol3 | 0…2 | 1.0 |  |  |  | flat |  |
| triptych | zoom1 | 1…4 | 1.0 | 0.58 | 0.83 | 1.00 | early | pow:2.79 |
| triptych | zoom2 | 1…4 | 1.0 | 0.59 | 0.84 | 0.99 | early | pow:2.95 |
| triptych | zoom3 | 1…4 | 1.0 | 0.61 | 0.85 | 1.00 | early | pow:3 |
| tunnel | amount | 0…1 | 1.0 | 0.25 | 0.50 | 0.75 | even |  |
| tunnel | around | 1…8 | 3 | 0.76 | 1.00 | 0.96 | early | pow:3 |
| tunnel | deep | 1…10 | 4 | 0.91 | 0.95 | 1.00 | early | pow:3 |
| tunnel | speed | -400…400 | 90.0 | 0.95 | 0.88 | 1.00 | early |  |
| twociz | amount | 0…1 | 1.0 | 0.29 | 0.58 | 0.85 | even |  |
| vhs_camcorder | amount | 0…1 | 1.0 | 0.24 | 0.50 | 0.75 | even |  |
| vhs_camcorder | noise | 0…30 | 7.0 | 0.25 | 0.50 | 0.75 | even |  |
| vhs_tracking | intensity | 0…1 | 1.0 | 0.28 | 0.42 | 0.58 | even |  |
| vhs_tracking | speed | 0…30 | 6.0 | 0.99 | 0.92 | 0.94 | early |  |
| video_wall | cols | 1…12 | 3 | 0.95 | 1.00 | 0.99 | early | pow:3 |
| video_wall | delay | 1…30 | 4 |  |  |  | flat |  |
| video_wall | gap | 0…40 | 0 | 0.33 | 0.58 | 0.80 | even |  |
| video_wall | rows | 1…12 | 3 | 1.00 | 1.00 | 0.98 | early | pow:3 |
| warp | amount | 0…1 | 1.0 | 0.31 | 0.55 | 0.78 | even |  |
| warp | center_x | 0…1 | 0.5 | 0.51 | 1.00 | 0.74 | varies |  |
| warp | center_y | 0…1 | 0.5 | 0.56 | 0.93 | 1.00 | early | pow:2.91 |
| warp | radius | 0.05…1.5 | 0.7 | 0.12 | 0.47 | 0.79 | even |  |
| warp | segments | 2…32 | 6 |  |  |  | flat |  |
| watermark | end | 0…3600 | 0.0 |  |  |  | flat |  |
| watermark | margin | 0…500 | 24 | 0.74 | 1.00 | 0.27 | varies |  |
| watermark | opacity | 0…1 | 0.8 | 0.29 | 0.54 | 0.78 | even |  |
| watermark | scale | 0.02…1 | 0.25 | 0.04 | 0.19 | 0.47 | late | pow:0.43 ✔ |
| watermark | spin | -360…360 | 0.0 |  |  |  | flat |  |
| watermark | start | 0…3600 | 0.0 | 1.00 | 1.00 | 1.00 | early |  |
| watermark | video-crf | 0…51 | 18 | 0.01 | 0.05 | 0.20 | late | pow:0.35 |
| watermark | wm-loop | 0…50 | 0 |  |  |  | flat |  |
| wbflare | amount | 0…1 | 1.0 | 0.26 | 0.49 | 0.76 | even |  |
| weak_signal | amount | 0…1 | 1.0 | 0.23 | 0.51 | 0.69 | even |  |
| weak_signal | bursts | 0…1 | 0.35 | 0.83 | 0.92 | 0.99 | early | pow:3 |
| weak_signal | noise | 0…60 | 14.0 | 0.48 | 0.70 | 0.82 | fast | pow:1.89 ✔ |
| weak_signal | skew | 0…0.2 | 0.035 | 0.41 | 0.61 | 0.81 | even |  |
| weak_signal | speckle | 0…0.2 | 0.02 | 0.43 | 0.57 | 0.79 | even |  |
| weak_signal | streaks | 0…30 | 5 | 0.59 | 0.81 | 0.86 | early | pow:2.68 ✔ |
| wipe_transitions | duration | 0.1…10 | 1.0 |  |  |  | error |  |
| wipe_transitions | offset | 0…3600 | 3.0 | 1.00 | 1.00 | 1.00 | early |  |
| xpiritualism | bloom-radius | 0…40 | 8.0 | 0.34 | 0.59 | 0.80 | even |  |
| xpiritualism | bloom-strength | 0…1 | 0.7 | 0.24 | 0.50 | 0.74 | even |  |
| xpiritualism | grain | 0…40 | 8.0 |  |  |  | flat |  |
| xpiritualism | hue-shift | -180…180 | 0.0 |  |  |  | flat |  |
| xpiritualism | saturation | 0…3 | 1.15 |  |  |  | flat |  |
| xpiritualism | vignette | 0…1 | 0.35 | 0.25 | 0.50 | 0.76 | even |  |
| xrgb | amount | 0…1 | 1.0 | 0.25 | 0.50 | 0.75 | even |  |
| zapruder | amount | 0…1 | 1.0 | 0.25 | 0.50 | 0.75 | even |  |
