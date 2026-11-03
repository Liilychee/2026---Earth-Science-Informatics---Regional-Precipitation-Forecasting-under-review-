# ============================================================
# Step 2D — (A) Train-only feature re-selection
#            (B) Leak-free 6-hour sliding window construction
#
# Fixes audit items:
#   #9  Feature selection must use TRAIN data only, not full data
#   #8  No leakage: window features must be strictly <= t,
#       target must be strictly t+1 (next sample), never overlapping
#   #12 Confirms no interpolation is needed / no leakage from it
#
# IMPORTANT: this uses ALL raw candidate variables (not just the
# 7 that were pre-selected in the ORIGINAL notebook using full-
# data Spearman correlation). That original selection was itself
# a leakage risk (#9), so we redo it here honestly on train-only
# data, using df_complete from Step 2B which still has all raw
# columns before the old narrowing to `required_cols`.
# ============================================================
import pandas as pd
import numpy as np
from scipy.stats import spearmanr

# ------------------------------------------------------------
# 0. Re-aggregate regional means using ALL candidate variables
#    (df_complete comes from Step 2B, filtered to 2004-2021,
#    Dublin 5x5 subset, BEFORE it was narrowed to the 7 features)
# ------------------------------------------------------------
ALL_CANDIDATES = [
    'u10', 'v10', 'd2m', 't2m', 'sp', 'e',
    'mxtpr', 'mntpr', 'tcc', 'ssr', 'lsp'
]
TARGET_RAW = 'tp'

# REVISION: read the already regional-averaged file produced by
# reduce_big_era5_csv.py (Dublin 5x5 = 25 cells averaged per timestamp,
# 2004-2021). No df_complete / notebook state needed any more.
import os
DATA_CANDIDATES = [
    "data/dublin_regional_reduced.csv",
    "../data/dublin_regional_reduced.csv",
    "dublin_regional_reduced.csv",
]
DATA_PATH = next((p for p in DATA_CANDIDATES if os.path.exists(p)), None)
assert DATA_PATH, (
    "dublin_regional_reduced.csv not found. Run this script from the "
    "repository root (the folder that contains data/)."
)
df_in = pd.read_csv(DATA_PATH, parse_dates=['valid_time'])

missing_cols = [c for c in ALL_CANDIDATES + [TARGET_RAW] if c not in df_in.columns]
assert not missing_cols, f"Missing expected raw columns: {missing_cols}"

print("===== 0. LOADING REGIONAL-MEAN FILE (25 cells already averaged) =====")
print("Source:", DATA_PATH)
assert df_in[ALL_CANDIDATES + [TARGET_RAW]].isna().sum().sum() == 0, \
    "Unexpected missing values in candidate columns — investigate before proceeding."
assert not df_in['valid_time'].duplicated().any(), "Duplicate timestamps."

df_regional_full = (
    df_in[['valid_time'] + ALL_CANDIDATES + [TARGET_RAW]]
    .sort_values('valid_time')
    .reset_index(drop=True)
)
# tp is in metres in ERA5 -> mm (done once, here)
df_regional_full['tp_mm'] = df_regional_full[TARGET_RAW] * 1000.0
df_regional_full = df_regional_full.drop(columns=[TARGET_RAW])
assert len(df_regional_full) == 26300, \
    f"Expected 26300 rows, got {len(df_regional_full)}"

print("Shape:", df_regional_full.shape)
print("Range:", df_regional_full['valid_time'].min(), "->", df_regional_full['valid_time'].max())

# ------------------------------------------------------------
# 1. Chronological 70/15/15 split (identical boundaries to Step 2C)
# ------------------------------------------------------------
n = len(df_regional_full)
train_end = int(n * 0.70)
val_end = int(n * 0.85)

train_full = df_regional_full.iloc[:train_end].copy()
val_full = df_regional_full.iloc[train_end:val_end].copy()
test_full = df_regional_full.iloc[val_end:].copy()

print("\n===== 1. SPLIT (for feature selection) =====")
for name, part in [('Train', train_full), ('Validation', val_full), ('Test', test_full)]:
    print(f"{name}: {len(part)} rows | {part['valid_time'].min()} -> {part['valid_time'].max()}")

# ------------------------------------------------------------
# 2. Spearman correlation — TRAIN ONLY
#    This is the corrected version of the original Fig. 2,
#    computed without touching val/test.
# ------------------------------------------------------------
print("\n===== 2. TRAIN-ONLY SPEARMAN CORRELATION WITH tp_mm =====")
corr_cols = ALL_CANDIDATES + ['tp_mm']
train_corr = train_full[corr_cols].corr(method='spearman')
tp_corr = train_corr['tp_mm'].drop('tp_mm').sort_values(key=abs, ascending=False)
print(tp_corr.round(3))

