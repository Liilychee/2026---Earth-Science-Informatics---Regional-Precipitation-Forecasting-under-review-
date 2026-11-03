# ============================================================
# analysis_q03_spatial_averaging.py — issue 03 (R2 M7, R3 L471, R4 l.240/l.471/l.695/l.962)
# Pure computation on the RAW 25-cell ERA5 file (data/04-24.csv). No training, no GPU.
#
# Questions answered
#   (a) What does Q95 = 0.574 mm mean?  -> it is a 1-HOUR amount (tp = accumulation over the
#       hour ending at the timestamp), not a 6-h accumulation, not log-transformed.
#   (b) How much does spatial averaging change the distribution?
#       regional mean (25 cells)  vs  the cell nearest Dublin Airport  vs  the cell nearest
#       Dublin city centre  vs  all 25 cells (range) vs  max over the 25 cells.
#   (c) How many samples reach the AMS/WMO-style intensity classes
#       (light <=2.5, moderate 2.6-7.6, heavy >7.6 mm/h)?
#
# Sampling is IDENTICAL to the main pipeline: 6-hourly stamps (00/06/12/18 UTC),
# 2004-01-01 .. 2021-12-31, tp (m) x 1000 -> mm. "Train" = first 70 % of the timestamps
# (same rule as Step 2D), so train-only quantiles match the manuscript's Q95 = 0.5740 mm.
#
# Run (Mac or AutoDL), from the folder containing data/ :
#     python code/analysis_q03_spatial_averaging.py                # looks for data/04-24.csv
#     python code/analysis_q03_spatial_averaging.py /path/to/04-24.csv
# Output: results/metrics/q03_*.csv  (+ console summary)
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

n_train = int(len(S) * 0.70)
train, full = S.iloc[:n_train], S


def stats(x):
    return {"N": len(x), "Mean_mm": x.mean(), "Std_mm": x.std(),
            "Frac_gt_0": (x > 0).mean(), "Frac_ge_0.1mm": (x >= 0.1).mean(),
            "Frac_ge_0.5mm": (x >= 0.5).mean(), "Frac_ge_1.0mm": (x >= 1.0).mean(),
            "Q50": x.quantile(.50), "Q90": x.quantile(.90), "Q95": x.quantile(.95),
            "Q97.5": x.quantile(.975), "Q99": x.quantile(.99), "Q99.9": x.quantile(.999),
            "Max_mm": x.max()}


rows = []
for name in S.columns:
    rows.append({"Series": name, "Period": "train (first 70 %)", **stats(train[name])})
    rows.append({"Series": name, "Period": "2004-2021 all", **stats(full[name])})
summ = pd.DataFrame(rows)
os.makedirs(OUTDIR, exist_ok=True)
summ.to_csv(os.path.join(OUTDIR, "q03_spatial_averaging_summary.csv"), index=False)
pd.set_option("display.width", 220)
print("\n=== TRAIN-PERIOD DISTRIBUTION (mm per hour) ===")
print(summ[summ.Period.str.startswith("train")].drop(columns="Period").round(3).to_string(index=False))

# ---- threshold transfer: how often does one cell exceed the REGIONAL Q95? ----
q95_reg = train.iloc[:, 0].quantile(.95)
q95_win = S.iloc[WINDOW:n_train, 0].quantile(.95)      # train TARGETS only (windowed)
print(f"\nRegional-mean train Q95 = {q95_reg:.4f} mm over all {n_train} train stamps "
      f"(= step10 definition); {q95_win:.4f} mm over the {n_train - WINDOW} train targets "
      f"(= prediction-file definition). Manuscript: 0.5740")
assert abs(q95_reg - 0.5740) < 5e-4 or abs(q95_win - 0.5740) < 5e-4, \
    "regional Q95 does not reproduce the manuscript's 0.5740 -> check the source file before using any result"
for name in S.columns:
    print(f"  {name:55s} P(value >= {q95_reg:.3f} mm) = {(full[name] >= q95_reg).mean()*100:5.2f} %"
          f"   own-series train Q95 = {train[name].quantile(.95):.3f} mm")

# ---- all 25 cells ----
cell_rows = []
for c in wide.columns:
    x_tr = wide[c].iloc[:n_train]
    cell_rows.append({"lat": c[0], "lon": c[1], "Mean_mm": x_tr.mean(), "Q90": x_tr.quantile(.9),
                      "Q95": x_tr.quantile(.95), "Q99": x_tr.quantile(.99), "Max_mm": wide[c].max(),
                      "Frac_ge_1.0mm": (wide[c] >= 1.0).mean(),
                      "Spearman_with_regional_mean": wide[c].corr(S.iloc[:, 0], method="spearman")})
cells = pd.DataFrame(cell_rows)
cells.to_csv(os.path.join(OUTDIR, "q03_cell_stats.csv"), index=False)
print("\n=== 25 CELLS (train period): Q95 range, spread ===")
print(f"Q95 over cells: min {cells.Q95.min():.3f}  median {cells.Q95.median():.3f}  max {cells.Q95.max():.3f} mm;"
      f"  Max over cells ranges {cells.Max_mm.min():.2f}-{cells.Max_mm.max():.2f} mm")
print("Spearman(cell, regional mean): min %.2f  median %.2f" %
      (cells.Spearman_with_regional_mean.min(), cells.Spearman_with_regional_mean.median()))

# ---- intensity classes (AMS Glossary: light <=2.5, moderate 2.6-7.6, heavy >7.6 mm/h) ----
cls = []
for name in S.columns:
    x = full[name]
    cls.append({"Series": name, "N": len(x), "Frac_gt_0.1": (x > 0.1).mean(),
                "Frac_gt_2.5mm_per_h (above 'light')": (x > 2.5).mean(),
                "N_gt_2.5": int((x > 2.5).sum()),
                "Frac_gt_7.6mm_per_h ('heavy')": (x > 7.6).mean(),
                "N_gt_7.6": int((x > 7.6).sum()), "Max_mm": x.max()})
cls = pd.DataFrame(cls)
cls.to_csv(os.path.join(OUTDIR, "q03_intensity_class_counts.csv"), index=False)
print("\n=== HOW MANY SAMPLES REACH PHYSICAL INTENSITY CLASSES (2004-2021) ===")
print(cls.round(4).to_string(index=False))
print("\nSaved q03_spatial_averaging_summary.csv, q03_cell_stats.csv, q03_intensity_class_counts.csv to", OUTDIR)
