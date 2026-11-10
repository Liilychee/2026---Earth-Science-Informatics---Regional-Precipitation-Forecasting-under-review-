# ============================================================
# analysis_q03e_convective_strata.py  --  issue 02 (R4 M3) / 03, zero-training
#
# Reviewer: "summer convective cases are typically harder to predict".
# We already have seasonal skill (07).  Here we add a direct look at convective-dominated hours,
# using ONLY the saved test predictions (no retraining):
#   strata of the TARGET hour among wet samples (tp >= 0.1 mm):
#       convective-dominated  : cp/tp >= 0.5   (cp = tp - lsp at the target hour)
#       large-scale-dominated : cp/tp <  0.5
#   crossed with  all seasons / JJA / non-JJA.
# NOTE: the strata are defined from the OUTCOME hour (descriptive evaluation split, not a predictor).
# RMSE is not comparable between strata with different mean intensity, so we also report
# RMSE / mean observation, Pearson r, and RMSE skill vs the month x hour climatology (TRAIN targets).
# Block-bootstrap (circular, block 28, 2,000, seed 42) 95% intervals for RMSE.
#
# Run from the folder containing data/ and results/ (AutoDL: cd /root/autodl-tmp):
#     python3 code/analysis_q03e_convective_strata.py 2>&1 | tee results/metrics/q03e_convective_strata_output.txt
# Output (results/metrics/): q03e_convective_strata.csv
# ============================================================
import os
import numpy as np
import pandas as pd

ROOTS = ["results", "/root/autodl-tmp/results", "../results"]
ROOT = next(r for r in ROOTS if os.path.isdir(r))
PRED_DIR = next(d for d in (os.path.join(ROOT, "predictions"), ROOT)
                if os.path.exists(os.path.join(d, "xgboost_preds.csv")))
MET = os.path.join(ROOT, "metrics")
os.makedirs(MET, exist_ok=True)
CANDS = ["data/dublin_regional_reduced.csv", "../data/dublin_regional_reduced.csv",
         "data/dublin_regional_2004_2021.csv", "../data/dublin_regional_2004_2021.csv",
         "/root/autodl-tmp/data/dublin_regional_reduced.csv"]
DATA = next(p for p in CANDS if os.path.exists(p))
MODELS = {
    "XGBoost": "xgboost_preds.csv",
    "Transformer": "transformer_preds.csv",
    "BU-LSTM": "bulstm_preds.csv",
    "BiLSTM-Attention": "bilstm_attention_preds.csv",
    "BU-LSTM-Attention (proposed)": "proposed_model_preds.csv",
    "Probabilistic BiLSTM-Attention": "prob_bilstm_attention_preds.csv",
}
WINDOW, BLOCK, NBOOT, SEED = 6, 28, 2000, 42
SEASON = {12: "DJF", 1: "DJF", 2: "DJF", 3: "MAM", 4: "MAM", 5: "MAM",
          6: "JJA", 7: "JJA", 8: "JJA", 9: "SON", 10: "SON", 11: "SON"}

df = pd.read_csv(DATA, parse_dates=["valid_time"]).sort_values("valid_time").reset_index(drop=True)
df["tp_mm"] = df["tp"] * 1000.0 if "tp" in df.columns else df["tp_mm"]
df["lsp_mm"] = df["lsp"] * 1000.0
n = len(df)
tr_end, va_end = int(n * 0.70), int(n * 0.85)
frames = {}
for k, (a, b) in {"train": (0, tr_end), "test": (va_end, n)}.items():
    p = df.iloc[a:b].reset_index(drop=True)
    t = p.iloc[WINDOW:].copy()
    t["y_lag"] = p.iloc[WINDOW - 1:len(p) - 1]["tp_mm"].to_numpy()
    t["y"] = t["tp_mm"]
    t["month"], t["hour"] = t.valid_time.dt.month, t.valid_time.dt.hour
    t["season"] = t.month.map(SEASON)
    frames[k] = t.reset_index(drop=True)
tr, te = frames["train"], frames["test"]
y, N = te["y"].to_numpy(), len(te)
print(f"Data: {DATA}; test targets {N}")

