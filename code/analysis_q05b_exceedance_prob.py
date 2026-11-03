# ============================================================
# analysis_q05b_exceedance_prob.py — issue 05b (R1 M1: "probabilistic models failed to identify positive
# cases at the 1.0 mm threshold"; R2 M4). NO training: reads the saved prediction CSVs only.
#
# Two fairer ways to test whether the models carry information about the upper tail:
#   A. Exceedance PROBABILITIES from the Gaussian head:  p = 1 - Phi((tau - mu) / sigma)
#      (probabilistic models only: those with a y_pred_std column). Evaluated on the test set with
#        Brier score and Brier skill score (reference: the TRAINING base rate), ROC-AUC of p and of mu,
#        and a reliability table by bins of p.
#   B. TUNED DECISION CUTOFF: the rule "predict an event when the predicted mean >= tau" is not a fair test
#      for a conditional-mean forecast. Here the cutoff on the score (mu, or p) is chosen on the VALIDATION
#      split to maximise CSI, then POD / FAR / CSI are reported on the TEST split. Applies to ALL models.
# Thresholds tau (all from the training period): wet 0.1 mm/h, Q90, Q95, Q97.5, 1.0 mm/h.
# Paired circular block bootstrap (block 28 = 7 days, 2,000 replicates, seed 42, percentile 95% CI)
# for AUC(p), AUC(p) - AUC(mu) and BSS.
#
# Run from the folder containing results/ (AutoDL: cd /root/autodl-tmp):
#     python3 code/analysis_q05b_exceedance_prob.py 2>&1 | tee results/metrics/q05b_output.txt
# Outputs (results/metrics/): q05b_exceedance_scores.csv, q05b_reliability.csv, q05b_tuned_cutoff_events.csv
#         (results/figures/):  fig_q05b_exceedance.png / .pdf
# ============================================================
import os
import numpy as np
import pandas as pd
from scipy.stats import norm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOTS = ["results", "/root/autodl-tmp/results", "../results"]
ROOT = next(r for r in ROOTS if os.path.isdir(r))
PRED_DIR = next(d for d in (os.path.join(ROOT, "predictions"), ROOT)
                if os.path.exists(os.path.join(d, "xgboost_preds.csv")))
