# ============================================================
# Item 10 + 17 (and 26): group ablation and group SHAP (zero training).
#   no_precip       : mxtpr, mntpr and lsp removed together
#   no_mxtpr_mntpr  : mxtpr and mntpr removed, lsp kept (R4 l.936-938)
# Ablation : paired dRMSE against the full model, five seeds, three subsets, seed t-interval
#            and moving-block bootstrap (as q10_ablation_stats.py); compared with the sum of
#            the single-feature dRMSE of the removed predictors.
# SHAP     : grouped_precip on the full models (precip = mxtpr+mntpr+lsp as one player) and
#            grouped SHAP on the no_mxtpr_mntpr models (is lsp the leading predictor?).
# Outputs  : results/metrics/q10_group_ablation.csv, q10_group_shap.csv, q10_reduced_shap.csv
# ============================================================
import glob, json, os
import numpy as np
import pandas as pd
from scipy.stats import t as tdist

ROOT = os.environ.get("Q10_ROOT", "/root/autodl-tmp")
OUT, MET = f"{ROOT}/results/q10", f"{ROOT}/results/metrics"
SEEDS = [42, 123, 7, 2024, 99]
ARCHS = ["bilstm_attn", "bulstm_attn"]
GROUPS = {"no_precip": ["mxtpr", "mntpr", "lsp"], "no_mxtpr_mntpr": ["mxtpr", "mntpr"]}
Q95, WET = 0.574048, 0.1
N_BOOT, BLOCK, BSEED = 10000, 28, 42
N_BOOT_SHAP = 2000
pd.set_option("display.width", 220)


def test_err(arch, config, seed):
    d = pd.read_csv(f"{OUT}/preds/{arch}__{config}__s{seed}.csv")
    d = d[d["split"] == "test"]
    return d["y_true"].values, d["y_pred_mean"].values - d["y_true"].values


for a in ARCHS:
    for c in ["full"] + list(GROUPS):
        for s in SEEDS:
            assert os.path.exists(f"{OUT}/runs/{a}__{c}__s{s}.json"), f"missing run {a} {c} {s}"
y, _ = test_err(ARCHS[0], "full", 42)
n = len(y)
SUBSETS = {"all": np.ones(n, bool), "wet_ge0.1": y >= WET, "upper_geQ95": y >= Q95}
rmse = lambda e, m: float(np.sqrt(np.mean(e[m] ** 2)))

rng = np.random.default_rng(BSEED)
starts = rng.integers(0, n - BLOCK + 1, size=(N_BOOT, int(np.ceil(n / BLOCK))))


def boot_rmse(e, mask):
    cs_e = np.concatenate([[0.0], np.cumsum(np.where(mask, e ** 2, 0.0))])
    cs_m = np.concatenate([[0.0], np.cumsum(mask.astype(float))])
    se = (cs_e[starts + BLOCK] - cs_e[starts]).sum(1)
    sm = (cs_m[starts + BLOCK] - cs_m[starts]).sum(1)
    return np.sqrt(se / np.maximum(sm, 1))


single = pd.read_csv(f"{MET}/q10_ablation_summary.csv")
tcrit = tdist.ppf(0.975, df=len(SEEDS) - 1)
rows = []
for a in ARCHS:
    E = {(c, s): test_err(a, c, s)[1] for c in ["full"] + list(GROUPS) for s in SEEDS}
    for sub, mk in SUBSETS.items():
        full = np.array([rmse(E[("full", s)], mk) for s in SEEDS])
        fb = {s: boot_rmse(E[("full", s)], mk) for s in SEEDS}
        for c, rem in GROUPS.items():
            dseed = np.array([rmse(E[(c, s)], mk) for s in SEEDS]) - full
            dboot = np.mean([boot_rmse(E[(c, s)], mk) - fb[s] for s in SEEDS], axis=0)
            lo, hi = np.percentile(dboot, [2.5, 97.5])
            ssum = single[(single.arch == a) & (single.subset == sub) & single.removed.isin(rem)]["dRMSE_mean"].sum()
            m_, sd = dseed.mean(), dseed.std(ddof=1)
            rows.append({"arch": a, "subset": sub, "config": c, "removed": "+".join(rem), "n": int(mk.sum()),
                         "RMSE_full_mean": full.mean(), "dRMSE_mean": m_, "dRMSE_sd": sd,
                         "seed_t_low": m_ - tcrit * sd / np.sqrt(5), "seed_t_high": m_ + tcrit * sd / np.sqrt(5),
                         "n_seeds_worse": int((dseed > 0).sum()), "boot_low": lo, "boot_high": hi,
                         "boot_significant": bool(lo > 0 or hi < 0), "sum_of_single_dRMSE": ssum,
                         **{f"dRMSE_s{s}": v for s, v in zip(SEEDS, dseed)}})
