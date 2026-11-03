# ============================================================
# analysis_q04_station_vs_era5.py — issue 04 (R1 M6, R4 m12 l.240, R4 m36 l.962-971)
# How well does the ERA5 precipitation TARGET agree with the Met Eireann observations at
# Dublin Airport?  Pure computation, no training, no GPU.
#
# Station : Met Eireann synoptic station Dublin Airport (hly532.csv, hourly, UTC,
#           lat 53.428, lon -6.241, 71 m; CC BY 4.0, Met Eireann must be credited).
# ERA5    : (a) the nearest 0.25-deg cell to the station  (b) the 25-cell regional mean
#           (the target actually used in the paper), at the same 6-hourly stamps
#           (00/06/12/18 UTC), 2004-01-01 .. 2021-12-31, tp (m) x 1000 -> mm per hour.
#
# TIME ALIGNMENT: the station key does not say whether the hourly 'rain' at stamp t covers the
# hour ENDING at t or STARTING at t.  ERA5 tp at t is the hour ending at t.  We therefore test
# station values at t-1h, t, t+1h and report all three (the best one is flagged, not hidden).
#
# Run (AutoDL):   cd /root/autodl-tmp && python3 code/analysis_q04_station_vs_era5.py
# Needs: data/hly532.csv, data/04-24.csv (raw 25 cells), data/dublin_regional_reduced.csv
# Outputs (results/metrics/): q04_station_vs_era5_summary.csv, q04_shift_test.csv,
#                             q04_seasonal.csv, q04_pairs.csv, q04_rain_indicator_counts.csv
# ============================================================
import os
import sys
import numpy as np
import pandas as pd

START, END = "2004-01-01", "2021-12-31 23:59:59"
CELL = (53.5, -6.25)                      # nearest 0.25-deg ERA5 cell to (53.428, -6.241)
WET = 0.1                                  # mm per hour (same as the revised wet definition)
CHUNK = 1_000_000
OUTDIR = "/root/autodl-tmp/results/metrics" if os.path.isdir("/root/autodl-tmp/results") else "results/metrics"
os.makedirs(OUTDIR, exist_ok=True)


def first(*paths):
    return next((p for p in paths if os.path.exists(p)), None)


ST = first("data/hly532.csv", "../data/hly532.csv", "/root/autodl-tmp/data/hly532.csv")
RAW = first("data/04-24.csv", "../data/04-24.csv", "/root/autodl-tmp/data/04-24.csv")
RED = first("data/dublin_regional_reduced.csv", "../data/dublin_regional_reduced.csv",
            "/root/autodl-tmp/data/dublin_regional_reduced.csv")
assert ST and RAW and RED, f"missing input: station={ST} raw={RAW} reduced={RED}"
print("Station file:", ST, "\nERA5 raw    :", RAW, "\nERA5 reduced:", RED)

# ---------------- station ----------------
with open(ST, encoding="utf-8", errors="ignore") as f:
    hdr = next(i for i, l in enumerate(f) if l.startswith("date,"))
st = pd.read_csv(ST, skiprows=hdr, low_memory=False)
cols = list(st.columns)                                   # ['date','ind','rain','ind.1',...]
st = st.rename(columns={cols[1]: "rain_ind"})
st["time"] = pd.to_datetime(st["date"], format="%d-%b-%Y %H:%M", errors="coerce")
st["rain"] = pd.to_numeric(st["rain"], errors="coerce")
st = st.dropna(subset=["time"]).drop_duplicates("time").set_index("time").sort_index()
st = st.loc[START:END]
print(f"Station rows 2004-2021: {len(st):,}; missing rain: {st.rain.isna().sum():,} "
      f"({st.rain.isna().mean()*100:.2f} %); max {st.rain.max():.1f} mm/h")

# ---------------- ERA5 ----------------
red = pd.read_csv(RED, parse_dates=["valid_time"]).set_index("valid_time").sort_index()
era_reg = red["tp"] * 1000.0
assert len(era_reg) == 26300, f"regional file rows {len(era_reg)}"

head = pd.read_csv(RAW, nrows=1)
low = {c.lower(): c for c in head.columns}
T = next(low[k] for k in ("valid_time", "time", "datetime", "date") if k in low)
LA = next(low[k] for k in ("latitude", "lat") if k in low)
LO = next(low[k] for k in ("longitude", "lon") if k in low)
TP = low["tp"]
parts = []
for ch in pd.read_csv(RAW, usecols=[T, LA, LO, TP], chunksize=CHUNK):
    m = ch[LA].round(2).eq(CELL[0]) & ch[LO].round(2).eq(CELL[1])
    if m.any():
        parts.append(ch.loc[m])
