# ============================================================
# R1 M2 evidence check (items 07, 08, 13). READ-ONLY: no training, no file is written or modified.
# Run: cd /root/autodl-tmp && python3 code/check_r1m2.py 2>&1 | tee /tmp/check_r1m2.txt
# ============================================================
import glob, hashlib, json, os, re
import numpy as np
import pandas as pd

os.chdir("/root/autodl-tmp")
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 60)
pd.set_option("display.max_rows", 120); pd.set_option("display.max_colwidth", 60)


def md5(f):
    return hashlib.md5(open(f, "rb").read()).hexdigest()


def info(f):
    t = pd.Timestamp(os.path.getmtime(f), unit="s").strftime("%Y-%m-%d %H:%M")
    return f"{t}  {os.path.getsize(f):>11}  {md5(f)}  {f}"


def files(pats):
    out = []
    for p in pats:
        out += glob.glob(p, recursive=True)
    return sorted(set(f for f in out if os.path.isfile(f)))


def show_files(title, pats):
    print(f"\n----- {title}: files -----")
    fs = files(pats)
    for f in fs:
        print(info(f))
    if not fs:
        print("NONE FOUND for", pats)
    return fs


def grep(f, pat, maxl=40):
    try:
        lines = open(f, errors="replace").read().splitlines()
    except Exception as e:
        print("  cannot read", f, e); return
    hit = [(i + 1, l) for i, l in enumerate(lines) if re.search(pat, l, re.I)]
    print(f"  [grep {pat!r}] {f}: {len(hit)} lines")
    for i, l in hit[:maxl]:
        print(f"   {i:5d}: {l[:220]}")


def csv(f, n=60):
    try:
        d = pd.read_csv(f)
    except Exception as e:
        print("  cannot read", f, e); return None
    print(f"  == {f}  shape {d.shape}")
    print(d.head(n).round(6).to_string())
    return d


def ci_excl_zero(d, label):
    """Print rows whose CI (lo/hi columns found by name) excludes 0."""
    if d is None:
        return
    cols = list(d.columns)
    LO = r"(?:^|_)(?:lower|low|lo|l|2\.5)(?=$|_)"; HI = r"(?:^|_)(?:upper|high|hi|u|97\.5)(?=$|_)"
    lo = [c for c in cols if re.search(LO, c, re.I)]
    hi = [c for c in cols if re.search(HI, c, re.I)]
    pairs = [(a, b) for a in lo for b in hi if re.sub(LO, "_X", a, flags=re.I) == re.sub(HI, "_X", b, flags=re.I)]
    if not pairs:
        print(f"  [{label}] no lo/hi column pair recognised; columns = {cols}"); return
    for a, b in pairs:
        x = d[(pd.to_numeric(d[a], errors="coerce") > 0) | (pd.to_numeric(d[b], errors="coerce") < 0)]
        print(f"  [{label}] rows with CI ({a}, {b}) excluding 0: {len(x)} of {len(d)}")
        if len(x):
            print(x.round(6).to_string())


CODE = ["code/*.py", "code/**/*.py", "*.py"]
LOGS = ["results/**/*.txt", "results/**/*.log", "*.txt"]

# ------------------------------------------------------------------ 1. q07 / q07b
print("\n" + "=" * 100 + "\n1. q07 / q07b baselines\n" + "=" * 100)
show_files("q07 CSV", ["results/**/q07*.csv"])
sc = [f for f in files(CODE) if re.search(r"q07|revision_metrics|damped|baseline", os.path.basename(f), re.I)]
print("\n----- q07 scripts -----"); [print(info(f)) for f in sc]
lg = [f for f in files(LOGS) if re.search(r"q07|revision_metrics|q05c", os.path.basename(f), re.I)]
print("\n----- q07 logs -----"); [print(info(f)) for f in lg]
for f in files(["results/**/q07b_linear_baselines.csv", "results/**/q07_baseline_metrics.csv"]):
    csv(f)
for f in files(["results/**/q07b_model_minus_linear.csv", "results/**/q07_model_minus_reference.csv"]):
    d = csv(f, 80); ci_excl_zero(d, os.path.basename(f))
for f in sc:
    grep(f, r"alpha|Ridge|RidgeCV|GridSearch|cv=|TimeSeriesSplit|block|n_?boot|reps|seed|final_all_seed|_preds\.csv|mean\(axis|seed[- ]avera|ensemble")
for f in lg:
    grep(f, r"alpha|ridge|L1|L2|L3|block|boot|reps|seed|selected")

# ------------------------------------------------------------------ 2-3. q08 HRES
print("\n" + "=" * 100 + "\n2-3. q08 / q08b / q08c HRES comparison\n" + "=" * 100)
show_files("q08 CSV", ["results/**/q08*.csv"])
sc8 = [f for f in files(CODE) if re.search(r"q08|hres", os.path.basename(f), re.I)]
print("\n----- q08 scripts -----"); [print(info(f)) for f in sc8]
lg8 = [f for f in files(LOGS) if re.search(r"q08|hres", os.path.basename(f), re.I)]
print("\n----- q08 logs -----"); [print(info(f)) for f in lg8]
print("\n----- HRES raw data files -----")
for f in files(["data/**/*hres*", "data/**/*HRES*", "HRES/**/*", "results/**/*hres*.nc", "data/q08/**/*"])[:40]:
    print(info(f))

