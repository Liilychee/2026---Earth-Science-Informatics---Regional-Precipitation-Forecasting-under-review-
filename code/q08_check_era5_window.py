# 08: (1) which 6 h window does WB2 ERA5 total_precipitation_6hr cover? (2) why does it differ from our CSV?
# Reads the .nc files with h5py only (no netCDF4/h5netcdf needed).
import glob, re
import h5py, numpy as np, pandas as pd

def read_var(h, name):
    v = h[name]
    a = v[...].astype("float64")
    fill = v.attrs.get("_FillValue")
    if fill is not None:
        a[a == np.asarray(fill).ravel()[0]] = np.nan
    a = a * float(np.asarray(v.attrs.get("scale_factor", 1.0)).ravel()[0]) \
          + float(np.asarray(v.attrs.get("add_offset", 0.0)).ravel()[0])
    return a, v

def read_time(h):
    t = h["time"]
    units = t.attrs["units"]
    units = units.decode() if isinstance(units, bytes) else str(units)
    m = re.match(r"(\w+) since (.+)", units)
    step, origin = m.group(1), pd.Timestamp(m.group(2).strip())
    unit_map = {"days": "D", "hours": "h", "minutes": "min", "seconds": "s", "nanoseconds": "ns", "microseconds": "us"}
    return origin + pd.to_timedelta(t[...].astype("int64"), unit=unit_map[step]), units

files = sorted(f for f in glob.glob("data/q08/**/*.nc", recursive=True) if "weatherbench" in f.lower())
frames, info = [], None
for f in files:
    with h5py.File(f, "r") as h:
        times, tunits = read_time(h)
        cols = {}
        for name, key in [("total_precipitation", "tp1h"), ("total_precipitation_6hr", "tp6h")]:
            a, v = read_var(h, name)
            t_axis = [i for i, n in enumerate(a.shape) if n == len(times)][0]
            other = tuple(i for i in range(a.ndim) if i != t_axis)
            cols[key] = np.nanmean(a, axis=other) * 1000.0
            if info is None and name == "total_precipitation":
                info = (v.dtype, a.shape, {k: v.attrs[k] for k in v.attrs if k in ("scale_factor", "add_offset", "_FillValue", "units")}, tunits)
        frames.append(pd.DataFrame(cols, index=times))
e = pd.concat(frames).sort_index()
e = e[~e.index.duplicated()]
print("files:", len(files), "| times:", len(e), "| first file:", info)

csv = pd.read_csv("data/dublin_regional_2004_2021.csv", parse_dates=["valid_time"]).set_index("valid_time")["tp_mm"]
e = e.join(csv.rename("csv"), how="inner")
print("matched with CSV:", len(e))

eps = 1e-6
end_at_T   = (e["tp6h"] >= e["tp1h"] - eps).mean()            # window (T-6, T] contains the hour ending at T
start_at_T = (e["tp6h"] >= e["tp1h"].shift(-1) - eps).mean()   # window (T, T+6] contains the hour ending at T+6
print(f"tp6h(T) >= tp1h(T)      : {end_at_T:.4f}   (1.0000 -> window ends at T)")
print(f"tp6h(T) >= tp1h(T+6 h)  : {start_at_T:.4f}  (1.0000 -> window starts at T)")
print(f"corr(tp6h(T), tp1h(T))  : {e['tp6h'].corr(e['tp1h']):.3f}")
print(f"corr(tp6h(T), tp1h(T+6)): {e['tp6h'].corr(e['tp1h'].shift(-1)):.3f}")

d = (e["tp1h"] - e["csv"]).abs()
print(f"\n|WB2 tp1h - CSV|: max {d.max():.2e}, mean {d.mean():.2e}, n>1e-4: {(d > 1e-4).sum()}")
bins = pd.cut(e["csv"], [-1, 0.01, 0.1, 0.5, 1, 10])
print(pd.DataFrame({"n": d.groupby(bins, observed=False).size(),
                    "mean_abs_diff": d.groupby(bins, observed=False).mean(),
                    "max_abs_diff": d.groupby(bins, observed=False).max(),
                    "max_rel_diff": (d / e["csv"].clip(lower=1e-6)).groupby(bins, observed=False).max()}).to_string())
