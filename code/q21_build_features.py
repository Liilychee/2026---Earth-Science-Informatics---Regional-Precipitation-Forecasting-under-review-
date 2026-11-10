#!/usr/bin/env python3
"""q21: 由 CDS 原始 nc（6 个文件）与 04-24.csv 构建第 21 项的新特征，并把新候选补进 09 的提前量筛选表。
只分析，不训练；CPU 即可（AutoDL 无卡模式）。只读输入，不改任何已有文件。

输入
  data/q21/raw/z500_{2004-2009,2010-2015,2016-2021}.nc       变量 z（m2 s-2），维度 valid_time×pressure_level(1)×lat×lon
  data/q21/raw/tcwv_lcc_{2004-2009,2010-2015,2016-2021}.nc   变量 tcwv（kg m-2）、lcc（0–1）
  data/04-24.csv                                            原始 11 变量，51.5–55.5N、10.5–5.5W
  （纬度北→南排列；镜像无 netCDF4，用 h5py 读）

区域（2026-11-07 已定）
  都柏林框 dub：52.75–53.75N、6.75–5.75W，25 格点简单平均（与原稿一致）
  U1 陆上上游框：52.75–53.75N、10.5–7.0W，简单平均（04-24.csv 变量）
  U2 大西洋上游框：50–57N、20–7W，cos(lat) 加权平均（新下载变量）

输出（data/q21/ 与 results/metrics/）
  data/q21/q21_features_2004_2021.csv   valid_time + 新特征（26,300 行），供 21 训练脚本读取
  results/metrics/q21_spearman_new.csv  新候选与原 13 个候选合并的训练期筛选表（同 q09 方法）
  results/metrics/q21_spearman_seasonal.csv
运行：cd /root/autodl-tmp && python3 code/q21_build_features.py 2>&1 | tee results/metrics/q21_build_output.txt
"""
import glob
import os

import h5py
import numpy as np
import pandas as pd
from scipy.stats import rankdata

BASE = "/root/autodl-tmp"
RAW = f"{BASE}/data/q21/raw"
SRC = f"{BASE}/data/04-24.csv"
REF = f"{BASE}/data/dublin_regional_2004_2021.csv"   # 原稿区域序列，用于核对 tp
OUT_DATA = f"{BASE}/data/q21"
OUT_MET = f"{BASE}/results/metrics"
END = pd.Timestamp("2021-12-31 18:00:00")
N_ALL, N_TRAIN = 26300, 18410
BLOCK, NBOOT, SEED = 28, 2000, 42
DUB = dict(lat=(52.75, 53.75), lon=(-6.75, -5.75))
U1 = dict(lat=(52.75, 53.75), lon=(-10.5, -7.0))
U2 = dict(lat=(50.0, 57.0), lon=(-20.0, -7.0))
RAW11 = ["u10", "v10", "d2m", "t2m", "sp", "e", "mxtpr", "mntpr", "tcc", "ssr", "lsp"]
ORIG7 = ["mxtpr", "mntpr", "lsp", "tcc", "v10", "sp", "d2m"]
U1_VARS = ORIG7 + ["ws", "tp"]
SEASON = {12: "DJF", 1: "DJF", 2: "DJF", 3: "MAM", 4: "MAM", 5: "MAM",
          6: "JJA", 7: "JJA", 8: "JJA", 9: "SON", 10: "SON", 11: "SON"}


# ---------------------------------------------------------------- 读 nc（h5py）
def decode_time(ds):
    units = ds.attrs.get("units", b"")
    units = units.decode() if isinstance(units, bytes) else str(units)
    unit, _, origin = units.partition(" since ")
    return pd.Timestamp(origin.strip()) + pd.to_timedelta(ds[...].astype("int64"), unit=unit.strip()[0])


def box_idx(lat, lon, box):
    """连续的纬度、经度下标切片（纬度北→南或南→北都可）。"""
    i = np.where((lat >= box["lat"][0] - 1e-6) & (lat <= box["lat"][1] + 1e-6))[0]
    j = np.where((lon >= box["lon"][0] - 1e-6) & (lon <= box["lon"][1] + 1e-6))[0]
    assert (np.diff(i) == 1).all() and (np.diff(j) == 1).all()
    return slice(i[0], i[-1] + 1), slice(j[0], j[-1] + 1)


def read_box(ds, si, sj):
    """只读区域子集（省内存：无卡模式内存小，整场读入会被系统杀掉）。"""
    a = (ds[:, 0, si, sj] if ds.ndim == 4 else ds[:, si, sj]).astype("float64")
    if ds.ndim == 4:
        assert ds.shape[1] == 1, f"pressure_level 维长度 {ds.shape[1]}"
    fv = ds.attrs.get("_FillValue")
    if fv is not None:
        a[a == np.asarray(fv).item()] = np.nan
    a = a * float(np.asarray(ds.attrs.get("scale_factor", 1.0)).item()) \
        + float(np.asarray(ds.attrs.get("add_offset", 0.0)).item())
    assert not np.isnan(a).any(), f"{ds.name} 区域内有 NaN"
    return a


