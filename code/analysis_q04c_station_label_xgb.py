# ============================================================
# analysis_q04c_station_label_xgb.py -- issue 04 (R1 M6, R4 m36), small CPU experiment
#
# Question: if the TARGET is the Dublin Airport observation instead of the ERA5 regional mean,
# does training on the observation help?  (inputs stay ERA5 regional-mean variables.)
#
#   S  : XGBoost trained on STATION hourly rain at the target stamp   (station-label training)
#   E  : XGBoost trained on ERA5 regional-mean tp (the paper's target), evaluated on the station
#   B1 : station climatology month x hour (TRAIN station targets)
#   B2 : constant = train mean of station rain
#   B3 : persistence = station rain at the last input stamp t
#
# Everything else is identical to the main pipeline: 2004-2021 six-hourly stamps, chronological 70/15/15,
# scalers on TRAIN only, 6-step windows built inside each split, same 7 features, XGBoost
# n_estimators=100, lr=0.05, max_depth=6, subsample=0.8, colsample_bytree=0.8, seeds 42,123,7,2024,99, no tuning.
# Time alignment: station value at the target stamp, shift 0 (same as q04: ERA5 tp at stamp t = hour ending t;
# the station key does not define the window; shift 0 had the highest/similar Spearman in q04_shift_test.csv).
#
# Evaluated on the STATION target of the test split (3,939 windows): RMSE, MAE, Spearman, wet>=0.1 POD/FAR/CSI
# (prediction >= 0.1 mm, and frequency-matched threshold), RMSE on wet and upper-tail (station train Q95) subsets,
# skill vs B1, paired circular block bootstrap (block 28, 2,000, seed 42) on seed-averaged predictions.
# Sanity: E on the ERA5 target must reproduce RMSE ~0.2439.
#
# Run from the folder containing data/ (AutoDL: cd /root/autodl-tmp):
#     python3 code/analysis_q04c_station_label_xgb.py 2>&1 | tee results/metrics/q04c_station_label_xgb_output.txt
# Outputs (results/ablation/): q04c_raw.csv, q04c_summary.csv, q04c_paired.csv, q04c_test_preds.csv
# ============================================================
import os
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.preprocessing import StandardScaler

SEEDS = [42, 123, 7, 2024, 99]
WINDOW = 6
FEATS = ['mxtpr', 'mntpr', 'lsp', 'tcc', 'v10', 'sp', 'd2m']
XGB_KW = dict(n_estimators=100, learning_rate=0.05, max_depth=6, subsample=0.8, colsample_bytree=0.8)
BLOCK, NBOOT, BSEED = 28, 2000, 42
WET = 0.1
SEASON = {12: "DJF", 1: "DJF", 2: "DJF", 3: "MAM", 4: "MAM", 5: "MAM", 6: "JJA", 7: "JJA", 8: "JJA",
          9: "SON", 10: "SON", 11: "SON"}


def first(*p):
    return next((x for x in p if os.path.exists(x)), None)


ST = first("data/hly532.csv", "../data/hly532.csv", "/root/autodl-tmp/data/hly532.csv")
RED = first("data/dublin_regional_reduced.csv", "../data/dublin_regional_reduced.csv",
            "/root/autodl-tmp/data/dublin_regional_reduced.csv")
assert ST and RED, f"missing input station={ST} reduced={RED}"

# ---- station ----
with open(ST, encoding="utf-8", errors="ignore") as f:
    hdr = next(i for i, l in enumerate(f) if l.startswith("date,"))
st = pd.read_csv(ST, skiprows=hdr, low_memory=False)
st = st.rename(columns={st.columns[1]: "rain_ind"})
st["time"] = pd.to_datetime(st["date"], format="%d-%b-%Y %H:%M", errors="coerce")
st["rain"] = pd.to_numeric(st["rain"], errors="coerce")
st = st.dropna(subset=["time"]).drop_duplicates("time").set_index("time").sort_index()

# ---- ERA5 regional ----
df = pd.read_csv(RED, parse_dates=["valid_time"]).sort_values("valid_time").reset_index(drop=True)
df["tp_mm"] = df["tp"] * 1000.0 if "tp" in df.columns else df["tp_mm"]
assert len(df) == 26300
df["st_mm"] = st["rain"].reindex(df["valid_time"]).to_numpy()
print(f"Station values missing at the 26,300 stamps: {int(df.st_mm.isna().sum())}")
n = len(df)
tr_end, va_end = int(n * 0.70), int(n * 0.85)
parts = {"train": df.iloc[:tr_end], "val": df.iloc[tr_end:va_end], "test": df.iloc[va_end:]}
sx = StandardScaler().fit(parts["train"][FEATS])


