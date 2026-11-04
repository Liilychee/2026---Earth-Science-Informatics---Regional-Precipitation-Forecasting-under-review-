# ============================================================
# Item 10 + 17: statistics of the leave-one-feature-out ablation (zero training).
# Reads results/q10/runs/*.json and results/q10/preds/*.csv written by q10_train.py.
#   - full-model five-seed mean vs Table 3 of the manuscript
#   - per-seed paired dRMSE = RMSE(without feature) - RMSE(full), three subsets
#   - seed-level mean, SD, t-interval, number of seeds with dRMSE > 0
#   - moving-block bootstrap (block 28 = 7 days, 10,000 reps) of the seed-averaged dRMSE
#   - ranking stability: Kendall tau between seeds and between architectures
#   - reproduction of the original BU-LSTM-Attention ablation (seed 42, Step 20)
# Outputs: results/metrics/q10_ablation_runs.csv, q10_ablation_summary.csv,
#          q10_ablation_rank_stability.csv, q10_training_cost.csv
# ============================================================
import glob, json, os
from itertools import combinations
import numpy as np
import pandas as pd
from scipy.stats import kendalltau, t as tdist

ROOT = os.environ.get("Q10_ROOT", "/root/autodl-tmp")
OUT, MET = f"{ROOT}/results/q10", f"{ROOT}/results/metrics"
FEATURES = ["mxtpr", "mntpr", "lsp", "tcc", "v10", "sp", "d2m"]
SEEDS = [42, 123, 7, 2024, 99]
ARCHS = ["bilstm_attn", "bulstm_attn"]
Q95, WET = 0.574048, 0.1
N_BOOT, BLOCK, BSEED = 10000, 28, 42
TABLE3 = {"bilstm_attn": (0.2429, 0.0010), "bulstm_attn": (0.2469, 0.0021)}       # manuscript Table 3
OLD_BU_S42 = {"tcc": 0.007438, "sp": 0.002315, "v10": 0.001640, "lsp": -0.000769,  # notebook Step 20
              "d2m": -0.000782, "mntpr": -0.001259, "mxtpr": -0.001922}
OLD_BU_5SEED = {"no_tcc": 0.250819, "no_mxtpr": 0.245369}                           # notebook targeted 5-seed
os.makedirs(MET, exist_ok=True)

# ---------- load ----------
SINGLE = ["full"] + [f"no_{f}" for f in FEATURES]
metas = [json.load(open(p)) for p in sorted(glob.glob(f"{OUT}/runs/*.json"))]
metas = [m for m in metas if m["config"] in SINGLE]          # group ablations are analysed in q10_group_stats.py
assert len(metas) == 80, f"expected 80 runs, found {len(metas)}"
runs = pd.DataFrame([{"arch": m["arch"], "config": m["config"], "seed": m["seed"], "tag": m["tag"],
                      "best_epoch": m["best_epoch"], "epochs_trained": m["epochs_trained"],
                      "train_seconds": m["train_seconds"], "gpu": m["gpu"], "tf": m["tf"]} for m in metas])
CONFIGS = ["full"] + [f"no_{f}" for f in FEATURES]
assert set(runs.groupby(["arch", "config"]).size()) == {5}, "every arch/config needs 5 seeds"

err, y_ref, t_ref = {}, None, None
for m in metas:
    d = pd.read_csv(f"{OUT}/preds/{m['tag']}.csv", parse_dates=["valid_time"])
    d = d[d["split"] == "test"].reset_index(drop=True)
    if y_ref is None:
        y_ref, t_ref = d["y_true"].values, d["valid_time"].values
    assert (d["valid_time"].values == t_ref).all() and np.abs(d["y_true"].values - y_ref).max() < 1e-6
    err[(m["arch"], m["config"], m["seed"])] = d["y_pred_mean"].values - y_ref
