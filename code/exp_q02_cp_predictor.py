# ============================================================
# exp_q02_cp_predictor.py — issue 02 (R4 M3) small CPU experiment
#
# Question: does adding convective precipitation cp(t) = tp(t) - lsp(t)
# as an extra predictor change XGBoost skill at the 6 h lead?
#
# Everything else is IDENTICAL to the main pipeline (Step 2D + Step 3):
#   - same data file, chronological 70/15/15 split
#   - scalers fitted on TRAIN only
#   - window of 6 snapshots t-5..t -> target t+1, built per split
#   - XGBoost: n_estimators=100, lr=0.05, max_depth=6, subsample=0.8,
#     colsample_bytree=0.8 (as in step3_train_xgboost.py)
#   - 5 seeds: 42, 123, 7, 2024, 99
# Variants:  A = base 7 features,  B = base 7 + cp(t)  (8 features)
#
# CPU only, a couple of minutes. Run from the folder containing data/:
#     python code/exp_q02_cp_predictor.py
# Output: results/ablation/cp_predictor_xgboost_raw.csv / _summary.csv
# ============================================================
import os
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

SEEDS = [42, 123, 7, 2024, 99]
WINDOW = 6
BASE = ['mxtpr', 'mntpr', 'lsp', 'tcc', 'v10', 'sp', 'd2m']

CANDS = ["data/dublin_regional_reduced.csv", "../data/dublin_regional_reduced.csv",
         "data/dublin_regional_2004_2021.csv", "../data/dublin_regional_2004_2021.csv"]
path = next(p for p in CANDS if os.path.exists(p))
df = pd.read_csv(path, parse_dates=['valid_time']).sort_values('valid_time').reset_index(drop=True)
print("Source:", path, df.shape)
df['tp_mm'] = df['tp'] * 1000.0 if 'tp' in df.columns else df['tp_mm']
df['cp_mm'] = (df['tp_mm'] - df['lsp'] * 1000.0).clip(lower=0.0)   # convective precip, mm

if 'sp' not in df.columns:
    print("WARNING: 'sp' not in this file -> using u10 instead (code-path test only).")
    BASE = [c if c != 'sp' else 'u10' for c in BASE]
assert len(df) == 26300 or 'sp' not in df.columns, f"unexpected rows: {len(df)}"

n = len(df)
tr_end, va_end = int(n * 0.70), int(n * 0.85)
parts = {'train': df.iloc[:tr_end].copy(), 'val': df.iloc[tr_end:va_end].copy(),
         'test': df.iloc[va_end:].copy()}
print({k: (len(v), str(v.valid_time.min()), str(v.valid_time.max())) for k, v in parts.items()})


def windows(part, feats, scaler_x, scaler_y):
    Xv = scaler_x.transform(part[feats])
    yv = scaler_y.transform(part[['tp_mm']]).ravel()
    X = np.stack([Xv[i:i + WINDOW] for i in range(len(part) - WINDOW)]).astype(np.float32)
    y = yv[WINDOW:].astype(np.float32)
    return X.reshape(len(X), -1), y


def run(feats, seed):
    sx, sy = StandardScaler().fit(parts['train'][feats]), StandardScaler().fit(parts['train'][['tp_mm']])
    Xtr, ytr = windows(parts['train'], feats, sx, sy)
    Xte, yte = windows(parts['test'], feats, sx, sy)
    m = xgb.XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=6,
                         subsample=0.8, colsample_bytree=0.8, random_state=seed)
    m.fit(Xtr, ytr)
    inv = lambda a: sy.inverse_transform(np.asarray(a).reshape(-1, 1)).ravel()
    yt, yp = inv(yte), inv(m.predict(Xte))
    return {'RMSE': float(np.sqrt(mean_squared_error(yt, yp))),
            'MAE': float(mean_absolute_error(yt, yp)), 'R2': float(r2_score(yt, yp)),
            'N_test': len(yt)}


variants = {'A_base7': BASE, 'B_base7_plus_cp': BASE + ['cp_mm']}
rows = []
for name, feats in variants.items():
    for s in SEEDS:
        r = run(feats, s)
        rows.append({'Variant': name, 'Seed': s, 'N_features': len(feats), **r})
        print(f"{name:18s} seed={s:5d} RMSE={r['RMSE']:.4f} MAE={r['MAE']:.4f} R2={r['R2']:.4f}")
raw = pd.DataFrame(rows)

# sanity: reproduce the saved main-pipeline XGBoost (seed 42) if its file is available
for p in ["results/xgboost_preds.csv", "results/predictions/xgboost_preds.csv"]:
    if os.path.exists(p):
        t = pd.read_csv(p); t = t[t.split == 'test']
        ref = float(np.sqrt(np.mean((t.y_true - t.y_pred_mean) ** 2)))
        mine = raw[(raw.Variant == 'A_base7') & (raw.Seed == 42)].RMSE.iloc[0]
        print(f"\nSANITY: saved XGBoost test RMSE = {ref:.4f}; variant A seed 42 = {mine:.4f} "
              f"(should match closely when the 7-feature set incl. sp is used)")
        break

summ = raw.groupby('Variant')[['RMSE', 'MAE', 'R2']].agg(['mean', 'std']).round(4)
print("\n===== 5-SEED SUMMARY (test) =====\n", summ.to_string())
a = raw[raw.Variant == 'A_base7'].set_index('Seed').RMSE
b = raw[raw.Variant == 'B_base7_plus_cp'].set_index('Seed').RMSE
d = (b - a)
print(f"\nPaired delta RMSE (B - A) per seed: {d.round(4).to_dict()}")
print(f"Mean delta = {d.mean():.4f}; seeds where adding cp is WORSE: {int((d > 0).sum())}/{len(d)}")

os.makedirs("results/ablation", exist_ok=True)
raw.to_csv("results/ablation/cp_predictor_xgboost_raw.csv", index=False)
summ.to_csv("results/ablation/cp_predictor_xgboost_summary.csv")
print("\nSaved to results/ablation/")
