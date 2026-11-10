# ============================================================
# analysis_q05e_event_paired_ci.py -- issue 05 (R2 M4, R2 minor 3, R1 M1), zero-training
#
# R2 M4: "event-detection performance sometimes underperforming persistence ... stronger emphasis on event-based metrics".
# Adds what 05 lacks: paired significance for event metrics, for ALL thresholds and ALL baselines.
#   thresholds : wet>=0.1, Q90, Q95, Q97.5 (train quantiles), 1.0 mm/h
#   methods    : 6 learned models + Persistence + AR(1) (fit on TRAIN) + climatology (month x hour, TRAIN)
#   metrics    : AUC of the predicted mean as a score; POD/FAR/CSI at a cutoff chosen on VALIDATION (max CSI) and
#                applied to TEST (the cutoff is never chosen on test)
#   paired differences (model minus baseline) with circular block bootstrap (block 28, 2,000, seed 42).
# Needs val AND test rows in results/predictions/*_preds.csv.
#
# Run (AutoDL):  cd /root/autodl-tmp
#   python3 code/analysis_q05e_event_paired_ci.py 2>&1 | tee results/metrics/q05e_output.txt
# Outputs (results/metrics/): q05e_event_scores.csv, q05e_event_paired.csv
# ============================================================
import os
import numpy as np
import pandas as pd
from scipy.stats import rankdata

ROOT = next(r for r in ["results", "/root/autodl-tmp/results", "../results"] if os.path.isdir(r))
PRED_DIR = next(d for d in (os.path.join(ROOT, "predictions"), ROOT) if os.path.exists(os.path.join(d, "xgboost_preds.csv")))
MET = os.path.join(ROOT, "metrics"); os.makedirs(MET, exist_ok=True)
DATA = next(p for p in ["data/dublin_regional_reduced.csv", "../data/dublin_regional_reduced.csv",
                        "/root/autodl-tmp/data/dublin_regional_reduced.csv",
                        "data/dublin_regional_2004_2021.csv"] if os.path.exists(p))
MODELS = {"XGBoost": "xgboost_preds.csv", "Transformer": "transformer_preds.csv", "BU-LSTM": "bulstm_preds.csv",
          "BiLSTM-Attention": "bilstm_attention_preds.csv", "BU-LSTM-Attention (proposed)": "proposed_model_preds.csv",
          "Probabilistic BiLSTM-Attention": "prob_bilstm_attention_preds.csv"}
W, BLOCK, NBOOT, SEED = 6, 28, 2000, 42
df = pd.read_csv(DATA, parse_dates=["valid_time"]).sort_values("valid_time").reset_index(drop=True)
df["tp_mm"] = df["tp"] * 1000.0 if "tp" in df.columns else df["tp_mm"]
n = len(df); a, b = int(n * .70), int(n * .85)
fr = {}
for k, (i, j) in {"train": (0, a), "val": (a, b), "test": (b, n)}.items():
    p = df.iloc[i:j].reset_index(drop=True)
    t = p.iloc[W:].copy()
    t["y_lag"] = p.iloc[W - 1:len(p) - 1]["tp_mm"].to_numpy()
    t["y"] = t["tp_mm"]; t["month"] = t.valid_time.dt.month; t["hour"] = t.valid_time.dt.hour
    fr[k] = t.reset_index(drop=True)
tr, va, te = fr["train"], fr["val"], fr["test"]
thr = {"wet>=0.1": 0.1, "Q90": float(tr.y.quantile(.90)), "Q95": float(tr.y.quantile(.95)),
       "Q97.5": float(tr.y.quantile(.975)), "1.0": 1.0}
print("thresholds:", {k: round(v, 4) for k, v in thr.items()})

S = {"val": {}, "test": {}}
for m, f in MODELS.items():
    d0 = pd.read_csv(os.path.join(PRED_DIR, f), parse_dates=["valid_time"])
    assert (d0.split == "val").any(), f"{f} has no validation rows"
    for sp, ref in (("val", va), ("test", te)):
        d = d0[d0.split == sp].drop_duplicates("valid_time").sort_values("valid_time").reset_index(drop=True)
        assert len(d) == len(ref) and (d.valid_time.to_numpy() == ref.valid_time.to_numpy()).all(), (m, sp)
        assert np.allclose(d.y_true.to_numpy(), ref.y.to_numpy(), atol=1e-6), (m, sp)
        S[sp][m] = d.y_pred_mean.to_numpy()
