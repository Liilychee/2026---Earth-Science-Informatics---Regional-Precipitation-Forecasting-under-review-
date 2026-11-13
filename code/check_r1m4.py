# ============================================================
# R1 M4 evidence check (items 10, 17, 25). READ-ONLY: no training, nothing written or modified.
# Run: cd /root/autodl-tmp && python3 code/check_r1m4.py > results/metrics/check_r1m4.txt 2>&1; wc -l results/metrics/check_r1m4.txt
# ============================================================
import glob, hashlib, json, os, re
import numpy as np
import pandas as pd

os.chdir("/root/autodl-tmp")
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 60)
pd.set_option("display.max_rows", 200); pd.set_option("display.max_colwidth", 50)
Q95 = 0.574048
SEEDS = [42, 123, 7, 2024, 99]


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


def grep(f, pat, maxl=60):
    try:
        lines = open(f, errors="replace").read().splitlines()
    except Exception as e:
        print("  cannot read", f, e); return
    hit = [(i + 1, l) for i, l in enumerate(lines) if re.search(pat, l, re.I)]
    print(f"  [grep] {f}: {len(hit)} lines")
    for i, l in hit[:maxl]:
        print(f"   {i:5d}: {l[:230]}")


def csv(f, n=80):
    try:
        d = pd.read_csv(f)
    except Exception as e:
        print("  cannot read", f, e); return None
    print(f"\n  == {f}  shape {d.shape}")
    print(d.head(n).to_string())
    return d


def sec(t):
    print("\n" + "=" * 110 + "\n" + t + "\n" + "=" * 110)


# ------------------------------------------------------------------ 1. files
sec("1. FILES")
code = files(["code/q10*.py", "code/*shap*.py", "code/*ablation*.py", "code/q17*.py", "code/q25*.py"])
print("----- scripts"); [print(info(f)) for f in code]
logs = files(["results/**/q10*.txt", "results/**/q10*.log", "results/**/*shap*output*.txt", "results/**/q17*.txt"])
print("----- logs"); [print(info(f)) for f in logs]
mets = files(["results/**/q10*.csv", "results/**/q17*.csv"])
print("----- metric CSVs"); [print(info(f)) for f in mets]
other = files(["results/q10/**/*"])
print(f"----- results/q10 tree: {len(other)} files")
by_dir = pd.Series([os.path.dirname(f) for f in other]).value_counts()
print(by_dir.to_string())
for f in [f for f in other if not re.search(r"/preds/|/runs/", f)][:60]:
    print(info(f))

# ------------------------------------------------------------------ 2. run identity
sec("2. RUN IDENTITY (results/q10/runs/*.json and preds)")
runs = []
for f in sorted(glob.glob("results/q10/runs/*.json")):
    try:
        j = json.load(open(f))
    except Exception:
        continue
    tag = os.path.basename(f)[:-5]
    m = re.match(r"(.+?)__(.+)__s(\d+)$", tag)
    t = j.get("test", {}) if isinstance(j.get("test"), dict) else {}
    runs.append({"tag": tag, "arch": m.group(1) if m else None, "cfg": m.group(2) if m else None,
                 "seed": int(m.group(3)) if m else j.get("seed"), "test_rmse": t.get("rmse", j.get("test_rmse")),
                 "best_epoch": j.get("best_epoch"), "epochs": j.get("epochs_trained"), "gpu": j.get("gpu"),
                 "tf": j.get("tf"), "finished": j.get("finished_utc"), "keys": ",".join(sorted(j.keys()))[:120]})
R = pd.DataFrame(runs)
print(f"json runs: {len(R)}")
if len(R):
    print("keys of first json:", R["keys"].iloc[0])
    print(pd.crosstab([R.arch, R.cfg], R.seed).to_string())
    print("\nGPU / TF:", R.gpu.value_counts(dropna=False).to_dict(), R.tf.value_counts(dropna=False).to_dict())
    print("finished range:", R.finished.min(), "->", R.finished.max())
preds = sorted(glob.glob("results/q10/preds/*.csv"))
P = {}
for f in preds:
    m = re.match(r"(.+?)__(.+)__s(\d+)$", os.path.basename(f)[:-4])
    if m:
        P[(m.group(1), m.group(2), int(m.group(3)))] = f
print(f"\npred files: {len(preds)}")
if P:
    k = pd.DataFrame(list(P.keys()), columns=["arch", "cfg", "seed"])
    print(pd.crosstab([k.arch, k.cfg], k.seed).to_string())


def load_test(f):
    d = pd.read_csv(f)
    if "split" in d:
        d = d[d["split"] == "test"]
    return d.reset_index(drop=True)


def rmse(a, b):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


