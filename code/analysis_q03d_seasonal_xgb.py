# ============================================================
# analysis_q03d_seasonal_xgb.py  --  issue 03 (R3 L469-471) small CPU experiment
#
# Reviewer R3: "modeling and analyses need to be carried out by separating seasons".
# Question: does season-specific XGBoost, or a global XGBoost with calendar
# (month / hour sin-cos) inputs, beat the global 7-feature XGBoost at the 6 h lead?
#
# Everything else is IDENTICAL to the main pipeline (Step 2D + Step 3) and to
# exp_q02_cp_predictor.py:
#   - same data file, chronological 70/15/15 split, scalers fitted on TRAIN only
#   - window of 6 snapshots t-5..t -> target at the next step, built per split
#   - XGBoost n_estimators=100, lr=0.05, max_depth=6, subsample=0.8,
#     colsample_bytree=0.8 (same hyper-parameters for every variant, NO re-tuning)
#   - 5 seeds: 42, 123, 7, 2024, 99
#
# Variants
#   G  global XGBoost, 42 inputs (6 x 7 features)                  [= main XGBoost]
#   S  four season-specific XGBoosts (DJF/MAM/JJA/SON); each is trained only on
#      training windows whose TARGET time falls in that season, and predicts only
#      test windows whose target time falls in that season
#   F  global XGBoost + calendar inputs of the target time:
#      sin/cos(month), sin/cos(hour of day)  (46 inputs)
#
# Season = season of the target time stamp (month of the row that is predicted).
# Subsets reported: all, DJF, MAM, JJA, SON, wet (>=0.1 mm/h), upper tail (>=Q95,
# Q95 derived from the TRAIN targets only).
#
# CPU only, a few minutes.  Run from the folder that contains data/ :
#     mkdir -p results/metrics
#     python3 code/analysis_q03d_seasonal_xgb.py 2>&1 | tee results/metrics/q03d_seasonal_xgb_output.txt
# Optional first argument: path of the regional csv.
# Outputs (results/ablation/):
#     q03d_seasonal_xgb_raw.csv        per seed x variant x subset
#     q03d_seasonal_xgb_summary.csv    mean/std over seeds
#     q03d_seasonal_xgb_paired.csv     S-G and F-G: per-seed mean/std/#worse + block-bootstrap CI
#     q03d_seasonal_xgb_test_preds.csv seed-averaged test predictions (G, S, F)
# Nothing existing is read for writing or overwritten.
# ============================================================
import os
import sys
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.preprocessing import StandardScaler

SEEDS = [42, 123, 7, 2024, 99]
WINDOW = 6
BASE = ['mxtpr', 'mntpr', 'lsp', 'tcc', 'v10', 'sp', 'd2m']
SEASONS = ['DJF', 'MAM', 'JJA', 'SON']
WET_MM = 0.1
BOOT_REPS, BOOT_BLOCK, BOOT_SEED = 2000, 28, 42     # same settings as the other bootstraps
XGB_KW = dict(n_estimators=100, learning_rate=0.05, max_depth=6,
              subsample=0.8, colsample_bytree=0.8)

CANDS = (sys.argv[1:2] or []) + [
    "data/dublin_regional_reduced.csv", "../data/dublin_regional_reduced.csv",
    "data/dublin_regional_2004_2021.csv", "../data/dublin_regional_2004_2021.csv"]
path = next(p for p in CANDS if os.path.exists(p))
df = pd.read_csv(path, parse_dates=['valid_time']).sort_values('valid_time').reset_index(drop=True)
print("Source:", path, df.shape)
df['tp_mm'] = df['tp'] * 1000.0 if 'tp' in df.columns else df['tp_mm']
assert len(df) == 26300, f"unexpected rows: {len(df)}"
missing = [c for c in BASE if c not in df.columns]
assert not missing, f"missing feature columns: {missing}"

n = len(df)
tr_end, va_end = int(n * 0.70), int(n * 0.85)
parts = {'train': df.iloc[:tr_end].copy(), 'test': df.iloc[va_end:].copy()}
print({k: (len(v), str(v.valid_time.min()), str(v.valid_time.max())) for k, v in parts.items()})


def season_of(month):
    return np.select([np.isin(month, [12, 1, 2]), np.isin(month, [3, 4, 5]),
                      np.isin(month, [6, 7, 8])], ['DJF', 'MAM', 'JJA'], default='SON')


