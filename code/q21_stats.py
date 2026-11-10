#!/usr/bin/env python3
"""q21 统计：C1–C6 各自与 C0 比（同模型、同种子配对），XGBoost 与 BiLSTM-Attention 分开。CPU 即可。

读 results/q21/runs/*.json 与 results/q21/preds/*.csv（测试集 3,939 个时刻）。
子集：全部；有雨 y ≥ 0.1 mm/h；上尾 y ≥ Q95 = 0.574048（训练窗口目标，与全文一致）。
指标：RMSE（主）、偏差、相对月×时刻气候态的技能分（分母 0.2731）、AUC（≥Q95、≥1.0，描述性）、验证 RMSE。
配对检验（ΔRMSE = 配置 − C0，负数为改进）：
  - 种子 t 区间（5 个种子，t_{0.975,4}）；5 个种子中 Δ<0 的个数
  - 移动块自助法：块 28（7 天）、5,000 次、种子 42，与 11/14/15 一致；
    统计量为每次重抽样上"5 个种子平均的 ΔRMSE"，取 2.5/97.5 百分位
判定（预先定，多重比较下从严）：只有 5 个种子方向一致、且 t 区间与块自助法区间都不含 0 才记为"稳健"
（robust_better / robust_worse）；其余记为"不确定"，不下结论。AUC 差只描述，不作稳健判定。
运行：cd /root/autodl-tmp && python3 code/q21_stats.py 2>&1 | tee results/metrics/q21_stats_output.txt
"""
import glob
import json
import os

import numpy as np
import pandas as pd
from scipy.stats import t as tdist
from sklearn.metrics import roc_auc_score

ROOT = "/root/autodl-tmp"
RUNS, PREDS, OUT = f"{ROOT}/results/q21/runs", f"{ROOT}/results/q21/preds", f"{ROOT}/results/metrics"
CONFIGS = ["C0", "C1", "C2", "C3", "C4", "C5", "C6", "C3a", "C3b"]
# (配置, 参照)；后 4 组为探索性（C3a/C3b 在看到 C3 结果后追加，未预先设定）
COMPARISONS = [(c, "C0") for c in ["C1", "C2", "C3", "C4", "C5", "C6"]] + \
              [("C3a", "C0"), ("C3b", "C0"), ("C3", "C3a"), ("C3", "C3b")]
EXPLORATORY = {("C3a", "C0"), ("C3b", "C0"), ("C3", "C3a"), ("C3", "C3b")}
MODELS = ["xgboost", "bilstm_attn"]
SEEDS = [42, 123, 7, 2024, 99]
Q95, WET, HEAVY, CLIM_RMSE = 0.574048, 0.1, 1.0, 0.2731
BLOCK, NBOOT, BSEED = 28, 5000, 42
SUBSETS = {"all": lambda y: np.ones_like(y, bool), "wet": lambda y: y >= WET, "tail": lambda y: y >= Q95}
LABEL = {"C1": "+ws", "C2": "+z500,tcwv", "C3": "+upstream(U1,U2)", "C4": "all additions",
         "C5": "tcc→lcc", "C6": "d2m→cp (item 09)",
         "C3a": "+U1 only", "C3b": "+U2 only"}


def load():
    runs, preds = [], {}
    for f in sorted(glob.glob(f"{RUNS}/*.json")):
        r = json.load(open(f))
        runs.append({"model": r["model"], "config": r["config"], "seed": r["seed"], "n_features": r["n_features"],
                     "val_rmse": r["val"]["rmse"], "test_rmse": r["test"]["rmse"], "best_epoch": r["best_epoch"],
                     "epochs_trained": r["epochs_trained"], "train_seconds": r["train_seconds"], "gpu": r["gpu"]})
        p = pd.read_csv(f"{PREDS}/{r['tag']}.csv", parse_dates=["valid_time"])
        preds[(r["model"], r["config"], r["seed"])] = p[p.split == "test"].reset_index(drop=True)
    R = pd.DataFrame(runs)
    miss = [(m, c, s) for m in MODELS for c in CONFIGS for s in SEEDS if (m, c, s) not in preds]
    print(f"运行数 {len(R)}（主配置 70 + 探索性 20 = 90）；缺少：{miss if miss else '无'}")
    return R, preds, miss


