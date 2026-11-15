# ============================================================
# Item 08: contextual comparison with ECMWF IFS HRES (WeatherBench 2), zero training.
#
# Sample set : test targets valid at 06 and 18 UTC (HRES initialised at 00/12 UTC,
#              i.e. at the model's input cut-off time t, lead +6 h).
# Truth      : y_true in the saved prediction files (ERA5 regional mean, hour (t+5h, t+6h], mm/h).
# Forecasts  : saved single-run predictions of all models; persistence;
#              month-by-hour climatology and AR(1) fitted on the training period;
#              HRES proxy  = HRES 6 h accumulation over (t, t+6h] / 6;
#              6 h ceiling = ERA5 (WeatherBench 2) 6 h accumulation over (t, t+6h] / 6.
#              The ceiling is a perfect 6 h-mean forecast: its error comes only
#              from predicting a 6 h mean instead of the last hour.
# Inputs (read-only): results/*_preds.csv, data/q08/HRES/*.nc, data/q08/WeatherBench/*.nc
# Outputs: results/metrics/q08_hres_comparison.csv      (Table S13 source)
#          results/metrics/q08_hres_bootstrap.csv       (paired block bootstrap, dRMSE)
#          results/metrics/q08_hres_aligned_samples.csv (per-sample audit file)
# ============================================================
import glob, os, re
import h5py
import numpy as np
import pandas as pd

ROOT = os.environ.get("Q08_ROOT", "/root/autodl-tmp")
RES = f"{ROOT}/results"
MET = f"{RES}/metrics"
Q95 = 0.574048          # training-period Q95 of window targets (q10_prepare_output.txt)
WET = 0.1               # wet threshold, mm/h (item 03)
N_BOOT, BLOCK, SEED = 10000, 14, 42   # 14 samples = 7 days at two samples per day
MODELS = {              # label -> saved single-run prediction file (seed 42)
    "BiLSTM-Attention": "bilstm_attention_preds.csv",
    "XGBoost": "xgboost_preds.csv",
    "BU-LSTM-Attention": "proposed_model_preds.csv",
    "Probabilistic BiLSTM-Attention": "prob_bilstm_attention_preds.csv",
    "BU-LSTM": "bulstm_preds.csv",
    "Transformer": "transformer_preds.csv",
}
os.makedirs(MET, exist_ok=True)


# ---------- reading netCDF with h5py only ----------
def _attr(v, k, default=None):
    a = v.attrs.get(k, default)
    if isinstance(a, (bytes, np.bytes_)):
        return a.decode()
    if isinstance(a, np.ndarray) and a.size == 1:
        a = a.ravel()[0]
        return a.decode() if isinstance(a, (bytes, np.bytes_)) else a
    return a


def read_var(h, name):
    v = h[name]
    a = v[...].astype("float64")
    fill = _attr(v, "_FillValue")
    if fill is not None and not (isinstance(fill, float) and np.isnan(fill)):
        a[a == fill] = np.nan
    a = a * float(_attr(v, "scale_factor", 1.0)) + float(_attr(v, "add_offset", 0.0))
    try:
        dims = [h[ref[0]].name.strip("/") for ref in v.attrs["DIMENSION_LIST"]]
    except Exception:
        dims = None
    return a, dims


def read_time(h, name="time"):
    t = h[name]
    units = str(_attr(t, "units"))
    unit_map = {"days": "D", "hours": "h", "minutes": "min", "seconds": "s",
                "milliseconds": "ms", "microseconds": "us", "nanoseconds": "ns"}
    m = re.match(r"(\w+) since (.+)", units)
    if m:
        return pd.Timestamp(m.group(2).strip()) + pd.to_timedelta(t[...].astype("int64"), unit=unit_map[m.group(1)])
    return pd.to_timedelta(t[...].astype("int64"), unit=unit_map[units.strip()])   # a duration axis


def regional_mean(a, dims, keep):
    """Average over every axis that is not in `keep` (latitude/longitude)."""
    if dims is None:
        raise RuntimeError("DIMENSION_LIST missing; cannot identify axes safely")
    axes = tuple(i for i, d in enumerate(dims) if d not in keep)
    return np.nanmean(a, axis=axes), [d for d in dims if d in keep]


# ---------- 1. HRES: 6 h accumulation over (t, t+6h], t = 00/12 UTC ----------
rows = []
hres_files = sorted(glob.glob(f"{ROOT}/data/q08/HRES/**/*.nc", recursive=True))
assert hres_files, "no HRES files found"
for f in hres_files:
    with h5py.File(f, "r") as h:
        init = read_time(h, "time")
        lead_name = "prediction_timedelta" if "prediction_timedelta" in h else "step"
        lead_h = (read_time(h, lead_name) / pd.Timedelta(hours=1)).astype(int)
        a, dims = read_var(h, "total_precipitation_6hr")
        if dims is None:
            raise RuntimeError("DIMENSION_LIST missing in HRES file")
        a6 = np.take(a, list(lead_h).index(6), axis=dims.index(lead_name))   # lead +6 h only
        dims6 = [d for d in dims if d != lead_name]
        m, _ = regional_mean(a6, dims6, keep=("time",))
        rows.append(pd.DataFrame({"init": init, "hres_tp6_mm": m * 1000.0}))
