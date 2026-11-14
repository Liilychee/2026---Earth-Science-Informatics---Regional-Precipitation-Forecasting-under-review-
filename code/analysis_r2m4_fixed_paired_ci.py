# ============================================================
# analysis_r2m4_fixed_paired_ci.py -- R2 M4 (event detection vs persistence), zero-training, read-only on inputs
#
# Question: under the FIXED mean-based rule (predicted mean >= tau), are the learning models worse than persistence?
#   thresholds : wet>=0.1, Q90, Q95, Q97.5 (training quantiles of the 18,404 windowed targets), 0.5 and 1.0 mm/h
#   scores     : hits, false alarms, misses, POD, FAR (NaN when no event is forecast), CSI (0 when hits+FA+misses=0)
#                for 6 learning models + Persistence + AR(1) (train fit) + month x hour climatology (train)
#   paired     : CSI(model) - CSI(Persistence), circular block bootstrap (block 28, 2,000, seed 42), one index set
#                shared by all models and thresholds (same construction as analysis_q05e_event_paired_ci.py)
#   p values   : two-sided percentile-inversion p = 2 (min(#d>=0, #d<=0) + 1) / (B + 1); Holm over two families:
#                "high" = Q95, Q97.5, 0.5, 1.0 (24 tests; chosen after inspection, report as such) and "all" (36 tests)
# Formalises the scratch check events_r2m4.py (md5 fa9a3558...), whose 36 fixed-rule cells this script reproduces.
# Inputs : results/<model>_preds.csv (split, valid_time, y_true, y_pred_mean); never modified.
# Run    : python3 code/analysis_r2m4_fixed_paired_ci.py 2>&1 | tee results/metrics/r2m4_fixed_output.txt
# Outputs (results/metrics/, new files only): r2m4_fixed_event_scores.csv, r2m4_fixed_event_paired.csv
# Optional env: NBOOT (default 2000), BSEED (default 42).
# ============================================================
import os
import numpy as np
import pandas as pd

ROOT = next(r for r in ["results", "/root/autodl-tmp/results", "../results"] if os.path.isdir(r))
PRED = next(d for d in (os.path.join(ROOT, "predictions"), ROOT) if os.path.exists(os.path.join(d, "xgboost_preds.csv")))
MET = os.path.join(ROOT, "metrics"); os.makedirs(MET, exist_ok=True)
OUT_S, OUT_P = os.path.join(MET, "r2m4_fixed_event_scores.csv"), os.path.join(MET, "r2m4_fixed_event_paired.csv")
for f in (OUT_S, OUT_P):
    assert not os.path.exists(f), f"{f} exists; refusing to overwrite"
MODELS = {"XGBoost": "xgboost_preds.csv", "Transformer": "transformer_preds.csv", "BU-LSTM": "bulstm_preds.csv",
          "BiLSTM-Attention": "bilstm_attention_preds.csv", "BU-LSTM-Attention": "proposed_model_preds.csv",
          "Probabilistic BiLSTM-Attention": "prob_bilstm_attention_preds.csv"}
PERS = "persistence_preds.csv"
BLOCK, NBOOT, BSEED = 28, int(os.environ.get("NBOOT", 2000)), int(os.environ.get("BSEED", 42))
HIGH = ["Q95", "Q97.5", "0.5 mm", "1.0 mm"]

# ---------------- load and align ----------------
raw = {m: pd.read_csv(os.path.join(PRED, f), parse_dates=["valid_time"]) for m, f in {**MODELS, "Persistence": PERS}.items()}
ref = raw["XGBoost"]
sp = {s: ref[ref.split == s].reset_index(drop=True) for s in ("train", "test")}
for m, d in raw.items():
    for s in ("train", "test"):
        t = d[d.split == s].reset_index(drop=True)
        assert len(t) == len(sp[s]), (m, s, len(t))
        assert (t.valid_time.to_numpy() == sp[s].valid_time.to_numpy()).all(), (m, s, "valid_time")
        dmax = float(np.abs(t.y_true.to_numpy() - sp[s].y_true.to_numpy()).max())
        assert dmax < 1e-6, (m, s, dmax)
        if dmax > 0:
            print(f"note: {m} {s} y_true differs from XGBoost file by at most {dmax:.2e} mm/h; XGBoost y_true is used")
