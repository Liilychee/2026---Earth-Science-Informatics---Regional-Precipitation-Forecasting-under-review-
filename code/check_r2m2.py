# R2-M2 evidence collection: are mxtpr, mntpr, lsp free of future (target-hour) information?
# READ-ONLY: no training, no files modified. Writes nothing except stdout.
# Run: cd /root/autodl-tmp && python3 code/check_r2m2.py > results/metrics/check_r2m2.txt 2>&1; wc -l results/metrics/check_r2m2.txt
import glob, hashlib, json, os, re
import numpy as np, pandas as pd

os.chdir("/root/autodl-tmp")
pd.set_option("display.width", 220); pd.set_option("display.max_columns", 40); pd.set_option("display.max_colwidth", 60)


def sec(t):
    print("\n" + "=" * 100 + "\n" + t + "\n" + "=" * 100)


def md5(f):
    return hashlib.md5(open(f, "rb").read()).hexdigest()


def info(f):
    t = pd.Timestamp(os.path.getmtime(f), unit="s").strftime("%Y-%m-%d %H:%M")
    return f"{t}  {os.path.getsize(f):>11}  {md5(f) if os.path.getsize(f) < 3e8 else '(big)'}  {f}"


def show(f, n=60):
    if not os.path.exists(f):
        print(f"  [missing] {f}"); return
    print(f"\n  -- {info(f)}")
    txt = open(f, errors="replace").read().splitlines()
    for l in txt[:n]:
        print("   " + l[:220])
    if len(txt) > n:
        print(f"   ... ({len(txt)} lines)")


# ---------------------------------------------------------------- 1. inventory
sec("1. INVENTORY (data files, raw downloads, notebooks, preprocessing scripts)")
for p in ["data/*.csv", "data/**/*.nc", "data/**/*.grib", "data/**/*.grb", "data/**/*.json", "data/**/*request*",
          "notebooks/**/*.ipynb", "*.ipynb", "code/*step2*", "code/*window*", "code/*feature*", "code/q01*", "code/q02*",
          "code/q06_audit*", "code/q09*"]:
    fs = sorted(set(f for f in glob.glob(p, recursive=True) if os.path.isfile(f) and "/q08/" not in f and "/q21/" not in f))
    if fs:
        print(f"--- {p}: {len(fs)}")
        for f in fs[:25]:
            print("  " + info(f))

# ---------------------------------------------------------------- 2. CSVs: columns, units, timestamps
sec("2. CSV COLUMNS, TIME AXIS, MAGNITUDES (mxtpr, mntpr, lsp, tp)")
for f in ["data/04-24.csv", "data/dublin_regional_2004_2021.csv"]:
    if not os.path.exists(f):
        print("  [missing]", f); continue
    d = pd.read_csv(f)
    print(f"\n{f}: shape {d.shape}\ncolumns: {list(d.columns)}")
    tcol = next((c for c in d.columns if re.search(r"time|date", c, re.I)), None)
    if tcol:
        t = pd.to_datetime(d[tcol])
        print(f"time col '{tcol}': {t.min()} -> {t.max()}, unique {t.nunique()}, hours {sorted(t.dt.hour.unique().tolist())[:24]}, "
              f"steps {pd.Series(t.drop_duplicates().sort_values()).diff().value_counts().head(3).to_dict()}")
    cols = [c for c in d.columns if re.search(r"mxtpr|mntpr|lsp|^tp|tp_mm|lat|lon", c, re.I)]
    if cols:
        print(d[cols].describe().T.to_string())
    print(d.head(3).to_string())

