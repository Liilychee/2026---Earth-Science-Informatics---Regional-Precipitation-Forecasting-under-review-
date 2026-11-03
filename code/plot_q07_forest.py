# ============================================================
# plot_q07_forest.py — issue 07 supplementary figure (proposed: Fig. S5). Reads results/metrics/
# q07_model_minus_reference.csv only (no training). Forest plot of RMSE(model) - RMSE(reference) with 95% paired
# block-bootstrap intervals; negative = the model is better than the reference.
# Panels: best climatology (monthly in the current run), AR(1) damped persistence, linear regression on lsp(t).
# Filled marker = interval excludes zero; open marker = interval includes zero (not significant).
#
# Run (AutoDL, cd /root/autodl-tmp):   python3 code/plot_q07_forest.py
# Output: results/figures/fig_q07_forest.png / .pdf
# ============================================================
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOTS = ["results", "/root/autodl-tmp/results", "../results"]
ROOT = next(r for r in ROOTS if os.path.isdir(r))
B = pd.read_csv(os.path.join(ROOT, "metrics", "q07_model_minus_reference.csv"))
FIG = os.path.join(ROOT, "figures")
os.makedirs(FIG, exist_ok=True)

INK, INK2, GRID, SURFACE, MARK = "#1f1e1c", "#52514e", "#e3e2de", "#ffffff", "#2a78d6"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "text.color": INK,
                     "axes.edgecolor": "#c9c8c4", "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK, "figure.facecolor": SURFACE,
                     "axes.facecolor": SURFACE})

# models ordered by test RMSE (best at top); reference panels in a fixed order
order = (B.drop_duplicates("Model").sort_values("RMSE_model")["Model"].tolist())
refs_all = B["Reference"].drop_duplicates().tolist()
clim = next(r for r in refs_all if r.startswith("Climatology"))
panels = [(clim, clim.replace("Climatology: ", "").capitalize() + " climatology"),
          ("AR(1) damped persistence", "AR(1) damped persistence"),
          ("Linear on lsp(t)", "Linear regression on lsp(t)")]
panels = [p for p in panels if p[0] in refs_all]
short = {"BU-LSTM-Attention (proposed)": "BU-LSTM-Attention\n(proposed)",
         "Probabilistic BiLSTM-Attention": "Probabilistic\nBiLSTM-Attention"}

lo = min(B.CI_low.min(), 0) * 1.08
hi = max(B.CI_high.max(), 0) + 0.004
fig, axes = plt.subplots(1, len(panels), figsize=(3.0 * len(panels) + 1.6, 3.6), sharey=True, sharex=True)
axes = np.atleast_1d(axes)
ypos = np.arange(len(order))[::-1]
for ax, (ref, title) in zip(axes, panels):
    d = B[B.Reference == ref].set_index("Model")
    for m, y in zip(order, ypos):
        r = d.loc[m]
        ax.plot([r.CI_low, r.CI_high], [y, y], color=MARK, lw=1.6, solid_capstyle="round", zorder=2)
        ax.plot(r.Diff, y, "o", ms=7, mfc=MARK if r.Significant else SURFACE, mec=MARK, mew=1.6, zorder=3)
    ax.axvline(0, color=INK2, lw=1.0, zorder=1)
    ax.set_title(title, fontsize=9.5, color=INK, loc="left")
    ax.set_xlim(lo, hi)
    ax.set_xlabel("RMSE(model) − RMSE(reference), mm h$^{-1}$\n(negative = model better)")
    ax.grid(axis="x", color=GRID, lw=0.7, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
axes[0].set_yticks(ypos)
axes[0].set_yticklabels([short.get(m, m) for m in order], fontsize=8.5)
h1, = axes[-1].plot([], [], "o", ms=7, mfc=MARK, mec=MARK, mew=1.6)
h2, = axes[-1].plot([], [], "o", ms=7, mfc=SURFACE, mec=MARK, mew=1.6)
fig.tight_layout(rect=(0, 0.07, 1, 1))
fig.legend([h1, h2], ["95% CI excludes 0 (significant)", "95% CI includes 0 (not significant)"], loc="lower center",
           ncol=2, frameon=False, fontsize=8.5, handletextpad=0.4, columnspacing=2.0)
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(FIG, f"fig_q07_forest.{ext}"), dpi=200 if ext == "png" else None,
                bbox_inches="tight", facecolor=SURFACE)
print("Saved", os.path.join(FIG, "fig_q07_forest.png / .pdf"))