n = len(y_ref)
SUBSETS = {"all": np.ones(n, bool), "wet_ge0.1": y_ref >= WET, "upper_geQ95": y_ref >= Q95}
print(f"Test samples: {n} | wet>=0.1: {SUBSETS['wet_ge0.1'].sum()} | >=Q95: {SUBSETS['upper_geQ95'].sum()}")


def rmse(e, mask):
    return float(np.sqrt(np.mean(e[mask] ** 2)))


# ---------- per-run metrics ----------
rows = []
for (a, c, s), e in err.items():
    r = {"arch": a, "config": c, "seed": s}
    for sub, mk in SUBSETS.items():
        r[f"RMSE_{sub}"] = rmse(e, mk)
    rows.append(r)
per_run = runs.merge(pd.DataFrame(rows), on=["arch", "config", "seed"]).sort_values(["arch", "config", "seed"])
per_run.to_csv(f"{MET}/q10_ablation_runs.csv", index=False)

# ---------- full model vs Table 3 ----------
print("\n===== Full model, five seeds (test RMSE, all samples) =====")
for a in ARCHS:
    v = per_run[(per_run.arch == a) & (per_run.config == "full")].set_index("seed").loc[SEEDS, "RMSE_all"]
    m3, s3 = TABLE3[a]
    print(f"{a:12s} seeds { {int(k): round(float(x), 6) for k, x in v.items()} } | mean {v.mean():.6f} +/- {v.std(ddof=1):.6f} "
          f"| Table 3 {m3:.4f} +/- {s3:.4f} | diff {v.mean() - m3:+.6f}")

# ---------- block bootstrap indices (moving blocks over the full test series) ----------
rng = np.random.default_rng(BSEED)
nb = int(np.ceil(n / BLOCK))
starts = rng.integers(0, n - BLOCK + 1, size=(N_BOOT, nb))


def boot_rmse(e, mask):
    """RMSE of every bootstrap resample, restricted to `mask`, via cumulative block sums."""
    cs_e = np.concatenate([[0.0], np.cumsum(np.where(mask, e ** 2, 0.0))])
    cs_m = np.concatenate([[0.0], np.cumsum(mask.astype(float))])
    se = (cs_e[starts + BLOCK] - cs_e[starts]).sum(1)
    sm = (cs_m[starts + BLOCK] - cs_m[starts]).sum(1)
    return np.sqrt(se / np.maximum(sm, 1))


# ---------- dRMSE summaries ----------
tcrit = tdist.ppf(0.975, df=len(SEEDS) - 1)
summ = []
for a in ARCHS:
    for sub, mk in SUBSETS.items():
        full_seed = np.array([rmse(err[(a, "full", s)], mk) for s in SEEDS])
        full_boot = {s: boot_rmse(err[(a, "full", s)], mk) for s in SEEDS}
        for f in FEATURES:
            c = f"no_{f}"
            d_seed = np.array([rmse(err[(a, c, s)], mk) for s in SEEDS]) - full_seed
            d_boot = np.mean([boot_rmse(err[(a, c, s)], mk) - full_boot[s] for s in SEEDS], axis=0)
            lo_b, hi_b = np.percentile(d_boot, [2.5, 97.5])
            mean, sd = d_seed.mean(), d_seed.std(ddof=1)
            summ.append({"arch": a, "subset": sub, "removed": f, "n": int(mk.sum()),
                         "RMSE_full_mean": full_seed.mean(), "dRMSE_mean": mean, "dRMSE_sd": sd,
                         "seed_t_low": mean - tcrit * sd / np.sqrt(len(SEEDS)),
                         "seed_t_high": mean + tcrit * sd / np.sqrt(len(SEEDS)),
                         "n_seeds_worse": int((d_seed > 0).sum()),
                         "boot_low": lo_b, "boot_high": hi_b,
                         "boot_significant": bool(lo_b > 0 or hi_b < 0),
                         **{f"dRMSE_s{s}": v for s, v in zip(SEEDS, d_seed)}})