def build(part, sx, sy):
    """Windows per split, exactly as in the main pipeline; plus target-time info."""
    Xv = sx.transform(part[BASE])
    yv = sy.transform(part[['tp_mm']]).ravel()
    X = np.stack([Xv[i:i + WINDOW] for i in range(len(part) - WINDOW)]).astype(np.float32)
    X = X.reshape(len(X), -1)
    y = yv[WINDOW:].astype(np.float32)
    tt = pd.to_datetime(part['valid_time'].values[WINDOW:])
    mon, hr = tt.month.values, tt.hour.values
    cal = np.column_stack([np.sin(2 * np.pi * (mon - 1) / 12), np.cos(2 * np.pi * (mon - 1) / 12),
                           np.sin(2 * np.pi * hr / 24), np.cos(2 * np.pi * hr / 24)]).astype(np.float32)
    return X, y, cal, season_of(mon), mon, hr, tt


sx = StandardScaler().fit(parts['train'][BASE])          # train only
sy = StandardScaler().fit(parts['train'][['tp_mm']])     # train only
inv = lambda a: sy.inverse_transform(np.asarray(a).reshape(-1, 1)).ravel()

Xtr, ytr, ctr, str_, mtr, htr, ttr = build(parts['train'], sx, sy)
Xte, yte, cte, ste, mte, hte, tte = build(parts['test'], sx, sy)
ytr_mm, yte_mm = inv(ytr), inv(yte)
print(f"train windows {len(Xtr)}, test windows {len(Xte)}")
assert len(Xtr) == 18404 and len(Xte) == 3939, "window counts differ from the main pipeline"

Q95 = float(np.quantile(ytr_mm, 0.95))
print(f"Train-derived Q95 = {Q95:.4f} mm/h (manuscript: 0.5740)")
if abs(Q95 - 0.5740) > 0.001:
    print("WARNING: Q95 differs from the manuscript value; check before using the tail rows.")

# month x hour climatology from TRAIN targets (reference for RMSE skill)
clim = pd.DataFrame({'m': mtr, 'h': htr, 'y': ytr_mm}).groupby(['m', 'h']).y.mean()
clim_te = np.array([clim.loc[(m, h)] for m, h in zip(mte, hte)])

masks = {'all': np.ones(len(yte_mm), bool)}
for s in SEASONS:
    masks[s] = ste == s
masks['wet>=0.1'] = yte_mm >= WET_MM
masks['tail>=Q95'] = yte_mm >= Q95
print("\nTest subset sizes:", {k: int(v.sum()) for k, v in masks.items()})
print("Train windows per season:", {s: int((str_ == s).sum()) for s in SEASONS})


def fit_predict(Xa, ya, Xb, seed):
    m = xgb.XGBRegressor(random_state=seed, **XGB_KW)
    m.fit(Xa, ya)
    return m.predict(Xb)


def pred_G(seed):
    return inv(fit_predict(Xtr, ytr, Xte, seed))


def pred_F(seed):
    return inv(fit_predict(np.hstack([Xtr, ctr]), ytr, np.hstack([Xte, cte]), seed))


def pred_S(seed):
    out = np.empty(len(Xte), dtype=np.float64)
    for s in SEASONS:
        a, b = str_ == s, ste == s
        out[b] = inv(fit_predict(Xtr[a], ytr[a], Xte[b], seed))
    return out


