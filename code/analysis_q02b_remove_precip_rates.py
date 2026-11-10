# ============================================================
# analysis_q02b_remove_precip_rates.py  --  issue 02 (R4 m34, l.936-938), small CPU experiment
#
# Reviewer: "if you removed mxtpr and mntpr, lsp would be a leading predictor in all
# considered prediction attribution methods, right?"
# The manuscript removed only mxtpr (BU-LSTM-Attention).  Here, with XGBoost (cheap), we remove
#   V0 all 7 | V1 no mxtpr | V2 no mxtpr, mntpr | V3 no lsp | V4 no mxtpr, mntpr, lsp
# and report (a) test RMSE (5 seeds, paired vs V0) and (b) the rank of lsp under four
# relevance measures:  Spearman |rho| (feature at t vs target), XGBoost total gain,
# permutation importance (VALIDATION set, never the test set), and SHAP mean |value| (test,
# only if the shap package is installed).  Importances are summed over the 6 time steps.
#
# Everything else is identical to the main pipeline and exp_q02_cp_predictor.py:
# chronological 70/15/15, scalers on TRAIN only, 6-step windows, XGBoost n_estimators=100,
# lr=0.05, max_depth=6, subsample=0.8, colsample_bytree=0.8, seeds 42,123,7,2024,99, no re-tuning.
#
# Run from the folder containing data/ :
#     mkdir -p results/metrics
#     python3 code/analysis_q02b_remove_precip_rates.py 2>&1 | tee results/metrics/q02b_remove_precip_rates_output.txt
# Outputs (results/ablation/): q02b_rmse_raw.csv, q02b_rmse_paired.csv, q02b_importance.csv,
#                              q02b_lsp_rank.csv
# Optional first argument: path of the regional csv.
# ============================================================
import os
import sys
import numpy as np
import pandas as pd
import xgboost as xgb
from scipy.stats import spearmanr
from sklearn.preprocessing import StandardScaler

try:
    import shap
    HAVE_SHAP = True
except Exception:
    HAVE_SHAP = False
    print("NOTE: shap not installed -> SHAP column skipped (pip install shap to include it).")

SEEDS = [42, 123, 7, 2024, 99]
WINDOW = 6
BASE = ['mxtpr', 'mntpr', 'lsp', 'tcc', 'v10', 'sp', 'd2m']
VARIANTS = {
    'V0_all7': BASE,
    'V1_no_mxtpr': [f for f in BASE if f != 'mxtpr'],
    'V2_no_mxtpr_mntpr': [f for f in BASE if f not in ('mxtpr', 'mntpr')],
    'V3_no_lsp': [f for f in BASE if f != 'lsp'],
    'V4_no_mxtpr_mntpr_lsp': [f for f in BASE if f not in ('mxtpr', 'mntpr', 'lsp')],
}
XGB_KW = dict(n_estimators=100, learning_rate=0.05, max_depth=6, subsample=0.8, colsample_bytree=0.8)
N_PERM = 3
BOOT_REPS, BOOT_BLOCK, BOOT_SEED = 2000, 28, 42

CANDS = (sys.argv[1:2] or []) + [
    "data/dublin_regional_reduced.csv", "../data/dublin_regional_reduced.csv",
    "data/dublin_regional_2004_2021.csv", "../data/dublin_regional_2004_2021.csv"]
path = next(p for p in CANDS if os.path.exists(p))
df = pd.read_csv(path, parse_dates=['valid_time']).sort_values('valid_time').reset_index(drop=True)
print("Source:", path, df.shape)
df['tp_mm'] = df['tp'] * 1000.0 if 'tp' in df.columns else df['tp_mm']
assert len(df) == 26300, f"unexpected rows: {len(df)}"
assert not [c for c in BASE if c not in df.columns], "missing feature columns"

