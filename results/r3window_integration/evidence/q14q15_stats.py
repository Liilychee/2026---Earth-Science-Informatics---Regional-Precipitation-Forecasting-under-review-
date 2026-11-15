# ============================================================
# Items 14 and 15 statistics (main 70/15/15 split, five seeds; outputs of q14q15_train.py).
#   14: 12 h (W = 3) vs 30 h (W = 6) input history, six models. Both windows are scored on the
#       common test time stamps (the 3,939 targets of W = 6).
#   15: Huber loss (delta 0.5, 1, 2 in standardized units) vs MSE for BiLSTM-Attention and Transformer
#       (MSE = W = 6 runs of item 14). delta selected per model by the mean validation RMSE over seeds;
#       all deltas are reported.
# For every comparison: RMSE overall / wet (>= 0.1) / upper (>= Q95 = 0.574048), bias and maximum
# prediction; seed-paired differences with seed t 95% interval and number of seeds improved; paired
# moving-block bootstrap of the seed-averaged squared errors (28-sample = 7-day blocks, 5,000 replicates,
# seed 42); reproduction check of W = 6 against the main study.
# Outputs: results/metrics/q14_runs.csv, q14_window_effect.csv, q15_runs.csv, q15_delta_selection.csv,
#          q15_loss_effect.csv, q14q15_stats_output.txt
# ============================================================
import json, os
import numpy as np
import pandas as pd
from scipy.stats import t as tdist

ROOT = os.environ.get("Q14_ROOT", "/root/autodl-tmp")
IN, MET = f"{ROOT}/results/q14", f"{ROOT}/results/metrics"
SEEDS = [42, 123, 7, 2024, 99]
Q95, WET = 0.574048, 0.1
N_BOOT, BSEED, BLOCK = 5000, 42, 28
LAB = {"xgboost": "XGBoost", "bulstm": "BU-LSTM", "bilstm_attn": "BiLSTM-Attention", "transformer": "Transformer",
       "bulstm_attn": "BU-LSTM-Attention", "prob_bilstm_attn": "Probabilistic BiLSTM-Attention"}
BASE_LOSS = {"xgboost": "tree", "bulstm": "nll", "bulstm_attn": "nll", "prob_bilstm_attn": "nll",
             "bilstm_attn": "mse", "transformer": "mse"}
REPRO = {("xgboost", 42): 0.243750, ("bilstm_attn", 42): 0.242848, ("bulstm_attn", 42): 0.246413}
DELTAS = ["huber0.5", "huber1", "huber2"]
lines = []
pd.set_option("display.width", 250)


def say(s=""):
    print(s); lines.append(str(s))


def load(model, w, loss, s):
    df = pd.read_csv(f"{IN}/preds/{model}__w{w}__{loss}__s{s}.csv", parse_dates=["valid_time"])
    return df


def metrics(y, p):
    out = {}
    for tag, mk in (("all", np.ones(len(y), bool)), ("wet", y >= WET), ("upper", y >= Q95)):
        e = p[mk] - y[mk]
        out[f"rmse_{tag}"] = float(np.sqrt(np.mean(e ** 2))); out[f"bias_{tag}"] = float(np.mean(e))
    out["max_pred"] = float(p.max()); out["sd_ratio"] = float(p.std() / y.std())
    return out


def seed_t(d):
    d = np.asarray(d, float); m = d.mean(); h = tdist.ppf(0.975, len(d) - 1) * d.std(ddof=1) / np.sqrt(len(d))
    return m, m - h, m + h


def boot_rmse_diff(ea, eb, masks):
    """paired moving-block bootstrap of RMSE(a) - RMSE(b); ea, eb = seed-averaged squared errors."""
    n = len(ea); rng = np.random.default_rng(BSEED); nb = int(np.ceil(n / BLOCK))
    starts = rng.integers(0, n - BLOCK + 1, size=(N_BOOT, nb))
    idx = (starts[:, :, None] + np.arange(BLOCK)[None, None, :]).reshape(N_BOOT, -1)
    res = {}
    for tag, mk in masks.items():
        m = mk[idx].astype(float); c = m.sum(1)
        bd = np.sqrt((ea[idx] * m).sum(1) / c) - np.sqrt((eb[idx] * m).sum(1) / c)
        res[tag] = (float(np.sqrt(ea[mk].mean()) - np.sqrt(eb[mk].mean())), *np.percentile(bd, [2.5, 97.5]))
    return res