ytr, yt = sp["train"].y_true.to_numpy(), sp["test"].y_true.to_numpy()
N = len(yt)
assert len(ytr) == 18404 and N == 3939, (len(ytr), N)
P = {m: raw[m][raw[m].split == "test"].y_pred_mean.to_numpy() for m in raw}
# reference forecasts from the persistence file (its y_pred_mean is y at the previous 6-hourly step)
lag_tr = raw["Persistence"][raw["Persistence"].split == "train"].y_pred_mean.to_numpy()
b1, a1 = np.polyfit(lag_tr, ytr, 1)
P["AR(1) (train fit)"] = a1 + b1 * P["Persistence"]
vt_tr, vt_te = sp["train"].valid_time, sp["test"].valid_time
clim = pd.Series(ytr).groupby([vt_tr.dt.month.to_numpy(), vt_tr.dt.hour.to_numpy()]).mean()
P["Climatology (month x hour)"] = np.array([clim.loc[(mo, h)] for mo, h in zip(vt_te.dt.month, vt_te.dt.hour)])
print(f"AR(1): y = {a1:.4f} + {b1:.4f} * y_lag")

thr = {"wet>=0.1": 0.1, "Q90": float(np.quantile(ytr, .90)), "Q95": float(np.quantile(ytr, .95)),
       "Q97.5": float(np.quantile(ytr, .975)), "0.5 mm": 0.5, "1.0 mm": 1.0}
assert abs(thr["Q95"] - 0.5740) < 5e-4
ypers = raw["Persistence"][raw["Persistence"].split == "test"].y_true.to_numpy()
for tn, tv in thr.items():  # the small target differences must not change any event label
    assert ((yt >= tv) == (ypers >= tv)).all(), tn
print("thresholds:", {k: round(v, 4) for k, v in thr.items()},
      "| test events:", {k: int((yt >= v).sum()) for k, v in thr.items()})

# ---------------- bootstrap index (identical construction to q05e) ----------------
rng = np.random.default_rng(BSEED)
nblk = int(np.ceil(N / BLOCK))
st = rng.integers(0, N, size=(NBOOT, nblk))
IDX = ((st[:, :, None] + np.arange(BLOCK)[None, None, :]) % N).reshape(NBOOT, -1)[:, :N]


def counts(pb, pos, axis=None):
    return (pb & pos).sum(axis), (pb & ~pos).sum(axis), (~pb & pos).sum(axis)


def csi_boot(p, pos, c):
    h, fa, mi = counts((p >= c)[IDX], pos[IDX], axis=1)
    return h / np.maximum(h + fa + mi, 1)


# ---------------- scores ----------------
rows, boot = [], {}
for tn, tv in thr.items():
    pos = yt >= tv
    for m, p in P.items():
        pb = p >= tv
        h, fa, mi = (int(v) for v in counts(pb, pos))
        rows.append({"Threshold": tn, "thr_mm_h": tv, "Model": m, "N_events_test": int(pos.sum()),
                     "Forecast_events": int(pb.sum()), "Hits": h, "False_alarms": fa, "Misses": mi,
                     "POD": h / (h + mi), "FAR": fa / (h + fa) if (h + fa) else np.nan,
                     "CSI": h / (h + fa + mi) if (h + fa + mi) else 0.0,
                     "Frequency_bias": int(pb.sum()) / int(pos.sum())})
        if m in MODELS or m == "Persistence":
            boot[(tn, m)] = csi_boot(p, pos, tv)
