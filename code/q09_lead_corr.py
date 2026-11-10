#!/usr/bin/env python3
"""q09: 与 6 h 提前量匹配的变量筛选检查（只分析，不训练）。

回答 R2 M3（同期相关不代表 6 h 预测价值）、R3 §3.2(b)(f)（选变量依据、季节依赖）。
原稿筛选：训练期同期 Spearman，x(t) 对 tp(t)（notebook 第 8 格），取 |ρ| 前 7。

本脚本只用训练期时刻（前 70%，即前 18,410 个时刻），都柏林 5×5 框的 25 格点简单平均（与原稿一致）：
  A 同期 ρ[x(t), tp(t)]                           —— 复现原稿
  B 提前量 ρ[x(t−6k h), y]，y = tp(t+6 h)，k = 0..5 —— 即模型真正的目标；k 覆盖 30 h 窗口
  C 偏 Spearman ρ[x(t), y | tp(t)]                —— 扣除持续性之后的增量信息
  D 分季节（按目标时刻 DJF/MAM/JJA/SON）的 B(k=0) 和 C
  E 移动块自助法（28 个时刻 = 7 天，2,000 次，种子 42）：B(k=0) 与 C 的 95% 区间、各变量进入前 7 的频率
候选：原稿 11 个 + 衍生 2 个（ws = 逐格点 √(u10²+v10²) 再平均；cp = tp − lsp）；tp(t) 只作参照，不参与排名。

预先定的判据（看结果前定，结果出来后不改）：
  1) 若按 B(k=0) 选出的前 7 与原稿 7 个变量集合相同 → 原稿选择对 6 h 目标仍成立；
  2) 若不同 → 报告差异，并用提前量选出的变量集做一组 XGBoost 与 BiLSTM-Attention 五种子重训（另写脚本）；
  3) 自助法里原稿 7 个变量各自进入前 7 的频率 ≥ 0.95 视为稳定；
  4) C 的 95% 区间不含 0 视为扣除持续性后仍有增量信息。
只读 data/04-24.csv，不写任何已有文件。
运行：cd /root/autodl-tmp && python3 code/q09_lead_corr.py 2>&1 | tee results/metrics/q09_output.txt
"""
import os
import numpy as np
import pandas as pd
from scipy.stats import rankdata

SRC = "/root/autodl-tmp/data/04-24.csv"
OUT = "/root/autodl-tmp/results/metrics"
END = pd.Timestamp("2021-12-31 18:00:00")
N_TRAIN = 18410            # 前 70% 时刻（int(0.7 × 26,300)）
ORIG7 = ["mxtpr", "mntpr", "lsp", "tcc", "v10", "sp", "d2m"]
RAW = ["u10", "v10", "d2m", "t2m", "sp", "e", "mxtpr", "mntpr", "tcc", "ssr", "lsp", "tp"]
CANDS = ["u10", "v10", "d2m", "t2m", "sp", "e", "mxtpr", "mntpr", "tcc", "ssr", "lsp", "ws", "cp"]
LAGS = range(6)
BLOCK, NBOOT, SEED = 28, 2000, 42
SEASON = {12: "DJF", 1: "DJF", 2: "DJF", 3: "MAM", 4: "MAM", 5: "MAM",
          6: "JJA", 7: "JJA", 8: "JJA", 9: "SON", 10: "SON", 11: "SON"}


def spearman(a, b):
    ra, rb = rankdata(a), rankdata(b)
    return np.corrcoef(ra, rb)[0, 1]


def partial_spearman(x, y, z):
    rx, ry, rz = rankdata(x), rankdata(y), rankdata(z)
    Z = np.column_stack([np.ones_like(rz), rz])
    ex = rx - Z @ np.linalg.lstsq(Z, rx, rcond=None)[0]
    ey = ry - Z @ np.linalg.lstsq(Z, ry, rcond=None)[0]
    return np.corrcoef(ex, ey)[0, 1]


