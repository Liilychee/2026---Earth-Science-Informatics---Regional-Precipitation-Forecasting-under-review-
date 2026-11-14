r"""
plot_r1m3.py — R1-M3: redraw of manuscript Figure 5 (empirical coverage of the nominal 95% prediction
interval), shared revision style (fig_style.py). No training, no recomputation of any coverage value.

Original figure: notebook Interpretable_analysis.ipynb, cell 28, plot_fig3_coverage(); data
results/final_stratified_probabilistic.csv (single saved test predictions of the three Gaussian models).
Changes: categorical point plot (markers only, no connecting lines) with four subsets:
  All                   final_stratified_probabilistic.csv, Regime "All"        (original value)
  Legacy wet (>0)       final_stratified_probabilistic.csv, Regime "Wet"        (original value, original definition)
  Wet (>=0.1)           results/metrics/q03b_wet_definition_interval.csv, "Wet (>=0.1 mm)"  (existing result)
  Upper tail (>=Q95)    final_stratified_probabilistic.csv, Regime "Heavy_Q95"  (original value)
Check: q03b's All, Wet (>0) and Upper-tail rows must equal the original values (same saved predictions).
Output: results/figures/revision/r1M3_interval_coverage.pdf/.eps/.png and r1M3_interval_coverage_values.csv

Run (AutoDL):  cd /root/autodl-tmp && python3 code/plot_r1m3.py
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fig_style as fs  # noqa: E402

ROOT = next(r for r in ("results", "/root/autodl-tmp/results") if os.path.isdir(r))
OUT = os.path.join(ROOT, "figures", "revision")
MODELS_RAW = ["BU-LSTM", "BU-LSTM-Attention (proposed)", "Probabilistic BiLSTM-Attention"]   # order of cell 28
CATS = [("All", "orig", "All"), (fs.LEGACY_WET, "orig", "Wet"), (fs.WET_SHORT, "q03b", "Wet (>=0.1 mm)"),
        (fs.UPPER_TAIL, "orig", "Heavy_Q95")]
EXPECTED_N = {"All": 3939, "Wet": 3228, "Wet (>=0.1 mm)": 854, "Heavy_Q95": 238}

orig = pd.read_csv(os.path.join(ROOT, "final_stratified_probabilistic.csv"))
q03b = pd.read_csv(os.path.join(ROOT, "metrics", "q03b_wet_definition_interval.csv"))


def get(df, col, model, key):
    r = df[(df["Model"] == model) & (df[col] == key)]
    assert len(r) == 1, f"{model} / {key}: {len(r)} rows"
    return float(r["Coverage95"].iloc[0]), int(r["N"].iloc[0])


# consistency: q03b uses the same saved predictions, so its All / >0 / upper-tail rows equal the originals
for m in MODELS_RAW:
    for k_o, k_q in (("All", "All"), ("Wet", "Wet (>0 mm)"), ("Heavy_Q95", "Upper tail (>=Q95=0.574)")):
        a, na = get(orig, "Regime", m, k_o)
        b, nb = get(q03b, "Subset", m, k_q)
        assert abs(a - b) < 1e-12 and na == nb, f"{m} {k_o}: original {a} (n={na}) vs q03b {b} (n={nb})"

rows = []
for m in MODELS_RAW:
    for lab, src, key in CATS:
        v, n = get(orig, "Regime", m, key) if src == "orig" else get(q03b, "Subset", m, key)
        assert n == EXPECTED_N[key], f"{m} {key}: N={n}"
        rows.append({"Model": fs.name(m), "Subset": key, "Source": src, "N": n, "Coverage95": v})
vals = pd.DataFrame(rows)
print("Empirical coverage of the nominal 95% interval (single saved runs; no value recomputed):")
print(vals.pivot(index="Model", columns="Subset", values="Coverage95")
      [["All", "Wet", "Wet (>=0.1 mm)", "Heavy_Q95"]].round(4).to_string())

fs.apply()
fig, ax = fs.figure(height_mm=72)
x = np.arange(len(CATS))
dx = 0.16                                     # horizontal offset so the three models do not overlap
for i, m in enumerate(MODELS_RAW):
    n = fs.name(m)
    v = vals[vals.Model == n].set_index("Subset").loc[[k for _, _, k in CATS], "Coverage95"].to_numpy()
    ax.plot(x + (i - 1) * dx, v, linestyle="none", marker=fs.marker(n), markersize=5.5,
            color=fs.color(n), label=n)
ax.axhline(0.95, color="black", lw=0.9, ls=(0, (4, 3)), zorder=0, label=r"Nominal 95\%")
ax.set_xticks(x, [lab for lab, _, _ in CATS])
ax.set_xlim(-0.5, len(CATS) - 0.5)
ax.set_ylim(0, 1.03)                          # as in the original figure
ax.set_ylabel(r"Empirical 95\% coverage")   # \% : a bare % starts a LaTeX comment
ax.grid(axis="y", alpha=0.25, linewidth=0.5)
ax.set_axisbelow(True)
ax.legend(loc="lower left", handlelength=2.0)
fs.save(fig, "r1M3_interval_coverage", outdir=OUT)
vals.to_csv(os.path.join(OUT, "r1M3_interval_coverage_values.csv"), index=False)
