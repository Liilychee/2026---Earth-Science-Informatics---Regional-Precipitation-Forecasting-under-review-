# ============================================================
# analysis_q04b_transfer_to_station.py — issue 04b: zero-retraining "transfer to observations" check.
# Question: models were trained on ERA5 (regional-mean tp). How do their TEST-SET predictions
# relate to the REAL hourly rain measured at Dublin Airport (Met Eireann hly532) at the same times?
#   - reference row  "ERA5 target (y_true)"  = how well the ERA5 label itself matches the station
#     (the practical ceiling for any model trained on ERA5)
#   - one row per model: Spearman / Pearson / RMSE / MAE vs the station + wet (>=0.1 mm/h) POD/FAR/CSI
#   - ranking of the models vs the ERA5 target and vs the station (does the ranking survive?)
#   - paired circular block bootstrap (block 28 = 7 days, 2,000 reps, seed 42) 95% CIs
# NO training. Reads saved prediction CSVs and results/metrics/q04_pairs.csv (from analysis_q04).
# Nothing existing is modified.
#
# Run from the folder containing results/ (AutoDL: cd /root/autodl-tmp):
#     python3 code/analysis_q04b_transfer_to_station.py
# Outputs (results/metrics/): q04b_transfer_to_station.csv, q04b_ranking_vs_station.csv
# ============================================================
import os
import numpy as np
import pandas as pd

ROOTS = ["results", "/root/autodl-tmp/results", "../results"]
ROOT = next(r for r in ROOTS if os.path.isdir(r))
PRED_DIR = next(d for d in (os.path.join(ROOT, "predictions"), ROOT)
                if os.path.exists(os.path.join(d, "xgboost_preds.csv")))
MET = os.path.join(ROOT, "metrics")
PAIRS = os.path.join(MET, "q04_pairs.csv")
assert os.path.exists(PAIRS), f"{PAIRS} not found: run analysis_q04_station_vs_era5.py first"

WET = 0.1
BLOCK, NBOOT, SEED = 28, 2000, 42

MODELS = {
    "Persistence": "persistence_preds.csv",
    "Climatology (global mean)": "climatology_preds.csv",
    "XGBoost": "xgboost_preds.csv",
    "Transformer": "transformer_preds.csv",
    "BU-LSTM": "bulstm_preds.csv",
    "BiLSTM-Attention": "bilstm_attention_preds.csv",
    "BU-LSTM-Attention (proposed)": "proposed_model_preds.csv",
    "Probabilistic BiLSTM-Attention": "prob_bilstm_attention_preds.csv",
}

pairs = pd.read_csv(PAIRS, parse_dates=["valid_time"]).drop_duplicates("valid_time").set_index("valid_time")
print(f"q04_pairs: {len(pairs):,} stamps; station missing: {pairs.station_mm.isna().sum():,}")

# ---- load test predictions and align with the station on valid_time ----
test = {}
for name, f in MODELS.items():
    p = os.path.join(PRED_DIR, f)
    if not os.path.exists(p):
        print(f"  (skip {name}: {f} not found)")
        continue
    d = pd.read_csv(p, parse_dates=["valid_time"])
    d = d[d.split == "test"].drop_duplicates("valid_time").set_index("valid_time").sort_index()
    test[name] = d
base = test["XGBoost"]
common = base.index
for d in test.values():
    common = common.intersection(d.index)
common = common.intersection(pairs.index)
print(f"Aligned test stamps: {len(common):,}")

# alignment sanity check: the saved y_true must equal ERA5 regional-mean tp in q04_pairs at the same stamp
y = base.loc[common, "y_true"].to_numpy()
era_reg = pairs.loc[common, "era5_regional_mm"].to_numpy()
mism = np.abs(y - era_reg)
print(f"Alignment check |y_true - ERA5 regional (pairs)|: max {np.nanmax(mism):.2e} mm, "
      f"share > 1e-3 mm: {np.mean(mism > 1e-3):.4f}")
assert np.mean(mism > 1e-3) < 0.01, ("y_true in the prediction files does not match the ERA5 regional mean at the "
                                     "same valid_time -> time alignment is wrong; do not use these results")
for n, d in test.items():
    assert np.allclose(d.loc[common, "y_true"].to_numpy(), y, atol=1e-6), f"{n}: y_true differs"

obs_all = pairs.loc[common, "station_mm"].to_numpy()
ok = ~np.isnan(obs_all)
obs = obs_all[ok]
print(f"Test stamps with a valid station value: {ok.sum():,}  (wet >= {WET}: {np.mean(obs >= WET)*100:.1f} %)")

series = {"ERA5 target (y_true)": y[ok]}
for n, d in test.items():
    series[n] = d.loc[common, "y_pred_mean"].to_numpy()[ok]
N = len(obs)


def rank(a):
    return pd.Series(a).rank().to_numpy()


def spearman(o, m):
    # a constant prediction (e.g. the global-mean climatology) has no defined correlation -> NaN
    if np.ptp(m) == 0 or np.ptp(o) == 0:
        return np.nan
    return float(np.corrcoef(rank(o), rank(m))[0, 1])


def pearson(o, m):
    if np.ptp(m) == 0 or np.ptp(o) == 0:
        return np.nan
    return float(np.corrcoef(o, m)[0, 1])


def rmse(o, m):
    return float(np.sqrt(np.mean((m - o) ** 2)))


def mae(o, m):
    return float(np.mean(np.abs(m - o)))


def wet_scores(o, m):
    ob, mb = o >= WET, m >= WET
    h, mi, fa = int((ob & mb).sum()), int((ob & ~mb).sum()), int((~ob & mb).sum())
    d = lambda a, b: float(a / b) if b else np.nan
    return d(h, h + mi), d(fa, h + fa), d(h, h + mi + fa)