# ------------------------------------------------------------------ 3. recompute ablation from predictions
sec("3. ABLATION RECOMPUTED FROM SAVED PREDICTIONS (two aggregation conventions)")
archs = sorted(set(a for a, c, s in P))
rows = []
for a in archs:
    cfgs = sorted(set(c for aa, c, s in P if aa == a))
    if "full" not in cfgs:
        print(f"{a}: no 'full' config, cfgs = {cfgs}"); continue
    F = {s: load_test(P[(a, "full", s)]) for s in SEEDS if (a, "full", s) in P}
    if not F:
        continue
    s0 = next(iter(F)); y = F[s0]["y_true"].to_numpy(float); vt = F[s0]["valid_time"].values
    tail = y >= Q95
    fr = {s: rmse(F[s].y_pred_mean, y) for s in F}
    print(f"\n{a}: full model test RMSE per seed {', '.join(f'{s}:{v:.6f}' for s, v in fr.items())}; "
          f"mean {np.mean(list(fr.values())):.6f} SD {np.std(list(fr.values()), ddof=1):.6f}; n test {len(y)}, tail {tail.sum()}")
    Fe = np.mean([F[s].y_pred_mean.to_numpy(float) for s in F], axis=0)
    for c in cfgs:
        if c == "full":
            continue
        A = {s: load_test(P[(a, c, s)]) for s in SEEDS if (a, c, s) in P}
        common = sorted(set(A) & set(F))
        for s in common:
            assert (A[s].valid_time.values == vt).all(), f"{a} {c} {s} time misaligned"
        for sub, mk in (("all", np.ones_like(y, bool)), ("upper>=Q95", tail)):
            d = np.array([rmse(A[s].y_pred_mean.to_numpy(float)[mk], y[mk]) - rmse(F[s].y_pred_mean.to_numpy(float)[mk], y[mk])
                          for s in common])
            Ae = np.mean([A[s].y_pred_mean.to_numpy(float) for s in common], axis=0)
            Fe_c = np.mean([F[s].y_pred_mean.to_numpy(float) for s in common], axis=0)
            se = d.std(ddof=1) / np.sqrt(len(d)) if len(d) > 1 else np.nan
            rows.append({"arch": a, "cfg": c, "subset": sub, "n_seeds": len(common),
                         "seedmean_dRMSE": d.mean(), "seed_sd": d.std(ddof=1) if len(d) > 1 else np.nan,
                         "t95_lo": d.mean() - 2.776 * se, "t95_hi": d.mean() + 2.776 * se,
                         "n_worse": int((d > 0).sum()), "ensemble_dRMSE": rmse(Ae[mk], y[mk]) - rmse(Fe_c[mk], y[mk]),
                         "per_seed": " ".join(f"{x:+.5f}" for x in d)})
AB = pd.DataFrame(rows)
if len(AB):
    print(AB.round(5).to_string(index=False))

# ------------------------------------------------------------------ 4. metric CSVs
sec("4. METRIC CSVs (as saved)")
for f in mets:
    if re.search(r"temporal", f):
        d = csv(f, 15)
    else:
        csv(f, 120)

# ------------------------------------------------------------------ 5. SHAP arrays
sec("5. SHAP ARRAYS")
for f in files(["results/q10/**/*.npz", "results/q10/**/*.npy"])[:40]:
    try:
        z = np.load(f, allow_pickle=True)
        if hasattr(z, "files"):
            print(f"{f}: " + "; ".join(f"{k} {z[k].shape} {z[k].dtype}" for k in z.files))
        else:
            print(f"{f}: {z.shape} {z.dtype}")
    except Exception as e:
        print(f, "cannot load", e)

# ------------------------------------------------------------------ 6. configuration in scripts and logs
sec("6. CONFIGURATION IN SCRIPTS AND LOGS")
PAT = (r"coalition|n_?coal|128|background|n_?bg|n_?back|kmeans|300|238|permutation|perm|exact|shapley|"
       r"kendall|tau|block|n_?boot|NBOOT|reps|10000|10,000|2000|2,000|calendar|day|date\.|normalize|"
       r"SEEDS|seed|group|drop|remove|ablat|Q95|0\.574|t\.ppf|2\.776|sem|ci_|percentile")
for f in code:
    grep(f, PAT, 90)
for f in logs:
    grep(f, r"coalition|background|300|238|kendall|tau|block|boot|reps|seed|repro|0\.24|mntpr|signed|ratio|tail|upper", 70)

sec("7. MAIN-TABLE CHECK")
for f in files(["results/final_5seed_point.csv", "results/final_all_seed_raw.csv"]):
    d = pd.read_csv(f)
    d = d[d.astype(str).apply(lambda r: r.str.contains("BiLSTM-Attention|BU-LSTM-Attention|proposed").any(), axis=1)]
    print(f"\n{f}\n{d.to_string()}")
print("\n===== CHECK COMPLETE (read-only) =====")
