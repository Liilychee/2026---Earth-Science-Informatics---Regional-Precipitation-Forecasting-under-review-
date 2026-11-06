# ============================================================
# Item 11: precipitation-appropriate predictive distributions (R2 M6).
# One architecture (Probabilistic BiLSTM-Attention: BiLSTM 64, dropout 0.2, additive attention,
# notebook Step 11/12), three output distributions trained by maximum likelihood:
#   gaussian : N(mu, sigma^2) on the standardized target (the original formulation)
#   tobit    : Gaussian censored at 0 on the mm scale (point mass at 0, no negative bounds)
#   bergamma : Bernoulli-gamma hurdle on the mm scale (Williams 1998; Cannon 2008):
#              P(wet) = p, wet amounts ~ Gamma(shape a, scale b)
# Dry definition (--dry, tobit / bergamma only): targets <= dry are zero for training.
#   --dry 0 means "exact zero": only numerical zeros (|y| <= ZERO_TOL, float32 round-off of the
#   stored standardized targets) are zero, every positive ERA5 value is modelled as wet.
# Verification: every run is scored against the same targets for all three distributions under
#   several dry definitions (0 = exact zero, 0.001, 0.01 mm/h), so that differences between
#   distributions cannot come from relabelling small positive values.
# Scores: RMSE/MAE of the predictive mean, CRPS (199-quantile approximation), 95/90% PICP,
#   95% width, 95% interval score (Gneiting & Raftery 2007), share of negative lower bounds,
#   Brier scores for P(y > 0.1), P(y >= Q95), P(y >= 1.0); overall / dry / wet / upper subsets.
# Training protocol of the main study: Adam 1e-3, batch 32, <= 30 epochs,
# EarlyStopping(val_loss, patience 10, restore best), seeding as q10_train (notebook Step 20).
# Inputs : results/windows/q10_windows.npz (main 70/15/15 split, from q10_prepare_data.py)
# Outputs: results/q11/preds/<tag>.csv, results/q11/runs/<tag>.json
#          tag = gaussian__s<seed> or <dist>__dry<dry>__s<seed>
# Q11_SMOKE=1 -> results/q11_smoke, few epochs; never used for results.
# ============================================================
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import argparse, json, socket, time
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import q10_train as qt                      # determinism, seeding, TemporalAttention, gpu_name
import tensorflow as tf
from tensorflow.keras import Model, Input
from tensorflow.keras.layers import LSTM, Bidirectional, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, TerminateOnNaN
from scipy.stats import norm, gamma as gamma_dist

ROOT = os.environ.get("Q11_ROOT", "/root/autodl-tmp")
WIN = f"{ROOT}/results/windows/q10_windows.npz"
SMOKE = bool(os.environ.get("Q11_SMOKE"))
OUT = f"{ROOT}/results/q11_smoke" if SMOKE else f"{ROOT}/results/q11"
SEEDS = [42, 123, 7, 2024, 99]
DISTS = ["gaussian", "tobit", "bergamma"]
ZERO_TOL = 1e-6                  # mm/h; |y| below this is a numerical zero (float32 round-off)
EVAL_DRY = [0.0, 0.001, 0.01]    # verification target definitions
Q95, WET = 0.574048, 0.1
EVENTS = {"gt0.1": 0.1, "geQ95": Q95, "ge1.0": 1.0}
LEVELS = np.round(np.arange(0.005, 1.0, 0.005), 3)       # 199 levels for quantile-based CRPS
REF_GAUSS_S42 = 0.246750                                  # notebook Step 12, seed 42 (different seeding helper)


def dry_cut(dry):
    return max(dry, ZERO_TOL)


def relabel(y, dry):
    return np.where(y <= dry_cut(dry), 0.0, y)


# ---------- losses (y_pred columns are raw network outputs) ----------
def loss_gaussian(y, o):          # standardized target, as notebook gaussian_nll_loss
    y = tf.reshape(tf.cast(y, tf.float32), [-1])
    mu, lv = o[:, 0], o[:, 1]
    return tf.reduce_mean(0.5 * tf.exp(-lv) * tf.square(y - mu) + 0.5 * lv)


