#!/usr/bin/env python3
"""q22c 统计（R3-19 实验 C）：A、B（results/q22，已有）与 CA、CB（results/q22c，训练集逐小时起报），同模型、同种子配对。
CPU 即可，不训练；不改动 q22 的任何结果文件。

比较（训练前预先设定，2026-11-15；本实验整体为看过 A/B 结果之后追加的事后敏感性分析）：
  主比较  CB − A ：逐小时输入 + 逐小时起报训练样本，相对原文做法
  探索性  CA − A ：只增加训练样本（输入同 A）
          CB − CA：样本增加之后，逐小时输入的额外作用
          CB − B ：输入同为逐小时时，增加训练样本的作用
  每组比较都用同一判定规则，但不做多重比较校正；不得事后挑选最显著的一组当主要结论。
主指标：测试集（2021 年，1,454 个时刻，与 A/B 完全相同）全部样本 RMSE；MAE、有雨 ≥ 0.1、上尾 ≥ Q95（0.5875，
        2017–2019 天气时次训练目标；主研究 0.5740 作敏感性）只描述。
区间：种子 t 区间（t_{0.975,4}）；移动块自助法，与 q22_stats / q21 相同算法，块 28（主）/56/120，5,000 次，种子 42。
判定：5 个种子方向一致，且种子 t 区间与块 28 区间都不含 0 → robust_better / robust_worse；否则 uncertain，
      写"未检测到满足预设标准的差异"，不写"等效"。XGBoost 的种子只改变行列抽样，其 t 区间只描述种子敏感性。
运行：cd /root/autodl-tmp && python3 code/q22c_stats.py 2>&1 | tee results/metrics/q22c_stats_output.txt
输出：results/metrics/q22c_runs.csv、q22c_effect.csv
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import t as tdist

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q22_train as q22  # noqa: E402

ROOT = q22.ROOT
DIRS = {"A": "q22", "B": "q22", "CA": "q22c", "CB": "q22c"}
OUT = f"{ROOT}/results/metrics"
MODELS, CONFIGS, SEEDS = q22.MODELS, list(DIRS), q22.SEEDS
COMPARISONS = [("CB", "A", True), ("CA", "A", False), ("CB", "CA", False), ("CB", "B", False)]   # (new, ref, primary)
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
    for cfg, sub in DIRS.items():
        for f in sorted(glob.glob(f"{ROOT}/results/{sub}/runs/*__{cfg}__s*.json")):
            r = json.load(open(f))
            assert r["input"] == cfg
            p = pd.read_csv(f"{ROOT}/results/{sub}/preds/{r['tag']}.csv", parse_dates=["valid_time", "issue_time"])
            pv = p[p.split == "val"]
            p = p[p.split == "test"].reset_index(drop=True)
            assert (p.valid_time.values == tau).all() and np.allclose(p.y_true.values, y), f"{r['tag']}: 测试样本不对齐"
            assert (pv.valid_time.values == out["val"]["tau"]).all(), f"{r['tag']}: 验证样本不对齐"
            P[(r["model"], cfg, r["seed"])] = p.y_pred_mean.to_numpy()
            runs.append({"model": r["model"], "config": cfg, "n_steps": r["n_steps"], "seed": r["seed"],
                         "n_train": r["n_train"], "val_rmse": r["val"]["rmse"], "best_epoch": r["best_epoch"],
                         "epochs_trained": r["epochs_trained"], "train_seconds": r["train_seconds"], "device": r["gpu"]})
    miss = [(m, c, s) for m in MODELS for c in CONFIGS for s in SEEDS if (m, c, s) not in P]
    print(f"运行数 {len(P)}/40；缺少：{miss if miss else '无'}；设备：{sorted(set(r['device'] for r in runs))}")
    print(f"测试集 {n} 个时刻（2021 年），四种配置逐一对齐；上尾阈值 Q95 = {q95:.4f} mm/h（主研究 {Q95_MAIN:.4f} 作敏感性）")
    print("子集样本数：" + "，".join(f"{k} {int(m.sum())}" for k, m in masks.items()))

    rows = []
    for (m, c, s), yp in P.items():
        r = {"model": m, "config": c, "seed": s, "mae_all": float(np.mean(np.abs(yp - y)))}
        for k, mk in masks.items():
            r[f"rmse_{k}"] = float(np.sqrt(np.mean((yp[mk] - y[mk]) ** 2)))
        r["pred_max"], r["sd_ratio"] = float(yp.max()), float(yp.std() / y.std())
        rows.append(r)
    M = pd.DataFrame(rows).merge(pd.DataFrame(runs), on=["model", "config", "seed"]).sort_values(["model", "config", "seed"])
    M.to_csv(f"{OUT}/q22c_runs.csv", index=False)
    pers = float(np.sqrt(np.mean((out["test"]["pers"] - y) ** 2)))

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
        for new, ref, primary in COMPARISONS:
            if any((m, c, s) not in P for c in (new, ref) for s in SEEDS):
                print(f"[跳过] {m} {new} − {ref}：运行不全"); continue
            for k, kind in [(k, "rmse") for k in masks] + [("all", "mae")]:
                mk = masks[k]; mkf = mk.astype(np.float32)
                d_seed, boot = [], {L: np.zeros(NBOOT) for L in BLOCKS}
                for s in SEEDS:
                    eR, eN = P[(m, ref, s)] - y, P[(m, new, s)] - y
                    if kind == "rmse":
                        a, b = (eR ** 2).astype(np.float32) * mkf, (eN ** 2).astype(np.float32) * mkf
                        d_seed.append(np.sqrt(b.sum() / mk.sum()) - np.sqrt(a.sum() / mk.sum()))
                        for L in BLOCKS:
                            cnt = W[L] @ mkf
                            boot[L] += np.sqrt((W[L] @ b) / cnt) - np.sqrt((W[L] @ a) / cnt)
                    else:
                        a, b = np.abs(eR).astype(np.float32), np.abs(eN).astype(np.float32)
                        d_seed.append(b.mean() - a.mean())
                        for L in BLOCKS:
                            boot[L] += (W[L] @ b - W[L] @ a) / n
                d = np.array(d_seed)
                mu, sd = d.mean(), d.std(ddof=1)
                tlo, thi = mu - tq * sd / np.sqrt(len(SEEDS)), mu + tq * sd / np.sqrt(len(SEEDS))
                is_main = k == "all" and kind == "rmse"
                row = {"model": m, "comparison": f"{new} − {ref}", "new": new, "ref": ref,
                       "role": ("primary" if primary else "exploratory") if is_main else "secondary metric",
                       "subset": k, "metric": kind, "n_subset": int(mk.sum()),
                       "value_ref": float(M[(M.model == m) & (M.config == ref)][f"{kind}_{k}"].mean()),
                       "value_new": float(M[(M.model == m) & (M.config == new)][f"{kind}_{k}"].mean()),
                       "d_mean": mu, "d_sd": sd, "t_lo": tlo, "t_hi": thi, "n_new_better_of_5": int((d < 0).sum())}
                row["d_pct"] = 100 * mu / row["value_ref"]
                for L in BLOCKS:
                    row[f"boot{L}_lo"], row[f"boot{L}_hi"] = np.percentile(boot[L] / len(SEEDS), [2.5, 97.5])
                blo, bhi = row[f"boot{PRIMARY_BLOCK}_lo"], row[f"boot{PRIMARY_BLOCK}_hi"]
                if not is_main:
                    row["verdict"] = "secondary (descriptive)"
                elif row["n_new_better_of_5"] == 5 and thi < 0 and bhi < 0:
                    row["verdict"] = "robust_better"
                elif row["n_new_better_of_5"] == 0 and tlo > 0 and blo > 0:
                    row["verdict"] = "robust_worse"
                else:
                    row["verdict"] = "uncertain"
                eff.append(row)
    E = pd.DataFrame(eff)
    E.to_csv(f"{OUT}/q22c_effect.csv", index=False)

    pd.set_option("display.width", 280); pd.set_option("display.max_columns", 40)
    print(f"\n持续性（参照）测试 RMSE = {pers:.4f}")
    print("\n===== 逐运行（测试集）=====")
    print(M[["model", "config", "seed", "n_train", "rmse_all", "mae_all", "rmse_wet", "rmse_tail", "pred_max",
             "sd_ratio", "val_rmse", "best_epoch", "epochs_trained", "train_seconds"]].round(4).to_string(index=False))
    print("\n===== 运行成本（每种配置 5 个种子）=====")
    print(M.groupby(["model", "config"]).train_seconds.agg(["sum", "mean", "max"]).round(0).to_string())
    print("\n===== 新 − 参照（负数 = 新配置更好）；t 区间、块自助法区间（28/56/120 个样本 = 7/14/30 天）=====")
    print(E[["model", "comparison", "role", "subset", "metric", "value_ref", "value_new", "d_mean", "d_pct", "t_lo",
             "t_hi", "boot28_lo", "boot28_hi", "boot56_lo", "boot56_hi", "boot120_lo", "boot120_hi",
             "n_new_better_of_5", "verdict"]].round(4).to_string(index=False))
    print("\n===== 判定（测试 RMSE，块 28；主比较为 CB − A，其余为探索性分解，未做多重比较校正）=====")
    for _, r in E[E.subset.eq("all") & E.metric.eq("rmse")].iterrows():
        msg = {"robust_better": "稳健更好", "robust_worse": "稳健更差", "uncertain": "未检测到满足预设标准的差异"}[r.verdict]
        print(f"{r.model:12s} {r.comparison:8s} [{r.role}]: ΔRMSE = {r.d_mean:+.5f}（{r.d_pct:+.2f}%），"
              f"t [{r.t_lo:+.5f}, {r.t_hi:+.5f}]，块 28 [{r.boot28_lo:+.5f}, {r.boot28_hi:+.5f}]，"
              f"{r.n_new_better_of_5}/5 → {msg}")
    print("注：XGBoost 的 5 个种子只改变行列抽样，不是独立重复；其 t 区间只描述种子敏感性。")


if __name__ == "__main__":
    main()
