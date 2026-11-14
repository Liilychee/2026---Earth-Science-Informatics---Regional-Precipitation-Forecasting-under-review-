r"""
plot_r1m1.py — figures for reviewer comment R1-M1 (internal item 05), shared revision style (code/fig_style.py).
No training, no resampling, no change to any data or result file: only saved results are read.

Outputs (results/figures/revision/):
  r1M1_stratified_rmse.pdf/.eps/.png
      Redraw of manuscript Figure 3 (notebook Interpretable_analysis.ipynb, cell 42): grouped bars of test
      RMSE for the same five models and the same subsets, values read unchanged from
      results/final_stratified_point.csv. Only formatting and labels change:
      All / Legacy wet (>0) / Upper tail (>=Q95), y axis "RMSE (mm h^-1)".
      GROUPING (below) can switch to the revised wet threshold, taken unchanged from
      results/metrics/q03b_wet_definition_point.csv (already computed; nothing is recomputed here).
  r1M1_prediction_distribution.pdf/.eps/.png
      3 x 1 panels, observed vs XGBoost / BiLSTM-Attention / BU-LSTM-Attention: histograms (relative
      frequency, log axis) of the 3,939 test targets and of the RAW saved predictions (negative predictions
      kept, not set to zero), identical 0.1 mm h-1 bins, x range and y range in all panels; legends give
      model names only (maxima and negative counts: stats CSV and caption); dashed line at the
      training-period Q95 = 0.5740 mm h-1.
  r1M1_prediction_distribution_stats.csv   numbers printed in the panels (for the evidence table)

Run (AutoDL):  cd /root/autodl-tmp && python3 code/plot_r1m1.py
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fig_style as fs  # noqa: E402

# "legacy": All / Legacy wet (>0) / Upper tail      (as in the original Figure 3; default)
# "new":    All / Wet (>=0.1) / Upper tail          (revised wet threshold, from q03b)
# "both":   All / Legacy wet (>0) / Wet (>=0.1) / Upper tail
GROUPING = "legacy"

ROOT = next(r for r in ("results", "/root/autodl-tmp/results") if os.path.isdir(r))
MET = os.path.join(ROOT, "metrics")
OUT = os.path.join(ROOT, "figures", "revision")
pname = fs.name   # printed model names come only from fig_style


fs.apply()

# =====================================================================================================
# Figure 1: r1M1_stratified_rmse (redraw of manuscript Figure 3, notebook cell 42)
# =====================================================================================================
MODELS_RAW = ["XGBoost", "BiLSTM-Attention", "BU-LSTM", "BU-LSTM-Attention (proposed)",
              "Probabilistic BiLSTM-Attention"]                       # order of cell 42
LEGACY = os.path.join(ROOT, "final_stratified_point.csv")
NEW = os.path.join(MET, "q03b_wet_definition_point.csv")
LAB_ALL, LAB_LEG, LAB_WET = "All", fs.LEGACY_WET, fs.WET_SHORT

if GROUPING == "legacy":
    d = pd.read_csv(LEGACY)
    subsets = [("All", LAB_ALL), ("Wet", LAB_LEG), ("Heavy_Q95", fs.UPPER_TAIL)]
    key = "Regime"
else:
    d = pd.read_csv(NEW)
    subsets = [("All", LAB_ALL)]
    if GROUPING == "both":
        subsets.append(("Wet (>0 mm)", LAB_LEG))
    subsets += [("Wet (>=0.1 mm)", LAB_WET), ("Upper tail (>=Q95=0.574)", fs.UPPER_TAIL)]
    key = "Subset"

vals = pd.DataFrame(index=MODELS_RAW, columns=[s for s, _ in subsets], dtype=float)
for m in MODELS_RAW:
    for s, _ in subsets:
        row = d[(d["Model"] == m) & (d[key] == s)]
        assert len(row) == 1, f"{m} / {s}: {len(row)} rows"
        vals.loc[m, s] = float(row["RMSE"].iloc[0])

# self-check: the legacy values must be the ones of the original Figure 3, whichever file they come from
leg = pd.read_csv(LEGACY)
for m in MODELS_RAW:
    for s_new, s_old in (("All", "All"), ("Wet (>0 mm)", "Wet"), ("Upper tail (>=Q95=0.574)", "Heavy_Q95")):
        if s_new in vals.columns or (GROUPING == "legacy" and s_old in vals.columns):
            col = s_old if GROUPING == "legacy" else s_new
            ref = float(leg[(leg.Model == m) & (leg.Regime == s_old)]["RMSE"].iloc[0])
            assert abs(vals.loc[m, col] - ref) < 1e-6, f"{m} {col}: {vals.loc[m, col]} vs Figure 3 {ref}"
# provenance: the "All" RMSE of every bar is recomputed from the single saved test predictions
# (results/*_preds.csv); Figure 3 therefore shows single runs, not five-seed means.
PRED_FILE = {"XGBoost": "xgboost_preds.csv", "BiLSTM-Attention": "bilstm_attention_preds.csv",
             "BU-LSTM": "bulstm_preds.csv", "BU-LSTM-Attention (proposed)": "proposed_model_preds.csv",
             "Probabilistic BiLSTM-Attention": "prob_bilstm_attention_preds.csv"}
for m in MODELS_RAW:
    q = pd.read_csv(os.path.join(ROOT, PRED_FILE[m]))
    q = q[q.split == "test"]
    r = float(np.sqrt(np.mean((q.y_true - q.y_pred_mean) ** 2)))
    ref = float(leg[(leg.Model == m) & (leg.Regime == "All")]["RMSE"].iloc[0])
    assert abs(r - ref) < 1e-6, f"{m}: saved-prediction RMSE {r:.6f} vs CSV {ref:.6f}"
    print(f"  provenance OK: {pname(m):24s} All-RMSE {ref:.6f} = single saved run {PRED_FILE[m]}")
print(f"[r1M1_stratified_rmse] GROUPING={GROUPING}; RMSE (mm h-1) plotted:")
print(vals.rename(index=pname).round(4).to_string())

fig, ax = fs.figure(height_mm=72)
x = np.arange(len(subsets))
w = 0.82 / len(MODELS_RAW)
for i, m in enumerate(MODELS_RAW):
    n = pname(m)
    ax.bar(x + (i - (len(MODELS_RAW) - 1) / 2) * w, vals.loc[m].to_numpy(), width=w,
           color=fs.color(n), edgecolor="none", label=n)
ax.set_xticks(x, [lab for _, lab in subsets])
ax.set_ylabel(f"RMSE ({fs.UNIT})")
ax.set_ylim(0, float(np.nanmax(vals.to_numpy())) * 1.05)
ax.grid(axis="y", alpha=0.25, linewidth=0.5)
ax.set_axisbelow(True)
fig.legend(*ax.get_legend_handles_labels(), loc="outside upper center", ncol=3, columnspacing=1.0,
           handlelength=1.2)   # outside the axes: never covers the bars
fs.save(fig, "r1M1_stratified_rmse", outdir=OUT)

# =====================================================================================================
# Figure 2: r1M1_prediction_distribution (observed vs raw saved predictions, 3 x 1)
# =====================================================================================================
FILES = [("XGBoost", "xgboost_preds.csv"), ("BiLSTM-Attention", "bilstm_attention_preds.csv"),
         ("BU-LSTM-Attention", "proposed_model_preds.csv")]   # single saved runs (BU-LSTM-Attention: notebook Step 7)
raw = {n: pd.read_csv(os.path.join(ROOT, f), parse_dates=["valid_time"]) for n, f in FILES}
ref = raw["XGBoost"]
Q95 = float(ref.loc[ref.split == "train", "y_true"].quantile(0.95))
test = {n: r[r.split == "test"].sort_values("valid_time").reset_index(drop=True) for n, r in raw.items()}
t = test["XGBoost"]["valid_time"].to_numpy()
y = test["XGBoost"]["y_true"].to_numpy()
for n, r in test.items():   # same 3,939 targets, identical time stamps and observations
    assert len(r) == 3939 and (r["valid_time"].to_numpy() == t).all(), n
    assert np.allclose(r["y_true"].to_numpy(), y, atol=1e-6), n
P = {n: r["y_pred_mean"].to_numpy() for n, r in test.items()}   # raw: no clipping

# 0.05 mm h-1 bins. The edge that would sit at 0 is placed at -1e-6 instead: 711 observed targets are stored as
# -7.45e-9 (float32 representation of an exact zero) and must fall in the first non-negative bin, not in a
# "negative" bin. Data are not changed; only that one bin edge moves by 1e-6. Negative predictions (< -1e-6)
# keep their own bins left of zero.
# 3 x 1 histograms. Identical bins, x range and y range in all panels; relative frequency on a log axis
# (on a linear axis the upper tail, 1-5 samples per bin, would be invisible).
# Bins of 0.1 mm h-1. The edge that would sit at 0 is placed at -1e-6: 711 observed targets are stored as
# -7.45e-9 (float32 representation of an exact zero) and belong to the first non-negative bin. Data are not
# changed; negative predictions (all < -1e-6) fall in the bin left of zero.
bins = np.round(np.arange(-0.10, 3.10 + 1e-9, 0.10), 10)
bins[np.isclose(bins, 0.0)] = -1e-6
TINY_NEG_OBS = int(((y < 0) & (y > -1e-6)).sum())
assert int((y <= -1e-6).sum()) == 0, "observed values below -1e-6"
assert all(int(((p < 0) & (p > -1e-6)).sum()) == 0 for p in P.values()), "predictions in (-1e-6, 0)"
assert bins[0] <= min(p.min() for p in P.values()) and bins[-1] >= y.max()
print(f"observed targets stored as tiny negatives (> -1e-6, counted in the first non-negative bin): {TINY_NEG_OBS}")
XLIM = (bins[0], bins[-1])
YLIM = (1e-4, 1.0)                     # 1/3939 = 2.5e-4 is the smallest non-zero relative frequency
wts = np.full(len(y), 1 / len(y))   # bar height = count in bin / 3939 (proportion, NOT density); empty bins not drawn on the log axis

stats = []
fig, axs = fs.figure(height_mm=135, nrows=3, ncols=1, sharex=True, sharey=True)
for a, (n, _), L in zip(axs, FILES, "abc"):
    p = P[n]
    a.hist(y, bins=bins, weights=wts, histtype="stepfilled", color=fs.OBSERVED_COLOR, linewidth=0,
           label="Observed (ERA5)")
    a.hist(p, bins=bins, weights=wts, histtype="stepfilled", color=fs.color(n), alpha=0.45, linewidth=0)
    a.hist(p, bins=bins, weights=wts, histtype="step", color=fs.color(n), linewidth=1.0,
           label=n)   # maxima and negative counts are given in the caption (stats CSV)
    a.axvline(Q95, color="0.25", lw=0.7, ls=(0, (2, 2)))
    a.axvline(0.0, color="0.45", lw=0.5, zorder=0)        # separates the bin of negative predictions
    a.set_yscale("log")
    a.set_xlim(*XLIM)
    a.set_ylim(*YLIM)
    a.set_title(rf"{{\fontsize{{{fs.FS_PANEL}}}{{12}}\selectfont\textbf{{({L})}}}} Observed vs {n}", loc="left")
    a.set_ylabel("Relative frequency")
    h, l = a.get_legend_handles_labels()
    from matplotlib.patches import Patch
    a.legend([Patch(color=fs.OBSERVED_COLOR), Patch(facecolor=fs.color(n), alpha=0.6, edgecolor=fs.color(n))], l,
             loc="upper right", handlelength=1.4)
    stats.append({"Model": n, "N": len(p), "Max_obs": y.max(), "Max_pred": p.max(), "Min_pred": p.min(),
                  "N_pred_negative": int((p < 0).sum()), "SD_ratio": p.std() / y.std(),
                  "Share_obs_ge_Q95": float(np.mean(y >= Q95)), "Share_pred_ge_Q95": float(np.mean(p >= Q95))})
# no in-figure Q95 text: the dashed line is explained in the caption (same in all three panels)
axs[-1].set_xlabel(f"Precipitation ({fs.UNIT})")

st = pd.DataFrame(stats)
print(f"[r1M1_prediction_distribution] N={len(y)}, Q95(train)={Q95:.4f}, {len(bins) - 1} bins of 0.1, "
      f"x range {XLIM}, y range {YLIM}")
print(st.round(4).to_string(index=False))
# self-check against the values already reported for R1-M1
assert abs(y.max() - 2.9865) < 5e-4 and abs(Q95 - 0.5740) < 5e-4
assert st.N_pred_negative.tolist() == [19, 144, 40], st.N_pred_negative.tolist()
assert [round(v, 2) for v in st.Max_pred] == [1.02, 0.58, 0.49], st.Max_pred.tolist()
fs.save(fig, "r1M1_prediction_distribution", outdir=OUT)
st.to_csv(os.path.join(OUT, "r1M1_prediction_distribution_stats.csv"), index=False)