def loss_tobit(y, o):             # y in mm, dry already 0
    y = tf.reshape(tf.cast(y, tf.float32), [-1])
    mu, s = o[:, 0], tf.nn.softplus(o[:, 1]) + 1e-3
    z = (y - mu) / s
    log_pdf = -0.5 * tf.square(z) - tf.math.log(s) - 0.5 * np.log(2 * np.pi)
    log_cdf0 = tf.math.log(tf.clip_by_value(0.5 * tf.math.erfc(mu / s / np.sqrt(2.0)), 1e-12, 1.0))  # P(Y* <= 0)
    wet = tf.cast(y > 0, tf.float32)
    return -tf.reduce_mean(wet * log_pdf + (1 - wet) * log_cdf0)


def loss_bergamma(y, o):          # y in mm, dry already 0
    y = tf.reshape(tf.cast(y, tf.float32), [-1])
    p = tf.clip_by_value(tf.sigmoid(o[:, 0]), 1e-5, 1 - 1e-5)
    a = tf.nn.softplus(o[:, 1]) + 1e-2                 # shape
    b = tf.nn.softplus(o[:, 2]) + 1e-3                 # scale (mm)
    wet = tf.cast(y > 0, tf.float32)
    yw = tf.where(y > 0, y, tf.ones_like(y))
    log_gam = (a - 1) * tf.math.log(yw) - yw / b - a * tf.math.log(b) - tf.math.lgamma(a)
    return -tf.reduce_mean(wet * (tf.math.log(p) + log_gam) + (1 - wet) * tf.math.log(1 - p))


LOSS = {"gaussian": loss_gaussian, "tobit": loss_tobit, "bergamma": loss_bergamma}
NOUT = {"gaussian": 2, "tobit": 2, "bergamma": 3}


def build(dist, T, F, clipnorm):
    inputs = Input(shape=(T, F))
    h = Bidirectional(LSTM(64, return_sequences=True))(inputs)
    h = Dropout(0.2)(h)
    context, _ = qt.TemporalAttention(attn_units=64)(h)
    m = Model(inputs, Dense(NOUT[dist])(context), name=f"Prob_BiLSTM_Attention_{dist}")
    opt = Adam(learning_rate=0.001, clipnorm=clipnorm) if clipnorm else Adam(learning_rate=0.001)
    m.compile(optimizer=opt, loss=LOSS[dist])
    return m


# ---------- predictive summaries on the mm scale ----------
def sp(x):
    return np.log1p(np.exp(-np.abs(x))) + np.maximum(x, 0)      # stable softplus


def summarize(dist, o, y_mean, y_scale):
    """mean, median, quantile matrix (n x 199) and exceedance probabilities, all in mm."""
    o = o.astype("float64")
    lv = LEVELS[None, :]
    if dist == "gaussian":
        mu = o[:, 0] * y_scale + y_mean
        sd = np.sqrt(np.exp(o[:, 1])) * y_scale
        Q = mu[:, None] + sd[:, None] * norm.ppf(lv)
        exc = {k: norm.sf((t - mu) / sd) for k, t in EVENTS.items()}
        return {"mean": mu, "median": mu, "Q": Q, "exc": exc, "par": (mu, sd, np.full(len(mu), np.nan))}
    if dist == "tobit":
        mu, s = o[:, 0], sp(o[:, 1]) + 1e-3
        mean = norm.cdf(mu / s) * mu + s * norm.pdf(mu / s)          # E[max(Y*, 0)]
        Q = np.maximum(0.0, mu[:, None] + s[:, None] * norm.ppf(lv))
        exc = {k: norm.sf((t - mu) / s) for k, t in EVENTS.items()}
        return {"mean": mean, "median": np.maximum(0.0, mu), "Q": Q, "exc": exc,
                "par": (mu, s, np.full(len(mu), np.nan))}
    p = np.clip(1 / (1 + np.exp(-o[:, 0])), 1e-5, 1 - 1e-5)
    a, b = sp(o[:, 1]) + 1e-2, sp(o[:, 2]) + 1e-3
    cond = np.clip((lv - (1 - p[:, None])) / p[:, None], 0, 1 - 1e-9)
    Q = np.where(lv <= (1 - p[:, None]), 0.0, gamma_dist.ppf(cond, a[:, None], scale=b[:, None]))
    exc = {k: p * gamma_dist.sf(t, a, scale=b) for k, t in EVENTS.items()}
    return {"mean": p * a * b, "median": Q[:, list(LEVELS).index(0.5)], "Q": Q, "exc": exc, "par": (p, a, b)}


def crps_quantile(y, Q):
    d = y[:, None] - Q
    return float(np.mean(2 * np.mean(np.maximum(LEVELS * d, (LEVELS - 1) * d), axis=1)))


