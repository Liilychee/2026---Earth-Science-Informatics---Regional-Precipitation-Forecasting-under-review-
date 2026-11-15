# ============================================================
# Item 21 (R3 §3.2(b–d); R4 M3, m16) and the item-09 retrain on the main 70/15/15 split of 2004-2021.
# Same split, scaling, window (W = 6, 30 h), models, hyperparameters, seeds and determinism as q14q15_train.py
# (which follows q06_train.py / q10_train.py). Only the predictor set changes:
#   C0  original 7 (mxtpr, mntpr, lsp, tcc, v10, sp, d2m)  -- must reproduce the main study (seed 42)
#   C1  C0 + ws_dub                         (wind speed, per-gridpoint sqrt(u10²+v10²) then 5×5 mean)
#   C2  C0 + z500_dub, tcwv_dub             (500 hPa geopotential, raw; total column water vapour)
#   C3  C0 + U1 (52.75–53.75N, 10.5–7.0W: 7 original vars + ws) + U2 (50–57N, 20–7W: z500, tcwv)
#   C4  C0 + C1 + C2 + C3 additions
#   C5  C0 with tcc replaced in place by lcc_dub                     (R4 m16)
#   C6  C0 with d2m replaced in place by cp_dub (= tp − lsp, ≥ 0)    (item 09 lead-time selection)
#   C3a C0 + U1 only; C3b C0 + U2 only  -- exploratory, added after seeing C3 (run with --configs C3a C3b)
# New columns come from data/q21/q21_features_2004_2021.csv (q21_build_features.py), merged on valid_time.
# Outputs: results/q21/preds/<model>__w6__<cfg>__<loss>__s<seed>.csv  (val and test, mm)
#          results/q21/runs/<model>__w6__<cfg>__<loss>__s<seed>.json
# --check: build every requested config, print shapes / checks, no training (CPU is enough).
# Q21_SMOKE=1 -> results/q21_smoke, 2 epochs; never used for results.
# ============================================================
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import argparse, json, socket, time
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import q10_train as qt                       # same import order as q14q15_train.py: determinism set before TF
import q06_train as q6
import tensorflow as tf
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import StandardScaler
from q06_common import ROOT, FEATURES, TARGET, SEEDS, load_regional

SMOKE = bool(os.environ.get("Q21_SMOKE"))
OUT = f"{ROOT}/results/q21_smoke" if SMOKE else f"{ROOT}/results/q21"
FEAT_FILE = f"{ROOT}/data/q21/q21_features_2004_2021.csv"
MODELS = ["xgboost", "bilstm_attn"]
REPRO = {("xgboost", 42): 0.243750, ("bilstm_attn", 42): 0.242848}

ORIG = ["mxtpr", "mntpr", "lsp", "tcc", "v10", "sp", "d2m"]
assert list(FEATURES) == ORIG, f"q06_common.FEATURES 与原稿顺序不同：{FEATURES}"
U1 = ["mxtpr_u1", "mntpr_u1", "lsp_u1", "tcc_u1", "v10_u1", "sp_u1", "d2m_u1", "ws_u1"]
U2 = ["z500_up", "tcwv_up"]
CONFIGS = {
    "C0": ORIG,
    "C1": ORIG + ["ws_dub"],
    "C2": ORIG + ["z500_dub", "tcwv_dub"],
    "C3": ORIG + U1 + U2,
    "C4": ORIG + ["ws_dub", "z500_dub", "tcwv_dub"] + U1 + U2,
    "C5": [("lcc_dub" if f == "tcc" else f) for f in ORIG],
    "C6": [("cp_dub" if f == "d2m" else f) for f in ORIG],
    # 探索性（2026-11-09 在看到 C3 结果后追加，未预先设定）：拆分 C3 的上游增益来源
    "C3a": ORIG + U1,            # 只加 U1 陆上上游框
    "C3b": ORIG + U2,            # 只加 U2 大西洋框
}


def load_merged():
    """2004–2021 regional table of the main study + q21 features, merged on valid_time and checked."""
    df = load_regional()
    d = df[df["valid_time"].dt.year >= 2004].reset_index(drop=True)
    assert len(d) == 26300, len(d)
    f = pd.read_csv(FEAT_FILE, parse_dates=["valid_time"])
    assert len(f) == 26300 and f["valid_time"].is_unique, f"特征文件 {len(f)} 行"
    m = d.merge(f, on="valid_time", how="left", validate="one_to_one")
    assert len(m) == 26300
    assert (m["valid_time"].values == d["valid_time"].values).all(), "合并后时间顺序变了"
    assert (m["valid_time"].values == f["valid_time"].values).all(), "时间戳与特征文件不完全对齐"
    for c in ORIG + [TARGET]:
        assert np.array_equal(m[c].values, d[c].values), f"{c} 在合并后变了"
    return m


def split_data(m, features, window):
    """Original 70/15/15 split, scaler fit on train only (identical to q14q15_train.main_split_data)."""
    miss = [c for c in features if c not in m.columns]
    assert not miss, f"缺列：{miss}"
    assert not m[features + [TARGET]].isna().any().any(), "有缺失值"
    n = len(m)
    parts = {"train": m.iloc[:int(n * .70)], "val": m.iloc[int(n * .70):int(n * .85)], "test": m.iloc[int(n * .85):]}
    parts = {k: v.reset_index(drop=True) for k, v in parts.items()}
    xs, ys = StandardScaler(), StandardScaler()
    xs.fit(parts["train"][features]); ys.fit(parts["train"][[TARGET]])
    out = {}
    for k, p in parts.items():
        vx = xs.transform(p[features]).astype("float32")
        vy = ys.transform(p[[TARGET]]).ravel().astype("float32")
        t = p["valid_time"].values
        X = np.stack([vx[i:i + window] for i in range(len(p) - window)])
        out[k] = (X, vy[window:], t[window:], p[TARGET].values[window - 1:-1])     # last value = persistence
    out["y_mean"], out["y_scale"] = float(ys.mean_[0]), float(ys.scale_[0])
    return out


