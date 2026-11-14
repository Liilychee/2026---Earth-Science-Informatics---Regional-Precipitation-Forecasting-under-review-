r"""
plot_r1m4.py — R1-M4: two-architecture SHAP attribution (Fig. A) and ablation (Fig. B) from the q10
experiment, shared revision style (fig_style.py). No training; no statistic is recomputed: every plotted
number is read from the saved q10 summary files. The script only CHECKS internal consistency.

Fig. A  r1M4_shap_comparison      results/metrics/q10_shap_global.csv
        Grouped exact Shapley values (7 players = 7 predictors, the 6 time steps of a predictor move
        together; NOT the 42-player temporal SHAP), mean |phi| in mm h-1 over the explained samples,
        averaged over the five seeds.
        Thick bar (no caps) = seed mean +- 1 SD across seeds (column sd_seeds).
        Thin line with caps  = calendar-day cluster bootstrap 95% interval, 2,000 resamples (boot_low/high).
        Random (n = 300) and Upper tail (y >= training Q95, n = 238) share 19 samples (checked in the npz).
Fig. B  r1M4_ablation_comparison  results/metrics/q10_ablation_summary.csv, q10_group_ablation.csv
        dRMSE = RMSE(model without predictor[s]) - RMSE(q10 full model), mean over five seeds, mm h-1.
        Controls are the q10 full models (NOT Table 3).
        Thick bar (no caps) = seed t-interval, 95%, df = 4 (seed_t_low/high).
        Thin line with caps  = moving-block bootstrap 95% interval, block 28 samples (7 days), 10,000
        resamples, per-seed paired differences averaged over seeds (boot_low/high).
        The boot_significant column is NOT used.
Outputs (results/figures/revision/): both figures as .pdf/.eps/.png, r1M4_shap_comparison_audit.csv,
r1M4_ablation_comparison_audit.csv, r1M4_audit.txt.

Run (AutoDL):  cd /root/autodl-tmp && python3 code/plot_r1m4.py
"""
import glob
import os
import sys

import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fig_style as fs  # noqa: E402

ROOT = next(r for r in ("results", "/root/autodl-tmp/results") if os.path.isdir(r))
MET = os.path.join(ROOT, "metrics")
OUT = os.path.join(ROOT, "figures", "revision")
os.makedirs(OUT, exist_ok=True)
ARCHS = ["bilstm_attn", "bulstm_attn"]
FEATURES = ["mxtpr", "mntpr", "lsp", "tcc", "v10", "sp", "d2m"]          # fixed order in every panel
GROUPS = ["mxtpr+mntpr", "mxtpr+mntpr+lsp"]
SEEDS = [42, 123, 7, 2024, 99]
log = []


def note(s):
    print(s)
    log.append(s)


# =================================================================== checks on the saved files
shap = pd.read_csv(os.path.join(MET, "q10_shap_global.csv"))
shap["src_row"] = shap.index + 2                                          # line number in the CSV file
assert len(shap) == 28 and set(shap.arch) == set(ARCHS) and set(shap.subset) == {"random", "upper"}
assert set(shap.feature) == set(FEATURES)
for (a, s), g in shap.groupby(["arch", "subset"]):
    assert len(g) == 7 and g.n.nunique() == 1
    assert int(g.n.iloc[0]) == {"random": 300, "upper": 238}[s], (a, s, g.n.iloc[0])
    m = g[[f"s{k}" for k in SEEDS]].mean(axis=1)
    assert np.allclose(m, g.mean_abs_phi, atol=1e-12), "mean_abs_phi is not the seed mean"
    assert ((g.boot_low <= g.mean_abs_phi) & (g.mean_abs_phi <= g.boot_high)).all()
    assert (g["rank"].to_numpy() == g.mean_abs_phi.rank(ascending=False).astype(int).to_numpy()).all()
note("q10_shap_global.csv: 28 rows (2 architectures x 2 subsets x 7 predictors); n = 300 random, 238 upper; "
     "mean_abs_phi = mean of the five seed columns; ranks consistent; unit mm h-1 (q10_shap.py inverse-scales "
     "the model output).")

# overlap of the explained subsets, from the saved grouped-SHAP npz files (all ten must agree)
npz = sorted(glob.glob(os.path.join(ROOT, "q10", "shap", "*__grouped.npz")))
if npz:
    ref_idx = None
    for f in npz:
        z = np.load(f, allow_pickle=True)
        up, rd, idx = z["is_upper"], z["is_random"], z["explain_idx"]
        assert int(up.sum()) == 238 and int(rd.sum()) == 300 and int((up & rd).sum()) == 19, f
        assert int((~up & ~rd).sum()) == 0 and len(idx) == 519, f
        ref_idx = idx if ref_idx is None else ref_idx
        assert (idx == ref_idx).all(), f"{f}: different explained samples"
    note(f"grouped-SHAP npz ({len(npz)} files): identical 519 explained samples; upper 238, random 300, "
         f"overlap 19 (the subsets are NOT disjoint).")
