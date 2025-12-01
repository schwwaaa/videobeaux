---
layout: default
title: Examples
nav_order: 4
---

# Examples

## Running a program that does not have additional arguments

### Check if the program needs additional arguments

```bash
       _     _            _
__   _(_) __| | ___  ___ | |__   ___  __ _ _   ___  __
\ \ / / |/ _` |/ _ \/ _ \| '_ \ / _ \/ _` | | | \ \/ /
 \ V /| | (_| |  __/ (_) | |_) |  __/ (_| | |_| |>  <
  \_/ |_|\__,_|\___|\___/|_.__/ \___|\__,_|\__,_/_/\_\


Your friendly multilateral video toolkit built for artists by artists.
https://schwwaaa.net
--------------------------------------------------
Selected program mode: bad_predator
✅ This program mode does not require additional arguments
usage: python3 -m videobeaux.cli --program PROGRAM [global options] [program options]

📺 Your friendly multilateral video toolkit built for artists by artists.
 It's your best friend!
https://schwwaaa.net

options:
  -P PROGRAM, --program PROGRAM
                        Name of the effect program to run (e.g. convert, glitch)
  -i INPUT, --input INPUT
                        Input video file - mp4 only
  -o OUTPUT, --output OUTPUT
                        Output file name, no extension. Output will be saved as mp4.
  -F, --force           Force overwrite output file
  -h, --help            Show help message and exit

 👁️ 👇 Additional help for program mode 👇 👁️
usage: videobeaux --program bad_predator [-h]

Apply bad Predator heat vision effect

options:
  -h, --help  show this help message and exit
```
### Run the program

``` bash
videobeaux --program PROGRAM --input INPUT_FILE --output OUTPUT_FILE
```
... translates to ...

``` bash
videobeaux --program bad_predator --input example.mp4 --output example_bp.mp4
```
### Output of the program
``` bash
       _     _            _
__   _(_) __| | ___  ___ | |__   ___  __ _ _   ___  __
\ \ / / |/ _` |/ _ \/ _ \| '_ \ / _ \/ _` | | | \ \/ /
 \ V /| | (_| |  __/ (_) | |_) |  __/ (_| | |_| |>  <
  \_/ |_|\__,_|\___|\___/|_.__/ \___|\__,_|\__,_/_/\_\


Your friendly multilateral video toolkit built for artists by artists.
https://schwwaaa.net
--------------------------------------------------
Selected program mode: bad_predator
✅ This program mode does not require additional arguments
Input duration: 10.01 seconds
🔨 Processing example.mp4: 100%|██████████████████████████████████████████████████████ | 10.01/10.01s [00:04<00:00]

📺 Process Complete: example_bp.mp4
```

<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/user-attachments/assets/fe45aa80-9878-4d15-bc64-87dd25071855" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Running a program that does have additional arguments

### Check if the program needs additional arguments
``` bash
       _     _            _
__   _(_) __| | ___  ___ | |__   ___  __ _ _   ___  __
\ \ / / |/ _` |/ _ \/ _ \| '_ \ / _ \/ _` | | | \ \/ /
 \ V /| | (_| |  __/ (_) | |_) |  __/ (_| | |_| |>  <
  \_/ |_|\__,_|\___|\___/|_.__/ \___|\__,_|\__,_/_/\_\


Your friendly multilateral video toolkit built for artists by artists.
https://schwwaaa.net
--------------------------------------------------
Selected program mode: stutter_pro
usage: python3 -m videobeaux.cli --program PROGRAM [global options] [program options]

📺 Your friendly multilateral video toolkit built for artists by artists.
 It's your best friend!
https://schwwaaa.net

options:
  -P PROGRAM, --program PROGRAM
                        Name of the effect program to run (e.g. convert, glitch)
  -i INPUT, --input INPUT
                        Input video file - mp4 only
  -o OUTPUT, --output OUTPUT
                        Output file name, no extension. Output will be saved as mp4.
  -F, --force           Force overwrite output file
  -h, --help            Show help message and exit

 👁️ 👇 Additional help for program mode 👇 👁️
usage: videobeaux --program stutter_pro [-h] --stutter STUTTER

Imagine watching a video where random frames are played instead of a smooth progression.

options:
  -h, --help         show this help message and exit
  --stutter STUTTER  Replaces the current video frame with a randomly selected one from the most recent N frames.The larger the value, the larger the variation.
```

### Run the program
``` bash
videobeaux --program PROGRAM --input INPUT_FILE --output OUTPUT_FILE --args ARGUMENTS
```

... translates to ...

``` bash
videobeaux --program stutter_pro -i example.mp4 -o stutter_example.mp4 --stutter 2
```
### Output of the program
```bash      
       _     _            _
__   _(_) __| | ___  ___ | |__   ___  __ _ _   ___  __
\ \ / / |/ _` |/ _ \/ _ \| '_ \ / _ \/ _` | | | \ \/ /
 \ V /| | (_| |  __/ (_) | |_) |  __/ (_| | |_| |>  <
  \_/ |_|\__,_|\___|\___/|_.__/ \___|\__,_|\__,_/_/\_\


Your friendly multilateral video toolkit built for artists by artists.
https://schwwaaa.net
--------------------------------------------------
Selected program mode: stutter_pro
Input duration: 10.01 seconds
🔨 Processing example.mp4: 100%|██████████████████████████████████████████████████████████ | 10.01/10.01s [00:00<00:00]

📺 Process Complete: stutter_example.mp4
```

<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/user-attachments/assets/fec22179-8e40-49e5-b591-c9d5fb07e31b" type="video/mp4">
  Your browser does not support the video tag.
</video>


## Running a program to chain process a video
### Find out more information about the program

``` bash
       _     _            _
__   _(_) __| | ___  ___ | |__   ___  __ _ _   ___  __
\ \ / / |/ _` |/ _ \/ _ \| '_ \ / _ \/ _` | | | \ \/ /
 \ V /| | (_| |  __/ (_) | |_) |  __/ (_| | |_| |>  <
  \_/ |_|\__,_|\___|\___/|_.__/ \___|\__,_|\__,_/_/\_\


Your friendly multilateral video toolkit built for artists by artists.
https://schwwaaa.net
--------------------------------------------------
Selected program mode: chain_builder
usage: python3 -m videobeaux.cli --program PROGRAM [global options] [program options]

📺 Your friendly multilateral video toolkit built for artists by artists.
 It's your best friend!
https://schwwaaa.net

options:
  -P PROGRAM, --program PROGRAM
                        Name of the effect program to run (e.g. convert, glitch)
  -i INPUT, --input INPUT
                        Input video file - mp4 only
  -o OUTPUT, --output OUTPUT
                        Output file name, no extension. Output will be saved as mp4.
  -F, --force           Force overwrite output file
  -h, --help            Show help message and exit

 👁️ 👇 Additional help for program mode 👇 👁️
usage: videobeaux --program chain_builder [-h] --chain CHAIN

The output of the first will be used as the input for the next, and so on.
Only supports program modes that do not require their own specific arguments.

options:
  -h, --help     show this help message and exit
  --chain CHAIN  A comma separated list of programs to run.
```
### Run the program
``` bash
videobeaux --program PROGRAM --input INPUT_FILE --output OUTPUT_FILE --chain CHAIN
```
... translates to ...

```bash
videobeaux --program chain_builder --input example.mp4 --output chainedoutput.mp4 --chain rb_blur,soapblind,lsd_feedback --force
```

### Output of the program
``` bash
       _     _            _
__   _(_) __| | ___  ___ | |__   ___  __ _ _   ___  __
\ \ / / |/ _` |/ _ \/ _ \| '_ \ / _ \/ _` | | | \ \/ /
 \ V /| | (_| |  __/ (_) | |_) |  __/ (_| | |_| |>  <
  \_/ |_|\__,_|\___|\___/|_.__/ \___|\__,_|\__,_/_/\_\


Your friendly multilateral video toolkit built for artists by artists.
https://schwwaaa.net
--------------------------------------------------
Selected program mode: chain_builder
🔁 Running step 1/3: rb_blur
Input duration: 10.01 seconds
🔨 Processing example.mp4: 100%|██████████████████████████████████████████████████████ | 10.01/10.01s [00:00<00:00]

📺 Process Complete: /var/folders/jv/lp20pdtn4jsgjpxw710m0vkm0000gn/T/videobeaux_chain_z7ixo5cs/step_0_rb_blur.mp4

🔁 Running step 2/3: soapblind
Input duration: 10.03 seconds
🔨 Processing step_0_rb_blur.mp4: 100%|███████████████████████████████████████████████ | 10.03/10.03s [00:46<00:00]

📺 Process Complete: /var/folders/jv/lp20pdtn4jsgjpxw710m0vkm0000gn/T/videobeaux_chain_z7ixo5cs/step_1_soapblind.mp4

🔁 Running step 3/3: lsd_feedback
Input duration: 10.03 seconds
🔨 Processing step_1_soapblind.mp4: 100%|█████████████████████████████████████████████ | 10.03/10.03s [00:03<00:00]

📺 Process Complete: /var/folders/jv/lp20pdtn4jsgjpxw710m0vkm0000gn/T/videobeaux_chain_z7ixo5cs/step_2_lsd_feedback.mp4

✅ Final output written to chainedoutput.mp4
```

<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/user-attachments/assets/ac321c77-4757-4846-b838-6847472e7e09" type="video/mp4">
  Your browser does not support the video tag.
</video>

