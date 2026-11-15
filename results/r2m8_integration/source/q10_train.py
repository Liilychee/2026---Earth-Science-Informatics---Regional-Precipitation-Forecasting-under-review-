# ============================================================
# Item 10 + 17: leave-one-feature-out ablation, 5 seeds, two architectures.
#   bilstm_attn : 1 x BiLSTM(64) + Dropout(0.2) + attention, MSE   (notebook Step 5)
#   bulstm_attn : 3 x BiLSTM(64) + Dropout(0.2) + attention, NLL   (notebook Step 7)
# Training protocol identical to the notebook: Adam(1e-3), batch 32, <=30 epochs,
# EarlyStopping(val_loss, patience 10, restore best). Seeding as notebook Step 20.
# Inputs : results/windows/q10_windows.npz (from q10_prepare_data.py)
# Outputs: results/q10/preds/<arch>__<config>__s<seed>.csv
#          results/q10/runs/<arch>__<config>__s<seed>.json   (metrics + environment)
#          results/q10/models/<arch>__<config>__s<seed>.weights.h5
# Finished runs are skipped, so a job can be restarted safely.
# ============================================================
import os
os.environ["TF_DETERMINISTIC_OPS"] = "1"
os.environ.setdefault("TF_FORCE_GPU_ALLOW_GROWTH", "true")

import argparse, json, random, socket, time
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import tensorflow as tf

for g in tf.config.list_physical_devices("GPU"):
    tf.config.experimental.set_memory_growth(g, True)
tf.config.experimental.enable_op_determinism()

from tensorflow.keras import Model, Input
from tensorflow.keras.layers import LSTM, Bidirectional, Dense, Dropout, Layer
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

ROOT = os.environ.get("Q10_ROOT", "/root/autodl-tmp")
WIN = f"{ROOT}/results/windows/q10_windows.npz"
SMOKE = bool(os.environ.get("Q10_SMOKE"))
OUT = f"{ROOT}/results/q10_smoke" if SMOKE else f"{ROOT}/results/q10"   # smoke runs never mix with real ones
SEEDS = [42, 123, 7, 2024, 99]
FEATURES = ["mxtpr", "mntpr", "lsp", "tcc", "v10", "sp", "d2m"]
SINGLE_CONFIGS = ["full"] + [f"no_{f}" for f in FEATURES]
GROUPS = {"no_precip": ["mxtpr", "mntpr", "lsp"],       # all precipitation-related predictors
          "no_mxtpr_mntpr": ["mxtpr", "mntpr"]}         # keeps lsp (R4 l.936-938)
CONFIGS = SINGLE_CONFIGS + list(GROUPS)


def removed_of(config):
    if config == "full":
        return []
    return GROUPS[config] if config in GROUPS else [config[3:]]
# Seed-42 full-model test RMSE from the notebook (RTX 5090), for the reproduction check
REFERENCE = {"bilstm_attn": {"Step 5 / Step 15": 0.242848},
             "bulstm_attn": {"Step 20 full model (same seeding)": 0.246413, "Step 7": 0.246441}}


class TemporalAttention(Layer):
    def __init__(self, attn_units=64, **kwargs):
        super().__init__(**kwargs)
        self.attn_units = attn_units

    def build(self, input_shape):
        H = input_shape[-1]
        self.W = self.add_weight(name="W", shape=(H, self.attn_units),
                                 initializer="glorot_uniform", trainable=True)
        self.b = self.add_weight(name="b", shape=(self.attn_units,),
                                 initializer="zeros", trainable=True)
        self.v = self.add_weight(name="v", shape=(self.attn_units, 1),
                                 initializer="glorot_uniform", trainable=True)
        super().build(input_shape)

    def call(self, h):
        score = tf.tanh(tf.tensordot(h, self.W, axes=1) + self.b)
        score = tf.tensordot(score, self.v, axes=1)
        alpha = tf.nn.softmax(score, axis=1)
        context = tf.reduce_sum(alpha * h, axis=1)
        return context, alpha


