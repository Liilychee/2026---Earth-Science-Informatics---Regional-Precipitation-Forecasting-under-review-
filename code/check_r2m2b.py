r"""
check_r2m2b.py — R2-M2, read-only check: does skill differ between issue times whose inputs are affected by
the ERA5 look-ahead and those that are not? No training; no saved file is modified (only new outputs).

Background (ECMWF ERA5 documentation):
  * 4D-Var windows 09-21 and 21-09 UTC: the analyses at 00 and 12 UTC assimilate observations up to t+9 h
    (covering the target hour t+5..t+6 h); the analyses at 06 and 18 UTC only up to t+3 h.
  * Accumulations/extremes (lsp, mxtpr, mntpr, target tp) come from short forecasts started at 06/18 UTC.
    For issue times 00 and 12 UTC the input precipitation (forecast step 6) and the target (step 12) come from
    the SAME forecast; for 06 and 18 UTC they come from two different forecasts.
  -> group A = issue times 00, 12 UTC (look-ahead and same forecast); group B = issue times 06, 18 UTC.
  Issue time t = target valid time - 6 h.

Criterion (fixed before running): an advantage of group A is reported only if, for BOTH XGBoost and
BiLSTM-Attention, SS_A - SS_B > 0 in 5/5 seeds AND the 95% moving-block bootstrap interval excludes 0.
Otherwise: "skill did not differ systematically between issue times affected and unaffected by the look-ahead".
SS = 1 - RMSE(model) / RMSE(month x hour climatology of the training targets), computed within each group.
Caveat: the groups also differ by time of day; the month x hour climatology removes the diurnal mean, not a
diurnal cycle of predictability. A difference is therefore consistent with, not proof of, a look-ahead effect.

Data: training targets for the climatology from results/xgboost_preds.csv (split == train, 18,404);
model predictions from results/q21/preds/{xgboost,bilstm_attn}__w6__C0__*__s{seed}.csv (configuration C0 = original seven
predictors, W = 6; seed 42 reproduces the original manuscript exactly).
Outputs: results/metrics/check_r2m2b_issue_time.csv, results/metrics/check_r2m2b_output.txt (via tee)
Run: cd /root/autodl-tmp && python3 code/check_r2m2b.py 2>&1 | tee results/metrics/check_r2m2b_output.txt
"""
import os

import numpy as np
import pandas as pd

ROOT = next(r for r in ("results", "/root/autodl-tmp/results") if os.path.isdir(r))
SEEDS = [42, 123, 7, 2024, 99]
MODELS = {"XGBoost": "xgboost__w6__C0__tree", "BiLSTM-Attention": "bilstm_attn__w6__C0__mse"}
BLOCK, NBOOT, BSEED = 28, 5000, 42
GROUP = {0: "A", 12: "A", 6: "B", 18: "B"}          # by issue hour (UTC)


def load(stem, s):
    d = pd.read_csv(os.path.join(ROOT, "q21", "preds", f"{stem}__s{s}.csv"), parse_dates=["valid_time"])
    return d


# ------------------------------------------------------------- reference: month x hour climatology
# (mean of the 18,404 training targets per month x hour of the target valid time, as in q07)
# training targets from the original saved predictions (the q21 files hold only validation and test rows)
orig = pd.read_csv(os.path.join(ROOT, "xgboost_preds.csv"), parse_dates=["valid_time"])
tr = orig[orig.split == "train"].copy()
assert len(tr) == 18404, len(tr)
ref = load(MODELS["XGBoost"], 42)
te = ref[ref.split == "test"].sort_values("valid_time").reset_index(drop=True)
ot = orig[orig.split == "test"].sort_values("valid_time").reset_index(drop=True)
assert (ot.valid_time.to_numpy() == te.valid_time.to_numpy()).all() and np.allclose(ot.y_true, te.y_true, atol=1e-6)
tr["m"], tr["h"] = tr.valid_time.dt.month, tr.valid_time.dt.hour
clim_tab = tr.groupby(["m", "h"]).y_true.mean()
y = te.y_true.to_numpy()
clim = clim_tab.reindex(pd.MultiIndex.from_arrays([te.valid_time.dt.month, te.valid_time.dt.hour])).to_numpy()
assert not np.isnan(clim).any()
issue_hour = ((te.valid_time - pd.Timedelta(hours=6)).dt.hour).to_numpy()
grp = np.array([GROUP[h] for h in issue_hour])
N = len(y)
r_clim = float(np.sqrt(np.mean((y - clim) ** 2)))
print(f"test N = {N}; issue-hour counts: " +
      ", ".join(f"{h:02d} UTC {int((issue_hour == h).sum())}" for h in (0, 6, 12, 18)))
print(f"check: month x hour climatology RMSE on all test = {r_clim:.6f} (Table 3 / q07: 0.273057)")
assert abs(r_clim - 0.273057) < 5e-6, "climatology does not reproduce q07"