def qcol(lev):
    return list(LEVELS).index(lev)


def scores(y, s, dry):
    Q = s["Q"]
    lo95, hi95 = Q[:, qcol(0.025)], Q[:, qcol(0.975)]
    lo90, hi90 = Q[:, qcol(0.05)], Q[:, qcol(0.95)]
    IS = (hi95 - lo95) + (2 / 0.05) * ((lo95 - y) * (y < lo95) + (y - hi95) * (y > hi95))
    r = {"rmse": float(np.sqrt(np.mean((s["mean"] - y) ** 2))), "mae": float(np.mean(np.abs(s["mean"] - y))),
         "mae_median": float(np.mean(np.abs(s["median"] - y))),
         "r2": float(1 - np.sum((s["mean"] - y) ** 2) / np.sum((y - y.mean()) ** 2)),
         "neg_lower95": float(np.mean(lo95 < 0)), "max_pred_mean": float(s["mean"].max())}
    for k, t in EVENTS.items():
        o = (y > t) if k == "gt0.1" else (y >= t)
        r[f"brier_{k}"] = float(np.mean((s["exc"][k] - o) ** 2))
    for tag, mk in (("all", np.ones(len(y), bool)), ("dry", y <= dry_cut(dry)), ("wet", y >= WET), ("upper", y >= Q95)):
        r[f"n_{tag}"] = int(mk.sum())
        r[f"crps_{tag}"] = crps_quantile(y[mk], Q[mk])
        r[f"picp95_{tag}"] = float(np.mean((y[mk] >= lo95[mk]) & (y[mk] <= hi95[mk])))
        r[f"picp90_{tag}"] = float(np.mean((y[mk] >= lo90[mk]) & (y[mk] <= hi90[mk])))
        r[f"width95_{tag}"] = float(np.mean(hi95[mk] - lo95[mk]))
        r[f"is95_{tag}"] = float(np.mean(IS[mk]))
        r[f"above95_{tag}"] = float(np.mean(y[mk] > hi95[mk]))
    r["crps"] = r["crps_all"]
    return r


def tag_of(dist, dry, seed):
    return f"gaussian__s{seed}" if dist == "gaussian" else f"{dist}__dry{dry:g}__s{seed}"


