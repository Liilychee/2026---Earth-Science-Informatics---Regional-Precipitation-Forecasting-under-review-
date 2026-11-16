"""R4-M2 read-only check: lsp/tp identity, large-scale share, and whether
the latest lsp input bounds the six-hour target. No training, no downloads.
Usage: python r4m2_lsp_semantics_check.py <dublin_regional_reduced.csv> <out_dir>"""
import sys, json, numpy as np, pandas as pd
src, out = sys.argv[1], sys.argv[2]
d = pd.read_csv(src, parse_dates=["valid_time"]).sort_values("valid_time").reset_index(drop=True)
assert len(d) == 26300 and (d.valid_time.diff().dropna() == pd.Timedelta(hours=6)).all()
tp, lsp = d.tp.values * 1000.0, d.lsp.values * 1000.0      # m -> mm (one-hour accumulations)
season = d.valid_time.dt.month.map({12:"DJF",1:"DJF",2:"DJF",3:"MAM",4:"MAM",5:"MAM",
                                    6:"JJA",7:"JJA",8:"JJA",9:"SON",10:"SON",11:"SON"}).values
res = {"source_rows": len(d), "first": str(d.valid_time.iloc[0]), "last": str(d.valid_time.iloc[-1])}
exc = lsp - tp
res["same_hour"] = {"max_lsp_minus_tp_mm": float(exc.max()),
    "n_lsp_gt_tp_by_1e-6": int((exc > 1e-6).sum()), "n_lsp_gt_tp_by_1e-4": int((exc > 1e-4).sum()),
    "n_lsp_gt_tp_by_1e-3": int((exc > 1e-3).sum()), "min_lsp_mm": float(lsp.min()), "min_tp_mm": float(tp.min())}
def share(m):
    w = m & (tp >= 0.1)
    return {"N": int(m.sum()), "N_wet": int(w.sum()),
            "ratio_of_sums_pct": 100 * lsp[m].sum() / tp[m].sum(),
            "ratio_of_sums_wet_only_pct": 100 * lsp[w].sum() / tp[w].sum(),
            "median_hourly_ratio_wet_pct": 100 * float(np.median(lsp[w] / tp[w]))}
rows = []
for per, sl in [("all_2004_2021", slice(0, 26300)), ("train_18410", slice(0, 18410))]:
    base = np.zeros(26300, bool); base[sl] = True
    for g in ["All", "DJF", "MAM", "JJA", "SON"]:
        m = base & ((season == g) if g != "All" else True)
        rows.append({"period": per, "group": g, **share(m)})
pd.DataFrame(rows).to_csv(f"{out}/R4M2_LSP_SHARE_RECOMPUTE.csv", index=False)
# windowed targets exactly as in the pipeline: X rows i..i+5, y row i+6, built within each partition
parts = {"train": (0, 18410), "val": (18410, 22355), "test": (22355, 26300)}
lb = []
for name, (a, b) in parts.items():
    idx = np.arange(a, b - 6)
    last_lsp, target = lsp[idx + 5], tp[idx + 6]
    tgt_time = d.valid_time.values[idx + 6]; org_time = d.valid_time.values[idx + 5]
    assert np.all((tgt_time - org_time) == np.timedelta64(6, "h"))
    for thr in [0.1, 0.7]:
        m = last_lsp >= thr
        lb.append({"partition": name, "n_targets": len(idx), "lsp_t0_threshold_mm": thr, "n_origins": int(m.sum()),
                   "pct_target_below_lsp_t0": 100 * float(np.mean(target[m] < last_lsp[m])) if m.any() else np.nan,
                   "pct_target_below_0.1mm": 100 * float(np.mean(target[m] < 0.1)) if m.any() else np.nan})
pd.DataFrame(lb).to_csv(f"{out}/R4M2_LOWER_BOUND_RECOMPUTE.csv", index=False)
json.dump(res, open(f"{out}/R4M2_SAME_HOUR_CHECK.json", "w"), indent=2)
print(json.dumps(res, indent=2)); print(pd.DataFrame(rows).round(3).to_string(index=False)); print(pd.DataFrame(lb).round(2).to_string(index=False))
