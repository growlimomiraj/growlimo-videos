#!/bin/bash
# usage: finish.sh OUT.mp4   (run inside the work dir after vo/zoom/build_video/timeline/audio)
set -e
T=$(python3 -c "import json;print(json.load(open('timings.json'))['total'])")
rm -rf ov && python3 render_ov.py $T 30 6
ffmpeg -v error -y -i base.mp4 -framerate 30 -i ov/%05d.png -i mix.wav -filter_complex "[0:v][1:v]overlay=format=auto[v]" -map "[v]" -map 2:a \
  -c:v libx264 -preset slow -crf 20 -maxrate 12M -bufsize 24M -pix_fmt yuv420p -af loudnorm=I=-14:TP=-1.0:LRA=14 -ar 48000 -c:a aac -b:a 192k -movflags +faststart -shortest "$1"
ls -la "$1"
