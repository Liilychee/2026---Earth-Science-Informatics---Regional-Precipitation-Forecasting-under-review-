# ============================================================
# r2m7_spatial_quantiles.py — R2-M7 / task 03: single-cell vs regional-mean upper-tail statistics
# Pure computation on the RAW 25-cell ERA5 file (data/04-24.csv). No training, no plotting.
#
# Extraction follows code/analysis_q03_spatial_averaging.py (same box, 2004-2021, 00/06/12/18 UTC,
# coordinates rounded to 0.01, tp m -> mm). Unlike q03, EVERY statistic here uses one time set:
# the 18,404 training prediction targets (rows 6 .. int(0.70 * 26300) - 1), i.e. the targets
# from which the manuscript Q95 = 0.574048 mm h-1 was computed. No validation/test or 2004-2021 data.
#
# Percent difference, always relative to the single-cell value:
#     pct = (regional_value - cell_value) / cell_value * 100
#
# Run:
#     python results/r2m7_evidence/r2m7_spatial_quantiles.py <04-24.csv> <regional_reduced.csv> <prob_preds.csv> <outdir>
# ============================================================
import hashlib
import json
import os
import platform
import sys

import numpy as np
import pandas as pd

RAW, RED, PRED, OUT = sys.argv[1:5]
LAT_MIN, LAT_MAX = 52.75, 53.75
LON_MIN, LON_MAX = -6.75, -5.75
START, END = "2004-01-01", "2021-12-31 23:59:59"
WINDOW, TRAIN_FRAC = 6, 0.70
AIRPORT = (53.4214, -6.2700)        # same reference points as q03
CITY = (53.3498, -6.2603)
QUANTS = [("Q90", .90), ("Q95", .95), ("Q99", .99), ("Q99.9", .999)]
STATS = ["Mean", "Wet_freq_ge_0.1", "Q90", "Q95", "Q99", "Q99.9", "Max"]
os.makedirs(OUT, exist_ok=True)


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


src = {"raw_era5": RAW, "regional_reduced": RED, "prob_bilstm_attention_preds": PRED,
       "script": os.path.abspath(__file__)}
src_md5 = {k: md5(v) for k, v in src.items()}
print("python", platform.python_version(), "| numpy", np.__version__, "| pandas", pd.__version__)
for k, v in src.items():
    print(f"MD5 {k}: {src_md5[k]}  {v}")

# ---------------- raw extraction (q03 logic) ----------------
parts, seen = [], 0
for ch in pd.read_csv(RAW, usecols=["valid_time", "latitude", "longitude", "tp"], chunksize=1_000_000):
    seen += len(ch)
    ch["valid_time"] = pd.to_datetime(ch["valid_time"])
    m = (ch.latitude.between(LAT_MIN - 1e-6, LAT_MAX + 1e-6) & ch.longitude.between(LON_MIN - 1e-6, LON_MAX + 1e-6)
         & (ch.valid_time >= START) & (ch.valid_time <= END))
    if m.any():
        parts.append(ch.loc[m])
raw = pd.concat(parts, ignore_index=True)
print(f"raw rows read {seen:,}; rows in box and period {len(raw):,}")
raw = raw[raw.valid_time.dt.hour % 6 == 0].copy()
raw["latitude"] = raw.latitude.round(2)
raw["longitude"] = raw.longitude.round(2)
dup = int(raw.duplicated(["valid_time", "latitude", "longitude"]).sum())
nan = int(raw.tp.isna().sum())
print("duplicate (time, lat, lon) rows:", dup, "| NaN tp:", nan, "| negative tp:", int((raw.tp < 0).sum()))
assert dup == 0 and nan == 0
g = raw.groupby(["valid_time", "latitude", "longitude"])["tp"].mean().reset_index()
assert g.groupby("valid_time").size().eq(25).all(), "expected 25 cells at every timestamp"
assert g.tp.max() < 1.0, "tp should be in metres"
W = g.pivot(index="valid_time", columns=["latitude", "longitude"], values="tp").sort_index() * 1000.0
assert W.shape == (26300, 25) and not W.isna().any().any()
assert (W.index.to_series().diff().dropna() == pd.Timedelta(hours=6)).all()
print("grid", W.shape, W.index[0], "->", W.index[-1], "| lats", sorted({c[0] for c in W.columns}),
      "| lons", sorted({c[1] for c in W.columns}))
