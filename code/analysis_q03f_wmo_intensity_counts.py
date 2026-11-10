# ============================================================
# analysis_q03f_wmo_intensity_counts.py  --  issue 03 (R1 M3), CORRECTED intensity counts
# Replaces the intensity-class block of analysis_q03_spatial_averaging.py, which still used the
# old AMS thresholds (heavy > 7.6 mm/h) and wet > 0.1.  Here:
#   WMO-No. 8 (2008, 7th ed., Part I, Ch. 14, Annex, p. I.14-7) classes for RAIN, 3-min basis:
#       light < 2.5 | moderate 2.5 to < 10 | heavy 10 to < 50 | >= 50 mm/h
#   wet = >= 0.1 mm/h (main-text definition)
# Counts are for the 6-hourly sampled hourly values (26,300 stamps, 2004-2021) of: regional mean
# (25 cells, the paper's target), the cell nearest Dublin Airport, the cell nearest the city centre,
# and the maximum over the 25 cells; for the whole period and for the test period (last 15 % of the
# stamps = the final test windows' targets are a subset of these).
# Pure computation on the RAW 25-cell file (data/04-24.csv), read-only. No training. NEW output file
# only; existing q03_*.csv are NOT touched.
#
# Run from the folder containing data/ :
#     python3 code/analysis_q03f_wmo_intensity_counts.py 2>&1 | tee results/metrics/q03f_wmo_intensity_counts_output.txt
# Output: results/metrics/q03_intensity_class_counts_wmo.csv
# ============================================================
import os
import sys
import numpy as np
import pandas as pd

# ---------------- config ----------------
LAT_MIN, LAT_MAX = 52.75, 53.75
LON_MIN, LON_MAX = -6.75, -5.75
START, END = "2004-01-01", "2021-12-31 23:59:59"
CHUNK = 1_000_000
AIRPORT = (53.4214, -6.2700)       # Dublin Airport official reference point (AirNav Ireland, approx.)
CITY = (53.3498, -6.2603)          # Dublin city centre (O'Connell Street / Spire)
# "Single point" = NEAREST-NEIGHBOUR ERA5 cell (0.25 deg x 0.25 deg box value), no interpolation.
WINDOW = 6                          # same as the main pipeline (first 6 stamps are never targets)
OUTDIR = "/root/autodl-tmp/results/metrics" if os.path.isdir("/root/autodl-tmp/results") else "results/metrics"

CANDS = ["data/04-24.csv", "../data/04-24.csv", "/root/autodl-tmp/data/04-24.csv", "/root/autodl-tmp/04-24.csv"]
path = sys.argv[1] if len(sys.argv) > 1 else next((p for p in CANDS if os.path.exists(p)), None)
assert path and os.path.exists(path), "04-24.csv not found: pass its path as the first argument"
print("Source:", path)

# ---------------- read raw file in chunks, keep Dublin box ----------------
head = pd.read_csv(path, nrows=1)
low = {c.lower(): c for c in head.columns}
T = next(low[k] for k in ("valid_time", "time", "datetime", "date") if k in low)
LA = next(low[k] for k in ("latitude", "lat") if k in low)
LO = next(low[k] for k in ("longitude", "lon") if k in low)
TP = low["tp"]
print("Columns used:", T, LA, LO, TP)

parts, seen = [], 0
for ch in pd.read_csv(path, usecols=[T, LA, LO, TP], chunksize=CHUNK):
    seen += len(ch)
    ch[T] = pd.to_datetime(ch[T])
    m = (ch[LA].between(LAT_MIN - 1e-6, LAT_MAX + 1e-6) & ch[LO].between(LON_MIN - 1e-6, LON_MAX + 1e-6)
         & (ch[T] >= START) & (ch[T] <= END))
    sub = ch.loc[m]
    if len(sub):
        parts.append(sub)
    print(f"read {seen:,} rows", end="\r")
raw = pd.concat(parts, ignore_index=True)
print()

