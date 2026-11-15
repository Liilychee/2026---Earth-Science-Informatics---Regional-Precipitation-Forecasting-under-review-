"""
q08c: cutoff-free event discrimination on the common HRES subset (1,970 samples, 06/18 UTC valid times),
for two targets: (A) the ERA5 regional-mean last-hour target, (B) Dublin Airport station rain.

Why: q08_hres_comparison.csv / q08b_station_comparison.csv score every forecast with ONE fixed threshold on the
predicted value. The ML models are compressed towards the mean (almost no predictions above Q95 or 1 mm/h), so a
fixed cutoff hides their ranking ability. This script adds two criteria that need no tuning on the test subset:
  (1) AUC for event = {truth >= threshold}
  (2) frequency-matched cutoff: cutoff = k-th largest forecast value, k = number of observed events
      (forecast and observed event counts agree); report POD, FAR, CSI.
Paired moving-block bootstrap of AUC differences. Same scheme as q08_hres_comparison.py / q08_station_comparison.py:
moving blocks (not circular), BLOCK=14 samples (7 days at two stamps/day), N_BOOT=10000, seed 42.

Zero training. Reads q08_hres_aligned_samples.csv and q04_pairs.csv (read-only). Does not modify any existing file.

Run (on AutoDL):
  cd /root/autodl-tmp && python3 code/analysis_q08c_event_auc.py 2>&1 | tee results/metrics/q08c_output.txt
Env (optional): BASE (default /root/autodl-tmp), NBOOT (10000), BLOCK (14), Q95 (0.5740)
Outputs: results/metrics/q08c_event_auc.csv, q08c_event_auc_paired.csv  (column 'target' = ERA5 | station)
"""
import os
import numpy as np
import pandas as pd
from scipy.stats import rankdata

BASE = os.environ.get("BASE", "/root/autodl-tmp")
MET = os.path.join(BASE, "results", "metrics")
SAMPLES = os.path.join(MET, "q08_hres_aligned_samples.csv")
PAIRS = os.path.join(MET, "q04_pairs.csv")
CMP = os.path.join(MET, "q08_hres_comparison.csv")
CMPS = os.path.join(MET, "q08b_station_comparison.csv")
NBOOT = int(os.environ.get("NBOOT", 10000))
BLOCK = int(os.environ.get("BLOCK", 14))
Q95 = float(os.environ.get("Q95", 0.5740))
SEED = 42

ML = ["BiLSTM-Attention", "XGBoost", "BU-LSTM-Attention",
      "Probabilistic BiLSTM-Attention", "BU-LSTM", "Transformer"]
HRES = "HRES (6 h mean)"
PERS = "Persistence"
CLIM = "Climatology (month x hour)"
AR1 = "AR(1)"
CEIL_ERA5 = "Perfect 6 h mean (ceiling)"
CEIL_ST = "ERA5 6 h mean (window diagnostic)"
ERA5_LABEL = "ERA5 label (regional mean)"