def load_regional():
    parts = []
    for ch in pd.read_csv(SRC, usecols=["valid_time", "latitude", "longitude"] + RAW, chunksize=2_000_000):
        m = ch.latitude.between(52.75, 53.75) & ch.longitude.between(-6.75, -5.75)
        parts.append(ch[m])
    d = pd.concat(parts)
    d["valid_time"] = pd.to_datetime(d["valid_time"])
    d = d[d.valid_time <= END]
    d["ws"] = np.sqrt(d.u10 ** 2 + d.v10 ** 2)
    d["cp"] = d.tp - d.lsp
    n = d.groupby("valid_time").size()
    assert (n == 25).all() and len(n) == 26300, "都柏林框不是每个时刻 25 格点或时刻数不是 26,300"
    r = d.groupby("valid_time")[RAW + ["ws", "cp"]].mean().sort_index()
    assert r.notna().all().all()
    return r


def main():
    os.makedirs(OUT, exist_ok=True)
    r = load_regional()
    print(f"区域序列 {r.shape}，{r.index[0]} 至 {r.index[-1]}")
    print(f"cp 为负的时刻（数值误差）：{(r.cp < 0).sum()}，最小 {r.cp.min():.3e}")
    tr = r.iloc[:N_TRAIN].copy()
    print(f"训练期时刻 {len(tr)}：{tr.index[0]} 至 {tr.index[-1]}")
    y = tr["tp"].shift(-1)                       # 目标 tp(t+6h)
    ok_y = y.notna()

    # A 同期（复现原稿）
    rowsA = [{"var": v, "rho_contemp": spearman(tr[v], tr["tp"])} for v in CANDS]
    A = pd.DataFrame(rowsA).set_index("var")

    # B 提前量，k = 0..5
    rowsB = []
    for v in CANDS + ["tp"]:
        for k in LAGS:
            x = tr[v].shift(k)
            m = ok_y & x.notna()
            rowsB.append({"var": v, "lag_k": k, "x_time": f"t-{6 * k}h", "n": int(m.sum()),
                          "rho_lead": spearman(x[m], y[m])})
    B = pd.DataFrame(rowsB)
    B.to_csv(f"{OUT}/q09_lead_spearman.csv", index=False)

    # C 偏相关（控制 tp(t)）
    m0 = ok_y
    C = pd.Series({v: partial_spearman(tr[v][m0].values, y[m0].values, tr["tp"][m0].values) for v in CANDS},
                  name="rho_partial_given_tp_t")

    B0 = B[B.lag_k == 0].set_index("var")["rho_lead"]
    tab = A.join(B0.rename("rho_lead_k0")).join(C)
    tab["rank_contemp"] = tab.rho_contemp.abs().rank(ascending=False).astype(int)
    tab["rank_lead"] = tab.rho_lead_k0.abs().rank(ascending=False).astype(int)
    tab["rank_partial"] = tab.rho_partial_given_tp_t.abs().rank(ascending=False).astype(int)
    tab["in_orig7"] = tab.index.isin(ORIG7)

    # E 移动块自助法
    rng = np.random.default_rng(SEED)
    xs = {v: tr[v][m0].values for v in CANDS}
    yy, zz = y[m0].values, tr["tp"][m0].values
    n = len(yy)
    nb = int(np.ceil(n / BLOCK))
    lead_bs = np.empty((NBOOT, len(CANDS)))
    part_bs = np.empty((NBOOT, len(CANDS)))
    for b in range(NBOOT):
        st = rng.integers(0, n - BLOCK + 1, nb)
        idx = (st[:, None] + np.arange(BLOCK)).ravel()[:n]
        for j, v in enumerate(CANDS):
            lead_bs[b, j] = spearman(xs[v][idx], yy[idx])
            part_bs[b, j] = partial_spearman(xs[v][idx], yy[idx], zz[idx])
    top7 = np.argsort(-np.abs(lead_bs), axis=1)[:, :7]
    freq = np.array([(top7 == j).any(axis=1).mean() for j in range(len(CANDS))])
    tab["lead_k0_lo"], tab["lead_k0_hi"] = np.percentile(lead_bs, [2.5, 97.5], axis=0)
    tab["partial_lo"], tab["partial_hi"] = np.percentile(part_bs, [2.5, 97.5], axis=0)
    tab["freq_top7_lead"] = freq
    tab = tab.sort_values("rank_lead")
    tab.to_csv(f"{OUT}/q09_selection_table.csv")

    # D 分季节（按目标时刻）
    tgt_season = pd.Series(tr.index.shift(1, freq="6h").month.map(SEASON), index=tr.index)
    rowsD = []
    for s in ["DJF", "MAM", "JJA", "SON"]:
        ms = m0 & (tgt_season == s)
        for v in CANDS:
            rowsD.append({"season": s, "var": v, "n": int(ms.sum()),
                          "rho_lead_k0": spearman(tr[v][ms], y[ms]),
                          "rho_partial": partial_spearman(tr[v][ms].values, y[ms].values, tr["tp"][ms].values)})
        rowsD.append({"season": s, "var": "tp(t) 参照", "n": int(ms.sum()),
                      "rho_lead_k0": spearman(tr["tp"][ms], y[ms]), "rho_partial": np.nan})
    D = pd.DataFrame(rowsD)
    D["rank_lead_in_season"] = D[D["var"] != "tp(t) 参照"].groupby("season").rho_lead_k0 \
        .transform(lambda s: s.abs().rank(ascending=False))
    D.to_csv(f"{OUT}/q09_seasonal.csv", index=False)

    # 输出
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    print("\n===== 选择表（训练期；按 |ρ_lead(k=0)| 排序）=====")
    print(tab.round(3).to_string())
    print(f"\ntp(t) 参照：同期 1；提前量 ρ[tp(t), tp(t+6h)] = {B0['tp']:.3f}")
    lead7 = list(tab.index[:7])
    con7 = list(tab.sort_values("rank_contemp").index[:7])
    print(f"\n原稿 7 个：{ORIG7}")
    print(f"同期前 7（复现）：{con7}，与原稿相同：{set(con7) == set(ORIG7)}")
    print(f"提前量前 7：{lead7}，与原稿相同：{set(lead7) == set(ORIG7)}")
    print(f"  进入：{sorted(set(lead7) - set(ORIG7))}；退出：{sorted(set(ORIG7) - set(lead7))}")
    print(f"原稿 7 个在自助法中进入提前量前 7 的频率：{tab.loc[ORIG7, 'freq_top7_lead'].round(3).to_dict()}")
    gap = tab.rho_lead_k0.abs().sort_values(ascending=False)
    print(f"第 7 名与第 8 名 |ρ_lead| 间隔：{gap.iloc[6]:.3f} − {gap.iloc[7]:.3f} = {gap.iloc[6] - gap.iloc[7]:.3f}")
    print(f"偏相关 95% 区间不含 0 的变量：{list(tab.index[(tab.partial_lo > 0) | (tab.partial_hi < 0)])}")

    print("\n===== 提前量剖面 |ρ| 随 k（x 在 t−6k h，目标 t+6h）=====")
    print(B.pivot(index="var", columns="x_time", values="rho_lead")[[f"t-{6 * k}h" for k in LAGS]]
          .loc[CANDS + ["tp"]].round(3).to_string())

    print("\n===== 分季节 ρ_lead(k=0) =====")
    print(D.pivot(index="var", columns="season", values="rho_lead_k0")[["DJF", "MAM", "JJA", "SON"]].round(3).to_string())
    print("\n===== 分季节前 7（按 |ρ_lead(k=0)|）=====")
    for s in ["DJF", "MAM", "JJA", "SON"]:
        ds = D[(D.season == s) & (D["var"] != "tp(t) 参照")].sort_values("rank_lead_in_season")
        t7 = list(ds["var"][:7])
        print(f"{s}（n={int(ds.n.iloc[0])}）：{t7}；与原稿相同：{set(t7) == set(ORIG7)}")
    print("\n===== 分季节偏相关（控制 tp(t)）=====")
    print(D.pivot(index="var", columns="season", values="rho_partial")[["DJF", "MAM", "JJA", "SON"]]
          .drop("tp(t) 参照").round(3).to_string())
    print(f"\n输出：{OUT}/q09_selection_table.csv、q09_lead_spearman.csv、q09_seasonal.csv")


if __name__ == "__main__":
    main()