P = {}
for name, stem in MODELS.items():
    for s in SEEDS:
        d = load(stem, s)
        d = d[d.split == "test"].sort_values("valid_time").reset_index(drop=True)
        assert (d.valid_time.to_numpy() == te.valid_time.to_numpy()).all()
        assert np.allclose(d.y_true.to_numpy(), y, atol=1e-6)
        P[(name, s)] = d.y_pred_mean.to_numpy()
pers = te.persistence.to_numpy()
r42 = {n: float(np.sqrt(np.mean((y - P[(n, 42)]) ** 2))) for n in MODELS}
print(f"check: seed-42 RMSE XGBoost {r42['XGBoost']:.6f} (orig 0.243750), "
      f"BiLSTM-Attention {r42['BiLSTM-Attention']:.6f} (orig 0.242848)")
assert abs(r42["XGBoost"] - 0.243750) < 1e-6 and abs(r42["BiLSTM-Attention"] - 0.242848) < 1e-6


def ss(p, mask):
    return 1 - np.sqrt(np.mean((y[mask] - p[mask]) ** 2)) / np.sqrt(np.mean((y[mask] - clim[mask]) ** 2))


# ------------------------------------------------------------- per issue hour and per group
rows = []
mA, mB = grp == "A", grp == "B"
masks = {"issue 00 UTC": issue_hour == 0, "issue 06 UTC": issue_hour == 6, "issue 12 UTC": issue_hour == 12,
         "issue 18 UTC": issue_hour == 18, "group A (00,12)": mA, "group B (06,18)": mB, "all": np.ones(N, bool)}
for lab, mk in masks.items():
    row = {"subset": lab, "n": int(mk.sum()),
           "RMSE_clim": float(np.sqrt(np.mean((y[mk] - clim[mk]) ** 2))),
           "SS_persistence": ss(pers, mk)}
    for n in MODELS:
        v = [ss(P[(n, s)], mk) for s in SEEDS]
        row[f"SS_{n}_mean"], row[f"SS_{n}_sd"] = float(np.mean(v)), float(np.std(v, ddof=1))
    rows.append(row)
tab = pd.DataFrame(rows)

# ------------------------------------------------------------- A - B, moving-block bootstrap
rng = np.random.default_rng(BSEED)
nb = int(np.ceil(N / BLOCK))
starts = rng.integers(0, N - BLOCK + 1, size=(NBOOT, nb))
idx = (starts[:, :, None] + np.arange(BLOCK)[None, None, :]).reshape(NBOOT, -1)[:, :N]


def boot_ss(p, mk):
    e2 = ((y - p) ** 2)[idx]
    c2 = ((y - clim) ** 2)[idx]
    m = mk[idx]
    return 1 - np.sqrt((e2 * m).sum(1) / m.sum(1)) / np.sqrt((c2 * m).sum(1) / m.sum(1))


diff_rows, verdict = [], {}
for n in MODELS:
    d_seed = np.array([ss(P[(n, s)], mA) - ss(P[(n, s)], mB) for s in SEEDS])
    d_boot = np.mean([boot_ss(P[(n, s)], mA) - boot_ss(P[(n, s)], mB) for s in SEEDS], axis=0)
    lo, hi = np.percentile(d_boot, [2.5, 97.5])
    verdict[n] = bool((d_seed > 0).all() and lo > 0)
    diff_rows.append({"model": n, "SS_A_minus_B_mean": float(d_seed.mean()),
                      "per_seed": " ".join(f"{v:+.4f}" for v in d_seed),
                      "seeds_A_better": int((d_seed > 0).sum()), "boot_low": float(lo), "boot_high": float(hi)})
dp = ss(pers, mA) - ss(pers, mB)
dpb = boot_ss(pers, mA) - boot_ss(pers, mB)
diff_rows.append({"model": "Persistence (reference)", "SS_A_minus_B_mean": float(dp), "per_seed": "",
                  "seeds_A_better": np.nan, "boot_low": float(np.percentile(dpb, 2.5)),
                  "boot_high": float(np.percentile(dpb, 97.5))})
dtab = pd.DataFrame(diff_rows)

pd.set_option("display.width", 200)
print("\nRMSE skill score against the month x hour climatology (within subset); models: mean and SD over 5 seeds")
print(tab.round(4).to_string(index=False))
print(f"\nSS(group A: issue 00/12 UTC) - SS(group B: issue 06/18 UTC); moving-block bootstrap, block {BLOCK} "
      f"(7 days), {NBOOT} resamples, seed {BSEED}, per-seed differences averaged over seeds")
print(dtab.round(4).to_string(index=False))
adv = all(verdict.values())
print("\nVERDICT (criterion fixed in advance): " +
      ("group A (issue 00/12 UTC) shows a systematic advantage for both models -> report the difference as a "
       "possible look-ahead / same-forecast effect"
       if adv else
       "skill did not differ systematically between issue times affected and unaffected by the look-ahead"))
out = pd.concat([tab.assign(table="by_subset"), dtab.assign(table="A_minus_B")], ignore_index=True)
out.to_csv(os.path.join(ROOT, "metrics", "check_r2m2b_issue_time.csv"), index=False)
print("CHECK COMPLETE")
