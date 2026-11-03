# ============================================================
# analysis_revision_metrics.py  — NO training, NO GPU, reads saved
# prediction CSVs only. Computes the extra evidence the reviewers ask
# for. Plotting is done by separate scripts (they read the CSVs below).
#
# Run (anywhere, from the folder that contains results/):
#     python code/analysis_revision_metrics.py
#
# Reviewer items addressed
#   R1-2 / R3 L341   monthly x time-of-day climatology baseline (train only)
#   R1 m5 / R4 m22   RMSE/MAE/R2 for ALL baselines + RMSE skill scores
#   R2 m2            90% AND 95% interval coverage + width
#   R2-4 / R2 m3     event-detection (POD, FAR, CSI, bias) for all
#                    thresholds, all models, incl. baselines
#   R3 §4.1          seasonal RMSE normalised by seasonal climatological mean
#   R1-1             histogram data (pred vs obs) + top-event table
# Thresholds are TRAIN-ONLY quantiles (no test information).
#
# Outputs (results/metrics/):
#   revision_point_metrics.csv, revision_interval_metrics.csv,
#   revision_event_detection.csv, revision_seasonal_rmse.csv,
#   revision_hist_data.csv, revision_top_events.csv,
#   revision_season_precip_dist.csv
# ============================================================
import os
import numpy as np
import pandas as pd

# ---------------- locate inputs / outputs ----------------
ROOTS = ["results", "/root/autodl-tmp/results", "../results"]
ROOT = next(r for r in ROOTS if os.path.isdir(r))
PRED_DIR = next(d for d in (os.path.join(ROOT, "predictions"), ROOT)
                if os.path.exists(os.path.join(d, "xgboost_preds.csv")))
OUT = os.path.join(ROOT, "metrics")
os.makedirs(OUT, exist_ok=True)

MODELS = {   # display name -> file
    "Persistence": "persistence_preds.csv",
    "Climatology (global mean)": "climatology_preds.csv",
    "XGBoost": "xgboost_preds.csv",
    "Transformer": "transformer_preds.csv",
    "BU-LSTM": "bulstm_preds.csv",
    "BiLSTM-Attention": "bilstm_attention_preds.csv",
    "BU-LSTM-Attention (proposed)": "proposed_model_preds.csv",
    "Probabilistic BiLSTM-Attention": "prob_bilstm_attention_preds.csv",
}
dfs = {}
for name, f in MODELS.items():
    d = pd.read_csv(os.path.join(PRED_DIR, f), parse_dates=["valid_time"])
    dfs[name] = d
print("Loaded:", list(dfs))

ref = dfs["XGBoost"]
train = ref[ref.split == "train"].reset_index(drop=True)
test = ref[ref.split == "test"].reset_index(drop=True)
y = test["y_true"].values
t_test = test["valid_time"]

# sanity: every model has the same test targets/times
for n, d in dfs.items():
    dt = d[d.split == "test"].reset_index(drop=True)
    assert np.allclose(dt["y_true"].values, y, atol=1e-6), f"{n}: y_true mismatch"
    assert (dt["valid_time"].values == t_test.values).all(), f"{n}: times mismatch"

# ---------------- monthly x hour climatology (TRAIN ONLY) ----------------
train["month"] = train.valid_time.dt.month
train["hour"] = train.valid_time.dt.hour
clim_tbl = train.groupby(["month", "hour"])["y_true"].mean()
test_key = list(zip(t_test.dt.month, t_test.dt.hour))
clim_month_pred = np.array([clim_tbl[k] for k in test_key])
monthly = test.copy()
monthly["y_pred_mean"] = clim_month_pred
monthly["y_pred_std"] = np.nan
dfs_test = {n: d[d.split == "test"].reset_index(drop=True) for n, d in dfs.items()}
dfs_test["Climatology (month x hour)"] = monthly


def rmse(a, b): return float(np.sqrt(np.mean((a - b) ** 2)))
def mae(a, b): return float(np.mean(np.abs(a - b)))
def r2(a, b): return float(1 - np.sum((a - b) ** 2) / np.sum((a - a.mean()) ** 2))


