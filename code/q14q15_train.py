# ============================================================
# Items 14 and 15 on the main 70/15/15 split of 2004-2021 (same split, scaling and models as Table 3).
#   14 window length (R3 L329-333, L752-758; R4 l.329):
#        input history of W 6-hourly steps; W = 6 is the main study (t-30 h ... t, 30 h),
#        W = 3 is a 12 h history (t-12 h, t-6 h, t). Six models, five seeds, MSE / NLL as in the main study.
#   15 loss function for the deterministic deep models (R3 L376; R1 M1):
#        BiLSTM-Attention and Transformer trained with Huber loss, delta in standardized target units;
#        the MSE reference runs are the W = 6 runs of item 14 (same code, seeds and data).
# Models, hyperparameters and training protocol come from q06_train.py (notebook Steps 3-7, 11);
# seeding and determinism from q10_train.py. Only the factor under study changes.
# Outputs: results/q14/preds/<model>__w<W>__<loss>__s<seed>.csv  (val and test, mm)
#          results/q14/runs/<model>__w<W>__<loss>__s<seed>.json
# Q14_SMOKE=1 -> results/q14_smoke, 2 epochs; never used for results.
# ============================================================
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import argparse, json, socket, time
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import q10_train as qt
import q06_train as q6                       # build(): the six model definitions of the main study
import tensorflow as tf
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import StandardScaler
from q06_common import ROOT, FEATURES, TARGET, SEEDS, load_regional

SMOKE = bool(os.environ.get("Q14_SMOKE"))
OUT = f"{ROOT}/results/q14_smoke" if SMOKE else f"{ROOT}/results/q14"
MODELS = q6.MODELS
DETERMINISTIC = ["bilstm_attn", "transformer"]
REPRO = {("xgboost", 42): 0.243750, ("bilstm_attn", 42): 0.242848, ("bulstm_attn", 42): 0.246413}


def main_split_data(window):
    """Original 70/15/15 split of 2004-2021 (identical to q06 fold ORIG), windows of length `window`."""
    df = load_regional()
    d = df[df["valid_time"].dt.year >= 2004].reset_index(drop=True)
    n = len(d)
    assert n == 26300, n
    parts = {"train": d.iloc[:int(n * .70)], "val": d.iloc[int(n * .70):int(n * .85)], "test": d.iloc[int(n * .85):]}
    parts = {k: v.reset_index(drop=True) for k, v in parts.items()}
    xs, ys = StandardScaler(), StandardScaler()
    xs.fit(parts["train"][FEATURES]); ys.fit(parts["train"][[TARGET]])
    out = {}
    for k, p in parts.items():
        vx = xs.transform(p[FEATURES]).astype("float32")
        vy = ys.transform(p[[TARGET]]).ravel().astype("float32")
        t = p["valid_time"].values
        X = np.stack([vx[i:i + window] for i in range(len(p) - window)])
        out[k] = (X, vy[window:], t[window:], p[TARGET].values[window - 1:-1])     # last value = persistence
    out["y_mean"], out["y_scale"] = float(ys.mean_[0]), float(ys.scale_[0])
    return out