def auc_from_rank(r, p):
    n1 = int(p.sum()); n0 = len(p) - n1
    if n1 == 0 or n0 == 0:
        return np.nan
    return (r[p].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def freq_matched(p, s):
    k = int(p.sum())
    thr = np.sort(s)[::-1][k - 1]
    f = s >= thr
    nf = int(f.sum()); hits = int((f & p).sum())
    return nf, hits / k, (1 - hits / nf) if nf else np.nan, hits / (k + nf - hits)


def run_target(name, d, ytrue, models, thr, pairs):
    n = len(d)
    pos = {k: (ytrue >= t) for k, t in thr.items()}
    print(f"\n########## target: {name}; n={n}; observed events:",
          {k: int(v.sum()) for k, v in pos.items()}, "##########")
    S = {m: d[m].to_numpy(float) for m in models}
    rk = {m: rankdata(S[m]) for m in models}
    rows = []
    for m in models:
        for k, p in pos.items():
            nf, pod, far, csi = freq_matched(p, S[m])
            rows.append(dict(target=name, model=m, event=k, n_obs=int(p.sum()),
                             AUC=auc_from_rank(rk[m], p),
                             FM_n_fcst=nf, FM_POD=pod, FM_FAR=far, FM_CSI=csi))
    res = pd.DataFrame(rows)

    rng = np.random.default_rng(SEED)
    nb = int(np.ceil(n / BLOCK))
    starts = rng.integers(0, n - BLOCK + 1, size=(NBOOT, nb))
    idx = (starts[:, :, None] + np.arange(BLOCK)).reshape(NBOOT, -1)[:, :n]
    A = {m: {k: np.empty(NBOOT) for k in thr} for m in models}
    for b in range(NBOOT):
        ii = idx[b]
        for m in models:
            r = rankdata(S[m][ii])
            for k, p in pos.items():
                A[m][k][b] = auc_from_rank(r, p[ii])
    prow = []
    for a, ref in pairs:
        for k in thr:
            pa = res[(res.model == a) & (res.event == k)]["AUC"].iloc[0]
            pr = res[(res.model == ref) & (res.event == k)]["AUC"].iloc[0]
            lo, hi = np.nanpercentile(A[a][k] - A[ref][k], [2.5, 97.5])
            prow.append(dict(target=name, model=a, reference=ref, event=k, dAUC=pa - pr,
                             ci_low=lo, ci_high=hi, significant=bool(lo > 0 or hi < 0)))
    pr_df = pd.DataFrame(prow)

    pd.set_option("display.width", 220)
    print(f"\n===== [{name}] AUC (event = truth >= threshold) =====")
    print(res.pivot(index="model", columns="event", values="AUC").loc[models].round(3).to_string())
    for k in thr:
        sub = res[res.event == k].set_index("model").loc[models]
        print(f"\n===== [{name}] frequency-matched cutoff, {k} (obs {int(pos[k].sum())}) =====")
        print(sub[["FM_n_fcst", "FM_POD", "FM_FAR", "FM_CSI"]].round(3).to_string())
    print(f"\n===== [{name}] paired AUC differences (model minus reference; negative = reference better) =====")
    print(pr_df.drop(columns="target").round(4).to_string(index=False))
    return res, pr_df


d = pd.read_csv(SAMPLES)
d["valid_time"] = pd.to_datetime(d["valid_time"])
d = d.sort_values("valid_time").reset_index(drop=True)
gaps = d["valid_time"].diff().dropna().dt.total_seconds() / 3600
print(f"samples {len(d)}; {d['valid_time'].dt.date.nunique()} distinct days; median gap {gaps.median():.0f} h; "
      f"gaps > 12 h: {(gaps > 12).sum()}")
print(f"moving-block bootstrap: block {BLOCK} samples (~{BLOCK/2:.0f} days), NBOOT {NBOOT}, seed {SEED}")
chk = np.abs(d["hres_tp6_mm"].to_numpy(float) / 6 - d[HRES].to_numpy(float)).max()
print(f"check HRES (6 h mean) == hres_tp6_mm/6: max abs diff {chk:.2e}")
need = ML + [HRES, PERS, CLIM, AR1, CEIL_ERA5]
miss = [m for m in need if m not in d.columns]
if miss:
    raise SystemExit(f"missing columns: {miss}")

# ---------------- A. ERA5 target ----------------
thrA = {"wet>=0.1": 0.1, "Q95": Q95, ">=1.0": 1.0}
modelsA = ML + [HRES, PERS, CLIM, AR1, CEIL_ERA5]
pairsA = [(m, HRES) for m in ML] + [(m, PERS) for m in ML] + [(HRES, PERS), (HRES, CLIM)]
yA = d["y_true"].to_numpy(float)
if os.path.exists(CMP):
    c = pd.read_csv(CMP)
    for col, k in (("wet01_obs_events", "wet>=0.1"), ("Q95_obs_events", "Q95")):
        got = int((yA >= thrA[k]).sum()); ref = int(c[col].iloc[0])
        print(f"count check {k}: here {got} vs q08_hres_comparison.csv {ref}" + ("" if got == ref else "  <-- WARNING"))
resA, prA = run_target("ERA5", d, yA, modelsA, thrA, pairsA)

# ---------------- B. station target ----------------
pairs_df = pd.read_csv(PAIRS, parse_dates=["valid_time"]).drop_duplicates("valid_time")
ds = d.merge(pairs_df[["valid_time", "station_mm", "era5_regional_mm"]], on="valid_time", how="left")
n_nan = int(ds["station_mm"].isna().sum())
ds = ds.dropna(subset=["station_mm"]).reset_index(drop=True)
print(f"\nstation merge: {len(d)} aligned samples, {n_nan} without station value, {len(ds)} used")
ds[ERA5_LABEL] = ds["era5_regional_mm"].to_numpy(float)
ds[CEIL_ST] = ds[CEIL_ERA5].to_numpy(float)
thrB = {"wet>=0.1": 0.1, ">=1.0": 1.0}
modelsB = ML + [HRES, PERS, CLIM, AR1, CEIL_ST, ERA5_LABEL]
pairsB = [(m, HRES) for m in ML] + [(m, PERS) for m in ML] + \
         [(ERA5_LABEL, HRES), (HRES, PERS), (HRES, CLIM)]
yB = ds["station_mm"].to_numpy(float)
if os.path.exists(CMPS):
    c = pd.read_csv(CMPS)
    for col, k in (("wet01_obs", "wet>=0.1"), ("ge1mm_obs", ">=1.0")):
        got = int((yB >= thrB[k]).sum()); ref = int(c[col].iloc[0])
        print(f"count check station {k}: here {got} vs q08b_station_comparison.csv {ref}" +
              ("" if got == ref else "  <-- WARNING"))
resB, prB = run_target("station", ds, yB, modelsB, thrB, pairsB)

pd.concat([resA, resB]).to_csv(os.path.join(MET, "q08c_event_auc.csv"), index=False)
pd.concat([prA, prB]).to_csv(os.path.join(MET, "q08c_event_auc_paired.csv"), index=False)
print(f"\nSaved q08c_event_auc.csv and q08c_event_auc_paired.csv to {MET}")
