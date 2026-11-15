# ============================================================
# Item 19 (R2 M9): sensitivity of the main model comparison to hyperparameter choice.
# Purpose: test whether conclusions depend on the fixed hyperparameters of the original study,
# NOT to show that the original settings were optimal. The original settings were fixed a priori
# (no systematic search); that fact is kept in the manuscript.
# Data, split, scaling, window (W = 6), seeds and determinism are identical to the main study
# (q21_train.load_merged/split_data with the original 7 predictors; q10_train seeding).
# Selection uses VALIDATION RMSE only; the test set is reported once per final configuration.
#
# Stages (run in order; each skips runs that already exist):
#   gate    : bilstm_attn rebuilt with explicit (units, dropout, lr) at original values, 30-epoch cap,
#             seed 42 -> must reproduce 0.242848, otherwise stop (structure differs from q10_train.build).
#   search  : seed 42, 27-point grid, original setting included.
#               xgboost     : n_estimators {100,300,600} x learning_rate {0.03,0.05,0.1} x max_depth {4,6,8}
#               bilstm_attn : units {32,64,128} x lr {3e-4,1e-3,3e-3} x dropout {0.1,0.2,0.3}; cap 60, patience 10
#   recheck : top 3 by seed-42 validation RMSE re-run with seeds 123 and 7; selected = lowest mean val RMSE (3 seeds)
#   final   : selected config x 5 seeds, and the original config x 5 seeds under the same cap (reference)
#   light   : transformer, bulstm, bulstm_attn, prob_bilstm_attn; architecture unchanged;
#             lr {3e-4,1e-3,3e-3}, cap 100, patience 10; seed 42 selects lr on VALIDATION data:
#             transformer by RMSE; the three Gaussian models by mean Gaussian CRPS (their task is probabilistic).
#             Group B (original lr 1e-3, cap 100) x 5 seeds always; group C (selected lr, cap 100) x 5 seeds if different.
# Groups (separate the epoch cap from the other hyperparameters):
#   A original settings, original cap (30)   -> bilstm_attn: q21 C0 runs; light models: item-14 W = 6 runs
#   B original settings, longer cap          -> bilstm_attn cap 60; light models cap 100
#   C validation-selected settings, longer cap
#   (xgboost has no epoch cap: A = B = original config.)
# Budget note: both main models get 27 candidate configurations (a comparable number), not equal compute.
# Outputs: results/q19/runs/<model>__<cfg>__s<seed>.json (val/test metrics, config, loss history)
#          results/q19/preds/<model>__<cfg>__s<seed>.csv
#          results/q19/selection_<model>.json
# Run:  cd /root/autodl-tmp && python3 code/q19_tune.py --stage gate 2>&1 | tee results/metrics/q19_gate_output.txt
# ============================================================
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import argparse, glob, itertools, json, socket, time
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from scipy.stats import norm
import q10_train as qt                        # same import order as q14q15/q21: determinism before TF
import q06_train as q6
import tensorflow as tf
from tensorflow.keras import Model, Input
from tensorflow.keras.layers import LSTM, Bidirectional, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
from q06_common import ROOT, SEEDS
from q21_train import load_merged, split_data, ORIG

OUT = f"{ROOT}/results/q19"
REF_42 = {"xgboost": 0.243750, "bilstm_attn": 0.242848}
ORIG_CFG = {"xgboost": {"n": 100, "lr": 0.05, "depth": 6},
            "bilstm_attn": {"units": 64, "lr": 1e-3, "dropout": 0.2}}
GRID = {"xgboost": [{"n": n, "lr": lr, "depth": dp} for n, lr, dp in
                    itertools.product([100, 300, 600], [0.03, 0.05, 0.1], [4, 6, 8])],
        "bilstm_attn": [{"units": u, "lr": lr, "dropout": dr} for u, lr, dr in
                        itertools.product([32, 64, 128], [3e-4, 1e-3, 3e-3], [0.1, 0.2, 0.3])]}
CAP = {"bilstm_attn": 60, "light": 100}
LIGHT = ["transformer", "bulstm", "bulstm_attn", "prob_bilstm_attn"]
LIGHT_LR = [3e-4, 1e-3, 3e-3]
PROB = ["bulstm", "bulstm_attn", "prob_bilstm_attn"]


def crps_gauss(y, mu, sd):
    z = (y - mu) / sd
    return sd * (z * (2 * norm.cdf(z) - 1) + 2 * norm.pdf(z) - 1 / np.sqrt(np.pi))


def tag_of(model, cfg, cap=None):
    if model == "xgboost":
        return f"xgboost__n{cfg['n']}_lr{cfg['lr']:g}_d{cfg['depth']}"
    if model == "bilstm_attn":
        return f"bilstm_attn__u{cfg['units']}_lr{cfg['lr']:g}_dr{cfg['dropout']:g}_cap{cap}"
    return f"{model}__lr{cfg['lr']:g}_cap{cap}"


