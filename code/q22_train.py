# ============================================================
# Item 22 (R3 L979-982; R4 m37): does a denser hourly input history help, at the same issue times, history span and
# target? Supplementary sensitivity analysis on 2017-2021 only (hourly ERA5 not available for earlier years in time).
#
#   A (6-hourly) : inputs at t-30, t-24, ..., t           (6 snapshots, the main-study sampling)
#   B (hourly)   : inputs at every hour t-30, t-29, ..., t (31 snapshots, same 30-h span)
#   issue time t : 00/06/12/18 UTC - 6 h, i.e. target stamps tau = t + 6 h at 00/06/12/18 UTC (as in the paper)
#   target       : tp_mm(tau) = ERA5 precipitation accumulated in the hour ending at tau (one hour, not 6 h)
#   predictors   : the 7 original variables mxtpr, mntpr, lsp, tcc, v10, sp, d2m (same order as the paper)
#   split        : by calendar year of the stamps: train 2017-2019, val 2020, test 2021. Windows never cross a
#                  split boundary (as in the main pipeline): a target is used only if all 31 hourly input stamps
#                  lie in the same split block, so A and B use exactly the same samples.
#   scaling      : one StandardScaler for X and one for y, fit on the 00/06/12/18 UTC stamps of the training block
#                  (the main-study rule) and applied unchanged to A and B; the two inputs differ only in sampling.
#   models       : XGBoost (A: 6 x 7 = 42 flattened features; B: 31 x 7 = 217) and BiLSTM-Attention (sequence
#                  length 6 vs 31; otherwise identical), main-study hyperparameters and training protocol
#                  (Adam 1e-3, batch 32, <= 30 epochs, EarlyStopping patience 10 on val_loss), seeds 42 123 7 2024 99.
# Pre-specified primary metric: test RMSE (MAE, wet >= 0.1 and upper-tail >= Q95 RMSE are secondary); comparison
# and bootstrap are done afterwards by q22_stats.py, not here.
#
# Input : data/q22/q22_hourly_boxmean_2017_2021.csv (q22_build_hourly.py; md5 44aa4baa89219c914dbea75c08df6ca4)
# Output: results/q22/preds/<model>__<A|B>__s<seed>.csv (val and test, mm/h), results/q22/runs/<same>.json
# --check : build A and B, run every alignment check, print the audit log; no training, no TensorFlow import.
# Q22_SMOKE=1 -> results/q22_smoke and 2 epochs; never used for results.
# Run (AutoDL):  python3 code/q22_train.py --check 2>&1 | tee results/metrics/q22_check_output.txt
#                python3 code/q22_train.py 2>&1 | tee results/metrics/q22_train_output.txt
# ============================================================
import argparse
import hashlib
import json
import os
import socket
import sys
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

ROOT = "/root/autodl-tmp" if os.path.isdir("/root/autodl-tmp") else "."
DATA = os.environ.get("Q22_DATA", f"{ROOT}/data/q22/q22_hourly_boxmean_2017_2021.csv")
DATA_MD5 = "44aa4baa89219c914dbea75c08df6ca4"
SMOKE = bool(os.environ.get("Q22_SMOKE"))
OUT = f"{ROOT}/results/q22_smoke" if SMOKE else f"{ROOT}/results/q22"
FEATURES = ["mxtpr", "mntpr", "lsp", "tcc", "v10", "sp", "d2m"]
TARGET = "tp_mm"
SEEDS = [42, 123, 7, 2024, 99]
MODELS = ["xgboost", "bilstm_attn"]
INPUTS = {"A": 6, "B": 1}                    # input step in hours; both span t-30 .. t
SPAN_H, LEAD_H = 30, 6
SPLITS = {"train": (2017, 2019), "val": (2020, 2020), "test": (2021, 2021)}
SYN = (0, 6, 12, 18)


def load():
    md5 = hashlib.md5(open(DATA, "rb").read()).hexdigest()
    assert md5 == DATA_MD5, f"{DATA}: md5 {md5} != {DATA_MD5} (rebuild with q22_build_hourly.py)"
    d = pd.read_csv(DATA, parse_dates=["valid_time"]).set_index("valid_time").sort_index()
    t = d.index
    assert len(d) == 43824 and t.is_unique and (np.diff(t.values) == np.timedelta64(1, "h")).all()
    assert not d[FEATURES + [TARGET]].isna().any().any()
    return d


