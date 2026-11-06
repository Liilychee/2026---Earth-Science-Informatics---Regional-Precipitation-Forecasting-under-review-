# ============================================================
# Item 06, step 4: audit of the rolling-origin experiment (zero training).
#   A. fold 4 (1992-2016) vs fold 4' (2004-2016): identical validation and test samples,
#      training sets differ only by the years 1992-2003
#   B. temporal isolation of every fold: train < val < test, no overlap, whole years,
#      scalers fitted on training years only (y_mean / y_scale differ between folds)
#   C. identical protocol across folds: 6 models x 5 seeds present, same software and GPU,
#      best epochs and stopping
#   D. pooled 2010-2021 test series: gaps between consecutive folds, no duplicated time stamps,
#      fold 4' not included
#   E. bootstrap settings actually used by q06_stats.py
# Output: results/metrics/q06_audit_output.txt (also printed)
# ============================================================
import glob, json, os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from q06_common import ROOT, FEATURES, TARGET, WINDOW, SEEDS, FOLDS, load_regional, split

OUT, MET = f"{ROOT}/results/q06", f"{ROOT}/results/metrics"
MODELS = ["xgboost", "bulstm", "bilstm_attn", "transformer", "bulstm_attn", "prob_bilstm_attn"]
ROLL = ["F1", "F2", "F3", "F4"]
lines, fails = [], []


def say(s=""):
    print(s); lines.append(s)


def check(ok, msg):
    say(f"  [{'OK' if ok else 'FAIL'}] {msg}")
    if not ok:
        fails.append(msg)


df = load_regional()
info = {f: json.load(open(f"{OUT}/folds/{f}.json")) for f in FOLDS}
parts = {f: split(df, f) for f in FOLDS}

# ---------- A. F4 vs F4' ----------
say("===== A. fold 4 (25 y) vs fold 4' (13 y) =====")
for k in ("val", "test"):
    check(info["F4"]["target_times"][k] == info["F4s"]["target_times"][k]
          and info["F4"]["n_windows"][k] == info["F4s"]["n_windows"][k],
          f"{k}: same target period {info['F4']['target_times'][k]} and n = {info['F4']['n_windows'][k]}")
tr4, tr4s = parts["F4"]["train"], parts["F4s"]["train"]
extra = tr4[~tr4["valid_time"].isin(tr4s["valid_time"])]
check(tr4s["valid_time"].isin(tr4["valid_time"]).all(), "every fold 4' training time stamp is also in fold 4")
check(extra["valid_time"].dt.year.between(1992, 2003).all(),
      f"extra training rows of fold 4 all lie in 1992-2003 (n = {len(extra)}, "
      f"{extra['valid_time'].min()} -> {extra['valid_time'].max()})")
common = tr4.merge(tr4s, on="valid_time", suffixes=("_a", "_b"))
dmax = max(np.abs(common[f"{c}_a"] - common[f"{c}_b"]).max() for c in FEATURES + [TARGET])
check(dmax == 0, f"shared training years 2004-2016 have identical values in both folds (max |diff| = {dmax})")
say(f"  training windows: fold 4 = {info['F4']['n_windows']['train']}, fold 4' = {info['F4s']['n_windows']['train']}")
say(f"  training Q95: fold 4 = {info['F4']['q95_train']:.4f}, fold 4' = {info['F4s']['q95_train']:.4f}")

# per-run predictions: identical validation and test truth / time stamps for every model and seed
bad = 0
for m in MODELS:
    for s in SEEDS:
        a = pd.read_csv(f"{OUT}/preds/F4__{m}__s{s}.csv")
        b = pd.read_csv(f"{OUT}/preds/F4s__{m}__s{s}.csv")
        for k in ("val", "test"):
            xa, xb = a[a.split == k], b[b.split == k]
            if not ((xa.valid_time.values == xb.valid_time.values).all()
                    and np.abs(xa.y_true.values - xb.y_true.values).max() < 1e-6
                    and np.abs(xa.persistence.values - xb.persistence.values).max() < 1e-9):
                bad += 1
check(bad == 0, f"saved predictions of all 6 models x 5 seeds: same validation and test samples in fold 4 and 4' "
                f"({bad} mismatches)")

