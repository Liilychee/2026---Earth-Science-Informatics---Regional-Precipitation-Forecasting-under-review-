# ============================================================
# analysis_q03c_wet01_bootstrap.py — issue 03c: paired block bootstrap with the NEW wet definition
# Same method as notebook Step 17B (circular block bootstrap, block = 28 samples = 7 days,
# 10,000 replicates, seed 42, regime mask applied AFTER block resampling, percentile 95% CI),
# so the regimes "All", "Wet (>0 mm)" and "Heavy_Q95" must REPRODUCE the existing results.
# New regime: "Wet (>=0.1 mm)". Pairs:
#     BiLSTM-Attention - XGBoost        (as in the paper)
#     BU-LSTM-Attention (proposed) - XGBoost
# Delta RMSE < 0 : first model better;  Delta RMSE > 0 : XGBoost better.
# NO training; reads saved prediction CSVs only.
#
# Run from the folder containing results/ (AutoDL: cd /root/autodl-tmp):
#     python3 code/analysis_q03c_wet01_bootstrap.py
# Output: results/metrics/q03c_block_bootstrap_wet01.csv
# ============================================================
import os
import numpy as np
import pandas as pd

ROOTS = ["results", "/root/autodl-tmp/results", "../results"]
ROOT = next(r for r in ROOTS if os.path.isdir(r))
PRED_DIR = next(d for d in (os.path.join(ROOT, "predictions"), ROOT)
                if os.path.exists(os.path.join(d, "xgboost_preds.csv")))
OUT = os.path.join(ROOT, "metrics")
os.makedirs(OUT, exist_ok=True)

BLOCK_LENGTH, N_BOOT, SEED = 28, 10000, 42


def load(f):
    d = pd.read_csv(os.path.join(PRED_DIR, f), parse_dates=["valid_time"])
    return d


xgb_all = load("xgboost_preds.csv")
Q95 = float(np.quantile(xgb_all[xgb_all.split == "train"]["y_true"], 0.95))
print(f"Train-only Q95 = {Q95:.6f} mm/h")


def test_of(d):
    return d[d.split == "test"].sort_values("valid_time").reset_index(drop=True)


base = test_of(xgb_all)
y = base["y_true"].to_numpy()
pred = {"XGBoost": base["y_pred_mean"].to_numpy()}
for name, f in {"BiLSTM-Attention": "bilstm_attention_preds.csv",
                "BU-LSTM-Attention (proposed)": "proposed_model_preds.csv"}.items():
    t = test_of(load(f))
    assert (t["valid_time"].values == base["valid_time"].values).all(), f"{name}: times differ"
    assert np.allclose(t["y_true"].to_numpy(), y, atol=1e-6), f"{name}: y_true differs"
    pred[name] = t["y_pred_mean"].to_numpy()
N = len(y)
print("Aligned test N =", N)


def rmse(a, b):
    return float(np.sqrt(np.mean((a - b) ** 2)))


def get_mask(yv, regime):
    if regime == "All":
        return np.ones(len(yv), bool)
    if regime == "Wet (>0 mm)":
        return yv > 0
    if regime == "Wet (>=0.1 mm)":
        return yv >= 0.1
    if regime == "Heavy_Q95":
        return yv >= Q95
    raise ValueError(regime)


def circular_block_indices(n, block_length, rng):
    n_blocks = int(np.ceil(n / block_length))
    starts = rng.integers(0, n, size=n_blocks)
    idx = []
    for s in starts:
        idx.extend((s + np.arange(block_length)) % n)
    return np.asarray(idx[:n])


def paired_block_bootstrap(yv, pa, pb, regime):
    rng = np.random.default_rng(SEED)
    m0 = get_mask(yv, regime)
    ra, rb = rmse(yv[m0], pa[m0]), rmse(yv[m0], pb[m0])
    diffs, sizes = [], []
    for _ in range(N_BOOT):
        idx = circular_block_indices(len(yv), BLOCK_LENGTH, rng)
        yb, ab, bb = yv[idx], pa[idx], pb[idx]
        m = get_mask(yb, regime)
        if m.sum() < 2:
            continue
        sizes.append(int(m.sum()))
        diffs.append(rmse(yb[m], ab[m]) - rmse(yb[m], bb[m]))
    diffs = np.asarray(diffs)
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return {"Regime": regime, "Observed_N": int(m0.sum()), "Block_Length": BLOCK_LENGTH,
            "Valid_Bootstrap_Runs": len(diffs), "Mean_Bootstrap_Regime_N": float(np.mean(sizes)),
            "RMSE_model": ra, "RMSE_XGBoost": rb, "Delta_RMSE_model_minus_XGB": ra - rb,
            "CI95_low": float(lo), "CI95_high": float(hi),
            "P_model_better": float(np.mean(diffs < 0)), "P_XGBoost_better": float(np.mean(diffs > 0))}


REGIMES = ["All", "Wet (>0 mm)", "Wet (>=0.1 mm)", "Heavy_Q95"]
rows = []
for model in ["BiLSTM-Attention", "BU-LSTM-Attention (proposed)"]:
    for reg in REGIMES:
        r = paired_block_bootstrap(y, pred[model], pred["XGBoost"], reg)
        r["Model"] = model
        if r["CI95_high"] < 0:
            r["Conclusion"] = f"{model} robustly lower RMSE"
        elif r["CI95_low"] > 0:
            r["Conclusion"] = "XGBoost robustly lower RMSE"
        else:
            r["Conclusion"] = "CI includes zero: not clearly distinguishable"
        rows.append(r)
        print(f"{model:30s} {reg:15s} N={r['Observed_N']:5d}  dRMSE={r['Delta_RMSE_model_minus_XGB']:+.4f} "
              f"CI[{r['CI95_low']:+.4f}, {r['CI95_high']:+.4f}]  -> {r['Conclusion']}")
res = pd.DataFrame(rows)
cols = ["Model", "Regime", "Observed_N", "RMSE_model", "RMSE_XGBoost", "Delta_RMSE_model_minus_XGB",
        "CI95_low", "CI95_high", "P_model_better", "P_XGBoost_better", "Conclusion",
        "Block_Length", "Valid_Bootstrap_Runs", "Mean_Bootstrap_Regime_N"]
res[cols].to_csv(os.path.join(OUT, "q03c_block_bootstrap_wet01.csv"), index=False)

# reproducibility check against the paper's saved bootstrap (BiLSTM-Attention vs XGBoost)
old = os.path.join(OUT, "final_block_bootstrap_bilstm_vs_xgb.csv")
if os.path.exists(old):
    o = pd.read_csv(old).set_index("Regime")
    n = res[res.Model == "BiLSTM-Attention"].set_index("Regime")
    for a, b in (("All", "All"), ("Wet", "Wet (>0 mm)"), ("Heavy_Q95", "Heavy_Q95")):
        print(f"REPRO {a:10s}: old [{o.loc[a, 'CI95_low']:+.6f}, {o.loc[a, 'CI95_high']:+.6f}]  "
              f"new [{n.loc[b, 'CI95_low']:+.6f}, {n.loc[b, 'CI95_high']:+.6f}]  "
              f"{'OK' if np.allclose([o.loc[a,'CI95_low'], o.loc[a,'CI95_high']], [n.loc[b,'CI95_low'], n.loc[b,'CI95_high']], atol=1e-9) else 'DIFFERENT'}")
else:
    print("(saved paper bootstrap CSV not found: reproducibility check skipped)")
print("Saved", os.path.join(OUT, "q03c_block_bootstrap_wet01.csv"))