n = len(df)
tr_end, va_end = int(n * 0.70), int(n * 0.85)
parts = {'train': df.iloc[:tr_end], 'val': df.iloc[tr_end:va_end], 'test': df.iloc[va_end:]}
sx = StandardScaler().fit(parts['train'][BASE])           # per-feature, so dropping a feature
sy = StandardScaler().fit(parts['train'][['tp_mm']])      # does not change the others' scaling
inv = lambda a: sy.inverse_transform(np.asarray(a).reshape(-1, 1)).ravel()


def windows(part):
    Xv = sx.transform(part[BASE])
    X = np.stack([Xv[i:i + WINDOW] for i in range(len(part) - WINDOW)]).astype(np.float32)  # (N,6,7)
    y = sy.transform(part[['tp_mm']]).ravel()[WINDOW:].astype(np.float32)
    return X, y


W = {k: windows(v) for k, v in parts.items()}
assert len(W['train'][0]) == 18404 and len(W['test'][0]) == 3939, "window counts differ from main pipeline"
yte_mm, yva_mm = inv(W['test'][1]), inv(W['val'][1])


def flat(X, feats):
    idx = [BASE.index(f) for f in feats]
    return X[:, :, idx].reshape(len(X), -1)          # layout: step-major -> column j = step*F + feat


def rmse(a, b):
    return float(np.sqrt(np.mean((a - b) ** 2)))


# ---- Spearman |rho| of the feature at t (last step) with the target (6 h ahead), test split ----
sp_rho = {f: abs(spearmanr(W['test'][0][:, -1, BASE.index(f)], yte_mm).correlation) for f in BASE}
print("\nSpearman |rho| (feature at t vs target, test):", {k: round(v, 3) for k, v in sp_rho.items()})


def rank_of(score):               # score: dict feature -> value ; rank 1 = largest
    s = pd.Series(score).rank(ascending=False, method='min')
    return s.to_dict()


rmse_rows, imp_rows, pred_store = [], [], {v: {} for v in VARIANTS}
rng_perm = np.random.default_rng(0)
for vname, feats in VARIANTS.items():
    F = len(feats)
    Xtr, Xva, Xte = (flat(W[k][0], feats) for k in ('train', 'val', 'test'))
    for seed in SEEDS:
        m = xgb.XGBRegressor(random_state=seed, **XGB_KW).fit(Xtr, W['train'][1])
        yp = inv(m.predict(Xte))
        pred_store[vname][seed] = yp
        rmse_rows.append({'Variant': vname, 'Seed': seed, 'N_features': F, 'RMSE': rmse(yte_mm, yp),
                          'MAE': float(np.mean(np.abs(yte_mm - yp)))})
        # --- gain (total_gain summed over time steps) ---
        tg = m.get_booster().get_score(importance_type='total_gain')
        gain = {f: 0.0 for f in feats}
        for k, v in tg.items():
            gain[feats[int(k[1:]) % F]] += v
        # --- permutation importance on VALIDATION (a feature's 6 columns permuted jointly) ---
        base_rmse = rmse(yva_mm, inv(m.predict(Xva)))
        perm = {}
        for fi, f in enumerate(feats):
            cols = [s * F + fi for s in range(WINDOW)]
            deltas = []
            for _ in range(N_PERM):
                Xp = Xva.copy()
                Xp[:, cols] = Xp[rng_perm.permutation(len(Xp))][:, cols]
                deltas.append(rmse(yva_mm, inv(m.predict(Xp))) - base_rmse)
            perm[f] = float(np.mean(deltas))
        # --- SHAP on test ---
        shp = None
        if HAVE_SHAP:
            sv = np.abs(shap.TreeExplainer(m).shap_values(Xte)).mean(0)
            shp = {f: float(sum(sv[s * F + fi] for s in range(WINDOW))) for fi, f in enumerate(feats)}
        for method, sc in (('Spearman', {f: sp_rho[f] for f in feats}), ('Gain', gain),
                           ('Permutation(val)', perm), ('SHAP', shp)):
            if sc is None:
                continue
            tot = sum(max(v, 0) for v in sc.values())
            rk = rank_of(sc)
            for f in feats:
                imp_rows.append({'Variant': vname, 'Seed': seed, 'Method': method, 'Feature': f,
                                 'Importance': sc[f], 'Share_%': 100 * max(sc[f], 0) / tot if tot > 0 else np.nan,
                                 'Rank': int(rk[f])})
    print(f"{vname:24s} ({F} feats) mean test RMSE over seeds = "
          f"{np.mean([r['RMSE'] for r in rmse_rows if r['Variant'] == vname]):.4f}")