def run_one(d, model, window, loss, delta, seed, epochs):
    ltag = loss if loss != "huber" else f"huber{delta:g}"
    if model not in DETERMINISTIC and loss == "huber":
        raise ValueError("Huber is only used for the deterministic deep models")
    tag = f"{model}__w{window}__{ltag}__s{seed}"
    meta_path = f"{OUT}/runs/{tag}.json"
    if os.path.exists(meta_path):
        print(f"[skip] {tag}"); return
    (Xtr, ytr, _, _), (Xva, yva, tva, pva), (Xte, yte, tte, pte) = d["train"], d["val"], d["test"]
    inv = lambda a: np.asarray(a, dtype="float64").ravel() * d["y_scale"] + d["y_mean"]
    t0 = time.time()
    if model == "xgboost":
        import xgboost as xgb
        m = xgb.XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=6, subsample=0.8,
                             colsample_bytree=0.8, random_state=seed)
        m.fit(Xtr.reshape(len(Xtr), -1), ytr)
        pred = {"val": (m.predict(Xva.reshape(len(Xva), -1)), None),
                "test": (m.predict(Xte.reshape(len(Xte), -1)), None)}
        best, ep, kind = None, None, "tree"
    else:
        qt.reset_seed(seed)
        m, kind = q6.build(model, Xtr.shape[1], Xtr.shape[2])
        if loss == "huber":                                # same optimizer settings, only the loss changes
            m.compile(optimizer=Adam(learning_rate=0.001), loss=tf.keras.losses.Huber(delta=delta))
        es = EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)
        hist = m.fit(Xtr, ytr, validation_data=(Xva, yva), epochs=epochs, batch_size=32, callbacks=[es], verbose=2)
        pred = {}
        for k, X in (("val", Xva), ("test", Xte)):
            o = m.predict(X, verbose=0, batch_size=1024)
            pred[k] = (o[:, 0], np.sqrt(np.exp(o[:, 1])) * d["y_scale"]) if kind == "nll" else (o.ravel(), None)
        vl = hist.history["val_loss"]; best, ep = int(np.argmin(vl)) + 1, len(vl)
    sec = time.time() - t0

    rows, met = [], {}
    for k, (y, t, p) in (("val", (yva, tva, pva)), ("test", (yte, tte, pte))):
        mean, std = pred[k]
        yt, yp = inv(y), inv(mean)
        rows.append(pd.DataFrame({"split": k, "valid_time": pd.to_datetime(t), "y_true": yt, "y_pred_mean": yp,
                                  "y_pred_std": std if std is not None else np.nan, "persistence": p}))
        met[k] = {"rmse": float(np.sqrt(np.mean((yp - yt) ** 2))), "mae": float(np.mean(np.abs(yp - yt))),
                  "r2": float(1 - np.sum((yp - yt) ** 2) / np.sum((yt - yt.mean()) ** 2))}
    os.makedirs(f"{OUT}/preds", exist_ok=True); os.makedirs(f"{OUT}/runs", exist_ok=True)
    pd.concat(rows, ignore_index=True).to_csv(f"{OUT}/preds/{tag}.csv", index=False)
    json.dump({"tag": tag, "model": model, "window": window, "history_hours": 6 * (window - 1), "loss": ltag,
               "huber_delta_std_units": delta if loss == "huber" else None, "seed": seed,
               "val": met["val"], "test": met["test"], "best_epoch": best, "epochs_trained": ep,
               "train_seconds": round(sec, 1), "n_train": int(len(Xtr)), "n_val": int(len(Xva)), "n_test": int(len(Xte)),
               "gpu": qt.gpu_name(), "tf": tf.__version__, "host": socket.gethostname(),
               "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")},
              open(meta_path, "w"), indent=2)
    print(f"[done] {tag} | val RMSE={met['val']['rmse']:.6f} test RMSE={met['test']['rmse']:.6f} | "
          f"best epoch {best}/{ep} | {sec:.0f}s", flush=True)
    if window == 6 and loss in ("mse", "nll", "tree") and (model, seed) in REPRO and not SMOKE:
        ref = REPRO[(model, seed)]
        diff = met["test"]["rmse"] - ref
        print(f"[repro] {model} seed {seed} W=6: {met['test']['rmse']:.6f} vs main study {ref} -> {diff:+.6f} "
              f"{'OK' if abs(diff) < 1e-5 else 'DIFFERENT'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=MODELS, choices=MODELS)
    ap.add_argument("--window", type=int, required=True)
    ap.add_argument("--loss", default="default", choices=["default", "huber"],
                    help="default = loss of the main study (MSE, Gaussian NLL, or tree)")
    ap.add_argument("--delta", type=float, default=None, help="Huber delta in standardized target units")
    ap.add_argument("--seeds", nargs="+", type=int, default=SEEDS)
    ap.add_argument("--epochs", type=int, default=2 if SMOKE else 30)
    a = ap.parse_args()
    d = main_split_data(a.window)
    print(f"window {a.window} ({6 * (a.window - 1)} h history) | windows train/val/test = "
          f"{len(d['train'][0])}/{len(d['val'][0])}/{len(d['test'][0])} | GPU {qt.gpu_name()}")
    for model in a.models:
        loss = a.loss if a.loss == "huber" else {"xgboost": "tree", "bulstm": "nll", "bulstm_attn": "nll",
                                                 "prob_bilstm_attn": "nll"}.get(model, "mse")
        for seed in a.seeds:
            run_one(d, model, a.window, loss, a.delta, seed, a.epochs)
    print("===== q14/q15 TRAIN JOB COMPLETE =====")