sc = pd.DataFrame(rows)

# optional cross-check against the earlier fixed-rule table
chk = os.path.join(MET, "revision_event_detection.csv")
if os.path.exists(chk):
    rv = pd.read_csv(chk)
    name = {"0.1 mm": "wet>=0.1", "BU-LSTM-Attention (proposed)": "BU-LSTM-Attention"}
    rv["Threshold"] = rv.Threshold.replace(name); rv["Model"] = rv.Model.replace(name)
    j = sc.merge(rv, on=["Threshold", "Model"], suffixes=("", "_rv"))
    assert len(j) == 48, len(j)
    assert (j.Hits == j.Hits_rv).all() and (j.Forecast_events == j.N_pred_events).all() and np.allclose(j.CSI, j.CSI_rv)
    print(f"cross-check: {len(j)} rows identical to revision_event_detection.csv (hits, forecast events, CSI)")

# ---------------- paired differences vs persistence + Holm ----------------
pr = []
for tn in thr:
    s = sc[sc.Threshold == tn].set_index("Model")
    for m in MODELS:
        d = boot[(tn, m)] - boot[(tn, "Persistence")]
        ge, le = int((d >= 0).sum()), int((d <= 0).sum())
        lo, hi = np.percentile(d, [2.5, 97.5])
        pr.append({"Threshold": tn, "Model": m, "Reference": "Persistence",
                   "CSI_model": s.loc[m, "CSI"], "CSI_reference": s.loc["Persistence", "CSI"],
                   "Forecast_events_model": int(s.loc[m, "Forecast_events"]),
                   "dCSI": s.loc[m, "CSI"] - s.loc["Persistence", "CSI"], "CI_low": lo, "CI_high": hi,
                   "CI_excludes_0": bool(lo > 0 or hi < 0), "n_boot_ge0": ge, "n_boot_le0": le,
                   "p_two_sided": min(1.0, 2 * (min(ge, le) + 1) / (NBOOT + 1)), "In_high_family": tn in HIGH})
pp = pd.DataFrame(pr)


def holm(p):
    o = np.argsort(p, kind="stable"); k = len(p); adj = np.empty(k)
    adj[o] = np.minimum(1, np.maximum.accumulate((k - np.arange(k)) * p[o]))
    return adj


pp["p_holm_all36"] = holm(pp.p_two_sided.to_numpy())
pp["p_holm_high24"] = np.nan
hm = pp.In_high_family.to_numpy()
pp.loc[hm, "p_holm_high24"] = holm(pp.loc[hm, "p_two_sided"].to_numpy())

sc.to_csv(OUT_S, index=False, float_format="%.10g")
pp.to_csv(OUT_P, index=False, float_format="%.10g")
pd.set_option("display.width", 250)
print(f"\n===== fixed rule (predicted mean >= tau), test N={N} =====")
print(sc.round(4).to_string(index=False))
print(f"\n===== CSI(model) - CSI(Persistence), circular block {BLOCK}, {NBOOT} reps, seed {BSEED} =====")
print(pp.drop(columns=["Reference"]).round(4).to_string(index=False))
h24 = pp[hm]
print(f"\nhigh family (24): CIs excluding 0 {int(h24.CI_excludes_0.sum())}/24; Holm p<0.05 {int((h24.p_holm_high24 < .05).sum())}/24;"
      f" max Holm p {h24.p_holm_high24.max():.4f}; p floor {2 / (NBOOT + 1):.4f}")
print(f"all (36): Holm p<0.05 {int((pp.p_holm_all36 < .05).sum())}/36; high-threshold tests failing under the 36 family:",
      h24[h24.p_holm_all36 >= .05][["Threshold", "Model"]].values.tolist())
print("Note: models with zero forecast events have CSI = 0 by definition; their dCSI equals -CSI(Persistence).")
print("Saved", OUT_S, "and", OUT_P)
