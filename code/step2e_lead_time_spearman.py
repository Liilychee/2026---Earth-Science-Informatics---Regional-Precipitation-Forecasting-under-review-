# ============================================================
# Step 2E — Lead-time-dependent train-only Spearman (reviewer R2-3)
#
# Contemporaneous correlation (feature at t vs precip at t) does not
# reflect predictive value at a 6 h lead. Here we correlate feature at
# time t with precipitation at t+k (k = 0, 1, 2 steps = 0, 6, 12 h),
# TRAIN SET ONLY. k=1 is the actual forecast task.
#
# Run in the same kernel after step2d:   %run -i code/step2e_lead_time_spearman.py
# Needs (from step2d): train_full, ALL_CANDIDATES
# Output: results/features/train_only_spearman_leadtime.csv
# ============================================================
import pandas as pd
from scipy.stats import spearmanr

assert 'train_full' in dir() and 'ALL_CANDIDATES' in dir(), "Run step2d first."

# consecutive 6-hourly rows => shift(-k) is the value k*6 h later
dt = train_full['valid_time'].diff().dropna().unique()
assert len(dt) == 1 and dt[0] == pd.Timedelta(hours=6), f"Train series not contiguous 6-hourly: {dt}"

rows = []
for feat in ALL_CANDIDATES + ['tp_mm']:
    rec = {'feature': feat}
    for k in (0, 1, 2):
        x = train_full[feat].iloc[:len(train_full) - k] if k else train_full[feat]
        y = train_full['tp_mm'].shift(-k).dropna() if k else train_full['tp_mm']
        rec[f'rho_lead_{6*k}h'] = spearmanr(x.values, y.values).correlation
    rows.append(rec)

out = pd.DataFrame(rows).set_index('feature')
out['abs_rho_6h'] = out['rho_lead_6h'].abs()
out = out.sort_values('abs_rho_6h', ascending=False)
print("===== TRAIN-ONLY SPEARMAN: feature(t) vs tp_mm(t+k) =====")
print(out.round(3).to_string())

path = "/root/autodl-tmp/results/features/train_only_spearman_leadtime.csv"
out.to_csv(path)
print("\nSaved:", path)
print("\nTop-7 at 6h lead:", [f for f in out.index if f != 'tp_mm'][:7])
print("Current FINAL_FEATURES:", FINAL_FEATURES if 'FINAL_FEATURES' in dir() else "(not in memory)")