bb, aa = np.polyfit(tr.y_lag, tr.y, 1)
clim = tr.groupby(["month", "hour"]).y.mean()
for sp, ref in (("val", va), ("test", te)):
    S[sp]["Persistence"] = ref.y_lag.to_numpy()
    S[sp]["AR(1) (train fit)"] = aa + bb * ref.y_lag.to_numpy()
    S[sp]["Climatology (month x hour)"] = np.array([clim.loc[(m, h)] for m, h in zip(ref.month, ref.hour)])
print(f"AR(1): y = {aa:.4f} + {bb:.4f} * y_lag")
names = list(S["test"])
N = len(te); yt, yv = te.y.to_numpy(), va.y.to_numpy()

rng = np.random.default_rng(SEED)
nblk = int(np.ceil(N / BLOCK))
st = rng.integers(0, N, size=(NBOOT, nblk))
IDX = ((st[:, :, None] + np.arange(BLOCK)[None, None, :]) % N).reshape(NBOOT, -1)[:, :N]


def auc(p, pos):
    r = rankdata(p); n1 = pos.sum(); n0 = len(p) - n1
    return (r[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def auc_boot(p, pos):
    r = rankdata(p[IDX], axis=1); pb = pos[IDX]
    n1 = pb.sum(1); n0 = N - n1
    return ((r * pb).sum(1) - n1 * (n1 + 1) / 2) / (n1 * n0)


def tune(pv, posv):
    cands = np.unique(np.quantile(pv, np.linspace(0.5, 0.999, 300)))
    best, bc = -1, cands[0]
    for c in cands:
        pb = pv >= c
        h = (pb & posv).sum(); fa = (pb & ~posv).sum(); mi = (~pb & posv).sum()
        csi = h / (h + fa + mi) if (h + fa + mi) else 0
        if csi > best: best, bc = csi, c
    return bc


def csi_boot(p, pos, c):
    pb = (p >= c); X = pb[IDX]; Y = pos[IDX]
    h = (X & Y).sum(1); fa = (X & ~Y).sum(1); mi = (~X & Y).sum(1)
    return h / np.maximum(h + fa + mi, 1)


rows, store = [], {}
for tn, tv in thr.items():
    pos, posv = yt >= tv, yv >= tv
    if pos.sum() < 10 or posv.sum() < 10:
        print(f"skip {tn}: too few events (test {pos.sum()}, val {posv.sum()})"); continue
    for m in names:
        c = tune(S["val"][m], posv)
        pb = S["test"][m] >= c
        h, fa, mi = int((pb & pos).sum()), int((pb & ~pos).sum()), int((~pb & pos).sum())
        rows.append({"Threshold": tn, "thr_mm": tv, "Model": m, "N_events_test": int(pos.sum()),
                     "AUC": auc(S["test"][m], pos), "cutoff_from_val": float(c), "Forecast_events": int(pb.sum()),
                     "Hits": h, "POD": h / (h + mi), "FAR": fa / (h + fa) if (h + fa) else np.nan,
                     "CSI": h / (h + fa + mi)})
        store[(tn, m)] = (auc_boot(S["test"][m], pos), csi_boot(S["test"][m], pos, c))
sc = pd.DataFrame(rows); sc.to_csv(os.path.join(MET, "q05e_event_scores.csv"), index=False)

learned = list(MODELS)
refs = ["Persistence", "AR(1) (train fit)", "Climatology (month x hour)"]
pr = []
for tn in thr:
    if (tn, names[0]) not in store: continue
    s = sc[sc.Threshold == tn].set_index("Model")
    pairs = [(m, r) for m in learned for r in refs] + [("BU-LSTM-Attention (proposed)", "XGBoost")]
    for m, r in pairs:
        for k, lab in ((0, "AUC"), (1, "CSI")):
            d = store[(tn, m)][k] - store[(tn, r)][k]
            pt = s.loc[m, lab] - s.loc[r, lab]
            pr.append({"Threshold": tn, "Metric": lab, "A": m, "B": r, "A_minus_B": pt,
                       "CI_low": float(np.percentile(d, 2.5)), "CI_high": float(np.percentile(d, 97.5)),
                       "CI_excludes_0": bool(np.percentile(d, 2.5) > 0 or np.percentile(d, 97.5) < 0)})
pp = pd.DataFrame(pr); pp.to_csv(os.path.join(MET, "q05e_event_paired.csv"), index=False)
pd.set_option("display.width", 250)
print("\n===== event scores (test; cutoff from validation) =====")
print(sc.round(3).to_string(index=False))
print(f"\n===== paired differences, block {BLOCK}, {NBOOT} reps, seed {SEED} =====")
print(pp.round(3).to_string(index=False))
print("\nSaved q05e_*.csv to", MET)
