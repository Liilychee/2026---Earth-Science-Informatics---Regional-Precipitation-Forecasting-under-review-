# ============================================================
# analysis_q07_baselines.py — issue 07 (R1 M2, R3 L341-344, R4 m8; overlaps item 20 = R1 m5 / R4 m22).
# NO deep-model training. Reads the saved prediction CSVs and the regional ERA5 csv. Fits every baseline on
# TRAINING rows only and evaluates on the TEST split.
#
# Baselines
#   Climatologies (training targets):  global mean | diurnal (hour of day) | seasonal (DJF..SON) | monthly (12) |
#                                      month x hour (48)
#   Persistence (saved file) and AR(1): y(t) = a + b*y(t-1)  (damped persistence, see q05c)
#   Single-predictor references (R4 m8: "what if a predictor like lsp were the reference?"):
#       linear regression of the target on lsp at the forecast origin (last input snapshot, row j-1)
#       linear regression of the target on mxtpr at the forecast origin
# Outputs: RMSE, MAE, R2 on test; RMSE skill score (1 - RMSE/RMSE_ref) against global climatology and against
# the best climatology; paired circular block bootstrap (block 28, 2,000 reps, seed 42) of
# RMSE(model) - RMSE(reference); per-season RMSE skill against the month x hour climatology.
#
# Alignment (same as step2d / exp_q02_cp_predictor): chronological 70/15/15 split of the csv; inside each split a
# window of 6 snapshots (rows i..i+5) predicts row i+6; so the forecast origin of target row j is row j-1.
#
# Run from the folder containing data/ and results/ (AutoDL: cd /root/autodl-tmp):
#     python3 code/analysis_q07_baselines.py 2>&1 | tee results/metrics/q07_output.txt
# Outputs (results/metrics/): q07_baseline_metrics.csv, q07_model_minus_reference.csv, q07_season_skill.csv
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

# ---------- data: rows, split, forecast-origin predictors ----------
df = pd.read_csv(DATA, parse_dates=["valid_time"]).sort_values("valid_time").reset_index(drop=True)
df["tp_mm"] = df["tp"] * 1000.0 if "tp" in df.columns else df["tp_mm"]
df["lsp_mm"] = df["lsp"] * 1000.0
n = len(df)
tr_end, va_end = int(n * 0.70), int(n * 0.85)
bounds = {"train": (0, tr_end), "val": (tr_end, va_end), "test": (va_end, n)}
frames = {}
for k, (a, b) in bounds.items():
    p = df.iloc[a:b].reset_index(drop=True)
    t = p.iloc[WINDOW:].copy()                       # target rows
    o = p.iloc[WINDOW - 1:len(p) - 1]                # forecast-origin rows (row j-1)
    t["lsp_origin"] = o["lsp_mm"].to_numpy()
    t["mxtpr_origin"] = o["mxtpr"].to_numpy()
    t["y_lag"] = o["tp_mm"].to_numpy()               # y(t-1): target of the previous step
    t["y"] = t["tp_mm"]
    t["month"] = t.valid_time.dt.month
    t["hour"] = t.valid_time.dt.hour
    t["season"] = t.month.map(SEASON)
    frames[k] = t.reset_index(drop=True)
tr, te = frames["train"], frames["test"]
print(f"Data: {DATA}; rows {n}; train/val/test targets {len(tr)}/{len(frames['val'])}/{len(te)}")

# ---------- saved predictions: alignment check ----------
raw = {m: pd.read_csv(os.path.join(PRED_DIR, f), parse_dates=["valid_time"])
       for m, f in MODELS.items() if os.path.exists(os.path.join(PRED_DIR, f))}
pers = pd.read_csv(os.path.join(PRED_DIR, "persistence_preds.csv"), parse_dates=["valid_time"])


def test_part(d):
    return d[d.split == "test"].drop_duplicates("valid_time").sort_values("valid_time").reset_index(drop=True)


pt = {m: test_part(d) for m, d in raw.items()}
ref_t = pt["XGBoost"]
assert len(ref_t) == len(te), f"test length mismatch: preds {len(ref_t)} vs csv windows {len(te)}"
assert (ref_t.valid_time.to_numpy() == te.valid_time.to_numpy()).all(), "test valid_time mismatch"
assert np.allclose(ref_t.y_true.to_numpy(), te["y"].to_numpy(), atol=1e-6), "y_true mismatch with csv target"
for m in pt:
    assert (pt[m].valid_time.to_numpy() == te.valid_time.to_numpy()).all(), m
y = te["y"].to_numpy()
N = len(y)
ptest = test_part(pers)
assert np.allclose(ptest.y_pred_mean.to_numpy(), te["y_lag"].to_numpy(), atol=1e-6), "y_lag != saved Persistence"
print("Alignment OK: csv targets, forecast-origin lag and saved Persistence agree on the test split.")

# ---------- baselines (fit on TRAIN only) ----------
S = {}
S["Climatology: global mean"] = np.full(N, tr["y"].mean())