def run_one(d, dist, dry, seed, epochs, clipnorm):
    tag = tag_of(dist, dry, seed)
    meta_path = f"{OUT}/runs/{tag}.json"
    if os.path.exists(meta_path):
        print(f"[skip] {tag}"); return
    y_mean, y_scale = float(d["y_mean"][0]), float(d["y_scale"][0])
    mm = {k: (d[f"y_{k}"].astype("float64") * y_scale + y_mean) for k in ("train", "val", "test")}
    if dist == "gaussian":
        ytr, yva = d["y_train"], d["y_val"]
    else:
        ytr, yva = (relabel(mm[k], dry).astype("float32") for k in ("train", "val"))
    qt.reset_seed(seed)
    m = build(dist, d["X_train"].shape[1], d["X_train"].shape[2], clipnorm)
    es = EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)
    t0 = time.time()
    hist = m.fit(d["X_train"], ytr, validation_data=(d["X_val"], yva), epochs=epochs, batch_size=32,
                 callbacks=[es, TerminateOnNaN()], verbose=2)
    sec = time.time() - t0
    vl = [float(v) for v in hist.history["val_loss"]]
    tl = [float(v) for v in hist.history["loss"]]
    finite = bool(np.all(np.isfinite(vl)) and np.all(np.isfinite(tl)))

    res, rows = {}, []
    for split in ("val", "test"):
        o = m.predict(d[f"X_{split}"], verbose=0, batch_size=1024)
        s = summarize(dist, o, y_mean, y_scale)
        y = mm[split]
        res[split] = {f"dry{e:g}": scores(relabel(y, e), s, e) for e in EVAL_DRY}
        rows.append(pd.DataFrame({"split": split, "valid_time": pd.to_datetime(d[f"t_{split}"]), "y_true": y,
                                  "y_pred_mean": s["mean"], "y_pred_median": s["median"],
                                  "q025": s["Q"][:, qcol(0.025)], "q05": s["Q"][:, qcol(0.05)],
                                  "q95": s["Q"][:, qcol(0.95)], "q975": s["Q"][:, qcol(0.975)],
                                  **{f"p_{k}": v for k, v in s["exc"].items()},
                                  "par1": s["par"][0], "par2": s["par"][1], "par3": s["par"][2]}))
    os.makedirs(f"{OUT}/preds", exist_ok=True); os.makedirs(f"{OUT}/runs", exist_ok=True)
    pd.concat(rows, ignore_index=True).to_csv(f"{OUT}/preds/{tag}.csv", index=False)
    json.dump({"tag": tag, "dist": dist, "train_dry_mm": None if dist == "gaussian" else dry, "zero_tol": ZERO_TOL,
               "clipnorm": clipnorm, "finite_losses": finite, "train_loss": tl, "val_loss": vl,
               "best_epoch": int(np.nanargmin(vl)) + 1, "epochs_trained": len(vl), "train_seconds": round(sec, 1),
               "val": res["val"], "test": res["test"], "gpu": qt.gpu_name(), "tf": tf.__version__,
               "host": socket.gethostname(), "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")},
              open(meta_path, "w"), indent=2)
    print(f"[done] {tag} | finite={finite} | best epoch {int(np.nanargmin(vl)) + 1}/{len(vl)} | {sec:.0f}s")
    for e in EVAL_DRY:
        t = res["test"][f"dry{e:g}"]
        print(f"   verify dry<={e:g}: RMSE {t['rmse']:.4f} CRPS {t['crps']:.4f} | PICP95 all/dry/wet/upper "
              f"{t['picp95_all']:.3f}/{t['picp95_dry']:.3f}/{t['picp95_wet']:.3f}/{t['picp95_upper']:.3f} | "
              f"IS95 all/upper {t['is95_all']:.3f}/{t['is95_upper']:.3f} | width95 all/upper "
              f"{t['width95_all']:.3f}/{t['width95_upper']:.3f} | negLB {t['neg_lower95']:.2f} | "
              f"BS >0.1/Q95/1.0 {t['brier_gt0.1']:.4f}/{t['brier_geQ95']:.4f}/{t['brier_ge1.0']:.4f}", flush=True)
    if dist == "gaussian" and seed == 42 and not SMOKE:
        t = res["test"]["dry0"]
        print(f"[ref] gaussian seed 42 RMSE {t['rmse']:.6f} vs notebook Step 12 {REF_GAUSS_S42} "
              f"(diff {t['rmse'] - REF_GAUSS_S42:+.6f}; Step 12 used its own seeding helper)")


def describe_targets(d):
    y = d["y_train"].astype("float64") * float(d["y_scale"][0]) + float(d["y_mean"][0])
    print(f"training targets (mm/h), n = {len(y)}:")
    edges = [-np.inf, -1e-6, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1, np.inf]
    lab = ["< -1e-6", "[-1e-6, 1e-7)", "[1e-7, 1e-6)", "[1e-6, 1e-5)", "[1e-5, 1e-4)", "[1e-4, 1e-3)",
           "[1e-3, 1e-2)", "[1e-2, 0.1)", ">= 0.1"]
    cnt = np.histogram(y, bins=edges)[0]
    for l_, c in zip(lab, cnt):
        print(f"   {l_:>15s}: {c:6d} ({c / len(y):.3f})")
    pos = np.unique(np.round(y[y > ZERO_TOL], 8))
    print("   smallest positive values above ZERO_TOL:", pos[:8])
    for e in EVAL_DRY:
        print(f"   share counted as dry with dry <= {e:g} (cut {dry_cut(e):g}): {np.mean(y <= dry_cut(e)):.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dists", nargs="+", default=DISTS, choices=DISTS)
    ap.add_argument("--dry", nargs="+", type=float, default=[0.01], help="training dry definition(s), mm/h")
    ap.add_argument("--seeds", nargs="+", type=int, default=SEEDS)
    ap.add_argument("--epochs", type=int, default=3 if SMOKE else 30)
    ap.add_argument("--clipnorm", type=float, default=None)
    ap.add_argument("--describe", action="store_true", help="only print the target distribution")
    a = ap.parse_args()
    d = dict(np.load(WIN, allow_pickle=False))
    print("GPU:", qt.gpu_name(), "| TF", tf.__version__, "| smoke" if SMOKE else "")
    describe_targets(d)
    if a.describe:
        sys.exit(0)
    for dist in a.dists:
        for dry in (a.dry if dist != "gaussian" else [None]):
            for seed in a.seeds:
                run_one(d, dist, dry, seed, a.epochs, a.clipnorm)
    print("===== q11 TRAIN JOB COMPLETE =====")