# ---- saved predictions + alignment (same checks as analysis_q07_baselines.py) ----
P = {}
for m, f in MODELS.items():
    fp = os.path.join(PRED_DIR, f)
    if not os.path.exists(fp):
        print("missing", f)
        continue
    d = pd.read_csv(fp, parse_dates=["valid_time"])
    d = d[d.split == "test"].drop_duplicates("valid_time").sort_values("valid_time").reset_index(drop=True)
    assert len(d) == N and (d.valid_time.to_numpy() == te.valid_time.to_numpy()).all(), m
    assert np.allclose(d.y_true.to_numpy(), y, atol=1e-6), m
    P[m] = d.y_pred_mean.to_numpy()
P["Persistence"] = te["y_lag"].to_numpy()
clim = tr.groupby(["month", "hour"]).y.mean()
P["Climatology (month x hour)"] = np.array([clim.loc[(a, b)] for a, b in zip(te.month, te.hour)])
ref = P["Climatology (month x hour)"]
print("Alignment OK. Models:", list(P))

# ---- strata (target hour) ----
cp_share = np.where(te.tp_mm > 0, (te.tp_mm - te.lsp_mm) / te.tp_mm.where(te.tp_mm > 0, np.nan), np.nan)
wet = y >= 0.1
conv = wet & (cp_share >= 0.5)
ls = wet & (cp_share < 0.5)
jja = (te.season == "JJA").to_numpy()
masks = {
    "all test": np.ones(N, bool),
    "JJA (all hours)": jja, "non-JJA (all hours)": ~jja,
    "wet": wet, "wet & convective-dominated": conv, "wet & large-scale-dominated": ls,
    "JJA & wet & convective-dominated": conv & jja, "JJA & wet & large-scale-dominated": ls & jja,
    "non-JJA & wet & convective-dominated": conv & ~jja, "non-JJA & wet & large-scale-dominated": ls & ~jja,
}
print("\nStratum sizes:", {k: int(v.sum()) for k, v in masks.items()})
for k, v in masks.items():
    if 0 < v.sum() < 30:
        print(f"  WARNING: '{k}' has only {int(v.sum())} samples -> read as descriptive only")

# ---- block bootstrap indices ----
rng = np.random.default_rng(SEED)
nblk = int(np.ceil(N / BLOCK))
starts = rng.integers(0, N, size=(NBOOT, nblk))
idx = ((starts[:, :, None] + np.arange(BLOCK)[None, None, :]) % N).reshape(NBOOT, -1)[:, :N]

rows = []
for mname, yp in P.items():
    e2 = (y - yp) ** 2
    for sname, mk in masks.items():
        k = int(mk.sum())
        if k == 0:
            continue
        yt, pp = y[mk], yp[mk]
        rm = float(np.sqrt(np.mean((yt - pp) ** 2)))
        mean_obs = float(yt.mean())
        r = float(np.corrcoef(yt, pp)[0, 1]) if k > 2 and np.std(pp) > 0 and np.std(yt) > 0 else np.nan
        rm_ref = float(np.sqrt(np.mean((yt - ref[mk]) ** 2)))
        m = mk.astype(float)
        num, den = (e2[idx] * m[idx]).sum(1), m[idx].sum(1)
        bs = np.sqrt(np.where(den > 0, num / np.maximum(den, 1), np.nan))
        rows.append({"Model": mname, "Stratum": sname, "N": k, "Mean_obs_mm_h": mean_obs,
                     "RMSE": rm, "RMSE_CI_low": float(np.nanpercentile(bs, 2.5)),
                     "RMSE_CI_high": float(np.nanpercentile(bs, 97.5)),
                     "RMSE_over_mean_obs": rm / mean_obs if mean_obs > 0 else np.nan,
                     "Pearson_r": r, "Skill_vs_monthhour_clim": 1 - rm / rm_ref if rm_ref > 0 else np.nan})
R = pd.DataFrame(rows)
R.to_csv(os.path.join(MET, "q03e_convective_strata.csv"), index=False)

show = ["XGBoost", "BU-LSTM-Attention (proposed)", "Persistence"]
for sname in masks:
    s = R[(R.Stratum == sname) & R.Model.isin(show)]
    if len(s):
        print(f"\n--- {sname} (N={int(masks[sname].sum())}) ---")
        print(s[["Model", "Mean_obs_mm_h", "RMSE", "RMSE_CI_low", "RMSE_CI_high", "RMSE_over_mean_obs",
                 "Pearson_r", "Skill_vs_monthhour_clim"]].round(3).to_string(index=False))
print("\nFull table (all models) saved to", os.path.join(MET, "q03e_convective_strata.csv"))