def tbl_pred(keys):
    g = tr.groupby(keys)["y"].mean()
    idx = pd.MultiIndex.from_frame(te[keys]) if len(keys) > 1 else te[keys[0]]
    return g.reindex(idx).to_numpy()


S["Climatology: diurnal (hour)"] = tbl_pred(["hour"])
S["Climatology: seasonal (DJF..SON)"] = tbl_pred(["season"])
S["Climatology: monthly"] = tbl_pred(["month"])
S["Climatology: month x hour"] = tbl_pred(["month", "hour"])
S["Persistence"] = te["y_lag"].to_numpy()
for lab, col in (("AR(1) damped persistence", "y_lag"), ("Linear on lsp(t)", "lsp_origin"),
                 ("Linear on mxtpr(t)", "mxtpr_origin")):
    b, a = np.polyfit(tr[col], tr["y"], 1)
    S[lab] = a + b * te[col].to_numpy()
    print(f"{lab:26s}: y = {a:.4f} + {b:.4g} * {col}")
for m in pt:
    S[m] = pt[m]["y_pred_mean"].to_numpy()
assert all(np.isfinite(v).all() for v in S.values()), "NaN in a baseline (a month/hour cell missing in training?)"


def rmse(p, o): return float(np.sqrt(np.mean((p - o) ** 2)))
def mae(p, o): return float(np.mean(np.abs(p - o)))
def r2(p, o): return float(1 - np.sum((o - p) ** 2) / np.sum((o - o.mean()) ** 2))


CLIMS = [k for k in S if k.startswith("Climatology")]
rm = {k: rmse(v, y) for k, v in S.items()}
best_clim = min(CLIMS, key=lambda k: rm[k])
print(f"\nBest climatology on test: {best_clim} (RMSE {rm[best_clim]:.4f}); global {rm['Climatology: global mean']:.4f}"
      f" (expected 0.2737 for global and 0.2731 for month x hour from analysis_revision_metrics.py)")

rows = []
for k, v in S.items():
    rows.append({"Forecast": k, "RMSE": rm[k], "MAE": mae(v, y), "R2": r2(v, y),
                 "Skill_vs_global_clim": 1 - rm[k] / rm["Climatology: global mean"],
                 "Skill_vs_best_clim": 1 - rm[k] / rm[best_clim],
                 "Skill_vs_month_x_hour": 1 - rm[k] / rm["Climatology: month x hour"]})
A = pd.DataFrame(rows)
print("\n=== A. TEST METRICS: all baselines and models (skill = 1 - RMSE/RMSE_reference) ===")
print(A.round(4).to_string(index=False))
A.to_csv(os.path.join(MET, "q07_baseline_metrics.csv"), index=False)

# ---------- B. paired block bootstrap: model - reference ----------
rng = np.random.default_rng(SEED)
nb = int(np.ceil(N / BLOCK))
IDX = [((rng.integers(0, N, nb)[:, None] + np.arange(BLOCK)[None, :]) % N).ravel()[:N] for _ in range(NBOOT)]


def boot(pm, pb):
    d = np.array([rmse(pm[ix], y[ix]) - rmse(pb[ix], y[ix]) for ix in IDX])
    return np.percentile(d, [2.5, 97.5])


REFS = [best_clim, "AR(1) damped persistence", "Linear on lsp(t)", "Linear on mxtpr(t)"]
rows = []
for r in REFS:
    for m in pt:
        lo, hi = boot(S[m], S[r])
        rows.append({"Reference": r, "Model": m, "RMSE_model": rm[m], "RMSE_reference": rm[r],
                     "Diff": rm[m] - rm[r], "CI_low": lo, "CI_high": hi, "Significant": bool(hi < 0 or lo > 0)})
B = pd.DataFrame(rows)
print("\n=== B. RMSE(model) - RMSE(reference); paired block bootstrap; negative = model better ===")
print(B.round(4).to_string(index=False))
B.to_csv(os.path.join(MET, "q07_model_minus_reference.csv"), index=False)

# ---------- C. per-season RMSE skill against month x hour climatology ----------
seas = te["season"].to_numpy()
rows = []
for k in S:
    for s in ["DJF", "MAM", "JJA", "SON"]:
        m = seas == s
        c = rmse(S["Climatology: month x hour"][m], y[m])
        rows.append({"Forecast": k, "Season": s, "N": int(m.sum()), "RMSE": rmse(S[k][m], y[m]),
                     "RMSE_month_x_hour_clim": c, "Skill_vs_month_x_hour": 1 - rmse(S[k][m], y[m]) / c})
C = pd.DataFrame(rows)
print("\n=== C. SEASONAL RMSE SKILL vs month x hour climatology (negative = worse than climatology) ===")
print(C.pivot(index="Forecast", columns="Season", values="Skill_vs_month_x_hour").round(3).to_string())
C.to_csv(os.path.join(MET, "q07_season_skill.csv"), index=False)
print("\nSaved q07_*.csv to", MET)