else:
    note("grouped-SHAP npz not found: overlap of 19 samples taken from the 2026-11-12 check (not re-verified here).")

abl = pd.read_csv(os.path.join(MET, "q10_ablation_summary.csv"))
abl["src_file"], abl["src_row"] = "q10_ablation_summary.csv", abl.index + 2
grp = pd.read_csv(os.path.join(MET, "q10_group_ablation.csv"))
grp["src_file"], grp["src_row"] = "q10_group_ablation.csv", grp.index + 2
SUBS_B = {"all": 3939, "upper_geQ95": 238}
for df in (abl, grp):
    d = df[df.subset.isin(SUBS_B)]
    m = d[[f"dRMSE_s{k}" for k in SEEDS]].mean(axis=1)
    assert np.allclose(m, d.dRMSE_mean, atol=1e-12), "dRMSE_mean is not the seed mean"
    assert (d.n == d.subset.map(SUBS_B)).all()
    assert ((d.seed_t_low <= d.dRMSE_mean + 1e-12) & (d.dRMSE_mean <= d.seed_t_high + 1e-12)).all()
ctrl = {}
for a in ARCHS:
    for s in SUBS_B:
        v = pd.concat([abl[(abl.arch == a) & (abl.subset == s)].RMSE_full_mean,
                       grp[(grp.arch == a) & (grp.subset == s)].RMSE_full_mean]).unique()
        assert len(v) == 1, (a, s, v)
        ctrl[(a, s)] = float(v[0])
note("q10 full-model controls (five-seed mean RMSE, mm h-1; used as the reference of every dRMSE, NOT the "
     "Table 3 values): " + "; ".join(f"{fs.name(a)} {s} {v:.6f}" for (a, s), v in ctrl.items()))
note("Table 3 for comparison: BiLSTM-Attention 0.2429 (same runs), BU-LSTM-Attention 0.2469 (different "
     "runs: q10 = 0.247207).")

# =================================================================== plotting helpers
fs.apply()
LEG = [Line2D([], [], color="0.2", marker="o", linestyle="none", markersize=4, label="Seed mean"),
       Line2D([], [], color="0.2", lw=3.2, alpha=0.45, solid_capstyle="butt", label="")]
BOOT_HANDLE = Line2D([], [], color="0.2", lw=0.8, marker="|", markersize=5, markeredgewidth=0.8, label="")


def draw(ax, y, mean, lo_thick, hi_thick, lo_thin, hi_thin, col, mk):
    ax.plot([lo_thick, hi_thick], [y, y], color=col, lw=3.2, alpha=0.45, solid_capstyle="butt", zorder=2)
    ax.errorbar(mean, y, xerr=[[mean - lo_thin], [hi_thin - mean]], fmt="none", ecolor=col, color=col,
                elinewidth=0.8, capsize=2.2, capthick=0.8, zorder=3)
    ax.plot(mean, y, marker=mk, color=col, markersize=4, linestyle="none", zorder=4)


def panel_title(ax, letter, text):
    ax.set_title(rf"{{\fontsize{{{fs.FS_PANEL}}}{{12}}\selectfont\textbf{{({letter})}}}} {text}", loc="left")


# =================================================================== Fig. A: SHAP
COLS_A = [("random", "Random (n = 300)"), ("upper", r"Upper tail (n = 238)")]
fig, axs = fs.figure(height_mm=112, nrows=2, ncols=2, sharey=True)
ypos = np.arange(len(FEATURES))[::-1]                                     # first predictor at the top
audit_a = []
for r, a in enumerate(ARCHS):
    col, mk = fs.color(a), fs.marker(a)
    for c, (s, ctitle) in enumerate(COLS_A):
        ax = axs[r, c]
        g = shap[(shap.arch == a) & (shap.subset == s)].set_index("feature").loc[FEATURES]
        for yv, f in zip(ypos, FEATURES):
            row = g.loc[f]
            draw(ax, yv, row.mean_abs_phi, row.mean_abs_phi - row.sd_seeds, row.mean_abs_phi + row.sd_seeds,
                 row.boot_low, row.boot_high, col, mk)
            audit_a.append({"figure": "r1M4_shap_comparison", "architecture": fs.name(a), "subset": s,
                            "n": int(row.n), "predictor": f, "mean_abs_phi_mm_h": row.mean_abs_phi,
                            "seed_sd": row.sd_seeds, "thick_low": row.mean_abs_phi - row.sd_seeds,
                            "thick_high": row.mean_abs_phi + row.sd_seeds, "boot_low": row.boot_low,
                            "boot_high": row.boot_high, "rank_in_panel": int(row["rank"]),
                            "source": f"q10_shap_global.csv line {int(row.src_row)}"})
        panel_title(ax, "abcd"[2 * r + c], ctitle)
        if c == 1:                                                        # architecture as a row label
            ax.yaxis.set_label_position("right")
            ax.set_ylabel(fs.name(a), rotation=270, labelpad=11)
        ax.set_yticks(ypos, FEATURES)
        ax.set_ylim(-0.6, len(FEATURES) - 0.4)
        ax.grid(axis="x", alpha=0.25, linewidth=0.5)
        ax.set_axisbelow(True)
