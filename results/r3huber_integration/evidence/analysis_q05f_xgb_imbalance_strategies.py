# ============================================================
# analysis_q05f_xgb_imbalance_strategies.py -- issue 05 (R1 M1 / R1 summary: no imbalance-aware training),
# issue 15 (R3 L376: Huber instead of MSE) and issue 11 (R2 M6: precipitation-appropriate loss). CPU only.
#
# Does changing the training objective / sample weighting reduce the compression of predictions toward the mean
# and improve upper-tail detection?  XGBoost (cheap) on the ERA5 regional target, everything else as the main pipeline:
# chronological 70/15/15, scalers on TRAIN only, 6-step windows built within each split (18,404 / 3,939 / 3,939),
# 7 features, n_estimators=100, lr=0.05, max_depth=6, subsample=0.8, colsample_bytree=0.8, seeds 42,123,7,2024,99.
# NO re-tuning of any hyperparameter, and the loss parameters below are FIXED a priori (not tuned on test).
#
#   M0 MSE (reg:squarederror, standardised target)  -> must reproduce RMSE ~0.2439
#   M1 pseudo-Huber, slope 0.1 mm/h (= wet threshold)
#   M2 pseudo-Huber, slope 0.5 mm/h (~ train Q95)
#   M3 sample weights = inverse class frequency (3 classes: <0.1, 0.1..Q95, >=Q95), normalised to mean 1
#   M4 sample weights = 1/sqrt(class frequency), normalised to mean 1
#   M5 log1p target (prediction back-transformed with expm1, clipped at 0)
#   M6 Tweedie, variance power 1.5 (reg:tweedie, raw mm target >= 0, predicts the conditional mean)
# Reported on the TEST split (ERA5 regional target): RMSE/MAE/bias on all, wet>=0.1, >=Q95, >=1.0; prediction max,
# std ratio, Pearson r; number of test targets predicted >= tau (fixed cutoff = tau) and hits at Q95 and 1.0;
# AUC and validation-tuned-cutoff POD/FAR/CSI at Q95 and 1.0; paired block bootstrap (block 28, reps below, seed 42)
# of each variant minus M0 on seed-averaged predictions.
#
# Run (AutoDL):  cd /root/autodl-tmp
#   python3 code/analysis_q05f_xgb_imbalance_strategies.py 2>&1 | tee results/metrics/q05f_output.txt
# Outputs (results/ablation/): q05f_raw.csv, q05f_summary.csv, q05f_paired.csv
# Optional env: NBOOT (default 2000), DATA path as first argument.
# ============================================================
import os
import sys
import numpy as np
import pandas as pd
import xgboost as xgb
from scipy.stats import rankdata
from sklearn.preprocessing import StandardScaler

SEEDS = [42, 123, 7, 2024, 99]
WINDOW = 6
BASE = ['mxtpr', 'mntpr', 'lsp', 'tcc', 'v10', 'sp', 'd2m']
XGB_KW = dict(n_estimators=100, learning_rate=0.05, max_depth=6, subsample=0.8, colsample_bytree=0.8)
BLOCK, BSEED = 28, 42
NBOOT = int(os.environ.get("NBOOT", 2000))
CANDS = (sys.argv[1:2] or []) + ["data/dublin_regional_reduced.csv", "../data/dublin_regional_reduced.csv",
                                 "data/dublin_regional_2004_2021.csv", "../data/dublin_regional_2004_2021.csv"]
path = next(p for p in CANDS if os.path.exists(p))
df = pd.read_csv(path, parse_dates=['valid_time']).sort_values('valid_time').reset_index(drop=True)
df['tp_mm'] = df['tp'] * 1000.0 if 'tp' in df.columns else df['tp_mm']
assert len(df) == 26300 and not [c for c in BASE if c not in df.columns]
n = len(df)
a, b = int(n * .70), int(n * .85)
parts = {'train': df.iloc[:a], 'val': df.iloc[a:b], 'test': df.iloc[b:]}
sx = StandardScaler().fit(parts['train'][BASE])


def windows(p):
    p = p.reset_index(drop=True)
    Xv = sx.transform(p[BASE])
    X = np.stack([Xv[i:i + WINDOW] for i in range(len(p) - WINDOW)]).reshape(len(p) - WINDOW, -1).astype(np.float32)
    return X, p['tp_mm'].to_numpy()[WINDOW:]


Wn = {k: windows(v) for k, v in parts.items()}
Xtr, ytr = Wn['train']; Xva, yva = Wn['val']; Xte, yte = Wn['test']
assert len(Xtr) == 18404 and len(Xva) == 3939 and len(Xte) == 3939
neg = int((ytr < 0).sum())
ytr_c = np.clip(ytr, 0, None)
mu, sd = float(ytr.mean()), float(ytr.std())          # == StandardScaler on tp_mm
ys = (ytr - mu) / sd
q95 = float(np.quantile(ytr, 0.95))
print(f"Source {path}; train windows {len(Xtr)}; train Q95 {q95:.4f}; negative train targets {neg}; mean {mu:.4f} sd {sd:.4f}")
assert abs(q95 - 0.5740) < 5e-4