def windows(p):
    p = p.reset_index(drop=True)
    Xv = sx.transform(p[FEATS])
    X = np.stack([Xv[i:i + WINDOW] for i in range(len(p) - WINDOW)]).reshape(len(p) - WINDOW, -1)
    t = p.iloc[WINDOW:].reset_index(drop=True)
    lag = p.iloc[WINDOW - 1:len(p) - 1]["st_mm"].to_numpy()
    return X.astype(np.float32), t, lag


W = {k: windows(v) for k, v in parts.items()}
Xtr, ttr, _ = W["train"]
Xte, tte, lag_te = W["test"]
assert len(Xtr) == 18404 and len(Xte) == 3939, "window counts differ from main pipeline"
y_era_tr, y_era_te = ttr.tp_mm.to_numpy(), tte.tp_mm.to_numpy()
y_st_tr, y_st_te = ttr.st_mm.to_numpy(), tte.st_mm.to_numpy()
ok_tr = ~np.isnan(y_st_tr)
ok_te = ~np.isnan(y_st_te)
print(f"train windows {len(Xtr)} (station target valid {int(ok_tr.sum())}); test {len(Xte)} (valid {int(ok_te.sum())})")
print(f"Station test: mean {np.nanmean(y_st_te):.4f}, wet>=0.1 {np.nanmean(y_st_te >= WET)*100:.1f}%, max {np.nanmax(y_st_te):.1f}")

q95_st = float(np.nanquantile(y_st_tr, 0.95))
wet_freq_tr = float(np.nanmean(y_st_tr >= WET))
print(f"Station train Q95 = {q95_st:.4f} mm/h; train wet freq {wet_freq_tr*100:.1f}%")

# ---- baselines on station target ----
tr_f = ttr.assign(y=y_st_tr)
tr_f["month"], tr_f["hour"] = tr_f.valid_time.dt.month, tr_f.valid_time.dt.hour
clim = tr_f.dropna(subset=["y"]).groupby(["month", "hour"]).y.mean()
B1 = np.array([clim.loc[(m, h)] for m, h in zip(tte.valid_time.dt.month, tte.valid_time.dt.hour)])
B2 = np.full(len(tte), float(np.nanmean(y_st_tr)))
B3 = lag_te.copy()

# ---- train S and E ----
preds = {"S_station_trained": {}, "E_ERA5_trained": {}}
era_rmse = []
for s in SEEDS:
    mS = xgb.XGBRegressor(random_state=s, **XGB_KW).fit(Xtr[ok_tr], y_st_tr[ok_tr])
    mE = xgb.XGBRegressor(random_state=s, **XGB_KW).fit(Xtr, y_era_tr)
    preds["S_station_trained"][s] = mS.predict(Xte)
    pe = mE.predict(Xte)
    preds["E_ERA5_trained"][s] = pe
    era_rmse.append(float(np.sqrt(np.mean((y_era_te - pe) ** 2))))
print(f"SANITY: E on ERA5 target, mean test RMSE over seeds = {np.mean(era_rmse):.4f} (main pipeline 0.2439 / 0.2437)")

# ---- metrics ----
def rmse(a, b):
    return float(np.sqrt(np.mean((a - b) ** 2)))


def spear(a, b):
    return float(pd.Series(a).corr(pd.Series(b), method="spearman")) if np.std(b) > 0 else np.nan


def events(o, p, thr_p):
    ob, pb = o >= WET, p >= thr_p
    h, mi, fa = int((ob & pb).sum()), int((ob & ~pb).sum()), int((~ob & pb).sum())
    d = lambda a, b: a / b if b else np.nan
    return d(h, h + mi), d(fa, h + fa), d(h, h + mi + fa)


o = y_st_te
masks = {"all": ok_te, "wet>=0.1": ok_te & (o >= WET), "upper tail (>=train Q95)": ok_te & (o >= q95_st)}
season = tte.valid_time.dt.month.map(SEASON).to_numpy()
for sname in ("DJF", "MAM", "JJA", "SON"):
    masks[sname] = ok_te & (season == sname)

methods = {f"S seed{s}": preds["S_station_trained"][s] for s in SEEDS}
methods.update({f"E seed{s}": preds["E_ERA5_trained"][s] for s in SEEDS})
S_mean = np.mean([preds["S_station_trained"][s] for s in SEEDS], axis=0)
E_mean = np.mean([preds["E_ERA5_trained"][s] for s in SEEDS], axis=0)
final = {"S station-trained (seed mean)": S_mean, "E ERA5-trained (seed mean)": E_mean,
         "B1 station clim month x hour": B1, "B2 constant (train mean)": B2, "B3 persistence": B3}