def nll_loss(y_true, y_pred_mean, y_pred_log_var):
    y_true = tf.cast(y_true, tf.float32)
    precision = tf.exp(-y_pred_log_var)
    return tf.reduce_mean(0.5 * precision * tf.square(y_true - y_pred_mean) + 0.5 * y_pred_log_var)


class CustomNLLModel(tf.keras.Model):
    def __init__(self, model, **kwargs):
        super().__init__(**kwargs)
        self.model = model
        self.loss_tracker = tf.keras.metrics.Mean(name="loss")
        self.val_loss_tracker = tf.keras.metrics.Mean(name="val_loss")

    def call(self, inputs, training=False):
        return self.model(inputs, training=training)

    def train_step(self, data):
        x, y = data
        with tf.GradientTape() as tape:
            out = self(x, training=True)
            loss = nll_loss(y, out[:, 0], out[:, 1])
        grads = tape.gradient(loss, self.trainable_variables)
        self.optimizer.apply_gradients(zip(grads, self.trainable_variables))
        self.loss_tracker.update_state(loss)
        return {"loss": self.loss_tracker.result()}

    def test_step(self, data):
        x, y = data
        out = self(x, training=False)
        loss = nll_loss(y, out[:, 0], out[:, 1])
        self.val_loss_tracker.update_state(loss)
        return {"loss": self.val_loss_tracker.result()}

    @property
    def metrics(self):
        return [self.loss_tracker, self.val_loss_tracker]


def reset_seed(seed):  # identical to notebook Step 20
    tf.keras.backend.clear_session()
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    tf.keras.utils.set_random_seed(seed)


def build(arch, T, F):
    inputs = Input(shape=(T, F))
    if arch == "bilstm_attn":
        h = Bidirectional(LSTM(64, return_sequences=True))(inputs)
        h = Dropout(0.2)(h)
        context, _ = TemporalAttention(attn_units=64)(h)
        model = Model(inputs, Dense(1)(context), name="BiLSTM_Attention")
        model.compile(optimizer=Adam(learning_rate=0.001), loss="mse")
        return model, model
    h = inputs
    for _ in range(3):
        h = Bidirectional(LSTM(64, return_sequences=True))(h)
        h = Dropout(0.2)(h)
    context, _ = TemporalAttention(attn_units=64)(h)
    base = Model(inputs, Dense(2)(context), name="BU_LSTM_Attention")
    wrapped = CustomNLLModel(base)
    wrapped.compile(optimizer=Adam(learning_rate=0.001))
    return wrapped, base


def gpu_name():
    gpus = tf.config.list_physical_devices("GPU")
    if not gpus:
        return "CPU only"
    try:
        return tf.config.experimental.get_device_details(gpus[0]).get("device_name", "GPU")
    except Exception:
        return "GPU (name unavailable)"


