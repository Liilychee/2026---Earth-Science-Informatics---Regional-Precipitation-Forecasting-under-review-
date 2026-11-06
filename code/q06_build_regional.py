# ============================================================
# Item 06, step 0: build the 1992-2021 Dublin regional-mean series (read-only on all inputs).
#   1992-2003: data/era5_1992_2003/era5_YYYY.nc (CDS download, validated locally)
#   2004-2021: data/04-24.csv, processed exactly as notebook Step 2B/2D
# Same Dublin box (25 cells), same 25-cell mean, tp converted m -> mm.
# Checks: 25 cells per time, no missing values, strictly 6-hourly and continuous over 30 years,
#         2004-2021 part identical to data/dublin_regional_2004_2021.csv (tp_mm),
#         year-by-year summaries to look for a jump at the 2003/2004 boundary.
# Outputs: data/q06/dublin_regional_1992_2021.csv
#          results/metrics/q06_yearly_summary.csv, q06_build_output.txt (via tee)
# ============================================================
import glob, os, re
import h5py
import numpy as np
import pandas as pd

ROOT = os.environ.get("Q06_ROOT", "/root/autodl-tmp")
NC_DIR = f"{ROOT}/data/era5_1992_2003"
CSV = f"{ROOT}/data/04-24.csv"
REF = f"{ROOT}/data/dublin_regional_2004_2021.csv"
OUT = f"{ROOT}/data/q06/dublin_regional_1992_2021.csv"
MET = f"{ROOT}/results/metrics"
VARS = ["u10", "v10", "d2m", "t2m", "sp", "e", "mxtpr", "mntpr", "tcc", "ssr", "lsp", "tp"]
LAT = (52.75, 53.75)
LON = (-6.75, -5.75)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
os.makedirs(MET, exist_ok=True)


def attr(v, k, default=None):
    a = v.attrs.get(k, default)
    if isinstance(a, np.ndarray) and a.size == 1:
        a = a.ravel()[0]
    return a.decode() if isinstance(a, (bytes, np.bytes_)) else a


def read_var(h, name):
    v = h[name]
    a = v[...].astype("float64")
    fill = attr(v, "_FillValue")
    if fill is not None and not (isinstance(fill, float) and np.isnan(fill)):
        a[a == fill] = np.nan
    a = a * float(attr(v, "scale_factor", 1.0)) + float(attr(v, "add_offset", 0.0))
    dims = [h[ref[0]].name.strip("/") for ref in v.attrs["DIMENSION_LIST"]]
    return a, dims


def read_time(h, name):
    t = h[name]
    m = re.match(r"(\w+) since (.+)", str(attr(t, "units")))
    unit = {"days": "D", "hours": "h", "minutes": "min", "seconds": "s"}[m.group(1)]
    return pd.Timestamp(m.group(2).strip()) + pd.to_timedelta(t[...].astype("int64"), unit=unit)


# ---------- 1992-2003 from NetCDF ----------
files = sorted(glob.glob(f"{NC_DIR}/era5_*.nc"))
assert len(files) == 12, f"expected 12 yearly files, found {len(files)}"
parts, enc = [], None
for f in files:
    with h5py.File(f, "r") as h:
        tname = "valid_time" if "valid_time" in h else "time"
        times = read_time(h, tname)
        lat, lon = h["latitude"][...].astype(float), h["longitude"][...].astype(float)
        lon = np.where(lon > 180, lon - 360, lon)
        li = np.where((lat >= LAT[0] - 1e-6) & (lat <= LAT[1] + 1e-6))[0]
        lo = np.where((lon >= LON[0] - 1e-6) & (lon <= LON[1] + 1e-6))[0]
        assert len(li) == 5 and len(lo) == 5, f"{f}: Dublin box not 5 x 5"
        cols = {}
        for vname in VARS:
            a, dims = read_var(h, vname)
            assert dims == [tname, "latitude", "longitude"], f"{f} {vname}: unexpected dims {dims}"
            box = a[:, li][:, :, lo]
            assert not np.isnan(box).any(), f"{f} {vname}: missing values in the Dublin box"
            cols[vname] = box.mean(axis=(1, 2))
        if enc is None:
            v = h["tp"]
            enc = {k: attr(v, k) for k in ("scale_factor", "add_offset", "units")} | {"dtype": str(v.dtype)}
    parts.append(pd.DataFrame(cols).assign(valid_time=times))
