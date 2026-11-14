# ============================================================
# Item 22 (R3 L979-982; R4 m37): build the hourly 25-cell box-mean table for 2017-2021 from the CDS downloads.
# Zero training. Reads era5_hourly_2004_2021/raw/<year>_{accum,maxmin,instantA,instantB}.nc (q22_get_merge.py),
# takes the equal-weight mean over the Dublin 5x5 box (52.75-53.75N, 6.75-5.75W), exactly as the main study,
# and checks the result against the 6-hourly regional table of the paper (dublin_regional_reduced.csv) at
# 00/06/12/18 UTC. Stops if any variable differs by more than 1e-4 of its SD or any event label changes.
# Output (new file, never overwritten): <out_csv>  columns valid_time, tp, lsp, mxtpr, mntpr, tcc, v10, sp, d2m
#   (raw ERA5 units, as in the paper's regional table) and tp_mm (= tp * 1000, mm per hour).
# Run (Mac or AutoDL; needs xarray + netCDF4):
#   python3 code/q22_build_hourly.py <raw_dir> <dublin_regional_reduced.csv> data/q22/q22_hourly_boxmean_2017_2021.csv
# ============================================================
import hashlib
import os
import sys

import numpy as np
import pandas as pd
import xarray as xr

RAW, REF, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
YEARS = range(2017, 2022)
GROUPS = ["accum", "maxmin", "instantA", "instantB"]
VARS = ["tp", "lsp", "mxtpr", "mntpr", "tcc", "v10", "sp", "d2m"]
assert not os.path.exists(OUT), f"{OUT} exists; refusing to overwrite"

per_year = []
for y in YEARS:
    parts = []
    for g in GROUPS:
        f = f"{RAW}/{y}_{g}.nc"
        d = xr.open_dataset(f)
        if "valid_time" not in d.dims and "time" in d.dims:
            d = d.rename({"time": "valid_time"})
        parts.append(d.drop_vars([c for c in ("number", "expver") if c in d.variables]).load())
        d.close()
        print(f"read {f}  md5 {hashlib.md5(open(f, 'rb').read()).hexdigest()}")
    per_year.append(xr.merge(parts, join="exact"))
ds = xr.concat(per_year, dim="valid_time").sortby("valid_time")

t = pd.DatetimeIndex(ds.valid_time.values)
assert len(t) == 43824 and t.is_unique and (np.diff(t.values) == np.timedelta64(1, "h")).all(), len(t)
assert str(t[0]) == "2017-01-01 00:00:00" and str(t[-1]) == "2021-12-31 23:00:00", (t[0], t[-1])
assert ds.sizes["latitude"] == 5 and ds.sizes["longitude"] == 5
assert np.allclose(np.sort(ds.latitude.values), np.arange(52.75, 53.751, 0.25))
assert np.allclose(np.sort(ds.longitude.values), np.arange(-6.75, -5.749, 0.25))
miss = [v for v in VARS if v not in ds]
assert not miss, f"missing variables {miss}"
for v in VARS:
    assert not np.isnan(ds[v].values).any(), f"NaN in {v}"

box = ds[VARS].mean(("latitude", "longitude")).to_dataframe()[VARS]
box.index.name = "valid_time"
box["tp_mm"] = box["tp"] * 1000.0
print(f"hourly box means: {len(box):,} rows, {box.index[0]} to {box.index[-1]}, 25 cells, no NaN")

# ---- reproduction gate against the paper's 6-hourly regional table ----
ref = pd.read_csv(REF, parse_dates=["valid_time"]).set_index("valid_time")
syn = box[box.index.hour.isin([0, 6, 12, 18])]
r = ref.reindex(syn.index)
assert len(syn) == 7304 and r[VARS].notna().all().all(), "synoptic stamps missing in the reference table"
print(f"\nreproduction gate: {len(syn):,} stamps at 00/06/12/18 UTC vs {os.path.basename(REF)}")
print(f"{'var':6s} {'max|diff|':>11s} {'ref SD':>11s} {'ratio':>10s}")
for v in VARS:
    dmax, sd = float((syn[v] - r[v]).abs().max()), float(ref[v].std())
    print(f"{v:6s} {dmax:11.3e} {sd:11.3e} {dmax / sd:10.2e}")
    assert dmax / sd < 1e-4, f"{v} differs from the paper's table by {dmax / sd:.2e} SD"
for thr in (0.1, 0.574):
    same = int(((syn.tp_mm >= thr) == (r.tp * 1000 >= thr)).sum())
    print(f"event label tp >= {thr} mm/h identical at {same}/{len(syn)} stamps")
    assert same == len(syn)

os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
box.reset_index().to_csv(OUT, index=False, float_format="%.10g")
print(f"\nSaved {OUT}  md5 {hashlib.md5(open(OUT, 'rb').read()).hexdigest()}")
