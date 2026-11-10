# ============================================================
# analysis_q07b_linear_baselines.py -- issue 07 (R1 M2 "baselines limited", R4 m8 l.110 "what if a predictor like lsp were a reference"),
# zero GPU, seconds.  Adds the natural STRONGER simple reference that 07 lacked: linear models on the same inputs.
#
#   L1 ridge on all 42 model inputs (6 snapshots x 7 variables, train-only standardisation)   -> how much do non-linear models add?
#   L2 ridge on the 7 variables at the forecast origin only (last snapshot)
#   L3 OLS on tp(t) and lsp(t) at the forecast origin (AR(1) plus lsp)           [tp(t) is NOT a model input; it is what Persistence/AR(1) use]
# Ridge strength chosen on VALIDATION from [0.1, 1, 10, 100, 1000, 10000]; nothing is fitted or selected on test.
# Reported on the TEST split (3,939 windows): RMSE, MAE, bias, R2, RMSE skill vs the month x hour climatology (TRAIN means),
# RMSE on wet>=0.1 and >=Q95, AUC and validation-tuned-cutoff CSI at Q95 and 1.0 mm/h;
# paired block bootstrap (28, 2,000, seed 42): model minus linear reference for the six saved models (RMSE all, AUC Q95, AUC 1.0).
#
# Run (AutoDL):  cd /root/autodl-tmp
#   python3 code/analysis_q07b_linear_baselines.py 2>&1 | tee results/metrics/q07b_output.txt
# Outputs (results/metrics/): q07b_linear_baselines.csv, q07b_model_minus_linear.csv
# Optional env: NBOOT (default 2000)
# ============================================================
import os
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.preprocessing import StandardScaler

W, BLOCK, BSEED = 6, 28, 42
NBOOT = int(os.environ.get("NBOOT", 2000))
BASE = ['mxtpr', 'mntpr', 'lsp', 'tcc', 'v10', 'sp', 'd2m']
ALPHAS = [0.1, 1, 10, 100, 1000, 10000]
ROOT = next(r for r in ["results", "/root/autodl-tmp/results", "../results"] if os.path.isdir(r))
PRED_DIR = next(d for d in (os.path.join(ROOT, "predictions"), ROOT) if os.path.exists(os.path.join(d, "xgboost_preds.csv")))
MET = os.path.join(ROOT, "metrics"); os.makedirs(MET, exist_ok=True)
DATA = next(p for p in ["data/dublin_regional_reduced.csv", "../data/dublin_regional_reduced.csv",
                        "/root/autodl-tmp/data/dublin_regional_reduced.csv"] if os.path.exists(p))
MODELS = {"XGBoost": "xgboost_preds.csv", "Transformer": "transformer_preds.csv", "BU-LSTM": "bulstm_preds.csv",
          "BiLSTM-Attention": "bilstm_attention_preds.csv", "BU-LSTM-Attention": "proposed_model_preds.csv",
          "Probabilistic BiLSTM-Attention": "prob_bilstm_attention_preds.csv"}

df = pd.read_csv(DATA, parse_dates=["valid_time"]).sort_values("valid_time").reset_index(drop=True)
df["tp_mm"] = df["tp"] * 1000.0 if "tp" in df.columns else df["tp_mm"]
df["lsp_mm"] = df["lsp"] * 1000.0
n = len(df); a, b = int(n * .70), int(n * .85)
parts = {"train": df.iloc[:a], "val": df.iloc[a:b], "test": df.iloc[b:]}
sx = StandardScaler().fit(parts["train"][BASE])


def build(p):
    p = p.reset_index(drop=True)
    Xv = sx.transform(p[BASE])
    X = np.stack([Xv[i:i + W] for i in range(len(p) - W)]).astype(np.float64)       # (N, 6, 7)
    t = p.iloc[W:].reset_index(drop=True)
    return {"X42": X.reshape(len(X), -1), "X7": X[:, -1, :], "y": t.tp_mm.to_numpy(), "time": t.valid_time,
            "tp0": p.tp_mm.to_numpy()[W - 1:len(p) - 1], "lsp0": p.lsp_mm.to_numpy()[W - 1:len(p) - 1],
            "month": t.valid_time.dt.month.to_numpy(), "hour": t.valid_time.dt.hour.to_numpy()}


D = {k: build(v) for k, v in parts.items()}
tr, va, te = D["train"], D["val"], D["test"]
assert len(tr["y"]) == 18404 and len(te["y"]) == 3939
yt, yv, N = te["y"], va["y"], len(te["y"])
q95 = float(np.quantile(tr["y"], .95)); TH = {"Q95": q95, "1.0": 1.0}
assert abs(q95 - 0.5740) < 5e-4
clim = pd.DataFrame({"m": tr["month"], "h": tr["hour"], "y": tr["y"]}).groupby(["m", "h"]).y.mean()
ref_te = np.array([clim.loc[(m, h)] for m, h in zip(te["month"], te["hour"])])
ref_rmse = float(np.sqrt(np.mean((yt - ref_te) ** 2)))
print(f"test targets {N}; month x hour climatology RMSE {ref_rmse:.4f} (expected ~0.2731)")


def rmse(p, o): return float(np.sqrt(np.mean((p - o) ** 2)))


def fit_ridge(key):
    best = None
    for al in ALPHAS:
        m = Ridge(alpha=al).fit(tr[key], tr["y"])
        r = rmse(m.predict(va[key]), yv)
        if best is None or r < best[0]: best = (r, al, m)
    print(f"  ridge on {key}: alpha {best[1]} (validation RMSE {best[0]:.4f})")
    return best[2].predict(va[key]), best[2].predict(te[key]), best[1]


