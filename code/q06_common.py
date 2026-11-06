# ============================================================
# Item 06: shared definitions for the rolling-origin (expanding-window) analysis.
# Every q06 script imports the fold definitions from here.
# ============================================================
import os
import pandas as pd

ROOT = os.environ.get("Q06_ROOT", "/root/autodl-tmp")
DATA = f"{ROOT}/data/q06/dublin_regional_1992_2021.csv"
CANDIDATES = ["u10", "v10", "d2m", "t2m", "sp", "e", "mxtpr", "mntpr", "tcc", "ssr", "lsp"]
FEATURES = ["mxtpr", "mntpr", "lsp", "tcc", "v10", "sp", "d2m"]          # main-study predictor set
TARGET = "tp_mm"
WINDOW = 6
SEEDS = [42, 123, 7, 2024, 99]

# calendar years, inclusive; each split uses whole years
FOLDS = {
    "F1":  {"train": (1992, 2007), "val": (2008, 2009), "test": (2010, 2012)},
    "F2":  {"train": (1992, 2010), "val": (2011, 2012), "test": (2013, 2015)},
    "F3":  {"train": (1992, 2013), "val": (2014, 2015), "test": (2016, 2018)},
    "F4":  {"train": (1992, 2016), "val": (2017, 2018), "test": (2019, 2021)},
    "F4s": {"train": (2004, 2016), "val": (2017, 2018), "test": (2019, 2021)},   # fold 4' (short history)
}


def load_regional():
    return pd.read_csv(DATA, parse_dates=["valid_time"])


def split(df, fold):
    y = df["valid_time"].dt.year
    out = {}
    for part, (a, b) in FOLDS[fold].items():
        out[part] = df[(y >= a) & (y <= b)].reset_index(drop=True)
    return out
