# ============================================================
# Item 10 + 17: statistics of the SHAP results (zero training).
# Inputs : results/q10/shap/<arch>__s<seed>__{grouped,temporal}.npz (q10_shap.py)
#          results/metrics/q10_ablation_summary.csv (q10_ablation_stats.py)
# Subsets: "random" = 300 test windows drawn from the whole test set (typical conditions)
#          "upper"  = all 238 test windows with y >= Q95
# Global importance = mean |phi| over the samples of a subset (grouped, exact Shapley, mm).
# Uncertainty: SD across the five seeds (training randomness) and a cluster bootstrap over
#              calendar days of the explained samples (sampling randomness, 2,000 reps).
# Outputs: results/metrics/q10_shap_global.csv, q10_shap_signed.csv, q10_shap_rank_stability.csv,
#          q10_shap_vs_ablation.csv, q10_shap_temporal.csv
# ============================================================
import glob, os
from itertools import combinations
import numpy as np
import pandas as pd
from scipy.stats import kendalltau

ROOT = os.environ.get("Q10_ROOT", "/root/autodl-tmp")
SH, MET = f"{ROOT}/results/q10/shap", f"{ROOT}/results/metrics"
FEATURES = ["mxtpr", "mntpr", "lsp", "tcc", "v10", "sp", "d2m"]
SEEDS = [42, 123, 7, 2024, 99]
ARCHS = ["bilstm_attn", "bulstm_attn"]
N_BOOT, BSEED = 2000, 42
OLD_SHAP = {"tcc": 0.0089, "v10": 0.0086, "sp": 0.0083, "mntpr": 0.0081,   # manuscript L745-751
            "d2m": 0.0034, "mxtpr": 0.0029, "lsp": 0.0018}
ABL_SUBSET = {"random": "all", "upper": "upper_geQ95"}


def load(arch, seed, method):
    z = np.load(f"{SH}/{arch}__s{seed}__{method}.npz", allow_pickle=False)
    return {k: z[k] for k in z.files}


files = glob.glob(f"{SH}/*.npz")
assert len(files) == 20, f"expected 20 SHAP files, found {len(files)}"
ref = load(ARCHS[0], SEEDS[0], "grouped")
idx_ref = ref["explain_idx"]
for a in ARCHS:
    for s in SEEDS:
        for m in ("grouped", "temporal"):
            assert (load(a, s, m)["explain_idx"] == idx_ref).all(), "explained samples differ between files"
SUB = {"random": ref["is_random"], "upper": ref["is_upper"]}
days = pd.to_datetime(ref["t_explain"]).strftime("%Y-%m-%d").values
print(f"Explained samples: {len(idx_ref)} | random {SUB['random'].sum()} | upper {SUB['upper'].sum()} "
      f"| calendar days random {len(set(days[SUB['random']]))}, upper {len(set(days[SUB['upper']]))}")

rng = np.random.default_rng(BSEED)


def cluster_boot_idx(mask):
    """Bootstrap index sets that resample whole calendar days within a subset."""
    pos = np.where(mask)[0]
    groups = pd.Series(pos).groupby(days[pos]).apply(list).tolist()
    out = []
    for _ in range(N_BOOT):
        pick = rng.integers(0, len(groups), len(groups))
        out.append(np.concatenate([groups[g] for g in pick]))
    return out


BOOT = {s: cluster_boot_idx(m) for s, m in SUB.items()}