# consistency mxtpr*3600 >= tp >= mntpr*3600 (same hour) on the regional CSV, if columns exist
f = "data/dublin_regional_2004_2021.csv"
if os.path.exists(f):
    d = pd.read_csv(f)
    c = {k: next((x for x in d.columns if re.fullmatch(p, x, re.I)), None)
         for k, p in [("mx", r"mxtpr.*"), ("mn", r"mntpr.*"), ("tp", r"tp_mm|tp"), ("lsp", r"lsp.*")]}
    print("\nconsistency columns:", c)
    if c["mx"] and c["mn"] and c["tp"]:
        mx, mn, tp = d[c["mx"]].astype(float), d[c["mn"]].astype(float), d[c["tp"]].astype(float)
        scale = 3600.0 if mx.max() < 0.1 else 1.0  # kg m-2 s-1 -> mm/h
        print(f"mxtpr scale used: x{scale}")
        for eps in [0, 1e-4, 1e-3]:
            print(f"  eps {eps:g}: mxtpr*s >= tp: {(mx * scale >= tp - eps).mean():.4f} | tp >= mntpr*s: {(tp >= mn * scale - eps).mean():.4f}")
        if c["lsp"]:
            l = d[c["lsp"]].astype(float)
            ls = 1000.0 if l.max() < 0.1 else 1.0
            print(f"  lsp*{ls:g} <= tp + 1e-4: {(l * ls <= tp + 1e-4).mean():.4f}  (lsp is part of tp in the same hour)")

# ---------------------------------------------------------------- 3. raw file metadata (if any non-WB2 nc exists)
sec("3. RAW ERA5 FILE METADATA (stepType, units, valid_time) if any raw download is on AutoDL")
ncs = sorted(f for f in glob.glob("data/**/*.nc", recursive=True) if "weatherbench" not in f.lower() and "/q08/" not in f)
if not ncs:
    print("  no raw ERA5 .nc on AutoDL (expected: raw CDS downloads are on the Mac; see q22 raw/ folder)")
try:
    import h5py
    for f in ncs[:6]:
        with h5py.File(f, "r") as h:
            print(f"\n  {f}: datasets {list(h.keys())}")
            for k in h.keys():
                if re.search(r"mxtpr|mntpr|lsp|tp", k):
                    a = {x: (h[k].attrs[x].decode() if isinstance(h[k].attrs[x], bytes) else h[k].attrs[x])
                         for x in h[k].attrs if x not in ("DIMENSION_LIST", "REFERENCE_LIST")}
                    print(f"    {k}: {a}")
except Exception as e:
    print("  h5py read failed:", e)

# ---------------------------------------------------------------- 4. windowing, split, scaler, feature selection in code
sec("4. CODE: windowing, target shift, split, scaler fit, feature selection")
PAT = (r"values_X\[|values_y\[|shift\(|\.shift|window|W *= *6|i *\+ *6|horizon|lead|"
       r"StandardScaler|MinMaxScaler|\.fit\(|fit_transform|scaler|"
       r"spearman|corr\(|select|top_?k|nlargest|"
       r"train_end|test_start|0\.7|0\.15|iloc\[|split|merge\(|join\(|resample|rolling|groupby\(.*time")
srcs = sorted(set(glob.glob("code/*step2*.py") + glob.glob("code/*window*.py") + glob.glob("code/*feature*.py")
                  + glob.glob("**/*.ipynb", recursive=True)))
for f in srcs:
    if "checkpoint" in f:
        continue
    if f.endswith(".ipynb"):
        try:
            nb = json.load(open(f))
        except Exception as e:
            print("  cannot read", f, e); continue
        print(f"\n  [notebook] {info(f)}")
        for ci, cell in enumerate(nb.get("cells", [])):
            if cell.get("cell_type") != "code":
                continue
            for li, l in enumerate("".join(cell.get("source", "")).splitlines()):
                if re.search(PAT, l) and not l.strip().startswith("#"):
                    print(f"   cell {ci:3d} L{li + 1:3d}: {l.strip()[:200]}")
    else:
        print(f"\n  [script] {info(f)}")
        for li, l in enumerate(open(f, errors="replace").read().splitlines()):
            if re.search(PAT, l) and not l.strip().startswith("#"):
                print(f"   L{li + 1:4d}: {l.strip()[:200]}")

# ---------------------------------------------------------------- 5. existing evidence files
sec("5. EXISTING EVIDENCE OUTPUTS (01 consistency, 02 ablation, 06 audit, 09 lead correlation, 10 ablation)")
for p in ["results/**/q01*", "results/**/q02*", "results/**/q06_audit*", "results/**/q06_repro*", "results/**/q09_output*",
          "results/**/q09_selection_table.csv", "results/**/q10_group_ablation.csv", "results/**/*leak*", "results/**/*align*"]:
    for f in sorted(set(glob.glob(p, recursive=True))):
        if os.path.isfile(f):
            show(f, 40)

print("\n===== CHECK COMPLETE (read-only) =====")