# ---------------- 1. point metrics + skill scores ----------------
rm_clim_global = rmse(y, dfs_test["Climatology (global mean)"]["y_pred_mean"].values)
rm_clim_month = rmse(y, clim_month_pred)
rows = []
for n, d in dfs_test.items():
    p = d["y_pred_mean"].values
    rm = rmse(y, p)
    rows.append({"Model": n, "N_test": len(y), "RMSE": rm, "MAE": mae(y, p), "R2": r2(y, p),
                 "RMSE_skill_vs_global_clim": 1 - rm / rm_clim_global,
                 "RMSE_skill_vs_month_hour_clim": 1 - rm / rm_clim_month})
pm = pd.DataFrame(rows).sort_values("RMSE")
pm.to_csv(os.path.join(OUT, "revision_point_metrics.csv"), index=False)
print("\n=== POINT METRICS (test) ===\n", pm.round(4).to_string(index=False))

# ---------------- 2. interval metrics (90% and 95%) ----------------
Z = {"90": 1.6448536269514722, "95": 1.959963984540054}
rows = []
for n, d in dfs_test.items():
    if d["y_pred_std"].isna().all():
        continue
    mu, sd = d["y_pred_mean"].values, d["y_pred_std"].values
    for lvl, z in Z.items():
        lo, hi = mu - z * sd, mu + z * sd
        lo_c = np.maximum(lo, 0.0)       # physically clipped at 0 mm
        rows.append({"Model": n, "Level": int(lvl),
                     "Coverage": float(np.mean((y >= lo) & (y <= hi))),
                     "Coverage_abs_error": abs(float(np.mean((y >= lo) & (y <= hi))) - int(lvl) / 100),
                     "MPIW_raw": float(np.mean(hi - lo)),
                     "MPIW_clipped_at_0": float(np.mean(hi - lo_c)),
                     "NegativeLowerBound_rate": float(np.mean(lo < 0))})
im = pd.DataFrame(rows)
im.to_csv(os.path.join(OUT, "revision_interval_metrics.csv"), index=False)
print("\n=== INTERVAL METRICS (test) ===\n", im.round(4).to_string(index=False))

# ---------------- 3. event detection (train-only thresholds) ----------------
qs = {"Q90": 0.90, "Q95": 0.95, "Q97.5": 0.975}
thr = {k: float(np.quantile(train["y_true"].values, q)) for k, q in qs.items()}
thr["0.1 mm"] = 0.1
thr["0.5 mm"] = 0.5
thr["1.0 mm"] = 1.0
rows = []
for tname, tv in thr.items():
    obs = y >= tv
    for n, d in dfs_test.items():
        pr = d["y_pred_mean"].values >= tv
        hit = int(np.sum(obs & pr)); miss = int(np.sum(obs & ~pr)); fa = int(np.sum(~obs & pr))
        div = lambda a, b: float(a / b) if b > 0 else np.nan
        rows.append({"Threshold": tname, "Threshold_mm": tv, "Model": n,
                     "N_obs_events": int(obs.sum()), "N_pred_events": int(pr.sum()),
                     "Hits": hit, "Misses": miss, "FalseAlarms": fa,
                     "POD": div(hit, hit + miss),
                     "FAR": div(fa, hit + fa),
                     "CSI": div(hit, hit + miss + fa),
                     "FrequencyBias": div(hit + fa, hit + miss)})
ev = pd.DataFrame(rows)
ev.to_csv(os.path.join(OUT, "revision_event_detection.csv"), index=False)
print("\n=== EVENT DETECTION (Q95 only shown) ===")
print(ev[ev.Threshold == "Q95"].round(3).to_string(index=False))

# ---------------- 4. seasonal RMSE normalised by seasonal climatology ----------------
season_of = {12: "DJF", 1: "DJF", 2: "DJF", 3: "MAM", 4: "MAM", 5: "MAM",
             6: "JJA", 7: "JJA", 8: "JJA", 9: "SON", 10: "SON", 11: "SON"}
