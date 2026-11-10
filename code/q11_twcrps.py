# ============================================================
# Item 11 add-on: threshold-weighted CRPS (Gneiting & Ranjan 2011) for the three predictive
# distributions. Conditioning the CRPS on observed wet / upper-tail cases is not a proper score
# (forecaster's dilemma, Lerch et al. 2017); the threshold-weighted CRPS keeps every test case
# and puts weight only on the part of the outcome range above a threshold r:
#     twCRPS_r(F, y) = integral_r^inf (F(z) - 1{y <= z})^2 dz
# Thresholds r = 0.1 mm/h (wet), Q95 = 0.574048, 1.0 mm/h. Predictive CDFs are analytic:
#     Gaussian F(z) = Phi((z - mu) / sigma); tobit F(z) = Phi((z - mu) / s) for z >= 0;
#     Bernoulli-gamma F(z) = (1 - p) + p G(z; a, b) for z > 0.
# The integral is evaluated on a fine grid from r to 8 mm/h (trapezoid rule; test maximum 2.99 mm/h).
# Check: twCRPS with r = 0 equals the full CRPS for the two non-negative distributions.
# 'full' = exact CRPS by the same integration (Gaussian from -4 mm/h), comparable with Table 4.
# Scores: seed mean +- SD; seed-paired differences (seed t 95% interval, seeds better);
# paired moving-block bootstrap of seed-averaged per-case scores (28 samples = 7 days, 5,000, seed 42).
# Inputs : results/q11/preds/*.csv (outputs of q11_train.py)
# Outputs: results/metrics/q11_twcrps_per_seed.csv, q11_twcrps_paired.csv, q11_twcrps_output.txt
# ============================================================
import os
import numpy as np
import pandas as pd
from scipy.stats import norm, gamma as gamma_dist, t as tdist

ROOT = os.environ.get("Q11_ROOT", "/root/autodl-tmp")
IN, MET = f"{ROOT}/results/q11", f"{ROOT}/results/metrics"
SEEDS = [42, 123, 7, 2024, 99]
ZERO_TOL, Q95 = 1e-6, 0.574048
THRESH = {"full": None, "r0.1": 0.1, "rQ95": Q95, "r1.0": 1.0}   # full = exact CRPS (no weighting)
ZMAX, NZ = 8.0, 3000
N_BOOT, BSEED, BLOCK = 5000, 42, 28
CONFIGS = {"Gaussian": "gaussian", "Tobit": "tobit__dry0", "Bernoulli-gamma": "bergamma__dry0",
           "Tobit (dry 0.001)": "tobit__dry0.001", "Bernoulli-gamma (dry 0.001)": "bergamma__dry0.001"}
PAIRS = [("Tobit", "Gaussian"), ("Bernoulli-gamma", "Gaussian"), ("Bernoulli-gamma", "Tobit"),
         ("Bernoulli-gamma (dry 0.001)", "Bernoulli-gamma")]
LEVELS = np.round(np.arange(0.005, 1.0, 0.005), 3)
TRAPZ = getattr(np, "trapezoid", None) or np.trapz          # numpy >= 2.0 / older
lines = []
pd.set_option("display.width", 220)


def say(s=""):
    print(s); lines.append(str(s))


def cdf(dist, df, z):
    """F(z) for every case (rows) on grid z (columns)."""
    if dist == "gaussian":
        return norm.cdf((z[None, :] - df.par1.values[:, None]) / df.par2.values[:, None])
    if dist == "tobit":
        F = norm.cdf((z[None, :] - df.par1.values[:, None]) / df.par2.values[:, None])
        return np.where(z[None, :] < 0, 0.0, F)
    p, a, b = df.par1.values[:, None], df.par2.values[:, None], df.par3.values[:, None]
    F = (1 - p) + p * gamma_dist.cdf(np.maximum(z[None, :], 0), a, scale=b)
    return np.where(z[None, :] < 0, 0.0, F)


def twcrps(dist, df, y, r):
    if r is None:                                           # exact CRPS: integrate over the whole support
        lo = -4.0 if dist == "gaussian" else 0.0
        z = np.concatenate([np.linspace(lo, 1.5, 4000, endpoint=False), np.linspace(1.5, ZMAX, 1000)])
    else:
        z = np.concatenate([np.linspace(r, 1.5, 2000, endpoint=False), np.linspace(1.5, ZMAX, NZ - 2000)])
    out = np.empty(len(y))
    for i in range(0, len(y), 500):                         # chunks to bound memory
        sl = slice(i, i + 500)
        F = cdf(dist, df.iloc[sl], z)
        H = (y[sl][:, None] <= z[None, :]).astype(float)
        out[sl] = TRAPZ((F - H) ** 2, z, axis=1)
    return out


