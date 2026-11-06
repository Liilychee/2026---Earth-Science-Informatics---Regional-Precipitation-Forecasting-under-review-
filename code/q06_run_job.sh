#!/bin/sh
# one job = one fold x one model x five seeds; called by xargs -P (see q06 launch command)
cd /root/autodl-tmp
export TF_FORCE_GPU_ALLOW_GROWTH=true
python3 code/q06_train.py --fold "$1" --models "$2" > "results/metrics/q06_$1_$2_output.txt" 2>&1