reg_all = W.mean(axis=1)                                   # equal-weight 25-cell mean

red = pd.read_csv(RED, parse_dates=["valid_time"]).set_index("valid_time")["tp"] * 1000.0
d_red = float((red.reindex(W.index) - reg_all).abs().max())
print(f"max |regional (here) - dublin_regional_reduced.csv| = {d_red:.2e} mm")
assert d_red < 1e-9

# ---------------- training prediction targets ----------------
n = len(W); ntr = int(n * TRAIN_FRAC)
T = W.iloc[WINDOW:ntr]
reg = reg_all.iloc[WINDOW:ntr]
p = pd.read_csv(PRED, parse_dates=["valid_time"])
ptr = p[p.split == "train"]
same_t = bool(len(ptr) == len(T) and (ptr.valid_time.values == T.index.values).all())
d_pred = float(np.abs(ptr.y_true.values - reg.values).max())
print(f"training targets {len(T)} ({T.index[0]} -> {T.index[-1]}); identical to prediction-file train times: {same_t}; "
      f"max |y_true - regional| = {d_pred:.2e}")
assert len(T) == 18404 and same_t and d_pred < 1e-5


def nearest(lat, lon):
    cells = np.array(W.columns.tolist())
    d = (cells[:, 0] - lat) ** 2 + ((cells[:, 1] - lon) * np.cos(np.deg2rad(lat))) ** 2
    return tuple(float(v) for v in cells[int(d.argmin())])


c_air, c_city = nearest(*AIRPORT), nearest(*CITY)
assert c_air == (53.5, -6.25) and c_city == (53.25, -6.25)


def stats(x):
    x = np.asarray(x, float)
    out = {"N": len(x), "Mean": x.mean(), "Wet_freq_ge_0.1": (x >= 0.1).mean()}
    out.update({k: float(np.quantile(x, q)) for k, q in QUANTS})   # numpy linear = pandas default
    out["Max"] = x.max()
    return out


rows = [{"Series": "Regional mean (25 cells, equal weight)", "Role": "regional", "Latitude": np.nan,
         "Longitude": np.nan, **stats(reg.values), "Max_time": reg.idxmax()}]
for c in W.columns:
    role = "airport_nearest_cell" if c == c_air else "city_nearest_cell" if c == c_city else "cell"
    rows.append({"Series": f"Cell ({c[0]:.2f}, {c[1]:.2f})", "Role": role, "Latitude": c[0], "Longitude": c[1],
                 **stats(T[c].values), "Max_time": T[c].idxmax()})
S = pd.DataFrame(rows)
S["Period"] = "18,404 training prediction targets"
S["First_time"], S["Last_time"] = T.index[0], T.index[-1]
S.to_csv(os.path.join(OUT, "r2m7_series_stats.csv"), index=False, float_format="%.6f")

R = S.iloc[0]
C = S.iloc[1:].reset_index(drop=True)
assert np.isclose(R["Mean"], C["Mean"].mean(), atol=1e-12)          # averaging preserves the mean

# ---------------- per-cell percentage comparison (long format) ----------------
long = []
for _, c in C.iterrows():
    for k in STATS:
        long.append({"Statistic": k, "Cell_latitude": c.Latitude, "Cell_longitude": c.Longitude, "Cell_role": c.Role,
                     "Cell_value": c[k], "Regional_value": R[k],
                     "Pct_diff_regional_vs_cell": (R[k] - c[k]) / c[k] * 100, "Regional_below_cell": bool(R[k] < c[k])})
L = pd.DataFrame(long)
L["Reference"] = "single-cell value of the same statistic on the same 18,404 targets"
L.to_csv(os.path.join(OUT, "r2m7_pct_by_cell.csv"), index=False, float_format="%.6f")