# ---------- global importance (grouped, exact) ----------
rows, signed = [], []
G = {a: np.stack([load(a, s, "grouped")["phi"] for s in SEEDS]) for a in ARCHS}   # (5, n, 7)
for a in ARCHS:
    for sub, mk in SUB.items():
        per_seed = np.abs(G[a][:, mk]).mean(1)                                   # (5, 7)
        mean_abs = np.abs(G[a]).mean(0)                                          # seed-averaged |phi| per sample
        boot = np.array([mean_abs[b].mean(0) for b in BOOT[sub]])                # (N_BOOT, 7)
        lo, hi = np.percentile(boot, [2.5, 97.5], axis=0)
        sg = G[a][:, mk].mean(1)                                                 # signed mean, per seed
        for j, f in enumerate(FEATURES):
            rows.append({"arch": a, "subset": sub, "feature": f, "n": int(mk.sum()),
                         "mean_abs_phi": per_seed[:, j].mean(), "sd_seeds": per_seed[:, j].std(ddof=1),
                         "boot_low": lo[j], "boot_high": hi[j],
                         **{f"s{s}": per_seed[k, j] for k, s in enumerate(SEEDS)}})
            signed.append({"arch": a, "subset": sub, "feature": f, "mean_signed_phi": sg[:, j].mean(),
                           "sd_seeds": sg[:, j].std(ddof=1),
                           "share_positive": float((G[a][:, mk, j] > 0).mean())})
glob_df = pd.DataFrame(rows)
glob_df["rank"] = glob_df.groupby(["arch", "subset"])["mean_abs_phi"].rank(ascending=False).astype(int)
glob_df.to_csv(f"{MET}/q10_shap_global.csv", index=False)
pd.DataFrame(signed).to_csv(f"{MET}/q10_shap_signed.csv", index=False)
pd.set_option("display.width", 220)
for a in ARCHS:
    for sub in SUB:
        t = glob_df[(glob_df.arch == a) & (glob_df.subset == sub)].sort_values("mean_abs_phi", ascending=False)
        print(f"\n===== Grouped SHAP | {a} | {sub} (n={t['n'].iloc[0]}) | mean |phi| in mm =====")
        print(t[["rank", "feature", "mean_abs_phi", "sd_seeds", "boot_low", "boot_high"]]
              .to_string(index=False, float_format=lambda v: f"{v:.5f}"))
sg = pd.DataFrame(signed)
print("\n===== Signed SHAP, seed mean (mm): upper vs random =====")
print(sg.pivot_table(index=["arch", "feature"], columns="subset", values="mean_signed_phi")
      .to_string(float_format=lambda v: f"{v:+.5f}"))

# ---------- ranking stability ----------
rk = []
for sub in SUB:
    for a in ARCHS:
        t = glob_df[(glob_df.arch == a) & (glob_df.subset == sub)].set_index("feature").loc[FEATURES]
        taus = [kendalltau(t[f"s{s1}"], t[f"s{s2}"]).statistic for s1, s2 in combinations(SEEDS, 2)]
        rk.append({"subset": sub, "comparison": f"{a}: between seeds (mean of 10 pairs)",
                   "kendall_tau": float(np.mean(taus)), "min": float(np.min(taus)), "max": float(np.max(taus))})
    ta = glob_df[(glob_df.arch == ARCHS[0]) & (glob_df.subset == sub)].set_index("feature").loc[FEATURES]
    tb = glob_df[(glob_df.arch == ARCHS[1]) & (glob_df.subset == sub)].set_index("feature").loc[FEATURES]
    rk.append({"subset": sub, "comparison": "bilstm_attn vs bulstm_attn (seed mean)",
               "kendall_tau": float(kendalltau(ta["mean_abs_phi"], tb["mean_abs_phi"]).statistic),
               "min": np.nan, "max": np.nan})
for a in ARCHS:
    ta = glob_df[(glob_df.arch == a) & (glob_df.subset == "random")].set_index("feature").loc[FEATURES]
    tb = glob_df[(glob_df.arch == a) & (glob_df.subset == "upper")].set_index("feature").loc[FEATURES]
    rk.append({"subset": "random vs upper", "comparison": f"{a}: typical vs upper-tail ranking",
               "kendall_tau": float(kendalltau(ta["mean_abs_phi"], tb["mean_abs_phi"]).statistic),
               "min": np.nan, "max": np.nan})
rank_df = pd.DataFrame(rk)
rank_df.to_csv(f"{MET}/q10_shap_rank_stability.csv", index=False)
print("\n===== SHAP ranking stability (Kendall tau over the 7 predictors) =====")
print(rank_df.to_string(index=False, float_format=lambda v: f"{v:.3f}"))

