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

🌐 https://schwwaaa.com

usage: videobeaux --program PROGRAM --input INPUT_FILE --output OUTPUT_FILE [program options]

options:
  -P, --program PROGRAM
                        Name of the effect program to run (e.g. convert, glitch)
  -i, --input INPUT     Input video file - mp4 only
  -o, --output OUTPUT   Output file name, no extension. Output will be saved as mp4.
  -F, --force           Force overwrite output file
  -h, --help            Show help message and exit

Available Program Modes:

bad_animation        extract_sound        pickle_juice         splitting
bad_contrast         fever                rb_blur              stack_2x
bad_predator         frame_delay_pro1     recalled_sensor      steel_wash
ball_point_pen       frame_delay_pro2     repainting           stutter_pro
blur_pix             ghostee              resize               t1000
broken_scroll        light_snow           reverse              transcraibe
chain_builder        looper_pro           scrolling_pro        twociz
chain_builder_pro    lsd_feedback         septic               wbflare
convert              mirror_delay         silence_xtraction    xrgb
digital_boss         nostalgic_stutter    slight_smear         zapruder
double_cup           num_edits            smudge
download_yt          overexposed_stutter  soapblind
extract_frames       overlay_img_pro      speed
  ```

Good to go!

## Examples

### Running a program that does not have additional arguments

#### Check if the program needs additional arguments

```bash
       _     _            _