def build(d):
    """Return {split: {"A": X, "B": X, "y", "tau", "issue", "pers"}} plus scalers; asserts every alignment rule."""
    tr = d[(d.index.year >= SPLITS["train"][0]) & (d.index.year <= SPLITS["train"][1]) & d.index.hour.isin(SYN)]
    xm, xs = tr[FEATURES].mean().to_numpy(), tr[FEATURES].std(ddof=0).to_numpy()     # = sklearn StandardScaler
    ym, ys = float(tr[TARGET].mean()), float(tr[TARGET].std(ddof=0))
    Xall = ((d[FEATURES].to_numpy() - xm) / xs).astype("float32")
    yall = d[TARGET].to_numpy()
    pos = {ts: i for i, ts in enumerate(d.index)}
    out = {}
    for sp, (a, b) in SPLITS.items():
        blk = d.index[(d.index.year >= a) & (d.index.year <= b)]
        start, end = blk[0], blk[-1]
        taus = [ts for ts in blk if ts.hour in SYN and ts - pd.Timedelta(hours=LEAD_H + SPAN_H) >= start]
        rec = {"tau": np.array(taus, dtype="datetime64[ns]")}
        it = np.array([pos[ts] for ts in taus])
        issue = it - LEAD_H                                                     # issue time t = tau - 6 h
        for name, step in INPUTS.items():
            offs = np.arange(-SPAN_H, 1, step)                                  # hours relative to t
            idx = issue[:, None] + offs[None, :]
            tin = d.index.values[idx]
            assert (tin <= d.index.values[issue][:, None]).all(), f"{sp} {name}: input after issue time"
            assert (tin >= np.datetime64(start)).all() and (tin <= np.datetime64(end)).all(), f"{sp} {name}: crosses split"
            assert (d.index.values[issue] == rec["tau"] - np.timedelta64(LEAD_H, "h")).all()
            rec[name] = Xall[idx]
            rec[name + "_times"] = tin
        rec["issue"] = d.index.values[issue]
        rec["y"] = yall[it]
        rec["pers"] = yall[issue]                                               # tp_mm at issue time
        # A is exactly every sixth hourly snapshot of B (same values, same times)
        assert np.array_equal(rec["B"][:, ::6], rec["A"]) and np.array_equal(rec["B_times"][:, ::6], rec["A_times"])
        out[sp] = rec
    # splits are disjoint and ordered in time
    assert out["train"]["tau"].max() < out["val"]["tau"].min() and out["val"]["tau"].max() < out["test"]["tau"].min()
    return out, (ym, ys)


def report(out, ym, ys):
    q95 = float(np.quantile(out["train"]["y"], 0.95))
    print(f"data {DATA} (md5 {DATA_MD5})\n")
    print(f"{'split':5s} {'n':>5s} {'first target':>20s} {'last target':>20s} {'wet>=0.1':>8s} {'>=Q95':>6s}"
          f" {'A shape':>12s} {'B shape':>13s} {'XGB A/B':>8s}")
    for sp, r in out.items():
        n = len(r["y"])
        print(f"{sp:5s} {n:5d} {str(pd.Timestamp(r['tau'][0])):>20s} {str(pd.Timestamp(r['tau'][-1])):>20s} "
              f"{int((r['y'] >= 0.1).sum()):8d} {int((r['y'] >= q95).sum()):6d} {str(r['A'].shape):>12s} "
              f"{str(r['B'].shape):>13s} {r['A'][0].size:4d}/{r['B'][0].size}")
    r = out["test"]
    print(f"\nexample (first test sample): target {pd.Timestamp(r['tau'][0])}, issue {pd.Timestamp(r['issue'][0])}")
    print("  A input times:", [str(pd.Timestamp(x))[5:16] for x in r["A_times"][0]])
    print("  B input times:", str(pd.Timestamp(r["B_times"][0][0]))[5:16], "...", str(pd.Timestamp(r["B_times"][0][-1]))[5:16],
          f"({r['B_times'].shape[1]} hourly)")
    print(f"\ntraining-target Q95 (this subset) = {q95:.4f} mm/h; y scaler mean {ym:.5f} sd {ys:.5f}")
    print("checks passed: same targets, issue times and labels for A and B; no input after the issue time;"
          " no window crosses a split; A == every 6th snapshot of B; splits disjoint and ordered")
    return q95


