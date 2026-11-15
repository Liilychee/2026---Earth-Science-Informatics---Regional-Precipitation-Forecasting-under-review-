# ============================================================
# analysis_q05g_multiseed_events.py -- issue 05 / 10-17 follow-up, zero-training
#
# Re-runs the 05 diagnostics (q05d tail table + q05e event scores) on the FIVE-SEED predictions saved by q10_train.py:
#     results/q10/preds/<arch>__full__s<seed>.csv   (columns split, valid_time, y_true, y_pred_mean, y_pred_std)
# For every architecture that has all five seeds in config "full":
#   per seed   : RMSE/MAE/bias (all, wet>=0.1, >=Q95), prediction max and std ratio, AUC and validation-tuned-cutoff
#                POD/FAR/CSI at wet>=0.1, Q90, Q95, Q97.5, 1.0 mm/h, and fixed-cutoff (=tau) forecasts/hits
#   summary    : mean and sd over seeds (and the single-seed-42 value for comparison with the earlier single-run tables)
#   paired     : seed-AVERAGED prediction minus Persistence / month x hour climatology (and architecture minus
#                architecture when there are two or more), AUC and CSI, circular block bootstrap (28, 2,000, seed 42),
#                plus the number of seeds (of 5) in which each single seed beats Persistence.
# Thresholds are train quantiles; cutoffs are chosen on VALIDATION (300-point grid, same as q05b/q05c/q05e).
#
# Run (AutoDL):  cd /root/autodl-tmp
#   python3 code/analysis_q05g_multiseed_events.py 2>&1 | tee results/metrics/q05g_output.txt
# Outputs (results/metrics/): q05g_multiseed_per_seed.csv, q05g_multiseed_summary.csv, q05g_multiseed_paired.csv
# Optional env: NBOOT (default 2000).  Optional arg 1: config name (default full).
# ============================================================
import glob
import os
import sys
import numpy as np
import pandas as pd
from scipy.stats import rankdata

CFG = sys.argv[1] if len(sys.argv) > 1 else "full"
SEEDS = [42, 123, 7, 2024, 99]
W, BLOCK, BSEED = 6, 28, 42
NBOOT = int(os.environ.get("NBOOT", 2000))
ROOT = next(r for r in ["results", "/root/autodl-tmp/results", "../results"] if os.path.isdir(r))
PRED = os.path.join(ROOT, "q10", "preds")
MET = os.path.join(ROOT, "metrics"); os.makedirs(MET, exist_ok=True)
DATA = next(p for p in ["data/dublin_regional_reduced.csv", "../data/dublin_regional_reduced.csv",
                        "/root/autodl-tmp/data/dublin_regional_reduced.csv"] if os.path.exists(p))

df = pd.read_csv(DATA, parse_dates=["valid_time"]).sort_values("valid_time").reset_index(drop=True)
df["tp_mm"] = df["tp"] * 1000.0 if "tp" in df.columns else df["tp_mm"]
n = len(df); a, b = int(n * .70), int(n * .85)
fr = {}
for k, (i, j) in {"train": (0, a), "val": (a, b), "test": (b, n)}.items():
    p = df.iloc[i:j].reset_index(drop=True)
    t = p.iloc[W:].copy()
    t["y_lag"] = p.iloc[W - 1:len(p) - 1]["tp_mm"].to_numpy()
    t["y"] = t["tp_mm"]; t["month"] = t.valid_time.dt.month; t["hour"] = t.valid_time.dt.hour
    fr[k] = t.reset_index(drop=True)
tr, va, te = fr["train"], fr["val"], fr["test"]
yt, yv, N = te.y.to_numpy(), va.y.to_numpy(), len(te)
q95 = float(tr.y.quantile(.95))
THR = {"wet>=0.1": 0.1, "Q90": float(tr.y.quantile(.90)), "Q95": q95, "Q97.5": float(tr.y.quantile(.975)), "1.0": 1.0}
print("thresholds:", {k: round(v, 4) for k, v in THR.items()}, "| test targets", N)
assert abs(q95 - 0.5740) < 5e-4

# ---- discover architectures with all five seeds ----
archs = {}
for f in sorted(glob.glob(os.path.join(PRED, f"*__{CFG}__s*.csv"))):
    arch, _, rest = os.path.basename(f)[:-4].partition(f"__{CFG}__s")
    archs.setdefault(arch, {})[int(rest)] = f