cls = np.where(ytr < 0.1, 0, np.where(ytr < q95, 1, 2))
freq = np.bincount(cls, minlength=3) / len(cls)
print("class shares (dry, wet<Q95, >=Q95):", freq.round(4))
w_inv = 1.0 / freq[cls]; w_inv /= w_inv.mean()
w_sqrt = 1.0 / np.sqrt(freq[cls]); w_sqrt /= w_sqrt.mean()


def fit_std(seed, extra=None, w=None):
    m = xgb.XGBRegressor(random_state=seed, **XGB_KW, **(extra or {})).fit(Xtr, ys, sample_weight=w)
    return lambda X: m.predict(X) * sd + mu


def fit_log(seed):
    m = xgb.XGBRegressor(random_state=seed, **XGB_KW).fit(Xtr, np.log1p(ytr_c))
    return lambda X: np.clip(np.expm1(m.predict(X)), 0, None)


def fit_tw(seed):
    m = xgb.XGBRegressor(random_state=seed, objective='reg:tweedie', tweedie_variance_power=1.5, **XGB_KW).fit(Xtr, ytr_c)
    return lambda X: m.predict(X)


VARIANTS = {
    'M0 MSE': lambda s: fit_std(s),
    'M1 pseudo-Huber 0.1': lambda s: fit_std(s, dict(objective='reg:pseudohubererror', huber_slope=0.1 / sd)),
    'M2 pseudo-Huber 0.5': lambda s: fit_std(s, dict(objective='reg:pseudohubererror', huber_slope=0.5 / sd)),
    'M3 weight inv-freq': lambda s: fit_std(s, None, w_inv),
    'M4 weight inv-sqrt-freq': lambda s: fit_std(s, None, w_sqrt),
    'M5 log1p target': fit_log,
    'M6 Tweedie 1.5': fit_tw,
}


def rmse(p, o): return float(np.sqrt(np.mean((p - o) ** 2)))


pv, pt, rawrows = {}, {}, []
for v, fn in VARIANTS.items():
    PV, PT = [], []
    for s in SEEDS:
        f = fn(s)
        pa, pb_ = f(Xva), f(Xte)
        PV.append(pa); PT.append(pb_)
        rawrows.append({'Variant': v, 'Seed': s, 'RMSE': rmse(pb_, yte), 'MAE': float(np.mean(np.abs(pb_ - yte))),
                        'Bias': float(np.mean(pb_ - yte)), 'Pred_max': float(pb_.max())})
    pv[v], pt[v] = np.mean(PV, 0), np.mean(PT, 0)
    r = [x['RMSE'] for x in rawrows if x['Variant'] == v]
    print(f"{v:26s} test RMSE over seeds {np.mean(r):.4f} +- {np.std(r, ddof=1):.4f}")
raw = pd.DataFrame(rawrows)
print("SANITY: M0 should be ~0.2439 (main pipeline 0.2437-0.2439).")

# ---- metrics on seed-averaged predictions ----
TH = {'Q95': q95, '1.0': 1.0}
masks = {'all': np.ones(len(yte), bool), 'wet>=0.1': yte >= 0.1, '>=Q95': yte >= q95, '>=1.0': yte >= 1.0}