raw = pd.DataFrame(rmse_rows)
imp = pd.DataFrame(imp_rows)

# ---------------- paired RMSE vs V0 (+ block bootstrap on seed-averaged predictions) ----------------
N = len(yte_mm)
rng = np.random.default_rng(BOOT_SEED)
nblk = int(np.ceil(N / BOOT_BLOCK))
starts = rng.integers(0, N, size=(BOOT_REPS, nblk))
idx = ((starts[:, :, None] + np.arange(BOOT_BLOCK)[None, None, :]) % N).reshape(BOOT_REPS, -1)[:, :N]
mean_pred = {v: np.mean([pred_store[v][s] for s in SEEDS], axis=0) for v in VARIANTS}
sq = {v: (yte_mm - mean_pred[v]) ** 2 for v in VARIANTS}
boot = {v: np.sqrt(sq[v][idx].mean(1)) for v in VARIANTS}
a0 = raw[raw.Variant == 'V0_all7'].set_index('Seed').RMSE
prow = []
for v in list(VARIANTS)[1:]:
    d = raw[raw.Variant == v].set_index('Seed').RMSE - a0
    bd = boot[v] - boot['V0_all7']
    prow.append({'Variant_minus_V0': v, 'mean_RMSE_V0': round(float(a0.mean()), 4),
                 'mean_RMSE_variant': round(float(raw[raw.Variant == v].RMSE.mean()), 4),
                 'seed_mean_delta': round(float(d.mean()), 4), 'seed_std_delta': round(float(d.std(ddof=1)), 4),
                 'n_seeds_worse': int((d > 0).sum()), 'n_seeds': len(d),
                 'boot_CI_low': round(float(np.percentile(bd, 2.5)), 4),
                 'boot_CI_high': round(float(np.percentile(bd, 97.5)), 4)})
paired = pd.DataFrame(prow)
print("\n===== TEST RMSE: variant minus V0 (negative = variant better; XGBoost, 5 seeds) =====")
print(paired.to_string(index=False))
print(f"(bootstrap: circular block {BOOT_BLOCK}, {BOOT_REPS} reps, seed {BOOT_SEED}, seed-averaged predictions)")

# ---------------- rank of lsp ----------------
L = imp[imp.Feature == 'lsp']
lr = (L.groupby(['Variant', 'Method'])
      .agg(median_rank=('Rank', 'median'), seeds_rank1=('Rank', lambda r: int((r == 1).sum())),
           n_seeds=('Seed', 'nunique'), mean_share_pct=('Share_%', 'mean')).round(2).reset_index())
nf = {v: len(f) for v, f in VARIANTS.items()}
lr['n_features_in_variant'] = lr.Variant.map(nf)
print("\n===== RANK OF lsp (1 = most important) PER VARIANT AND METHOD =====")
print(lr.to_string(index=False))
print("\nTop-ranked feature per variant and method (modal over seeds):")
top = (imp[imp.Rank == 1].groupby(['Variant', 'Method']).Feature
       .agg(lambda s: s.value_counts().index[0] + f" ({s.value_counts().iloc[0]}/{imp.Seed.nunique()} seeds)"))
print(top.to_string())

os.makedirs("results/ablation", exist_ok=True)
raw.to_csv("results/ablation/q02b_rmse_raw.csv", index=False)
paired.to_csv("results/ablation/q02b_rmse_paired.csv", index=False)
imp.to_csv("results/ablation/q02b_importance.csv", index=False)
lr.to_csv("results/ablation/q02b_lsp_rank.csv", index=False)
print("\nSaved results/ablation/q02b_*.csv")
