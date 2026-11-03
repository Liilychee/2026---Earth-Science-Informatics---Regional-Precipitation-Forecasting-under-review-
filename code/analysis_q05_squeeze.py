# ============================================================
# analysis_q05_squeeze.py — issue 05 (R1 M1, R2 M4, R4 m3/m26):
# "Are the predictions squeezed toward the mean? Do the models fail to reach high precipitation?"
# NO training. Reads the saved prediction CSVs (test split) only. Nothing existing is modified.
#
# What it computes (test set, all models):
#   1. Spread / tail of the predictions vs the observations (std, quantiles, max, share above thresholds)
#   2. Calibration slope  b  from  obs = a + b * pred   (b > 1: predictions too narrow)
#      and the check  std(pred)/std(obs)  vs  Pearson r.  For a calibrated conditional-mean forecast
#      (b = 1) the ratio equals r, i.e. a narrow spread is then explained by LIMITED SKILL, not by a bias.
#   3. Mean prediction vs mean observation inside observed-intensity classes
#      (< 0.1, 0.1 to Q95, Q95 to 1.0, >= 1.0 mm/h): how much of the high-rain signal is captured
#   4. Reliability by deciles of the prediction (mean obs vs mean pred)
#   5. Events >= 1.0 mm/h (R1: "positive cases not identified"): hits, misses, false alarms per model
#   6. The top-15 observed test events with every model's prediction
# Figures: results/figures/fig_q05_distribution.png/.pdf  (histogram + reliability)
#          results/figures/fig_q05_events.png/.pdf        (4 largest separate events, +-48 h)
#
# Run from the folder containing results/ (AutoDL: cd /root/autodl-tmp):
#     python3 code/analysis_q05_squeeze.py 2>&1 | tee results/metrics/q05_output.txt
# Outputs (results/metrics/): q05_spread_calibration.csv, q05_class_means.csv, q05_reliability.csv,
#                             q05_events_ge1mm.csv, q05_top_events.csv
# ============================================================
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

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
    "Climatology (global mean)": "climatology_preds.csv",
    "XGBoost": "xgboost_preds.csv",
    "Transformer": "transformer_preds.csv",
    "BU-LSTM": "bulstm_preds.csv",
    "BiLSTM-Attention": "bilstm_attention_preds.csv",
    "BU-LSTM-Attention (proposed)": "proposed_model_preds.csv",
    "Probabilistic BiLSTM-Attention": "prob_bilstm_attention_preds.csv",
}
PLOT = ["XGBoost", "BiLSTM-Attention", "BU-LSTM-Attention (proposed)"]
COLOR = {"Observed": "#0b0b0b", "XGBoost": "#2a78d6", "BiLSTM-Attention": "#eb6834",
         "BU-LSTM-Attention (proposed)": "#1baf7a"}
STYLE = {"Observed": "-", "XGBoost": "--", "BiLSTM-Attention": "-.", "BU-LSTM-Attention (proposed)": ":"}
INK2, GRID = "#52514e", "#e3e2de"

raw = {n: pd.read_csv(os.path.join(PRED_DIR, f), parse_dates=["valid_time"])
       for n, f in MODELS.items() if os.path.exists(os.path.join(PRED_DIR, f))}
ref = raw["XGBoost"]
Q95 = float(ref[ref.split == "train"]["y_true"].quantile(0.95))
test = {n: d[d.split == "test"].drop_duplicates("valid_time").sort_values("valid_time").reset_index(drop=True)
        for n, d in raw.items()}
t = test["XGBoost"]["valid_time"].to_numpy()
y = test["XGBoost"]["y_true"].to_numpy()
for n, d in test.items():
    assert (d["valid_time"].to_numpy() == t).all(), f"{n}: times differ"
    assert np.allclose(d["y_true"].to_numpy(), y, atol=1e-6), f"{n}: y_true differs"
P = {n: d["y_pred_mean"].to_numpy() for n, d in test.items()}
N = len(y)
print(f"Test samples: {N}; train-only Q95 = {Q95:.4f} mm/h; obs mean {y.mean():.4f}, std {y.std():.4f}, max {y.max():.3f}")
print(f"Observed share >= 0.1: {np.mean(y >= 0.1)*100:.1f} %, >= Q95: {np.mean(y >= Q95)*100:.1f} % ({int((y >= Q95).sum())}), "
      f">= 1.0: {np.mean(y >= 1.0)*100:.2f} % ({int((y >= 1.0).sum())})")


