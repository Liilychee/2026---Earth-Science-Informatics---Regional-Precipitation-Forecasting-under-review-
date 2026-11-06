# ============================================================
# Item 06, step 3: statistics of the rolling-origin analysis (zero training).
#   Q1 training history : fold 4 (1992-2016) vs fold 4' (2004-2016), identical test samples 2019-2021,
#                         paired by seed; subsets all / wet >= 0.1 / upper >= 0.5740 (main-study Q95)
#   Q2 stability        : per test period (2010-12, 2013-15, 2016-18, 2019-21) RMSE, skill, events;
#                         model ranking agreement between folds (Kendall tau)
#   Q3 reliability      : paired moving-block bootstrap of RMSE differences, per fold and pooled
#                         over the 12 test years 2010-2021; block 28 samples (7 days) as the main
#                         setting, 56 (14 days) and 120 (30 days) as sensitivity
# Reference forecasts are refitted on the training years of each fold: persistence,
# month-by-hour climatology, AR(1) (y(t+6h) = a + b y(t), least squares).
# Event scores use the fixed rule "forecast >= threshold" (as item 05); upper threshold = the
# training-period Q95 of each fold.
# Outputs: results/metrics/q06_run_metrics.csv, q06_fold_metrics.csv, q06_history_effect.csv,
#          q06_rank_stability.csv, q06_pairwise.csv, q06_block_sensitivity.csv
# ============================================================
import glob, json, os, sys
from itertools import combinations
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from scipy.stats import kendalltau, norm, t as tdist
from q06_common import ROOT, TARGET, WINDOW, SEEDS, FOLDS, load_regional, split

OUT, MET = f"{ROOT}/results/q06", f"{ROOT}/results/metrics"
MODELS = ["xgboost", "bulstm", "bilstm_attn", "transformer", "bulstm_attn", "prob_bilstm_attn"]
LABEL = {"xgboost": "XGBoost", "bulstm": "BU-LSTM", "bilstm_attn": "BiLSTM-Attention", "transformer": "Transformer",
         "bulstm_attn": "BU-LSTM-Attention", "prob_bilstm_attn": "Probabilistic BiLSTM-Attention",
         "persistence": "Persistence", "clim": "Climatology (month x hour)", "ar1": "AR(1)"}
REFS = ["persistence", "clim", "ar1"]
ROLL = ["F1", "F2", "F3", "F4"]
Q95_MAIN, WET = 0.574048, 0.1
N_BOOT, BSEED, BLOCK = 5000, 42, 28
pd.set_option("display.width", 230)

# ---------- load predictions ----------
runs = [json.load(open(p)) for p in glob.glob(f"{OUT}/runs/F*.json")]
assert len(runs) == 150, f"expected 150 runs, found {len(runs)}"
df = load_regional()
T, Y, P, S, E, Q = {}, {}, {}, {}, {}, {}
for f in FOLDS:
    Q[f] = json.load(open(f"{OUT}/folds/{f}.json"))["q95_train"]
    for m in MODELS:
        for s in SEEDS:
            d = pd.read_csv(f"{OUT}/preds/{f}__{m}__s{s}.csv", parse_dates=["valid_time"])
            d = d[d["split"] == "test"].reset_index(drop=True)
            if f not in T:
                T[f], Y[f], P[f] = d["valid_time"].values, d["y_true"].values, d["persistence"].values
            assert (d["valid_time"].values == T[f]).all() and np.abs(d["y_true"].values - Y[f]).max() < 1e-6
            E[(f, m, s)] = d["y_pred_mean"].values - Y[f]
            S[(f, m, s)] = d["y_pred_std"].values
    # references fitted on the training years of this fold
    tr = split(df, f)["train"]
    y_t, y_prev = tr[TARGET].values[WINDOW:], tr[TARGET].values[WINDOW - 1:-1]
    b, a = np.polyfit(y_prev, y_t, 1)
    tt = pd.to_datetime(tr["valid_time"].values[WINDOW:])
    clim = pd.Series(y_t).groupby([tt.month, tt.hour]).mean()
    te = pd.to_datetime(T[f])
    E[(f, "persistence", 0)] = P[f] - Y[f]
    E[(f, "clim", 0)] = clim.reindex(list(zip(te.month, te.hour))).values - Y[f]
    E[(f, "ar1", 0)] = (a + b * P[f]) - Y[f]
    print(f"{f}: test {pd.Timestamp(T[f][0])} -> {pd.Timestamp(T[f][-1])}, n={len(Y[f])}, "
          f"train Q95={Q[f]:.4f}, AR(1) y = {a:.4f} + {b:.4f} y(t)")
