r"""
plot_r2m7.py — R2-M7: effect of spatial averaging on the hourly rainfall distribution, shared revision style
(fig_style.py v6, unchanged). No training and no statistic is recomputed from data; all values are read from CSV.

Input : results/r2m7_evidence/r2m7_series_stats.csv (archived, commit dc85083): 25 ERA5 cells + equal-weight
        regional mean on the 18,404 windowed training targets; Q90, Q95, Q99, Q99.9, Max in mm/h (full precision).
        Ratios are computed here from these unrounded values, never from rounded percentages.
Figure: one panel; x = statistic (Q90, Q95, Q99, Q99.9, Max) as equally spaced categories; y = value divided by
        the median of the 25 cells for that statistic. Grey dots = the 25 cells (fixed horizontal jitter, left of the
        category centre), black diamond = regional mean, dashed line = ratio 1 (cell median).
        y range is computed from the data so that no point is clipped.
        Percentage of the regional mean relative to the cell median is printed under each diamond.
Checks: 26 rows (25 cells + 1 regional mean), n_samples = 18404 everywhere, regional Q95 = 0.5740 mm/h.
Output: results/figures/revision/r2M7_spatial_quantiles.pdf/.eps/.png and r2M7_spatial_quantiles_values.csv

Run (AutoDL):  cd /root/autodl-tmp && python3 code/plot_r2m7.py
"""
import hashlib
import math
import os
import sys

import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fig_style as fs  # noqa: E402

ROOT = next(r for r in ("results", "/root/autodl-tmp/results") if os.path.isdir(r))
SRC = os.path.join(ROOT, "r2m7_evidence", "r2m7_series_stats.csv")
OUT = os.path.join(ROOT, "figures", "revision")
STEM = "r2M7_spatial_quantiles"
STATS = [("Q90", "Q90"), ("Q95", "Q95"), ("Q99", "Q99"), ("Q99.9", "Q99.9"), ("Max", "Max")]
CELL_GREY, REG_COLOR = "#9E9E9E", "#000000"
CELL_X, REG_X = -0.17, 0.21        # cells left of the category centre, regional mean right of it (category units)
JITTER = 0.08                      # half-width of the fixed horizontal jitter of the 25 cell dots

d = pd.read_csv(SRC)
# Role: "regional" or a cell ("cell", "airport_nearest_cell", "city_nearest_cell")
cells, reg = d[d.Role != "regional"].copy(), d[d.Role == "regional"]
assert len(d) == 26 and len(cells) == 25 and len(reg) == 1, (len(d), len(cells), len(reg))
assert (d.N == 18404).all(), d.N.unique()
assert cells[["Latitude", "Longitude"]].drop_duplicates().shape[0] == 25
cells["cell_id"] = [f"{la:.2f},{lo:.2f}" for la, lo in zip(cells.Latitude, cells.Longitude)]
reg = reg.iloc[0]
assert abs(reg.Q95 - 0.5740) < 5e-4, reg.Q95

rows = []
offs = np.random.default_rng(0).uniform(-JITTER, JITTER, 25)   # fixed jitter, identical for every statistic
for k, (col, lab) in enumerate(STATS):
    med = float(cells[col].median())
    for (_, c), o in zip(cells.iterrows(), offs):
        rows.append({"statistic": lab, "series_type": "cell", "cell_id": c.cell_id, "value_mm_h": float(c[col]),
                     "cell_median_mm_h": med, "ratio_to_cell_median": float(c[col]) / med,
                     "x_category": k, "x_plotted": k + CELL_X + o})
    rows.append({"statistic": lab, "series_type": "regional_mean", "cell_id": "REG", "value_mm_h": float(reg[col]),
                 "cell_median_mm_h": med, "ratio_to_cell_median": float(reg[col]) / med,
                 "x_category": k, "x_plotted": k + REG_X})
v = pd.DataFrame(rows)
r = v[v.series_type == "regional_mean"].set_index("statistic")
summary = pd.DataFrame({"regional": r.value_mm_h, "cell_median": r.cell_median_mm_h,
                        "pct_vs_median": 100 * (r.ratio_to_cell_median - 1),
                        "cells_below_regional": [int((cells[c] < reg[c]).sum()) for c, _ in STATS]})