old = pd.concat(parts, ignore_index=True)
print(f"NetCDF 1992-2003: {len(old)} timestamps, {old.valid_time.min()} -> {old.valid_time.max()} | tp encoding {enc}")

# ---------- 2004-2021 from the CSV (notebook Steps 2B/2D) ----------
chunks = []
for ch in pd.read_csv(CSV, usecols=["valid_time", "latitude", "longitude"] + VARS, chunksize=1_000_000):
    keep = ch["latitude"].between(*LAT) & ch["longitude"].between(*LON)
    chunks.append(ch[keep])
df = pd.concat(chunks, ignore_index=True)
df["valid_time"] = pd.to_datetime(df["valid_time"])
df = df[df["valid_time"] <= pd.Timestamp("2021-12-31 18:00")]
assert df.groupby("valid_time").size().eq(25).all()
assert df[VARS].isna().sum().sum() == 0
new = df.groupby("valid_time", as_index=False)[VARS].mean().sort_values("valid_time").reset_index(drop=True)
print(f"CSV 2004-2021: {len(new)} timestamps, {new.valid_time.min()} -> {new.valid_time.max()}")

ref = pd.read_csv(REF, parse_dates=["valid_time"])
d = np.abs(new["tp"].values * 1000 - ref["tp_mm"].values).max()
print(f"2004-2021 tp vs dublin_regional_2004_2021.csv: max |diff| = {d:.2e} mm")
assert len(ref) == len(new) and d < 1e-9

# ---------- merge ----------
old["source"], new["source"] = "nc_1992_2003", "csv_2004_2021"
reg = pd.concat([old, new], ignore_index=True).sort_values("valid_time").reset_index(drop=True)
reg["tp_mm"] = reg["tp"] * 1000.0
reg = reg.drop(columns=["tp"])
steps = reg["valid_time"].diff().dropna().unique()
print(f"Merged: {len(reg)} timestamps, {reg.valid_time.min()} -> {reg.valid_time.max()}, "
      f"time steps found: {[str(s) for s in steps]}")
assert len(reg) == 43832 and list(steps) == [np.timedelta64(6, "h")]
assert reg["valid_time"].is_unique
reg[["valid_time"] + [v for v in VARS if v != "tp"] + ["tp_mm", "source"]].to_csv(OUT, index=False)
print("Saved:", OUT)

# ---------- year-by-year summaries ----------
reg["year"] = reg["valid_time"].dt.year
summ = reg.groupby("year").agg(
    n=("tp_mm", "size"), tp_mean=("tp_mm", "mean"), tp_q95=("tp_mm", lambda x: x.quantile(0.95)),
    tp_max=("tp_mm", "max"), wet01=("tp_mm", lambda x: (x >= 0.1).mean()),
    lsp_mean=("lsp", "mean"), mxtpr_mean=("mxtpr", "mean"), tcc_mean=("tcc", "mean"),
    sp_mean=("sp", "mean"), t2m_mean=("t2m", "mean"), d2m_mean=("d2m", "mean"), v10_mean=("v10", "mean"))
summ.to_csv(f"{MET}/q06_yearly_summary.csv")
pd.set_option("display.width", 220)
print("\n===== Year-by-year summary (look for a jump between 2003 and 2004) =====")
print(summ.to_string(float_format=lambda v: f"{v:.4g}"))
a, b = reg[reg.year <= 2003], reg[(reg.year >= 2004)]
print("\n===== 1992-2003 vs 2004-2021 =====")
for c in ["tp_mm", "lsp", "mxtpr", "mntpr", "tcc", "sp", "t2m", "d2m", "v10", "u10"]:
    print(f"{c:6s} mean {a[c].mean():.5g} vs {b[c].mean():.5g} | sd {a[c].std():.5g} vs {b[c].std():.5g} "
          f"| Q95 {a[c].quantile(.95):.5g} vs {b[c].quantile(.95):.5g}")
print("===== q06 BUILD COMPLETE =====")