seeds_of = lambda m: SEEDS if m in MODELS else [0]


# ---------- per-run metrics ----------
def metrics(f, m, s):
    e, y = E[(f, m, s)], Y[f]
    p = y + e
    r = {"rmse": np.sqrt(np.mean(e ** 2)), "mae": np.mean(np.abs(e)), "bias": np.mean(e),
         "r2": 1 - np.sum(e ** 2) / np.sum((y - y.mean()) ** 2)}
    r["skill"] = 1 - r["rmse"] / np.sqrt(np.mean(E[(f, "clim", 0)] ** 2))
    for tag, thr in (("wet", WET), ("upper", Q[f])):
        mk = y >= thr
        r[f"rmse_{tag}"] = np.sqrt(np.mean(e[mk] ** 2))
        o, fc = mk, p >= thr
        h, fa, mi = (o & fc).sum(), (~o & fc).sum(), (o & ~fc).sum()
        r[f"pod_{tag}"] = h / (h + mi) if h + mi else np.nan
        r[f"far_{tag}"] = fa / (h + fa) if h + fa else np.nan
        r[f"csi_{tag}"] = h / (h + fa + mi) if h + fa + mi else np.nan
    sd = S.get((f, m, s))
    if sd is not None and np.isfinite(sd).all():
        z = e / sd
        r["cov95"] = np.mean(np.abs(z) <= 1.959964)
        r["crps"] = np.mean(sd * (z * (2 * norm.cdf(z) - 1) + 2 * norm.pdf(z) - 1 / np.sqrt(np.pi)))
    return r


rows = [{"fold": f, "forecast": m, "seed": s, **metrics(f, m, s)}
        for f in FOLDS for m in MODELS + REFS for s in seeds_of(m)]
run_df = pd.DataFrame(rows)
run_df.to_csv(f"{MET}/q06_run_metrics.csv", index=False)
cols = [c for c in run_df.columns if c not in ("fold", "forecast", "seed")]
g = run_df.groupby(["fold", "forecast"])[cols]
fold_df = g.mean().add_suffix("_mean").join(g.std(ddof=1).add_suffix("_sd")).reset_index()
fold_df["label"] = fold_df["forecast"].map(LABEL)
fold_df.to_csv(f"{MET}/q06_fold_metrics.csv", index=False)

print("\n===== Q2: test RMSE (seed mean +/- SD) and skill vs month-by-hour climatology, per test period =====")
for metric in ("rmse", "skill", "rmse_upper", "csi_upper"):
    tab = fold_df.pivot(index="forecast", columns="fold", values=f"{metric}_mean").loc[MODELS + REFS, ROLL + ["F4s"]]
    sd = fold_df.pivot(index="forecast", columns="fold", values=f"{metric}_sd").loc[MODELS + REFS, ROLL + ["F4s"]]
    print(f"\n-- {metric} --")
    print(pd.DataFrame({c: [f"{tab.loc[i, c]:.4f}" + (f" ± {sd.loc[i, c]:.4f}" if pd.notna(sd.loc[i, c]) else "")
                            for i in tab.index] for c in tab.columns}, index=[LABEL[i] for i in tab.index]).to_string())
prob = fold_df[fold_df["cov95_mean"].notna()]
if len(prob):
    print("\n-- probabilistic models: 95% coverage and CRPS (seed mean) --")
    print(prob.pivot(index="label", columns="fold", values="cov95_mean").to_string(float_format=lambda v: f"{v:.3f}"))
    print(prob.pivot(index="label", columns="fold", values="crps_mean").to_string(float_format=lambda v: f"{v:.4f}"))

# ---------- block bootstrap helpers ----------
def make_starts(n, block, rng):
    return rng.integers(0, n - block + 1, size=(N_BOOT, int(np.ceil(n / block))))


def boot_rmse(e, mask, starts, block):
    cs_e = np.concatenate([[0.0], np.cumsum(np.where(mask, e ** 2, 0.0))])
    cs_m = np.concatenate([[0.0], np.cumsum(mask.astype(float))])
    return np.sqrt((cs_e[starts + block] - cs_e[starts]).sum(1) / np.maximum((cs_m[starts + block] - cs_m[starts]).sum(1), 1))


