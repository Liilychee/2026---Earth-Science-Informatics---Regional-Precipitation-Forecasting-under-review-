# ============================================================
# Item 11 statistics: Gaussian vs censored Gaussian (tobit) vs Bernoulli-gamma, Probabilistic
# BiLSTM-Attention, main 70/15/15 split, five seeds.
# Main setting: tobit / bergamma trained with exact zeros (dry 0); every distribution verified
# against the raw ERA5 target (only numerical zeros |y| <= 1e-6 set to 0). Sensitivity: dry 0.001.
#   A. seed mean +- SD of every score (overall / wet >= 0.1 / upper >= Q95)
#   B. seed-paired differences vs Gaussian (and bergamma vs tobit): mean, seed t 95% interval,
#      number of seeds in which the alternative is better
#   C. paired moving-block bootstrap of the seed-averaged per-sample scores
#      (28-sample = 7-day blocks, 5,000 replicates, seed 42): CRPS, interval score, coverage,
#      Brier scores, squared error
#   D. dry 0.001 vs dry 0 (training definition sensitivity)
# Inputs : results/q11/runs/*.json, results/q11/preds/*.csv
# Outputs: results/metrics/q11_per_seed.csv, q11_summary.csv, q11_paired_seed.csv,
#          q11_paired_bootstrap.csv, q11_stats_output.txt
# ============================================================
import glob, json, os
import numpy as np
import pandas as pd
from scipy.stats import t as tdist, norm, gamma as gamma_dist

ROOT = os.environ.get("Q11_ROOT", "/root/autodl-tmp")
IN, MET = f"{ROOT}/results/q11", f"{ROOT}/results/metrics"
SEEDS = [42, 123, 7, 2024, 99]
Q95, WET, ZERO_TOL = 0.574048, 0.1, 1e-6
LEVELS = np.round(np.arange(0.005, 1.0, 0.005), 3)
N_BOOT, BSEED, BLOCK = 5000, 42, 28
CONFIGS = {"Gaussian": "gaussian", "Tobit": "tobit__dry0", "Bernoulli-gamma": "bergamma__dry0",
           "Tobit (dry 0.001)": "tobit__dry0.001", "Bernoulli-gamma (dry 0.001)": "bergamma__dry0.001"}
MAIN = ["Gaussian", "Tobit", "Bernoulli-gamma"]
lines = []
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)


def say(s=""):
    print(s); lines.append(str(s))


# ---------- A. per-seed scores from the run files (verification target: raw, key dry0) ----------
rows = []
for lab, pre in CONFIGS.items():
    for s in SEEDS:
        p = f"{IN}/runs/{pre}__s{s}.json"
        if not os.path.exists(p):
            say(f"MISSING {p}"); continue
        j = json.load(open(p))
        r = {"config": lab, "seed": s, "best_epoch": j["best_epoch"], "epochs": j["epochs_trained"],
             "finite": j["finite_losses"]}
        r.update(j["test"]["dry0"])
        rows.append(r)
per = pd.DataFrame(rows)
per.to_csv(f"{MET}/q11_per_seed.csv", index=False)
KEYS = ["rmse", "mae", "crps_all", "crps_wet", "crps_upper", "is95_all", "is95_wet", "is95_upper",
        "picp95_all", "picp95_wet", "picp95_upper", "picp90_all", "picp90_wet", "picp90_upper",
        "width95_all", "width95_wet", "width95_upper", "above95_upper", "neg_lower95",
        "brier_gt0.1", "brier_geQ95", "brier_ge1.0", "max_pred_mean", "best_epoch"]
g = per.groupby("config")[KEYS]
summ = g.mean().add_suffix("_mean").join(g.std(ddof=1).add_suffix("_sd")).reindex(list(CONFIGS))
summ.to_csv(f"{MET}/q11_summary.csv")
say("===== A. test scores, seed mean ± SD (verification against raw ERA5 target) =====")
say(f"all runs finite: {bool(per.finite.all())}; n per config: {per.groupby('config').size().to_dict()}")
for block in (["rmse", "mae", "crps_all", "crps_wet", "crps_upper"],
              ["is95_all", "is95_wet", "is95_upper", "width95_all", "width95_wet", "width95_upper"],
              ["picp95_all", "picp95_wet", "picp95_upper", "picp90_all", "picp90_wet", "picp90_upper"],
              ["above95_upper", "neg_lower95", "brier_gt0.1", "brier_geQ95", "brier_ge1.0", "max_pred_mean"]):
    tab = pd.DataFrame({k: [f"{summ.loc[c, k + '_mean']:.4f} ± {summ.loc[c, k + '_sd']:.4f}" for c in summ.index]
                        for k in block}, index=summ.index)
    say(tab.to_string()); say()