print(summary.round(4).to_string())

# QC: exactly 25 cells + 1 regional mean per statistic; y range from the data (never clipped)
cnt = v.groupby(["statistic", "series_type"]).size().unstack()
assert (cnt["cell"] == 25).all() and (cnt["regional_mean"] == 1).all(), cnt
print("regional ratios:", r.ratio_to_cell_median.round(3).to_dict())
for lab in ("Q90", "Q95"):
    print(f"{lab}: cells below regional = {int((v[(v.statistic == lab) & (v.series_type == 'cell')].ratio_to_cell_median < r.loc[lab, 'ratio_to_cell_median']).sum())}/25")
lo, hi = v.ratio_to_cell_median.min(), v.ratio_to_cell_median.max()
YLIM = (math.floor((lo - 0.05) * 10) / 10, math.ceil((hi + 0.03) * 10) / 10)
assert v.ratio_to_cell_median.between(*YLIM).all()
print(f"ratio range in data {lo:.4f} .. {hi:.4f}; y axis {YLIM[0]} .. {YLIM[1]} (all {len(v)} points inside)")

fs.apply()
fig, ax = fs.figure(height_mm=70)
ax.axhline(1.0, color="0.35", lw=0.8, ls=(0, (4, 2)), zorder=1)
c = v[v.series_type == "cell"]
ax.plot(c.x_plotted, c.ratio_to_cell_median, ls="none", color=CELL_GREY, marker="o", ms=3.2, mfc=CELL_GREY, mec="white",
        mew=0.3, zorder=2)
ax.plot(r.x_plotted, r.ratio_to_cell_median, ls="none", color=REG_COLOR, marker="D", ms=6.5, mfc=REG_COLOR, mec="white",
        mew=0.6, zorder=4)
for _, rr in r.iterrows():
    pct = 100 * (rr.ratio_to_cell_median - 1)
    ax.text(rr.x_plotted, rr.ratio_to_cell_median - 0.035, fs.tex(f"{pct:+.1f}%").replace("-", "−"),
            ha="center", va="top", fontsize=fs.FS_MIN, color="0.4", zorder=5)   # 8 pt is the style floor
for k in range(1, len(STATS)):
    ax.axvline(k - 0.5, color="0.88", lw=0.5, zorder=0)
ax.set_xticks(range(len(STATS)), [lab for _, lab in STATS])
ax.tick_params(axis="x", length=0)
ax.set_xlim(-0.5, len(STATS) - 0.5)
ax.set_ylim(*YLIM)
ax.set_yticks(np.round(np.arange(YLIM[0], YLIM[1] + 1e-9, 0.1), 1))
ax.set_xlabel("Precipitation statistic")
ax.set_ylabel("Ratio to median of 25 grid cells")
ax.grid(axis="y", alpha=0.25, linewidth=0.5)
ax.set_axisbelow(True)
handles = [Line2D([], [], ls="none", color=CELL_GREY, marker="o", ms=2.8, mfc=CELL_GREY, mec="white", mew=0.3,
                  label="Individual grid cells"),
           Line2D([], [], ls="none", color=REG_COLOR, marker="D", ms=4.5, mfc=REG_COLOR, mec="white", mew=0.6,
                  label="Regional mean")]
fig.legend(handles=handles, loc="outside upper center", ncol=2, handlelength=1.0, handletextpad=0.3,
           columnspacing=1.5, borderpad=0.1)
fs.save(fig, STEM, outdir=OUT)

v.to_csv(os.path.join(OUT, f"{STEM}_values.csv"), index=False, float_format="%.10g")
md5 = lambda f: hashlib.md5(open(f, "rb").read()).hexdigest()
print("md5 input CSV  ", md5(SRC), SRC)
print("md5 script     ", md5(os.path.abspath(__file__)))
print("md5 figure PDF ", md5(os.path.join(OUT, STEM + ".pdf")))
print("Saved", os.path.join(OUT, STEM + ".pdf"), "and", f"{STEM}_values.csv")