for c in range(2):                                                        # same x range within a column
    lo = min(axs[r, c].get_xlim()[0] for r in range(2))
    hi = max(axs[r, c].get_xlim()[1] for r in range(2))
    for r in range(2):
        axs[r, c].set_xlim(0.0, hi)                                   # mean |phi| >= 0: axis starts at zero
    axs[1, c].set_xlabel(rf"Mean $|\phi|$ ({fs.UNIT})")
LEG[1].set_label(r"Seed mean $\pm$1 SD (5 seeds)")
BOOT_HANDLE.set_label("Calendar-day bootstrap 95\\% interval")
fig.legend(handles=[LEG[0], LEG[1], BOOT_HANDLE], loc="outside upper center", ncol=2, handlelength=1.8,
           columnspacing=1.5)
fs.save(fig, "r1M4_shap_comparison", outdir=OUT)

# =================================================================== Fig. B: ablation
COLS_B = [("all", "All (n = 3,939)"), ("upper_geQ95", r"Upper tail (n = 238)")]
ROWS_B = FEATURES + GROUPS
fig, axs = fs.figure(height_mm=125, nrows=2, ncols=2, sharey=True)
ypos = np.arange(len(ROWS_B))[::-1]
audit_b = []
for r, a in enumerate(ARCHS):
    col, mk = fs.color(a), fs.marker(a)
    for c, (s, ctitle) in enumerate(COLS_B):
        ax = axs[r, c]
        d = pd.concat([abl[(abl.arch == a) & (abl.subset == s)],
                       grp[(grp.arch == a) & (grp.subset == s)]]).set_index("removed").loc[ROWS_B]
        for yv, f in zip(ypos, ROWS_B):
            row = d.loc[f]
            draw(ax, yv, row.dRMSE_mean, row.seed_t_low, row.seed_t_high, row.boot_low, row.boot_high, col, mk)
            audit_b.append({"figure": "r1M4_ablation_comparison", "architecture": fs.name(a), "subset": s,
                            "n": int(row.n), "removed": f, "control_RMSE_q10_full": row.RMSE_full_mean,
                            "dRMSE_mm_h": row.dRMSE_mean, "seed_t_low": row.seed_t_low,
                            "seed_t_high": row.seed_t_high, "boot_low": row.boot_low,
                            "boot_high": row.boot_high, "n_seeds_worse": int(row.n_seeds_worse),
                            "source": f"{row.src_file} line {int(row.src_row)}"})
        ax.axvline(0, color="black", lw=0.7, zorder=1)
        ax.axhline(ypos[len(FEATURES) - 1] - 0.5, color="0.6", lw=0.5, ls=(0, (2, 2)))   # singles | groups
        panel_title(ax, "abcd"[2 * r + c], ctitle)
        if c == 1:
            ax.yaxis.set_label_position("right")
            ax.set_ylabel(fs.name(a), rotation=270, labelpad=11)
        ax.set_yticks(ypos, ROWS_B)
        ax.set_ylim(-0.6, len(ROWS_B) - 0.4)
        ax.grid(axis="x", alpha=0.25, linewidth=0.5)
        ax.set_axisbelow(True)
for c in range(2):
    lo = min(axs[r, c].get_xlim()[0] for r in range(2))
    hi = max(axs[r, c].get_xlim()[1] for r in range(2))
    for r in range(2):
        axs[r, c].set_xlim(lo, hi)
    axs[1, c].set_xlabel(rf"$\Delta$RMSE ({fs.UNIT})")
LEG[1].set_label("Seed $t$-interval, 95\\%")
BOOT_HANDLE.set_label("Moving-block bootstrap 95\\% interval")
fig.legend(handles=[LEG[0], LEG[1], BOOT_HANDLE], loc="outside upper center", ncol=2, handlelength=1.8,
           columnspacing=1.5)
fs.save(fig, "r1M4_ablation_comparison", outdir=OUT)

# =================================================================== audit files
pd.DataFrame(audit_a).to_csv(os.path.join(OUT, "r1M4_shap_comparison_audit.csv"), index=False)
pd.DataFrame(audit_b).to_csv(os.path.join(OUT, "r1M4_ablation_comparison_audit.csv"), index=False)
note("Fig. A uncertainty: thick = seed mean +- 1 SD (sd_seeds); thin with caps = calendar-day cluster "
     "bootstrap 95% (2,000 resamples). Fig. B uncertainty: thick = seed t-interval 95% (df = 4); thin with "
     "caps = moving-block bootstrap 95% (block 28 = 7 days, 10,000 resamples, per-seed paired differences "
     "averaged over seeds). boot_significant not used. Wet (>=0.1) rows of the ablation files not plotted.")
with open(os.path.join(OUT, "r1M4_audit.txt"), "w") as fh:
    fh.write("\n".join(log) + "\n")