def slope(x, z):
    """OLS slope of z on x; NaN for a constant x."""
    return float(np.polyfit(x, z, 1)[0]) if np.ptp(x) > 0 else np.nan


def corr(a, b):
    return float(np.corrcoef(a, b)[0, 1]) if np.ptp(a) > 0 and np.ptp(b) > 0 else np.nan


# ---------- 1 + 2. spread, tail and calibration ----------
rows = []
for n, p in P.items():
    r = corr(y, p)
    sd_ratio = float(p.std() / y.std())
    rows.append({"Model": n, "Std_pred": float(p.std()), "Std_obs": float(y.std()), "Std_ratio": sd_ratio,
                 "Pearson_r": r, "Std_ratio_minus_r": sd_ratio - r if not np.isnan(r) else np.nan,
                 "Calib_slope_obs_on_pred": slope(p, y), "Slope_pred_on_obs": slope(y, p),
                 "Pred_max": float(p.max()), "Obs_max": float(y.max()),
                 "Pred_Q99": float(np.quantile(p, .99)), "Obs_Q99": float(np.quantile(y, .99)),
                 "Pred_Q95": float(np.quantile(p, .95)), "Obs_Q95_test": float(np.quantile(y, .95)),
                 "Share_pred_ge_0.1": float(np.mean(p >= 0.1)), "Share_obs_ge_0.1": float(np.mean(y >= 0.1)),
                 "Share_pred_ge_Q95": float(np.mean(p >= Q95)), "Share_obs_ge_Q95": float(np.mean(y >= Q95)),
                 "N_pred_ge_1.0": int((p >= 1.0).sum()), "N_obs_ge_1.0": int((y >= 1.0).sum()),
                 "Frac_pred_negative": float(np.mean(p < 0))})
spread = pd.DataFrame(rows)
spread.to_csv(os.path.join(MET, "q05_spread_calibration.csv"), index=False)

# ---------- 3. class means ----------
cls = [("< 0.1", y < 0.1), (f"0.1 to Q95 ({Q95:.3f})", (y >= 0.1) & (y < Q95)),
       (f"Q95 to 1.0", (y >= Q95) & (y < 1.0)), (">= 1.0", y >= 1.0)]
crow = []
for n, p in P.items():
    for lab, m in cls:
        crow.append({"Model": n, "Obs_class_mm_h": lab, "N": int(m.sum()), "Mean_obs": float(y[m].mean()),
                     "Mean_pred": float(p[m].mean()), "Capture_ratio_pred_over_obs": float(p[m].mean() / y[m].mean())})
class_df = pd.DataFrame(crow)
class_df.to_csv(os.path.join(MET, "q05_class_means.csv"), index=False)

# ---------- 4. reliability by prediction deciles ----------
rel = []
for n in PLOT:
    p = P[n]
    edges = np.unique(np.quantile(p, np.linspace(0, 1, 11)))
    b = np.clip(np.searchsorted(edges, p, side="right") - 1, 0, len(edges) - 2)
    for k in range(len(edges) - 1):
        m = b == k
        if m.any():
            rel.append({"Model": n, "Decile": k + 1, "N": int(m.sum()),
                        "Mean_pred": float(p[m].mean()), "Mean_obs": float(y[m].mean())})
rel_df = pd.DataFrame(rel)
rel_df.to_csv(os.path.join(MET, "q05_reliability.csv"), index=False)

# ---------- 5. events >= 1.0 mm/h ----------
erow = []
ob = y >= 1.0
for n, p in P.items():
    pb = p >= 1.0
    h, mi, fa = int((ob & pb).sum()), int((ob & ~pb).sum()), int((~ob & pb).sum())
    d = lambda a, c: float(a / c) if c else np.nan
    erow.append({"Model": n, "N_obs_events": int(ob.sum()), "N_pred_events": int(pb.sum()), "Hits": h, "Misses": mi,
                 "FalseAlarms": fa, "POD": d(h, h + mi), "FAR": d(fa, h + fa), "CSI": d(h, h + mi + fa),
                 "Max_pred_at_obs_events": float(p[ob].max()) if ob.any() else np.nan,
                 "Mean_pred_at_obs_events": float(p[ob].mean()) if ob.any() else np.nan,
                 "Mean_obs_at_obs_events": float(y[ob].mean()) if ob.any() else np.nan})
