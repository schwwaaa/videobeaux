---
layout: default
title: Getting Started
nav_order: 2
---

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
