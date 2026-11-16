# ============================================================
# Item 22 / R3-19, experiment C: does a larger TRAINING sample from hourly issue times help?
# Post hoc sensitivity analysis, added on 2026-11-15 after the A/B results (q22) had been seen; specified before
# any C run. Reuses q22_train.py unchanged (data, windows, scalers, models, training protocol, seeds).
#
#   CA : inputs as A (6 snapshots, t-30 .. t every 6 h), training issue times EVERY HOUR
#   CB : inputs as B (31 hourly snapshots, t-30 .. t),   training issue times EVERY HOUR
#   training : all targets tau in 2017-2019 (any hour) whose 36-h window (30-h history + 6-h lead) lies inside
#              the training block -> about 26,200 samples instead of 4,374 (00/06/12/18 UTC only, as in A/B).
#   val/test : UNCHANGED and identical, sample by sample, to A/B (00/06/12/18 UTC targets; 2020 / 2021), so that
#              early stopping uses the same validation set and every test comparison is paired.
#   scalers  : UNCHANGED: the q22 X and y scalers fit on the 00/06/12/18 UTC training stamps (training block only),
#              applied as they are; only the number (and the hour-of-day mix) of training samples changes.
# Comparisons (q22c_stats.py): primary CB - A; exploratory decomposition CA - A, CB - CA, CB - B.
# Caveats to report: neighbouring hourly issue times are strongly autocorrelated, so the effective sample size grows
# far less than six-fold; for BiLSTM-Attention each epoch has about six times as many updates (inherent to "more
# samples"; protocol not re-tuned); training targets now include non-synoptic hours (diurnal mix).
#
# Input : data/q22/q22_hourly_boxmean_2017_2021.csv (md5 checked by q22_train.load)
# Output: results/q22c/preds/<model>__<CA|CB>__s<seed>.csv, results/q22c/runs/<same>.json
#         (results/q22 is never written; existing runs are skipped, never overwritten)
# --check : build CA/CB, run all alignment, leakage and scaler checks, print the audit; no training, no TensorFlow.
# Run (AutoDL):  cd /root/autodl-tmp
#                python3 code/q22c_train.py --check 2>&1 | tee results/metrics/q22c_check_output.txt
#                nohup python3 code/q22c_train.py > results/metrics/q22c_train_output.txt 2>&1 &
# ============================================================
import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q22_train as q22  # noqa: E402  (no TensorFlow import at module level)

OUT_C = f"{q22.ROOT}/results/q22c_smoke" if q22.SMOKE else f"{q22.ROOT}/results/q22c"
C_INPUTS = {"CA": "A", "CB": "B"}            # new config -> input layout it copies


def build_c(d, base):
    """Training set with hourly issue times; val/test are the q22 arrays themselves (same objects)."""
    ym, ys = base[1]
    base = base[0]
    feats, tgt, lead, span = q22.FEATURES, q22.TARGET, q22.LEAD_H, q22.SPAN_H
    a, b = q22.SPLITS["train"]
    blk = d.index[(d.index.year >= a) & (d.index.year <= b)]
    start, end = blk[0], blk[-1]

    # scalers: recompute from the training block's synoptic stamps and require equality with q22's
    tr = d[(d.index.year >= a) & (d.index.year <= b) & d.index.hour.isin(q22.SYN)]
    xm, xs = tr[feats].mean().to_numpy(), tr[feats].std(ddof=0).to_numpy()
    assert abs(float(tr[tgt].mean()) - ym) < 1e-12 and abs(float(tr[tgt].std(ddof=0)) - ys) < 1e-12
    assert tr.index.max() <= end and tr.index.max() < pd.Timestamp(f"{q22.SPLITS['val'][0]}-01-01")
    Xall = ((d[feats].to_numpy() - xm) / xs).astype("float32")
    yall = d[tgt].to_numpy()
    pos = {ts: i for i, ts in enumerate(d.index)}

    taus = [ts for ts in blk if ts - pd.Timedelta(hours=lead + span) >= start]
    it = np.array([pos[ts] for ts in taus])
    issue = it - lead
    rec = {"tau": np.array(taus, dtype="datetime64[ns]"), "issue": d.index.values[issue],
           "y": yall[it], "pers": yall[issue]}
    for cfg, src in C_INPUTS.items():
        offs = np.arange(-span, 1, q22.INPUTS[src])
        idx = issue[:, None] + offs[None, :]
        tin = d.index.values[idx]
        assert (tin <= d.index.values[issue][:, None]).all(), f"{cfg}: input after issue time"
        assert (tin >= np.datetime64(start)).all() and (tin <= np.datetime64(end)).all(), f"{cfg}: crosses split"
        rec[cfg], rec[cfg + "_times"] = Xall[idx], tin
    assert np.array_equal(rec["CB"][:, ::6], rec["CA"]) and np.array_equal(rec["CB_times"][:, ::6], rec["CA_times"])

    # the synoptic subset of the new training set is exactly the q22 training set (values, times, targets)
    syn = pd.DatetimeIndex(rec["tau"]).hour.isin(q22.SYN)
    bt = base["train"]
    assert np.array_equal(rec["tau"][syn], bt["tau"]) and np.array_equal(rec["y"][syn], bt["y"])
    assert np.array_equal(rec["CA"][syn], bt["A"]) and np.array_equal(rec["CB"][syn], bt["B"])
    # no training target or input reaches the validation / test period
    assert rec["tau"].max() < base["val"]["A_times"].min() and rec["tau"].max() < base["test"]["A_times"].min()

    out = {"train": rec}
    for sp in ("val", "test"):
        r = dict(base[sp])
        r["CA"], r["CB"] = base[sp]["A"], base[sp]["B"]          # identical arrays -> identical samples
        out[sp] = r
    return out, syn


