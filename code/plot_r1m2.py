r"""
plot_r1m2.py — R1-M2: redraw of manuscript Figure 2 (five-seed test RMSE), shared revision style (fig_style.py).
No training; nothing is recomputed except the mean and SD of the saved per-seed RMSE values.

Data: results/final_all_seed_raw.csv (per-seed test RMSE of the original five-seed runs, seeds 42, 123, 7,
2024, 99; the source of Table 3 and of the original Figure 2). Mean and sample SD (ddof = 1) per model are
checked against results/final_5seed_point.csv before plotting.
Models (6): XGBoost, BiLSTM-Attention, BiLSTM-NoAttention, BU-LSTM, BU-LSTM-Attention, Prob. BiLSTM-Attention.
Output: results/figures/revision/r1M2_seed_rmse.pdf/.eps/.png and r1M2_seed_rmse_values.csv

Run (AutoDL):  cd /root/autodl-tmp && python3 code/plot_r1m2.py
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fig_style as fs  # noqa: E402

ROOT = next(r for r in ("results", "/root/autodl-tmp/results") if os.path.isdir(r))
OUT = os.path.join(ROOT, "figures", "revision")
ORDER = ["XGBoost", "BiLSTM-Attention", "BiLSTM-NoAttention", "BU-LSTM", "BU-LSTM-Attention",
         "Prob. BiLSTM-Attention"]
EXPECTED_COLOR = {"XGBoost": "#E69F00", "BiLSTM-Attention": "#0072B2", "BiLSTM-NoAttention": "#56B4E9",
                  "BU-LSTM": "#009E73", "BU-LSTM-Attention": "#D55E00", "Prob. BiLSTM-Attention": "#882255"}
SEEDS = {42, 123, 7, 2024, 99}


def pname(raw):
    return fs.name(str(raw).replace("(control)", "").strip())


raw = pd.read_csv(os.path.join(ROOT, "final_all_seed_raw.csv"))
raw["Model"] = raw["model"].map(pname)
assert set(raw["Model"]) == set(ORDER), sorted(set(raw["Model"]))
for m, g in raw.groupby("Model"):
    assert len(g) == 5 and set(g["seed"]) == SEEDS, f"{m}: seeds {sorted(g['seed'])}"
summ = raw.groupby("Model")["RMSE"].agg(mean="mean", sd=lambda v: v.std(ddof=1), n="count").loc[ORDER]

# check against the summary file used for Table 3 / original Figure 2
ref = pd.read_csv(os.path.join(ROOT, "final_5seed_point.csv"))
ref["Model"] = ref["Model"].map(pname)
ref = ref.set_index("Model").loc[ORDER]
assert np.allclose(summ["mean"], ref["RMSE_mean"], atol=1e-9), "mean differs from final_5seed_point.csv"
assert np.allclose(summ["sd"], ref["RMSE_std"], atol=1e-9), "SD differs from final_5seed_point.csv"
for m in ORDER:
    assert fs.color(m).upper() == EXPECTED_COLOR[m], f"{m}: colour {fs.color(m)}"
print("five-seed test RMSE (mm h-1), mean and sample SD (ddof=1); identical to final_5seed_point.csv:")
print(summ.round(6).to_string())

fs.apply()
fig, ax = fs.figure(height_mm=75)
fig.get_layout_engine().set(h_pad=6 / 72)   # extra margin (6 pt) so the three-line bottom label is clear of the edge
x = np.arange(len(ORDER))
for i, m in enumerate(ORDER):
    ax.errorbar(x[i], summ.loc[m, "mean"], yerr=summ.loc[m, "sd"], fmt=fs.marker(m), color=fs.color(m),
                markersize=5, elinewidth=1.2, capsize=3, capthick=1.2)
# horizontal two-line labels (split after the hyphen) instead of rotated text: easier to read at 100 %
LABEL = {m: (r"\shortstack{" + m.replace("-", r"-\\", 1) + "}") if m not in ("XGBoost", "BU-LSTM")
         else m for m in ORDER}
LABEL["BU-LSTM-Attention"] = r"\shortstack{BU-LSTM-\\Attention}"
LABEL["Prob. BiLSTM-Attention"] = r"\shortstack{Prob.\\BiLSTM-\\Attention}"
ax.set_xticks(x, [LABEL[m] for m in ORDER])
ax.set_xlim(-0.6, len(ORDER) - 0.4)
lo = float((summ["mean"] - summ["sd"]).min())
hi = float((summ["mean"] + summ["sd"]).max())
pad = 0.12 * (hi - lo)
ax.set_ylim(lo - pad, hi + pad)
ax.set_ylabel(f"RMSE ({fs.UNIT})")
ax.grid(axis="y", alpha=0.25, linewidth=0.5)
ax.set_axisbelow(True)
fs.save(fig, "r1M2_seed_rmse", outdir=OUT)
summ.assign(seeds="42,123,7,2024,99").to_csv(os.path.join(OUT, "r1M2_seed_rmse_values.csv"))
