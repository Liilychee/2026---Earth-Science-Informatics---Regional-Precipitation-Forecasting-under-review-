# ============================================================
# analysis_q03b_wet_definition.py — issue 03b: effect of the "wet" definition.
# The manuscript defines wet = observed precipitation > 0 mm (L465). For the 25-cell
# regional mean almost every sample is > 0 (3,228 of 3,939 test samples), so "wet"
# is nearly the whole test set. This script recomputes the stratified results with
#   Wet(>0 mm)  [current],  Wet(>=0.1 mm)  [proposed],  Upper tail (>=Q95, train-derived)
# NO training: reads saved prediction CSVs only. Nothing is changed in the manuscript by this
# script; it only provides the numbers needed to decide.
#
# Run from the folder that contains results/ (AutoDL: cd /root/autodl-tmp):
#     python3 code/analysis_q03b_wet_definition.py
# Output: results/metrics/q03b_wet_definition_point.csv   (N, RMSE, MAE per model x subset)
#         results/metrics/q03b_wet_definition_interval.csv (95% coverage / width, prob. models)
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
dfs = {n: pd.read_csv(os.path.join(PRED_DIR, f), parse_dates=["valid_time"]) for n, f in MODELS.items()}
ref = dfs["XGBoost"]
q95 = float(ref[ref.split == "train"]["y_true"].quantile(0.95))
test = {n: d[d.split == "test"].reset_index(drop=True) for n, d in dfs.items()}
y = test["XGBoost"]["y_true"].values
for n, d in test.items():
    assert np.allclose(d["y_true"].values, y, atol=1e-6), f"{n}: y_true mismatch"

subsets = {"All": np.ones(len(y), bool), "Wet (>0 mm)": y > 0, "Wet (>=0.1 mm)": y >= 0.1,
           f"Upper tail (>=Q95={q95:.3f})": y >= q95}
print(f"Test samples: {len(y)}")
for k, m in subsets.items():
    print(f"  {k:28s} N = {int(m.sum()):5d}  ({m.mean()*100:5.1f} % of test)")

rows, irows = [], []
for n, d in test.items():
    p = d["y_pred_mean"].values
    for k, m in subsets.items():
        e = y[m] - p[m]
        rows.append({"Model": n, "Subset": k, "N": int(m.sum()),
                     "RMSE": float(np.sqrt(np.mean(e ** 2))), "MAE": float(np.mean(np.abs(e)))})
    if not d["y_pred_std"].isna().all():
        sd = d["y_pred_std"].values
        lo, hi = p - 1.959963984540054 * sd, p + 1.959963984540054 * sd
        for k, m in subsets.items():
            irows.append({"Model": n, "Subset": k, "N": int(m.sum()),
                          "Coverage95": float(np.mean((y[m] >= lo[m]) & (y[m] <= hi[m]))),
                          "MPIW95": float(np.mean(hi[m] - lo[m]))})
pt = pd.DataFrame(rows)
it = pd.DataFrame(irows)
pt.to_csv(os.path.join(OUT, "q03b_wet_definition_point.csv"), index=False)
it.to_csv(os.path.join(OUT, "q03b_wet_definition_interval.csv"), index=False)
pd.set_option("display.width", 200)
print("\n=== RMSE by subset (test) ===")
print(pt.pivot(index="Model", columns="Subset", values="RMSE").round(4).to_string())
print("\n=== 95% interval coverage / width by subset (probabilistic models) ===")
print(it.round(4).to_string(index=False))
print("\nSaved q03b_wet_definition_point.csv and q03b_wet_definition_interval.csv to", OUT)
