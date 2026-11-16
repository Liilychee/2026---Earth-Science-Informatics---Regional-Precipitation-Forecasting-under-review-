"""R4-M3 read-only recheck (no training): (1) cp-addition XGBoost paired deltas with seed-t interval;
(2) independent recomputation of q03e convective/large-scale strata, RMSE skill vs train month x hour climatology.
Usage: python r4m3_check.py <regional_csv> <xgboost_preds.csv> <proposed_model_preds.csv> <cp_raw.csv> <out_dir>"""
import sys, json, numpy as np, pandas as pd
from scipy import stats
data, xp, bp, raw, out = sys.argv[1:6]
r = pd.read_csv(raw); a = r[r.Variant == 'A_base7'].set_index('Seed').RMSE; b = r[r.Variant == 'B_base7_plus_cp'].set_index('Seed').RMSE
d = (b - a).loc[[42, 123, 7, 2024, 99]]
h = stats.t.ppf(0.975, 4) * d.std(ddof=1) / np.sqrt(5)
A = {"A_mean": a.mean(), "A_sd": a.std(ddof=1), "B_mean": b.mean(), "B_sd": b.std(ddof=1),
     "delta_by_seed": d.to_dict(), "delta_mean": d.mean(), "delta_pct": 100 * d.mean() / a.mean(),
     "seed_t_95": [d.mean() - h, d.mean() + h], "n_improved": int((d < 0).sum())}
df = pd.read_csv(data, parse_dates=["valid_time"]).sort_values("valid_time").reset_index(drop=True)
df["tp_mm"], df["lsp_mm"] = df.tp * 1000, df.lsp * 1000
n = len(df); tr = df.iloc[:int(n * .7)].iloc[6:].copy(); te = df.iloc[int(n * .85):].reset_index(drop=True).iloc[6:].reset_index(drop=True)
for t in (tr, te): t["month"], t["hour"] = t.valid_time.dt.month, t.valid_time.dt.hour
clim = tr.groupby(["month", "hour"]).tp_mm.mean(); ref = np.array([clim.loc[(m, hh)] for m, hh in zip(te.month, te.hour)])
y = te.tp_mm.to_numpy(); share = np.where(y > 0, (te.tp_mm - te.lsp_mm) / np.where(y > 0, y, 1), np.nan)
wet = y >= 0.1; conv = wet & (share >= 0.5); ls = wet & (share < 0.5); jja = te.month.isin([6, 7, 8]).to_numpy()
M = {"all": np.ones(len(y), bool), "JJA": jja, "nonJJA": ~jja, "wet": wet, "conv": conv, "ls": ls,
     "JJA_conv": conv & jja, "JJA_ls": ls & jja, "nonJJA_conv": conv & ~jja, "nonJJA_ls": ls & ~jja,
     "JJA_wet": wet & jja, "nonJJA_wet": wet & ~jja}
rows = []
for name, f in [("XGBoost", xp), ("BU-LSTM-Attention", bp)]:
    p = pd.read_csv(f, parse_dates=["valid_time"]); p = p[p.split == "test"].drop_duplicates("valid_time").sort_values("valid_time").reset_index(drop=True)
    assert (p.valid_time.to_numpy() == te.valid_time.to_numpy()).all() and np.allclose(p.y_true, y, atol=1e-6)
    yp = p.y_pred_mean.to_numpy()
    for k, m in M.items():
        rm = np.sqrt(np.mean((y[m] - yp[m]) ** 2)); rr = np.sqrt(np.mean((y[m] - ref[m]) ** 2))
        rows.append({"model": name, "stratum": k, "N": int(m.sum()), "mean_obs": y[m].mean(), "RMSE": rm, "RMSE_clim": rr,
                     "skill": 1 - rm / rr, "RMSE_over_mean": rm / y[m].mean(), "pearson": np.corrcoef(y[m], yp[m])[0, 1]})
S = pd.DataFrame(rows); S.to_csv(f"{out}/R4M3_STRATA_RECOMPUTE.csv", index=False)
json.dump({"cp_addition": A, "n_target_cp_share_nan_in_wet": int(np.isnan(share[wet]).sum()),
           "max_lsp_minus_tp_in_wet_mm": float((te.lsp_mm - te.tp_mm)[wet].max())}, open(f"{out}/R4M3_CP_ADDITION.json", "w"), indent=2, default=float)
print(json.dumps(A, indent=1, default=float)); print(S.round(4).to_string(index=False))
