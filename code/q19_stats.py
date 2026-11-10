#!/usr/bin/env python3
"""q19 统计：把"延长训练轮数上限"和"按验证集调参"两种作用分开。CPU 即可。

组别（同模型、同种子配对）
  A 原参数、原轮数上限（30）：bilstm_attn 用 q21 的 C0；transformer/bulstm/bulstm_attn/prob_bilstm_attn 用 14 的 W = 6
  B 原参数、加长上限：bilstm_attn 60 轮；其余深度模型 100 轮
  C 验证集选出的参数、加长上限
  xgboost 没有轮数上限：A = B = 原配置（q19 重跑），只比 C − A
比较：B − A（只改上限）、C − B（只改参数）、C − A（合计）；C 与 B 相同时不比 C − B。
指标：RMSE（全部 / 有雨 y ≥ 0.1 / 上尾 y ≥ Q95 = 0.574048）；三个 Gaussian 概率模型另报全部样本的平均 CRPS（mm）。
  按观测取子集的 CRPS 不是严格评分，所以 CRPS 只在全部样本上比较。
区间：种子 t 区间（5 个种子，反映训练随机性）；移动块自助法（块 28，5,000 次，种子 42，反映测试样本的时间抽样波动）。
  两者衡量的不确定性来源不同，不视为相互独立的两次检验。
证据等级（2026-11-09 预先定，是描述性等级，不是新的显著性检验）：
  强 = 5/5 同向且两种区间都不含 0；中 = ≥4/5 同向且至少一种区间不含 0（注明哪一种）；弱或无 = 其余
实际重要性门槛 |Δ| ≥ 1%：只用于决定是否写进正文讨论，不是显著性标准。
正文触发：XGBoost 与 BiLSTM-Attention 排名改变；任一 C − A 达到中或强且 |Δ| ≥ 1%；6 个模型（A 对 C）排名有任何改变。
运行：cd /root/autodl-tmp && python3 code/q19_stats.py 2>&1 | tee results/metrics/q19_stats_output.txt
"""
import glob
import json

import numpy as np
import pandas as pd
from scipy.stats import norm, t as tdist

ROOT = "/root/autodl-tmp"
Q19, Q14, Q21, OUT = (f"{ROOT}/results/q19", f"{ROOT}/results/q14", f"{ROOT}/results/q21", f"{ROOT}/results/metrics")
SEEDS = [42, 123, 7, 2024, 99]
Q95, WET = 0.574048, 0.1
BLOCK, NBOOT, BSEED = 28, 5000, 42
ORIG = {"xgboost": {"n": 100, "lr": 0.05, "depth": 6}, "bilstm_attn": {"units": 64, "lr": 1e-3, "dropout": 0.2}}
LIGHT = ["transformer", "bulstm", "bulstm_attn", "prob_bilstm_attn"]
PROB = ["bulstm", "bulstm_attn", "prob_bilstm_attn"]
Q14_LOSS = {"transformer": "mse", "bulstm": "nll", "bulstm_attn": "nll", "prob_bilstm_attn": "nll"}
NAMES = {"xgboost": "XGBoost", "bilstm_attn": "BiLSTM-Attention", "transformer": "Transformer", "bulstm": "BU-LSTM",
         "bulstm_attn": "BU-LSTM-Attention", "prob_bilstm_attn": "Prob. BiLSTM-Attention"}


def crps_gauss(y, mu, sd):
    z = (y - mu) / sd
    return sd * (z * (2 * norm.cdf(z) - 1) + 2 * norm.pdf(z) - 1 / np.sqrt(np.pi))


def load(path):
    p = pd.read_csv(path, parse_dates=["valid_time"])
    return {k: p[p.split == k].reset_index(drop=True) for k in ("val", "test")}


def level(nbet, tlo, thi, blo, bhi):
    t_ex, b_ex = (thi < 0 or tlo > 0), (bhi < 0 or blo > 0)
    if nbet in (0, 5) and t_ex and b_ex:
        return "strong"
    if (nbet >= 4 or nbet <= 1) and (t_ex or b_ex):
        return "medium(" + ("seed-t" if t_ex else "block-bootstrap") + ")"
    return "weak/none"