def run_one(d, cfg, features, model, window, seed, epochs):
    loss = "tree" if model == "xgboost" else "mse"
    tag = f"{model}__w{window}__{cfg}__{loss}__s{seed}"
    meta_path = f"{OUT}/runs/{tag}.json"
    if os.path.exists(meta_path):
        print(f"[skip] {tag}"); return
    (Xtr, ytr, _, _), (Xva, yva, tva, pva), (Xte, yte, tte, pte) = d["train"], d["val"], d["test"]
    inv = lambda a: np.asarray(a, dtype="float64").ravel() * d["y_scale"] + d["y_mean"]
    t0 = time.time()
    if model == "xgboost":
        import xgboost as xgb
        mdl = xgb.XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=6, subsample=0.8,
                               colsample_bytree=0.8, random_state=seed)
        mdl.fit(Xtr.reshape(len(Xtr), -1), ytr)
        pred = {"val": mdl.predict(Xva.reshape(len(Xva), -1)), "test": mdl.predict(Xte.reshape(len(Xte), -1))}
        best, ep = None, None
    else:
        qt.reset_seed(seed)
        mdl, kind = q6.build(model, Xtr.shape[1], Xtr.shape[2])
        assert kind != "nll"
        es = EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)
        hist = mdl.fit(Xtr, ytr, validation_data=(Xva, yva), epochs=epochs, batch_size=32, callbacks=[es], verbose=2)
        pred = {k: mdl.predict(X, verbose=0, batch_size=1024).ravel() for k, X in (("val", Xva), ("test", Xte))}
        vl = hist.history["val_loss"]; best, ep = int(np.argmin(vl)) + 1, len(vl)
    sec = time.time() - t0

    rows, met = [], {}
    for k, (y, t, p) in (("val", (yva, tva, pva)), ("test", (yte, tte, pte))):
        yt, yp = inv(y), inv(pred[k])
        rows.append(pd.DataFrame({"split": k, "valid_time": pd.to_datetime(t), "y_true": yt, "y_pred_mean": yp,
                                  "persistence": p}))
        met[k] = {"rmse": float(np.sqrt(np.mean((yp - yt) ** 2))), "mae": float(np.mean(np.abs(yp - yt))),
                  "r2": float(1 - np.sum((yp - yt) ** 2) / np.sum((yt - yt.mean()) ** 2))}
    os.makedirs(f"{OUT}/preds", exist_ok=True); os.makedirs(f"{OUT}/runs", exist_ok=True)
    pd.concat(rows, ignore_index=True).to_csv(f"{OUT}/preds/{tag}.csv", index=False)
    json.dump({"tag": tag, "config": cfg, "features": features, "n_features": len(features),
               "model": model, "window": window, "loss": loss, "seed": seed,
               "val": met["val"], "test": met["test"], "best_epoch": best, "epochs_trained": ep,
               "train_seconds": round(sec, 1), "n_train": int(len(Xtr)), "n_val": int(len(Xva)), "n_test": int(len(Xte)),
               "gpu": qt.gpu_name(), "tf": tf.__version__, "xgboost": __import__("xgboost").__version__,
               "host": socket.gethostname(), "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")},
              open(meta_path, "w"), indent=2)
    print(f"[done] {tag} | val RMSE={met['val']['rmse']:.6f} test RMSE={met['test']['rmse']:.6f} | "
          f"best epoch {best}/{ep} | {sec:.0f}s", flush=True)
    if cfg == "C0" and window == 6 and (model, seed) in REPRO and not SMOKE:
        ref = REPRO[(model, seed)]
        diff = met["test"]["rmse"] - ref
        print(f"[repro] {model} seed {seed} C0 W=6: {met['test']['rmse']:.6f} vs main study {ref} -> {diff:+.6f} "
              f"{'OK' if abs(diff) < 1e-5 else 'DIFFERENT'}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", nargs="+", default=[c for c in CONFIGS if c not in ("C3a", "C3b")], choices=list(CONFIGS))
    ap.add_argument("--models", nargs="+", default=MODELS, choices=MODELS)
    ap.add_argument("--window", type=int, default=6)
    ap.add_argument("--seeds", nargs="+", type=int, default=SEEDS)
    ap.add_argument("--epochs", type=int, default=2 if SMOKE else 30)
    ap.add_argument("--check", action="store_true", help="只构建数据并检查，不训练")
    a = ap.parse_args()
    m = load_merged()
    print(f"合并表 {m.shape}，{m['valid_time'].iloc[0]} 至 {m['valid_time'].iloc[-1]}，无缺失、时间戳对齐")
    for cfg in a.configs:
        feats = CONFIGS[cfg]
        d = split_data(m, feats, a.window)
        print(f"\n===== {cfg}（{len(feats)} 个变量）：{feats}\n  windows train/val/test = "
              f"{len(d['train'][0])}/{len(d['val'][0])}/{len(d['test'][0])}，X 形状 {d['train'][0].shape}", flush=True)
        if a.check:
            continue
        for model in a.models:
            for seed in a.seeds:
                run_one(d, cfg, feats, model, a.window, seed, a.epochs)
    print("===== q21 CHECK COMPLETE =====" if a.check else "===== q21 TRAIN JOB COMPLETE =====")
