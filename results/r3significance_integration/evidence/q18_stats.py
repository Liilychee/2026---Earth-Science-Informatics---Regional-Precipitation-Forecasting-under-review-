#!/usr/bin/env python3
"""q18 统计：模型之间小幅差别的显著性，与复杂度（参数量、训练时间）放在一起看。CPU 即可。

预测来源（主 70/15/15 划分，W = 6，5 个种子，测试 3,939 个时刻）
  XGBoost、BiLSTM-Attention：results/q21/preds 的 C0（与 Table 3、原稿 seed 42 逐位一致）
  BU-LSTM、Transformer、BU-LSTM-Attention、Prob. BiLSTM-Attention：results/q14/preds 的 W = 6
  BiLSTM-NoAttention：results/q18/preds（q18_noattn.py，同一确定性流程重跑）
  参照：Persistence；训练期月×时刻气候态；训练期 AR(1)（OLS）
预定比较（2026-11-10 定，结果出来后不改）
  主问题（R3 L822–824）：BiLSTM-Attention − BiLSTM-NoAttention
  架构：BiLSTM-Attention − XGBoost；Transformer、BU-LSTM、BU-LSTM-Attention、Prob. BiLSTM-Attention、BiLSTM-NoAttention 各 − XGBoost；
        BU-LSTM-Attention − BU-LSTM；BU-LSTM-Attention − Prob. BiLSTM-Attention（三层对一层）
  参照：每个模型 − AR(1)
  指标：RMSE（全部 / 有雨 ≥0.1 / 上尾 ≥ Q95 = 0.574048）；两组概率模型比较另报全部样本的 Gaussian CRPS
区间与检验
  种子 t 区间与 t 检验 p（5 个种子，反映训练随机性）；
  移动块自助法（块 28，5,000 次，种子 42）上"5 个种子平均 Δ"的 95% 区间与双侧 p（反映测试样本的时间抽样）；
  多重比较：只对"全部样本 RMSE"这一主指标、在整个预定比较族内做 Holm 校正（两种 p 分别校正）；子集与 CRPS 只描述。
  证据等级（描述性，与 19、21 相同）：强 = 5/5 同向且两种区间都不含 0；中 = ≥4/5 同向且至少一种区间不含 0；其余弱或无。
复杂度：可训练参数量（count_params）与单次平均训练时间（q19/q18 的 train_seconds；XGBoost 用 q19）。
运行：cd /root/autodl-tmp && python3 code/q18_stats.py 2>&1 | tee results/metrics/q18_stats_output.txt
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import norm, t as tdist

ROOT = "/root/autodl-tmp"
sys.path.insert(0, f"{ROOT}/code")
from q06_common import TARGET, load_regional  # noqa: E402

OUT = f"{ROOT}/results/metrics"
SEEDS = [42, 123, 7, 2024, 99]
Q95, WET = 0.574048, 0.1
BLOCK, NBOOT, BSEED = 28, 5000, 42
SRC = {
    "XGBoost": ("q21", "xgboost__w6__C0__tree"),
    "BiLSTM-Attention": ("q21", "bilstm_attn__w6__C0__mse"),
    "BiLSTM-NoAttention": ("q18", "bilstm_noattn__w6"),
    "BU-LSTM": ("q14", "bulstm__w6__nll"),
    "BU-LSTM-Attention": ("q14", "bulstm_attn__w6__nll"),
    "Prob. BiLSTM-Attention": ("q14", "prob_bilstm_attn__w6__nll"),
    "Transformer": ("q14", "transformer__w6__mse"),
}
SAME = "BiLSTM-Attention (same card)"
if os.path.exists(f"{ROOT}/results/q18/preds/bilstm_attn_samecard__w6__s42.csv"):
    SRC[SAME] = ("q18", "bilstm_attn_samecard__w6")
PROB = {"BU-LSTM", "BU-LSTM-Attention", "Prob. BiLSTM-Attention"}
# 预定：若有同卡重跑的 BiLSTM-Attention（NoAttention 不在 5090 上训练时），主问题用同卡这一对；跨卡那一对只描述、不进 Holm 族
PAIRS = ([(SAME, "BiLSTM-NoAttention", "attention (R3 L822-824), same card"),
          ("BiLSTM-Attention", "BiLSTM-NoAttention", "attention, cross-card (descriptive)")] if SAME in SRC else
         [("BiLSTM-Attention", "BiLSTM-NoAttention", "attention (R3 L822-824)")]) + [
         ("BiLSTM-Attention", "XGBoost", "architecture"),
         ("Transformer", "XGBoost", "architecture"),
         ("BU-LSTM", "XGBoost", "architecture"),
         ("BU-LSTM-Attention", "XGBoost", "architecture"),
         ("Prob. BiLSTM-Attention", "XGBoost", "architecture"),
         ("BiLSTM-NoAttention", "XGBoost", "architecture"),
         ("BU-LSTM-Attention", "BU-LSTM", "attention, probabilistic"),
         ("BU-LSTM-Attention", "Prob. BiLSTM-Attention", "depth 3 vs 1, probabilistic")]
PAIRS += [(m, "AR(1)", "vs reference") for m in SRC]
NAME = {"XGBoost": "xgboost", "BiLSTM-Attention": "bilstm_attn", "BU-LSTM": "bulstm", "BU-LSTM-Attention": "bulstm_attn",
        "Prob. BiLSTM-Attention": "prob_bilstm_attn", "Transformer": "transformer"}


def test_part(path):
    p = pd.read_csv(path, parse_dates=["valid_time"])
    return p[p.split == "test"].reset_index(drop=True)


def crps(y, mu, sd):
    z = (y - mu) / sd
    return sd * (z * (2 * norm.cdf(z) - 1) + 2 * norm.pdf(z) - 1 / np.sqrt(np.pi))


def holm(p):
    p = np.asarray(p, float); m = len(p); o = np.argsort(p)
    adj = np.empty(m); run = 0.0
    for r, i in enumerate(o):
        run = max(run, (m - r) * p[i]); adj[i] = min(run, 1.0)
    return adj


def level(nbet, tlo, thi, blo, bhi):
    t_ex, b_ex = (thi < 0 or tlo > 0), (bhi < 0 or blo > 0)
    if nbet in (0, 5) and t_ex and b_ex:
        return "strong"
    if (nbet >= 4 or nbet <= 1) and (t_ex or b_ex):
        return "medium(" + ("seed-t" if t_ex else "block-bootstrap") + ")"
    return "weak/none"


def main():
    P = {m: {s: test_part(f"{ROOT}/results/{d}/preds/{tag}__s{s}.csv") for s in SEEDS} for m, (d, tag) in SRC.items()}
    ref = P["XGBoost"][42]
    y, t = ref["y_true"].values, pd.DatetimeIndex(ref["valid_time"])
    for m in P:
        for s in SEEDS:
            assert (P[m][s]["valid_time"].values == ref["valid_time"].values).all(), f"{m} s{s} 未对齐"
    d = load_regional(); d = d[d["valid_time"].dt.year >= 2004].reset_index(drop=True)
    tr = d.iloc[:int(len(d) * .70)]; ytr, ttr = tr[TARGET].values, pd.DatetimeIndex(tr["valid_time"])
    clim = pd.Series(ytr).groupby([ttr.month, ttr.hour]).mean()
    pers = P["Transformer"][42]["persistence"].values
    ar = np.polyval(np.polyfit(ytr[:-1], ytr[1:], 1), pers)
    refs = {"AR(1)": ar, "Clim (month×hour)": np.array([clim[(a, b)] for a, b in zip(t.month, t.hour)]),
            "Persistence": pers}
    rm = lambda a: float(np.sqrt(np.mean((a - y) ** 2)))
    print(f"核对：月×时刻气候态 {rm(refs['Clim (month×hour)']):.4f}（.2731），AR(1) {rm(ar):.4f}（.2627），"
          f"Persistence {rm(pers):.4f}（.3282）")
    for m, r42 in (("XGBoost", .243750), ("BiLSTM-Attention", .242848)):
        print(f"复现 {m} seed 42：{rm(P[m][42].y_pred_mean.values):.6f}（原稿 {r42}）")

    # 五种子均值与复杂度
    runs19 = [json.load(open(f)) for f in glob.glob(f"{ROOT}/results/q19/runs/*.json")]
    runs18 = [json.load(open(f)) for f in glob.glob(f"{ROOT}/results/q18/runs/*.json")]
    params = {"BU-LSTM": 83802, "BiLSTM-Attention": 45313, "Transformer": 8833, "BU-LSTM-Attention": 243074,
              "Prob. BiLSTM-Attention": 45442, "XGBoost": np.nan}
    for r in runs18:
        params[SAME if r["tag"].startswith("bilstm_attn_samecard") else "BiLSTM-NoAttention"] = r["n_params"]
    gpus = sorted({r.get("gpu", "?") for r in runs18})
    print(f"q18 运行所在 GPU：{gpus}")
    tsec = {}
    for m, key in NAME.items():
        v = [r["train_seconds"] for r in runs19 if r["model"] == key]
        tsec[m] = float(np.mean(v)) if v else np.nan
    for m, pre in (("BiLSTM-NoAttention", "bilstm_noattn"), (SAME, "bilstm_attn_samecard")):
        v = [r["train_seconds"] for r in runs18 if r["tag"].startswith(pre)]
        tsec[m] = float(np.mean(v)) if v else np.nan
    S = pd.DataFrame({m: {"rmse_mean": np.mean([rm(P[m][s].y_pred_mean.values) for s in SEEDS]),
                          "rmse_sd": np.std([rm(P[m][s].y_pred_mean.values) for s in SEEDS], ddof=1),
                          "params": params.get(m, np.nan), "train_s_mean": tsec.get(m, np.nan)} for m in SRC}).T
    S["ss_clim"] = 1 - S.rmse_mean / rm(refs["Clim (month×hour)"])
    S = S.sort_values("rmse_mean")
    S.to_csv(f"{OUT}/q18_model_summary.csv")

    # 配对检验
    masks = {"all": np.ones_like(y, bool), "wet": y >= WET, "tail": y >= Q95}
    n = len(y); nb = int(np.ceil(n / BLOCK)); rng = np.random.default_rng(BSEED)
    W = np.empty((NBOOT, n), dtype=np.float32)
    for b in range(NBOOT):
        st = rng.integers(0, n - BLOCK + 1, nb)
        W[b] = np.bincount((st[:, None] + np.arange(BLOCK)).ravel()[:n], minlength=n)
    tq = tdist.ppf(0.975, 4)
    get = lambda m, s: refs[m] if m in refs else P[m][s].y_pred_mean.values
    rows = []
    for a, b, grp in PAIRS:
        mets = [("rmse", k) for k in masks]
        if a in PROB and b in PROB:
            mets.append(("crps", "all"))
        for met, k in mets:
            mk = masks[k]; mf = mk.astype(np.float32); cnt = W @ mf
            ds, db, base = [], np.zeros(NBOOT), []
            for s in SEEDS:
                if met == "rmse":
                    e1 = ((get(a, s) - y) ** 2).astype(np.float32) * mf
                    e0 = ((get(b, s) - y) ** 2).astype(np.float32) * mf
                    r1, r0 = np.sqrt(e1.sum() / mk.sum()), np.sqrt(e0.sum() / mk.sum())
                    db += np.sqrt((W @ e1) / cnt) - np.sqrt((W @ e0) / cnt)
                else:
                    e1 = crps(y, P[a][s].y_pred_mean.values, P[a][s].y_pred_std.values).astype(np.float32)
                    e0 = crps(y, P[b][s].y_pred_mean.values, P[b][s].y_pred_std.values).astype(np.float32)
                    r1, r0 = e1.mean(), e0.mean()
                    db += (W @ e1) / n - (W @ e0) / n
                ds.append(r1 - r0); base.append(r0)
            ds, db = np.array(ds), db / 5
            mu, sd = ds.mean(), ds.std(ddof=1)
            se = sd / np.sqrt(5)
            p_seed = float(2 * tdist.sf(abs(mu / se), 4)) if se > 0 else 0.0
            p_boot = float(min(1.0, 2 * min((db <= 0).mean(), (db >= 0).mean())))
            tlo, thi = mu - tq * se, mu + tq * se
            blo, bhi = np.percentile(db, [2.5, 97.5])
            nbet = int((ds < 0).sum())
            rows.append({"a": a, "b": b, "group": grp, "metric": met, "subset": k, "ref_b": np.mean(base),
                         "delta": mu, "pct": 100 * mu / np.mean(base), "t_lo": tlo, "t_hi": thi,
                         "boot_lo": blo, "boot_hi": bhi, "n_a_better_of_5": nbet, "p_seed_t": p_seed,
                         "p_boot": p_boot, "evidence": level(nbet, tlo, thi, blo, bhi),
                         "d_params": params.get(a, np.nan) - params.get(b, np.nan) if b not in refs else np.nan,
                         "train_s_a": tsec.get(a, np.nan), "train_s_b": tsec.get(b, np.nan)})
    E = pd.DataFrame(rows)
    prim = (E.metric == "rmse") & (E.subset == "all") & ~E.group.str.contains("descriptive")
    E.loc[prim, "p_seed_holm"] = holm(E.loc[prim, "p_seed_t"].values)
    E.loc[prim, "p_boot_holm"] = holm(E.loc[prim, "p_boot"].values)
    E.to_csv(f"{OUT}/q18_pairwise.csv", index=False)

    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 30)
    print("\n===== 五种子均值、技能分与复杂度 =====")
    print(S.round(4).to_string())
    print(f"参照：AR(1) {rm(ar):.4f}；月×时刻气候态 {rm(refs['Clim (month×hour)']):.4f}；Persistence {rm(pers):.4f}")
    print("\n===== 主指标（全部样本 RMSE）配对差，负数 = a 更好；Holm 校正（整个预定比较族）=====")
    print(E[prim][["a", "b", "group", "ref_b", "delta", "pct", "t_lo", "t_hi", "boot_lo", "boot_hi", "n_a_better_of_5",
                   "p_seed_t", "p_seed_holm", "p_boot", "p_boot_holm", "evidence", "d_params", "train_s_a", "train_s_b"]]
          .round(4).to_string(index=False))
    print("\n===== 子集与 CRPS（只描述，不做多重校正）=====")
    print(E[~prim][["a", "b", "metric", "subset", "ref_b", "delta", "pct", "t_lo", "t_hi", "boot_lo", "boot_hi",
                    "n_a_better_of_5", "evidence"]].round(4).to_string(index=False))
    print(f"\n输出：{OUT}/q18_model_summary.csv、q18_pairwise.csv")


if __name__ == "__main__":
    main()