# keep the pipeline's 6-hourly stamps only (no-op if the file is already 6-hourly)
raw = raw[raw[T].dt.hour % 6 == 0]
raw[LA] = raw[LA].round(2)
raw[LO] = raw[LO].round(2)
g = raw.groupby([T, LA, LO])[TP].mean().reset_index()      # same as the regional-mean step
ncell = g.groupby(T).size()
assert ncell.min() == ncell.max() == 25, f"cells per timestamp: {ncell.min()}..{ncell.max()} (expect 25)"
assert g[TP].max() < 1.0, "tp looks like mm already (expected metres)"
g["tp_mm"] = g[TP] * 1000.0

wide = g.pivot(index=T, columns=[LA, LO], values="tp_mm").sort_index()
assert len(wide) == 26300, f"expected 26,300 timestamps, got {len(wide)}"
assert (wide.index.to_series().diff().dropna() == pd.Timedelta(hours=6)).all(), "not contiguous 6-hourly"
print("Grid:", wide.shape, "(timestamps x cells)")


def nearest(lat, lon):
    cells = np.array(wide.columns.tolist())
    d = (cells[:, 0] - lat) ** 2 + ((cells[:, 1] - lon) * np.cos(np.deg2rad(lat))) ** 2
    return tuple(float(v) for v in cells[int(d.argmin())])


c_air, c_city = nearest(*AIRPORT), nearest(*CITY)
print(f"Nearest cell to Dublin Airport {AIRPORT}: {c_air};  to city centre {CITY}: {c_city}")

series = {
    "Regional mean (25 cells) [used in paper]": wide.mean(axis=1),
    f"Single cell nearest Dublin Airport {c_air}": wide[c_air],
    f"Single cell nearest city centre {c_city}": wide[c_city],
    "Maximum over the 25 cells": wide.max(axis=1),
}
S = pd.DataFrame(series)

# sanity vs the file used in the paper (if present)
for p in ["data/dublin_regional_reduced.csv", "../data/dublin_regional_reduced.csv"]:
    if os.path.exists(p):
        r = pd.read_csv(p, parse_dates=["valid_time"]).set_index("valid_time")["tp"] * 1000.0
        diff = (r.reindex(S.index) - S.iloc[:, 0]).abs().max()
        print(f"SANITY: max |regional tp (reduced file) - regional tp (here)| = {diff:.2e} mm")
        break


n = len(S)
va_end = int(n * 0.85)
periods = {"2004-2021 all": S, "test period (last 15 % of stamps)": S.iloc[va_end:]}
rows = []
for pname, P in periods.items():
    for name in S.columns:
        x = P[name]
        rows.append({
            "Series": name, "Period": pname, "N": len(x),
            "N_wet_ge_0.1": int((x >= 0.1).sum()), "Frac_wet_ge_0.1": float((x >= 0.1).mean()),
            "N_light_lt_2.5": int((x < 2.5).sum()),
            "N_moderate_2.5_to_lt_10": int(((x >= 2.5) & (x < 10)).sum()),
            "N_heavy_10_to_lt_50": int(((x >= 10) & (x < 50)).sum()),
            "N_ge_50": int((x >= 50).sum()),
            "N_ge_1.0": int((x >= 1.0).sum()), "N_gt_2.5": int((x > 2.5).sum()),
            "Max_mm_per_h": float(x.max())})
R = pd.DataFrame(rows)
pd.set_option("display.width", 250)
print("\n=== WMO-No. 8 (2008) RAIN CLASSES, COUNTS OF SAMPLED HOURLY VALUES ===")
print(R.round(5).to_string(index=False))
os.makedirs(OUTDIR, exist_ok=True)
R.to_csv(os.path.join(OUTDIR, "q03_intensity_class_counts_wmo.csv"), index=False)
print("\nSaved", os.path.join(OUTDIR, "q03_intensity_class_counts_wmo.csv"))
