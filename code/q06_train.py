# ============================================================
# Item 06, step 2: rolling-origin (expanding-window) training, six models x five seeds.
# Folds come from q06_common.py; per fold the scalers are fitted on the training years only
# and windows never cross split boundaries (same as notebook Step 2D).
# Model definitions and training protocol are those of the main study:
#   xgboost          : notebook Step 3   (100 trees, lr 0.05, depth 6, subsample/colsample 0.8)
#   bulstm           : notebook Step 4   (BiLSTM 50 -> BiLSTM 50, dropout 0.3, Gaussian NLL)
#   bilstm_attn      : notebook Step 5   (BiLSTM 64, dropout 0.2, additive attention, MSE)
#   transformer      : notebook Step 6   (d_model 32, 4 heads, FF 64, dropout 0.2, MSE)
#   bulstm_attn      : notebook Step 7   (3 x BiLSTM 64, dropout 0.2, attention, Gaussian NLL)
#   prob_bilstm_attn : notebook Step 11  (BiLSTM 64, dropout 0.2, attention, Gaussian NLL)
# Adam 1e-3, batch 32, <= 30 epochs, EarlyStopping(val_loss, patience 10, restore best).
# Seeding and determinism as q10_train.py (notebook Step 20).
# Fold "ORIG" rebuilds the original 70/15/15 split of 2004-2021 from the merged file and is used
# only to check that the pipeline reproduces the main study (seed 42).
# Outputs: results/q06/preds/<fold>__<model>__s<seed>.csv  (val and test splits)
#          results/q06/runs/<fold>__<model>__s<seed>.json   (metrics, training time, environment)
#          results/q06/folds/<fold>.json                   (sizes, periods, training Q95)
# ============================================================
import os, sys, argparse, json, socket, time
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
import q10_train as qt                      # determinism, GPU memory growth, attention, NLL wrapper
import tensorflow as tf
from tensorflow.keras import Model, Input
from tensorflow.keras.layers import (LSTM, Bidirectional, Dense, Dropout, LayerNormalization,
                                     MultiHeadAttention, GlobalAveragePooling1D, Embedding, Add)
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import StandardScaler
from q06_common import ROOT, FEATURES, TARGET, WINDOW, SEEDS, FOLDS, load_regional, split

OUT = f"{ROOT}/results/q06"
MODELS = ["xgboost", "bulstm", "bilstm_attn", "transformer", "bulstm_attn", "prob_bilstm_attn"]
REPRO = {("xgboost", 42): 0.243750, ("bilstm_attn", 42): 0.242848, ("bulstm_attn", 42): 0.246413}


# ---------- data ----------
def fold_data(fold):
    df = load_regional()
    if fold == "ORIG":
        d = df[df["valid_time"].dt.year >= 2004].reset_index(drop=True)
        n = len(d)
        parts = {"train": d.iloc[:int(n * .70)], "val": d.iloc[int(n * .70):int(n * .85)], "test": d.iloc[int(n * .85):]}
        parts = {k: v.reset_index(drop=True) for k, v in parts.items()}
    else:
        parts = split(df, fold)
    xs, ys = StandardScaler(), StandardScaler()
    xs.fit(parts["train"][FEATURES]); ys.fit(parts["train"][[TARGET]])
    out = {}
    for k, p in parts.items():
        diffs = p["valid_time"].diff().dropna()
        assert (diffs == pd.Timedelta(hours=6)).all(), f"{fold} {k}: gap inside split"
        vx = xs.transform(p[FEATURES]).astype("float32")
        vy = ys.transform(p[[TARGET]]).ravel().astype("float32")
        t = p["valid_time"].values
        X = np.stack([vx[i:i + WINDOW] for i in range(len(p) - WINDOW)])
        out[k] = (X, vy[WINDOW:], t[WINDOW:], p[TARGET].values[WINDOW - 1:-1])   # last value = persistence
    out["y_mean"], out["y_scale"] = float(ys.mean_[0]), float(ys.scale_[0])
    out["q95_train"] = float(np.quantile(out["train"][1] * out["y_scale"] + out["y_mean"], 0.95))
    return out