# ---------- B. temporal isolation ----------
say("\n===== B. temporal isolation of every fold =====")
for f in FOLDS:
    p = parts[f]
    tmax_tr, tmin_va = p["train"].valid_time.max(), p["val"].valid_time.min()
    tmax_va, tmin_te = p["val"].valid_time.max(), p["test"].valid_time.min()
    ok = tmax_tr < tmin_va and tmax_va < tmin_te
    yrs = {k: (int(v.valid_time.dt.year.min()), int(v.valid_time.dt.year.max())) for k, v in p.items()}
    full = all(v.valid_time.min() == pd.Timestamp(f"{yrs[k][0]}-01-01 00:00") and
               v.valid_time.max() == pd.Timestamp(f"{yrs[k][1]}-12-31 18:00") for k, v in p.items())
    check(ok and full, f"{f}: train {yrs['train']} < val {yrs['val']} < test {yrs['test']}, whole calendar years")
    # scaler of this fold = training-period statistics
    y = p["train"][TARGET]
    check(abs(info[f]["y_mean"] - y.mean()) < 1e-6 and abs(info[f]["y_scale"] - y.std(ddof=0)) < 1e-6,
          f"{f}: target scaler equals training-period mean/std ({info[f]['y_mean']:.5f} / {info[f]['y_scale']:.5f})")
fc = f"{MET}/q06_feature_check.csv"
say(f"  predictor set: fixed 7 variables {FEATURES}; per-fold check on training years only -> {fc}")
if os.path.exists(fc):
    say("  " + pd.read_csv(fc).to_string(index=False).replace("\n", "\n  "))

# ---------- C. identical protocol ----------
say("\n===== C. protocol across folds =====")
runs = pd.DataFrame([json.load(open(p)) for p in glob.glob(f"{OUT}/runs/F*.json")])
grid = runs.groupby(["fold", "model"]).seed.apply(sorted)
check(len(runs) == 150 and all(v == sorted(SEEDS) for v in grid), f"{len(runs)} runs; every fold x model has seeds {sorted(SEEDS)}")
check(runs.tf.nunique() == 1 and runs.gpu.nunique() == 1, f"software / GPU: TF {runs.tf.unique()}, GPU {runs.gpu.unique()}")
nn = runs[runs.model != "xgboost"]
say("  best epoch (mean over seeds) / runs stopped before epoch 30:")
tab = nn.groupby(["model", "fold"]).best_epoch.mean().unstack()[list(FOLDS)]
say("  " + tab.round(1).to_string().replace("\n", "\n  "))
say(f"  runs that hit the 30-epoch cap: {int((nn.epochs_trained == 30).sum())} of {len(nn)}")

# ---------- D. pooled test series ----------
say("\n===== D. pooled 2010-2021 test series =====")
t = np.concatenate([pd.read_csv(f"{OUT}/preds/{f}__xgboost__s42.csv", parse_dates=["valid_time"])
                    .query("split == 'test'").valid_time.values for f in ROLL])
t = pd.to_datetime(t)
check(t.is_unique and t.is_monotonic_increasing, f"pooled test: n = {len(t)}, unique and in time order, fold 4' excluded")
gaps = pd.Series(t).diff()
big = gaps[gaps > pd.Timedelta(hours=6)]
for i in big.index:
    say(f"  gap between folds: {t[i - 1]} -> {t[i]} ({big[i]}); first {WINDOW} targets of each test period "
        f"are lost to the input window")

# ---------- E. bootstrap settings ----------
say("\n===== E. bootstrap settings used in q06_stats.py =====")
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "q06_stats.py")).read()
say("  " + re.search(r"N_BOOT, BSEED, BLOCK = .*", src).group(0))
say("  scheme: moving-block (non-circular), block starts uniform on [0, n - L], ceil(n / L) blocks per replicate;")
say("          the same block starts are applied to both forecasts (paired); RMSE of each replicate = sqrt(sum e^2 / count)")
say("          within the resampled blocks; seed handling: RMSE averaged over the 5 seeds inside every replicate;")
say("          95% percentile interval; main L = 28 samples (7 days), sensitivity 56 and 120 (14 and 30 days);")
say("          pooled series = folds 1-4 only, blocks may span the short gap between consecutive folds")

say(f"\n===== AUDIT {'PASSED' if not fails else 'FAILED: ' + '; '.join(fails)} =====")
open(f"{MET}/q06_audit_output.txt", "w").write("\n".join(lines) + "\n")
