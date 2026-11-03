# ============================================================
# analysis_q05c_damped_persistence.py — issue 05c / 07 (R1 M2: baselines too weak; supports 05 "reactive" finding).
# NO deep-model training: reads the saved prediction CSVs only. Fits two cheap baselines on TRAINING rows only:
#   AR1      : y(t) = a + b * y(t-1)                      (damped persistence; y(t-1) = previous 6-hourly target)
#   AR1+clim : y(t) = c(t) + b * (y(t-1) - c(t-1))         (c = training month x hour-of-day mean)
# where y(t-1) is the target at valid_time - 6 h, i.e. exactly what the Persistence baseline uses.
# Reports on TEST: RMSE, MAE, R2, Pearson, std ratio; ROC-AUC and validation-tuned-cutoff POD/FAR/CSI at Q95 and
# 1.0 mm/h; and paired circular block bootstrap (block 28, 2,000 reps, seed 42) of RMSE(model) - RMSE(baseline)
# (negative = model better than the baseline).
#
# Run from the folder containing results/ (AutoDL: cd /root/autodl-tmp):
#     python3 code/analysis_q05c_damped_persistence.py 2>&1 | tee results/metrics/q05c_output.txt
# Outputs (results/metrics/): q05c_baselines.csv, q05c_model_minus_baseline.csv, q05c_event_scores.csv
# ============================================================
import os
import numpy as np
import pandas as pd
from scipy.stats import rankdata
 
ROOTS = ["results", "/root/autodl-tmp/results", "../results"]
ROOT = next(r for r in ROOTS if os.path.isdir(r))
PRED_DIR = next(d for d in (os.path.join(ROOT, "predictions"), ROOT)
                if os.path.exists(os.path.join(d, "xgboost_preds.csv")))
MET = os.path.join(ROOT, "metrics")
os.makedirs(MET, exist_ok=True)
 
MODELS = {
    "Persistence": "persistence_preds.csv",
    "XGBoost": "xgboost_preds.csv",
    "Transformer": "transformer_preds.csv",
    "BU-LSTM": "bulstm_preds.csv",
    "BiLSTM-Attention": "bilstm_attention_preds.csv",
    "BU-LSTM-Attention (proposed)": "proposed_model_preds.csv",
    "Probabilistic BiLSTM-Attention": "prob_bilstm_attention_preds.csv",
}
BLOCK, NBOOT, SEED = 28, 2000, 42
 
raw = {n: pd.read_csv(os.path.join(PRED_DIR, f), parse_dates=["valid_time"])
       for n, f in MODELS.items() if os.path.exists(os.path.join(PRED_DIR, f))}
ref = raw["XGBoost"].drop_duplicates("valid_time").sort_values("valid_time").reset_index(drop=True)
ser = ref.set_index("valid_time")["y_true"]          # full target series (train+val+test)
STEP = pd.Timedelta(hours=6)
# The prediction files keep only windowed targets, so the first rows of each split have no y(t-6h) in the series.
# The saved Persistence prediction IS y(t-6h) (built from the input window), so use it to fill those gaps.
if "Persistence" in raw:
    _p = raw["Persistence"].drop_duplicates("valid_time").set_index("valid_time")["y_pred_mean"]
else:
    _p = pd.Series(dtype=float)
 
tr = ref[ref.split == "train"]
tr_y_all = tr["y_true"].to_numpy()
THR = {"Q95": float(np.quantile(tr_y_all, 0.95)), "1.0 mm/h": 1.0}
print("Thresholds (training):", {k: round(v, 4) for k, v in THR.items()})
 
# ---- climatology month x hour from training targets ----
clim = tr.assign(m=tr.valid_time.dt.month, h=tr.valid_time.dt.hour).groupby(["m", "h"])["y_true"].mean()
 
 
def c_of(times):
    idx = pd.MultiIndex.from_arrays([times.dt.month, times.dt.hour])
    return clim.reindex(idx).to_numpy()
 
 