hres = pd.concat(rows).drop_duplicates("init").sort_values("init")
hres["valid_time"] = hres["init"] + pd.Timedelta(hours=6)
n_neg = int((hres["hres_tp6_mm"] < 0).sum())
hres["hres_tp6_mm"] = hres["hres_tp6_mm"].clip(lower=0)
print(f"HRES: {len(hres)} inits, {hres['init'].min()} -> {hres['init'].max()}, "
      f"negative 6 h totals clipped: {n_neg}, NaN: {int(hres['hres_tp6_mm'].isna().sum())}")

# ---------- 2. ERA5 (WeatherBench 2): 6 h accumulation over (T-6h, T] ----------
rows = []
era_files = sorted(glob.glob(f"{ROOT}/data/q08/WeatherBench/**/*.nc", recursive=True))
assert era_files, "no WeatherBench ERA5 files found"
for f in era_files:
    with h5py.File(f, "r") as h:
        tt = read_time(h, "time")
        a, dims = read_var(h, "total_precipitation_6hr")
        m, _ = regional_mean(a, dims, keep=("time",))
        rows.append(pd.DataFrame({"valid_time": tt, "era5_tp6_mm": m * 1000.0}))
era = pd.concat(rows).drop_duplicates("valid_time").sort_values("valid_time")
print(f"ERA5 WB2: {len(era)} times, {era['valid_time'].min()} -> {era['valid_time'].max()}")

# ---------- 3. Saved model predictions, truth and references ----------
def load(fn):
    d = pd.read_csv(f"{RES}/{fn}", parse_dates=["valid_time"])
    return d

base = load(MODELS["XGBoost"])
test = base[base["split"] == "test"][["valid_time", "y_true"]].reset_index(drop=True)
train = base[base["split"] == "train"][["valid_time", "y_true"]].reset_index(drop=True)
for lab, fn in MODELS.items():
    d = load(fn)
    d = d[d["split"] == "test"].reset_index(drop=True)
    assert (d["valid_time"].values == test["valid_time"].values).all(), f"{lab}: times differ"
    assert np.abs(d["y_true"].values - test["y_true"].values).max() < 1e-6, f"{lab}: y_true differs"
    test[lab] = d["y_pred_mean"].values

pers = load("persistence_preds.csv")
pers = pers[pers["split"] == "test"][["valid_time", "y_pred_mean"]].rename(columns={"y_pred_mean": "Persistence"})
test = test.merge(pers, on="valid_time", how="left")

# month-by-hour climatology and AR(1), training period only (same definitions as item 07)
train["month"], train["hour"] = train["valid_time"].dt.month, train["valid_time"].dt.hour
clim = train.groupby(["month", "hour"])["y_true"].mean().rename("Climatology (month x hour)")
test["month"], test["hour"] = test["valid_time"].dt.month, test["valid_time"].dt.hour
test = test.join(clim, on=["month", "hour"])
tr = train.set_index("valid_time")["y_true"]
lag = tr.shift(1, freq="6h").reindex(tr.index)
ok = lag.notna()
b, a0 = np.polyfit(lag[ok].values, tr[ok].values, 1)
print(f"AR(1) on training targets: y(t+6h) = {a0:.4f} + {b:.4f} * y(t)   (item 07: 0.0763 + 0.2811)")
test["AR(1)"] = a0 + b * test["Persistence"]

# ---------- 4. Align with HRES and the 6 h ceiling; keep 06/18 UTC targets ----------
test = test.merge(hres[["valid_time", "init", "hres_tp6_mm"]], on="valid_time", how="left")
test = test.merge(era, on="valid_time", how="left")
sub = test[test["valid_time"].dt.hour.isin([6, 18])].copy()
sub = sub.dropna(subset=["hres_tp6_mm", "era5_tp6_mm", "Persistence"]).reset_index(drop=True)
assert (sub["init"] == sub["valid_time"] - pd.Timedelta(hours=6)).all()
sub["HRES (6 h mean)"] = sub["hres_tp6_mm"] / 6.0
sub["Perfect 6 h mean (ceiling)"] = sub["era5_tp6_mm"] / 6.0
print(f"Aligned samples (valid 06/18 UTC): {len(sub)} "
      f"({sub['valid_time'].min()} -> {sub['valid_time'].max()}); "
      f"of all test samples at 06/18 UTC: {int(test['valid_time'].dt.hour.isin([6, 18]).sum())}")