def main():
    R, P, miss = load()
    ref = P[(MODELS[0], "C0", SEEDS[0])]
    y, t = ref["y_true"].values, ref["valid_time"].values
    assert len(y) == 3939, len(y)
    for k, p in P.items():
        assert (p["valid_time"].values == t).all() and np.allclose(p["y_true"].values, y), f"{k} 测试样本不对齐"
    masks = {k: f(y) for k, f in SUBSETS.items()}
    print("测试集 3,939 个时刻已对齐；子集样本数：" + "，".join(f"{k} {int(m.sum())}" for k, m in masks.items()))
    for m, ref_v in (("xgboost", 0.243750), ("bilstm_attn", 0.242848)):
        if (m, "C0", 42) in P:
            v = float(np.sqrt(np.mean((P[(m, "C0", 42)]["y_pred_mean"].values - y) ** 2)))
            print(f"复现：{m} C0 seed 42 = {v:.6f}（原稿 {ref_v}）{'OK' if abs(v - ref_v) < 1e-5 else 'DIFFERENT'}")

    # ---- 逐运行指标
    rows = []
    for (m, c, s), p in P.items():
        yp = p["y_pred_mean"].values
        r = {"model": m, "config": c, "seed": s}
        for k, mk in masks.items():
            r[f"rmse_{k}"] = float(np.sqrt(np.mean((yp[mk] - y[mk]) ** 2)))
            r[f"bias_{k}"] = float(np.mean(yp[mk] - y[mk]))
        r["ss_all"] = 1 - r["rmse_all"] / CLIM_RMSE
        r["auc_q95"] = roc_auc_score(y >= Q95, yp)
        r["auc_1mm"] = roc_auc_score(y >= HEAVY, yp)
        r["pred_max"], r["sd_ratio"] = float(yp.max()), float(yp.std() / y.std())
        rows.append(r)
    M = pd.DataFrame(rows).merge(R, on=["model", "config", "seed"])
    M.to_csv(f"{OUT}/q21_runs.csv", index=False)

    cols = ["rmse_all", "rmse_wet", "rmse_tail", "bias_all", "bias_tail", "ss_all", "auc_q95", "auc_1mm",
            "pred_max", "sd_ratio", "val_rmse", "best_epoch"]
    S = M.groupby(["model", "config"])[cols].agg(["mean", "std"])
    S.columns = [f"{a}_{b}" for a, b in S.columns]
    S = S.reset_index()
    S["n_features"] = S.apply(lambda r: int(M[(M.model == r.model) & (M.config == r.config)].n_features.iloc[0]), axis=1)
    S.to_csv(f"{OUT}/q21_summary.csv", index=False)

    # ---- 配对检验
    rng = np.random.default_rng(BSEED)
    n = len(y)
    nb = int(np.ceil(n / BLOCK))
    W = np.empty((NBOOT, n), dtype=np.float32)          # 每次重抽样中各样本被抽到的次数
    for b in range(NBOOT):
        st = rng.integers(0, n - BLOCK + 1, nb)
        idx = (st[:, None] + np.arange(BLOCK)).ravel()[:n]
        W[b] = np.bincount(idx, minlength=n)
    tq = tdist.ppf(0.975, len(SEEDS) - 1)
    eff = []
    for m in MODELS:
        for c, rc in COMPARISONS:
            if any((m, cc, s) not in P for cc in (rc, c) for s in SEEDS):
                continue
            for k, mk in masks.items():
                mk_f = mk.astype(np.float32)
                cnt = W @ mk_f                               # 每次重抽样的子集样本数
                d_seed, d_boot = [], np.zeros(NBOOT)
                for s in SEEDS:
                    e0 = ((P[(m, rc, s)]["y_pred_mean"].values - y) ** 2).astype(np.float32) * mk_f
                    e1 = ((P[(m, c, s)]["y_pred_mean"].values - y) ** 2).astype(np.float32) * mk_f
                    d_seed.append(np.sqrt(e1.sum() / mk.sum()) - np.sqrt(e0.sum() / mk.sum()))
                    d_boot += np.sqrt((W @ e1) / cnt) - np.sqrt((W @ e0) / cnt)
                d_seed, d_boot = np.array(d_seed), d_boot / len(SEEDS)
                mu, sd = d_seed.mean(), d_seed.std(ddof=1)
                tlo, thi = mu - tq * sd / np.sqrt(len(SEEDS)), mu + tq * sd / np.sqrt(len(SEEDS))
                blo, bhi = np.percentile(d_boot, [2.5, 97.5])
                nbet = int((d_seed < 0).sum())
                if nbet == 5 and thi < 0 and bhi < 0:
                    verdict = "robust_better"
                elif nbet == 0 and tlo > 0 and blo > 0:
                    verdict = "robust_worse"
                else:
                    verdict = "uncertain"
                base = M[(M.model == m) & (M.config == rc)][f"rmse_{k}"].mean()
                row = {"model": m, "config": c, "ref": rc, "change": LABEL[c], "subset": k, "n_subset": int(mk.sum()),
                       "exploratory": (c, rc) in EXPLORATORY, "rmse_ref": base, "d_rmse_mean": mu, "d_rmse_pct": 100 * mu / base, "d_rmse_sd": sd,
                       "t_lo": tlo, "t_hi": thi, "boot_lo": blo, "boot_hi": bhi, "n_better_of_5": nbet,
                       "verdict": verdict}
                if k == "all":
                    for a in ("auc_q95", "auc_1mm", "val_rmse"):
                        v0 = M[(M.model == m) & (M.config == rc)].set_index("seed")[a]
                        v1 = M[(M.model == m) & (M.config == c)].set_index("seed")[a]
                        dd = (v1 - v0).loc[SEEDS]
                        row[f"d_{a}"] = dd.mean()
                        row[f"n_{a}_up"] = int((dd > 0).sum())
                eff.append(row)
    E = pd.DataFrame(eff)
    E.to_csv(f"{OUT}/q21_effect.csv", index=False)

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    print("\n===== 各配置五种子均值 ± SD（测试集）=====")
    show = S[["model", "config", "n_features", "rmse_all_mean", "rmse_all_std", "rmse_wet_mean", "rmse_tail_mean",
              "bias_tail_mean", "ss_all_mean", "auc_q95_mean", "auc_1mm_mean", "val_rmse_mean", "best_epoch_mean"]]
    print(show.round(4).to_string(index=False))
    print("\n===== 配置 − 参照的 ΔRMSE（负数 = 改进；exploratory=True 为追加的探索性比较）；t 区间、块自助法区间、5 个种子中改进数 =====")
    print(E[["model", "config", "ref", "exploratory", "change", "subset", "rmse_ref", "d_rmse_mean", "d_rmse_pct", "t_lo", "t_hi",
             "boot_lo", "boot_hi", "n_better_of_5", "verdict"]].round(4).to_string(index=False))
    print("\n===== AUC 与验证 RMSE 的差（全部子集行；描述性）=====")
    print(E[E.subset == "all"][["model", "config", "ref", "change", "d_auc_q95", "n_auc_q95_up", "d_auc_1mm",
                                "n_auc_1mm_up", "d_val_rmse"]].round(4).to_string(index=False))
    print("\n===== 稳健结论（5/5 同向且两种区间都不含 0）=====")
    rb = E[E.verdict != "uncertain"]
    print(rb[["model", "config", "ref", "exploratory", "change", "subset", "d_rmse_mean", "d_rmse_pct", "verdict"]].round(4).to_string(index=False)
          if len(rb) else "无")
    print(f"\n输出：{OUT}/q21_runs.csv、q21_summary.csv、q21_effect.csv")
    if miss:
        print(f"注意：还有 {len(miss)} 个运行未完成，以上只含已完成的配置。")


if __name__ == "__main__":
    main()