# ---------------- summary ----------------
summ = []
for k in STATS:
    v, l = C[k].values, L[L.Statistic == k]
    med = float(np.median(v))
    air, city = float(C.loc[C.Role == "airport_nearest_cell", k].iloc[0]), float(C.loc[C.Role == "city_nearest_cell", k].iloc[0])
    summ.append({"Statistic": k, "Regional": R[k], "Cell_min": v.min(), "Cell_median": med, "Cell_max": v.max(),
                 "Pct_vs_cell_median": (R[k] - med) / med * 100,
                 "Pct_min_over_25_cells": l.Pct_diff_regional_vs_cell.min(),
                 "Pct_max_over_25_cells": l.Pct_diff_regional_vs_cell.max(),
                 "N_cells_regional_below": int(l.Regional_below_cell.sum()), "N_cells": len(v),
                 "Airport_cell_53.50_-6.25": air, "Pct_vs_airport_cell": (R[k] - air) / air * 100,
                 "City_cell_53.25_-6.25": city, "Pct_vs_city_cell": (R[k] - city) / city * 100})
M = pd.DataFrame(summ)
M.to_csv(os.path.join(OUT, "r2m7_summary_comparison.csv"), index=False, float_format="%.6f")
pd.set_option("display.width", 250)
print("\n=== 26 series on the 18,404 training targets (mm h-1; wet = fraction) ===")
print(S[["Series", "N", "Mean", "Wet_freq_ge_0.1", "Q90", "Q95", "Q99", "Q99.9", "Max", "Max_time"]].round(4).to_string(index=False))
print("\n=== regional vs 25 cells; pct = (regional - cell) / cell * 100 ===")
print(M.round(4).to_string(index=False))

# ---------------- extra diagnostics ----------------
q95 = R["Q95"]
fr = np.array([(T[c].values >= q95).mean() for c in W.columns])
any_fr = float((T.values >= q95).any(axis=1).mean())
print(f"\nP(single cell >= regional Q95): {fr.min()*100:.2f}..{fr.max()*100:.2f}% (median {np.median(fr)*100:.2f}%); "
      f"P(any of 25 cells >= regional Q95) = {any_fr*100:.2f}%")
print("log1p-space value of Q95 would be %.4f (manuscript reports 0.5740 -> threshold is in mm h-1)" % np.log1p(q95))

# ---------------- fixed checks (audit values) ----------------
chk = {"regional_Q95": (R["Q95"], 0.574048, 5e-7), "cell_Q95_min": (C.Q95.min(), 0.5441, 5e-5),
       "cell_Q95_max": (C.Q95.max(), 0.6990, 5e-5), "cell_Q95_median": (float(np.median(C.Q95)), 0.6189, 5e-5),
       "regional_Q99": (R["Q99"], 1.4402, 5e-5), "regional_Q99.9": (R["Q99.9"], 2.8642, 5e-5),
       "regional_Max": (R["Max"], 4.1345, 5e-5), "cell_Max_max": (C.Max.max(), 7.1120, 5e-5)}
res = {k: {"value": float(v), "expected": e, "pass": bool(abs(v - e) <= t)} for k, (v, e, t) in chk.items()}
for k, r in res.items():
    print(f"CHECK {k:16s} {r['value']:.6f} vs {r['expected']}  {'PASS' if r['pass'] else 'FAIL'}")
assert all(r["pass"] for r in res.values())

outs = ["r2m7_series_stats.csv", "r2m7_pct_by_cell.csv", "r2m7_summary_comparison.csv"]
json.dump({"inputs": {k: {"path": v, "md5": src_md5[k]} for k, v in src.items()},
           "environment": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__},
           "time_set": {"n_targets": len(T), "first": str(T.index[0]), "last": str(T.index[-1]),
                        "rows": f"{WINDOW}..{ntr - 1} of {n}", "identical_to_prediction_train_times": same_t,
                        "max_abs_diff_vs_prediction_y_true": d_pred, "max_abs_diff_vs_regional_reduced": d_red},
           "nearest_cells": {"airport": c_air, "city": c_city},
           "pct_formula": "(regional_value - cell_value) / cell_value * 100",
           "single_cell_exceed_regional_Q95_range": [float(fr.min()), float(fr.max())], "any_cell_exceed_regional_Q95": any_fr,
           "checks": res, "outputs": {o: md5(os.path.join(OUT, o)) for o in outs}},
          open(os.path.join(OUT, "r2m7_run_manifest.json"), "w"), indent=2, default=str)
print("\nSaved:", ", ".join(outs), "+ r2m7_run_manifest.json ->", OUT)