def load(lab, s):
    df = pd.read_csv(f"{IN}/preds/{CONFIGS[lab]}__s{s}.csv").query("split == 'test'").reset_index(drop=True)
    y = np.where(df.y_true.values <= ZERO_TOL, 0.0, df.y_true.values)
    return df, y


# ---------- check: r = 0 reproduces the full CRPS for the non-negative distributions ----------
say("===== check: twCRPS(r = 0) vs full CRPS (199-quantile approximation, from q11_train), seed 42 =====")
for lab in ("Tobit", "Bernoulli-gamma"):
    df, y = load(lab, 42)
    dist = CONFIGS[lab].split("__")[0]
    tw0 = twcrps(dist, df, y, 0.0).mean()
    import json
    full = json.load(open(f"{IN}/runs/{CONFIGS[lab]}__s42.json"))["test"]["dry0"]["crps_all"]
    say(f"  {lab:16s} twCRPS(r=0) {tw0:.5f} | CRPS (quantile approx.) {full:.5f} | diff {tw0 - full:+.5f}")

# ---------- per seed ----------
per, cases = [], {}
for lab in CONFIGS:
    dist = CONFIGS[lab].split("__")[0]
    acc = {k: 0.0 for k in THRESH}
    for s in SEEDS:
        df, y = load(lab, s)
        row = {"config": lab, "seed": s}
        for k, r in THRESH.items():
            v = twcrps(dist, df, y, r)
            row[k] = v.mean(); acc[k] = acc[k] + v / len(SEEDS)
        per.append(row)
    cases[lab] = acc
    say(f"done {lab}")
per = pd.DataFrame(per)
per.to_csv(f"{MET}/q11_twcrps_per_seed.csv", index=False)
g = per.groupby("config")[list(THRESH)]
tab = pd.DataFrame({k: [f"{g.mean().loc[c, k]:.5f} ± {g.std(ddof=1).loc[c, k]:.5f}" for c in CONFIGS]
                    for k in THRESH}, index=list(CONFIGS))
say("\n===== threshold-weighted CRPS on all 3,939 test cases, seed mean ± SD (lower is better) =====")
say(tab.to_string())

# ---------- paired comparisons ----------
n = len(load("Gaussian", 42)[1])
rng = np.random.default_rng(BSEED)
nb = int(np.ceil(n / BLOCK))
starts = rng.integers(0, n - BLOCK + 1, size=(N_BOOT, nb))
idx = (starts[:, :, None] + np.arange(BLOCK)[None, None, :]).reshape(N_BOOT, -1)
rows = []
say("\n===== paired differences a − b: seed t 95% interval, seeds in which a is better; "
    f"block bootstrap ({BLOCK} samples, {N_BOOT}) =====")
for a, b in PAIRS:
    say(f"-- {a} − {b} --")
    for k in THRESH:
        d = (per[per.config == a].set_index("seed")[k] - per[per.config == b].set_index("seed")[k]).reindex(SEEDS)
        m = d.mean(); h = tdist.ppf(0.975, 4) * d.std(ddof=1) / np.sqrt(5)
        bd = cases[a][k][idx].mean(1) - cases[b][k][idx].mean(1)
        lo, hi = np.percentile(bd, [2.5, 97.5])
        rel = m / per[per.config == b][k].mean()
        f1 = "*" if (m - h > 0 or m + h < 0) else " "
        f2 = "*" if (lo > 0 or hi < 0) else " "
        say(f"   {k:5s} {m:+.5f} ({rel:+.1%}) seed[{m - h:+.5f}, {m + h:+.5f}]{f1} boot[{lo:+.5f}, {hi:+.5f}]{f2} "
            f"{int((d < 0).sum())}/5 better")
        rows.append({"a": a, "b": b, "threshold": k, "diff_seed_mean": m, "rel_diff": rel, "seed_t_low": m - h,
                     "seed_t_high": m + h, "boot_low": lo, "boot_high": hi, "n_seeds_a_better": int((d < 0).sum())})
pd.DataFrame(rows).to_csv(f"{MET}/q11_twcrps_paired.csv", index=False)
open(f"{MET}/q11_twcrps_output.txt", "w").write("\n".join(lines) + "\n")
say("===== q11 twCRPS COMPLETE =====")
