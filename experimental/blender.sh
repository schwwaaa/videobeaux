#!/bin/bash

mkdir -p blended_outputs

python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_addition.mp4 --blend_mode addition --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_addition128.mp4 --blend_mode addition128 --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_and.mp4 --blend_mode and --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_average.mp4 --blend_mode average --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_burn.mp4 --blend_mode burn --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_darken.mp4 --blend_mode darken --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_difference.mp4 --blend_mode difference --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_difference128.mp4 --blend_mode difference128 --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_divide.mp4 --blend_mode divide --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_exclusion.mp4 --blend_mode exclusion --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_extremity.mp4 --blend_mode extremity --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_freeze.mp4 --blend_mode freeze --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_glow.mp4 --blend_mode glow --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_grainextract.mp4 --blend_mode grainextract --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_grainmerge.mp4 --blend_mode grainmerge --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_hardlight.mp4 --blend_mode hardlight --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_hardmix.mp4 --blend_mode hardmix --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_heat.mp4 --blend_mode heat --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_lighten.mp4 --blend_mode lighten --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_linearlight.mp4 --blend_mode linearlight --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_multiply.mp4 --blend_mode multiply --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_multiply128.mp4 --blend_mode multiply128 --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_negation.mp4 --blend_mode negation --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_normal.mp4 --blend_mode normal --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_or.mp4 --blend_mode or --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_overlay.mp4 --blend_mode overlay --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_phoenix.mp4 --blend_mode phoenix --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_pinlight.mp4 --blend_mode pinlight --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_reflect.mp4 --blend_mode reflect --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_screen.mp4 --blend_mode screen --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_softlight.mp4 --blend_mode softlight --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_subtract.mp4 --blend_mode subtract --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_vividlight.mp4 --blend_mode vividlight --audio_mode mix
sleep 2
python3 blender.py --input1 video1.mp4 --input2 video2.mp4 --output blended_outputs/output_xor.mp4 --blend_mode xor --audio_mode mix
sleep 2