def load_nc():
    pieces = []
    for f in sorted(glob.glob(f"{RAW}/z500_*.nc")):
        pieces.append(("z500", f, ["z"]))
    for f in sorted(glob.glob(f"{RAW}/tcwv_lcc_*.nc")):
        pieces.append(("tcwv_lcc", f, ["tcwv", "lcc"]))
    assert len(pieces) == 6, f"应有 6 个 nc，找到 {len(pieces)}：{[p[1] for p in pieces]}"
    frames = {}
    for kind, f, vs in pieces:
        with h5py.File(f, "r") as h:
            t = decode_time(h["valid_time"])
            lat, lon = h["latitude"][...].astype(float), h["longitude"][...].astype(float)
            assert len(lat) == 61 and len(lon) == 141, f"{f} 网格 {len(lat)}×{len(lon)}"
            assert np.isclose(lat.max(), 60) and np.isclose(lat.min(), 45)
            assert np.isclose(lon.min(), -30) and np.isclose(lon.max(), 5)
            cols = {}
            for v in vs:
                name = "z500" if v == "z" else v
                for tag, box, wtd in (("dub", DUB, False), ("up", U2, True)):
                    si, sj = box_idx(lat, lon, box)
                    a = read_box(h[v], si, sj)
                    if tag == "dub":
                        assert a.shape[1:] == (5, 5), f"都柏林框 {a.shape[1:]}"
                        cols[f"{name}_{tag}"] = a.mean(axis=(1, 2))
                    else:
                        w = np.cos(np.deg2rad(lat[si]))[:, None] * np.ones(a.shape[2])[None, :]
                        cols[f"{name}_{tag}"] = (a * w).sum(axis=(1, 2)) / w.sum()
                    del a
            print(f"读入 {os.path.basename(f)}：{len(t)} 个时刻，{t[0]} 至 {t[-1]}，变量 {vs}", flush=True)
            frames.setdefault(kind, []).append(pd.DataFrame(cols, index=t))
    return pd.concat([pd.concat(frames["z500"]).sort_index(), pd.concat(frames["tcwv_lcc"]).sort_index()], axis=1)


# ---------------------------------------------------------------- 读 04-24.csv
def load_csv():
    use = ["valid_time", "latitude", "longitude"] + RAW11 + ["tp"]
    parts = []
    print("读 04-24.csv（分块）……", flush=True)
    for ch in pd.read_csv(SRC, usecols=use, chunksize=1_000_000, dtype={c: "float32" for c in RAW11 + ["tp"]}):
        m = ch.latitude.between(52.75 - 1e-6, 53.75 + 1e-6) & ch.longitude.between(-10.5 - 1e-6, -5.75 + 1e-6)
        parts.append(ch[m])
    d = pd.concat(parts)
    del parts
    print(f"  都柏林框与 U1 框共 {len(d):,} 行", flush=True)
    d["valid_time"] = pd.to_datetime(d["valid_time"])
    d = d[d.valid_time <= END]
    d["ws"] = np.sqrt(d.u10 ** 2 + d.v10 ** 2)
    d["cp"] = (d.tp - d.lsp).clip(lower=0)
    isdub = d.longitude.between(-6.75 - 1e-6, -5.75 + 1e-6)
    isu1 = d.longitude.between(-10.5 - 1e-6, -7.0 + 1e-6)
    n_dub, n_u1 = d[isdub].groupby("valid_time").size(), d[isu1].groupby("valid_time").size()
    assert (n_dub == 25).all() and len(n_dub) == N_ALL, "都柏林框格点数或时刻数不对"
    print(f"U1 框每时刻格点数：{sorted(n_u1.unique())}（应为 5 × 15 = 75）")
    assert (n_u1 == 75).all()
    dub = d[isdub].groupby("valid_time")[RAW11 + ["tp", "ws", "cp"]].mean().sort_index()
    u1 = d[isu1].groupby("valid_time")[U1_VARS].mean().sort_index().add_suffix("_u1")
    return dub, u1


# ---------------------------------------------------------------- 筛选统计（与 q09 同一方法）
def spearman(a, b):
    return np.corrcoef(rankdata(a), rankdata(b))[0, 1]


def partial_spearman(x, y, z):
    rx, ry, rz = rankdata(x), rankdata(y), rankdata(z)
    Z = np.column_stack([np.ones_like(rz), rz])
    ex = rx - Z @ np.linalg.lstsq(Z, rx, rcond=None)[0]
    ey = ry - Z @ np.linalg.lstsq(Z, ry, rcond=None)[0]
    return np.corrcoef(ex, ey)[0, 1]


