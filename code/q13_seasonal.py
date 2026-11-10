#!/usr/bin/env python3
"""q13: 季节分析（R3 L469–471、R3 §4.1、R3 §3.2(f)；R1 M2 见 07）。只用已有预测，不训练，CPU 即可。

季节按目标时刻（DJF/MAM/JJA/SON）。测试集 3,939 个时刻（2019-04-22 06:00 至 2021-12-31 18:00）。
A 季节样本：各季样本数、有雨（≥0.1）与上尾（≥Q95 = 0.574048）事件数、训练期与测试期的季节平均降水。
B 季节性能（R3 §4.1）：6 个模型 × 5 种子（14 的 W = 6 流程；XGBoost、BiLSTM-Attention、BU-LSTM-Attention 的 seed 42
  精确复现原稿）与参照（Persistence、训练期月×时刻气候态、训练期 AR(1)）。
  - RMSE（全部、上尾）、偏差
  - 标准化 RMSE：NRMSE = RMSE / 训练期该季节的平均降水（主口径，不用测试期信息）；另报除以测试期季节平均的版本作敏感性
  - 季节技能分 SS = 1 − RMSE / 同季节月×时刻气候态 RMSE
C 配对差（每季）：各模型 − 月×时刻气候态；BiLSTM-Attention − XGBoost。
  区间：种子 t（5 个种子）与季节内移动块自助法（块 28，5,000 次，种子 42；季节子序列按时间拼接，块可能跨年，表注说明）。
D 变量贡献的季节性：10/17 的单变量与按组消融预测（BiLSTM-Attention、BU-LSTM-Attention × 5 种子），
  每季 ΔRMSE = RMSE(去掉该变量) − RMSE(完整模型)，种子 t 区间与 5 个种子中变差的数量。
E 上游预测因子的季节性：21 的 C3 − C0（XGBoost、BiLSTM-Attention），每季 ΔRMSE。
证据等级（与 19、21 相同，描述性）：强 = 5/5 同向且两种区间都不含 0；中 = ≥4/5 同向且至少一种区间不含 0；其余为弱或无。
测试期各季只有 2–3 个季节样本（年份少），季节结论是描述性的，写进表注。
运行：cd /root/autodl-tmp && python3 code/q13_seasonal.py 2>&1 | tee results/metrics/q13_output.txt
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from scipy.stats import t as tdist
from q06_common import TARGET, load_regional

ROOT = "/root/autodl-tmp"
OUT = f"{ROOT}/results/metrics"
SEEDS = [42, 123, 7, 2024, 99]
Q95, WET = 0.574048, 0.1
BLOCK, NBOOT, BSEED = 28, 5000, 42
SEAS = ["DJF", "MAM", "JJA", "SON"]
SMAP = {12: "DJF", 1: "DJF", 2: "DJF", 3: "MAM", 4: "MAM", 5: "MAM", 6: "JJA", 7: "JJA", 8: "JJA", 9: "SON", 10: "SON", 11: "SON"}
Q14 = {"xgboost": "tree", "bulstm": "nll", "bilstm_attn": "mse", "transformer": "mse", "bulstm_attn": "nll",
       "prob_bilstm_attn": "nll"}
NAMES = {"xgboost": "XGBoost", "bulstm": "BU-LSTM", "bilstm_attn": "BiLSTM-Attention", "transformer": "Transformer",
         "bulstm_attn": "BU-LSTM-Attention", "prob_bilstm_attn": "Prob. BiLSTM-Attention"}
FEATS = ["mxtpr", "mntpr", "lsp", "tcc", "v10", "sp", "d2m"]
ABL = [f"no_{f}" for f in FEATS] + ["no_precip", "no_mxtpr_mntpr"]
tq = tdist.ppf(0.975, 4)


def test_part(path):
    p = pd.read_csv(path, parse_dates=["valid_time"])
    return p[p.split == "test"].reset_index(drop=True)


def rmse(a, b):
    return float(np.sqrt(np.mean((a - b) ** 2)))


def boot_w(n, rng):
    nb = int(np.ceil(n / BLOCK))
    W = np.empty((NBOOT, n), dtype=np.float32)
    for b in range(NBOOT):
        st = rng.integers(0, max(n - BLOCK + 1, 1), nb)
        W[b] = np.bincount((st[:, None] + np.arange(BLOCK)).ravel()[:n] % n, minlength=n)
    return W


def level(nbet, tlo, thi, blo, bhi):
    t_ex, b_ex = (thi < 0 or tlo > 0), (bhi < 0 or blo > 0)
    if nbet in (0, 5) and t_ex and b_ex:
        return "strong"
    if (nbet >= 4 or nbet <= 1) and (t_ex or b_ex):
        return "medium(" + ("seed-t" if t_ex else "block-bootstrap") + ")"
    return "weak/none"


def main():
    # ---- 训练期（原 70/15/15 划分的前 70%，按目标时刻）与参照
    df = load_regional()
    d = df[df["valid_time"].dt.year >= 2004].reset_index(drop=True)
    assert len(d) == 26300
    tr = d.iloc[:int(len(d) * .70)]
    y_tr, t_tr = tr[TARGET].values, pd.DatetimeIndex(tr["valid_time"])
    clim = pd.Series(y_tr).groupby([t_tr.month, t_tr.hour]).mean()
    b_ar = np.polyfit(y_tr[:-1], y_tr[1:], 1)                       # AR(1): y(t+6h) = a·y(t) + c，训练期 OLS
    seas_mean_tr = pd.Series(y_tr).groupby(pd.Series(t_tr.month).map(SMAP).values).mean()

    # ---- 测试预测
    P = {m: {s: test_part(f"{ROOT}/results/q14/preds/{m}__w6__{l}__s{s}.csv") for s in SEEDS} for m, l in Q14.items()}
    ref = P["xgboost"][42]
    y, t = ref["y_true"].values, pd.DatetimeIndex(ref["valid_time"])
    assert len(y) == 3939
    for m in P:
        for s in SEEDS:
            assert (P[m][s]["valid_time"].values == ref["valid_time"].values).all(), f"{m} s{s} 未对齐"
    seas = np.array([SMAP[x] for x in t.month])
    pers = ref["persistence"].values
    refs = {"Persistence": pers,
            "Clim (month×hour)": np.array([clim[(mo, hr)] for mo, hr in zip(t.month, t.hour)]),
            "AR(1)": np.polyval(b_ar, pers)}
    print(f"核对全测试集：月×时刻气候态 RMSE {rmse(refs['Clim (month×hour)'], y):.4f}（S11 为 .2731），"
          f"Persistence {rmse(pers, y):.4f}（Table 3 为 .3282），AR(1) {rmse(refs['AR(1)'], y):.4f}")
    for m, ref42 in (("xgboost", 0.243750), ("bilstm_attn", 0.242848), ("bulstm_attn", 0.246413)):
        print(f"复现 {NAMES[m]} seed 42：{rmse(P[m][42].y_pred_mean.values, y):.6f}（原稿 {ref42}）")

    # ---- A 季节样本
    A = []
    for sn in SEAS:
        mk = seas == sn
        A.append({"season": sn, "n_test": int(mk.sum()), "wet_test": int((y[mk] >= WET).sum()),
                  "tail_test": int((y[mk] >= Q95).sum()), "mean_train": seas_mean_tr[sn], "mean_test": y[mk].mean(),
                  "wetfreq_train": float((y_tr[pd.Series(t_tr.month).map(SMAP).values == sn] >= WET).mean()),
                  "wetfreq_test": float((y[mk] >= WET).mean())})
    A = pd.DataFrame(A)
    A.to_csv(f"{OUT}/q13_season_counts.csv", index=False)

    # ---- B 季节性能
    rows = []
    for sn in SEAS + ["all"]:
        mk = np.ones_like(y, bool) if sn == "all" else seas == sn
        tk = mk & (y >= Q95)
        mtr = y_tr.mean() if sn == "all" else seas_mean_tr[sn]
        crm = rmse(refs["Clim (month×hour)"][mk], y[mk])
        for name, yp in refs.items():
            r = rmse(yp[mk], y[mk])
            rows.append({"season": sn, "model": name, "rmse": r, "rmse_sd": 0.0, "nrmse_train": r / mtr,
                         "nrmse_test": r / y[mk].mean(), "ss_clim": 1 - r / crm, "rmse_tail": rmse(yp[tk], y[tk]),
                         "bias": float(np.mean(yp[mk] - y[mk]))})
        for m in P:
            rs = np.array([rmse(P[m][s].y_pred_mean.values[mk], y[mk]) for s in SEEDS])
            rt = np.array([rmse(P[m][s].y_pred_mean.values[tk], y[tk]) for s in SEEDS])
            bs = np.array([np.mean(P[m][s].y_pred_mean.values[mk] - y[mk]) for s in SEEDS])
            rows.append({"season": sn, "model": NAMES[m], "rmse": rs.mean(), "rmse_sd": rs.std(ddof=1),
                         "nrmse_train": rs.mean() / mtr, "nrmse_test": rs.mean() / y[mk].mean(),
                         "ss_clim": 1 - rs.mean() / crm, "rmse_tail": rt.mean(), "bias": bs.mean()})
    B = pd.DataFrame(rows)
    B.to_csv(f"{OUT}/q13_season_metrics.csv", index=False)

    # ---- C 季节配对差
    rng = np.random.default_rng(BSEED)
    crows = []

    def paired(sn, mk, new_list, ref_list, label, model):
        yy = y[mk]
        W = boot_w(mk.sum(), rng)
        ds, db = [], np.zeros(NBOOT)
        for a_, b_ in zip(new_list, ref_list):
            e1, e0 = ((a_[mk] - yy) ** 2).astype(np.float32), ((b_[mk] - yy) ** 2).astype(np.float32)
            ds.append(np.sqrt(e1.mean()) - np.sqrt(e0.mean()))
            db += np.sqrt((W @ e1) / mk.sum()) - np.sqrt((W @ e0) / mk.sum())
        ds, db = np.array(ds), db / len(ds)
        mu, sd = ds.mean(), ds.std(ddof=1)
        tlo, thi = mu - tq * sd / np.sqrt(5), mu + tq * sd / np.sqrt(5)
        blo, bhi = np.percentile(db, [2.5, 97.5])
        nbet = int((ds < 0).sum())
        base = np.mean([np.sqrt(np.mean((b_[mk] - yy) ** 2)) for b_ in ref_list])
        return {"season": sn, "model": model, "comparison": label, "n": int(mk.sum()), "rmse_ref": base,
                "delta": mu, "pct": 100 * mu / base, "t_lo": tlo, "t_hi": thi, "boot_lo": blo, "boot_hi": bhi,
                "n_better_of_5": nbet, "evidence": level(nbet, tlo, thi, blo, bhi)}

    cl = refs["Clim (month×hour)"]
    for sn in SEAS + ["all"]:
        mk = np.ones_like(y, bool) if sn == "all" else seas == sn
        for m in P:
            crows.append(paired(sn, mk, [P[m][s].y_pred_mean.values for s in SEEDS], [cl] * 5,
                                "model − clim(month×hour)", NAMES[m]))
        crows.append(paired(sn, mk, [P["bilstm_attn"][s].y_pred_mean.values for s in SEEDS],
                            [P["xgboost"][s].y_pred_mean.values for s in SEEDS], "BiLSTM-Attention − XGBoost", "pair"))
    C = pd.DataFrame(crows)
    C.to_csv(f"{OUT}/q13_season_paired.csv", index=False)

    # ---- D 变量贡献的季节性（10/17 消融预测）
    drows = []
    for arch in ["bilstm_attn", "bulstm_attn"]:
        full = {s: test_part(f"{ROOT}/results/q10/preds/{arch}__full__s{s}.csv") for s in SEEDS}
        for s in SEEDS:
            assert (full[s]["valid_time"].values == ref["valid_time"].values).all(), f"q10 {arch} 测试时刻未对齐"
        for cfg in ABL:
            path = f"{ROOT}/results/q10/preds/{arch}__{cfg}__s42.csv"
            if not os.path.exists(path):
                continue
            ab = {s: test_part(f"{ROOT}/results/q10/preds/{arch}__{cfg}__s{s}.csv") for s in SEEDS}
            for sn in SEAS + ["all"]:
                mk = np.ones_like(y, bool) if sn == "all" else seas == sn
                for sub, mm in (("all", mk), ("tail", mk & (y >= Q95))):
                    ds = np.array([rmse(ab[s].y_pred_mean.values[mm], y[mm]) - rmse(full[s].y_pred_mean.values[mm], y[mm])
                                   for s in SEEDS])
                    mu, sd = ds.mean(), ds.std(ddof=1)
                    drows.append({"arch": NAMES[arch], "removed": {"no_precip": "group:mxtpr+mntpr+lsp", "no_mxtpr_mntpr": "group:mxtpr+mntpr"}.get(cfg, cfg[3:]), "season": sn, "subset": sub,
                                  "n": int(mm.sum()), "d_rmse": mu, "t_lo": mu - tq * sd / np.sqrt(5),
                                  "t_hi": mu + tq * sd / np.sqrt(5), "n_worse_of_5": int((ds > 0).sum())})
    D = pd.DataFrame(drows)
    D.to_csv(f"{OUT}/q13_season_ablation.csv", index=False)

    # ---- E 上游预测因子的季节性（21）
    erows = []
    for m, l in (("xgboost", "tree"), ("bilstm_attn", "mse")):
        c0 = [test_part(f"{ROOT}/results/q21/preds/{m}__w6__C0__{l}__s{s}.csv").y_pred_mean.values for s in SEEDS]
        c3 = [test_part(f"{ROOT}/results/q21/preds/{m}__w6__C3__{l}__s{s}.csv").y_pred_mean.values for s in SEEDS]
        for sn in SEAS + ["all"]:
            mk = np.ones_like(y, bool) if sn == "all" else seas == sn
            erows.append(paired(sn, mk, c3, c0, "C3 − C0 (upstream)", NAMES[m]))
    E = pd.DataFrame(erows)
    E.to_csv(f"{OUT}/q13_season_upstream.csv", index=False)

    # ---- 输出
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print("\n===== A 季节样本 =====")
    print(A.round(4).to_string(index=False))
    print("\n===== B 季节性能（RMSE 为五种子均值；NRMSE 主口径 = RMSE / 训练期季节平均）=====")
    for col in ["rmse", "nrmse_train", "ss_clim", "rmse_tail", "bias"]:
        print(f"\n-- {col}")
        print(B.pivot(index="model", columns="season", values=col)[SEAS + ["all"]].round(4).to_string())
    print("\n===== C 季节配对差（负数 = 模型优于参照 / BiLSTM-Attention 优于 XGBoost）=====")
    print(C.round(4).to_string(index=False))
    print("\n===== D 单变量 / 按组消融的季节 ΔRMSE（正数 = 去掉后变差；全部子集）=====")
    for arch in D.arch.unique():
        sub = D[(D.arch == arch) & (D.subset == "all")]
        print(f"\n-- {arch}（括号内为 5 个种子中变差的数量）")
        piv = sub.pivot(index="removed", columns="season", values="d_rmse")[SEAS + ["all"]]
        cnt = sub.pivot(index="removed", columns="season", values="n_worse_of_5")[SEAS + ["all"]]
        print((piv.round(4).astype(str) + " (" + cnt.astype(int).astype(str) + ")").to_string())
    print("\n===== E 上游预测因子 C3 − C0 的季节 ΔRMSE =====")
    print(E.round(4).to_string(index=False))
    print(f"\n输出：{OUT}/q13_season_counts.csv、q13_season_metrics.csv、q13_season_paired.csv、"
          f"q13_season_ablation.csv、q13_season_upstream.csv")


if __name__ == "__main__":
    main()