al = files(["results/**/q08_hres_aligned_samples.csv"])
if al:
    d = pd.read_csv(al[0])
    print(f"\n  aligned samples: {al[0]} shape {d.shape}\n  columns: {list(d.columns)}")
    print(d.head(5).to_string())
    tcols = [c for c in d.columns if re.search(r"time|date|init|valid|origin", c, re.I)]
    for c in tcols:
        try:
            t = pd.to_datetime(d[c])
            print(f"  {c}: n={t.notna().sum()} unique={t.nunique()} min={t.min()} max={t.max()} "
                  f"hours={sorted(t.dt.hour.unique().tolist())}")
        except Exception:
            pass
    vc = [c for c in tcols if re.search(r"valid", c, re.I)]
    ic = [c for c in tcols if re.search(r"init|origin|base|issue", c, re.I)]
    if vc and ic:
        lead = (pd.to_datetime(d[vc[0]]) - pd.to_datetime(d[ic[0]])).dt.total_seconds() / 3600
        print(f"  lead time {vc[0]} - {ic[0]} (h): {lead.value_counts().to_dict()}")
    if vc:
        t = pd.to_datetime(d[vc[0]]).sort_values()
        gaps = t.diff().dropna().value_counts().head(5)
        print(f"  gaps between consecutive {vc[0]}: {gaps.to_dict()}")
        print(f"  distinct days: {t.dt.normalize().nunique()}")
for f in files(["results/**/q08_hres_comparison.csv", "results/**/q08b_station_comparison.csv", "results/**/q08c_event_auc.csv"]):
    csv(f, 80)
for f in files(["results/**/q08_hres_bootstrap.csv", "results/**/q08b_station_bootstrap.csv", "results/**/q08c_event_auc_paired.csv"]):
    d = csv(f, 100); ci_excl_zero(d, os.path.basename(f))
for f in sc8:
    grep(f, r"/ ?6|6\.0|\* ?1000|1000|step|accum|tp|lead|init|valid|time_step|05:00|\+ ?6|hours=|block|n_?boot|reps|BSEED|seed|default_rng|RandomState")
for f in lg8:
    grep(f, r"block|boot|reps|seed|n ?=|samples|lead|init|valid|1970|1,970|/ ?6|accum|warn|error")

# ------------------------------------------------------------------ 4. Table 3 sources
print("\n" + "=" * 100 + "\n4. Table 3 statistics\n" + "=" * 100)
show_files("Table 3 source CSV", ["results/**/final_5seed_point.csv", "results/**/seed_stability_summary.csv",
                                  "results/**/prob_bilstm_attention_seed_summary.csv", "results/**/final_all_seed_raw.csv",
                                  "results/**/final_5seed_probabilistic.csv"])
for f in files(["results/**/seed_stability_summary.csv", "results/**/prob_bilstm_attention_seed_summary.csv",
                "results/**/final_5seed_point.csv"]):
    csv(f)
tj = sorted(glob.glob("results/q14/runs/transformer__w6__mse__s*.json"))
print(f"\n  Transformer W=6 MSE runs: {len(tj)}")
rows = []
for f in tj:
    j = json.load(open(f)); t = j.get("test", {})
    rows.append({"file": os.path.basename(f), "seed": j.get("seed"), "rmse": t.get("rmse"), "mae": t.get("mae"),
                 "r2": t.get("r2"), "best": j.get("best_epoch"), "epochs": j.get("epochs_trained"), "gpu": j.get("gpu")})
if rows:
    T = pd.DataFrame(rows); print(T.to_string(index=False))
    print(f"  Transformer five-seed RMSE mean {T.rmse.mean():.6f} SD {T.rmse.std(ddof=1):.6f}")
    for f in files(["results/q14/preds/transformer__w6__mse__s*.csv"]):
        p = pd.read_csv(f); p = p[p.split == "test"] if "split" in p else p
        print(f"  check preds {os.path.basename(f)}: n={len(p)} rmse={np.sqrt(np.mean((p.y_pred_mean - p.y_true) ** 2)):.6f}")
CLIM = 0.273057
print(f"\n  SS with unrounded denominator {CLIM}:")
for name, m in [("Prob. BiLSTM-Attention 5-seed", 0.248843), ("Transformer 5-seed", T.rmse.mean() if rows else np.nan)]:
    print(f"   {name}: RMSE {m:.6f} -> SS {1 - m / CLIM:.4f}")
for f in files(["results/**/prob_bilstm_attention_seed_summary.csv"]):
    d = pd.read_csv(f)
    num = d.select_dtypes("number")
    print(f"  {f} numeric means:\n{num.mean().round(6).to_string()}")

# ------------------------------------------------------------------ 5. q13 / q03d
print("\n" + "=" * 100 + "\n5. q13 seasonal and q03d\n" + "=" * 100)
show_files("q13 / q03d files", ["results/**/q13_*", "results/**/q03d_*", "code/q13_seasonal.py",
                               "code/analysis_q03d_seasonal_xgb.py"])
for f in files(["code/q13_seasonal.py"]):
    grep(f, r"preds|predictions|q14|q21|q10|q06|glob|SEEDS|seed|block|n_?boot|reps|BSEED|clim|AR\(1\)|ar1")
for f in files(["results/**/q13_output.txt"]):
    grep(f, r"source|preds|seed 42|repro|check|核对|0\.2731|0\.2627|0\.3282|0\.24375|0\.242848|block|boot")
for f in files(["code/analysis_q03d_seasonal_xgb.py"]):
    grep(f, r"variant|G |S |F |global|season|month|hour|feature|SEEDS|seed|block|n_?boot|NBOOT|reps|BSEED|XGB_KW|n_estimators")
for f in files(["results/**/q03d_seasonal_xgb_summary.csv"]):
    csv(f)
for f in files(["results/**/q03d_seasonal_xgb_paired.csv"]):
    d = csv(f, 80); ci_excl_zero(d, "q03d_paired")
print("\n===== CHECK COMPLETE (read-only) =====")