def rmse_m(e, mask):
    return float(np.sqrt(np.mean(e[mask] ** 2)))


# ---------- Q1: training history (F4 vs F4s) ----------
assert (T["F4"] == T["F4s"]).all() and np.abs(Y["F4"] - Y["F4s"]).max() < 1e-6, "F4 and F4s test samples differ"
y4 = Y["F4"]
subs = {"all": np.ones(len(y4), bool), "wet_ge0.1": y4 >= WET, "upper_geQ95main": y4 >= Q95_MAIN}
starts4 = make_starts(len(y4), BLOCK, np.random.default_rng(BSEED))
tcrit = tdist.ppf(0.975, df=len(SEEDS) - 1)
h_rows = []
for m in MODELS + ["clim", "ar1"]:
    for sub, mk in subs.items():
        ss = seeds_of(m)
        d = np.array([rmse_m(E[("F4", m, s)], mk) - rmse_m(E[("F4s", m, s)], mk) for s in ss])
        db = np.mean([boot_rmse(E[("F4", m, s)], mk, starts4, BLOCK) - boot_rmse(E[("F4s", m, s)], mk, starts4, BLOCK)
                      for s in ss], axis=0)
        lo, hi = np.percentile(db, [2.5, 97.5])
        sd = d.std(ddof=1) if len(d) > 1 else np.nan
        h_rows.append({"forecast": m, "subset": sub, "n": int(mk.sum()),
                       "rmse_F4s_13y": np.mean([rmse_m(E[("F4s", m, s)], mk) for s in ss]),
                       "rmse_F4_25y": np.mean([rmse_m(E[("F4", m, s)], mk) for s in ss]),
                       "dRMSE_F4_minus_F4s": d.mean(), "sd_seeds": sd,
                       "seed_t_low": d.mean() - tcrit * sd / np.sqrt(len(d)) if len(d) > 1 else np.nan,
                       "seed_t_high": d.mean() + tcrit * sd / np.sqrt(len(d)) if len(d) > 1 else np.nan,
                       "n_seeds_better_with_25y": int((d < 0).sum()), "boot_low": lo, "boot_high": hi,
                       "boot_significant": bool(lo > 0 or hi < 0)})
hist = pd.DataFrame(h_rows)
hist.to_csv(f"{MET}/q06_history_effect.csv", index=False)
print("\n===== Q1: effect of a longer training history (fold 4, 25 y) vs (fold 4', 13 y); negative = 25 y better =====")
print(hist.assign(forecast=hist.forecast.map(LABEL)).to_string(index=False, float_format=lambda v: f"{v:+.5f}"))

# ---------- Q2: ranking stability ----------
rk = fold_df[fold_df.forecast.isin(MODELS)].pivot(index="forecast", columns="fold", values="rmse_mean")
r_rows = []
for a_, b_ in combinations(ROLL, 2):
    r_rows.append({"fold_a": a_, "fold_b": b_, "kendall_tau_6_models": kendalltau(rk[a_], rk[b_]).statistic})
rank_df = pd.DataFrame(r_rows)
rank_df.to_csv(f"{MET}/q06_rank_stability.csv", index=False)
print("\n===== Q2: model ranks by test RMSE in each period (1 = lowest) =====")
print(rk[ROLL].rank().rename(index=LABEL).astype(int).to_string())
print(f"Kendall tau between periods (6 models): mean {rank_df.kendall_tau_6_models.mean():.3f}, "
      f"min {rank_df.kendall_tau_6_models.min():.3f}, max {rank_df.kendall_tau_6_models.max():.3f}")
sk = fold_df[fold_df.forecast.isin(MODELS + ["ar1"])].pivot(index="forecast", columns="fold", values="skill_mean")[ROLL]
print("Skill across the four periods (min / max):")
for i in sk.index:
    print(f"  {LABEL[i]:32s} {sk.loc[i].min():+.3f} / {sk.loc[i].max():+.3f}")

# ---------- Q3: pairwise differences, per fold and pooled 2010-2021 ----------
PAIRS = [("bilstm_attn", "xgboost"), ("bulstm_attn", "bilstm_attn"), ("bulstm_attn", "xgboost")] + \
        [(m, "ar1") for m in MODELS] + [(m, "clim") for m in MODELS]