abl = pd.DataFrame(rows)
abl.to_csv(f"{MET}/q10_group_ablation.csv", index=False)
print("===== Group ablation: dRMSE = RMSE(without group) - RMSE(full) =====")
print(abl[["arch", "subset", "removed", "n", "dRMSE_mean", "dRMSE_sd", "seed_t_low", "seed_t_high",
           "n_seeds_worse", "boot_low", "boot_high", "sum_of_single_dRMSE"]]
      .to_string(index=False, float_format=lambda v: f"{v:+.5f}"))

# lsp given that mxtpr and mntpr are absent: no_precip minus no_mxtpr_mntpr (same seeds)
print("\n===== Incremental value of lsp when mxtpr and mntpr are absent (no_precip - no_mxtpr_mntpr) =====")
for a in ARCHS:
    for sub, mk in SUBSETS.items():
        d = np.array([rmse(test_err(a, "no_precip", s)[1], mk) - rmse(test_err(a, "no_mxtpr_mntpr", s)[1], mk)
                      for s in SEEDS])
        print(f"{a:12s} {sub:12s} dRMSE mean {d.mean():+.5f} sd {d.std(ddof=1):.5f} seeds worse {(d > 0).sum()}/5")


# ---------- SHAP ----------
def load(p):
    z = np.load(p, allow_pickle=False)
    return {k: z[k] for k in z.files}


def shap_table(pattern, label):
    out = []
    for a in ARCHS:
        Z = [load(pattern.format(a=a, s=s)) for s in SEEDS]
        names = [str(x) for x in Z[0]["player_names"]]
        sub = {"random": Z[0]["is_random"], "upper": Z[0]["is_upper"]}
        days = pd.to_datetime(Z[0]["t_explain"]).strftime("%Y-%m-%d").values
        phi = np.stack([z["phi"] for z in Z])                                   # (5, n, players)
        brng = np.random.default_rng(BSEED)
        for sn, mk in sub.items():
            per_seed = np.abs(phi[:, mk]).mean(1)
            pos = np.where(mk)[0]
            groups = pd.Series(pos).groupby(days[pos]).apply(list).tolist()
            ma = np.abs(phi).mean(0)
            boot = np.array([ma[np.concatenate([groups[g] for g in brng.integers(0, len(groups), len(groups))])].mean(0)
                             for _ in range(N_BOOT_SHAP)])
            lo, hi = np.percentile(boot, [2.5, 97.5], axis=0)
            order = np.argsort(-per_seed.mean(0))
            for r, j in enumerate(order, 1):
                out.append({"analysis": label, "arch": a, "subset": sn, "rank": r, "player": names[j],
                            "mean_abs_phi": per_seed[:, j].mean(), "sd_seeds": per_seed[:, j].std(ddof=1),
                            "boot_low": lo[j], "boot_high": hi[j],
                            "mean_signed_phi": phi[:, mk, j].mean()})
    return pd.DataFrame(out)


gs = shap_table(f"{OUT}/shap_groups/{{a}}__full__s{{s}}__grouped_precip.npz", "full model, precip grouped")
gs.to_csv(f"{MET}/q10_group_shap.csv", index=False)
rs = shap_table(f"{OUT}/shap_groups/{{a}}__no_mxtpr_mntpr__s{{s}}__grouped.npz", "model without mxtpr, mntpr")
rs.to_csv(f"{MET}/q10_reduced_shap.csv", index=False)
for t, title in ((gs, "Grouped SHAP with precip = mxtpr+mntpr+lsp (full models)"),
                 (rs, "Grouped SHAP of the models trained without mxtpr and mntpr")):
    print(f"\n===== {title} | mean |phi| in mm =====")
    for (a, sn), g in t.groupby(["arch", "subset"], sort=False):
        print(f"\n{a} | {sn}")
        print(g[["rank", "player", "mean_abs_phi", "sd_seeds", "boot_low", "boot_high", "mean_signed_phi"]]
              .to_string(index=False, float_format=lambda v: f"{v:+.5f}"))
print("===== q10 GROUP STATS COMPLETE =====")
