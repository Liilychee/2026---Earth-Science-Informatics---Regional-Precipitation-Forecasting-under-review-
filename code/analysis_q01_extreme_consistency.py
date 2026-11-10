# ============================================================
# analysis_q01_extreme_consistency.py  --  issue 01 (R3 3.2(e), R2 M1), evidence 01-E5 / 01-E6
# Pure computation on the regional-mean file. No training, no GPU, seconds.
#
# What it checks (and what it does NOT prove)
#   01-E6  If mxtpr / mntpr are the max / min precipitation RATE inside the same hour that tp
#          accumulates over, then for every sample   mntpr*3600 <= tp_mm <= mxtpr*3600
#          (rates in kg m-2 s-1 = mm/s ; tp in m -> *1000 = mm over the hour).
#          The check supports the "same hour" reading. It does NOT independently prove the
#          window length (a longer window would also satisfy it), and near-zero samples carry
#          floating-point noise. Reported strictly and with a small tolerance.
#   01-E5  tp magnitude by hour of day (00/06/12/18): if tp were a multi-hour forecast
#          accumulation, 06/18 UTC values would differ systematically from 00/12.
#
# Run from the folder containing data/ :
#     mkdir -p results/metrics
#     python3 code/analysis_q01_extreme_consistency.py 2>&1 | tee results/metrics/q01_extreme_consistency_output.txt
# Outputs (results/metrics/): q01_extreme_consistency_summary.csv, q01_tp_by_hour.csv,
#                             q01_extreme_violations.csv
# Optional first argument: path of the regional csv.
# ============================================================
import os
import sys
import numpy as np
import pandas as pd

CANDS = (sys.argv[1:2] or []) + [
    "data/dublin_regional_reduced.csv", "../data/dublin_regional_reduced.csv",
    "data/dublin_regional_2004_2021.csv", "../data/dublin_regional_2004_2021.csv"]
path = next(p for p in CANDS if os.path.exists(p))
d = pd.read_csv(path, parse_dates=["valid_time"]).sort_values("valid_time").reset_index(drop=True)
print("Source:", path, d.shape)
d["tp_mm"] = d["tp"] * 1000.0 if "tp" in d.columns else d["tp_mm"]
d["mx_mmh"] = d["mxtpr"] * 3600.0       # kg m-2 s-1 == mm/s  ->  mm/h
d["mn_mmh"] = d["mntpr"] * 3600.0
print("Units assumed: tp [m] -> mm; mxtpr, mntpr [kg m-2 s-1] -> mm/h (x3600).")
print(f"Medians: tp_mm {d.tp_mm.median():.4f}, mx_mmh {d.mx_mmh.median():.4f}, mn_mmh {d.mn_mmh.median():.4f}")

THR = 0.1
rows = []
for label, g in (("all samples", d), (f"tp >= {THR} mm", d[d.tp_mm >= THR])):
    for tol_name, tol in (("strict", 0.0), ("tol 1e-3 mm", 1e-3)):
        ok_mx = (g.mx_mmh >= g.tp_mm - tol)
        ok_mn = (g.mn_mmh <= g.tp_mm + tol)
        rows.append({"Subset": label, "Tolerance": tol_name, "N": len(g),
                     "mxtpr*3600 >= tp (%)": 100 * ok_mx.mean(),
                     "mntpr*3600 <= tp (%)": 100 * ok_mn.mean(),
                     "both (%)": 100 * (ok_mx & ok_mn).mean()})
res = pd.DataFrame(rows)
print("\n===== 01-E6: max/min rate vs hourly total (same-hour consistency) =====")
print(res.round(2).to_string(index=False))

w = d[d.tp_mm >= THR]
ratio_mx, ratio_mn = w.mx_mmh / w.tp_mm, w.mn_mmh / w.tp_mm
print(f"\nSamples with tp >= {THR} mm: {len(w)}  (earlier record: 5,363; inequalities 99.7% / 99.4%)")
print(f"Median ratio mxtpr*3600/tp = {ratio_mx.median():.2f}, mntpr*3600/tp = {ratio_mn.median():.2f} "
      f"(earlier record: about 1.6 / 0.6)")
print("Ratio quantiles (5/25/50/75/95%): mx", ratio_mx.quantile([.05, .25, .5, .75, .95]).round(2).tolist(),
      "| mn", ratio_mn.quantile([.05, .25, .5, .75, .95]).round(2).tolist())

viol = w[(w.mx_mmh < w.tp_mm) | (w.mn_mmh > w.tp_mm)].copy()
viol["excess_mx_mm"] = (viol.tp_mm - viol.mx_mmh).clip(lower=0)
viol["excess_mn_mm"] = (viol.mn_mmh - viol.tp_mm).clip(lower=0)
print(f"\nViolations among tp >= {THR}: {len(viol)}; largest excess (mm): "
      f"mx {viol.excess_mx_mm.max() if len(viol) else 0:.4f}, mn {viol.excess_mn_mm.max() if len(viol) else 0:.4f}")

d["hour"] = d.valid_time.dt.hour
bh = (d.groupby("hour").tp_mm.agg(N="size", mean="mean", median="median",
                                  p95=lambda s: s.quantile(.95), max="max")
      .join(d.groupby("hour").apply(lambda g: (g.tp_mm >= THR).mean(), include_groups=False).rename("frac_ge_0.1mm")))
print("\n===== 01-E5: tp (mm) by hour of day of the stored timestamp =====")
print(bh.round(4).to_string())

os.makedirs("results/metrics", exist_ok=True)
res.to_csv("results/metrics/q01_extreme_consistency_summary.csv", index=False)
bh.round(5).to_csv("results/metrics/q01_tp_by_hour.csv")
viol[["valid_time", "tp_mm", "mx_mmh", "mn_mmh", "excess_mx_mm", "excess_mn_mm"]].to_csv(
    "results/metrics/q01_extreme_violations.csv", index=False)
print("\nSaved results/metrics/q01_*.csv")