def pooled(m, s):
    return np.concatenate([E[(f, m, s)] for f in ROLL])


def pair_stats(ea_list, eb_list, mask, block, rng):
    st = make_starts(len(mask), block, rng)
    d_obs = np.mean([rmse_m(e, mask) for e in ea_list]) - np.mean([rmse_m(e, mask) for e in eb_list])
    d_bs = np.mean([boot_rmse(e, mask, st, block) for e in ea_list], axis=0) - \
           np.mean([boot_rmse(e, mask, st, block) for e in eb_list], axis=0)
    lo, hi = np.percentile(d_bs, [2.5, 97.5])
    return d_obs, lo, hi


p_rows = []
for scope in ROLL + ["pooled_2010_2021"]:
    yv = np.concatenate([Y[f] for f in ROLL]) if scope.startswith("pooled") else Y[scope]
    for sub, mk in {"all": np.ones(len(yv), bool), "wet_ge0.1": yv >= WET}.items():
        for a_, b_ in PAIRS:
            get = (lambda m: [pooled(m, s) for s in seeds_of(m)]) if scope.startswith("pooled") else \
                  (lambda m, f=scope: [E[(f, m, s)] for s in seeds_of(m)])
            d, lo, hi = pair_stats(get(a_), get(b_), mk, BLOCK, np.random.default_rng(BSEED))
            p_rows.append({"scope": scope, "subset": sub, "a": a_, "b": b_, "n": int(mk.sum()),
                           "dRMSE_a_minus_b": d, "boot_low": lo, "boot_high": hi,
                           "significant": bool(lo > 0 or hi < 0)})
pw = pd.DataFrame(p_rows)
pw.to_csv(f"{MET}/q06_pairwise.csv", index=False)
print(f"\n===== Q3: RMSE(a) - RMSE(b), seed means, block {BLOCK} (7 days), {N_BOOT} reps; negative = a better =====")
show = pw[pw.subset == "all"].copy()
show["cell"] = show.apply(lambda r: f"{r.dRMSE_a_minus_b:+.4f} [{r.boot_low:+.4f},{r.boot_high:+.4f}]{'*' if r.significant else ''}", axis=1)
show["pair"] = show.a.map(LABEL) + " - " + show.b.map(LABEL)
print(show.pivot(index="pair", columns="scope", values="cell")[ROLL + ["pooled_2010_2021"]].to_string())
print("(* = 95% interval excludes 0)")

# ---------- block-length sensitivity (pooled) ----------
yv = np.concatenate([Y[f] for f in ROLL])
mk = np.ones(len(yv), bool)
b_rows = []
for a_, b_ in [("bilstm_attn", "xgboost"), ("bilstm_attn", "ar1"), ("xgboost", "ar1"), ("bulstm_attn", "bilstm_attn")]:
    for blk, days in ((28, 7), (56, 14), (120, 30)):
        d, lo, hi = pair_stats([pooled(a_, s) for s in seeds_of(a_)], [pooled(b_, s) for s in seeds_of(b_)],
                               mk, blk, np.random.default_rng(BSEED))
        b_rows.append({"a": a_, "b": b_, "block_samples": blk, "block_days": days, "dRMSE": d,
                       "boot_low": lo, "boot_high": hi, "significant": bool(lo > 0 or hi < 0)})
bs = pd.DataFrame(b_rows)
bs.to_csv(f"{MET}/q06_block_sensitivity.csv", index=False)
print("\n===== Block-length sensitivity, pooled 2010-2021 =====")
print(bs.assign(a=bs.a.map(LABEL), b=bs.b.map(LABEL)).to_string(index=False, float_format=lambda v: f"{v:+.5f}"))

# ---------- training cost ----------
rc = pd.DataFrame([{"fold": r["fold"], "model": r["model"], "sec": r["train_seconds"], "n_train": r["n_train"],
                    "epochs": r["epochs_trained"]} for r in runs])
print("\n===== Training time per run (s, 8 jobs in parallel; XGBoost on CPU) =====")
print(rc.pivot_table(index="model", columns="fold", values="sec", aggfunc="mean").loc[MODELS, ROLL + ["F4s"]]
      .rename(index=LABEL).to_string(float_format=lambda v: f"{v:.0f}"))
print("===== q06 STATS COMPLETE =====")
