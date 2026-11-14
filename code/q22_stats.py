#!/usr/bin/env python3
"""q22 统计：逐小时输入（B，31 个快照）对 6 小时间隔输入（A，6 个快照），同模型、同种子配对。CPU 即可，不训练。

读 results/q22/runs/*.json 与 results/q22/preds/*.csv（测试集 2021 年，1,454 个时刻）；上尾阈值从
q22_train.build() 重建的训练目标计算（这一子集 2017–2019 的 Q95 = 0.5875，主口径），主研究的 0.5740 作敏感性。
预先设定（训练前，2026-11-14）：
  主指标：测试集全部样本的 RMSE，ΔRMSE = B − A（负数 = 逐小时输入更好）
  补充：MAE、有雨 y ≥ 0.1 的 RMSE、上尾 y ≥ Q95 的 RMSE（只描述，不另作结论）
  区间：种子 t 区间（5 个种子，t_{0.975,4}）；移动块自助法（与 q21/q14 相同的算法，块 28 = 7 天，5,000 次，
        种子 42；统计量为每次重抽样上"5 个种子平均的 ΔRMSE"），块 56（14 天）、120（30 天）作敏感性
  判定：只有 5 个种子方向一致、且种子 t 区间与块 28 的自助法区间都不含 0，才记为稳健（robust_better /
        robust_worse）；否则为 uncertain，写"未检测到满足预设标准的差异"，不写"两者等效"。
  注意：XGBoost 的种子只改变行列抽样，5 个种子不是 5 次独立重复，其种子区间只描述种子敏感性。
运行：cd /root/autodl-tmp && python3 code/q22_stats.py 2>&1 | tee results/metrics/q22_stats_output.txt
输出：results/metrics/q22_runs.csv、q22_effect.csv
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import t as tdist

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q22_train as q22  # noqa: E402  (no TensorFlow import at module level)

ROOT = q22.ROOT
RUNS, PREDS, OUT = f"{ROOT}/results/q22/runs", f"{ROOT}/results/q22/preds", f"{ROOT}/results/metrics"
MODELS, INPUTS, SEEDS = q22.MODELS, ["A", "B"], q22.SEEDS
WET, Q95_MAIN = 0.1, 0.574048
BLOCKS, NBOOT, BSEED, PRIMARY_BLOCK = [28, 56, 120], 5000, 42, 28


def main():
    out, _ = q22.build(q22.load())
    q95 = float(np.quantile(out["train"]["y"], 0.95))
    y, tau = out["test"]["y"], out["test"]["tau"]
    n = len(y)
    assert n == 1454, n
    masks = {"all": np.ones(n, bool), "wet": y >= WET, "tail": y >= q95, "tail_main_q95": y >= Q95_MAIN}

    runs, P = [], {}
    for f in sorted(glob.glob(f"{RUNS}/*.json")):
        r = json.load(open(f))
        p = pd.read_csv(f"{PREDS}/{r['tag']}.csv", parse_dates=["valid_time", "issue_time"])
        p = p[p.split == "test"].reset_index(drop=True)
        assert (p.valid_time.values == tau).all() and np.allclose(p.y_true.values, y), f"{r['tag']}: 测试样本不对齐"
        P[(r["model"], r["input"], r["seed"])] = p.y_pred_mean.to_numpy()
        runs.append({"model": r["model"], "input": r["input"], "n_steps": r["n_steps"], "seed": r["seed"],
                     "val_rmse": r["val"]["rmse"], "best_epoch": r["best_epoch"], "epochs_trained": r["epochs_trained"],
                     "train_seconds": r["train_seconds"], "device": r["gpu"]})
    miss = [(m, i, s) for m in MODELS for i in INPUTS for s in SEEDS if (m, i, s) not in P]
    print(f"运行数 {len(P)}/20；缺少：{miss if miss else '无'}；设备：{sorted(set(r['device'] for r in runs))}")
    print(f"测试集 {n} 个时刻（2021 年），已与 q22_train 重建的目标逐一对齐；上尾阈值 Q95（2017–2019 训练目标）"
          f"= {q95:.4f} mm/h，主研究 Q95 = {Q95_MAIN:.4f}（敏感性）")
    print("子集样本数：" + "，".join(f"{k} {int(m.sum())}" for k, m in masks.items()))

    rows = []
    for (m, i, s), yp in P.items():
        r = {"model": m, "input": i, "seed": s, "mae_all": float(np.mean(np.abs(yp - y)))}
        for k, mk in masks.items():
            r[f"rmse_{k}"] = float(np.sqrt(np.mean((yp[mk] - y[mk]) ** 2)))
        r["pred_max"], r["sd_ratio"] = float(yp.max()), float(yp.std() / y.std())
        rows.append(r)
    M = pd.DataFrame(rows).merge(pd.DataFrame(runs), on=["model", "input", "seed"]).sort_values(["model", "input", "seed"])
    M.to_csv(f"{OUT}/q22_runs.csv", index=False)
    pers = float(np.sqrt(np.mean((out["test"]["pers"] - y) ** 2)))

    # moving-block bootstrap weights (same construction as q21_stats.py), one set per block length
    W = {}
    for L in BLOCKS:
        rng = np.random.default_rng(BSEED)
        nb = int(np.ceil(n / L))
        Wb = np.empty((NBOOT, n), dtype=np.float32)
        for b in range(NBOOT):
            st = rng.integers(0, n - L + 1, nb)
            Wb[b] = np.bincount((st[:, None] + np.arange(L)).ravel()[:n], minlength=n)
        W[L] = Wb
    tq = tdist.ppf(0.975, len(SEEDS) - 1)

    eff = []
    for m in MODELS:
        if any((m, i, s) not in P for i in INPUTS for s in SEEDS):
            continue
        metrics = [(k, "rmse") for k in masks] + [("all", "mae")]
        for k, kind in metrics:
            mk = masks[k]; mkf = mk.astype(np.float32)
            d_seed = []
            boot = {L: np.zeros(NBOOT) for L in BLOCKS}
            for s in SEEDS:
                eA, eB = P[(m, "A", s)] - y, P[(m, "B", s)] - y
                if kind == "rmse":
                    a, b = (eA ** 2).astype(np.float32) * mkf, (eB ** 2).astype(np.float32) * mkf
                    d_seed.append(np.sqrt(b.sum() / mk.sum()) - np.sqrt(a.sum() / mk.sum()))
                    for L in BLOCKS:
                        cnt = W[L] @ mkf
                        boot[L] += np.sqrt((W[L] @ b) / cnt) - np.sqrt((W[L] @ a) / cnt)
                else:
                    a, b = np.abs(eA).astype(np.float32), np.abs(eB).astype(np.float32)
                    d_seed.append(b.mean() - a.mean())
                    for L in BLOCKS:
                        boot[L] += (W[L] @ b - W[L] @ a) / n
            d = np.array(d_seed)
            mu, sd = d.mean(), d.std(ddof=1)
            tlo, thi = mu - tq * sd / np.sqrt(len(SEEDS)), mu + tq * sd / np.sqrt(len(SEEDS))
            row = {"model": m, "subset": k, "metric": kind, "n_subset": int(mk.sum()),
                   "primary": (k == "all" and kind == "rmse"),
                   "value_A": float(M[(M.model == m) & (M.input == "A")][f"{kind}_{k}"].mean()),
                   "value_B": float(M[(M.model == m) & (M.input == "B")][f"{kind}_{k}"].mean()),
                   "d_mean": mu, "d_sd": sd, "t_lo": tlo, "t_hi": thi, "n_B_better_of_5": int((d < 0).sum())}
            row["d_pct"] = 100 * mu / row["value_A"]
            for L in BLOCKS:
                row[f"boot{L}_lo"], row[f"boot{L}_hi"] = np.percentile(boot[L] / len(SEEDS), [2.5, 97.5])
            blo, bhi = row[f"boot{PRIMARY_BLOCK}_lo"], row[f"boot{PRIMARY_BLOCK}_hi"]
            if not row["primary"]:
                row["verdict"] = "secondary (descriptive)"     # pre-specified: no verdict on secondary metrics
            elif row["n_B_better_of_5"] == 5 and thi < 0 and bhi < 0:
                row["verdict"] = "robust_better"
            elif row["n_B_better_of_5"] == 0 and tlo > 0 and blo > 0:
                row["verdict"] = "robust_worse"
            else:
                row["verdict"] = "uncertain"
            eff.append(row)
    E = pd.DataFrame(eff)
    E.to_csv(f"{OUT}/q22_effect.csv", index=False)

    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40)
    print(f"\n持续性（参照）测试 RMSE = {pers:.4f}")
    print("\n===== 逐运行（测试集）=====")
    print(M[["model", "input", "seed", "rmse_all", "mae_all", "rmse_wet", "rmse_tail", "pred_max", "sd_ratio",
             "val_rmse", "best_epoch", "train_seconds"]].round(4).to_string(index=False))
    print("\n===== B − A（负数 = 逐小时输入更好）；t 区间、块自助法区间（28/56/120 个样本 = 7/14/30 天）=====")
    print(E[["model", "subset", "metric", "primary", "n_subset", "value_A", "value_B", "d_mean", "d_pct", "t_lo", "t_hi",
             "boot28_lo", "boot28_hi", "boot56_lo", "boot56_hi", "boot120_lo", "boot120_hi", "n_B_better_of_5",
             "verdict"]].round(4).to_string(index=False))
    print("\n===== 主判定（预先设定：测试 RMSE，块 28）=====")
    for _, r in E[E.primary].iterrows():
        msg = {"robust_better": "逐小时输入稳健更好", "robust_worse": "逐小时输入稳健更差",
               "uncertain": "未检测到满足预设标准的差异"}[r.verdict]
        print(f"{r.model}: ΔRMSE = {r.d_mean:+.5f}（{r.d_pct:+.2f}%），t [{r.t_lo:+.5f}, {r.t_hi:+.5f}]，"
              f"块 28 [{r.boot28_lo:+.5f}, {r.boot28_hi:+.5f}]，{r.n_B_better_of_5}/5 → {msg}")
    print("注：XGBoost 的 5 个种子只改变行列抽样，不是独立重复；其 t 区间只描述种子敏感性。")


if __name__ == "__main__":
    main()
