<p align="center">
  <img width="45%" height="45%" src="https://github.com/schwwaaa/videobeaux/blob/main/img/videobeaux-1.png?raw=true"/>  
</p>

<p align="center"><em>The friendly multilateral video toolkit built for artists by artists. It's your best friend.</em></p> 

## Project dependencies
### macOS/Linux

In the shell prompt, go to the place where you want the project to live. Paste that in a macOS Terminal or Linux shell prompt & run it.

``` bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/schwwaaa/videobeaux/refs/heads/main/install.sh)"
```

### Windows

``` powershell 
choco install ffmpeg
setx VIDEOBEAUX_PATH "C:\videobeaux"
```

## Usage

### Activate virtual environment
This will activate your virtual environment. Immediately, you will notice that your terminal path includes env, signifying an activated virtual environment.
``` bash
source env/bin/activate
```

### Check the installation

### Get help and find out more about videobeaux
``` bash
videobeaux --help
```
... outputs the following ...

```bash
       _     _            _
__   _(_) __| | ___  ___ | |__   ___  __ _ _   ___  __
\ \ / / |/ _` |/ _ \/ _ \| '_ \ / _ \/ _` | | | \ \/ /
 \ V /| | (_| |  __/ (_) | |_) |  __/ (_| | |_| |>  <
  \_/ |_|\__,_|\___|\___/|_.__/ \___|\__,_|\__,_/_/\_\


📺 The friendly multilateral video toolkit built for artists by artists.
🫂  It's your best friend!

🌐 https://schwwaaa.net

usage: videobeaux --program PROGRAM --input INPUT_FILE --output OUTPUT_FILE [program options]

options:
  -P, --program PROGRAM
                        Name of the effect program to run (e.g. convert, glitch)
  -i, --input INPUT     Input video file - mp4 only
  -o, --output OUTPUT   Output file name, no extension. Output will be saved as mp4.
  -F, --force           Force overwrite output file
  -h, --help            Show help message and exit

Available Program Modes:

bad_animation        download_yt          lsd_feedback_pro     repainting           subs_convert
bad_contrast         extract_frames       lut_apply            resize               t1000
bad_predator         extract_sound        meta_extraction      reverse              thumbs
ball_point_pen       fever                mince                scrolling_pro        tonemap_hdr_sdr
blur_pix             frame_delay_pro1     mirror_delay         septic               transcraibe
broken_scroll        frame_delay_pro2     nostalgic_stutter    silence_xtraction    triptych
captburn             frame_interpolate    num_edits            slight_smear         twociz
chain_builder        gamma_fix            overexposed_stutter  smudge               twociz_pro
chain_builder_pro    ghostee              overlay_img_pro      soapblind            watermark
convert              hash_fingerprint     pickle_juice         speed                wbflare
convert_dims         lagkage              qwikchop             splitting            wbflare_pro
convert_mux          lagkage-old          rb_blur              splitting_pro        wipe_transitions
crossmosh            light_snow           rb_blur_pro          stack_2x             xpiritualism
digital_boss         looper_pro           recalled_sensor      steel_wash           xrgb
double_cup           lsd_feedback         recalled_sensor_pro  stutter_pro          zapruder
  ```

## Available Programs
An overview of each program can be find in this [YouTube playlist](https://www.youtube.com/watch?v=7i-WaDgBkcI&list=PLmyETqg8KgDcwV3-JnGoAiQyjR764sBI_).

### Effects 

| Program | Description | Arguments |
| -------- | ------- | ------- | 
| bad_animation | Apply a bad animation effect | - |
| bad_contrast | Apply a bad constrast effect | - |
| ball_point_pen | Apply a ball point pen style effect | - |
| blur_pix | Extracting the silence out of a video file | - |
| bad_predator | Apply bad Predator heat vision effect | - |
| crossmosh | A controlled datamoshing engine that manipulates motion vectors and frame order to create stylized glitch-drift distortions | b_input, outfile, codec, qscale, gop, keep_temp, mode, frames, decay, blend |
| digital_boss | Apply busted gameboy style digital boss effect | - |
| double_cup | Apply the effect of purple drank | - |
| frame_delay_pro1 | Apply frame delay effect with parameter input | frame_quantity, frame_weights |
| frame_delay_pro2 | Apply frame delay effect with parameter input | decay, plane |
| ghostee | Apply a slight ghost effect | - |
| lagkage | A JSON-driven multilayer video compositor that stacks, positions, resizes, and mixes multiple media sources into one unified output | layout_json, sequence_direction, audio_mode, audio_src |
| looper_pro | Apply video looper effect base on frame size & start frame | - |
| lsd_feedback | Apply LSD-like frame delay effect | - |
| mince | A fast, lossless segment-extractor and concatenator that slices videos into parts and recombines them with precision | mode, seed, engine, normalize, size, fit, fps, pixfmt, ar, ac, norm_vcodec, norm_crf, norm_preset, vcodec, acodec, crf, preset, faststart, fallback_reencode, decode_tolerant, hard_trim |
| mirror_delay | Apply a frame delay plus a mirrored effect | - |
| nostalgic_stutter | Apply frame stutter akin to a corrupted file | - |
| overexposed_stutter | Apply a frame stutter and exposing the video like the- | file is corrupted | - |
| overlay_img_pro | Overlay an image with location & dimension control | overlay_img, x_pos, y_pos, img_height, img_width |
| pickle_juice | Apply filter like the video was dipped in pickle juice | - |
| recalled_sensor | Apply filter like a sensor was broken and to-be recalled |- |
| repainting | Apply filter like repainting the same image while smudged with- | alcohol |- |
| resize | Resizing the dimensions of a video file | new_height, new_width |
| reverse | Reverse video file | - |
| scrolling_pro | Apply video scrolling effect with definable parameters | horiz_speed, vert_speed |
| scrolling | Apply static video scrolling effect | - |
| septic | Apply filter like a person in septic shock | - |
| slight_smear | Slightly smearing RGB color space |  - |
| smudge | Smudging image slightly |  - |
| soapblind | Apply filter like soap blinded eyes |  - |
| speed | Change the video and audio speed of a file | speed_factor |
| splitting | A simple segmentation utility that divides a video into evenly timed chunks or scene-based fragments for modular editing | - |
| splitting_pro | Precise segmentation tool that slices a source video into reusable chunks based on time, count, or scene-style rules for downstream editing and recombination. | width, position |
| stack_2x | Stack 2 videos on top of each other keeping the original- | orientation | input2 |
| steel_wash | Apply steel blue filter to video | - |
| stutter_pro | Apply frame stutter effect with definable parameters | stutter |
| t1000 | Apply filter from the perspective of liquid T-1000 | - |
| twociz | Apply filter from the perspective of a zombie on TC-1 hallucinogens | - |
| wbflare | Apply filter with a blown out white-balance flare | - |
| zapruder | Apply zapruder-film like effect | - |
| xrgb | Extreme RGB adjustment | - |

### Utilities

| Program | Description | Arguments |
| -------- | ------- | ------- | 
| captburn | Burns subtitles, captions, or transcript text directly into the video with precise styling, timing, and layout control | caption, style, rollup_lines, words_per_line, font, font_size, bold, italic, primary, outline, outline_width, shadow, back, back_opacity, scale_x, scale_y, spacing, rotate, margin_l, margin_r, margin_v, align, border_style, x, y, move, vcodec, crf, preset |
| chain_builder | Assembles a sequence of videobeaux program steps into a single automated workflow, chaining multiple transformations into one output | chain |
| convert | Simple video file convert | - |
| convert_dims | Video file dimensions converter based on industry standards  | - |
| convert_mux | Rewraps or converts media streams while copying or re-encoding video/audio, ideal for fixing containers, codecs, or sync issues. | format, profile, vcodec, acodec, crf, bitrate, maxrate, bufsize, preset, profile_v, level, pix_fmt, gop, r, vf, tagv, abitrate, ac, ar, copy |
| download_yt | Video ripper | - |
| extract_frames | Extract individuals frames from a video file as PNGs | - |
| extract_sound | Extract audio from video file | - |
| frame_interpolate | Generates smooth slow-motion or higher-FPS video by creating intermediate frames using motion-compensated interpolation | outfile, engine, fps, multiplier, mi_mode, me_mode, mc_mode, vsbmc, scd, x264_preset, crf, copy_audio, rife_bin, dain_bin |
| gamma_fix | Normalizes gamma, brightness, and exposure levels for broadcast-safe or web-safe consistency across diverse footage | target_yavg, min_contrast, max_contrast, gamma, sat, legalize, vcodec, crf, preset, acodec, ab |
| hash_fingerprint | Creates unique perceptual or checksum-style fingerprints of a video for identification, comparison, or deduplication | recursive, exts, file_hashes, stream_hash, framemd5, phash, phash_fps, phash_size, catalog, stream_kind |
| lut_apply | Applies a 3D or 1D LUT file to recolor a video, enabling film-style grading, color transforms, or creative look development | outfile, vcodec, lut, interp, intensity, brightness, contrast, saturation, gamma, pix_fmt, x264_preset, crf, copy_audio |
| meta_extraction | Extracts detailed metadata—including codecs, bitrates, dimensions, color info, and stream structure—from any media file | outputfile, sample_frames, sample_stride, sample_limit, blackdetect, black_pic_th, black_dur_min, loudness |
| num_edits | Analyzes a timeline or cut structure to count edits, transitions, or shot boundaries for editorial statistics or QC | count |
| qwikchop | Rapidly slices videos into precise segments based on timecodes or cut lists, optimized for speed and batch operations | pieces, recurse, keep_temp, trim_black_front, black_scan, black_thresh, black_pict, edge_pad_pre, edge_pad_post, min_edit |
| silence_extraction | Extracting the silence out of a video file | min_d, max_d, adjuster |
| subs_convert | Converts subtitle files between formats (e.g., SRT, VTT, ASS), preserving timing, text, and style metadata | list, indexes, langs, all, forced_only, exclude_hi, format, outdir, outputfile, time_shift |
| thumbs | Generates thumbnails or contact sheets by sampling frames at chosen intervals for previews, galleries, or QC review | fps, scene, scene_threshold, tile, scale, timestamps, label, fontfile, bg, margin, padding, outdir, outputfile, image_format, jpeg_quality |
| tonemap_hdr_sdr | Converts HDR footage (PQ/HLG) to SDR using tunable tonemapping curves, preserving highlight detail and color accuracy | outfile, algo, desat, peak, dither, pix_fmt, x264_preset, crf, copy_audio |
| transraibe | AI-based transcription tool | stt_model |
| watermark | Applies image or text watermarks onto video with configurable positioning, scaling, opacity, and blend style | watermark, placement, margin, scale, opacity, spin, start, end, wm_loop, ignore_loop, video_crf, video_preset |
| wipe_transitions | Creates directional wipe transitions between clips using customizable timing, edge softness, and motion orientation | input1, input2, output_format, preset, duration, offset |