def lag_frame(d):
    """rows of d with the target at valid_time-6h attached (NaN if missing)."""
    out = d[["valid_time", "y_true"]].copy()
    out["y_lag_ser"] = (out["valid_time"] - STEP).map(ser)
    out["y_lag"] = out["y_lag_ser"].fillna(out["valid_time"].map(_p))
    out["c"] = c_of(out["valid_time"])
    out["c_lag"] = c_of(out["valid_time"] - STEP)
    return out
 
 
# ---- fit on TRAIN only ----
f_tr = lag_frame(tr).dropna(subset=["y_lag", "c_lag", "c"])
b1, a1 = np.polyfit(f_tr["y_lag"], f_tr["y_true"], 1)
x2 = f_tr["y_lag"] - f_tr["c_lag"]
t2 = f_tr["y_true"] - f_tr["c"]
b2 = float((x2 * t2).sum() / (x2 * x2).sum())
print(f"AR1      : y(t) = {a1:.4f} + {b1:.4f} * y(t-1)   (train N = {len(f_tr)})")
print(f"AR1+clim : y(t) = c(t) + {b2:.4f} * (y(t-1) - c(t-1))")
 
 
def part(d, which):
    m = (d.split == "test") if which == "test" else ~d.split.isin(["train", "test"])
    return d[m].drop_duplicates("valid_time").sort_values("valid_time").reset_index(drop=True)
 
 
def baselines(d):
    f = lag_frame(d)
    f["AR1 (damped persistence)"] = a1 + b1 * f["y_lag"]
    f["AR1 + month x hour clim"] = f["c"] + b2 * (f["y_lag"] - f["c_lag"])
    return f
 
 
test_b = baselines(part(ref, "test"))
val_b = baselines(part(ref, "val"))
assert test_b["y_lag"].notna().all() and val_b["y_lag"].notna().all(), "missing lagged target"
y = test_b["y_true"].to_numpy()
t0 = test_b["valid_time"].to_numpy()
N = len(y)
 
# sanity: my lagged target must equal the saved Persistence prediction
if "Persistence" in raw:
    pt = part(raw["Persistence"], "test")
    assert (pt["valid_time"].to_numpy() == t0).all()
    _m = test_b["y_lag_ser"].notna().to_numpy()
    assert np.allclose(pt["y_pred_mean"].to_numpy()[_m], test_b["y_lag_ser"].to_numpy()[_m], atol=1e-6), \
        "lagged target != saved Persistence prediction"
    print(f"Check OK: y(t-1) equals the saved Persistence predictions ({int(_m.sum())} of {N} test rows checked; "
          f"{int((~_m).sum())} first-of-split rows take y(t-1) from the Persistence file).")
 
# ---- collect score vectors on test / val ----
BASE = ["AR1 (damped persistence)", "AR1 + month x hour clim"]
pt_ = {n: part(d, "test") for n, d in raw.items()}
pv_ = {n: part(d, "val") for n, d in raw.items()}
S_test = {n: pt_[n]["y_pred_mean"].to_numpy() for n in raw}
S_val = {n: pv_[n]["y_pred_mean"].to_numpy() for n in raw}
for n in raw:
    assert (pt_[n]["valid_time"].to_numpy() == t0).all(), n
    assert np.allclose(pt_[n]["y_true"].to_numpy(), y, atol=1e-6), n
for b in BASE:
    S_test[b] = test_b[b].to_numpy()
    S_val[b] = val_b[b].to_numpy()
y_val = val_b["y_true"].to_numpy()
ORDER = list(raw) + BASE
 
 
def rmse(p, o): return float(np.sqrt(np.mean((p - o) ** 2)))
def mae(p, o): return float(np.mean(np.abs(p - o)))
 
 
def r2(p, o): return float(1 - np.sum((o - p) ** 2) / np.sum((o - o.mean()) ** 2))
 
 
def pear(p, o): return float(np.corrcoef(p, o)[0, 1]) if np.ptp(p) > 0 else np.nan
 
 
def auc(o, s):
    o = np.asarray(o, bool)
    n1, n0 = int(o.sum()), int((~o).sum())
    if n1 == 0 or n0 == 0:
        return np.nan
    r = rankdata(s)
    return float((r[o].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))
 
 