def main():
    os.makedirs(OUT_MET, exist_ok=True)
    nc = load_nc()
    assert nc.index.is_unique and len(nc) == N_ALL, f"nc 时刻数 {len(nc)}，应为 {N_ALL}"
    assert (np.diff(nc.index.values) == np.timedelta64(6, "h")).all()
    assert nc.index[0] == pd.Timestamp("2004-01-01 00:00") and nc.index[-1] == END
    dub, u1 = load_csv()
    assert dub.index.equals(nc.index) and u1.index.equals(nc.index), "nc 与 04-24.csv 的时刻不一致"

    if os.path.exists(REF):
        ref = pd.read_csv(REF, parse_dates=["valid_time"]).set_index("valid_time")
        dmax = np.abs(ref["tp_mm"].values - dub["tp"].values * 1000).max()
        print(f"与原稿区域序列 tp_mm 的最大差：{dmax:.2e} mm（应约为 0）")
        assert dmax < 1e-6

    # z500 距平：减训练期（前 18,410 个时刻）月×时刻均值；只用于筛选，模型用原值
    tr_idx = nc.index[:N_TRAIN]
    key = pd.Series(list(zip(nc.index.month, nc.index.hour)), index=nc.index)
    for c in ["z500_dub", "z500_up"]:
        clim = nc.loc[tr_idx, c].groupby(key.loc[tr_idx]).mean()
        nc[c.replace("z500", "z500a")] = nc[c] - key.map(clim).values

    feat = pd.concat([nc, dub[["ws", "cp"]].rename(columns={"ws": "ws_dub", "cp": "cp_dub"}), u1], axis=1)
    feat.index.name = "valid_time"
    feat.to_csv(f"{OUT_DATA}/q21_features_2004_2021.csv")
    print(f"\n特征文件：{OUT_DATA}/q21_features_2004_2021.csv，{feat.shape}，列：{list(feat.columns)}")
    print(feat.describe().T.round(4).to_string())

    # ---- 筛选表：原 13 个候选 + 新候选，训练期，目标 tp(t+6h)
    allv = pd.concat([dub[RAW11 + ["ws", "cp"]], feat.drop(columns=["ws_dub", "cp_dub"])], axis=1)
    tr = allv.iloc[:N_TRAIN]
    tp_t = dub["tp"].iloc[:N_TRAIN]
    y = tp_t.shift(-1)
    m = y.notna().values
    cands = list(allv.columns)
    new = [c for c in cands if c not in RAW11 + ["ws", "cp"]]
    rows = []
    for v in cands:
        x = tr[v].values[m]
        rows.append({"var": v, "new": v in new, "rho_contemp": spearman(tr[v].values, tp_t.values),
                     "rho_lead_k0": spearman(x, y.values[m]),
                     "rho_partial_given_tp_t": partial_spearman(x, y.values[m], tp_t.values[m])})
    tab = pd.DataFrame(rows).set_index("var")
    for c, r in (("rho_lead_k0", "rank_lead"), ("rho_partial_given_tp_t", "rank_partial")):
        tab[r] = tab[c].abs().rank(ascending=False).astype(int)

    rng = np.random.default_rng(SEED)
    X = {v: tr[v].values[m] for v in cands}
    yy, zz = y.values[m], tp_t.values[m]
    n = len(yy)
    nb = int(np.ceil(n / BLOCK))
    lead_bs = np.empty((NBOOT, len(cands)))
    part_bs = np.empty((NBOOT, len(cands)))
    for b in range(NBOOT):
        st = rng.integers(0, n - BLOCK + 1, nb)
        idx = (st[:, None] + np.arange(BLOCK)).ravel()[:n]
        for j, v in enumerate(cands):
            lead_bs[b, j] = spearman(X[v][idx], yy[idx])
            part_bs[b, j] = partial_spearman(X[v][idx], yy[idx], zz[idx])
    tab["lead_lo"], tab["lead_hi"] = np.percentile(lead_bs, [2.5, 97.5], axis=0)
    tab["partial_lo"], tab["partial_hi"] = np.percentile(part_bs, [2.5, 97.5], axis=0)
    tab = tab.sort_values("rank_lead")
    tab.to_csv(f"{OUT_MET}/q21_spearman_new.csv")

    tgt_season = pd.Series(tr.index.shift(1, freq="6h").month.map(SEASON), index=tr.index)
    srows = []
    for s in ["DJF", "MAM", "JJA", "SON"]:
        ms = m & (tgt_season == s).values
        for v in new:
            srows.append({"season": s, "var": v, "n": int(ms.sum()),
                          "rho_lead_k0": spearman(tr[v].values[ms], y.values[ms]),
                          "rho_partial": partial_spearman(tr[v].values[ms], y.values[ms], tp_t.values[ms])})
    S = pd.DataFrame(srows)
    S.to_csv(f"{OUT_MET}/q21_spearman_seasonal.csv", index=False)

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    print("\n===== 训练期筛选表（原 13 个 + 新候选；按 |ρ_lead| 排序）=====")
    print(tab.round(3).to_string())
    print("\n===== 新候选分季节 ρ_lead(k=0) =====")
    print(S.pivot(index="var", columns="season", values="rho_lead_k0")[["DJF", "MAM", "JJA", "SON"]].round(3).to_string())
    print("\n===== 新候选分季节偏相关（控制 tp(t)）=====")
    print(S.pivot(index="var", columns="season", values="rho_partial")[["DJF", "MAM", "JJA", "SON"]].round(3).to_string())
    print(f"\n输出：{OUT_MET}/q21_spearman_new.csv、q21_spearman_seasonal.csv")


if __name__ == "__main__":
    main()