# ---- paired circular block bootstrap (same resamples for every series) ----
rng = np.random.default_rng(SEED)
nb = int(np.ceil(N / BLOCK))
boot = {k: {"sp": [], "rm": []} for k in series}
for _ in range(NBOOT):
    starts = rng.integers(0, N, size=nb)
    idx = np.concatenate([(s + np.arange(BLOCK)) % N for s in starts])[:N]
    ob_b = obs[idx]
    for k, v in series.items():
        vb = v[idx]
        boot[k]["sp"].append(spearman(ob_b, vb))
        boot[k]["rm"].append(rmse(ob_b, vb))
boot = {k: {m: np.asarray(x) for m, x in v.items()} for k, v in boot.items()}


def ci(a):
    a = np.asarray(a, float)
    if np.isnan(a).all():
        return np.nan, np.nan
    lo, hi = np.nanpercentile(a, [2.5, 97.5])
    return float(lo), float(hi)


rows = []
for k, v in series.items():
    sp, rm = spearman(obs, v), rmse(obs, v)
    pod, far, csi = wet_scores(obs, v)
    sp_lo, sp_hi = ci(boot[k]["sp"])
    rm_lo, rm_hi = ci(boot[k]["rm"])
    d_sp = boot[k]["sp"] - boot["XGBoost"]["sp"]
    d_rm = boot[k]["rm"] - boot["XGBoost"]["rm"]
    rows.append({"Series": k, "N": N, "Spearman_vs_station": sp, "Spearman_CI_low": sp_lo, "Spearman_CI_high": sp_hi,
                 "Pearson_vs_station": pearson(obs, v), "RMSE_vs_station_mm": rm, "RMSE_CI_low": rm_lo,
                 "RMSE_CI_high": rm_hi, "MAE_vs_station_mm": mae(obs, v),
                 "Bias_pred_minus_station_mm": float(np.mean(v - obs)),
                 "Wet_POD": pod, "Wet_FAR": far, "Wet_CSI": csi,
                 "dSpearman_vs_XGB": sp - spearman(obs, series["XGBoost"]),
                 "dSpearman_CI_low": ci(d_sp)[0], "dSpearman_CI_high": ci(d_sp)[1],
                 "dRMSE_vs_XGB": rm - rmse(obs, series["XGBoost"]),
                 "dRMSE_CI_low": ci(d_rm)[0], "dRMSE_CI_high": ci(d_rm)[1]})
res = pd.DataFrame(rows)
res.to_csv(os.path.join(MET, "q04b_transfer_to_station.csv"), index=False)

# ---- ranking: ERA5 target vs station target (models only) ----
mods = [k for k in series if k != "ERA5 target (y_true)"]
rk = []
for k in mods:
    rk.append({"Model": k,
               "RMSE_vs_ERA5_target": rmse(y[ok], series[k]),
               "RMSE_vs_station": rmse(obs, series[k]),
               "Spearman_vs_ERA5_target": spearman(y[ok], series[k]),
               "Spearman_vs_station": spearman(obs, series[k])})
rk = pd.DataFrame(rk)
for c in ("RMSE_vs_ERA5_target", "RMSE_vs_station"):
    rk["Rank_" + c] = rk[c].rank(method="min").astype(int)          # 1 = lowest RMSE
for c in ("Spearman_vs_ERA5_target", "Spearman_vs_station"):
    # undefined rho (constant prediction) is ranked last
    rk["Rank_" + c] = rk[c].fillna(-2.0).rank(ascending=False, method="min").astype(int)   # 1 = highest rho
rk.to_csv(os.path.join(MET, "q04b_ranking_vs_station.csv"), index=False)

pd.set_option("display.width", 220)
print("\n=== Test predictions vs HOURLY STATION observations (Dublin Airport) ===")
show = ["Series", "N", "Spearman_vs_station", "Spearman_CI_low", "Spearman_CI_high", "Pearson_vs_station",
        "RMSE_vs_station_mm", "MAE_vs_station_mm", "Bias_pred_minus_station_mm", "Wet_POD", "Wet_FAR", "Wet_CSI"]
print(res[show].round(4).to_string(index=False))
print("\n=== Difference to XGBoost (paired block bootstrap, 95% CI; CI excluding 0 = clear difference) ===")
print(res[["Series", "dSpearman_vs_XGB", "dSpearman_CI_low", "dSpearman_CI_high",
           "dRMSE_vs_XGB", "dRMSE_CI_low", "dRMSE_CI_high"]].round(4).to_string(index=False))
print("\n=== Ranking: ERA5 target vs station (1 = best) ===")
print(rk.round(4).to_string(index=False))
r_rmse = float(pd.Series(rk["RMSE_vs_ERA5_target"]).corr(pd.Series(rk["RMSE_vs_station"]), method="spearman"))
r_sp = float(pd.Series(rk["Spearman_vs_ERA5_target"]).corr(pd.Series(rk["Spearman_vs_station"]), method="spearman"))
print(f"\nRank agreement between the two targets (Spearman of the model rankings): "
      f"by RMSE {r_rmse:.3f}, by rho {r_sp:.3f}")
ref = res[res.Series == "ERA5 target (y_true)"].iloc[0]
best = res[res.Series != "ERA5 target (y_true)"].dropna(subset=["Spearman_vs_station"]) \
    .sort_values("Spearman_vs_station").iloc[-1]
print(f"Reference (ERA5 label vs station): rho {ref.Spearman_vs_station:.3f}; best model vs station: "
      f"{best.Series} rho {best.Spearman_vs_station:.3f}")
print("\nSaved q04b_transfer_to_station.csv and q04b_ranking_vs_station.csv to", MET)
