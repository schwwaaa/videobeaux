#!/bin/bash

ffmpeg -f lavfi -i color=black:s=640x360:d=5 \
-vf "drawtext=fontfile='/Users/tgm/Desktop/videotitles/dir/Aktifo-B-Black':text='Test':fontcolor=white:fontsize=32:x=10:y=10" \
-c:v libx264 -t 5 out.mp4