archs = {k: v for k, v in archs.items() if all(s in v for s in SEEDS)}
print("architectures with 5 seeds in config", CFG, ":", list(archs))
assert archs, "no architecture with five seeds found"


def load(path):
    d0 = pd.read_csv(path, parse_dates=["valid_time"])
    out = {}
    for sp, ref in (("val", va), ("test", te)):
        d = d0[d0.split == sp].drop_duplicates("valid_time").sort_values("valid_time").reset_index(drop=True)
        assert len(d) == len(ref) and (d.valid_time.to_numpy() == ref.valid_time.to_numpy()).all(), (path, sp)
        assert np.allclose(d.y_true.to_numpy(), ref.y.to_numpy(), atol=1e-6), (path, sp)
        out[sp] = d.y_pred_mean.to_numpy()
    return out


P = {a_: {s: load(f) for s, f in v.items()} for a_, v in archs.items()}
clim = tr.groupby(["month", "hour"]).y.mean()
REF = {"Persistence": {"val": va.y_lag.to_numpy(), "test": te.y_lag.to_numpy()},
       "Climatology (month x hour)": {sp: np.array([clim.loc[(m, h)] for m, h in zip(r.month, r.hour)])
                                      for sp, r in (("val", va), ("test", te))}}


def rmse(p, o): return float(np.sqrt(np.mean((p - o) ** 2)))