cell = pd.concat(parts)
cell[T] = pd.to_datetime(cell[T])
cell = cell[(cell[T] >= START) & (cell[T] <= END) & (cell[T].dt.hour % 6 == 0)]
era_cell = cell.drop_duplicates(T).set_index(T).sort_index()[TP] * 1000.0
assert len(era_cell) == 26300, f"cell rows {len(era_cell)}"
print(f"ERA5 cell {CELL}: {len(era_cell):,} stamps; regional mean: {len(era_reg):,} stamps")
idx = era_reg.index

# ---------------- helpers ----------------
def stats(obs, mod):
    ok = ~(np.isnan(obs) | np.isnan(mod))
    o, m = obs[ok], mod[ok]
    pr = float(np.corrcoef(o, m)[0, 1])
    sp = float(pd.Series(o).corr(pd.Series(m), method="spearman"))
    out = {"N": int(ok.sum()), "Pearson_r": pr, "Spearman_rho": sp,
           "Mean_obs_mm": float(o.mean()), "Mean_ERA5_mm": float(m.mean()),
           "Bias_ERA5_minus_obs_mm": float((m - o).mean()), "RMSE_mm": float(np.sqrt(np.mean((m - o) ** 2))),
           "Wet_freq_obs": float((o >= WET).mean()), "Wet_freq_ERA5": float((m >= WET).mean()),
           "Q95_obs": float(np.quantile(o, .95)), "Q95_ERA5": float(np.quantile(m, .95)),
           "Q99_obs": float(np.quantile(o, .99)), "Q99_ERA5": float(np.quantile(m, .99)),
           "Max_obs": float(o.max()), "Max_ERA5": float(m.max())}
    for lab, thr in (("0.1", 0.1), ("0.5", 0.5), ("1.0", 1.0), ("obsQ95", float(np.quantile(o, .95)))):
        ob, mb = o >= thr, m >= thr
        h, mi, fa = int((ob & mb).sum()), int((ob & ~mb).sum()), int((~ob & mb).sum())
        d = lambda a, b: float(a / b) if b else np.nan
        out.update({f"POD_{lab}": d(h, h + mi), f"FAR_{lab}": d(fa, h + fa), f"CSI_{lab}": d(h, h + mi + fa),
                    f"Bias_{lab}": d(h + fa, h + mi), f"Nobs_{lab}": int(ob.sum())})
    return out


def station_at(shift_h):
    return st["rain"].reindex(idx + pd.Timedelta(hours=shift_h)).to_numpy()


# ---------------- 1. time-alignment test ----------------
rows = []
for sh in (-1, 0, 1):
    obs = station_at(sh)
    for name, era in (("ERA5 nearest cell", era_cell.to_numpy()), ("ERA5 regional mean", era_reg.to_numpy())):
        s = stats(obs, era)
        rows.append({"Station_shift_h": sh, "ERA5_series": name, "N": s["N"],
                     "Pearson_r": s["Pearson_r"], "Spearman_rho": s["Spearman_rho"]})
shift = pd.DataFrame(rows)
shift.to_csv(os.path.join(OUTDIR, "q04_shift_test.csv"), index=False)
print("\n=== TIME-ALIGNMENT TEST (station value at t+shift vs ERA5 tp at t) ===")
print(shift.round(4).to_string(index=False))
best = int(shift[shift.ERA5_series == "ERA5 nearest cell"].sort_values("Spearman_rho").iloc[-1]["Station_shift_h"])
print(f"-> highest Spearman for the nearest cell at shift {best:+d} h")
print("   shift  0: station stamp t labels the hour ENDING at t (same convention as ERA5)")
print("   shift -1: station stamp labels the START of the hour (station value at t-1h = hour ending at t)")
print("   shift +1: station stamp labels the hour ending one hour LATER than ERA5's")
if best != 0:
    print("   NOTE: best shift is not 0 -> state the alignment you used in the Methods / Supplement.")

# ---------------- 2. main comparison (best shift) ----------------
obs = station_at(best)
n_test0 = int(len(idx) * 0.85)
periods = {"2004-2021 all": np.ones(len(idx), bool),
           "test period (last 15 %)": np.arange(len(idx)) >= n_test0}
srows = []
for pname, pm in periods.items():
    for name, era in (("ERA5 nearest cell", era_cell.to_numpy()), ("ERA5 regional mean", era_reg.to_numpy())):
        s = stats(obs[pm], era[pm])
        srows.append({"Period": pname, "ERA5_series": name, "Station_shift_h": best, **s})
summ = pd.DataFrame(srows)
summ.to_csv(os.path.join(OUTDIR, "q04_station_vs_era5_summary.csv"), index=False)
pd.set_option("display.width", 220)
show = ["Period", "ERA5_series", "N", "Pearson_r", "Spearman_rho", "Mean_obs_mm", "Mean_ERA5_mm",
        "Bias_ERA5_minus_obs_mm", "RMSE_mm", "Wet_freq_obs", "Wet_freq_ERA5", "Q95_obs", "Q95_ERA5",
        "Q99_obs", "Q99_ERA5", "Max_obs", "Max_ERA5"]
