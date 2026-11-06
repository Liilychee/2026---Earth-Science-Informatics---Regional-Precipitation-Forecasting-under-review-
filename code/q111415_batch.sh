#!/bin/bash
# ============================================================
# One GPU batch for items 11, 14 and 15 (independent experiments, main 70/15/15 split).
#   usage: bash q111415_batch.sh <DRY> [PARALLEL]
#     DRY      : training dry definition for tobit / bergamma chosen from the seed-42 check (e.g. 0)
#     PARALLEL : simultaneous jobs (default 8)
# Each line of the job list is one model x setting x seed; finished runs are skipped, so the batch
# can be restarted safely. Long jobs are listed first.
# Logs: results/batch_logs/<job>.log ; summary of failures at the end.
# ============================================================
set -u
DRY=${1:?give the dry definition for item 11, e.g. 0}
PAR=${2:-8}
ROOT=/root/autodl-tmp
CODE=$ROOT/code
LOG=$ROOT/results/batch_logs
mkdir -p $LOG
JOBS=$LOG/jobs.txt
: > $JOBS
SEEDS="42 123 7 2024 99"
DELTAS="0.5 1 2"

# 14: window 6 (30 h, main study) and window 3 (12 h); long models first
for m in transformer bulstm_attn bulstm prob_bilstm_attn bilstm_attn; do
  for w in 6 3; do
    for s in $SEEDS; do echo "q14 python $CODE/q14q15_train.py --models $m --window $w --seeds $s" >> $JOBS; done
  done
done
# 15: Huber, deterministic deep models, window 6
for m in transformer bilstm_attn; do
  for dl in $DELTAS; do
    for s in $SEEDS; do echo "q15 python $CODE/q14q15_train.py --models $m --window 6 --loss huber --delta $dl --seeds $s" >> $JOBS; done
  done
done
# 11: three distributions, five seeds (seed-42 runs of the check are reused automatically)
for s in $SEEDS; do
  echo "q11 python $CODE/q11_train.py --dists gaussian --seeds $s" >> $JOBS
  echo "q11 python $CODE/q11_train.py --dists tobit --dry $DRY --seeds $s" >> $JOBS
  echo "q11 python $CODE/q11_train.py --dists bergamma --dry $DRY --seeds $s" >> $JOBS
done
# 14: XGBoost (CPU, seconds)
for w in 6 3; do
  for s in $SEEDS; do echo "q14 python $CODE/q14q15_train.py --models xgboost --window $w --seeds $s" >> $JOBS; done
done

echo "jobs: $(wc -l < $JOBS) | parallel: $PAR | dry for item 11: $DRY | start $(date)"
run_job() {
  line="$1"; item=${line%% *}; cmd=${line#* }
  name=$(echo "$cmd" | sed -E 's#.*/##; s/\.py//; s/--//g; s/ +/_/g')
  cd /root/autodl-tmp/code && $cmd > /root/autodl-tmp/results/batch_logs/${item}_${name}.log 2>&1
  echo "[$(date +%H:%M:%S)] exit $? ${item} ${name}"
}
export -f run_job
tr '\n' '\0' < $JOBS | xargs -0 -P $PAR -I{} bash -c 'run_job "$@"' _ {} | tee $LOG/progress.txt
echo "===== BATCH FINISHED $(date) ====="
echo "failed jobs:"; grep -v "exit 0" $LOG/progress.txt || echo "none"
grep -lE "Traceback|Error:|Killed" $LOG/*.log || echo "no tracebacks"
