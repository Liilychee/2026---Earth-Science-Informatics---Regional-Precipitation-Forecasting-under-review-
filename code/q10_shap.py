# ============================================================
# Item 10 + 17: SHAP on the same five full models used in the ablation (q10_train.py).
#
# grouped  : exact Shapley values with 7 players, one per predictor (all six time steps
#            of a predictor move together). Same unit of analysis as leave-one-feature-out,
#            and no mixing of time steps within a predictor. 2^7 = 128 coalitions, exact.
# temporal : 42 players (6 time steps x 7 predictors), antithetic permutation sampling,
#            used only for the time-resolved figure (Fig. 6).
# Masking  : interventional; players outside the coalition take values from background
#            windows drawn at random from the training period.
# Samples  : all test windows with y >= Q95 (training-period threshold) plus 300 test
#            windows drawn at random from the whole test set (seed 42).
# Checks   : model predictions on the full test set must equal the saved predictions;
#            Shapley efficiency (sum of phi = f(x) - E f(background)) for every sample.
# Outputs  : results/q10/shap/<arch>__s<seed>__<method>.npz
# Usage    : python3 code/q10_shap.py --pilot
#            python3 code/q10_shap.py --method grouped --arch bilstm_attn bulstm_attn
#            python3 code/q10_shap.py --method temporal --arch bilstm_attn --n_perm 20
#            python3 code/q10_shap.py --method grouped_precip              (mxtpr+mntpr+lsp as one player)
#            python3 code/q10_shap.py --method grouped --config no_mxtpr_mntpr  (models without mxtpr, mntpr)
#            Results other than full-model grouped/temporal go to results/q10/shap_groups/
# ============================================================
import os, sys, argparse, itertools, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
import q10_train as qt          # determinism, GPU memory growth, model definitions
import tensorflow as tf

ROOT, FEATURES, SEEDS = qt.ROOT, qt.FEATURES, qt.SEEDS
OUT_MAIN, OUT_GROUPS = f"{ROOT}/results/q10/shap", f"{ROOT}/results/q10/shap_groups"
PRECIP = ("mxtpr", "mntpr", "lsp")
Q95, N_RANDOM, SAMPLE_SEED = 0.574048, 300, 42
N_BG = {"grouped": 100, "grouped_precip": 100, "temporal": 50}
BATCH = 16384
T, F = 6, 7

d = dict(np.load(qt.WIN, allow_pickle=False))
y_mean, y_scale = float(d["y_mean"][0]), float(d["y_scale"][0])
X_tr, X_te = d["X_train"], d["X_test"]
y_te = d["y_test"] * y_scale + y_mean

rng = np.random.default_rng(SAMPLE_SEED)
BG_IDX = {"grouped": rng.choice(len(X_tr), N_BG["grouped"], replace=False)}
BG_IDX["grouped_precip"] = BG_IDX["grouped"]
BG_IDX["temporal"] = BG_IDX["grouped"][:N_BG["temporal"]]          # nested: same first 50
rand_idx = rng.choice(len(X_te), N_RANDOM, replace=False)
upper_idx = np.where(y_te >= Q95)[0]
EXPLAIN = np.union1d(upper_idx, rand_idx)
IS_UPPER, IS_RANDOM = np.isin(EXPLAIN, upper_idx), np.isin(EXPLAIN, rand_idx)


def kept_features(config):
    return [f for f in FEATURES if f not in qt.removed_of(config)]


def make_predict(arch, seed, config="full"):
    keep = [FEATURES.index(f) for f in kept_features(config)]
    tf.keras.backend.clear_session()
    _, base = qt.build(arch, T, len(keep))
    base.load_weights(f"{ROOT}/results/q10/models/{arch}__{config}__s{seed}.weights.h5")
    fn = tf.function(lambda x: base(x, training=False), reduce_retracing=True)

    def predict(X):
        out = []
        for i in range(0, len(X), BATCH):
            o = fn(tf.constant(X[i:i + BATCH], dtype=tf.float32)).numpy()
            out.append(o[:, 0] if o.shape[-1] == 2 else o.ravel())
        return np.concatenate(out).astype("float64") * y_scale + y_mean

    saved = pd.read_csv(f"{ROOT}/results/q10/preds/{arch}__{config}__s{seed}.csv")
    saved = saved[saved["split"] == "test"]["y_pred_mean"].values
    diff = np.abs(predict(np.ascontiguousarray(X_te[:, :, keep])) - saved).max()
    print(f"[load] {arch} {config} seed {seed}: max |prediction - saved prediction| = {diff:.2e} mm")
    assert diff < 1e-4, "reloaded model does not reproduce the saved predictions"
    return predict


