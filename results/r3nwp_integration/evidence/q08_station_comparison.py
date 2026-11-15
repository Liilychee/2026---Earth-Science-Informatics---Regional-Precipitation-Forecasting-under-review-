# ============================================================
# Item 08b: the same HRES comparison verified against an independent truth,
# Dublin Airport hourly rain (Met Eireann hly532), zero training.
# Uses the per-sample file written by q08_hres_comparison.py and the station pairs of item 04
# (results/metrics/q04_pairs.csv, same alignment as 04b), so every forecast is identical to
# the ERA5-verified comparison; only the truth changes.
# Note: the station is a point, every forecast and the ERA5 label are 25-cell regional means.
# Outputs: results/metrics/q08b_station_comparison.csv, q08b_station_bootstrap.csv
# ============================================================
import os
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = os.environ.get("Q08_ROOT", "/root/autodl-tmp")
MET = f"{ROOT}/results/metrics"
N_BOOT, BLOCK, SEED = 10000, 14, 42
THRESH = {"wet01": 0.1, "ge1mm": 1.0}   # station resolution is 0.1 mm

al = pd.read_csv(f"{MET}/q08_hres_aligned_samples.csv", parse_dates=["valid_time"])
pairs = pd.read_csv(f"{MET}/q04_pairs.csv", parse_dates=["valid_time"]).drop_duplicates("valid_time")
d = al.merge(pairs[["valid_time", "station_mm", "era5_regional_mm"]], on="valid_time", how="left")
assert np.abs(d["era5_regional_mm"] - d["y_true"]).max() < 1e-5, "ERA5 label in q04_pairs differs from y_true"
n_all, n_nan = len(d), int(d["station_mm"].isna().sum())
d = d.dropna(subset=["station_mm"]).reset_index(drop=True)
print(f"Samples: {n_all} aligned (valid 06/18 UTC); station missing {n_nan}; used {len(d)}")

d = d.rename(columns={"y_true": "ERA5 label (regional mean)",
                      "Perfect 6 h mean (ceiling)": "ERA5 6 h mean (window diagnostic)"})
CLIM = "Climatology (month x hour)"
FORECASTS = ["BiLSTM-Attention", "XGBoost", "BU-LSTM-Attention", "Probabilistic BiLSTM-Attention",
             "BU-LSTM", "Transformer", "Persistence", CLIM, "AR(1)", "HRES (6 h mean)",
             "ERA5 6 h mean (window diagnostic)", "ERA5 label (regional mean)"]
y = d["station_mm"].values
rmse_clim = np.sqrt(np.mean((d[CLIM].values - y) ** 2))
rows = []
for lab in FORECASTS:
    p = d[lab].values
    rmse = float(np.sqrt(np.mean((p - y) ** 2)))
    r = {"forecast": lab, "n": len(y), "RMSE": rmse, "MAE": float(np.mean(np.abs(p - y))),
         "bias": float(np.mean(p - y)), "pearson": float(np.corrcoef(p, y)[0, 1]),
         "spearman": float(spearmanr(p, y).correlation), "skill_vs_clim": 1 - rmse / rmse_clim}
    for tag, thr in THRESH.items():
        o, f = y >= thr, p >= thr
        hi, fa, mi = int((o & f).sum()), int((~o & f).sum()), int((o & ~f).sum())
        r.update({f"{tag}_obs": int(o.sum()), f"{tag}_fcst": hi + fa,
                  f"{tag}_POD": hi / (hi + mi) if hi + mi else np.nan,
                  f"{tag}_FAR": fa / (hi + fa) if hi + fa else np.nan,
                  f"{tag}_CSI": hi / (hi + fa + mi) if hi + fa + mi else np.nan})
    rows.append(r)
tab = pd.DataFrame(rows)
tab.to_csv(f"{MET}/q08b_station_comparison.csv", index=False)
pd.set_option("display.width", 220)
print(f"\nStation truth: mean {y.mean():.4f} mm/h, max {y.max():.1f}, wet>=0.1: {(y >= 0.1).mean():.3f}")
print("\n===== Verified against Dublin Airport (hourly rain, mm) =====")
print(tab[["forecast", "n", "RMSE", "MAE", "bias", "pearson", "spearman", "skill_vs_clim"]]
      .to_string(index=False, float_format=lambda v: f"{v:.4f}"))
print(tab[["forecast"] + [f"{t}_{k}" for t in THRESH for k in ("obs", "fcst", "POD", "FAR", "CSI")]]
      .to_string(index=False, float_format=lambda v: f"{v:.3f}"))

rng = np.random.default_rng(SEED)
n = len(y)
starts = rng.integers(0, n - BLOCK + 1, size=(N_BOOT, int(np.ceil(n / BLOCK))))
idx = (starts[:, :, None] + np.arange(BLOCK)).reshape(N_BOOT, -1)[:, :n]
e2 = {lab: (d[lab].values - y) ** 2 for lab in FORECASTS}
out = []
ref = "HRES (6 h mean)"
for lab in FORECASTS:
    if lab == ref:
        continue
    obs = np.sqrt(e2[lab].mean()) - np.sqrt(e2[ref].mean())
    bs = np.sqrt(e2[lab][idx].mean(1)) - np.sqrt(e2[ref][idx].mean(1))
    lo, hi = np.percentile(bs, [2.5, 97.5])
    out.append({"forecast": lab, "reference": ref, "dRMSE": obs, "ci_low": lo, "ci_high": hi,
                "significant": bool(lo > 0 or hi < 0)})
boot = pd.DataFrame(out)
boot.to_csv(f"{MET}/q08b_station_bootstrap.csv", index=False)
print(f"\n===== dRMSE vs HRES against station truth (block {BLOCK}, {N_BOOT} reps) =====")
print(boot.to_string(index=False, float_format=lambda v: f"{v:+.4f}"))
print("===== q08b STATION COMPARISON COMPLETE =====")
