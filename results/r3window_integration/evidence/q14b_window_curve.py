# ============================================================
# Item 14b: window-length curve (R4 m18 "did you test different combinations?").
# XGBoost and BiLSTM-Attention, input windows W = 2, 3, 4, 6, 8, 12 six-hourly steps
# (6, 12, 18, 30, 42 and 66 h of history), five seeds each, main 70/15/15 split.
# Runs come from q14q15_train.py (W = 3 and 6 already exist from the item 14 batch).
# All windows are scored on the common test times = test targets of the longest window (W = 12).
# For each model and window: test RMSE overall / wet (>= 0.1) / upper (>= Q95), validation RMSE,
# and the paired difference to W = 6 (seed t 95% interval, seeds better, moving-block bootstrap of
# seed-averaged squared errors, 28 samples = 7 days, 5,000 replicates, seed 42).
# Outputs: results/metrics/q14b_window_curve.csv, q14b_window_curve_output.txt
# ============================================================
import json, os
import numpy as np
import pandas as pd
from scipy.stats import t as tdist

ROOT = os.environ.get("Q14_ROOT", "/root/autodl-tmp")
IN, MET = f"{ROOT}/results/q14", f"{ROOT}/results/metrics"
SEEDS = [42, 123, 7, 2024, 99]
WINDOWS = [2, 3, 4, 6, 8, 12]
MODELS = {"xgboost": ("XGBoost", "tree"), "bilstm_attn": ("BiLSTM-Attention", "mse")}
Q95, WET = 0.574048, 0.1
N_BOOT, BSEED, BLOCK = 5000, 42, 28
lines = []


def say(s=""):
    print(s); lines.append(str(s))


def test_df(m, w, loss, s):
    df = pd.read_csv(f"{IN}/preds/{m}__w{w}__{loss}__s{s}.csv", parse_dates=["valid_time"])
    return df.query("split == 'test'").set_index("valid_time")


def val_rmse(m, w, loss, s):
    return json.load(open(f"{IN}/runs/{m}__w{w}__{loss}__s{s}.json"))["val"]["rmse"]


missing = [f"{m}__w{w}__{l}__s{s}" for m, (_, l) in MODELS.items() for w in WINDOWS for s in SEEDS
           if not os.path.exists(f"{IN}/runs/{m}__w{w}__{l}__s{s}.json")]
if missing:
    raise SystemExit(f"missing runs ({len(missing)}): {missing[:6]} ...")

times = test_df("xgboost", max(WINDOWS), "tree", 42).index
say(f"common test times (W = {max(WINDOWS)}): {len(times)}")
rng = np.random.default_rng(BSEED)
n = len(times); nb = int(np.ceil(n / BLOCK))
starts = rng.integers(0, n - BLOCK + 1, size=(N_BOOT, nb))
IDX = (starts[:, :, None] + np.arange(BLOCK)[None, None, :]).reshape(N_BOOT, -1)

rows = []
for m, (lab, loss) in MODELS.items():
    se, rm, vr = {}, {}, {}
    for w in WINDOWS:
        per, acc, y = [], 0, None
        for s in SEEDS:
            d = test_df(m, w, loss, s).loc[times]
            y = d.y_true.values; e2 = (d.y_pred_mean.values - y) ** 2
            acc = acc + e2 / len(SEEDS)
            per.append({"seed": s, "all": np.sqrt(e2.mean()), "wet": np.sqrt(e2[y >= WET].mean()),
                        "upper": np.sqrt(e2[y >= Q95].mean())})
        se[w], rm[w] = acc, pd.DataFrame(per).set_index("seed")
        vr[w] = np.array([val_rmse(m, w, loss, s) for s in SEEDS])
    masks = {"all": np.ones(n, bool), "wet": y >= WET, "upper": y >= Q95}
    say(f"\n===== {lab}: test RMSE by input history (seed mean ± SD); Δ = W − W6 =====")
    for w in WINDOWS:
        r = {"model": lab, "window": w, "history_h": 6 * (w - 1), "val_rmse_mean": vr[w].mean(), "val_rmse_sd": vr[w].std(ddof=1)}
        txt = f"W={w:2d} ({6 * (w - 1):2d} h) val {vr[w].mean():.4f} | "
        for sub, mk in masks.items():
            r[f"rmse_{sub}_mean"] = rm[w][sub].mean(); r[f"rmse_{sub}_sd"] = rm[w][sub].std(ddof=1)
            if w != 6:
                d = (rm[w][sub] - rm[6][sub]).values
                mm = d.mean(); h = tdist.ppf(0.975, 4) * d.std(ddof=1) / np.sqrt(5)
                m_ = mk[IDX].astype(float); c = m_.sum(1)
                bd = np.sqrt((se[w][IDX] * m_).sum(1) / c) - np.sqrt((se[6][IDX] * m_).sum(1) / c)
                lo, hi = np.percentile(bd, [2.5, 97.5])
                r.update({f"d_{sub}": mm, f"d_{sub}_seed_low": mm - h, f"d_{sub}_seed_high": mm + h,
                          f"d_{sub}_boot_low": lo, f"d_{sub}_boot_high": hi, f"d_{sub}_n_better": int((d < 0).sum())})
                f1 = "*" if (mm - h > 0 or mm + h < 0) else ""; f2 = "*" if (lo > 0 or hi < 0) else ""
                txt += (f"{sub} {r[f'rmse_{sub}_mean']:.4f}±{r[f'rmse_{sub}_sd']:.4f} Δ{mm:+.4f}{f1}"
                        f"[boot {lo:+.4f},{hi:+.4f}]{f2} {int((d < 0).sum())}/5 | ")
            else:
                txt += f"{sub} {r[f'rmse_{sub}_mean']:.4f}±{r[f'rmse_{sub}_sd']:.4f} (reference) | "
        say(txt); rows.append(r)
    best_val = min(WINDOWS, key=lambda w: vr[w].mean())
    best_test = min(WINDOWS, key=lambda w: rm[w]["all"].mean())
    say(f"window with lowest validation RMSE: W={best_val} ({6 * (best_val - 1)} h); "
        f"lowest test RMSE: W={best_test} ({6 * (best_test - 1)} h)")
pd.DataFrame(rows).to_csv(f"{MET}/q14b_window_curve.csv", index=False)
say("\nnotes: * = seed t interval (first) or bootstrap interval (second) excludes 0; "
    f"bootstrap = paired moving block, {BLOCK} samples, {N_BOOT} replicates, seed {BSEED}.")
open(f"{MET}/q14b_window_curve_output.txt", "w").write("\n".join(lines) + "\n")
say("===== q14b WINDOW CURVE COMPLETE =====")
