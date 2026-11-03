# ============================================================
# analysis_q02_lsp_share.py  — issue 02 (R2-2, R4 M2, R4 M3)
# Pure computation on the regional-mean file. No training, no GPU.
#
# Questions answered
#   (a) What share of total precipitation is large-scale (lsp) vs
#       convective (cp = tp - lsp)?  overall, per season, per intensity
#   (b) R4 M2: "if lsp = 0.7 mm the model knows tp cannot be lower".
#       True only for the SAME hour. Our inputs are at time t and the
#       target is the hour ending t+6h, so lsp(t) is NOT a lower bound.
#       -> fraction of cases where tp(t+6h) < lsp(t)
#   (c) How informative is lsp(t) for tp(t+6h)? (Spearman)
#
# Run from the folder containing data/ :
#     python code/analysis_q02_lsp_share.py
# Output: results/metrics/q02_lsp_share.csv  (+ console summary)
# ============================================================
import os
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

CANDS = ["data/dublin_regional_reduced.csv", "../data/dublin_regional_reduced.csv",
         "data/dublin_regional_2004_2021.csv", "../data/dublin_regional_2004_2021.csv"]
path = next(p for p in CANDS if os.path.exists(p))
d = pd.read_csv(path, parse_dates=["valid_time"]).sort_values("valid_time").reset_index(drop=True)
print("Source:", path, d.shape)

# tp / lsp in mm (ERA5 metres * 1000); old file already has tp_mm
d["tp_mm"] = d["tp"] * 1000.0 if "tp" in d.columns else d["tp_mm"]
d["lsp_mm"] = d["lsp"] * 1000.0
d["cp_mm"] = d["tp_mm"] - d["lsp_mm"]          # convective precipitation = tp - lsp
print(f"cp = tp - lsp: min {d.cp_mm.min():.6f} mm (tiny negatives = float noise), "
      f"fraction < -1e-4 mm: {(d.cp_mm < -1e-4).mean():.4f}")

season = {12: "DJF", 1: "DJF", 2: "DJF", 3: "MAM", 4: "MAM", 5: "MAM",
          6: "JJA", 7: "JJA", 8: "JJA", 9: "SON", 10: "SON", 11: "SON"}
d["season"] = d.valid_time.dt.month.map(season)

rows = []
def add(label, g):
    wet = g[g.tp_mm >= 0.1]
    rows.append({
        "Group": label, "N": len(g), "N_wet_ge_0.1mm": len(wet),
        "Share_lsp_of_total_tp_%": 100 * g.lsp_mm.sum() / g.tp_mm.sum(),
        "Share_cp_of_total_tp_%": 100 * g.cp_mm.clip(lower=0).sum() / g.tp_mm.sum(),
        "Median_lsp_over_tp_wet_%": 100 * float((wet.lsp_mm / wet.tp_mm).median()) if len(wet) else np.nan,
        "Frac_wet_with_cp_gt_10pct_of_tp": float((wet.cp_mm > 0.1 * wet.tp_mm).mean()) if len(wet) else np.nan,
    })
add("All", d)
for s in ["DJF", "MAM", "JJA", "SON"]:
    add(s, d[d.season == s])
for lo, hi, lab in [(0.1, 0.5, "0.1-0.5 mm"), (0.5, 1.0, "0.5-1.0 mm"), (1.0, 99, ">=1.0 mm")]:
    add(f"tp {lab}", d[(d.tp_mm >= lo) & (d.tp_mm < hi)])
res = pd.DataFrame(rows)
print("\n=== SHARE OF LARGE-SCALE (lsp) vs CONVECTIVE (cp = tp - lsp) PRECIPITATION ===")
print(res.round(2).to_string(index=False))

# (b) lsp(t) as lower bound of tp(t+6h)?  consecutive 6-hourly rows
assert (d.valid_time.diff().dropna() == pd.Timedelta(hours=6)).all(), "series not contiguous"
now_lsp = d.lsp_mm.iloc[:-1].values
next_tp = d.tp_mm.iloc[1:].values
m = now_lsp >= 0.1
print("\n=== IS lsp(t) A LOWER BOUND FOR tp(t+6h)?  (R4 M2) ===")
print(f"Same hour: tp >= lsp in {(d.tp_mm >= d.lsp_mm - 1e-4).mean()*100:.2f}% of samples (by construction, tp = lsp + cp).")
print(f"Next sample: among {int(m.sum())} cases with lsp(t) >= 0.1 mm, "
      f"tp(t+6h) < lsp(t) in {np.mean(next_tp[m] < now_lsp[m])*100:.1f}%; "
      f"tp(t+6h) < 0.1 mm in {np.mean(next_tp[m] < 0.1)*100:.1f}%")
print(f"Spearman lsp(t) vs tp(t+6h): {spearmanr(now_lsp, next_tp).correlation:.3f}   "
      f"(same-hour lsp vs tp: {spearmanr(d.lsp_mm, d.tp_mm).correlation:.3f})")

os.makedirs("results/metrics", exist_ok=True)
res.to_csv("results/metrics/q02_lsp_share.csv", index=False)
print("\nSaved results/metrics/q02_lsp_share.csv")
