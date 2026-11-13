# R2-M1 follow-up: why is tp6h(T) >= tp1h(T) only 0.9754 (not 1.0000)? READ-ONLY, CPU, no files modified.
# Run: cd /root/autodl-tmp && python3 code/check_q08_window.py > results/metrics/check_q08_window.txt 2>&1; cat results/metrics/check_q08_window.txt
import glob, re
import h5py, numpy as np, pandas as pd

pd.set_option("display.width", 200)


def read_var(h, name):
    v = h[name]
    a = v[...].astype("float64")
    fill = v.attrs.get("_FillValue")
    if fill is not None:
        f0 = np.asarray(fill).ravel()[0]
        if np.isnan(f0):
            pass
        else:
            a[a == f0] = np.nan
    a = a * float(np.asarray(v.attrs.get("scale_factor", 1.0)).ravel()[0]) \
          + float(np.asarray(v.attrs.get("add_offset", 0.0)).ravel()[0])
    attrs = {k: (v.attrs[k].decode() if isinstance(v.attrs[k], bytes) else v.attrs[k]) for k in v.attrs
             if k not in ("DIMENSION_LIST", "REFERENCE_LIST")}
    return a, attrs


def read_time(h):
    t = h["time"]
    units = t.attrs["units"]
    units = units.decode() if isinstance(units, bytes) else str(units)
    m = re.match(r"(\w+) since (.+)", units)
    unit_map = {"days": "D", "hours": "h", "minutes": "min", "seconds": "s"}
    return pd.Timestamp(m.group(2).strip()) + pd.to_timedelta(t[...].astype("int64"), unit=unit_map[m.group(1)])


files = sorted(f for f in glob.glob("data/q08/**/*.nc", recursive=True) if "weatherbench" in f.lower())
T1, T6, TT = [], [], []
for i, f in enumerate(files):
    with h5py.File(f, "r") as h:
        times = read_time(h)
        a1, at1 = read_var(h, "total_precipitation")
        a6, at6 = read_var(h, "total_precipitation_6hr")
        if i == 0:
            print("tp1h attrs:", at1)
            print("tp6h attrs:", at6)
            print("datasets in first file:", list(h.keys()))
        ax = [k for k, n in enumerate(a1.shape) if n == len(times)][0]
        T1.append(np.moveaxis(a1, ax, 0).reshape(len(times), -1) * 1000)
        T6.append(np.moveaxis(a6, ax, 0).reshape(len(times), -1) * 1000)
        TT.append(times)
t = pd.DatetimeIndex(np.concatenate([np.asarray(x) for x in TT]))
g1, g6 = np.concatenate(T1), np.concatenate(T6)
o = np.argsort(t.values, kind="stable"); t, g1, g6 = t[o], g1[o], g6[o]
keep = ~t.duplicated(); t, g1, g6 = t[keep], g1[keep], g6[keep]

print(f"\n== 1. coverage: {len(t)} times, {t.min()} -> {t.max()}, cells per time {g1.shape[1]}")
print("hour of day counts:", pd.Series(t.hour).value_counts().sort_index().to_dict())
dt = pd.Series(t).diff().dropna()
print("time steps:", dt.value_counts().head(8).to_dict())
print("NaN tp1h / tp6h:", int(np.isnan(g1).sum()), int(np.isnan(g6).sum()))
print("min tp1h / tp6h (mm):", np.nanmin(g1), np.nanmin(g6), "| n<0:", int((g1 < 0).sum()), int((g6 < 0).sum()))

m1, m6 = np.nanmean(g1, 1), np.nanmean(g6, 1)
d = m1 - m6  # >0 means violation of tp6h(T) >= tp1h(T)
print("\n== 2. box-mean tp6h(T) >= tp1h(T) - eps, by tolerance")
for eps in [0, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2]:
    print(f"  eps {eps:g} mm: {(d <= eps).mean():.4f}  (violations {(d > eps).sum()})")
v = d > 1e-6
print(f"\n== 3. violations (eps 1e-6): n {v.sum()}")
if v.any():
    V = pd.DataFrame({"time": t[v], "tp1h": m1[v], "tp6h": m6[v], "excess": d[v], "ratio": m1[v] / np.where(m6[v] > 0, m6[v], np.nan)})
    print("by hour:", V.time.dt.hour.value_counts().sort_index().to_dict())
    print("by year:", V.time.dt.year.value_counts().sort_index().to_dict())
    print(V[["tp1h", "tp6h", "excess", "ratio"]].describe(percentiles=[.5, .9, .99]).to_string())
    print("largest 15 excess:\n" + V.sort_values("excess", ascending=False).head(15).to_string(index=False))

print("\n== 4. per cell (time x cell) tp6h >= tp1h - eps")
for eps in [1e-6, 1e-4, 1e-3]:
    print(f"  eps {eps:g}: {(g1 - g6 <= eps).mean():.4f}")

print("\n== 5. 'window starts at T' using only true +6 h neighbours")
s = pd.Series(m1, index=t)
nxt = s.reindex(t + pd.Timedelta(hours=6)).to_numpy()
ok = ~np.isnan(nxt)
print(f"  pairs with T+6 h present: {ok.sum()} / {len(t)}")
for eps in [1e-6, 1e-4, 1e-3]:
    print(f"  eps {eps:g}: tp6h(T) >= tp1h(T+6h): {(m6[ok] >= nxt[ok] - eps).mean():.4f}   vs  tp6h(T) >= tp1h(T): {(m6[ok] >= m1[ok] - eps).mean():.4f}")
print(f"  corr tp6h(T)~tp1h(T) {np.corrcoef(m6[ok], m1[ok])[0,1]:.3f} | tp6h(T)~tp1h(T+6h) {np.corrcoef(m6[ok], nxt[ok])[0,1]:.3f}")

print("\n== 6. wet-only (tp6h > 0.1 mm): fraction tp6h(T) >= tp1h(T)")
w = m6 > 0.1
print(f"  n {w.sum()}: {(d[w] <= 1e-6).mean():.4f}")
print("\n===== CHECK COMPLETE (read-only) =====")
