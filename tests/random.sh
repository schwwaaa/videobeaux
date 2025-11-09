#!/bin/bash

# Define the array
ARRAY=(
    # "bad_animation"
    "bad_contrast"
    "ball_point_pen"
    "blur_pix"
    "bad_predator"
    # "convert"
    "digital_boss"
    "double_cup"
    # "download_yt"
    # "extract_frames"
    # "extract_sound"
    # "frame_delay_pro1"
    "frame_delay_pro2"
    "ghostee"
    "looper_pro"
    "lsd_feedback"
    "mirror_delay"
    "nostalgic_stutter"
    "overexposed_stutter"
    # "overlay_img_pro"
    "pickle_juice"
    "recalled_sensor"
    "repainting"
    # "resize" 
    "reverse"
    # "scrolling_pro"
    # "scrolling"
    "septic"
    # "silence_extraction"
    # "slight_smear"
    "smudge"
    "soapblind"
    # "speed"
    # "stack_2x"
    "steel_wash"
    # "stutter_pro"
    "t1000"
    # "transraibe"
    "twociz"
    "wbflare"
    "zapruder"
    "xrgb"
)

# Generate random number between 2 and 10
num_items=$((RANDOM % 3 + 2))
# num_items=$((RANDOM % 9 + 2))

# Select random items and concatenate with commas
selected_items=$(shuf -n $num_items -e "${ARRAY[@]}" | tr '\n' ',' | sed 's/,$//')

# Construct the videobeaux command
command="videobeaux --program chain_builder --input example.mp4 --output chainedoutput.mp4 --chain 
$selected_items --force"

# Output the command
echo $command

# Run the command
$command