# ---------- exact grouped Shapley (one player per predictor, or per group of predictors) ----------
def shapley_tables(players, n_feat):
    M = len(players)
    masks = np.array(list(itertools.product([False, True], repeat=M)))   # [0]=empty, [-1]=full
    W = np.zeros((len(masks), M))
    for k, m in enumerate(masks):
        s = int(m.sum())
        for j in range(M):
            if m[j]:
                W[k, j] += math.factorial(s - 1) * math.factorial(M - s) / math.factorial(M)
            else:
                W[k, j] -= math.factorial(s) * math.factorial(M - s - 1) / math.factorial(M)
    fmask = np.zeros((len(masks), n_feat), bool)
    for k, m in enumerate(masks):
        for j, on in enumerate(m):
            if on:
                fmask[k, players[j]] = True
    return fmask, W


def grouped_phi(predict, X, bg, players=None, chunk=8):
    n_feat = X.shape[2]
    players = players or [[j] for j in range(n_feat)]
    fmask, W = shapley_tables(players, n_feat)
    phis, bases, fxs = [], [], []
    for i in range(0, len(X), chunk):
        x = X[i:i + chunk]
        comp = np.where(fmask[None, :, None, None, :], x[:, None, None], bg[None, None])
        v = predict(comp.reshape(-1, *X.shape[1:])).reshape(len(x), len(fmask), len(bg)).mean(2)
        phis.append(v @ W); bases.append(v[:, 0]); fxs.append(v[:, -1])
    return np.concatenate(phis), np.concatenate(bases), np.concatenate(fxs)


