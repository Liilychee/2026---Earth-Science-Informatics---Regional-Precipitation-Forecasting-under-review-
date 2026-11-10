# ============================================================
# Item 16 (R2 m2): 90% and 95% prediction-interval coverage and width, no training.
# Source A (main): q14 five-seed reruns at W = 6 (results/q14/preds/*__w6__*__s*.csv) of the Gaussian models,
#   i.e. every file whose test rows have y_pred_std. The original notebook five-seed runs stored Coverage95 only
#   (Step 13: "MPIW95: not stored in original 5-seed runs"), so 90% for five seeds can only come from the reruns.
# Source B (reference): saved single-run predictions results/predictions/*_preds.csv that contain y_pred_std.
# Gaussian central interval mu ± z·sigma, z = 1.6449 (90%) / 1.9600 (95%); subsets all, wet >= 0.1, upper tail >= Q95.
# Metrics: PICP, MPIW, share of obs above upper / below lower, share of negative lower bounds,
#   interval score (Gneiting & Raftery 2007 form: width + 2/alpha·miss distance) — strict for the full sample only.
# Outputs: results/metrics/q16_interval_per_run.csv, q16_interval_summary.csv
# Run: cd /root/autodl-tmp && python3 code/q16_intervals.py 2>&1 | tee results/metrics/q16_output.txt
# ============================================================
import glob, os, re
import numpy as np
import pandas as pd

ROOT = "/root/autodl-tmp"
OUT = f"{ROOT}/results/metrics"
Q95, WET = 0.574048, 0.1
Z = {0.90: 1.6448536269514722, 0.95: 1.959963984540054}


def metrics(y, mu, sd):
    rows = []
    for sub, m in (("all", np.ones_like(y, bool)), ("wet>=0.1", y >= WET), ("upper>=Q95", y >= Q95)):
        yy, mm, ss = y[m], mu[m], sd[m]
        r = {"subset": sub, "n": int(m.sum()), "mean_sigma": ss.mean()}
        for p, z in Z.items():
            a, lo, hi = 1 - p, mm - z * ss, mm + z * ss
            k = int(round(p * 100))
            r[f"PICP{k}"] = np.mean((yy >= lo) & (yy <= hi))
            r[f"MPIW{k}"] = np.mean(hi - lo)
            r[f"above{k}"] = np.mean(yy > hi)
            r[f"below{k}"] = np.mean(yy < lo)
            r[f"neglow{k}"] = np.mean(lo < 0)
            r[f"IS{k}"] = np.mean((hi - lo) + 2 / a * (lo - yy) * (yy < lo) + 2 / a * (yy - hi) * (yy > hi))
        rows.append(r)
    return rows


def load(path):
    d = pd.read_csv(path)
    if "split" in d:
        d = d[d["split"] == "test"]
    if "y_pred_std" not in d or d["y_pred_std"].isna().all():
        return None
    assert len(d) == 3939, f"{path}: {len(d)} test rows"
    assert d["y_pred_std"].notna().all() and (d["y_pred_std"] > 0).all(), f"{path}: bad sigma"
    return d["y_true"].to_numpy(float), d["y_pred_mean"].to_numpy(float), d["y_pred_std"].to_numpy(float)


rows = []
for f in sorted(glob.glob(f"{ROOT}/results/q14/preds/*__w6__*__s*.csv")):
    got = load(f)
    if got is None:
        continue
    tag = os.path.basename(f)[:-4]
    model, seed = tag.split("__w6__")[0], int(re.search(r"__s(\d+)$", tag).group(1))
    y, mu, sd = got
    for r in metrics(y, mu, sd):
        rows.append({"source": "q14_rerun_5seed", "model": model, "seed": seed, "file": tag,
                     "rmse_all": float(np.sqrt(np.mean((mu - y) ** 2))), **r})
for f in sorted(glob.glob(f"{ROOT}/results/predictions/*_preds.csv")):
    got = load(f)
    if got is None:
        continue
    y, mu, sd = got
    for r in metrics(y, mu, sd):
        rows.append({"source": "saved_single_run", "model": os.path.basename(f)[:-10], "seed": -1,
                     "file": os.path.basename(f), "rmse_all": float(np.sqrt(np.mean((mu - y) ** 2))), **r})

df = pd.DataFrame(rows)
if df.empty:
    raise SystemExit("没有找到带 y_pred_std 的测试预测，停止")
df.to_csv(f"{OUT}/q16_interval_per_run.csv", index=False)
print("files used:")
print(df[df.subset == "all"][["source", "model", "seed", "rmse_all", "mean_sigma"]].to_string(index=False))
num = [c for c in df.columns if c not in ("source", "model", "seed", "file", "subset")]
g = df.groupby(["source", "model", "subset"], sort=False)
summ = g[num].agg(["mean", "std"])
summ.columns = [f"{a}_{b}" for a, b in summ.columns]
summ.insert(0, "n_runs", g.size())
summ = summ.reset_index()
summ.to_csv(f"{OUT}/q16_interval_summary.csv", index=False)
pd.set_option("display.width", 250)
show = ["source", "model", "subset", "n_runs", "n_mean", "rmse_all_mean", "PICP90_mean", "PICP90_std", "MPIW90_mean",
        "PICP95_mean", "PICP95_std", "MPIW95_mean", "above90_mean", "above95_mean", "neglow95_mean", "IS90_mean", "IS95_mean"]
print(summ[show].round(4).to_string(index=False))
print("===== q16 COMPLETE =====")