def two(d): return np.column_stack([d["tp0"], d["lsp0"]])


m3 = LinearRegression().fit(two(tr), tr["y"])
LIN = {}
v1, t1, al1 = fit_ridge("X42"); LIN["L1 ridge, 42 inputs"] = (v1, t1)
v2, t2, al2 = fit_ridge("X7"); LIN["L2 ridge, origin 7 variables"] = (v2, t2)
LIN["L3 OLS tp(t)+lsp(t)"] = (m3.predict(two(va)), m3.predict(two(te)))
print(f"  L3 coefficients: intercept {m3.intercept_:.4f}, tp(t) {m3.coef_[0]:.4f}, lsp(t) {m3.coef_[1]:.4f}")


def auc(p, pos):
    r = rankdata(p); n1 = pos.sum(); return float((r[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(p) - n1)))


def tune(pv, posv):
    cands = np.unique(np.quantile(pv, np.linspace(0.5, 0.999, 300))); best, bc = -1, cands[0]
    for c in cands:
        pb = pv >= c; h, fa, mi = (pb & posv).sum(), (pb & ~posv).sum(), (~pb & posv).sum()
        csi = h / (h + fa + mi) if (h + fa + mi) else 0
        if csi > best: best, bc = csi, c
    return bc


def metrics(name, pv, pt):
    r = {"Method": name, "RMSE": rmse(pt, yt), "MAE": float(np.mean(np.abs(pt - yt))), "Bias": float(np.mean(pt - yt)),
         "R2": float(1 - np.sum((yt - pt) ** 2) / np.sum((yt - yt.mean()) ** 2)), "Skill_vs_clim_MH": 1 - rmse(pt, yt) / ref_rmse,
         "RMSE_wet>=0.1": rmse(pt[yt >= .1], yt[yt >= .1]), "RMSE_>=Q95": rmse(pt[yt >= q95], yt[yt >= q95]),
         "Pred_max": float(pt.max()), "Std_ratio": float(pt.std() / yt.std())}
    for tn, tv in TH.items():
        pos, posv = yt >= tv, yv >= tv
        c = tune(pv, posv); pb = pt >= c
        h, fa, mi = int((pb & pos).sum()), int((pb & ~pos).sum()), int((~pb & pos).sum())
        r.update({f"AUC_{tn}": auc(pt, pos), f"POD_{tn}": h / (h + mi), f"FAR_{tn}": fa / (h + fa) if (h + fa) else np.nan,
                  f"CSI_{tn}": h / (h + fa + mi)})
    return r


S, P_te = {}, {}
for m, f in MODELS.items():
    d0 = pd.read_csv(os.path.join(PRED_DIR, f), parse_dates=["valid_time"])
    out = {}
    for sp, ref in (("val", va), ("test", te)):
        d = d0[d0.split == sp].drop_duplicates("valid_time").sort_values("valid_time").reset_index(drop=True)
        assert len(d) == len(ref["y"]) and (d.valid_time.to_numpy() == ref["time"].to_numpy()).all(), (m, sp)
        assert np.allclose(d.y_true.to_numpy(), ref["y"], atol=1e-6), (m, sp)
        out[sp] = d.y_pred_mean.to_numpy()
    S[m] = out; P_te[m] = out["test"]
rows = [metrics(k, v[0], v[1]) for k, v in LIN.items()] + [metrics(k, v["val"], v["test"]) for k, v in S.items()]
rows.append(metrics("Persistence", va["tp0"], te["tp0"]))
R = pd.DataFrame(rows); R.to_csv(os.path.join(MET, "q07b_linear_baselines.csv"), index=False)

rng = np.random.default_rng(BSEED)
st = rng.integers(0, N, size=(NBOOT, int(np.ceil(N / BLOCK))))
IDX = ((st[:, :, None] + np.arange(BLOCK)[None, None, :]) % N).reshape(NBOOT, -1)[:, :N]
b_rmse = lambda p: np.sqrt(((yt - p) ** 2)[IDX].mean(1))


def b_auc(p, pos):
    r = rankdata(p[IDX], axis=1); pb = pos[IDX]; n1 = pb.sum(1)
    return ((r * pb).sum(1) - n1 * (n1 + 1) / 2) / (n1 * (N - n1))


prow = []
for lname, (lv, lt) in LIN.items():
    for m in MODELS:
        for met, f, g in (("RMSE", lambda p: rmse(p, yt), b_rmse),
                          ("AUC_Q95", lambda p: auc(p, yt >= q95), lambda p: b_auc(p, yt >= q95)),
                          ("AUC_1.0", lambda p: auc(p, yt >= 1.0), lambda p: b_auc(p, yt >= 1.0))):
            d = g(P_te[m]) - g(lt)
            prow.append({"Model": m, "Reference": lname, "Metric": met, "Model_minus_ref": f(P_te[m]) - f(lt),
                         "CI_low": float(np.percentile(d, 2.5)), "CI_high": float(np.percentile(d, 97.5)),
                         "CI_excludes_0": bool(np.percentile(d, 2.5) > 0 or np.percentile(d, 97.5) < 0)})
PP = pd.DataFrame(prow); PP.to_csv(os.path.join(MET, "q07b_model_minus_linear.csv"), index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
print("\n===== test metrics (RMSE negative difference = better) =====")
print(R.round(4).to_string(index=False))
print(f"\n===== model minus linear reference (RMSE: negative = model better; AUC: positive = model better); block {BLOCK}, {NBOOT} reps =====")
print(PP.round(4).to_string(index=False))
print("\nSaved q07b_*.csv to", MET)
