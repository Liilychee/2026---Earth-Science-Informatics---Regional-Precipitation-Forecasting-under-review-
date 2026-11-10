# ============================================================
# analysis_q05d_counts_and_tail_table.py -- issue 05 (R1 M1, R4 l.28-29), zero-training, seconds
#
# (1) R1 M1 premise: "the number of events > 1 mm in the TRAINING data is likely very limited".
#     -> event counts per split (train/val/test) at wet>=0.1, Q90, Q95, Q97.5 (train quantiles) and 1.0 mm/h.
# (2) R4 l.28-29: "a statement is missing that all the scores got worse for heavy rainfall".
#     -> for every saved model + baselines: RMSE, MAE, bias, R2(in subset) and skill vs month x hour
#        climatology on all / wet>=0.1 / upper tail (>=train Q95) of the test split.
# (3) evidence 05-E14: Spearman of same-hour tp with mxtpr, mntpr, lsp (all stamps and tp>=0.1).
#
# Run (AutoDL):  cd /root/autodl-tmp
#   python3 code/analysis_q05d_counts_and_tail_table.py 2>&1 | tee results/metrics/q05d_output.txt
# Outputs (results/metrics/): q05d_event_counts.csv, q05d_tail_table.csv, q05d_same_hour_spearman.csv
# ============================================================
import os
import numpy as np
import pandas as pd

ROOT = next(r for r in ["results", "/root/autodl-tmp/results", "../results"] if os.path.isdir(r))
PRED_DIR = next(d for d in (os.path.join(ROOT, "predictions"), ROOT) if os.path.exists(os.path.join(d, "xgboost_preds.csv")))
MET = os.path.join(ROOT, "metrics"); os.makedirs(MET, exist_ok=True)
DATA = next(p for p in ["data/dublin_regional_reduced.csv", "../data/dublin_regional_reduced.csv",
                        "/root/autodl-tmp/data/dublin_regional_reduced.csv",
                        "data/dublin_regional_2004_2021.csv"] if os.path.exists(p))
MODELS = {"XGBoost": "xgboost_preds.csv", "Transformer": "transformer_preds.csv", "BU-LSTM": "bulstm_preds.csv",
          "BiLSTM-Attention": "bilstm_attention_preds.csv", "BU-LSTM-Attention (proposed)": "proposed_model_preds.csv",
          "Probabilistic BiLSTM-Attention": "prob_bilstm_attention_preds.csv"}
W = 6
df = pd.read_csv(DATA, parse_dates=["valid_time"]).sort_values("valid_time").reset_index(drop=True)
df["tp_mm"] = df["tp"] * 1000.0 if "tp" in df.columns else df["tp_mm"]
df["lsp_mm"] = df["lsp"] * 1000.0
n = len(df); a, b = int(n * .70), int(n * .85)
fr = {}
for k, (i, j) in {"train": (0, a), "val": (a, b), "test": (b, n)}.items():
    p = df.iloc[i:j].reset_index(drop=True)
    t = p.iloc[W:].copy()
    t["y_lag"] = p.iloc[W - 1:len(p) - 1]["tp_mm"].to_numpy()
    t["y"] = t["tp_mm"]; t["month"] = t.valid_time.dt.month; t["hour"] = t.valid_time.dt.hour
    fr[k] = t.reset_index(drop=True)
tr, va, te = fr["train"], fr["val"], fr["test"]
print(f"Data {DATA}; windows train {len(tr)} val {len(va)} test {len(te)}")
q = {"wet>=0.1": 0.1, "Q90": float(tr.y.quantile(.90)), "Q95": float(tr.y.quantile(.95)),
     "Q97.5": float(tr.y.quantile(.975)), ">=1.0": 1.0}
print("Train-derived thresholds (mm/h):", {k: round(v, 4) for k, v in q.items()})
assert abs(q["Q95"] - 0.5740) < 5e-4, "train Q95 != 0.5740"

# (1) counts
rows = []
for name, thr in q.items():
    r = {"Threshold": name, "mm_per_h": thr}
    for sp, f in fr.items():
        c = int((f.y >= thr).sum()); r[f"{sp}_N"] = c; r[f"{sp}_pct"] = 100 * c / len(f)
    rows.append(r)
cnt = pd.DataFrame(rows); cnt.to_csv(os.path.join(MET, "q05d_event_counts.csv"), index=False)
print("\n===== (1) event counts per split =====\n", cnt.round(3).to_string(index=False))

# (2) tail table
y = te.y.to_numpy(); N = len(te)
P = {}
for m, f in MODELS.items():
    d = pd.read_csv(os.path.join(PRED_DIR, f), parse_dates=["valid_time"])
    d = d[d.split == "test"].drop_duplicates("valid_time").sort_values("valid_time").reset_index(drop=True)
    assert len(d) == N and (d.valid_time.to_numpy() == te.valid_time.to_numpy()).all(), m
    assert np.allclose(d.y_true.to_numpy(), y, atol=1e-6), m
    P[m] = d.y_pred_mean.to_numpy()
P["Persistence"] = te.y_lag.to_numpy()
clim = tr.groupby(["month", "hour"]).y.mean()
ref = np.array([clim.loc[(m, h)] for m, h in zip(te.month, te.hour)])
P["Climatology (month x hour)"] = ref
masks = {"all": np.ones(N, bool), "wet>=0.1": y >= 0.1, "upper tail (>=train Q95)": y >= q["Q95"]}
rows = []
for m, p in P.items():
    for s, mk in masks.items():
        o, pp = y[mk], p[mk]
        rm = float(np.sqrt(np.mean((o - pp) ** 2))); rr = float(np.sqrt(np.mean((o - ref[mk]) ** 2)))
        sst = float(np.sum((o - o.mean()) ** 2))
        rows.append({"Model": m, "Subset": s, "N": int(mk.sum()), "RMSE": rm, "MAE": float(np.mean(np.abs(o - pp))),
                     "Bias_pred_minus_obs": float(np.mean(pp - o)), "R2_in_subset": 1 - float(np.sum((o - pp) ** 2)) / sst,
                     "Skill_vs_clim": 1 - rm / rr})
tt = pd.DataFrame(rows); tt.to_csv(os.path.join(MET, "q05d_tail_table.csv"), index=False)
print("\n===== (2) all / wet / upper-tail, test split =====")
print(tt.round(4).to_string(index=False))
print("\nNOTE: RMSE and MAE rise from 'all' to 'upper tail' for every model if the columns above show it; "
      "skill vs climatology and R2_in_subset are reported separately and need not move the same way.")

# (3) same-hour Spearman
rows = []
for lab, g in (("all stamps", df), ("tp>=0.1 mm", df[df.tp_mm >= 0.1])):
    for v, col in (("mxtpr", df.mxtpr * 3600), ("mntpr", df.mntpr * 3600), ("lsp", df.lsp_mm)):
        c = col.loc[g.index]
        rows.append({"Subset": lab, "N": len(g), "Variable": v,
                     "Spearman_with_tp_same_hour": float(pd.Series(g.tp_mm.to_numpy()).corr(pd.Series(c.to_numpy()), method="spearman"))})
sp = pd.DataFrame(rows); sp.to_csv(os.path.join(MET, "q05d_same_hour_spearman.csv"), index=False)
print("\n===== (3) same-hour Spearman with tp =====\n", sp.round(3).to_string(index=False))
print("\nSaved q05d_*.csv to", MET)
