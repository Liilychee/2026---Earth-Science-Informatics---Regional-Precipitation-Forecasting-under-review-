# ============================================================
# Item 10 + 17, step 0: rebuild the Step 2D windows once.
# Reads data/04-24.csv (read-only) exactly as notebook Steps 2B-2D,
# checks the result against the saved predictions, and stores the
# windows so that parallel training jobs do not each read the CSV.
# Output: results/windows/q10_windows.npz (git-ignored)
# ============================================================
import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

ROOT = os.environ.get("Q10_ROOT", "/root/autodl-tmp")
CSV = f"{ROOT}/data/04-24.csv"
REF_PREDS = f"{ROOT}/results/bilstm_attention_preds.csv"
OUT = f"{ROOT}/results/windows/q10_windows.npz"
FEATURES = ["mxtpr", "mntpr", "lsp", "tcc", "v10", "sp", "d2m"]
TARGET = "tp_mm"
END_TIME = pd.Timestamp("2021-12-31 18:00:00")
WINDOW = 6

os.makedirs(os.path.dirname(OUT), exist_ok=True)
if os.path.exists(OUT):
    raise SystemExit(f"{OUT} already exists. Nothing to do.")

# 1. Dublin 5x5 box, same filter as notebook Step 2A
parts = []
for ch in pd.read_csv(CSV, usecols=["valid_time", "latitude", "longitude"] + FEATURES + ["tp"],
                      chunksize=1_000_000):
    keep = ch["latitude"].between(52.75, 53.75) & ch["longitude"].between(-6.75, -5.75)
    parts.append(ch[keep])
df = pd.concat(parts, ignore_index=True)
df["valid_time"] = pd.to_datetime(df["valid_time"])
df = df[df["valid_time"] <= END_TIME]
assert df.groupby("valid_time").size().eq(25).all(), "not 25 cells per timestamp"
assert df[FEATURES + ["tp"]].isna().sum().sum() == 0, "missing values"

# 2. Regional mean, metres -> mm (Step 2B/2D)
reg = (df.groupby("valid_time", as_index=False)[FEATURES + ["tp"]].mean()
         .sort_values("valid_time").reset_index(drop=True))
reg[TARGET] = reg["tp"] * 1000.0
reg = reg.drop(columns=["tp"])
assert len(reg) == 26300, len(reg)

# 3. Chronological 70/15/15 split
n = len(reg)
train_end, val_end = int(n * 0.70), int(n * 0.85)
train_df = reg.iloc[:train_end].reset_index(drop=True)
val_df = reg.iloc[train_end:val_end].reset_index(drop=True)
test_df = reg.iloc[val_end:].reset_index(drop=True)

# 4. Train-only scaling
x_scaler, y_scaler = StandardScaler(), StandardScaler()
x_scaler.fit(train_df[FEATURES])
y_scaler.fit(train_df[[TARGET]])
for part in (train_df, val_df, test_df):
    part[FEATURES] = x_scaler.transform(part[FEATURES])
    part[TARGET + "_scaled"] = y_scaler.transform(part[[TARGET]])

# 5. Windows (identical to build_windows in Step 2D)
def build_windows(p):
    vx, vy, tt = p[FEATURES].values, p[TARGET + "_scaled"].values, p["valid_time"].values
    X = [vx[i:i + WINDOW] for i in range(len(p) - WINDOW)]
    y = [vy[i + WINDOW] for i in range(len(p) - WINDOW)]
    t = [tt[i + WINDOW] for i in range(len(p) - WINDOW)]
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32), np.array(t)

X_train, y_train, t_train = build_windows(train_df)
X_val, y_val, t_val = build_windows(val_df)
X_test, y_test, t_test = build_windows(test_df)
print("Shapes:", X_train.shape, X_val.shape, X_test.shape)
assert (X_train.shape[0], X_val.shape[0], X_test.shape[0]) == (18404, 3939, 3939)

# 6. Checks against known values
inv = lambda a: y_scaler.inverse_transform(np.asarray(a).reshape(-1, 1)).ravel()
q95_rows = float(np.quantile(train_df[TARGET].values, 0.95))
q95_win = float(np.quantile(inv(y_train), 0.95))
print(f"Train Q95 (18,410 rows) = {q95_rows:.6f} | Train Q95 (18,404 window targets) = {q95_win:.6f} "
      "| manuscript 0.5740, notebook Step 16 0.574048")
assert abs(q95_win - 0.574048) < 1e-5 or abs(q95_rows - 0.574048) < 1e-5, "Q95 does not reproduce"

if os.path.exists(REF_PREDS):
    ref = pd.read_csv(REF_PREDS, parse_dates=["valid_time"])
    ref = ref[ref["split"] == "test"].reset_index(drop=True)
    assert (pd.to_datetime(t_test) == ref["valid_time"].values).all(), "test timestamps differ"
    d = np.abs(inv(y_test) - ref["y_true"].values).max()
    print(f"max |y_true - saved y_true| on test = {d:.2e} mm")
    assert d < 1e-5, "targets do not match saved predictions"
else:
    print("WARNING: reference predictions not found, target check skipped")

np.savez_compressed(
    OUT,
    X_train=X_train, y_train=y_train, t_train=t_train.astype(str),
    X_val=X_val, y_val=y_val, t_val=t_val.astype(str),
    X_test=X_test, y_test=y_test, t_test=t_test.astype(str),
    features=np.array(FEATURES),
    y_mean=np.ravel(y_scaler.mean_), y_scale=np.ravel(y_scaler.scale_),
)
print("Saved:", OUT)
print("===== q10 PREPARE COMPLETE =====")