def run_one(d, arch, config, seed):
    tag = f"{arch}__{config}__s{seed}"
    meta_path = f"{OUT}/runs/{tag}.json"
    if os.path.exists(meta_path):
        print(f"[skip] {tag} already done")
        return json.load(open(meta_path))

    removed = removed_of(config)
    keep = [i for i, f in enumerate(FEATURES) if f not in removed]
    Xtr = np.ascontiguousarray(d["X_train"][:, :, keep])
    Xva = np.ascontiguousarray(d["X_val"][:, :, keep])
    Xte = np.ascontiguousarray(d["X_test"][:, :, keep])
    ytr, yva, yte = d["y_train"], d["y_val"], d["y_test"]
    y_mean, y_scale = float(d["y_mean"][0]), float(d["y_scale"][0])
    inv = lambda a: np.asarray(a).ravel() * y_scale + y_mean

    print(f"\n===== {tag} | features: {[FEATURES[i] for i in keep]} =====", flush=True)
    reset_seed(seed)
    fit_model, base = build(arch, Xtr.shape[1], Xtr.shape[2])
    es = EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)
    t0 = time.time()
    epochs = 1 if SMOKE else 30   # smoke test only, never for results
    hist = fit_model.fit(Xtr, ytr, validation_data=(Xva, yva), epochs=epochs, batch_size=32,
                         callbacks=[es], verbose=2)
    train_sec = time.time() - t0

    rows, metrics = [], {}
    for split, X, y, t in [("train", Xtr, ytr, d["t_train"]), ("val", Xva, yva, d["t_val"]),
                           ("test", Xte, yte, d["t_test"])]:
        out = fit_model.predict(X, verbose=0, batch_size=1024)
        if arch == "bilstm_attn":
            mean_s, std_mm = out.ravel(), np.full(len(y), np.nan)
        else:
            mean_s, std_mm = out[:, 0], np.sqrt(np.exp(out[:, 1])) * y_scale
        yt, yp = inv(y), inv(mean_s)
        rows.append(pd.DataFrame({"split": split, "valid_time": pd.to_datetime(t),
                                  "y_true": yt, "y_pred_mean": yp, "y_pred_std": std_mm}))
        metrics[split] = {"rmse": float(np.sqrt(mean_squared_error(yt, yp))),
                          "mae": float(mean_absolute_error(yt, yp)),
                          "r2": float(r2_score(yt, yp))}

    os.makedirs(f"{OUT}/preds", exist_ok=True)
    os.makedirs(f"{OUT}/models", exist_ok=True)
    os.makedirs(f"{OUT}/runs", exist_ok=True)
    pd.concat(rows, ignore_index=True).to_csv(f"{OUT}/preds/{tag}.csv", index=False)
    base.save_weights(f"{OUT}/models/{tag}.weights.h5")

    vl = hist.history["val_loss"]
    meta = {"tag": tag, "arch": arch, "config": config, "seed": seed,
            "removed": None if config == "full" else ",".join(removed),
            "features": [FEATURES[i] for i in keep],
            "test": metrics["test"], "val": metrics["val"], "train": metrics["train"],
            "best_epoch": int(np.argmin(vl)) + 1, "epochs_trained": len(vl),
            "train_seconds": round(train_sec, 1),
            "gpu": gpu_name(), "tf": tf.__version__, "keras": tf.keras.__version__,
            "numpy": np.__version__, "host": socket.gethostname(),
            "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    json.dump(meta, open(meta_path, "w"), indent=2)   # written last = run complete
    print(f"[done] {tag} | test RMSE={metrics['test']['rmse']:.6f} R2={metrics['test']['r2']:.4f} "
          f"| best epoch {meta['best_epoch']}/{meta['epochs_trained']} | {train_sec:.0f}s", flush=True)

    if config == "full" and seed == 42:
        for name, ref in REFERENCE[arch].items():
            diff = metrics["test"]["rmse"] - ref
            flag = "OK (<1e-4)" if abs(diff) < 1e-4 else "DIFFERENT (>=1e-4)"
            print(f"[repro] {arch} seed 42 vs notebook {name}: {ref:.6f} -> diff {diff:+.6f}  {flag}")
    return meta


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", nargs="+", choices=["bilstm_attn", "bulstm_attn"], required=True)
    ap.add_argument("--configs", nargs="+", default=SINGLE_CONFIGS, choices=CONFIGS)
    ap.add_argument("--seeds", nargs="+", type=int, default=SEEDS)
    a = ap.parse_args()
    d = dict(np.load(WIN, allow_pickle=False))
    assert list(d["features"]) == FEATURES, "feature order mismatch"
    print("GPU:", gpu_name(), "| TF", tf.__version__, "| determinism on")
    for arch in a.arch:
        for config in a.configs:
            for seed in a.seeds:
                run_one(d, arch, config, seed)
    print("===== q10 TRAIN JOB COMPLETE =====")