def csi_stats(o, p):
    o = np.asarray(o, bool); p = np.asarray(p, bool)
    h = int((o & p).sum()); fa = int((~o & p).sum()); m = int((o & ~p).sum())
    pod = h / (h + m) if h + m else np.nan
    far = fa / (h + fa) if h + fa else np.nan
    csi = h / (h + m + fa) if h + m + fa else 0.0
    return h, fa, pod, far, csi
 
 
# ---- A. overall skill ----
rows = []
for n in ORDER:
    p = S_test[n]
    rows.append({"Model": n, "RMSE": rmse(p, y), "MAE": mae(p, y), "R2": r2(p, y), "Pearson_r": pear(p, y),
                 "Std_ratio": float(np.std(p) / np.std(y))})
A = pd.DataFrame(rows)
print("\n=== A. TEST SKILL (mm/h): deep models vs cheap baselines ===")
print(A.round(4).to_string(index=False))
A.to_csv(os.path.join(MET, "q05c_baselines.csv"), index=False)
 
# ---- B. paired block bootstrap of RMSE(model) - RMSE(baseline) ----
rng = np.random.default_rng(SEED)
nb = int(np.ceil(N / BLOCK))
IDX = [((rng.integers(0, N, nb)[:, None] + np.arange(BLOCK)[None, :]) % N).ravel()[:N] for _ in range(NBOOT)]
 
 
def boot_diff(pm, pb):
    d = np.empty(NBOOT)
    for i, ix in enumerate(IDX):
        d[i] = rmse(pm[ix], y[ix]) - rmse(pb[ix], y[ix])
    return np.percentile(d, [2.5, 97.5])
 
 
rows = []
for b in BASE:
    for n in raw:
        if n == "Persistence":
            continue
        lo, hi = boot_diff(S_test[n], S_test[b])
        rows.append({"Baseline": b, "Model": n, "RMSE_model": rmse(S_test[n], y), "RMSE_baseline": rmse(S_test[b], y),
                     "Diff": rmse(S_test[n], y) - rmse(S_test[b], y), "CI_low": lo, "CI_high": hi,
                     "Significant": bool(hi < 0 or lo > 0)})
B = pd.DataFrame(rows)
print("\n=== B. RMSE(model) - RMSE(baseline), paired block bootstrap; negative = model better ===")
print(B.round(4).to_string(index=False))
B.to_csv(os.path.join(MET, "q05c_model_minus_baseline.csv"), index=False)
 
# ---- C. event scores: AUC and validation-tuned cutoff ----
rows = []
for tn, tau in THR.items():
    o_te = y >= tau
    o_va = y_val >= tau
    for n in ORDER:
        sv, st = S_val[n], S_test[n]
        grid = np.unique(np.quantile(sv, np.linspace(0.5, 0.999, 300)))
        best_c, best_v = grid[0], -1.0
        for c in grid:
            v = csi_stats(o_va, sv >= c)[4]
            if v > best_v:
                best_c, best_v = c, v
        h, fa, pod, far, csi = csi_stats(o_te, st >= best_c)
        rows.append({"Threshold": tn, "Model": n, "AUC_test": auc(o_te, st), "Cutoff_from_val": best_c,
                     "Val_CSI": best_v, "N_test_events": int(o_te.sum()), "N_pred_events": int((st >= best_c).sum()),
                     "Hits": h, "FalseAlarms": fa, "POD": pod, "FAR": far, "CSI": csi})
C = pd.DataFrame(rows)
print("\n=== C. EVENT DETECTION (cutoff tuned on validation, applied to test) ===")
print(C.round(3).to_string(index=False))
C.to_csv(os.path.join(MET, "q05c_event_scores.csv"), index=False)
print("\nSaved q05c_*.csv to", MET)