# ---------- models ----------
def build(name, T, F):
    inputs = Input(shape=(T, F))
    if name == "bilstm_attn":
        m, _ = qt.build("bilstm_attn", T, F); return m, "mse"
    if name == "bulstm_attn":
        m, _ = qt.build("bulstm_attn", T, F); return m, "nll"
    if name == "bulstm":
        x = Bidirectional(LSTM(50, return_sequences=True))(inputs)
        x = Dropout(0.3)(x)
        x = Bidirectional(LSTM(50))(x)
        x = Dropout(0.3)(x)
        m = qt.CustomNLLModel(Model(inputs, Dense(2)(x), name="BU_LSTM"))
        m.compile(optimizer=Adam(learning_rate=0.001)); return m, "nll"
    if name == "prob_bilstm_attn":
        h = Bidirectional(LSTM(64, return_sequences=True))(inputs)
        h = Dropout(0.2)(h)
        context, _ = qt.TemporalAttention(attn_units=64)(h)
        m = Model(inputs, Dense(2)(context), name="Probabilistic_BiLSTM_Attention")

        def gaussian_nll_loss(y_true, y_pred):
            y_true = tf.reshape(tf.cast(y_true, tf.float32), [-1])
            mean, log_var = y_pred[:, 0], y_pred[:, 1]
            return tf.reduce_mean(0.5 * tf.exp(-log_var) * tf.square(y_true - mean) + 0.5 * log_var)
        m.compile(optimizer=Adam(learning_rate=0.001), loss=gaussian_nll_loss); return m, "nll"
    if name == "transformer":
        D, H, FF, DR = 32, 4, 64, 0.2
        x = Dense(D)(inputs)
        pos = Embedding(input_dim=T, output_dim=D)(tf.range(start=0, limit=T, delta=1))
        x = Add()([x, tf.expand_dims(pos, axis=0)])
        a = MultiHeadAttention(num_heads=H, key_dim=D // H, dropout=DR)(x, x)
        x = LayerNormalization(epsilon=1e-6)(Add()([x, a]))
        ff = Dense(D)(Dropout(DR)(Dense(FF, activation="relu")(x)))
        x = LayerNormalization(epsilon=1e-6)(Add()([x, ff]))
        x = Dropout(DR)(GlobalAveragePooling1D()(x))
        m = Model(inputs, Dense(1)(x), name="Transformer")
        m.compile(optimizer=Adam(learning_rate=0.001), loss="mse"); return m, "mse"
    raise ValueError(name)


def run_one(d, fold, model, seed):
    tag = f"{fold}__{model}__s{seed}"
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
        best, ep = None, None
    else:
        qt.reset_seed(seed)
        m, kind = build(model, Xtr.shape[1], Xtr.shape[2])
        es = EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)
        hist = m.fit(Xtr, ytr, validation_data=(Xva, yva), epochs=30, batch_size=32, callbacks=[es], verbose=2)
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
    json.dump({"tag": tag, "fold": fold, "model": model, "seed": seed, "val": met["val"], "test": met["test"],
               "best_epoch": best, "epochs_trained": ep, "train_seconds": round(sec, 1),
               "n_train": int(len(Xtr)), "n_val": int(len(Xva)), "n_test": int(len(Xte)),
               "gpu": qt.gpu_name(), "tf": tf.__version__, "host": socket.gethostname(),
               "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")},
              open(meta_path, "w"), indent=2)
    print(f"[done] {tag} | test RMSE={met['test']['rmse']:.6f} R2={met['test']['r2']:.4f} | "
          f"best epoch {best}/{ep} | {sec:.0f}s", flush=True)
    if fold == "ORIG" and (model, seed) in REPRO:
        ref = REPRO[(model, seed)]
        diff = met["test"]["rmse"] - ref
        print(f"[repro] {model} seed {seed}: {met['test']['rmse']:.6f} vs main study {ref} -> diff {diff:+.6f} "
              f"{'OK' if abs(diff) < 1e-5 else 'DIFFERENT'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fold", required=True, choices=list(FOLDS) + ["ORIG"])
    ap.add_argument("--models", nargs="+", default=MODELS, choices=MODELS)
    ap.add_argument("--seeds", nargs="+", type=int, default=SEEDS)
    a = ap.parse_args()
    d = fold_data(a.fold)
    info = {"fold": a.fold, "periods": FOLDS.get(a.fold, "original 70/15/15 of 2004-2021"),
            "n_windows": {k: int(len(d[k][0])) for k in ("train", "val", "test")},
            "target_times": {k: [str(pd.Timestamp(d[k][2][0])), str(pd.Timestamp(d[k][2][-1]))]
                             for k in ("train", "val", "test")},
            "q95_train": d["q95_train"], "y_mean": d["y_mean"], "y_scale": d["y_scale"]}
    os.makedirs(f"{OUT}/folds", exist_ok=True)
    json.dump(info, open(f"{OUT}/folds/{a.fold}.json", "w"), indent=2)
    print("fold:", json.dumps(info))
    for model in a.models:
        for seed in a.seeds:
            run_one(d, a.fold, model, seed)
    print("===== q06 TRAIN JOB COMPLETE =====")
