#!/bin/bash
ffmpeg -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=wipeleft:duration=1:offset=5,format=yuv420p" -c:v libx264 -y horizontal_wipe.mp4
sleep 2
ffmpeg -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=wipeup:duration=1:offset=5,format=yuv420p" -c:v libx264 -y vertical_wipe.mp4
sleep 2
ffmpeg -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=diagbr:duration=1:offset=5,format=yuv420p" -c:v libx264 -y diagonal_topleft_bottomright_wipe.mp4
sleep 2
#!/bin/bash
ffmpeg -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=diagbl:duration=1:offset=5,format=yuv420p" -c:v libx264 -y diagonal_topright_bottomleft_wipe.mp4
sleep 2
#!/bin/bash
ffmpeg -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=circleopen:duration=1:offset=5,format=yuv420p" -c:v libx264 -y circular_wipe.mp4
sleep 2
#!/bin/bash
ffmpeg -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=rectcrop:duration=1:offset=5,format=yuv420p" -c:v libx264 -y square_wipe.mp4
sleep 2
#!/bin/bash
# Note: FFmpeg's xfade does not have a direct diamond wipe. Approximating with custom mask.
# Create a diamond-shaped mask image (white diamond on black background) named diamond_mask.png
ffmpeg -i 0.mp4 -i 1.mp4 -i diamond_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y diamond_wipe.mp4
sleep 2
#!/bin/bash
# Note: FFmpeg's xfade does not support star wipe. Requires custom star-shaped mask.
# Create a star-shaped mask image (white star on black background) named star_mask.png
ffmpeg -i 0.mp4 -i 1.mp4 -i star_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y star_wipe.mp4
sleep 2
#!/bin/bash
# Note: FFmpeg's xfade does not support cross wipe. Approximating with custom mask.
# Create a cross-shaped mask image (white cross on black background) named cross_mask.png
ffmpeg -i 0.mp4 -i 1.mp4 -i cross_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y cross_wipe.mp4
sleep 2
#!/bin/bash
# Note: FFmpeg's xfade does not support checkerboard wipe. Approximating with pixelize filter.
ffmpeg -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=pixelize:duration=1:offset=5,format=yuv420p" -c:v libx264 -y checkerboard_wipe.mp4