# ============================================================
# reduce_big_era5_csv.py  — run LOCALLY on your own computer
#
# Reads a very large ERA5 CSV in chunks (low memory), keeps only
# the Dublin box (lat 52.75-53.75, lon -6.75..-5.75) and
# 2004-01-01 .. 2021-12-31, then averages the grid cells per time
# step -> one row per timestamp (regional mean).
#
# USAGE:
#   python reduce_big_era5_csv.py inspect  "D:/path/big.csv"
#       -> prints columns + first rows only (run this FIRST)
#   python reduce_big_era5_csv.py reduce   "D:/path/big.csv"
#       -> writes dublin_regional_reduced.csv next to the script
#
# If auto-detected column names are wrong, edit the CONFIG block.
# ============================================================
import sys
import pandas as pd

# ---------------- CONFIG (edit if needed) ----------------
TIME_COL = None   # e.g. "valid_time" / "time"; None = auto-detect
LAT_COL = None    # e.g. "latitude";            None = auto-detect
LON_COL = None    # e.g. "longitude";           None = auto-detect
LAT_MIN, LAT_MAX = 52.75, 53.75
LON_MIN, LON_MAX = -6.75, -5.75
START, END = "2004-01-01", "2021-12-31 23:59:59"
CHUNK = 1_000_000
OUT = "dublin_regional_reduced.csv"
# ---------------------------------------------------------


def detect(cols):
    low = {c.lower(): c for c in cols}
    t = TIME_COL or next((low[k] for k in ("valid_time", "time", "datetime", "date") if k in low), None)
    la = LAT_COL or next((low[k] for k in ("latitude", "lat") if k in low), None)
    lo = LON_COL or next((low[k] for k in ("longitude", "lon") if k in low), None)
    assert t and la and lo, f"Cannot detect time/lat/lon in {list(cols)}; edit CONFIG."
    return t, la, lo


def inspect(path):
    head = pd.read_csv(path, nrows=5)
    print("Columns:", list(head.columns))
    print(head.to_string())
    n = 0
    for ch in pd.read_csv(path, usecols=[0], chunksize=CHUNK):
        n += len(ch)
    print("Total rows:", n)


def reduce(path):
    first = pd.read_csv(path, nrows=1)
    t, la, lo = detect(first.columns)
    print("Using:", t, la, lo)
    parts, kept, seen = [], 0, 0
    for ch in pd.read_csv(path, chunksize=CHUNK):
        seen += len(ch)
        ch[t] = pd.to_datetime(ch[t])
        m = (ch[la].between(LAT_MIN - 1e-6, LAT_MAX + 1e-6)
             & ch[lo].between(LON_MIN - 1e-6, LON_MAX + 1e-6)
             & (ch[t] >= START) & (ch[t] <= END))
        sub = ch.loc[m]
        kept += len(sub)
        if len(sub):
            parts.append(sub)
        print(f"read {seen:,} rows, kept {kept:,}", end="\r")
    df = pd.concat(parts, ignore_index=True)
    ncell = df.groupby(t).size()
    print("\nCells per timestamp: min/max =", ncell.min(), ncell.max(), "(expect 25)")
    num = df.drop(columns=[c for c in (la, lo, "number", "expver") if c in df.columns]).select_dtypes("number").columns
    reg = df.groupby(t)[list(num)].mean().reset_index()
    reg.to_csv(OUT, index=False)
    print("Saved", OUT, reg.shape)
    print("Columns:", list(reg.columns))
    print("Range:", reg[t].min(), "->", reg[t].max())


if __name__ == "__main__":
    mode, path = sys.argv[1], sys.argv[2]
    inspect(path) if mode == "inspect" else reduce(path)