def compare(a_spec, b_spec, times):
    """a_spec/b_spec = (model, window, loss). Scores on the common test times; returns rows per subset."""
    per, sea, seb, y_ref = [], 0, 0, None
    for s in SEEDS:
        A = load(*a_spec, s).query("split == 'test'").set_index("valid_time").loc[times]
        B = load(*b_spec, s).query("split == 'test'").set_index("valid_time").loc[times]
        assert np.allclose(A.y_true.values, B.y_true.values, atol=1e-6)
        y = A.y_true.values
        ma, mb = metrics(y, A.y_pred_mean.values), metrics(y, B.y_pred_mean.values)
        per.append({"seed": s, **{f"a_{k}": v for k, v in ma.items()}, **{f"b_{k}": v for k, v in mb.items()}})
        sea = sea + (A.y_pred_mean.values - y) ** 2 / len(SEEDS)
        seb = seb + (B.y_pred_mean.values - y) ** 2 / len(SEEDS)
        y_ref = y
    per = pd.DataFrame(per)
    masks = {"all": np.ones(len(y_ref), bool), "wet": y_ref >= WET, "upper": y_ref >= Q95}
    bt = boot_rmse_diff(sea, seb, masks)
    rows = []
    for tag in masks:
        d = per[f"a_rmse_{tag}"] - per[f"b_rmse_{tag}"]
        m, lo, hi = seed_t(d)
        rows.append({"subset": tag, "n": int(masks[tag].sum()),
                     "a_rmse_mean": per[f"a_rmse_{tag}"].mean(), "a_rmse_sd": per[f"a_rmse_{tag}"].std(ddof=1),
                     "b_rmse_mean": per[f"b_rmse_{tag}"].mean(), "b_rmse_sd": per[f"b_rmse_{tag}"].std(ddof=1),
                     "diff_seed_mean": m, "seed_t_low": lo, "seed_t_high": hi, "n_seeds_a_better": int((d < 0).sum()),
                     "diff_boot_point": bt[tag][0], "boot_low": bt[tag][1], "boot_high": bt[tag][2],
                     "a_bias": per[f"a_bias_{tag}"].mean(), "b_bias": per[f"b_bias_{tag}"].mean()})
    extra = {"a_max_pred": per.a_max_pred.mean(), "b_max_pred": per.b_max_pred.mean(),
             "a_sd_ratio": per.a_sd_ratio.mean(), "b_sd_ratio": per.b_sd_ratio.mean()}
    return rows, extra


def fmt(r):
    f1 = "*" if (r["seed_t_low"] > 0 or r["seed_t_high"] < 0) else " "
    f2 = "*" if (r["boot_low"] > 0 or r["boot_high"] < 0) else " "
    return (f"{r['subset']:6s} (n={r['n']:4d})  a {r['a_rmse_mean']:.4f}±{r['a_rmse_sd']:.4f}  b {r['b_rmse_mean']:.4f}±"
            f"{r['b_rmse_sd']:.4f}  Δ {r['diff_seed_mean']:+.4f} seed[{r['seed_t_low']:+.4f}, {r['seed_t_high']:+.4f}]{f1} "
            f"boot[{r['boot_low']:+.4f}, {r['boot_high']:+.4f}]{f2}  {r['n_seeds_a_better']}/5 better  "
            f"bias a {r['a_bias']:+.4f} b {r['b_bias']:+.4f}")


# ---------- run table ----------
runs = []
for f in sorted(os.listdir(f"{IN}/runs")):
    j = json.load(open(f"{IN}/runs/{f}"))
    runs.append({"model": j["model"], "window": j["window"], "loss": j["loss"], "seed": j["seed"],
                 "val_rmse": j["val"]["rmse"], "test_rmse": j["test"]["rmse"], "best_epoch": j["best_epoch"],
                 "epochs": j["epochs_trained"], "sec": j["train_seconds"]})