def metrics(yt, yp, ref):
    e = yt - yp
    rmse = float(np.sqrt(np.mean(e ** 2)))
    mae = float(np.mean(np.abs(e)))
    ss_res, ss_tot = float(np.sum(e ** 2)), float(np.sum((yt - yt.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
    rmse_ref = float(np.sqrt(np.mean((yt - ref) ** 2)))
    return rmse, mae, r2, 1 - rmse / rmse_ref


preds = {'G': {}, 'S': {}, 'F': {}}
rows = []
for seed in SEEDS:
    for v, fn in (('G', pred_G), ('S', pred_S), ('F', pred_F)):
        yp = fn(seed)
        preds[v][seed] = yp
        for sub, mk in masks.items():
            rmse, mae, r2, skill = metrics(yte_mm[mk], yp[mk], clim_te[mk])
            rows.append({'Variant': v, 'Seed': seed, 'Subset': sub, 'N': int(mk.sum()),
                         'RMSE': rmse, 'MAE': mae, 'R2': r2, 'Skill_vs_monthhour_clim': skill})
        print(f"seed={seed:5d} {v}: RMSE(all)={rows[-len(masks)]['RMSE']:.4f}")
raw = pd.DataFrame(rows)

# sanity: reproduce the saved main-pipeline XGBoost (seed 42)
for p in ["results/xgboost_preds.csv", "results/predictions/xgboost_preds.csv"]:
    if os.path.exists(p):
        t = pd.read_csv(p)
        t = t[t.split == 'test']
        ref = float(np.sqrt(np.mean((t.y_true - t.y_pred_mean) ** 2)))
        mine = raw[(raw.Variant == 'G') & (raw.Seed == 42) & (raw.Subset == 'all')].RMSE.iloc[0]
        print(f"\nSANITY: saved XGBoost test RMSE = {ref:.4f}; variant G seed 42 = {mine:.4f} (should match)")
        break
print("Climatology (month x hour) overall test RMSE:",
      round(float(np.sqrt(np.mean((yte_mm - clim_te) ** 2))), 4), "(07 reported 0.2731; small difference possible if defined differently)")

# ---------------- summary over seeds ----------------
summ = (raw.groupby(['Variant', 'Subset'])[['RMSE', 'MAE', 'R2', 'Skill_vs_monthhour_clim']]
        .agg(['mean', 'std']).round(4))
order = {s: i for i, s in enumerate(masks)}
summ = summ.reset_index()
summ.columns = ['_'.join([c for c in col if c]) for col in summ.columns.values]
summ = summ.sort_values(['Variant', 'Subset'],
                        key=lambda c: c.map(order) if c.name == 'Subset' else c)
print("\n===== 5-SEED SUMMARY (test, mm/h) =====")
print(summ.to_string(index=False))

# ---------------- paired differences ----------------
mean_pred = {v: np.mean([preds[v][s] for s in SEEDS], axis=0) for v in preds}   # seed-averaged
sqerr = {v: (yte_mm - mean_pred[v]) ** 2 for v in mean_pred}

rng = np.random.default_rng(BOOT_SEED)
N = len(yte_mm)
nblk = int(np.ceil(N / BOOT_BLOCK))
starts = rng.integers(0, N, size=(BOOT_REPS, nblk))
idx = ((starts[:, :, None] + np.arange(BOOT_BLOCK)[None, None, :]) % N).reshape(BOOT_REPS, -1)[:, :N]


def boot_rmse(v, mk):
    e, m = sqerr[v], mk.astype(float)
    out = np.empty(BOOT_REPS)
    for a in range(0, BOOT_REPS, 250):
        ii = idx[a:a + 250]
        num, den = (e[ii] * m[ii]).sum(1), m[ii].sum(1)
        out[a:a + 250] = np.sqrt(np.where(den > 0, num / np.maximum(den, 1), np.nan))
    return out


bootG = {sub: boot_rmse('G', mk) for sub, mk in masks.items()}
prow = []
for v, name in (('S', 'S_minus_G'), ('F', 'F_minus_G')):
    for sub, mk in masks.items():
        a = raw[(raw.Variant == v) & (raw.Subset == sub)].set_index('Seed').RMSE
        b = raw[(raw.Variant == 'G') & (raw.Subset == sub)].set_index('Seed').RMSE
        d = a - b
        bd = boot_rmse(v, mk) - bootG[sub]
        pt = float(np.sqrt(sqerr[v][mk].mean()) - np.sqrt(sqerr['G'][mk].mean()))
        prow.append({'Comparison': name, 'Subset': sub, 'N': int(mk.sum()),
                     'seed_mean_delta_RMSE': round(float(d.mean()), 4),
                     'seed_std_delta': round(float(d.std(ddof=1)), 4),
                     'n_seeds_worse': int((d > 0).sum()), 'n_seeds': len(d),
                     'seedavg_pred_delta_RMSE': round(pt, 4),
                     'boot_CI_low': round(float(np.nanpercentile(bd, 2.5)), 4),
                     'boot_CI_high': round(float(np.nanpercentile(bd, 97.5)), 4)})
paired = pd.DataFrame(prow)
print("\n===== PAIRED DIFFERENCES vs GLOBAL XGBOOST (negative = variant better) =====")
print(paired.to_string(index=False))
print(f"\nBootstrap: circular block, block={BOOT_BLOCK}, reps={BOOT_REPS}, seed={BOOT_SEED}; "
      "applied to seed-averaged predictions; subsets use the resampled windows that fall in them.")

# ---------------- save ----------------
os.makedirs("results/ablation", exist_ok=True)
raw.to_csv("results/ablation/q03d_seasonal_xgb_raw.csv", index=False)
summ.to_csv("results/ablation/q03d_seasonal_xgb_summary.csv", index=False)
paired.to_csv("results/ablation/q03d_seasonal_xgb_paired.csv", index=False)
pd.DataFrame({'valid_time': tte, 'season': ste, 'y_true': yte_mm,
              'y_G': mean_pred['G'], 'y_S': mean_pred['S'], 'y_F': mean_pred['F']}
             ).to_csv("results/ablation/q03d_seasonal_xgb_test_preds.csv", index=False)
print("\nSaved to results/ablation/ (q03d_seasonal_xgb_*.csv)")