def build_bilstm_attn(T, F, units, dropout, lr):
    """Identical to q10_train.build("bilstm_attn") (same layers, order, name, compile) with units/dropout/lr as arguments."""
    inputs = Input(shape=(T, F))
    h = Bidirectional(LSTM(units, return_sequences=True))(inputs)
    h = Dropout(dropout)(h)
    context, _ = qt.TemporalAttention(attn_units=64)(h)
    m = Model(inputs, Dense(1)(context), name="BiLSTM_Attention")
    m.compile(optimizer=Adam(learning_rate=lr), loss="mse")
    return m, "mse"


def set_lr(m, lr):
    v = m.optimizer.learning_rate          # Keras 3: the optimizer's learning-rate variable
    v.assign(lr)
    got = float(v.numpy()) if hasattr(v, "numpy") else float(np.asarray(v))
    assert abs(got - lr) <= 1e-6 * lr, f"learning rate not set: {got} vs {lr}"


def run(d, model, cfg, seed, cap=None):
    tag = f"{tag_of(model, cfg, cap)}__s{seed}"
    path = f"{OUT}/runs/{tag}.json"
    if os.path.exists(path):
        print(f"[skip] {tag}", flush=True)
        return json.load(open(path))
    (Xtr, ytr, _, _), (Xva, yva, tva, pva), (Xte, yte, tte, pte) = d["train"], d["val"], d["test"]
    inv = lambda a: np.asarray(a, dtype="float64").ravel() * d["y_scale"] + d["y_mean"]
    t0, hist_d, best, ep, sdv = time.time(), None, None, None, {"val": None, "test": None}
    if model == "xgboost":
        import xgboost as xgb
        m = xgb.XGBRegressor(n_estimators=cfg["n"], learning_rate=cfg["lr"], max_depth=cfg["depth"],
                             subsample=0.8, colsample_bytree=0.8, random_state=seed)
        m.fit(Xtr.reshape(len(Xtr), -1), ytr)
        pred = {"val": m.predict(Xva.reshape(len(Xva), -1)), "test": m.predict(Xte.reshape(len(Xte), -1))}
    else:
        qt.reset_seed(seed)
        if model == "bilstm_attn":
            m, kind = build_bilstm_attn(Xtr.shape[1], Xtr.shape[2], cfg["units"], cfg["dropout"], cfg["lr"])
        else:
            m, kind = q6.build(model, Xtr.shape[1], Xtr.shape[2])
            set_lr(m, cfg["lr"])
        es = EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)
        h = m.fit(Xtr, ytr, validation_data=(Xva, yva), epochs=cap, batch_size=32, callbacks=[es], verbose=2)
        pred, sdv = {}, {}
        for k, X in (("val", Xva), ("test", Xte)):
            o = m.predict(X, verbose=0, batch_size=1024)
            pred[k] = o[:, 0] if kind == "nll" else o.ravel()
            sdv[k] = np.sqrt(np.exp(o[:, 1])) * d["y_scale"] if kind == "nll" else None
        hist_d = {k: [float(v) for v in vs] for k, vs in h.history.items()}
        vl = h.history["val_loss"]; best, ep = int(np.argmin(vl)) + 1, len(vl)
    sec = time.time() - t0
    rows, met = [], {}
    for k, (y, t, p) in (("val", (yva, tva, pva)), ("test", (yte, tte, pte))):
        yt, yp = inv(y), inv(pred[k])
        sd = sdv[k]
        rows.append(pd.DataFrame({"split": k, "valid_time": pd.to_datetime(t), "y_true": yt, "y_pred_mean": yp,
                                  "y_pred_std": sd if sd is not None else np.nan}))
        met[k] = {"rmse": float(np.sqrt(np.mean((yp - yt) ** 2))), "mae": float(np.mean(np.abs(yp - yt)))}
        if sd is not None:
            met[k]["crps"] = float(np.mean(crps_gauss(yt, yp, sd)))
            met[k]["nll"] = float(np.mean(0.5 * np.log(2 * np.pi * sd ** 2) + 0.5 * ((yt - yp) / sd) ** 2))
    os.makedirs(f"{OUT}/preds", exist_ok=True); os.makedirs(f"{OUT}/runs", exist_ok=True)
    pd.concat(rows, ignore_index=True).to_csv(f"{OUT}/preds/{tag}.csv", index=False)
    rec = {"tag": tag, "model": model, "config": cfg, "cap": cap, "seed": seed, "val": met["val"], "test": met["test"],
           "best_epoch": best, "epochs_trained": ep, "hit_cap": (ep == cap) if ep else None,
           "train_seconds": round(sec, 1), "history": hist_d, "gpu": qt.gpu_name(), "tf": tf.__version__,
           "host": socket.gethostname(), "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    json.dump(rec, open(path, "w"), indent=1)
    print(f"[done] {tag} | val {met['val']['rmse']:.6f} test {met['test']['rmse']:.6f} | "
          f"best {best}/{ep} | {sec:.0f}s", flush=True)
    return rec


def results(model, prefix=None):
    out = []
    for f in glob.glob(f"{OUT}/runs/{model}__*.json"):
        r = json.load(open(f))
        if r["model"] == model and (prefix is None or r["tag"].startswith(prefix)):
            out.append(r)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=["gate", "search", "recheck", "final", "light"])
    ap.add_argument("--models", nargs="+", default=None)
    a = ap.parse_args()
    d = split_data(load_merged(), ORIG, 6)
    print(f"windows {len(d['train'][0])}/{len(d['val'][0])}/{len(d['test'][0])} | GPU {qt.gpu_name()}", flush=True)

    if a.stage == "gate":
        r = run(d, "bilstm_attn", ORIG_CFG["bilstm_attn"], 42, cap=30)
        diff = r["test"]["rmse"] - REF_42["bilstm_attn"]
        ok = abs(diff) < 1e-5
        print(f"[gate] bilstm_attn rebuilt, seed 42, cap 30: {r['test']['rmse']:.6f} vs {REF_42['bilstm_attn']} "
              f"-> {diff:+.6f} {'OK' if ok else 'DIFFERENT — stop; send q10_train.py'}")
        r = run(d, "xgboost", ORIG_CFG["xgboost"], 42)
        diff = r["test"]["rmse"] - REF_42["xgboost"]
        print(f"[gate] xgboost seed 42: {r['test']['rmse']:.6f} vs {REF_42['xgboost']} -> {diff:+.6f} "
              f"{'OK' if abs(diff) < 1e-5 else 'DIFFERENT'}")
        return

    models = a.models or (LIGHT if a.stage == "light" else ["xgboost", "bilstm_attn"])
    for model in models:
        cap = CAP.get(model)
        if a.stage == "search":
            for cfg in GRID[model]:
                run(d, model, cfg, 42, cap)
            rs = sorted([r for r in results(model) if r["seed"] == 42 and r["cap"] == cap], key=lambda r: r["val"]["rmse"])
            print(f"\n[{model}] seed-42 validation ranking (top 10 of {len(rs)}):")
            for r in rs[:10]:
                print(f"  {r['tag']:<45} val {r['val']['rmse']:.6f} best {r['best_epoch']}/{r['epochs_trained']}")
            o = [r for r in rs if r["config"] == ORIG_CFG[model]]
            if o:
                print(f"  original config rank {rs.index(o[0]) + 1}/{len(rs)}, val {o[0]['val']['rmse']:.6f}")
        elif a.stage == "recheck":
            rs = sorted([r for r in results(model) if r["seed"] == 42 and r["cap"] == cap], key=lambda r: r["val"]["rmse"])
            assert len(rs) == 27, f"{model}: search incomplete ({len(rs)}/27)"
            top = [r["config"] for r in rs[:3]]
            score = []
            for cfg in top:
                vals = [run(d, model, cfg, s, cap)["val"]["rmse"] for s in (42, 123, 7)]
                score.append((float(np.mean(vals)), cfg, vals))
            score.sort(key=lambda x: x[0])
            sel = score[0][1]
            json.dump({"model": model, "cap": cap, "top3": [{"config": c, "val_42_123_7": v, "mean": m_}
                                                            for m_, c, v in score],
                       "selected": sel, "selected_is_original": sel == ORIG_CFG[model],
                       "original_in_top3": ORIG_CFG[model] in top},
                      open(f"{OUT}/selection_{model}.json", "w"), indent=2)
            print(f"[{model}] selected {sel} (original: {ORIG_CFG[model]}; original in top 3: {ORIG_CFG[model] in top})")
        elif a.stage == "final":
            sel = json.load(open(f"{OUT}/selection_{model}.json"))["selected"]
            for cfg in ([sel] if sel == ORIG_CFG[model] else [sel, ORIG_CFG[model]]):
                for s in SEEDS:
                    run(d, model, cfg, s, cap)
        elif a.stage == "light":
            cap = CAP["light"]
            for lr in LIGHT_LR:
                run(d, model, {"lr": lr}, 42, cap)
            metric = "crps" if model in PROB else "rmse"
            rs = sorted([r for r in results(model) if r["seed"] == 42 and r["cap"] == cap], key=lambda r: r["val"][metric])
            sel = rs[0]["config"]
            print(f"[{model}] lr by seed-42 validation {metric.upper()}: " +
                  ", ".join(f"{r['config']['lr']:g}: {metric} {r['val'][metric]:.6f}, rmse {r['val']['rmse']:.6f} "
                            f"(best {r['best_epoch']}/{r['epochs_trained']})" for r in rs))
            json.dump({"model": model, "cap": cap, "selection_metric": f"validation {metric}",
                       "seed42_val": {f"{r['config']['lr']:g}": r["val"] for r in rs},
                       "selected": sel, "selected_is_original": sel["lr"] == 1e-3},
                      open(f"{OUT}/selection_{model}.json", "w"), indent=2)
            cfgs = [{"lr": 1e-3}] + ([sel] if sel["lr"] != 1e-3 else [])     # group B always, group C if different
            for cfg in cfgs:
                for s in SEEDS:
                    run(d, model, cfg, s, cap)
    print(f"===== q19 {a.stage.upper()} COMPLETE =====")


if __name__ == "__main__":
    main()