MET = os.path.join(ROOT, "metrics")
FIG = os.path.join(ROOT, "figures")
os.makedirs(MET, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

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
COLOR = {"BU-LSTM-Attention (proposed)": "#1baf7a", "Probabilistic BiLSTM-Attention": "#eb6834",
         "BU-LSTM": "#2a78d6", "XGBoost": "#7a4fd0"}
STYLE = {"BU-LSTM-Attention (proposed)": ":", "Probabilistic BiLSTM-Attention": "-.", "BU-LSTM": "--", "XGBoost": "-"}
INK2, GRID = "#52514e", "#e3e2de"

raw = {n: pd.read_csv(os.path.join(PRED_DIR, f), parse_dates=["valid_time"])
       for n, f in MODELS.items() if os.path.exists(os.path.join(PRED_DIR, f))}
ref = raw["XGBoost"]
tr_y = ref[ref.split == "train"]["y_true"].to_numpy()
THR = {"wet 0.1": 0.1, "Q90": float(np.quantile(tr_y, 0.90)), "Q95": float(np.quantile(tr_y, 0.95)),
       "Q97.5": float(np.quantile(tr_y, 0.975)), "1.0 mm/h": 1.0}
print("Thresholds (training period):", {k: round(v, 4) for k, v in THR.items()})
TRAIN_RATE = {k: float(np.mean(tr_y >= v)) for k, v in THR.items()}
print("Training base rates:", {k: round(v, 4) for k, v in TRAIN_RATE.items()})


def part(d, which):
    if which == "test":
        m = d.split == "test"
    elif which == "val":
        m = ~d.split.isin(["train", "test"])
    return d[m].drop_duplicates("valid_time").sort_values("valid_time").reset_index(drop=True)


test = {n: part(d, "test") for n, d in raw.items()}
val = {n: part(d, "val") for n, d in raw.items()}
t0 = test["XGBoost"]["valid_time"].to_numpy()
y = test["XGBoost"]["y_true"].to_numpy()
N = len(y)
for n in raw:
    assert (test[n]["valid_time"].to_numpy() == t0).all(), f"{n}: test times differ"
    assert np.allclose(test[n]["y_true"].to_numpy(), y, atol=1e-6), f"{n}: y_true differs"
    assert len(val[n]) > 0, "no validation rows: split labels are " + str(raw[n].split.unique())
print(f"Test N = {N}; validation N = {len(val['XGBoost'])}")
PROB = [n for n in raw if not raw[n]["y_pred_std"].isna().all()]
print("Probabilistic models:", PROB)


def auc(o, s):
    """ROC-AUC via the rank-sum statistic; NaN if one class is empty."""
    o = np.asarray(o, bool)
    npos, nneg = int(o.sum()), int((~o).sum())
    if npos == 0 or nneg == 0:
        return np.nan
    r = pd.Series(s).rank().to_numpy()
    return float((r[o].sum() - npos * (npos + 1) / 2) / (npos * nneg))


def exceed_prob(mu, sd, tau):
    return 1.0 - norm.cdf((tau - mu) / np.maximum(sd, 1e-6))


def brier(o, p):
    return float(np.mean((p - o) ** 2))


def csi_scores(o, pred_event):
    h, mi, fa = int((o & pred_event).sum()), int((o & ~pred_event).sum()), int((~o & pred_event).sum())
    d = lambda a, c: float(a / c) if c else np.nan
    return h, mi, fa, d(h, h + mi), d(fa, h + fa), d(h, h + mi + fa)


def tuned_cutoff(o_val, s_val):
    """Cutoff on the score that maximises CSI on the validation split."""
    if o_val.sum() == 0:
        return np.nan, np.nan
    cands = np.unique(np.quantile(s_val, np.linspace(0.50, 0.999, 300)))
    best, bc = -1.0, np.nan
    for c in cands:
        h, mi, fa, _, _, csi = csi_scores(o_val, s_val >= c)
        if not np.isnan(csi) and csi > best:
            best, bc = csi, float(c)
    return bc, best


# ---------- scores per model and threshold ----------
mu = {n: test[n]["y_pred_mean"].to_numpy() for n in raw}
sd = {n: test[n]["y_pred_std"].to_numpy() for n in PROB}
mu_val = {n: val[n]["y_pred_mean"].to_numpy() for n in raw}
sd_val = {n: val[n]["y_pred_std"].to_numpy() for n in PROB}
y_val = val["XGBoost"]["y_true"].to_numpy()

# bootstrap indices (shared by all models and thresholds)
rng = np.random.default_rng(SEED)
nb = int(np.ceil(N / BLOCK))
boot_idx = [np.concatenate([(s + np.arange(BLOCK)) % N for s in rng.integers(0, N, size=nb)])[:N]
            for _ in range(NBOOT)]


def ci(a):
    a = np.asarray(a, float)
    a = a[~np.isnan(a)]
    if len(a) == 0:
        return np.nan, np.nan
    return tuple(float(v) for v in np.percentile(a, [2.5, 97.5]))


srows, rrows, trows = [], [], []
P = {}                                    # exceedance probabilities for the plot
for tk, tau in THR.items():
    o = y >= tau
    o_val = y_val >= tau
    for n in raw:
        # ---- B. tuned cutoff on mu (all models) ----
        c, vcsi = tuned_cutoff(o_val, mu_val[n])
        if not np.isnan(c):
            h, mi, fa, pod, far, csi = csi_scores(o, mu[n] >= c)
            trows.append({"Threshold": tk, "tau_mm_h": tau, "Model": n, "Score": "mean",
                          "Cutoff_from_validation": c, "Val_CSI": vcsi, "N_test_events": int(o.sum()),
                          "N_pred_events": int((mu[n] >= c).sum()), "Hits": h, "Misses": mi, "FalseAlarms": fa,
                          "POD": pod, "FAR": far, "CSI": csi})
        # ---- default rule: mean >= tau ----
        h, mi, fa, pod, far, csi = csi_scores(o, mu[n] >= tau)
        trows.append({"Threshold": tk, "tau_mm_h": tau, "Model": n, "Score": "mean, cutoff = tau",
                      "Cutoff_from_validation": tau, "Val_CSI": np.nan, "N_test_events": int(o.sum()),
                      "N_pred_events": int((mu[n] >= tau).sum()), "Hits": h, "Misses": mi, "FalseAlarms": fa,
                      "POD": pod, "FAR": far, "CSI": csi})
    for n in PROB:
        p = exceed_prob(mu[n], sd[n], tau)
        P[(n, tk)] = p
        pv = exceed_prob(mu_val[n], sd_val[n], tau)
        # ---- A. probability scores ----
        bs = brier(o, p)
        bs_ref = brier(o, np.full(N, TRAIN_RATE[tk]))
        bss = 1.0 - bs / bs_ref
        a_p, a_mu = auc(o, p), auc(o, mu[n])
        bb, ba, bd = [], [], []
        for idx in boot_idx:
            ob, pb, mb = o[idx], p[idx], mu[n][idx]
            if ob.sum() == 0 or ob.sum() == N:
                continue
            bsb = brier(ob, pb)
            bsr = brier(ob, np.full(N, TRAIN_RATE[tk]))
            bb.append(1 - bsb / bsr)
            x, z = auc(ob, pb), auc(ob, mb)
            ba.append(x)
            bd.append(x - z)
        srows.append({"Model": n, "Threshold": tk, "tau_mm_h": tau, "Train_base_rate": TRAIN_RATE[tk],
                      "Test_base_rate": float(o.mean()), "N_test_events": int(o.sum()),
                      "Brier": bs, "Brier_ref_train_rate": bs_ref, "BSS": bss,
                      "BSS_CI_low": ci(bb)[0], "BSS_CI_high": ci(bb)[1],
                      "AUC_p": a_p, "AUC_p_CI_low": ci(ba)[0], "AUC_p_CI_high": ci(ba)[1],
                      "AUC_mean": a_mu, "dAUC_p_minus_mean": a_p - a_mu,
                      "dAUC_CI_low": ci(bd)[0], "dAUC_CI_high": ci(bd)[1],
                      "Max_p": float(p.max()), "Mean_p_at_events": float(p[o].mean()) if o.any() else np.nan,
                      "Mean_p_at_nonevents": float(p[~o].mean())})
        # ---- B. tuned cutoff on p ----
        c, vcsi = tuned_cutoff(o_val, pv)
        if not np.isnan(c):
            h, mi, fa, pod, far, csi = csi_scores(o, p >= c)
            trows.append({"Threshold": tk, "tau_mm_h": tau, "Model": n, "Score": "exceedance probability",
                          "Cutoff_from_validation": c, "Val_CSI": vcsi, "N_test_events": int(o.sum()),
                          "N_pred_events": int((p >= c).sum()), "Hits": h, "Misses": mi, "FalseAlarms": fa,
                          "POD": pod, "FAR": far, "CSI": csi})
        # ---- reliability table (bins of p) ----
        edges = np.array([0, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0001])   # fixed probability bins
        b = np.digitize(p, edges) - 1
        for k in range(len(edges) - 1):
            m = b == k
            if m.any():
                rrows.append({"Model": n, "Threshold": tk, "Bin": k + 1, "N": int(m.sum()),
                              "Mean_p": float(p[m].mean()), "Obs_freq": float(o[m].mean()),
                              "N_events": int(o[m].sum())})

sc = pd.DataFrame(srows)
rel = pd.DataFrame(rrows)
tu = pd.DataFrame(trows)
sc.to_csv(os.path.join(MET, "q05b_exceedance_scores.csv"), index=False)
rel.to_csv(os.path.join(MET, "q05b_reliability.csv"), index=False)
tu.to_csv(os.path.join(MET, "q05b_tuned_cutoff_events.csv"), index=False)

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
print("\n=== A. EXCEEDANCE PROBABILITIES FROM THE GAUSSIAN HEAD (test) ===")
print("BSS > 0: better than always predicting the training base rate.  dAUC > 0 (CI excl. 0): sigma adds information beyond mu.")
print(sc[["Model", "Threshold", "N_test_events", "Test_base_rate", "BSS", "BSS_CI_low", "BSS_CI_high", "AUC_p",
          "AUC_p_CI_low", "AUC_p_CI_high", "AUC_mean", "dAUC_p_minus_mean", "dAUC_CI_low", "dAUC_CI_high",
          "Max_p"]].round(4).to_string(index=False))
print("\n=== A2. AUC of the predicted mean for the deterministic models (test) ===")
aucs = []
for tk, tau in THR.items():
    row = {"Threshold": tk, "N_events": int((y >= tau).sum())}
    for n in raw:
        row[n] = auc(y >= tau, mu[n])
    aucs.append(row)
print(pd.DataFrame(aucs).round(3).to_string(index=False))
print("\n=== B. EVENT DETECTION: cutoff = tau  versus  cutoff tuned on validation (test results) ===")
show = tu[tu.Threshold.isin(["Q95", "1.0 mm/h"])][["Threshold", "Model", "Score", "Cutoff_from_validation", "Val_CSI",
                                                  "N_test_events", "N_pred_events", "Hits", "FalseAlarms", "POD",
                                                  "FAR", "CSI"]]
print(show.round(3).to_string(index=False))

# ---------- figure: reliability at Q95 and ROC at Q95 ----------
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK2,
                     "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(1, 2, figsize=(7.4, 3.4), dpi=150)
tk = "Q95"
o = y >= THR[tk]
for n in PROB:
    r = rel[(rel.Model == n) & (rel.Threshold == tk) & (rel.N >= 30)]      # skip bins with fewer than 30 samples
    ax[0].plot(r.Mean_p, r.Obs_freq, STYLE[n], color=COLOR[n], marker="o", ms=3.5, lw=1.5,
               label=n.replace(" (proposed)", ""))
rr = rel[(rel.Threshold == tk) & (rel.N >= 30)]
mx = float(max(rr.Mean_p.max(), rr.Obs_freq.max())) * 1.1
ax[0].plot([0, mx], [0, mx], color=INK2, lw=0.9, ls=(0, (1, 2)))
ax[0].set_xlim(0, mx)
ax[0].set_ylim(0, mx)
ax[0].set_xlabel(f"Forecast probability of exceeding Q95 = {THR[tk]:.3f} mm h$^{{-1}}$")
ax[0].set_ylabel("Observed frequency")
ax[0].set_title("(a) Reliability of exceedance probability", loc="left", fontsize=9.5)
ax[0].grid(True, color=GRID, lw=0.6)
ax[0].legend(frameon=False, fontsize=7, loc="lower right")


def roc(o_, s):
    order = np.argsort(-s, kind="mergesort")
    oo = o_[order]
    tpr = np.concatenate([[0], np.cumsum(oo) / oo.sum()])
    fpr = np.concatenate([[0], np.cumsum(~oo) / (~oo).sum()])
    return fpr, tpr


for n in PROB:
    f, t_ = roc(o, P[(n, tk)])
    ax[1].plot(f, t_, STYLE[n], color=COLOR[n], lw=1.6, label=f"{n.replace(' (proposed)', '')} (p)")
f, t_ = roc(o, mu["XGBoost"])
ax[1].plot(f, t_, STYLE["XGBoost"], color=COLOR["XGBoost"], lw=1.6, label="XGBoost (mean)")
ax[1].plot([0, 1], [0, 1], color=INK2, lw=0.9, ls=(0, (1, 2)))
ax[1].set_xlabel("False positive rate")
ax[1].set_ylabel("True positive rate")
ax[1].set_title("(b) ROC for exceeding Q95", loc="left", fontsize=9.5)
ax[1].grid(True, color=GRID, lw=0.6)
ax[1].legend(frameon=False, fontsize=7, loc="lower right")
fig.tight_layout()
for ext, kw in (("png", {"dpi": 300}), ("pdf", {})):
    fig.savefig(os.path.join(FIG, f"fig_q05b_exceedance.{ext}"), facecolor="white", **kw)
plt.close(fig)
print("\nSaved q05b_*.csv to", MET, "and fig_q05b_exceedance (.png .pdf) to", FIG)