print("\n===== FULL TRAIN-ONLY SPEARMAN MATRIX =====")
print(train_corr.round(2))

# ------------------------------------------------------------
# 2b. Save to results/features/ — this is the ONLY source Fig. 2
#     should be plotted from downstream. Plotting scripts must
#     never recompute correlations themselves.
# ------------------------------------------------------------
import os
RESULTS_FEATURES_DIR = "/root/autodl-tmp/results/features"
os.makedirs(RESULTS_FEATURES_DIR, exist_ok=True)
train_corr_path = os.path.join(RESULTS_FEATURES_DIR, "train_only_spearman.csv")
train_corr.to_csv(train_corr_path)
print(f"\nSaved train-only Spearman matrix to: {train_corr_path}")

# ------------------------------------------------------------
# 3. Compare against the ORIGINAL (full-data, leaky) selection
#    Original selected set: mxtpr, mntpr, lsp, tcc, v10, u10, d2m
# ------------------------------------------------------------
ORIGINAL_SELECTION = ['mxtpr', 'mntpr', 'lsp', 'tcc', 'v10', 'u10', 'd2m']
print("\n===== 3. ORIGINAL (FULL-DATA) SELECTION vs TRAIN-ONLY RANKING =====")
print("Original selected features:", ORIGINAL_SELECTION)
print("\nTrain-only |Spearman| ranking (all candidates, descending):")
print(tp_corr.abs().sort_values(ascending=False).round(3))
print(
    "\n>>> Manually compare: do the top-7 by |correlation| on TRAIN-ONLY "
    "match ORIGINAL_SELECTION? If not, decide whether to switch feature "
    "sets (changes Table 1 / Fig. 2 / all downstream SHAP) or keep the "
    "original set with a documented justification (e.g. physical "
    "relevance beyond raw correlation magnitude). <<<"
)

# ------------------------------------------------------------
# 4. FINALIZE feature set
#    CONFIRMED DECISION: swap u10 (|corr|=0.006, ~noise) for
#    sp (|corr|=0.428, physically well-motivated — low pressure
#    systems associate with precipitation). See train-only
#    ranking in Section 3 above.
# ------------------------------------------------------------
FINAL_FEATURES = ['mxtpr', 'mntpr', 'lsp', 'tcc', 'v10', 'sp', 'd2m']
TARGET = 'tp_mm'

print(f"\n===== 4. FINAL FEATURES USED GOING FORWARD =====\n{FINAL_FEATURES}")

# ------------------------------------------------------------
# 5. Rebuild train/val/test with only the finalized columns
# ------------------------------------------------------------
train_df = train_full[['valid_time'] + FINAL_FEATURES + [TARGET]].reset_index(drop=True)
val_df = val_full[['valid_time'] + FINAL_FEATURES + [TARGET]].reset_index(drop=True)
test_df = test_full[['valid_time'] + FINAL_FEATURES + [TARGET]].reset_index(drop=True)

# ------------------------------------------------------------
# 6. Scaler — fit on TRAIN only (unchanged principle from Step 2C)
# ------------------------------------------------------------
from sklearn.preprocessing import StandardScaler

x_scaler = StandardScaler()
y_scaler = StandardScaler()
x_scaler.fit(train_df[FINAL_FEATURES])
y_scaler.fit(train_df[[TARGET]])

for name, part in [('train_df', train_df), ('val_df', val_df), ('test_df', test_df)]:
    part[FINAL_FEATURES] = x_scaler.transform(part[FINAL_FEATURES])
    part[TARGET + '_scaled'] = y_scaler.transform(part[[TARGET]])

print("\n===== 6. SCALING CHECK =====")
print("Train scaled feature means (~0 expected):",
      np.round(train_df[FINAL_FEATURES].mean().values, 4))
print("Train scaled feature stds (~1 expected):",
      np.round(train_df[FINAL_FEATURES].std().values, 4))

# ------------------------------------------------------------
# 7. Leak-free 6-hour sliding window construction
#    X[t-5, ..., t] -> y[t+1]  (each step 6 hours apart)
#    Built SEPARATELY per split so no window ever crosses a
#    split boundary.
# ------------------------------------------------------------
WINDOW = 6

def build_windows(df_part, features, target_col):
    """
    df_part must be sorted chronologically with no internal gaps.
    Returns X of shape (N, WINDOW, n_features), y of shape (N,),
    and the target timestamps for traceability.
    """
    values_X = df_part[features].values
    values_y = df_part[target_col].values
    times = df_part['valid_time'].values

    X_list, y_list, t_list = [], [], []
    # window covers indices [i, i+WINDOW-1] as input (t-5..t)
    # target is index i+WINDOW (i.e. t+1)
    for i in range(len(df_part) - WINDOW):
        X_list.append(values_X[i:i + WINDOW])
        y_list.append(values_y[i + WINDOW])
        t_list.append(times[i + WINDOW])

    return (
        np.array(X_list, dtype=np.float32),
        np.array(y_list, dtype=np.float32),
        np.array(t_list),
    )