# ---------- B. seed-paired differences ----------
def seed_paired(a, b, k):
    x = per[per.config == a].set_index("seed")[k]; y = per[per.config == b].set_index("seed")[k]
    d = (x - y).reindex(SEEDS).dropna()
    m, se = d.mean(), d.std(ddof=1) / np.sqrt(len(d))
    h = tdist.ppf(0.975, len(d) - 1) * se
    return m, m - h, m + h, d


LOWER_BETTER = {"rmse", "mae", "crps_all", "crps_wet", "crps_upper", "is95_all", "is95_wet", "is95_upper",
                "brier_gt0.1", "brier_geQ95", "brier_ge1.0", "neg_lower95"}
PAIRS = [("Tobit", "Gaussian"), ("Bernoulli-gamma", "Gaussian"), ("Bernoulli-gamma", "Tobit"),
         ("Tobit (dry 0.001)", "Tobit"), ("Bernoulli-gamma (dry 0.001)", "Bernoulli-gamma")]
prow = []
for a, b in PAIRS:
    for k in KEYS[:-1]:
        m, lo, hi, d = seed_paired(a, b, k)
        if k in LOWER_BETTER:
            better = int((d < 0).sum())
        elif k.startswith("picp"):
            nom = 0.95 if "95" in k else 0.90
            xa = per[per.config == a].set_index("seed")[k].reindex(SEEDS)
            xb = per[per.config == b].set_index("seed")[k].reindex(SEEDS)
            better = int(((xa - nom).abs() < (xb - nom).abs()).sum())     # closer to nominal
        else:
            better = np.nan
        prow.append({"a": a, "b": b, "metric": k, "diff_mean": m, "seed_t_low": lo, "seed_t_high": hi,
                     "n_seeds_a_better": better, "n": len(d)})
pair = pd.DataFrame(prow)
pair.to_csv(f"{MET}/q11_paired_seed.csv", index=False)
say("===== B. seed-paired differences (a − b), seed t 95% interval, seeds in which a is better =====")
say("     (for coverage: 'better' = closer to the nominal level)")
show = ["rmse", "crps_all", "crps_wet", "crps_upper", "is95_all", "is95_upper", "picp95_all", "picp95_wet",
        "picp95_upper", "width95_all", "width95_upper", "brier_gt0.1", "brier_geQ95", "brier_ge1.0"]
for a, b in PAIRS:
    t_ = pair[(pair.a == a) & (pair.b == b) & pair.metric.isin(show)].set_index("metric").loc[show]
    say(f"-- {a} − {b} --")
    for k, r in t_.iterrows():
        flag = "*" if (r.seed_t_low > 0 or r.seed_t_high < 0) else " "
        nb = "" if pd.isna(r.n_seeds_a_better) else f"  {int(r.n_seeds_a_better)}/{int(r.n)}"
        say(f"   {k:14s} {r.diff_mean:+.4f} [{r.seed_t_low:+.4f}, {r.seed_t_high:+.4f}]{flag}{nb}")
    say()

# ---------- C. paired block bootstrap on seed-averaged per-sample scores ----------
def sp(x):
    return np.log1p(np.exp(-np.abs(x))) + np.maximum(x, 0)


def quantiles(dist, df):
    lv = LEVELS[None, :]
    if dist == "gaussian":
        return df.par1.values[:, None] + df.par2.values[:, None] * norm.ppf(lv)
    if dist == "tobit":
        return np.maximum(0.0, df.par1.values[:, None] + df.par2.values[:, None] * norm.ppf(lv))
    p, a, b = df.par1.values[:, None], df.par2.values[:, None], df.par3.values[:, None]
    cond = np.clip((lv - (1 - p)) / p, 0, 1 - 1e-9)
    return np.where(lv <= (1 - p), 0.0, gamma_dist.ppf(cond, a, scale=b))