# sanity: the hour ending at T is part of the 6 h window ending at T
viol = (sub["y_true"] - sub["era5_tp6_mm"]).max()
print(f"max (hourly truth - ERA5 6 h total) = {viol:.2e} mm (must be <= 3e-4; storage precision)")
assert viol <= 3e-4, "hourly truth exceeds the 6 h total: window direction or alignment is wrong"

# ---------- 5. Metrics ----------
y = sub["y_true"].values
CLIM = "Climatology (month x hour)"
ORDER = (list(MODELS) + ["Persistence", CLIM, "AR(1)", "HRES (6 h mean)", "Perfect 6 h mean (ceiling)"])


def scores(p, thr):
    o, f = y >= thr, p >= thr
    hits, fa, miss = int((o & f).sum()), int((~o & f).sum()), int((o & ~f).sum())
    pod = hits / (hits + miss) if hits + miss else np.nan
    far = fa / (hits + fa) if hits + fa else np.nan
    csi = hits / (hits + fa + miss) if hits + fa + miss else np.nan
    return hits, fa, miss, pod, far, csi


rmse_clim = np.sqrt(np.mean((sub[CLIM].values - y) ** 2))
out = []
for lab in ORDER:
    p = sub[lab].values
    rmse = float(np.sqrt(np.mean((p - y) ** 2)))
    r = {"forecast": lab, "n": len(y), "RMSE": rmse, "MAE": float(np.mean(np.abs(p - y))),
         "R2": float(1 - np.sum((p - y) ** 2) / np.sum((y - y.mean()) ** 2)),
         "bias": float(np.mean(p - y)), "corr": float(np.corrcoef(p, y)[0, 1]) if p.std() > 0 else np.nan,
         "skill_vs_clim": 1 - rmse / rmse_clim, "pred_max": float(p.max())}
    for tag, thr in (("wet01", WET), ("Q95", Q95)):
        hi, fa, mi, pod, far, csi = scores(p, thr)
        r.update({f"{tag}_obs_events": int((y >= thr).sum()), f"{tag}_fcst_events": hi + fa,
                  f"{tag}_POD": pod, f"{tag}_FAR": far, f"{tag}_CSI": csi})
    out.append(r)
table = pd.DataFrame(out)
table.to_csv(f"{MET}/q08_hres_comparison.csv", index=False)
pd.set_option("display.width", 200)
print("\n===== Point and event scores, valid 06/18 UTC (fixed rule: forecast >= threshold) =====")
print(table[["forecast", "n", "RMSE", "MAE", "R2", "bias", "corr", "skill_vs_clim", "pred_max"]]
      .to_string(index=False, float_format=lambda v: f"{v:.4f}"))
print(table[["forecast", "wet01_POD", "wet01_FAR", "wet01_CSI", "Q95_obs_events", "Q95_fcst_events",
             "Q95_POD", "Q95_FAR", "Q95_CSI"]].to_string(index=False, float_format=lambda v: f"{v:.3f}"))

# ---------- 6. Paired moving-block bootstrap of dRMSE (forecast minus HRES) ----------
rng = np.random.default_rng(SEED)
n = len(y)
starts = rng.integers(0, n - BLOCK + 1, size=(N_BOOT, int(np.ceil(n / BLOCK))))
idx = (starts[:, :, None] + np.arange(BLOCK)).reshape(N_BOOT, -1)[:, :n]
err2 = {lab: (sub[lab].values - y) ** 2 for lab in ORDER}
rows = []
for ref in ("HRES (6 h mean)", "Perfect 6 h mean (ceiling)"):
    for lab in ORDER:
        if lab == ref:
            continue
        d_obs = np.sqrt(err2[lab].mean()) - np.sqrt(err2[ref].mean())
        d_bs = np.sqrt(err2[lab][idx].mean(1)) - np.sqrt(err2[ref][idx].mean(1))
        lo, hi = np.percentile(d_bs, [2.5, 97.5])
        rows.append({"forecast": lab, "reference": ref, "dRMSE": d_obs, "ci_low": lo, "ci_high": hi,
                     "significant": bool(lo > 0 or hi < 0)})
boot = pd.DataFrame(rows)
boot.to_csv(f"{MET}/q08_hres_bootstrap.csv", index=False)
print(f"\n===== dRMSE = RMSE(forecast) - RMSE(reference), block {BLOCK}, {N_BOOT} reps =====")
print(boot.to_string(index=False, float_format=lambda v: f"{v:+.4f}"))

sub[["valid_time", "init", "y_true", "hres_tp6_mm", "era5_tp6_mm"] + ORDER].to_csv(
    f"{MET}/q08_hres_aligned_samples.csv", index=False)
print("\nSaved: q08_hres_comparison.csv, q08_hres_bootstrap.csv, q08_hres_aligned_samples.csv")
print("===== q08 HRES COMPARISON COMPLETE =====")