# ---------- SHAP vs ablation (same architecture, same five models) ----------
abl = pd.read_csv(f"{MET}/q10_ablation_summary.csv")
cmp_rows = []
for a in ARCHS:
    for sub, asub in ABL_SUBSET.items():
        s_ = glob_df[(glob_df.arch == a) & (glob_df.subset == sub)].set_index("feature").loc[FEATURES]
        b_ = abl[(abl.arch == a) & (abl.subset == asub)].set_index("removed").loc[FEATURES]
        tau = kendalltau(s_["mean_abs_phi"], b_["dRMSE_mean"]).statistic
        for f in FEATURES:
            cmp_rows.append({"arch": a, "shap_subset": sub, "ablation_subset": asub, "feature": f,
                             "shap_mean_abs_phi": s_.loc[f, "mean_abs_phi"], "shap_rank": int(s_.loc[f, "rank"]),
                             "ablation_dRMSE_mean": b_.loc[f, "dRMSE_mean"],
                             "ablation_rank": int(b_["dRMSE_mean"].rank(ascending=False)[f]),
                             "ablation_n_seeds_worse": int(b_.loc[f, "n_seeds_worse"]), "kendall_tau": tau})
cmp_df = pd.DataFrame(cmp_rows)
cmp_df.to_csv(f"{MET}/q10_shap_vs_ablation.csv", index=False)
print("\n===== SHAP (grouped) vs ablation, same models =====")
for (a, sub), t in cmp_df.groupby(["arch", "shap_subset"], sort=False):
    print(f"\n{a} | SHAP {sub} vs ablation {t['ablation_subset'].iloc[0]} | Kendall tau {t['kendall_tau'].iloc[0]:.3f}")
    print(t.sort_values("shap_rank")[["feature", "shap_rank", "shap_mean_abs_phi", "ablation_rank",
                                      "ablation_dRMSE_mean", "ablation_n_seeds_worse"]]
          .to_string(index=False, float_format=lambda v: f"{v:+.5f}"))

# ---------- temporal (42 players) ----------
trows = []
TP = {a: np.stack([load(a, s, "temporal")["phi"] for s in SEEDS]) for a in ARCHS}   # (5, n, 6, 7)
for a in ARCHS:
    for sub, mk in SUB.items():
        per_seed = np.abs(TP[a][:, mk]).mean(1)                                   # (5, 6, 7)
        for ti in range(6):
            for j, f in enumerate(FEATURES):
                trows.append({"arch": a, "subset": sub, "lag": f"t-{5 - ti}" if ti < 5 else "t",
                              "feature": f, "mean_abs_phi": per_seed[:, ti, j].mean(),
                              "sd_seeds": per_seed[:, ti, j].std(ddof=1)})
temp_df = pd.DataFrame(trows)
temp_df.to_csv(f"{MET}/q10_shap_temporal.csv", index=False)
print("\n===== Temporal SHAP, seed mean of mean |phi| (mm), random subset =====")
for a in ARCHS:
    t = temp_df[(temp_df.arch == a) & (temp_df.subset == "random")]
    print(f"\n{a}")
    print(t.pivot(index="feature", columns="lag", values="mean_abs_phi")[["t-5", "t-4", "t-3", "t-2", "t-1", "t"]]
          .loc[FEATURES].to_string(float_format=lambda v: f"{v:.4f}"))

# ---------- comparison with the original single-seed SHAP (same summary as the manuscript) ----------
p42 = load("bilstm_attn", 42, "temporal")
old_style = np.abs(p42["phi"][SUB["random"]]).mean((0, 1))      # mean over samples and time steps
print("\n===== Original-style summary (BiLSTM-Attention seed 42, mean |phi| over samples and time steps) =====")
for j in np.argsort(-old_style):
    f = FEATURES[j]
    print(f"{f:6s} new {old_style[j]:.4f} | manuscript {OLD_SHAP[f]:.4f}")
print("note: the manuscript used 100 random test windows, 50 background windows and one permutation; "
      "here 300 random windows, 50 background windows and 100 permutations")
print("===== q10 SHAP STATS COMPLETE =====")