def main():
    R = [json.load(open(f)) for f in glob.glob(f"{Q19}/runs/*.json")]
    print(f"q19 运行数 {len(R)}")
    g = pd.DataFrame([{"model": r["model"], **{f"cfg_{k}": v for k, v in r["config"].items()}, "cap": r["cap"],
                       "seed": r["seed"], "val_rmse": r["val"]["rmse"], "val_crps": r["val"].get("crps"),
                       "test_rmse": r["test"]["rmse"], "test_crps": r["test"].get("crps"),
                       "best_epoch": r["best_epoch"], "epochs_trained": r["epochs_trained"], "hit_cap": r["hit_cap"]}
                      for r in R])
    g.to_csv(f"{OUT}/q19_all_runs.csv", index=False)          # 全部候选（含原参数）的验证与测试结果
    sel = {m: json.load(open(f"{Q19}/selection_{m}.json")) for m in ["xgboost", "bilstm_attn"] + LIGHT
           if glob.glob(f"{Q19}/selection_{m}.json")}

    def q19set(m, cfg, cap):
        rs = {r["seed"]: r for r in R if r["model"] == m and r["config"] == cfg and r["cap"] == cap}
        return {s: load(f"{Q19}/preds/{rs[s]['tag']}.csv") for s in SEEDS} if all(s in rs for s in SEEDS) else None

    groups = {}       # model -> {"A":..., "B":..., "C":...}，每组 {seed: {"val": df, "test": df}}
    for m in ["xgboost", "bilstm_attn"]:
        if m not in sel:
            continue
        s_ = sel[m]
        print(f"\n[{NAMES[m]}] 选定 {s_['selected']}（原 {ORIG[m]}；原配置在前 3：{s_['original_in_top3']}）；前 3 的 3 种子验证均值："
              + "，".join(f"{t['config']}={t['mean']:.6f}" for t in s_["top3"]))
        gs = g[(g.model == m) & (g.seed == 42)].sort_values("val_rmse").reset_index(drop=True)
        is_o = np.all([gs[f"cfg_{k}"] == v for k, v in ORIG[m].items()], axis=0)
        if is_o.any():
            print(f"  seed 42 网格 {len(gs)} 组，原配置验证排名 {int(np.where(is_o)[0][0]) + 1}")
        cap = s_["cap"]
        G = {"B": q19set(m, ORIG[m], cap), "C": q19set(m, s_["selected"], cap)}
        if m == "xgboost":
            G["A"] = G["B"]; G.pop("B")
        else:
            G["A"] = {s: load(f"{Q21}/preds/bilstm_attn__w6__C0__mse__s{s}.csv") for s in SEEDS}
        groups[m] = G
    for m in LIGHT:
        if m not in sel:
            continue
        s_ = sel[m]
        print(f"[{NAMES[m]}] 按 {s_['selection_metric']} 选学习率：选定 {s_['selected']}；seed 42 验证："
              + "，".join(f"lr {k}: rmse {v['rmse']:.5f}" + (f", crps {v['crps']:.5f}" if 'crps' in v else "")
                         for k, v in s_["seed42_val"].items()))
        G = {"A": {s: load(f"{Q14}/preds/{m}__w6__{Q14_LOSS[m]}__s{s}.csv") for s in SEEDS},
             "B": q19set(m, {"lr": 1e-3}, 100), "C": q19set(m, s_["selected"], 100)}
        groups[m] = G
        rb = [r for r in R if r["model"] == m and r["config"] == {"lr": 1e-3} and r["cap"] == 100]
        if rb:
            print(f"  B 组（lr 1e-3，上限 100）best epoch {[r['best_epoch'] for r in sorted(rb, key=lambda r: SEEDS.index(r['seed']))]}，"
                  f"跑满上限 {sum(bool(r['hit_cap']) for r in rb)}/{len(rb)}")

    # 原配置在加长上限下与 A 组是否一致（只延长上限、早停在 30 轮前时应完全一致）
    for m in ["bilstm_attn"] + LIGHT:
        G = groups.get(m)
        if G and G.get("B"):
            dmax = max(np.abs(G["B"][s]["test"].y_pred_mean.values - G["A"][s]["test"].y_pred_mean.values).max() for s in SEEDS)
            print(f"[{NAMES[m]}] B 与 A 测试预测最大差 {dmax:.2e}（为 0 说明 A 组从未受 30 轮上限限制）")

    # 自助法权重
    any_set = next(iter(next(iter(groups.values())).values()))
    y = any_set[SEEDS[0]]["test"].y_true.values
    t0 = any_set[SEEDS[0]]["test"].valid_time.values
    masks = {"all": np.ones_like(y, bool), "wet": y >= WET, "tail": y >= Q95}
    n = len(y); nb = int(np.ceil(n / BLOCK))
    rng = np.random.default_rng(BSEED)
    W = np.empty((NBOOT, n), dtype=np.float32)
    for b in range(NBOOT):
        st = rng.integers(0, n - BLOCK + 1, nb)
        W[b] = np.bincount((st[:, None] + np.arange(BLOCK)).ravel()[:n], minlength=n)
    tq = tdist.ppf(0.975, 4)

    def compare(m, new, ref, label):
        for s in SEEDS:
            for dct in (new, ref):
                assert (dct[s]["test"].valid_time.values == t0).all() and np.allclose(dct[s]["test"].y_true.values, y)
        vr = lambda G: np.mean([np.sqrt(np.mean((G[s]["val"].y_pred_mean - G[s]["val"].y_true) ** 2)) for s in SEEDS])
        out = []
        metrics = [("rmse", k, mk) for k, mk in masks.items()]
        if m in PROB:
            metrics.append(("crps", "all", masks["all"]))
        for met, k, mk in metrics:
            mf = mk.astype(np.float32); cnt = W @ mf
            ds, db, a0, a1 = [], np.zeros(NBOOT), [], []
            for s in SEEDS:
                if met == "rmse":
                    e1 = ((new[s]["test"].y_pred_mean.values - y) ** 2).astype(np.float32) * mf
                    e0 = ((ref[s]["test"].y_pred_mean.values - y) ** 2).astype(np.float32) * mf
                    v1, v0 = np.sqrt(e1.sum() / mk.sum()), np.sqrt(e0.sum() / mk.sum())
                    db += np.sqrt((W @ e1) / cnt) - np.sqrt((W @ e0) / cnt)
                else:
                    e1 = crps_gauss(y, new[s]["test"].y_pred_mean.values, new[s]["test"].y_pred_std.values).astype(np.float32)
                    e0 = crps_gauss(y, ref[s]["test"].y_pred_mean.values, ref[s]["test"].y_pred_std.values).astype(np.float32)
                    v1, v0 = e1.mean(), e0.mean()
                    db += (W @ e1) / n - (W @ e0) / n
                ds.append(v1 - v0); a1.append(v1); a0.append(v0)
            ds, db = np.array(ds), db / 5
            mu, sd = ds.mean(), ds.std(ddof=1)
            tlo, thi = mu - tq * sd / np.sqrt(5), mu + tq * sd / np.sqrt(5)
            blo, bhi = np.percentile(db, [2.5, 97.5])
            nbet = int((ds < 0).sum())
            out.append({"model": NAMES[m], "comparison": label, "metric": met, "subset": k,
                        "ref": np.mean(a0), "new": np.mean(a1), "delta": mu, "pct": 100 * mu / np.mean(a0),
                        "t_lo": tlo, "t_hi": thi, "boot_lo": blo, "boot_hi": bhi, "n_better_of_5": nbet,
                        "evidence": level(nbet, tlo, thi, blo, bhi),
                        "val_rmse_ref": vr(ref) if (met, k) == ("rmse", "all") else np.nan,
                        "val_rmse_new": vr(new) if (met, k) == ("rmse", "all") else np.nan})
        return out

    rows, final = [], {}
    for m, G in groups.items():
        same_bc = G.get("B") is not None and sel[m]["selected"] == (ORIG.get(m) or {"lr": 1e-3})
        if G.get("B") is not None:
            rows += compare(m, G["B"], G["A"], "B-A (longer cap only)")
        if G.get("C") is not None and G.get("B") is not None and not same_bc:
            rows += compare(m, G["C"], G["B"], "C-B (tuning only)")
        if G.get("C") is not None:
            rows += compare(m, G["C"], G["A"], "C-A (total)")
            final[NAMES[m]] = G
    E = pd.DataFrame(rows)
    E.to_csv(f"{OUT}/q19_effect.csv", index=False)

    rm = lambda G: np.mean([np.sqrt(np.mean((G[s]["test"].y_pred_mean - G[s]["test"].y_true) ** 2)) for s in SEEDS])
    K = pd.DataFrame({nm: {"A_original": rm(G["A"]), "C_tuned": rm(G["C"])} for nm, G in final.items()}).T
    K["rank_A"] = K.A_original.rank().astype(int); K["rank_C"] = K.C_tuned.rank().astype(int)
    K = K.sort_values("rank_A")

    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 30)
    print("\n===== 配对差（负数 = 改进）=====")
    print(E.round(4).to_string(index=False))
    print("\n===== 测试 RMSE 排名：A（原设置）对 C（调参后）=====")
    print(K.round(4).to_string())
    trig = []
    if {"XGBoost", "BiLSTM-Attention"} <= set(K.index):
        if np.sign(K.loc["XGBoost", "A_original"] - K.loc["BiLSTM-Attention", "A_original"]) != \
           np.sign(K.loc["XGBoost", "C_tuned"] - K.loc["BiLSTM-Attention", "C_tuned"]):
            trig.append("XGBoost 与 BiLSTM-Attention 排名改变")
    big = E[(E.comparison == "C-A (total)") & (E.subset == "all") & (E.evidence != "weak/none") & (E.pct.abs() >= 1)]
    for _, r in big.iterrows():
        trig.append(f"{r.model} C−A {r.metric}: {r.pct:+.2f}%（{r.evidence}）")
    if (K.rank_A != K.rank_C).any():
        trig.append("6 个模型排名改变：" + ", ".join(f"{i} {a}→{b}" for i, a, b in zip(K.index, K.rank_A, K.rank_C) if a != b))
    print("\n===== 正文触发（预定规则）=====")
    print("\n".join(trig) if trig else "无：结果放附录与回复信")
    print(f"\n输出：{OUT}/q19_all_runs.csv（全部候选）、q19_effect.csv")


if __name__ == "__main__":
    main()