# Explicit continuity check per split before windowing — a gap
# inside a split would silently create a window that spans a
# real time discontinuity.
for name, part in [('train', train_df), ('val', val_df), ('test', test_df)]:
    diffs = pd.Series(pd.to_datetime(part['valid_time'])).diff().dropna()
    assert (diffs == pd.Timedelta(hours=6)).all(), (
        f"{name}_df is not strictly 6-hourly contiguous — "
        f"unexpected gap found. Investigate before windowing."
    )

X_train, y_train, t_train = build_windows(train_df, FINAL_FEATURES, TARGET + '_scaled')
X_val, y_val, t_val = build_windows(val_df, FINAL_FEATURES, TARGET + '_scaled')
X_test, y_test, t_test = build_windows(test_df, FINAL_FEATURES, TARGET + '_scaled')

print("\n===== 7. WINDOWED SHAPES =====")
print("X_train:", X_train.shape, "y_train:", y_train.shape)
print("X_val:  ", X_val.shape, "y_val:  ", y_val.shape)
print("X_test: ", X_test.shape, "y_test: ", y_test.shape)

print("\n===== 7b. TARGET TIME RANGES (for later Fig. 4/5 sanity checks) =====")
print("Train targets:", pd.to_datetime(t_train).min(), "->", pd.to_datetime(t_train).max())
print("Val targets:  ", pd.to_datetime(t_val).min(), "->", pd.to_datetime(t_val).max())
print("Test targets: ", pd.to_datetime(t_test).min(), "->", pd.to_datetime(t_test).max())

# ------------------------------------------------------------
# 8. Leakage spot-check: confirm target timestamp is always
#    exactly 6h after the last feature timestamp in its window
# ------------------------------------------------------------
print("\n===== 8. LEAKAGE SPOT-CHECK (train, first 3 windows) =====")
for i in range(3):
    window_times = train_df['valid_time'].iloc[i:i + WINDOW].values
    target_time = train_df['valid_time'].iloc[i + WINDOW]
    gap = pd.to_datetime(target_time) - pd.to_datetime(window_times[-1])
    print(f"Window {i}: last feature time = {window_times[-1]}, "
          f"target time = {target_time}, gap = {gap}")
assert gap == pd.Timedelta(hours=6), "Gap between window end and target is not 6h!"

print("\n===== STEP 2D COMPLETE =====")
print("X_train/X_val/X_test and y_train/y_val/y_test are ready for modeling.")
print("Report back: Section 2 (train-only correlations), Section 3 comparison, "
      "and confirm whether FINAL_FEATURES should change.")

# ------------------------------------------------------------
# 9. PERSIST everything to disk — so future kernel restarts only
#    need to run load_pipeline_state.py (fast, no raw-data
#    re-processing) instead of re-running this entire script.
# ------------------------------------------------------------
import pickle

WINDOWS_DIR = "/root/autodl-tmp/results/windows"
os.makedirs(WINDOWS_DIR, exist_ok=True)

# a) train/val/test dataframes (unscaled + scaled columns, valid_time)
train_df.to_csv(os.path.join(WINDOWS_DIR, "train_df.csv"), index=False)
val_df.to_csv(os.path.join(WINDOWS_DIR, "val_df.csv"), index=False)
test_df.to_csv(os.path.join(WINDOWS_DIR, "test_df.csv"), index=False)

# b) windowed arrays + target timestamps
np.savez(
    os.path.join(WINDOWS_DIR, "windowed_arrays.npz"),
    X_train=X_train, y_train=y_train, t_train=t_train.astype(str),
    X_val=X_val, y_val=y_val, t_val=t_val.astype(str),
    X_test=X_test, y_test=y_test, t_test=t_test.astype(str),
)

# c) scalers + final feature list
with open(os.path.join(WINDOWS_DIR, "scalers_and_features.pkl"), "wb") as f:
    pickle.dump({
        "x_scaler": x_scaler,
        "y_scaler": y_scaler,
        "FINAL_FEATURES": FINAL_FEATURES,
        "TARGET": TARGET,
        "WINDOW": WINDOW,
    }, f)

print(f"\n===== PERSISTED STEP 2D STATE TO DISK =====\n{WINDOWS_DIR}")
print("From now on, after any kernel restart, just run "
      "load_pipeline_state.py instead of re-running this whole script.")