summary = pd.DataFrame(summ)
summary.to_csv(f"{MET}/q10_ablation_summary.csv", index=False)
pd.set_option("display.width", 220)
cols = ["removed", "n", "dRMSE_mean", "dRMSE_sd", "seed_t_low", "seed_t_high", "n_seeds_worse",
        "boot_low", "boot_high", "boot_significant"]
for a in ARCHS:
    for sub in SUBSETS:
        t = summary[(summary.arch == a) & (summary.subset == sub)].sort_values("dRMSE_mean", ascending=False)
        print(f"\n===== {a} | {sub} | full-model RMSE {t['RMSE_full_mean'].iloc[0]:.5f} | dRMSE = without - full =====")
        print(t[cols].to_string(index=False, float_format=lambda v: f"{v:+.5f}"))

# ---------- ranking stability ----------
rk = []
for sub in SUBSETS:
    for a in ARCHS:
        t = summary[(summary.arch == a) & (summary.subset == sub)].set_index("removed").loc[FEATURES]
        taus = [kendalltau(t[f"dRMSE_s{s1}"], t[f"dRMSE_s{s2}"]).statistic for s1, s2 in combinations(SEEDS, 2)]
        rk.append({"subset": sub, "comparison": f"{a}: between seeds (mean of 10 pairs)",
                   "kendall_tau": float(np.mean(taus)), "min": float(np.min(taus)), "max": float(np.max(taus))})
    ta = summary[(summary.arch == "bilstm_attn") & (summary.subset == sub)].set_index("removed").loc[FEATURES]
    tb = summary[(summary.arch == "bulstm_attn") & (summary.subset == sub)].set_index("removed").loc[FEATURES]
    rk.append({"subset": sub, "comparison": "bilstm_attn vs bulstm_attn (mean dRMSE)",
               "kendall_tau": float(kendalltau(ta["dRMSE_mean"], tb["dRMSE_mean"]).statistic),
               "min": np.nan, "max": np.nan})
rank = pd.DataFrame(rk)
rank.to_csv(f"{MET}/q10_ablation_rank_stability.csv", index=False)
print("\n===== Ranking stability (Kendall tau of dRMSE across the 7 features) =====")
print(rank.to_string(index=False, float_format=lambda v: f"{v:.3f}"))

# ---------- reproduction of the original BU-LSTM-Attention ablation ----------
print("\n===== Reproduction of the original ablation (BU-LSTM-Attention) =====")
full42 = rmse(err[("bulstm_attn", "full", 42)], SUBSETS["all"])
for f, old in OLD_BU_S42.items():
    new = rmse(err[("bulstm_attn", f"no_{f}", 42)], SUBSETS["all"]) - full42
    print(f"seed 42 without {f:5s}: new dRMSE {new:+.6f} | Step 20 {old:+.6f} | diff {new - old:+.6f}")
for c, old in OLD_BU_5SEED.items():
    v = per_run[(per_run.arch == "bulstm_attn") & (per_run.config == c)]["RMSE_all"]
    print(f"five-seed mean {c:9s}: new {v.mean():.6f} | targeted 5-seed run {old:.6f} | diff {v.mean() - old:+.6f}")

# ---------- training cost ----------
cost = per_run.groupby("arch").agg(runs=("tag", "size"), gpu=("gpu", "first"), tf=("tf", "first"),
                                   mean_seconds=("train_seconds", "mean"), median_seconds=("train_seconds", "median"),
                                   mean_epochs=("epochs_trained", "mean"), mean_best_epoch=("best_epoch", "mean"))
cost.to_csv(f"{MET}/q10_training_cost.csv")
print("\n===== Training cost (8 jobs in parallel on one GPU, so per-run times are inflated) =====")
print(cost.to_string(float_format=lambda v: f"{v:.1f}"))
print("===== q10 ABLATION STATS COMPLETE =====")