def run_one(out, ym, ys, model, inp, seed, epochs):
    import q10_train as qt                   # determinism flags are set inside q10_train before TF is imported
    import q06_train as q6
    import tensorflow as tf
    from tensorflow.keras.callbacks import EarlyStopping
    tag = f"{model}__{inp}__s{seed}"
    meta = f"{OUT}/runs/{tag}.json"
    if os.path.exists(meta):
        print(f"[skip] {tag}"); return
    sc = lambda y: ((y - ym) / ys).astype("float32")
    Xtr, ytr = out["train"][inp], sc(out["train"]["y"])
    Xva, yva = out["val"][inp], sc(out["val"]["y"])
    Xte = out["test"][inp]
    t0 = time.time()
    if model == "xgboost":
        import xgboost as xgb
        mdl = xgb.XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=6, subsample=0.8,
                               colsample_bytree=0.8, random_state=seed)
        mdl.fit(Xtr.reshape(len(Xtr), -1), ytr)
        pred = {"val": mdl.predict(Xva.reshape(len(Xva), -1)), "test": mdl.predict(Xte.reshape(len(Xte), -1))}
        best = ep = None
    else:
        qt.reset_seed(seed)
        mdl, kind = q6.build(model, Xtr.shape[1], Xtr.shape[2])
        assert kind == "mse"
        es = EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)
        h = mdl.fit(Xtr, ytr, validation_data=(Xva, yva), epochs=epochs, batch_size=32, callbacks=[es], verbose=2)
        pred = {k: mdl.predict(out[k][inp], verbose=0, batch_size=1024).ravel() for k in ("val", "test")}
        vl = h.history["val_loss"]; best, ep = int(np.argmin(vl)) + 1, len(vl)
    sec = time.time() - t0
    rows, met = [], {}
    for k in ("val", "test"):
        yt, yp = out[k]["y"], np.asarray(pred[k], "float64") * ys + ym
        rows.append(pd.DataFrame({"split": k, "valid_time": pd.to_datetime(out[k]["tau"]),
                                  "issue_time": pd.to_datetime(out[k]["issue"]), "y_true": yt, "y_pred_mean": yp,
                                  "persistence": out[k]["pers"]}))
        met[k] = {"rmse": float(np.sqrt(np.mean((yp - yt) ** 2))), "mae": float(np.mean(np.abs(yp - yt)))}
    os.makedirs(f"{OUT}/preds", exist_ok=True); os.makedirs(f"{OUT}/runs", exist_ok=True)
    pd.concat(rows, ignore_index=True).to_csv(f"{OUT}/preds/{tag}.csv", index=False)
    json.dump({"tag": tag, "model": model, "input": inp, "n_steps": int(Xtr.shape[1]), "step_hours": INPUTS[inp],
               "features": FEATURES, "seed": seed, "val": met["val"], "test": met["test"],
               "best_epoch": best, "epochs_trained": ep, "train_seconds": round(sec, 1),
               "n_train": int(len(Xtr)), "n_val": int(len(Xva)), "n_test": int(len(Xte)), "data_md5": DATA_MD5,
               "gpu": qt.gpu_name(), "tf": tf.__version__, "xgboost": __import__("xgboost").__version__,
               "host": socket.gethostname(), "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")},
              open(meta, "w"), indent=2)
    print(f"[done] {tag} | val RMSE {met['val']['rmse']:.6f} test RMSE {met['test']['rmse']:.6f} | "
          f"best epoch {best}/{ep} | {sec:.0f}s", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=MODELS, choices=MODELS)
    ap.add_argument("--inputs", nargs="+", default=list(INPUTS), choices=list(INPUTS))
    ap.add_argument("--seeds", nargs="+", type=int, default=SEEDS)
    ap.add_argument("--epochs", type=int, default=2 if SMOKE else 30)
    ap.add_argument("--check", action="store_true", help="build and check A and B only; no training")
    a = ap.parse_args()
    if not a.check:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    out, (ym, ys) = build(load())
    report(out, ym, ys)
    if a.check:
        print("===== q22 CHECK COMPLETE (no training) =====")
        sys.exit(0)
    for model in a.models:
        for inp in a.inputs:
            for seed in a.seeds:
                run_one(out, ym, ys, model, inp, seed, a.epochs)
    print("===== q22 TRAIN JOB COMPLETE =====")