print("\n=== ERA5 vs DUBLIN AIRPORT OBSERVATIONS (mm per hour) ===")
print(summ[show].round(3).to_string(index=False))
ev = ["Period", "ERA5_series", "POD_0.1", "FAR_0.1", "CSI_0.1", "Bias_0.1", "POD_obsQ95", "FAR_obsQ95", "CSI_obsQ95"]
print("\n=== EVENT AGREEMENT (wet >=0.1 mm, and observed-Q95 exceedance) ===")
print(summ[ev].round(3).to_string(index=False))

# ---------------- 3. seasonal ----------------
season = {12: "DJF", 1: "DJF", 2: "DJF", 3: "MAM", 4: "MAM", 5: "MAM", 6: "JJA", 7: "JJA", 8: "JJA",
          9: "SON", 10: "SON", 11: "SON"}
sea = idx.month.map(season).to_numpy()
rr = []
for s_ in ["DJF", "MAM", "JJA", "SON"]:
    pm = sea == s_
    for name, era in (("ERA5 nearest cell", era_cell.to_numpy()), ("ERA5 regional mean", era_reg.to_numpy())):
        s = stats(obs[pm], era[pm])
        rr.append({"Season": s_, "ERA5_series": name, "N": s["N"], "Spearman_rho": s["Spearman_rho"],
                   "Bias_mm": s["Bias_ERA5_minus_obs_mm"], "Wet_freq_obs": s["Wet_freq_obs"],
                   "Wet_freq_ERA5": s["Wet_freq_ERA5"], "Q95_obs": s["Q95_obs"], "Q95_ERA5": s["Q95_ERA5"]})
seas = pd.DataFrame(rr)
seas.to_csv(os.path.join(OUTDIR, "q04_seasonal.csv"), index=False)
print("\n=== BY SEASON ===")
print(seas.round(3).to_string(index=False))

# ---------------- 4. data-quality bookkeeping + aligned pairs ----------------
ind = st["rain_ind"].reindex(idx + pd.Timedelta(hours=best))
cnt = ind.value_counts(dropna=False).rename_axis("rain_indicator").reset_index(name="count")
cnt["share"] = cnt["count"] / cnt["count"].sum()
cnt.to_csv(os.path.join(OUTDIR, "q04_rain_indicator_counts.csv"), index=False)
print("\n=== STATION RAIN INDICATOR at the matched stamps (0 = satisfactory) ===")
print(cnt.round(4).to_string(index=False))

# indicator distribution by year over the whole station file (when does a code appear / change?)
with open(ST, encoding="utf-8", errors="ignore") as f:
    hdr2 = next(i for i, l in enumerate(f) if l.startswith("date,"))
allst = pd.read_csv(ST, skiprows=hdr2, usecols=[0, 1], header=0, names=["date", "ind"], low_memory=False)
allst["year"] = pd.to_datetime(allst["date"], format="%d-%b-%Y %H:%M", errors="coerce").dt.year
yr = allst.groupby(["year", "ind"]).size().unstack(fill_value=0)
yr.to_csv(os.path.join(OUTDIR, "q04_rain_indicator_by_year.csv"))
print("\n=== RAIN INDICATOR BY YEAR (whole station file, 1995-2022) ===")
print(yr.loc[1995:2022].to_string())

# observed intensity at the matched stamps (for the WMO intensity discussion)
o_ok = obs[~np.isnan(obs)]
print(f"\nObserved hourly rain at matched stamps: max {o_ok.max():.1f} mm/h; "
      f">=2.5 mm/h: {int((o_ok >= 2.5).sum())}; >=10 mm/h: {int((o_ok >= 10).sum())} of {len(o_ok)}")
print(f"ERA5 nearest cell: >=2.5: {int((era_cell.to_numpy() >= 2.5).sum())}; >=10: {int((era_cell.to_numpy() >= 10).sum())}")

ok0 = ind.to_numpy() == 0
if ok0.sum() >= 500:
    s0 = stats(obs[ok0], era_cell.to_numpy()[ok0])
    print(f"\nSensitivity: indicator==0 only (N={s0['N']}): nearest-cell Spearman {s0['Spearman_rho']:.3f}, "
          f"Pearson {s0['Pearson_r']:.3f}, bias {s0['Bias_ERA5_minus_obs_mm']:+.3f} mm")
else:
    print(f"\nSensitivity (indicator==0 only) skipped: only {int(ok0.sum())} matched stamps have indicator 0.")
pd.DataFrame({"valid_time": idx, "station_mm": obs, "era5_cell_mm": era_cell.to_numpy(),
              "era5_regional_mm": era_reg.to_numpy(), "rain_indicator": ind.to_numpy()}
             ).to_csv(os.path.join(OUTDIR, "q04_pairs.csv"), index=False)
print("\nSaved q04_*.csv to", OUTDIR)
