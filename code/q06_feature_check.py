# ============================================================
# Item 06, step 1: does each fold's own training period select the same 7 predictors?
# The main study ranked 11 candidates by |Spearman rho| with tp_mm at the same time step,
# using the training period only, and kept the top 7. Here the same rule is applied to the
# training period of every fold. Read-only; no training.
# Output: results/metrics/q06_feature_check.csv
# ============================================================
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
from q06_common import ROOT, CANDIDATES, FEATURES, TARGET, FOLDS, load_regional, split

df = load_regional()
rows = []

# reproduction of the original ranking (original training period, 70% of 2004-2021)
orig = df[df["valid_time"].dt.year >= 2004].reset_index(drop=True)
orig_train = orig.iloc[:int(len(orig) * 0.70)]
periods = {"original (2004-01 to 2016-08)": orig_train}
for f in FOLDS:
    a, b = FOLDS[f]["train"]
    periods[f"{f} train {a}-{b}"] = split(df, f)["train"]

for name, part in periods.items():
    rho = part[CANDIDATES + [TARGET]].corr(method="spearman")[TARGET].drop(TARGET)
    rank = rho.abs().sort_values(ascending=False)
    top7 = list(rank.index[:7])
    rows.append({"period": name, "n": len(part), "top7": ",".join(top7),
                 "same_set_as_main": set(top7) == set(FEATURES),
                 "rank7_feature": rank.index[6], "rank7_abs_rho": rank.iloc[6],
                 "rank8_feature": rank.index[7], "rank8_abs_rho": rank.iloc[7],
                 **{f"rho_{c}": rho[c] for c in CANDIDATES}})
out = pd.DataFrame(rows)
out.to_csv(f"{ROOT}/results/metrics/q06_feature_check.csv", index=False)
pd.set_option("display.width", 220)
print(out[["period", "n", "same_set_as_main", "rank7_feature", "rank7_abs_rho",
           "rank8_feature", "rank8_abs_rho"]].to_string(index=False, float_format=lambda v: f"{v:.3f}"))
print("\nSpearman rho with tp_mm (training period of each row):")
print(out.set_index("period")[[f"rho_{c}" for c in CANDIDATES]].T.to_string(float_format=lambda v: f"{v:+.3f}"))
print("\nmain-study set:", FEATURES)
print("===== q06 FEATURE CHECK COMPLETE =====")