def report_c(out, syn, base_out):
    tr, bt = out["train"], base_out["train"]
    q95 = float(np.quantile(bt["y"], 0.95))
    print("\n===== experiment C: training set with hourly issue times =====")
    print(f"training samples: hourly issue {len(tr['y'])} (synoptic subset {int(syn.sum())} == q22 train "
          f"{len(bt['y'])}); first target {pd.Timestamp(tr['tau'][0])}, last {pd.Timestamp(tr['tau'][-1])}")
    print(f"shapes: CA {tr['CA'].shape}, CB {tr['CB'].shape}; val {out['val']['CA'].shape[0]}, test "
          f"{out['test']['CA'].shape[0]} (unchanged)")
    y_h, y_s = tr["y"], bt["y"]
    print("training-target distribution (mm/h)   hourly-issue   synoptic (q22)")
    for lab, f in [("mean", np.mean), ("sd", np.std), ("wet >= 0.1 fraction", lambda v: np.mean(v >= 0.1)),
                   ("Q95", lambda v: np.quantile(v, 0.95)), (f">= {q95:.4f} fraction", lambda v: np.mean(v >= q95)),
                   ("max", np.max)]:
        print(f"  {lab:28s} {f(y_h):12.4f}   {f(y_s):12.4f}")
    lag1 = np.corrcoef(y_h[:-1], y_h[1:])[0, 1]
    print(f"lag-1 h autocorrelation of hourly training targets = {lag1:.3f}; neighbouring CB windows share 30 of 31 "
          f"input hours, so the effective sample size grows far less than {len(y_h) / len(y_s):.1f}x")
    r = out["train"]
    print(f"example: target {pd.Timestamp(r['tau'][1])}, issue {pd.Timestamp(r['issue'][1])}, CA inputs "
          f"{[str(pd.Timestamp(x))[5:16] for x in r['CA_times'][1]]}")
    print("checks passed: scalers equal q22's and use training stamps only; no input after the issue time; no window "
          "crosses a split; no training target/input reaches 2020-2021; CA == every 6th snapshot of CB; synoptic "
          "subset == q22 training set; val/test arrays identical to A/B")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=q22.MODELS, choices=q22.MODELS)
    ap.add_argument("--configs", nargs="+", default=list(C_INPUTS), choices=list(C_INPUTS))
    ap.add_argument("--seeds", nargs="+", type=int, default=q22.SEEDS)
    ap.add_argument("--epochs", type=int, default=2 if q22.SMOKE else 30)
    ap.add_argument("--check", action="store_true", help="build and check only; no training")
    a = ap.parse_args()
    d = q22.load()
    base = q22.build(d)
    q22.report(base[0], *base[1])
    out, syn = build_c(d, base)
    report_c(out, syn, base[0])
    if a.check:
        print("===== q22c CHECK COMPLETE (no training) =====")
        sys.exit(0)
    q22.OUT = OUT_C                                   # run_one writes here; results/q22 is never touched
    for cfg, src in C_INPUTS.items():
        q22.INPUTS[cfg] = q22.INPUTS[src]             # step_hours recorded in the run json
    ym, ys = base[1]
    for model in a.models:
        for cfg in a.configs:
            for seed in a.seeds:
                q22.run_one(out, ym, ys, model, cfg, seed, a.epochs)
    print("===== q22c TRAIN JOB COMPLETE =====")
