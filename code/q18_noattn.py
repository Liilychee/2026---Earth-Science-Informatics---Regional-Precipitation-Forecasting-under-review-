# ============================================================
# Item 18 (R3 L822–824): BiLSTM without attention, retrained in the main deterministic pipeline so that it can be
# compared with BiLSTM-Attention seed by seed (the notebook Step 9b control saved metrics only, not predictions,
# and was seeded without clear_session/op determinism).
# Architecture identical to notebook Step 9b: BiLSTM(64, return_sequences) -> Dropout(0.2) -> GlobalAveragePooling1D
#   -> Dense(1), MSE, Adam(1e-3), batch 32, <= 30 epochs, EarlyStopping(val_loss, patience 10, restore best).
# Data, split, scaling, W = 6 and seeding identical to q21_train.py / q19_tune.py (q10_train.reset_seed).
# Outputs: results/q18/preds/bilstm_noattn__w6__s<seed>.csv, results/q18/runs/bilstm_noattn__w6__s<seed>.json
# --with-attn (use on any GPU other than the RTX 5090 that produced q21 C0): first retrains BiLSTM-Attention on the
#   same card (builder identical to q10_train.build / q19 gate: BiLSTM 64, dropout 0.2, TemporalAttention 64, Adam 1e-3),
#   tag bilstm_attn_samecard__w6__s<seed>, so that attention vs no-attention is compared within one GPU.
#   Seed 42 on a 5090 reproduces 0.242848; on another card a small difference is expected and only reported.
# Run (5090): cd /root/autodl-tmp && python3 code/q18_noattn.py 2>&1 | tee results/metrics/q18_noattn_output.txt
# Run (other GPU): ... python3 code/q18_noattn.py --with-attn 2>&1 | tee results/metrics/q18_noattn_output.txt
# ============================================================
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json, socket, time
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import q10_train as qt                        # same import order as q14q15/q19/q21: determinism before TF
import tensorflow as tf
from tensorflow.keras import Model, Input
from tensorflow.keras.layers import LSTM, Bidirectional, Dense, Dropout, GlobalAveragePooling1D
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
from q06_common import ROOT, SEEDS
from q21_train import load_merged, split_data, ORIG

OUT = f"{ROOT}/results/q18"


def build(T, F):
    inputs = Input(shape=(T, F))
    h = Bidirectional(LSTM(64, return_sequences=True))(inputs)
    h = Dropout(0.2)(h)
    m = Model(inputs, Dense(1)(GlobalAveragePooling1D()(h)), name="BiLSTM_NoAttention")
    m.compile(optimizer=Adam(learning_rate=0.001), loss="mse")
    return m


def build_attn(T, F):
    inputs = Input(shape=(T, F))
    h = Bidirectional(LSTM(64, return_sequences=True))(inputs)
    h = Dropout(0.2)(h)
    context, _ = qt.TemporalAttention(attn_units=64)(h)
    m = Model(inputs, Dense(1)(context), name="BiLSTM_Attention")
    m.compile(optimizer=Adam(learning_rate=0.001), loss="mse")
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-attn", action="store_true")
    a = ap.parse_args()
    d = split_data(load_merged(), ORIG, 6)
    (Xtr, ytr, _, _), (Xva, yva, tva, _), (Xte, yte, tte, _) = d["train"], d["val"], d["test"]
    inv = lambda a: np.asarray(a, dtype="float64").ravel() * d["y_scale"] + d["y_mean"]
    os.makedirs(f"{OUT}/preds", exist_ok=True); os.makedirs(f"{OUT}/runs", exist_ok=True)
    print(f"windows {len(Xtr)}/{len(Xva)}/{len(Xte)} | GPU {qt.gpu_name()}", flush=True)
    jobs = ([("bilstm_attn_samecard", build_attn)] if a.with_attn else []) + [("bilstm_noattn", build)]
    for name, builder in jobs:
        for seed in SEEDS:
            tag = f"{name}__w6__s{seed}"
            if os.path.exists(f"{OUT}/runs/{tag}.json"):
                print(f"[skip] {tag}"); continue
            qt.reset_seed(seed)
            m = builder(Xtr.shape[1], Xtr.shape[2])
            t0 = time.time()
            h = m.fit(Xtr, ytr, validation_data=(Xva, yva), epochs=30, batch_size=32,
                      callbacks=[EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)], verbose=2)
            sec = time.time() - t0
            rows, met = [], {}
            for k, X, y, t in (("val", Xva, yva, tva), ("test", Xte, yte, tte)):
                yt, yp = inv(y), inv(m.predict(X, verbose=0, batch_size=1024).ravel())
                rows.append(pd.DataFrame({"split": k, "valid_time": pd.to_datetime(t), "y_true": yt, "y_pred_mean": yp}))
                met[k] = {"rmse": float(np.sqrt(np.mean((yp - yt) ** 2))), "mae": float(np.mean(np.abs(yp - yt)))}
            pd.concat(rows, ignore_index=True).to_csv(f"{OUT}/preds/{tag}.csv", index=False)
            vl = h.history["val_loss"]
            json.dump({"tag": tag, "seed": seed, "val": met["val"], "test": met["test"], "n_params": int(m.count_params()),
                       "best_epoch": int(np.argmin(vl)) + 1, "epochs_trained": len(vl), "train_seconds": round(sec, 1),
                       "gpu": qt.gpu_name(), "tf": tf.__version__, "host": socket.gethostname(),
                       "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")},
                      open(f"{OUT}/runs/{tag}.json", "w"), indent=2)
            if name == "bilstm_attn_samecard" and seed == 42:
                print(f"[repro] BiLSTM-Attention seed 42 on {qt.gpu_name()}: {met['test']['rmse']:.6f} (5090 original 0.242848)",
                      flush=True)
            print(f"[done] {tag} | val {met['val']['rmse']:.6f} test {met['test']['rmse']:.6f} | "
                  f"best {int(np.argmin(vl)) + 1}/{len(vl)} | params {m.count_params()} | {sec:.0f}s", flush=True)
    print("===== q18 NOATTN COMPLETE =====")


if __name__ == "__main__":
    main()