def auc(p, pos):
    r = rankdata(p); n1 = pos.sum(); n0 = len(p) - n1
    return float((r[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def tune(pv, posv):
    cands = np.unique(np.quantile(pv, np.linspace(0.5, 0.999, 300)))
    best, bc = -1, cands[0]
    for c in cands:
        pb = pv >= c
        h, fa, mi = (pb & posv).sum(), (pb & ~posv).sum(), (~pb & posv).sum()
        csi = h / (h + fa + mi) if (h + fa + mi) else 0
        if csi > best: best, bc = csi, c
    return bc


def event_row(pv, pt):
    r = {}
    for tn, tv in THR.items():
        pos, posv = yt >= tv, yv >= tv
        c = tune(pv, posv); pb = pt >= c
        h, fa, mi = int((pb & pos).sum()), int((pb & ~pos).sum()), int((~pb & pos).sum())
        r.update({f"AUC_{tn}": auc(pt, pos), f"POD_{tn}": h / (h + mi), f"FAR_{tn}": fa / (h + fa) if (h + fa) else np.nan,
                  f"CSI_{tn}": h / (h + fa + mi), f"Fcst_{tn}": int(pb.sum()),
                  f"NpredGeTau_{tn}": int((pt >= tv).sum()), f"HitsFixed_{tn}": int(((pt >= tv) & pos).sum())})
    return r


def skill_row(pt):
    r = {"Pred_max": float(pt.max()), "Std_ratio": float(pt.std() / yt.std())}
    for nm, mk in (("all", np.ones(N, bool)), ("wet>=0.1", yt >= 0.1), (">=Q95", yt >= q95)):
        r[f"RMSE_{nm}"] = rmse(pt[mk], yt[mk]); r[f"Bias_{nm}"] = float(np.mean(pt[mk] - yt[mk]))
    r["MAE_all"] = float(np.mean(np.abs(pt - yt)))
    return r


rows = []
for a_ in P:
    for s in SEEDS:
        rows.append({"Arch": a_, "Seed": s, **skill_row(P[a_][s]["test"]), **event_row(P[a_][s]["val"], P[a_][s]["test"])})
    ens = {sp: np.mean([P[a_][s][sp] for s in SEEDS], 0) for sp in ("val", "test")}
    P[a_]["ens"] = ens
    rows.append({"Arch": a_, "Seed": "ensemble", **skill_row(ens["test"]), **event_row(ens["val"], ens["test"])})
for nm, d in REF.items():
    rows.append({"Arch": nm, "Seed": "-", **skill_row(d["test"]), **event_row(d["val"], d["test"])})
PS = pd.DataFrame(rows)
PS.to_csv(os.path.join(MET, "q05g_multiseed_per_seed.csv"), index=False)

num = [c for c in PS.columns if c not in ("Arch", "Seed")]
sm = []
for a_ in P:
    g = PS[(PS.Arch == a_) & PS.Seed.isin(SEEDS)]
    row = {"Arch": a_, "n_seeds": len(g)}
    for c in num:
        row[f"{c}_mean"] = g[c].mean(); row[f"{c}_sd"] = g[c].std(ddof=1)
    row["RMSE_all_seed42"] = float(g[g.Seed == 42].RMSE_all.iloc[0])
    sm.append(row)
SM = pd.DataFrame(sm)
SM.to_csv(os.path.join(MET, "q05g_multiseed_summary.csv"), index=False)

# ---- paired block bootstrap (ensemble vs references; arch vs arch) ----
rng = np.random.default_rng(BSEED)
st = rng.integers(0, N, size=(NBOOT, int(np.ceil(N / BLOCK))))
IDX = ((st[:, :, None] + np.arange(BLOCK)[None, None, :]) % N).reshape(NBOOT, -1)[:, :N]


def b_auc(p, pos):
    r = rankdata(p[IDX], axis=1); pb = pos[IDX]; n1 = pb.sum(1)
    return ((r * pb).sum(1) - n1 * (n1 + 1) / 2) / (n1 * (N - n1))


def b_csi(p, pos, c):
    X = (p >= c)[IDX]; Y = pos[IDX]
    h, fa, mi = (X & Y).sum(1), (X & ~Y).sum(1), (~X & Y).sum(1)
    return h / np.maximum(h + fa + mi, 1)


def bstats(pv, pt):
    d = {}
    for tn, tv in THR.items():
        pos, posv = yt >= tv, yv >= tv
        c = tune(pv, posv); pb = pt >= c
        h, fa, mi = (pb & pos).sum(), (pb & ~pos).sum(), (~pb & pos).sum()
        d[f"AUC_{tn}"] = (auc(pt, pos), b_auc(pt, pos))
        d[f"CSI_{tn}"] = (h / (h + fa + mi), b_csi(pt, pos, c))
    return d


B = {a_: bstats(P[a_]["ens"]["val"], P[a_]["ens"]["test"]) for a_ in P}
B.update({nm: bstats(d["val"], d["test"]) for nm, d in REF.items()})
prow = []
pairs = [(a_, r) for a_ in P for r in REF] + [(x, y) for i, x in enumerate(P) for y in list(P)[i + 1:]]
for x, y in pairs:
    for k in B[x]:
        d = B[x][k][1] - B[y][k][1]
        r = {"A": x, "B": y, "Metric": k, "A_minus_B": B[x][k][0] - B[y][k][0],
             "CI_low": float(np.percentile(d, 2.5)), "CI_high": float(np.percentile(d, 97.5))}
        r["CI_excludes_0"] = bool(r["CI_low"] > 0 or r["CI_high"] < 0)
        if y in REF:
            g = PS[(PS.Arch == x) & PS.Seed.isin(SEEDS)]
            ref = PS[PS.Arch == y].iloc[0][k]
            r["Seeds_above_ref_of_5"] = int((g[k] > ref).sum())
        prow.append(r)
PP = pd.DataFrame(prow)
PP.to_csv(os.path.join(MET, "q05g_multiseed_paired.csv"), index=False)

pd.set_option("display.width", 260); pd.set_option("display.max_columns", 60)
print("\n===== per seed: skill (test) =====")
print(PS[["Arch", "Seed", "Pred_max", "Std_ratio", "RMSE_all", "MAE_all", "RMSE_wet>=0.1", "RMSE_>=Q95", "Bias_>=Q95"]].round(4).to_string(index=False))
print("\n===== seed mean +- sd: events (validation-tuned cutoff) =====")
for tn in THR:
    print(f"\n--- {tn} ---")
    print(SM[["Arch"] + [f"{m}_{tn}_{s}" for m in ("AUC", "POD", "FAR", "CSI") for s in ("mean", "sd")]].round(3).to_string(index=False))
    ref = PS[PS.Arch.isin(REF)][["Arch", f"AUC_{tn}", f"POD_{tn}", f"FAR_{tn}", f"CSI_{tn}"]]
    print(ref.round(3).to_string(index=False))
print(f"\n===== paired (block {BLOCK}, {NBOOT} reps, seed {BSEED}); ensemble of five seeds =====")
print(PP.round(3).to_string(index=False))
print("\nSaved q05g_*.csv to", MET)