raw_rows = []
for k, p in methods.items():
    m = ok_te
    raw_rows.append({"Method": k, "RMSE": rmse(o[m], p[m]), "MAE": float(np.mean(np.abs(o[m] - p[m]))),
                     "Spearman": spear(o[m], p[m])})
raw = pd.DataFrame(raw_rows)
raw.to_csv("results/ablation/q04c_raw.csv", index=False) if os.path.isdir("results/ablation") else None

rows = []
for name, p in final.items():
    for sname, mk in masks.items():
        if mk.sum() < 5:
            continue
        pp, oo = p[mk], o[mk]
        rm_ref = rmse(oo, B1[mk])
        r = {"Method": name, "Subset": sname, "N": int(mk.sum()), "RMSE": rmse(oo, pp),
             "Skill_vs_B1": 1 - rmse(oo, pp) / rm_ref, "Spearman": spear(oo, pp)}
        if sname == "all":
            pod, far, csi = events(o[ok_te], p[ok_te], WET)
            thr_fm = float(np.nanquantile(p[ok_te], 1 - wet_freq_tr))
            pod2, far2, csi2 = events(o[ok_te], p[ok_te], thr_fm)
            r.update({"POD_0.1": pod, "FAR_0.1": far, "CSI_0.1": csi,
                      "Thr_freq_matched": thr_fm, "POD_fm": pod2, "FAR_fm": far2, "CSI_fm": csi2})
        rows.append(r)
summ = pd.DataFrame(rows)

# ---- paired block bootstrap ----
N = len(o)
rng = np.random.default_rng(BSEED)
nblk = int(np.ceil(N / BLOCK))
starts = rng.integers(0, N, size=(NBOOT, nblk))
idx = ((starts[:, :, None] + np.arange(BLOCK)[None, None, :]) % N).reshape(NBOOT, -1)[:, :N]


def boot_rmse(p, mk):
    m = mk.astype(float)
    num, den = ((o - p) ** 2 * m)[idx].sum(1), m[idx].sum(1)
    return np.sqrt(num / np.maximum(den, 1))


prow = []
pairs = [("S station-trained", S_mean, "E ERA5-trained", E_mean),
         ("S station-trained", S_mean, "B1 clim", B1),
         ("E ERA5-trained", E_mean, "B1 clim", B1),
         ("S station-trained", S_mean, "B2 constant", B2)]
for a, pa, b, pb in pairs:
    for sname in ("all", "wet>=0.1", "upper tail (>=train Q95)"):
        mk = masks[sname]
        d = boot_rmse(pa, mk) - boot_rmse(pb, mk)
        prow.append({"A": a, "B": b, "Subset": sname, "N": int(mk.sum()),
                     "RMSE_A": rmse(o[mk], pa[mk]), "RMSE_B": rmse(o[mk], pb[mk]),
                     "A_minus_B": rmse(o[mk], pa[mk]) - rmse(o[mk], pb[mk]),
                     "CI_low": float(np.percentile(d, 2.5)), "CI_high": float(np.percentile(d, 97.5))})
paired = pd.DataFrame(prow)
# seed consistency S vs E (all)
sd = [rmse(o[ok_te], preds["S_station_trained"][s][ok_te]) - rmse(o[ok_te], preds["E_ERA5_trained"][s][ok_te])
      for s in SEEDS]

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 30)
print("\n===== per-seed RMSE / Spearman on STATION test target =====")
print(raw.round(4).to_string(index=False))
print("\n===== summary (station target) =====")
print(summ.round(4).to_string(index=False))
print(f"\n===== paired RMSE (A minus B; negative = A better); bootstrap block {BLOCK}, {NBOOT} reps, seed {BSEED} =====")
print(paired.round(4).to_string(index=False))
print(f"\nS minus E per seed (all): {[round(x, 4) for x in sd]}; seeds with S better: {sum(x < 0 for x in sd)}/{len(SEEDS)}")

os.makedirs("results/ablation", exist_ok=True)
raw.to_csv("results/ablation/q04c_raw.csv", index=False)
summ.to_csv("results/ablation/q04c_summary.csv", index=False)
paired.to_csv("results/ablation/q04c_paired.csv", index=False)
pd.DataFrame({"valid_time": tte.valid_time, "station_mm": o, "era5_mm": y_era_te, "S": S_mean, "E": E_mean,
              "B1": B1, "B2": B2, "B3": B3}).to_csv("results/ablation/q04c_test_preds.csv", index=False)
print("\nSaved results/ablation/q04c_*.csv")