def auc(p, pos):
    r = rankdata(p); n1 = pos.sum(); n0 = len(p) - n1
    return float((r[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def tune(pvv, posv):
    cands = np.unique(np.quantile(pvv, np.linspace(0.5, 0.999, 300)))
    best, bc = -1, cands[0]
    for c in cands:
        pb = pvv >= c
        h, fa, mi = (pb & posv).sum(), (pb & ~posv).sum(), (~pb & posv).sum()
        csi = h / (h + fa + mi) if (h + fa + mi) else 0
        if csi > best: best, bc = csi, c
    return bc


rows, cut = [], {}
for v in VARIANTS:
    p = pt[v]
    r = {'Variant': v, 'Pred_max': float(p.max()), 'Std_ratio': float(p.std() / yte.std()),
         'Pearson_r': float(np.corrcoef(p, yte)[0, 1])}
    for s_, mk in masks.items():
        r[f'RMSE_{s_}'] = rmse(p[mk], yte[mk]); r[f'Bias_{s_}'] = float(np.mean(p[mk] - yte[mk]))
    r['MAE_all'] = float(np.mean(np.abs(p - yte)))
    for tn, tv in TH.items():
        pos, posv = yte >= tv, yva >= tv
        r[f'N_pred_ge_tau_{tn}'] = int((p >= tv).sum()); r[f'Hits_fixed_{tn}'] = int(((p >= tv) & pos).sum())
        r[f'AUC_{tn}'] = auc(p, pos)
        c = tune(pv[v], posv); cut[(v, tn)] = c
        pb = p >= c
        h, fa, mi = int((pb & pos).sum()), int((pb & ~pos).sum()), int((~pb & pos).sum())
        r.update({f'Cut_{tn}': float(c), f'Fcst_{tn}': int(pb.sum()), f'POD_{tn}': h / (h + mi),
                  f'FAR_{tn}': fa / (h + fa) if (h + fa) else np.nan, f'CSI_{tn}': h / (h + fa + mi)})
    rows.append(r)
S = pd.DataFrame(rows)

# ---- paired block bootstrap vs M0 ----
N = len(yte)
rng = np.random.default_rng(BSEED)
st = rng.integers(0, N, size=(NBOOT, int(np.ceil(N / BLOCK))))
IDX = ((st[:, :, None] + np.arange(BLOCK)[None, None, :]) % N).reshape(NBOOT, -1)[:, :N]


def b_rmse(p, mk):
    m = mk.astype(float)
    return np.sqrt(((yte - p) ** 2 * m)[IDX].sum(1) / np.maximum(m[IDX].sum(1), 1))


def b_auc(p, pos):
    r = rankdata(p[IDX], axis=1); pb = pos[IDX]; n1 = pb.sum(1); n0 = N - n1
    return ((r * pb).sum(1) - n1 * (n1 + 1) / 2) / (n1 * n0)


def b_csi(p, pos, c):
    X = (p >= c)[IDX]; Y = pos[IDX]
    h, fa, mi = (X & Y).sum(1), (X & ~Y).sum(1), (~X & Y).sum(1)
    return h / np.maximum(h + fa + mi, 1)


def stats_for(v):
    d = {}
    for s_, mk in masks.items():
        if s_ in ('all', 'wet>=0.1', '>=Q95'):
            d[f'RMSE_{s_}'] = (rmse(pt[v][mk], yte[mk]), b_rmse(pt[v], mk))
    for tn, tv in TH.items():
        pos = yte >= tv
        d[f'AUC_{tn}'] = (auc(pt[v], pos), b_auc(pt[v], pos))
        c = cut[(v, tn)]
        pb = pt[v] >= c
        h, fa, mi = (pb & pos).sum(), (pb & ~pos).sum(), (~pb & pos).sum()
        d[f'CSI_{tn}'] = (h / (h + fa + mi), b_csi(pt[v], pos, c))
    return d


base = stats_for('M0 MSE')
prow = []
for v in list(VARIANTS)[1:]:
    cur = stats_for(v)
    for k in base:
        d = cur[k][1] - base[k][1]
        prow.append({'Variant': v, 'Metric': k, 'M0': base[k][0], 'Variant_value': cur[k][0],
                     'Diff_variant_minus_M0': cur[k][0] - base[k][0],
                     'CI_low': float(np.percentile(d, 2.5)), 'CI_high': float(np.percentile(d, 97.5))})
P = pd.DataFrame(prow)

pd.set_option('display.width', 260); pd.set_option('display.max_columns', 60)
print("\n===== summary (test, seed-averaged predictions) =====")
print(S[['Variant', 'Pred_max', 'Std_ratio', 'Pearson_r', 'RMSE_all', 'MAE_all', 'Bias_all', 'RMSE_wet>=0.1', 'Bias_wet>=0.1',
         'RMSE_>=Q95', 'Bias_>=Q95', 'RMSE_>=1.0', 'Bias_>=1.0']].round(4).to_string(index=False))
print("\n===== events: fixed cutoff = tau, AUC, validation-tuned cutoff =====")
print(S[['Variant', 'N_pred_ge_tau_Q95', 'Hits_fixed_Q95', 'AUC_Q95', 'POD_Q95', 'FAR_Q95', 'CSI_Q95',
         'N_pred_ge_tau_1.0', 'Hits_fixed_1.0', 'AUC_1.0', 'POD_1.0', 'FAR_1.0', 'CSI_1.0']].round(3).to_string(index=False))
print(f"\n===== paired: variant minus M0 (block {BLOCK}, {NBOOT} reps, seed {BSEED}) =====")
print(P.round(4).to_string(index=False))
os.makedirs('results/ablation', exist_ok=True)
raw.to_csv('results/ablation/q05f_raw.csv', index=False)
S.to_csv('results/ablation/q05f_summary.csv', index=False)
P.to_csv('results/ablation/q05f_paired.csv', index=False)
print("\nSaved results/ablation/q05f_*.csv")