# ---------- temporal Shapley by antithetic permutation sampling (42 players) ----------
def temporal_phi(predict, X, bg, n_perm, seed, chunk=16):
    P = T * F
    prng = np.random.default_rng(seed)
    perms = []
    for _ in range(n_perm // 2):
        p = prng.permutation(P)
        perms += [p, p[::-1]]
    phi = np.zeros((len(X), P)); base = fx = None
    for i in range(0, len(X), chunk):
        x = X[i:i + chunk]
        acc = np.zeros((len(x), P))
        for p in perms:
            m = np.zeros((P + 1, P), bool)
            for k in range(1, P + 1):
                m[k] = m[k - 1]; m[k, p[k - 1]] = True
            m = m.reshape(P + 1, T, F)
            comp = np.where(m[None, :, None], x[:, None, None], bg[None, None])
            v = predict(comp.reshape(-1, T, F)).reshape(len(x), P + 1, len(bg)).mean(2)
            acc[:, p] += np.diff(v, axis=1)
        phi[i:i + chunk] = acc / len(perms)
        b, f = v[:, 0], v[:, -1]
        base = b if base is None else np.concatenate([base, b])
        fx = f if fx is None else np.concatenate([fx, f])
    return phi.reshape(len(X), T, F), base, fx


def out_path(arch, seed, method, config):
    if config == "full" and method in ("grouped", "temporal"):
        return f"{OUT_MAIN}/{arch}__s{seed}__{method}.npz"
    return f"{OUT_GROUPS}/{arch}__{config}__s{seed}__{method}.npz"


def save(arch, seed, method, phi, base, fx, n_perm, sec, config="full", player_names=None):
    path = out_path(arch, seed, method, config)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.savez_compressed(
        path, phi=phi, base=base, fx=fx, config=config,
        player_names=np.array(player_names if player_names is not None else FEATURES),
        explain_idx=EXPLAIN, is_upper=IS_UPPER, is_random=IS_RANDOM, y_true=y_te[EXPLAIN],
        X_explain=X_te[EXPLAIN], t_explain=d["t_test"][EXPLAIN], bg_idx=BG_IDX[method],
        features=np.array(kept_features(config)), method=method, arch=arch, seed=seed,
        n_bg=len(BG_IDX[method]), n_perm=n_perm, seconds=sec)


def run(arch, seed, method, n_perm, config="full"):
    path = out_path(arch, seed, method, config)
    if os.path.exists(path):
        print(f"[skip] {path}"); return
    kept = kept_features(config)
    keep = [FEATURES.index(f) for f in kept]
    predict = make_predict(arch, seed, config)
    X = np.ascontiguousarray(X_te[EXPLAIN][:, :, keep])
    bg = np.ascontiguousarray(X_tr[BG_IDX[method]][:, :, keep])
    names = kept
    assert method != "temporal" or config == "full", "temporal SHAP is only defined for the full model"
    t0 = time.time()
    if method in ("grouped", "grouped_precip"):
        players = None
        if method == "grouped_precip":
            players = [[kept.index(f) for f in PRECIP if f in kept]] + \
                      [[kept.index(f)] for f in kept if f not in PRECIP]
            names = ["precip"] + [f for f in kept if f not in PRECIP]
        phi, base, fx = grouped_phi(predict, X, bg, players)
        resid = np.abs(phi.sum(1) - (fx - base)).max()
    else:
        phi, base, fx = temporal_phi(predict, X, bg, n_perm, seed=SAMPLE_SEED)
        resid = np.abs(phi.sum((1, 2)) - (fx - base)).max()
    sec = time.time() - t0
    assert resid < 1e-6, f"efficiency check failed: {resid}"
    save(arch, seed, method, phi, base, fx, n_perm, sec, config, names)
    imp = np.abs(phi).mean(0) if phi.ndim == 2 else np.abs(phi).sum(1).mean(0)
    order = np.argsort(-imp)
    print(f"[done] {arch} {config} s{seed} {method}: {len(X)} samples, {sec:.0f}s, efficiency residual {resid:.1e}; "
          f"mean|phi| (mm): " + ", ".join(f"{names[j]} {imp[j]:.4f}" for j in order), flush=True)


def pilot():
    print("===== PILOT: bilstm_attn seed 42, 20 samples (10 upper-tail, 10 random) =====")
    sel = np.r_[np.where(IS_UPPER)[0][:10], np.where(IS_RANDOM & ~IS_UPPER)[0][:10]]
    X = X_te[EXPLAIN][sel]
    predict = make_predict("bilstm_attn", 42)
    t0 = time.time(); g, gb, gf = grouped_phi(predict, X, X_tr[BG_IDX["grouped"]]); tg = time.time() - t0
    print(f"grouped exact: {tg:.1f}s for 20 samples -> about {tg / 20 * len(EXPLAIN) / 60:.1f} min per model "
          f"for {len(EXPLAIN)} samples; efficiency residual {np.abs(g.sum(1) - (gf - gb)).max():.1e}")
    res = {}
    for K in (10, 40):
        t0 = time.time()
        res[K], b, f = temporal_phi(predict, X, X_tr[BG_IDX["temporal"]], K, seed=SAMPLE_SEED)
        tk = time.time() - t0
        print(f"temporal K={K}: {tk:.1f}s for 20 samples -> about {tk / 20 * len(EXPLAIN) / 60:.1f} min per model")
    a, b = res[10].ravel(), res[40].ravel()
    print(f"temporal K=10 vs K=40: correlation of per-sample values {np.corrcoef(a, b)[0, 1]:.3f}")
    for K in (10, 40):
        imp = np.abs(res[K]).sum(1).mean(0)
        print(f"  K={K} ranking: " + " > ".join(FEATURES[j] for j in np.argsort(-imp)))
    gi = np.abs(g).mean(0)
    print("  grouped ranking: " + " > ".join(FEATURES[j] for j in np.argsort(-gi)))
    print(f"Explain set: {len(EXPLAIN)} samples ({IS_UPPER.sum()} upper-tail, {IS_RANDOM.sum()} random, "
          f"{(IS_UPPER & IS_RANDOM).sum()} in both)")
    print("===== PILOT COMPLETE =====")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--method", choices=["grouped", "grouped_precip", "temporal"])
    ap.add_argument("--config", default="full", choices=qt.CONFIGS)
    ap.add_argument("--arch", nargs="+", choices=["bilstm_attn", "bulstm_attn"], default=["bilstm_attn", "bulstm_attn"])
    ap.add_argument("--seeds", nargs="+", type=int, default=SEEDS)
    ap.add_argument("--n_perm", type=int, default=20)
    a = ap.parse_args()
    if a.pilot:
        pilot()
    else:
        assert a.method, "--method is required"
        for arch in a.arch:
            for seed in a.seeds:
                run(arch, seed, a.method, a.n_perm, a.config)
        print("===== q10 SHAP JOB COMPLETE =====")