__   _(_) __| | ___  ___ | |__   ___  __ _ _   ___  __
\ \ / / |/ _` |/ _ \/ _ \| '_ \ / _ \/ _` | | | \ \/ /
 \ V /| | (_| |  __/ (_) | |_) |  __/ (_| | |_| |>  <
  \_/ |_|\__,_|\___|\___/|_.__/ \___|\__,_|\__,_/_/\_\


Your friendly multilateral video toolkit built for artists by artists.
https://schwwaaa.com
--------------------------------------------------
Selected program mode: bad_predator
✅ This program mode does not require additional arguments
usage: python3 -m videobeaux.cli --program PROGRAM [global options] [program options]

📺 Your friendly multilateral video toolkit built for artists by artists.
 It's your best friend!
https://schwwaaa.com

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
#### Run the program

``` bash
videobeaux --program PROGRAM --input INPUT_FILE --output OUTPUT_FILE
```
... translates to ...

``` bash
videobeaux --program bad_predator --input example.mp4 --output example_bp.mp4
```
#### Output of the program
``` bash
       _     _            _
__   _(_) __| | ___  ___ | |__   ___  __ _ _   ___  __
\ \ / / |/ _` |/ _ \/ _ \| '_ \ / _ \/ _` | | | \ \/ /
 \ V /| | (_| |  __/ (_) | |_) |  __/ (_| | |_| |>  <
  \_/ |_|\__,_|\___|\___/|_.__/ \___|\__,_|\__,_/_/\_\


Your friendly multilateral video toolkit built for artists by artists.
https://schwwaaa.com
--------------------------------------------------
Selected program mode: bad_predator
✅ This program mode does not require additional arguments
Input duration: 10.01 seconds
🔨 Processing example.mp4: 100%|██████████████████████████████████████████████████████ | 10.01/10.01s [00:04<00:00]

📺 Process Complete: example_bp.mp4
```

https://github.com/user-attachments/assets/fe45aa80-9878-4d15-bc64-87dd25071855

### Running a program that does have additional arguments

#### Check if the program needs additional arguments
``` bash
       _     _            _
__   _(_) __| | ___  ___ | |__   ___  __ _ _   ___  __
\ \ / / |/ _` |/ _ \/ _ \| '_ \ / _ \/ _` | | | \ \/ /
 \ V /| | (_| |  __/ (_) | |_) |  __/ (_| | |_| |>  <
  \_/ |_|\__,_|\___|\___/|_.__/ \___|\__,_|\__,_/_/\_\


Your friendly multilateral video toolkit built for artists by artists.
https://schwwaaa.com
--------------------------------------------------
Selected program mode: stutter_pro
usage: python3 -m videobeaux.cli --program PROGRAM [global options] [program options]

📺 Your friendly multilateral video toolkit built for artists by artists.
 It's your best friend!
https://schwwaaa.com

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

#### Run the program
``` bash
videobeaux --program PROGRAM --input INPUT_FILE --output OUTPUT_FILE --args ARGUMENTS
```
... translates to ...

``` bash
videobeaux --program stutter_pro -i example.mp4 -o stutter_example.mp4 --stutter 2
```
#### Output of the program
```bash      
       _     _            _
__   _(_) __| | ___  ___ | |__   ___  __ _ _   ___  __
\ \ / / |/ _` |/ _ \/ _ \| '_ \ / _ \/ _` | | | \ \/ /
 \ V /| | (_| |  __/ (_) | |_) |  __/ (_| | |_| |>  <
  \_/ |_|\__,_|\___|\___/|_.__/ \___|\__,_|\__,_/_/\_\


Your friendly multilateral video toolkit built for artists by artists.
https://schwwaaa.com
--------------------------------------------------
Selected program mode: stutter_pro
Input duration: 10.01 seconds
🔨 Processing example.mp4: 100%|██████████████████████████████████████████████████████████ | 10.01/10.01s [00:00<00:00]

📺 Process Complete: stutter_example.mp4
```

https://github.com/user-attachments/assets/fec22179-8e40-49e5-b591-c9d5fb07e31b

### Running a program to chain process a video
#### Find out more information about the program

``` bash
       _     _            _
__   _(_) __| | ___  ___ | |__   ___  __ _ _   ___  __
\ \ / / |/ _` |/ _ \/ _ \| '_ \ / _ \/ _` | | | \ \/ /
 \ V /| | (_| |  __/ (_) | |_) |  __/ (_| | |_| |>  <
  \_/ |_|\__,_|\___|\___/|_.__/ \___|\__,_|\__,_/_/\_\


Your friendly multilateral video toolkit built for artists by artists.
https://schwwaaa.com
--------------------------------------------------
Selected program mode: chain_builder
usage: python3 -m videobeaux.cli --program PROGRAM [global options] [program options]

📺 Your friendly multilateral video toolkit built for artists by artists.
 It's your best friend!
https://schwwaaa.com

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
#### Run the program
``` bash
videobeaux --program PROGRAM --input INPUT_FILE --output OUTPUT_FILE --chain CHAIN
```
... translates to ...

```bash
videobeaux --program chain_builder --input example.mp4 --output chainedoutput.mp4 --chain rb_blur,soapblind,lsd_feedback --force
```

#### Output of the program
``` bash
       _     _            _
__   _(_) __| | ___  ___ | |__   ___  __ _ _   ___  __
\ \ / / |/ _` |/ _ \/ _ \| '_ \ / _ \/ _` | | | \ \/ /
 \ V /| | (_| |  __/ (_) | |_) |  __/ (_| | |_| |>  <
  \_/ |_|\__,_|\___|\___/|_.__/ \___|\__,_|\__,_/_/\_\


Your friendly multilateral video toolkit built for artists by artists.
https://schwwaaa.com
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

https://github.com/user-attachments/assets/ac321c77-4757-4846-b838-6847472e7e09

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
| digital_boss | Apply busted gameboy style digital boss effect | - |
| double_cup | Apply the effect of purple drank | - |
| frame_delay_pro1 | Apply frame delay effect with parameter input | frame_quantity, frame_weights |
| frame_delay_pro2 | Apply frame delay effect with parameter input | decay, plane |
| ghostee | Apply a slight ghost effect | - |
| looper_pro | Apply video looper effect base on frame size & start frame | - |
| lsd_feedback | Apply LSD-like frame delay effect | - |
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
| convert | Simple video file convert | - |
| convert_dims | Video file dimensions converter based on industry standards  | - |
| download_yt | Video ripper | - |
| extract_frames | Extract individuals frames from a video file as PNGs | - |
| extract_sound | Extract audio from video file | - |
| silence_extraction | Extracting the silence out of a video file | min_d, max_d, adjuster |
| transraibe | AI-based transcription tool | stt_model |

## Video Exaxmples

bad_animation

https://github.com/user-attachments/assets/1fa8de04-98ef-49f7-9415-616e07210f0e

bad_contrast

https://github.com/schwwaaa/videobeaux/assets/7625379/9ba59b08-79a8-4a09-8b18-c0fe90a6c5e2

bad_predator

https://github.com/schwwaaa/videobeaux/assets/7625379/0968ad50-cc97-4336-938f-01b47d86a7bd

ball_point_pen

https://github.com/user-attachments/assets/10e703a5-5036-4c3e-83f6-be04476ad089

blur_pix

https://github.com/schwwaaa/videobeaux/assets/7625379/65403294-3e34-4ff8-816a-5de7c80c811d

broken_scroll

https://github.com/schwwaaa/videobeaux/assets/7625379/4cdebccc-8519-45c6-aded-089db73d20d2

digital_boss

https://github.com/user-attachments/assets/23958066-f384-4801-9d91-5b2df6081a31

double_cup

https://github.com/schwwaaa/videobeaux/assets/7625379/83d30a18-40d1-42e4-aff3-dbd50d67a7d1

fever

https://github.com/schwwaaa/videobeaux/assets/7625379/b476426f-0ca6-4667-be40-97df932b9909

frame_delay_pro1-1

https://github.com/schwwaaa/videobeaux/assets/7625379/871ccdb9-ae2b-46e1-8b0f-0514eb92e1aa

frame_delay_pro1-2

https://github.com/schwwaaa/videobeaux/assets/7625379/0a727474-25cf-42ab-a717-583e12b4a04d

frame_delay_pro1-3

https://github.com/schwwaaa/videobeaux/assets/7625379/5ab60f24-b4e2-4e0e-abc0-cfab62e09cda

frame_delay_pro2-1

https://github.com/schwwaaa/videobeaux/assets/7625379/a88284bc-ca7e-4355-8f95-377434c61d13

frame_delay_pro2-2

https://github.com/schwwaaa/videobeaux/assets/7625379/acf571e7-7162-413f-80f8-769815093267

frame_delay_pro2-3

https://github.com/schwwaaa/videobeaux/assets/7625379/f717d419-687b-4cc3-ac07-64f45c763531

ghostee

https://github.com/user-attachments/assets/87c8b569-5165-485d-ae09-7a8bbbe74051

lsd_feedback

https://github.com/schwwaaa/videobeaux/assets/7625379/9653929c-30ad-4c72-81c8-e3777c590783

looper_pro

https://github.com/schwwaaa/videobeaux/assets/7625379/01090d49-8626-4fc0-b55c-807d100a78fa

mirror_delay

https://github.com/schwwaaa/videobeaux/assets/7625379/a3dea5c6-03a6-4f65-951d-211f50457b63

nostalgic

https://github.com/schwwaaa/videobeaux/assets/7625379/3cef37d9-093f-4bd9-850c-4b163e8a3e01

overexposed_stutter

https://github.com/schwwaaa/videobeaux/assets/7625379/f7250a1e-3cf5-4826-977a-a5a18b231ddb

overlay_img_pro

https://github.com/schwwaaa/videobeaux/assets/7625379/3932d910-b898-4ed7-ba3a-288a708c0d83

pickle_juice

https://github.com/schwwaaa/videobeaux/assets/7625379/387bfff5-fbdd-423d-b482-8ab4d5ce744f

recalled_sensor

OMITTED DUE TO SIZE

repainting

https://github.com/user-attachments/assets/1770144d-4448-4719-8ef3-e44b720ec857

reverse

https://github.com/schwwaaa/videobeaux/assets/7625379/74367227-6fee-455f-af36-804a1e6d6cb6

scrolling_pro-1

https://github.com/schwwaaa/videobeaux/assets/7625379/e84cfb49-f72d-449e-833a-0271903704f4

scrolling_pro-2

https://github.com/schwwaaa/videobeaux/assets/7625379/19c6eef1-2bc0-4d84-b531-55f9ca07a912

scrolling_pro-3

https://github.com/schwwaaa/videobeaux/assets/7625379/4a4272de-e074-4e37-8c2d-a282f2d8be57

septic

https://github.com/user-attachments/assets/25f65267-60fa-421a-aaf3-02918844a488

slight_smear

https://github.com/schwwaaa/videobeaux/assets/7625379/a7bca4c5-46b5-4b51-a827-6b8137d0117d

smudge

https://github.com/user-attachments/assets/9bb80e0b-bf16-49e7-b4e1-6c0c79b59c32

soapblind

https://github.com/user-attachments/assets/28070fe5-52cd-42c9-93b7-a417c83add2d

speed

https://github.com/schwwaaa/videobeaux/assets/7625379/c27efdb1-ae81-4d8d-a153-de6294b7fedf

splitting

https://github.com/user-attachments/assets/b6c13707-aaa8-416e-9f80-5ca6a386cd0f

stack_2x

https://github.com/schwwaaa/videobeaux/assets/7625379/6f244aba-e741-46c9-9863-7fc43527a8d6

steel_wash

https://github.com/schwwaaa/videobeaux/assets/7625379/eea99448-9352-48f1-a1ec-b2cac6ad056d

stutter_pro-1

https://github.com/schwwaaa/videobeaux/assets/7625379/03e234fb-d0fe-4d72-a11c-dff1bc59fa83

stutter_pro-2

https://github.com/schwwaaa/videobeaux/assets/7625379/e6d8c14a-9f20-4365-bb1f-5f473289a855

stutter_pro-3

https://github.com/schwwaaa/videobeaux/assets/7625379/864835ba-dc9d-4392-aa77-2cc062e2b700

t1000

https://github.com/user-attachments/assets/5de6db36-f8d4-426e-9262-b9dbeb2095ae

twociz

OMITTED DUE TO SIZE

wbflare

https://github.com/user-attachments/assets/e2a5f065-163e-4bb9-8fd3-1edbfbdbab2a

zapruder

https://github.com/user-attachments/assets/cad79483-b21f-43b8-a1cd-91ed8406574a

xrgb

https://github.com/user-attachments/assets/c9644cd5-a584-4f0d-ada3-13046e6938a5