runs = pd.DataFrame(runs)
runs.to_csv(f"{MET}/q14_runs.csv", index=False)
say(f"runs found: {len(runs)} (expected 90)")
say("===== reproduction of the main study (W = 6, seed 42) =====")
for (m, s), ref in REPRO.items():
    v = runs[(runs.model == m) & (runs.window == 6) & (runs.seed == s) & (runs.loss == BASE_LOSS[m])].test_rmse
    say(f"  {LAB[m]:18s} {float(v.iloc[0]):.6f} vs {ref}  {'OK' if abs(float(v.iloc[0]) - ref) < 1e-5 else 'DIFFERENT'}")

# common test times = the W = 6 test targets
times = load("xgboost", 6, "tree", 42).query("split == 'test'").valid_time.values
say(f"common test time stamps: {len(times)}")

# ---------- 14 ----------
say("\n===== 14. 12 h (W = 3) minus 30 h (W = 6) input history: test RMSE, seed mean ± SD =====")
r14 = []
for m in LAB:
    rows, ex = compare((m, 3, BASE_LOSS[m]), (m, 6, BASE_LOSS[m]), times)
    say(f"-- {LAB[m]} (a = 12 h, b = 30 h) | max pred a {ex['a_max_pred']:.3f} b {ex['b_max_pred']:.3f} | "
        f"sd ratio a {ex['a_sd_ratio']:.3f} b {ex['b_sd_ratio']:.3f}")
    for r in rows:
        say("   " + fmt(r)); r14.append({"model": LAB[m], **r, **ex})
r14 = pd.DataFrame(r14)
r14.to_csv(f"{MET}/q14_window_effect.csv", index=False)
rk = r14[r14.subset == "all"].assign(r3=lambda x: x.a_rmse_mean.rank().astype(int), r6=lambda x: x.b_rmse_mean.rank().astype(int))
say("ranking by overall RMSE (12 h | 30 h): " + "; ".join(f"{r.model} {r.r3}|{r.r6}" for r in rk.itertuples()))
v = runs[runs.loss.isin(["tree", "nll", "mse"])].groupby(["model", "window"]).val_rmse.mean().unstack()
say("validation RMSE (seed mean), columns = window:\n" + v.rename(index=LAB).round(4).to_string())

# ---------- 15 ----------
say("\n===== 15. Huber vs MSE (W = 6), BiLSTM-Attention and Transformer =====")
sel = runs[(runs.window == 6) & runs.loss.isin(["mse"] + DELTAS) & runs.model.isin(["bilstm_attn", "transformer"])]
vt = sel.groupby(["model", "loss"])[["val_rmse", "test_rmse", "best_epoch"]].agg(["mean", "std"])
vt.to_csv(f"{MET}/q15_runs.csv")
say("validation / test RMSE by loss (seed mean ± SD); delta in standardized target units (SD = 0.2752 mm):")
say(vt.round(4).to_string())
r15, selrows = [], []
for m in ["bilstm_attn", "transformer"]:
    vm = sel[(sel.model == m) & sel.loss.isin(DELTAS)].groupby("loss").val_rmse.mean()
    best = vm.idxmin()
    selrows.append({"model": LAB[m], "selected_loss": best, **{f"val_{k}": v for k, v in vm.items()}})
    say(f"-- {LAB[m]}: delta selected on validation = {best} (val RMSE {vm.round(4).to_dict()})")
    for loss in DELTAS:
        rows, ex = compare((m, 6, loss), (m, 6, "mse"), times)
        tagsel = " [selected]" if loss == best else ""
        say(f"   a = {loss}{tagsel}, b = MSE | max pred a {ex['a_max_pred']:.3f} b {ex['b_max_pred']:.3f} | "
            f"sd ratio a {ex['a_sd_ratio']:.3f} b {ex['b_sd_ratio']:.3f}")
        for r in rows:
            say("      " + fmt(r)); r15.append({"model": LAB[m], "huber": loss, "selected": loss == best, **r, **ex})
pd.DataFrame(selrows).to_csv(f"{MET}/q15_delta_selection.csv", index=False)
pd.DataFrame(r15).to_csv(f"{MET}/q15_loss_effect.csv", index=False)
say("\nnotes: a negative Δ means a has lower RMSE; * = interval excludes 0; bootstrap = paired moving block, "
    f"{BLOCK} samples (7 days), {N_BOOT} replicates, seed {BSEED}, seed-averaged squared errors.")
open(f"{MET}/q14q15_stats_output.txt", "w").write("\n".join(lines) + "\n")
say("===== q14/q15 STATS COMPLETE =====")