train["season"] = train.valid_time.dt.month.map(season_of)
test_season = t_test.dt.month.map(season_of).values
clim_season_mean = train.groupby("season")["y_true"].mean()
rows = []
for n, d in dfs_test.items():
    p = d["y_pred_mean"].values
    for s in ["DJF", "MAM", "JJA", "SON"]:
        m = test_season == s
        rm = rmse(y[m], p[m])
        rows.append({"Model": n, "Season": s, "N": int(m.sum()), "RMSE": rm,
                     "Train_season_mean_mm": float(clim_season_mean[s]),
                     "RMSE_over_season_mean": rm / float(clim_season_mean[s]),
                     "Obs_mean_test_mm": float(y[m].mean())})
ss = pd.DataFrame(rows)
ss.to_csv(os.path.join(OUT, "revision_seasonal_rmse.csv"), index=False)
print("\n=== SEASONAL RMSE / seasonal train mean ===")
print(ss.pivot(index="Model", columns="Season", values="RMSE_over_season_mean").round(2).to_string())

# ---------------- 5. per-season precipitation distribution (whole 2004-2021) ----------------
allobs = ref.drop_duplicates("valid_time")[["valid_time", "y_true"]].copy()
allobs["season"] = allobs.valid_time.dt.month.map(season_of)
qlist = [0.5, 0.75, 0.9, 0.95, 0.975, 0.99, 0.999]
rows = []
for s, g in allobs.groupby("season"):
    rec = {"Season": s, "N": len(g), "Mean_mm": g.y_true.mean(),
           "Frac_ge_0.1mm": float((g.y_true >= 0.1).mean()),
           "Frac_ge_0.5mm": float((g.y_true >= 0.5).mean()),
           "Frac_ge_1.0mm": float((g.y_true >= 1.0).mean()), "Max_mm": g.y_true.max()}
    for q in qlist:
        rec[f"Q{q*100:g}_mm"] = float(g.y_true.quantile(q))
    rows.append(rec)
pd.DataFrame(rows).to_csv(os.path.join(OUT, "revision_season_precip_dist.csv"), index=False)
print("\n=== PRECIP DISTRIBUTION BY SEASON (all years) ===")
print(pd.DataFrame(rows).round(3).to_string(index=False))

# ---------------- 6. histogram data + top events ----------------
bins = np.concatenate([[0], np.arange(0.05, 1.0, 0.05), [1.0, 2.0, 10.0]])
hist_rows = []
oh, _ = np.histogram(y, bins=bins)
for i in range(len(bins) - 1):
    hist_rows.append({"Series": "Observed", "bin_lo": bins[i], "bin_hi": bins[i + 1], "count": int(oh[i])})
for n in ["XGBoost", "BiLSTM-Attention", "BU-LSTM-Attention (proposed)"]:
    ph, _ = np.histogram(np.clip(dfs_test[n]["y_pred_mean"].values, 0, None), bins=bins)
    for i in range(len(bins) - 1):
        hist_rows.append({"Series": n, "bin_lo": bins[i], "bin_hi": bins[i + 1], "count": int(ph[i])})
pd.DataFrame(hist_rows).to_csv(os.path.join(OUT, "revision_hist_data.csv"), index=False)

print("\n=== PREDICTION SPREAD vs OBSERVATION (test) — are predictions squeezed to the mean? ===")
for n in ["XGBoost", "BiLSTM-Attention", "BU-LSTM-Attention (proposed)"]:
    p = dfs_test[n]["y_pred_mean"].values
    print(f"{n:32s} std={p.std():.3f} (obs std={y.std():.3f}) max={p.max():.3f} (obs max={y.max():.3f}) "
          f"P(pred>=Q95 thr)={np.mean(p >= thr['Q95']):.4f} vs obs {np.mean(y >= thr['Q95']):.4f}")

top_idx = np.argsort(-y)[:15]
te = pd.DataFrame({"valid_time": t_test.values[top_idx], "obs_mm": y[top_idx]})
for n in ["XGBoost", "BiLSTM-Attention", "BU-LSTM-Attention (proposed)"]:
    te[n] = dfs_test[n]["y_pred_mean"].values[top_idx]
te.to_csv(os.path.join(OUT, "revision_top_events.csv"), index=False)
print("\n=== TOP-15 OBSERVED TEST EVENTS vs predictions ===")
print(te.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
print("\nSaved CSVs to", OUT)
