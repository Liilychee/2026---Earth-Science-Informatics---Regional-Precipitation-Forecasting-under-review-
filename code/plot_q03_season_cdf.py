# ============================================================
# plot_q03_season_cdf.py — issue 03 (R3 L469-471): distribution of precipitation
# across the four seasons, entire 2004-2021 dataset.
# Reads the observed target (y_true, mm per hour) from a saved prediction file; no training.
#
#   Panel (a): empirical CDF per season (x zoomed to 0-2 mm/h)
#   Panel (b): exceedance probability 1-CDF per season, log y-axis, x to 5 mm/h
#              -> shows the upper tail; reference lines at
#                 0.1 mm/h  (wet-hour threshold),
#                 Q95 = 0.574 mm/h (training-derived threshold used in the paper),
#                 1.0 mm/h  (R3: "< 1 mm is not even rain" convention),
#                 2.5 mm/h  (WMO-No.8 rain: light < 2.5 <= moderate)
# Seasons: DJF (Dec-Feb), MAM (Mar-May), JJA (Jun-Aug), SON (Sep-Nov).
#
# Run from the folder that contains results/ (AutoDL: cd /root/autodl-tmp):
#     python3 code/plot_q03_season_cdf.py
# Output: results/figures/fig_season_cdf.png (300 dpi), .pdf, and
#         results/metrics/q03_season_cdf_data.csv (the plotted values)
# ============================================================
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOTS = ["results", "/root/autodl-tmp/results", "../results"]
ROOT = next(r for r in ROOTS if os.path.isdir(r))
PRED = next(p for p in (os.path.join(ROOT, "predictions", "xgboost_preds.csv"),
                        os.path.join(ROOT, "xgboost_preds.csv")) if os.path.exists(p))
FIG_DIR = os.path.join(ROOT, "figures")
MET_DIR = os.path.join(ROOT, "metrics")
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(MET_DIR, exist_ok=True)

d = pd.read_csv(PRED, parse_dates=["valid_time"]).drop_duplicates("valid_time")
tr = pd.read_csv(PRED, parse_dates=["valid_time"])
q95_train = float(tr[tr.split == "train"]["y_true"].quantile(0.95))
print(f"Source: {PRED}; target samples: {len(d)}; train-derived Q95 = {q95_train:.4f} mm/h")

SEASON = {12: "DJF", 1: "DJF", 2: "DJF", 3: "MAM", 4: "MAM", 5: "MAM",
          6: "JJA", 7: "JJA", 8: "JJA", 9: "SON", 10: "SON", 11: "SON"}
d["season"] = d.valid_time.dt.month.map(SEASON)
ORDER = ["DJF", "MAM", "JJA", "SON"]                 # fixed order = fixed colour
COLOR = {"DJF": "#2a78d6", "MAM": "#eb6834", "JJA": "#1baf7a", "SON": "#eda100"}
STYLE = {"DJF": "-", "MAM": "--", "JJA": "-.", "SON": ":"}   # secondary encoding (print / CVD)
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e3e2de"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK2,
                     "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False})

fig, ax = plt.subplots(1, 2, figsize=(7.4, 3.3), dpi=150)
rows = []
for s in ORDER:
    x = np.sort(d.loc[d.season == s, "y_true"].values)
    n = len(x)
    cdf = np.arange(1, n + 1) / n
    ex = 1.0 - np.arange(0, n) / n                   # P(X >= x_i)
    ax[0].plot(x, cdf, STYLE[s], color=COLOR[s], lw=2, label=f"{s} (n={n:,})", zorder=3)
    ax[1].plot(x, ex, STYLE[s], color=COLOR[s], lw=2, label=s, zorder=3)
    for thr in (0.1, q95_train, 1.0, 2.5):
        rows.append({"Season": s, "Threshold_mm_per_h": round(thr, 4),
                     "CDF_below": float((x < thr).mean()), "Exceedance_ge": float((x >= thr).mean()),
                     "N_ge": int((x >= thr).sum()), "N": n})

refs = [(0.1, "0.1"), (q95_train, "Q95"), (1.0, "1.0"), (2.5, "2.5")]
for a in ax:
    a.grid(True, color=GRID, lw=0.6)
    a.set_axisbelow(True)
    for thr, _ in refs:
        a.axvline(thr, color=INK2, lw=0.9, ls=(0, (1, 2)), zorder=1.5)

ax[0].set_xlim(0, 2.0)
ax[0].set_ylim(0, 1.0)
ax[0].set_xlabel("Hourly precipitation (mm h$^{-1}$)")
ax[0].set_ylabel("Cumulative probability")
ax[0].set_title("(a) Empirical CDF", loc="left", fontsize=9.5, color=INK)
ax[0].legend(frameon=False, fontsize=8, loc="lower right")

ax[1].set_yscale("log")
ax[1].set_xlim(0, 5.0)
ax[1].set_ylim(2e-4, 1.2)
ax[1].set_xlabel("Hourly precipitation (mm h$^{-1}$)")
ax[1].set_ylabel("Exceedance probability  P(X $\\geq$ x)")
ax[1].set_title("(b) Upper tail (log scale)", loc="left", fontsize=9.5, color=INK)
# reference labels sit ABOVE the plotting area (no collision with the curves)
for a, xmax in ((ax[0], 2.0), (ax[1], 5.0)):
    for thr, lab in refs:
        if thr <= xmax:
            a.text(thr, 1.015, lab, transform=a.get_xaxis_transform(), fontsize=7, color=INK2,
                   ha="center", va="bottom")
    a.set_title(a.get_title(loc="left"), loc="left", fontsize=9.5, color=INK, pad=14)
fig.text(0.5, 0.005, "Dotted lines: 0.1, Q95 = %.3f (training-derived), 1.0 and 2.5 mm h$^{-1}$ "
         "(lower bound of WMO-No. 8 'moderate' rain; 3-min basis)." % q95_train,
         ha="center", va="bottom", fontsize=7, color=INK2)
fig.tight_layout(rect=(0, 0.04, 1, 1))
for ext, kw in (("png", {"dpi": 300}), ("pdf", {})):
    fig.savefig(os.path.join(FIG_DIR, f"fig_season_cdf.{ext}"), facecolor="white", **kw)
pd.DataFrame(rows).to_csv(os.path.join(MET_DIR, "q03_season_cdf_data.csv"), index=False)
print("Saved", os.path.join(FIG_DIR, "fig_season_cdf.png / .pdf"), "and q03_season_cdf_data.csv")
print(pd.DataFrame(rows).round(4).to_string(index=False))