def per_sample(lab):
    pre = CONFIGS[lab]; dist = pre.split("__")[0]
    acc, y, t = None, None, None
    for s in SEEDS:
        df = pd.read_csv(f"{IN}/preds/{pre}__s{s}.csv").query("split == 'test'").reset_index(drop=True)
        yy = np.where(df.y_true.values <= ZERO_TOL, 0.0, df.y_true.values)
        Q = quantiles(dist, df)
        d = yy[:, None] - Q
        crps = 2 * np.mean(np.maximum(LEVELS * d, (LEVELS - 1) * d), axis=1)
        lo, hi = df.q025.values, df.q975.values
        cov = ((yy >= lo) & (yy <= hi)).astype(float)
        IS = (hi - lo) + 40 * ((lo - yy) * (yy < lo) + (yy - hi) * (yy > hi))
        sc = {"se": (df.y_pred_mean.values - yy) ** 2, "crps": crps, "is95": IS, "cov95": cov, "width95": hi - lo,
              "bs_gt0.1": (df["p_gt0.1"].values - (yy > 0.1)) ** 2,
              "bs_geQ95": (df["p_geQ95"].values - (yy >= Q95)) ** 2,
              "bs_ge1.0": (df["p_ge1.0"].values - (yy >= 1.0)) ** 2}
        if acc is None:
            acc, y, t = {k: v / len(SEEDS) for k, v in sc.items()}, yy, df.valid_time.values
        else:
            assert (df.valid_time.values == t).all()
            for k in acc:
                acc[k] += sc[k] / len(SEEDS)
    return acc, y


def boot_diff(a, b, mask, stat, rng_starts):
    """mean over the resampled blocks of a - b (mask applied inside); sqrt for squared error."""
    va, vb, mk = a[rng_starts], b[rng_starts], mask[rng_starts]
    cnt = mk.sum(axis=1)
    ma = (va * mk).sum(axis=1) / cnt; mb = (vb * mk).sum(axis=1) / cnt
    return (np.sqrt(ma) - np.sqrt(mb)) if stat == "se" else (ma - mb)


scores = {lab: per_sample(lab) for lab in CONFIGS}
y = scores["Gaussian"][1]
n = len(y)
rng = np.random.default_rng(BSEED)
nb = int(np.ceil(n / BLOCK))
starts = rng.integers(0, n - BLOCK + 1, size=(N_BOOT, nb))
idx = (starts[:, :, None] + np.arange(BLOCK)[None, None, :]).reshape(N_BOOT, -1)
subsets = {"all": np.ones(n, bool), "wet": y >= WET, "upper": y >= Q95}
brow = []
for a, b in PAIRS[:3]:
    sa, sb = scores[a][0], scores[b][0]
    for stat in ("se", "crps", "is95", "cov95", "width95", "bs_gt0.1", "bs_geQ95", "bs_ge1.0"):
        for sub, mk in subsets.items():
            if stat.startswith("bs_") and sub != "all":
                continue
            point = (np.sqrt(sa[stat][mk].mean()) - np.sqrt(sb[stat][mk].mean())) if stat == "se" \
                else sa[stat][mk].mean() - sb[stat][mk].mean()
            bd = boot_diff(sa[stat], sb[stat], mk.astype(float), stat, idx)
            lo, hi = np.percentile(bd, [2.5, 97.5])
            brow.append({"a": a, "b": b, "score": "rmse" if stat == "se" else stat, "subset": sub,
                         "n": int(mk.sum()), "diff": point, "boot_low": lo, "boot_high": hi})
boot = pd.DataFrame(brow)
boot.to_csv(f"{MET}/q11_paired_bootstrap.csv", index=False)
say(f"===== C. paired moving-block bootstrap, seed-averaged scores (block {BLOCK}, {N_BOOT} replicates) =====")
for a, b in PAIRS[:3]:
    say(f"-- {a} − {b} --")
    for _, r in boot[(boot.a == a) & (boot.b == b)].iterrows():
        flag = "*" if (r.boot_low > 0 or r.boot_high < 0) else " "
        say(f"   {r.score:9s} {r.subset:6s} (n={r.n:4d}) {r['diff']:+.4f} [{r.boot_low:+.4f}, {r.boot_high:+.4f}]{flag}")
say()
say("note: Gaussian 5-seed test RMSE here vs Table 4 of the manuscript (different seeding helper):",)
say(f"      {summ.loc['Gaussian', 'rmse_mean']:.4f} ± {summ.loc['Gaussian', 'rmse_sd']:.4f}")
open(f"{MET}/q11_stats_output.txt", "w").write("\n".join(lines) + "\n")
say("===== q11 STATS COMPLETE =====")
