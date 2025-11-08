#!/bin/bash
# run_examples.sh
# Batch conversions using convertersink.py, pausing 2s between each job.

set -e

# General H.264 MP4 (web-friendly)
python3 convertersink.py -i bbb.mov -o out.mp4 --profile mp4_h264 -F
sleep 2

# HEVC in MP4 (Apple-friendly tag)
# python3 convertersink.py -i bbb.mkv -o out_hevc.mp4 --profile mp4_hevc -F
sleep 2

# AV1 in MP4 (tiny files, slow encode)
python3 convertersink.py -i bbb.mov -o out_av1.mp4 --profile mp4_av1 -F
sleep 2

# WebM VP9 + Opus
python3 convertersink.py -i bbb.mp4 -o out.webm --profile webm_vp9 -F
sleep 2

# WebM AV1 + Opus
python3 convertersink.py -i bbb.mp4 -o out_av1.webm --profile webm_av1 -F
sleep 2

# ProRes 422 in MOV (mezzanine)
python3 convertersink.py -i bbb.mp4 -o out_prores.mov --profile prores_422 -F
sleep 2

# ProRes 4444 in MOV (alpha support)
python3 convertersink.py -i in_prores4444_src.mov -o out_4444.mov --profile prores_4444 -F
sleep 2

# DNxHR HQ in MOV
python3 convertersink.py -i bbb.mp4 -o out_dnxhr.mov --profile dnxhr_hq -F
sleep 2

# MXF XDCAM HD 50 (1080i59.94 broadcast)
python3 convertersink.py -i bbb.mov -o out_xdcamhd50.mxf --profile mxf_xdcamhd50_1080i59 -F
sleep 2

# Lossless archival (FFV1 in MKV)
python3 convertersink.py -i bbb.mov -o archive.mkv --profile lossless_ffv1 -F
sleep 2

# High-quality GIF
python3 convertersink.py -i bbb.mp4 -o out.gif --profile gif -F
sleep 2

# Image sequence (PNG)
python3 convertersink.py -i bbb.mp4 -o frames_%05d.png --format image2 --profile png_seq -F
sleep 2

# Image sequence (JPEG, quality ~2)
python3 convertersink.py -i bbb.mp4 -o frames_%05d.jpg --format image2 --profile jpg_seq -F
sleep 2

# Audio-only (MP3 320k)
python3 convertersink.py -i bbb.mov -o track.mp3 --profile mp3_320 -F
sleep 2

# Audio-only (AAC 192k in M4A)
python3 convertersink.py -i bbb.mov -o track.m4a --profile aac_192 -F
sleep 2

# Quick stream-copy (no re-encode) when compatible
python3 convertersink.py -i bbb.mp4 -o just_rewrap.mkv --copy -F
sleep 2

# Custom overrides (manual control)
python3 convertersink.py -i bbb.mov -o out_custom.mp4 --vcodec libx264 --crf 20 --preset medium \
  --pix-fmt yuv420p --acodec aac --abitrate 160k --ac 2 --vf "scale=1280:-2" -F
sleep 2

# Pass raw ffmpeg flags after `--`
python3 convertersink.py -i bbb.mov -o out_muxqueue.mp4 --profile mp4_h264 -- --max_muxing_queue_size 9999
sleep 2

# --- New fast AVI presets ---
# Fast AVI via MJPEG (very fast encode; large output)
python3 convertersink.py -i bbb.mp4 -o fast_review.avi --profile avi_mjpeg_fast -F
sleep 2

# Faster legacy AVI via MPEG-4 ASP
python3 convertersink.py -i bbb.mp4 -o legacy_fast.avi --profile avi_mpeg4_fast -F
sleep 2