ev = pd.DataFrame(erow)
ev.to_csv(os.path.join(MET, "q05_events_ge1mm.csv"), index=False)

# ---------- 6. top events ----------
top = np.argsort(-y)[:15]
te = pd.DataFrame({"valid_time": t[top], "obs_mm": y[top]})
for n in PLOT + ["Probabilistic BiLSTM-Attention", "Persistence"]:
    if n in P:
        te[n] = P[n][top]
te.to_csv(os.path.join(MET, "q05_top_events.csv"), index=False)

# ---------- 7. timing check: does the prediction track the observation at the same time or one step later? ----------
# corr(pred at time t, obs at time t+k), k in steps of 6 h. k = 0: same valid time. k = -1: the PREVIOUS target
# (a prediction that mostly echoes what has just been observed correlates best at k = -1).
lag_rows = []
for n, p in P.items():
    for k in (-2, -1, 0, 1, 2):
        a, b = (p[:N - k], y[k:]) if k >= 0 else (p[-k:], y[:N + k])
        lag_rows.append({"Model": n, "Lag_steps_k": k, "Corr_pred_t_obs_t_plus_k": corr(a, b)})
lag_df = pd.DataFrame(lag_rows)
lag_df.to_csv(os.path.join(MET, "q05_lag_corr.csv"), index=False)
# peak timing for the 15 largest events: valid time of the largest prediction within +-1 step of the observed peak
trows = []
for n in PLOT:
    for i in top:
        lo, hi = max(0, i - 1), min(N, i + 2)
        j = lo + int(np.argmax(P[n][lo:hi]))
        trows.append({"Model": n, "Peak_offset_steps": j - i})
timing = pd.DataFrame(trows).groupby(["Model", "Peak_offset_steps"]).size().unstack(fill_value=0)

# ---------- print ----------
pd.set_option("display.width", 230)
pd.set_option("display.max_columns", 40)
print("\n=== 1+2. SPREAD AND CALIBRATION (test). Std_ratio ~ Pearson_r and slope ~ 1  =>  narrow spread = limited skill ===")
print(spread[["Model", "Std_pred", "Std_obs", "Std_ratio", "Pearson_r", "Calib_slope_obs_on_pred",
              "Slope_pred_on_obs", "Pred_max", "Obs_max", "Pred_Q99", "Obs_Q99"]].round(3).to_string(index=False))
print("\n  share of samples above thresholds (pred vs obs):")
print(spread[["Model", "Share_pred_ge_0.1", "Share_obs_ge_0.1", "Share_pred_ge_Q95", "Share_obs_ge_Q95",
              "N_pred_ge_1.0", "N_obs_ge_1.0", "Frac_pred_negative"]].round(4).to_string(index=False))
print("\n=== 3. MEAN PREDICTION INSIDE OBSERVED CLASSES (capture ratio = mean pred / mean obs) ===")
print(class_df.pivot(index="Model", columns="Obs_class_mm_h", values="Capture_ratio_pred_over_obs").round(3).to_string())
print(class_df[class_df.Model == "XGBoost"][["Obs_class_mm_h", "N", "Mean_obs"]].round(3).to_string(index=False))
print("\n=== 5. EVENTS >= 1.0 mm/h ===")
print(ev.round(3).to_string(index=False))
print("\n=== 6. TOP-15 OBSERVED TEST EVENTS ===")
print(te.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
print("\n=== 7. TIMING: corr(pred at t, obs at t+k); k = -1 means the previous 6-hourly target ===")
print(lag_df.pivot(index="Model", columns="Lag_steps_k", values="Corr_pred_t_obs_t_plus_k").round(3).to_string())
print("\n  For the 15 largest events: where is the largest prediction within +-1 step of the observed peak?")
print("  (offset -1 = one step earlier, 0 = same step, +1 = one step later; entries are numbers of events)")
print(timing.to_string())

# ---------- figures ----------
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK2,
                     "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(1, 2, figsize=(7.4, 3.3), dpi=150)
bins = np.concatenate([np.arange(0, 1.0, 0.05), np.arange(1.0, 3.01, 0.25)])
ax[0].hist(y, bins=bins, histtype="step", color=COLOR["Observed"], lw=2, ls=STYLE["Observed"], label="Observed")
for n in PLOT:
    ax[0].hist(np.clip(P[n], 0, None), bins=bins, histtype="step", color=COLOR[n], lw=1.8, ls=STYLE[n],
               label=n.replace(" (proposed)", ""))
ax[0].set_yscale("log")
ax[0].axvline(Q95, color=INK2, lw=0.9, ls=(0, (1, 2)))
ax[0].text(Q95, 1.015, "Q95", transform=ax[0].get_xaxis_transform(), fontsize=7, color=INK2, ha="center", va="bottom")
ax[0].set_xlabel("Hourly precipitation (mm h$^{-1}$)")
ax[0].set_ylabel("Number of test samples")
ax[0].set_title("(a) Observed and predicted distributions", loc="left", fontsize=9.5, pad=14)
ax[0].grid(True, color=GRID, lw=0.6)
ax[0].legend(frameon=False, fontsize=7, loc="upper right")
for n in PLOT:
    r = rel_df[rel_df.Model == n]
    ax[1].plot(r.Mean_pred, r.Mean_obs, STYLE[n], color=COLOR[n], marker="o", ms=3.5, lw=1.6,
               label=n.replace(" (proposed)", ""))
mx = float(max(rel_df.Mean_pred.max(), rel_df.Mean_obs.max())) * 1.05
ax[1].plot([0, mx], [0, mx], color=INK2, lw=0.9, ls=(0, (1, 2)))
ax[1].set_xlim(0, mx)
ax[1].set_ylim(0, mx)
ax[1].set_xlabel("Mean prediction in decile (mm h$^{-1}$)")
ax[1].set_ylabel("Mean observation in decile (mm h$^{-1}$)")
ax[1].set_title("(b) Reliability by prediction decile", loc="left", fontsize=9.5, pad=14)
ax[1].grid(True, color=GRID, lw=0.6)
ax[1].legend(frameon=False, fontsize=7, loc="upper left")
fig.tight_layout()
for ext, kw in (("png", {"dpi": 300}), ("pdf", {})):
    fig.savefig(os.path.join(FIG, f"fig_q05_distribution.{ext}"), facecolor="white", **kw)
plt.close(fig)

# four largest separate events (peaks at least 7 days apart), +-48 h = 8 samples either side
order = np.argsort(-y)
picked = []
for i in order:
    if all(abs(i - j) > 28 for j in picked):
        picked.append(int(i))
    if len(picked) == 4:
        break
fig, axs = plt.subplots(2, 2, figsize=(7.4, 5.0), dpi=150, sharey=False)
for a, i in zip(axs.ravel(), picked):
    lo, hi = max(0, i - 8), min(N, i + 9)
    x = pd.to_datetime(t[lo:hi])
    a.bar(x, y[lo:hi], width=0.15, color=COLOR["Observed"], alpha=0.35, label="Observed")
    for n in PLOT:
        a.plot(x, np.clip(P[n][lo:hi], 0, None), STYLE[n], color=COLOR[n], marker="o", ms=2.5, lw=1.5,
               label=n.replace(" (proposed)", ""))
    a.axhline(Q95, color=INK2, lw=0.8, ls=(0, (1, 2)))
    a.set_title(pd.Timestamp(t[i]).strftime("%Y-%m-%d %H:%M UTC") + f"  (obs {y[i]:.2f} mm h$^{{-1}}$)",
                loc="left", fontsize=8.5)
    a.grid(True, color=GRID, lw=0.6)
    a.xaxis.set_major_locator(mdates.HourLocator(byhour=[0, 12]))     # data are at 00/06/12/18 UTC
    a.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H"))
    a.tick_params(axis="x", labelrotation=30, labelsize=7)
    a.set_ylabel("mm h$^{-1}$")
axs[0, 0].legend(frameon=False, fontsize=7, loc="upper left")
fig.text(0.5, 0.005, "Bars: observed (ERA5 target). Lines: model predictions. Dotted line: Q95 = %.3f mm h$^{-1}$." % Q95,
         ha="center", va="bottom", fontsize=7, color=INK2)
fig.tight_layout(rect=(0, 0.03, 1, 1))
for ext, kw in (("png", {"dpi": 300}), ("pdf", {})):
    fig.savefig(os.path.join(FIG, f"fig_q05_events.{ext}"), facecolor="white", **kw)
plt.close(fig)
print("\nSaved CSVs to", MET, "and figures fig_q05_distribution / fig_q05_events (.png .pdf) to", FIG)
