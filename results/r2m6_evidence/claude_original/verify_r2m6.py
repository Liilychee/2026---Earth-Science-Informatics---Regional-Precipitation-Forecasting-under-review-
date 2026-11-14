# Read-only re-verification of item 11 / R2-M6 from saved q11 predictive parameters. No training, no scipy.
# Independent implementations: closed-form Gaussian CRPS; closed-form Bernoulli-gamma CRPS
# (point mass + gamma, Gneiting/Scheuerer gamma CRPS); Tobit CRPS by fine-grid integration.
import csv, json, math, os
import numpy as np

R = os.path.expanduser("~/Interpretable-BU-LSTM-for-Rainfall-Prediction-in-Dublin/esi_github/results")
SEEDS = [42, 123, 7, 2024, 99]
CFG = {"Gaussian": "gaussian", "Tobit": "tobit__dry0", "BG": "bergamma__dry0",
       "Tobit001": "tobit__dry0.001", "BG001": "bergamma__dry0.001"}
Q95, ZT = 0.574048, 1e-6


def erf(x):                                   # Abramowitz-Stegun 7.1.26, |err| < 1.5e-7
    s = np.sign(x); x = np.abs(x); t = 1 / (1 + 0.3275911 * x)
    yv = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * np.exp(-x * x)
    return s * yv


Phi = lambda z: 0.5 * (1 + erf(z / math.sqrt(2)))
phi = lambda z: np.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)


def gammainc(a, x):                           # regularized lower incomplete gamma P(a, x), scalar
    if x <= 0: return 0.0
    gln = math.lgamma(a)
    if x < a + 1:
        ap, s, d = a, 1 / a, 1 / a
        for _ in range(1000):
            ap += 1; d *= x / ap; s += d
            if abs(d) < abs(s) * 1e-14: break
        return s * math.exp(-x + a * math.log(x) - gln)
    b = x + 1 - a; c = 1e300; d = 1 / b; h = d
    for i in range(1, 1000):
        an = -i * (i - a); b += 2
        d = an * d + b; d = 1e-300 if abs(d) < 1e-300 else d
        c = b + an / c; c = 1e-300 if abs(c) < 1e-300 else c
        d = 1 / d; de = d * c; h *= de
        if abs(de - 1) < 1e-14: break
    return 1 - math.exp(-x + a * math.log(x) - gln) * h


Pv = np.vectorize(gammainc)


def load(pre, s):
    rows = [r for r in csv.DictReader(open(f"{R}/q11/preds/{pre}__s{s}.csv")) if r["split"] == "test"]
    f = lambda k: np.array([float(r[k]) if r[k] != "" else np.nan for r in rows])
    return [r["valid_time"] for r in rows], {k: f(k) for k in ("y_true", "y_pred_mean", "q025", "q05", "q95", "q975",
                                                              "p_gt0.1", "p_geQ95", "p_ge1.0", "par1", "par2", "par3")}


t0, d0 = load("gaussian", 42)
main = [r for r in csv.DictReader(open(os.path.expanduser("~/Downloads/prob_bilstm_attention_preds.csv"))) if r["split"] == "test"]
assert [r["valid_time"][:19] for r in main] == [t[:19] for t in t0]
print("max |y_true(q11) - y_true(main saved Prob BiLSTM-Attn)| =",
      float(np.max(np.abs(d0["y_true"] - np.array([float(r["y_true"]) for r in main])))))
y = np.where(d0["y_true"] <= ZT, 0.0, d0["y_true"])
print("n test", len(y), "| exact zeros", int((y == 0).sum()), "| |y-0.1|<1e-9:", int(np.sum(np.abs(y - 0.1) < 1e-9)),
      "| n(y>0.1)", int((y > 0.1).sum()), "n(y>=0.1)", int((y >= 0.1).sum()), "| n(y>=Q95)", int((y >= Q95).sum()))
D = {}
for lab, pre in CFG.items():
    for s in SEEDS:
        t, d = load(pre, s)
        assert t == t0 and np.abs(d["y_true"] - d0["y_true"]).max() == 0
        D[(lab, s)] = d
print("all 25 runs share the same 3,939 test times and targets")


def crps_gauss(y, mu, sd):
    z = (y - mu) / sd
    return sd * (z * (2 * Phi(z) - 1) + 2 * phi(z) - 1 / math.sqrt(math.pi))


def crps_bg(y, p, a, b):
    # X = 0 w.p. 1-p, Gamma(a, scale b) w.p. p.  CRPS = E|X-y| - 0.5 E|X-X'|
    Fa = Pv(a, y / b); Fa1 = Pv(a + 1, y / b)
    e_abs_g = y * (2 * Fa - 1) - a * b * (2 * Fa1 - 1) + 0 * y            # E|Y - y|
    e_gg = 2 * b / np.exp(np.vectorize(math.lgamma)(0.5) + np.vectorize(math.lgamma)(a) - np.vectorize(math.lgamma)(a + 0.5))  # E|Y-Y'| = 2b/B(1/2,a)
    e_abs = (1 - p) * y + p * e_abs_g
    e_xx = 2 * p * (1 - p) * a * b + p * p * e_gg
    return e_abs - 0.5 * e_xx


def crps_tobit(y, mu, s, hi=12.0, n=24001):
    z = np.linspace(0, hi, n); out = np.empty(len(y))
    for i in range(0, len(y), 200):
        F = Phi((z[None, :] - mu[i:i + 200, None]) / s[i:i + 200, None])
        H = (y[i:i + 200, None] <= z[None, :])
        out[i:i + 200] = np.trapz((F - H) ** 2, z, axis=1)
    return out


tw = {r["config"] + "|" + r["seed"]: r for r in csv.DictReader(open(f"{R}/metrics/q11_twcrps_per_seed.csv"))}
name = {"Gaussian": "Gaussian", "Tobit": "Tobit", "BG": "Bernoulli-gamma", "Tobit001": "Tobit (dry 0.001)",
        "BG001": "Bernoulli-gamma (dry 0.001)"}
CR = {}
print("\nexact CRPS (independent) vs q11_twcrps_per_seed.csv 'full'")
for lab in CFG:
    v = []
    for s in SEEDS:
        d = D[(lab, s)]
        if lab == "Gaussian":
            c = crps_gauss(y, d["par1"], d["par2"])
        elif lab.startswith("Tobit"):
            c = crps_tobit(y, d["par1"], d["par2"])
        else:
            c = crps_bg(y, d["par1"], d["par2"], d["par3"])
        CR[(lab, s)] = c; v.append(c.mean())
    ref = [float(tw[name[lab] + "|" + str(s)]["full"]) for s in SEEDS]
    print(f"  {lab:9s} {np.mean(v):.5f} ± {np.std(v, ddof=1):.5f} | archived {np.mean(ref):.5f} ± {np.std(ref, ddof=1):.5f} | max per-seed |diff| {np.max(np.abs(np.array(v) - ref)):.1e}")
g = np.mean([CR[("Gaussian", s)].mean() for s in SEEDS]); b_ = np.mean([CR[("BG", s)].mean() for s in SEEDS])
tb = np.mean([CR[("Tobit", s)].mean() for s in SEEDS])
print(f"  BG vs Gaussian {(b_ - g) / g:+.2%}; Tobit vs Gaussian {(tb - g) / g:+.2%}; BG vs Tobit {(b_ - tb) / tb:+.2%}")
mn = min((D[('Gaussian', s)]['par1'] - 6 * D[('Gaussian', s)]['par2']).min() for s in SEEDS)
print(f"  Gaussian: min(mu - 6 sd) = {mn:.3f} mm (archived integration lower limit -4 mm); max sd = {max(D[('Gaussian', s)]['par2'].max() for s in SEEDS):.3f}")

for s in SEEDS:
    d = D[("BG", s)]
    assert (d["par1"] > 0).all() and (d["par1"] < 1).all() and (d["par2"] > 0).all() and (d["par3"] > 0).all()
    assert (D[("Tobit", s)]["par2"] > 0).all() and (D[("Gaussian", s)]["par2"] > 0).all()
print("parameters valid in all runs: BG p in (0,1), shape>0, scale>0; Tobit/Gaussian sd>0")

# ---------- quantile, exceedance and mean consistency for BG (seed 42) ----------
d = D[("BG", 42)]; p, a, sc = d["par1"], d["par2"], d["par3"]
F975 = np.where(d["q975"] > 0, (1 - p) + p * Pv(a, d["q975"] / sc), np.nan)
print("\nBG seed 42: max |F(q975)-0.975| where q975>0:", float(np.nanmax(np.abs(F975 - 0.975))),
      "| q975==0 requires 1-p>=0.975:", bool(np.all((1 - p[d['q975'] == 0]) >= 0.975 - 1e-9)),
      "| q025==0 share:", float(np.mean(d["q025"] == 0)))
print("   max |p_geQ95 - p*(1-P(a,Q95/b))|:", float(np.max(np.abs(d["p_geQ95"] - p * (1 - Pv(a, Q95 / sc))))),
      "| max rel |mean - p*a*b|:", float(np.max(np.abs(d["y_pred_mean"] - p * a * sc) / (p * a * sc))))
dg = D[("Gaussian", 42)]
print("Gaussian seed 42: max |q975 - (mu+1.95996 sd)|:", float(np.max(np.abs(dg["q975"] - (dg["par1"] + 1.959963985 * dg["par2"])))),
      "| y_pred_mean == mu:", bool(np.allclose(dg["y_pred_mean"], dg["par1"])))

# ---------- interval scores and Brier from saved quantiles / probabilities ----------
summ = {}
for r in csv.DictReader(open(f"{R}/metrics/q11_summary.csv")):
    summ[r.get("config") or r[list(r)[0]]] = r
up, wet = y >= Q95, y >= 0.1
print("\nrecomputed seed means vs q11_summary.csv")
for lab, key in (("Gaussian", "Gaussian"), ("Tobit", "Tobit"), ("BG", "Bernoulli-gamma"), ("BG001", "Bernoulli-gamma (dry 0.001)")):
    acc = {}
    for s in SEEDS:
        d = D[(lab, s)]
        lo, hi, lo9, hi9 = d["q025"], d["q975"], d["q05"], d["q95"]
        cov, cov9 = (y >= lo) & (y <= hi), (y >= lo9) & (y <= hi9)
        IS = (hi - lo) + 40 * ((lo - y) * (y < lo) + (y - hi) * (y > hi))
        r = {"neg_lower95": np.mean(lo < 0), "picp95_all": cov.mean(), "picp95_wet": cov[wet].mean(),
             "picp95_upper": cov[up].mean(), "picp90_all": cov9.mean(), "picp90_upper": cov9[up].mean(),
             "width95_all": np.mean(hi - lo), "width95_upper": np.mean((hi - lo)[up]), "is95_all": IS.mean(),
             "is95_upper": IS[up].mean(), "above95_upper": np.mean(y[up] > hi[up]),
             "brier_gt0.1": np.mean((d["p_gt0.1"] - (y > 0.1)) ** 2), "brier_ge0.1_alt": np.mean((d["p_gt0.1"] - (y >= 0.1)) ** 2),
             "brier_geQ95": np.mean((d["p_geQ95"] - (y >= Q95)) ** 2), "brier_ge1.0": np.mean((d["p_ge1.0"] - (y >= 1.0)) ** 2),
             "rmse": np.sqrt(np.mean((d["y_pred_mean"] - y) ** 2)), "max_pred_mean": d["y_pred_mean"].max(),
             "crps_wet_exact": CR[(lab, s)][wet].mean(), "crps_upper_exact": CR[(lab, s)][up].mean()}
        for k, v in r.items():
            acc.setdefault(k, []).append(v)
    row = summ[key]; print(f"  {key}:")
    for k, v in acc.items():
        arc = row.get(k + "_mean")
        txt = f"   archived {float(arc):.4f}  diff {np.mean(v) - float(arc):+.1e}" if arc not in (None, "") else ""
        print(f"     {k:16s} {np.mean(v):.4f} ± {np.std(v, ddof=1):.4f}{txt}")

# ---------- exact-CRPS moving-block bootstrap (28, 5000, seed 42) on seed-averaged per-case scores ----------
n = len(y); rng = np.random.default_rng(42); nb = int(np.ceil(n / 28))
st = rng.integers(0, n - 28 + 1, size=(5000, nb)); idx = (st[:, :, None] + np.arange(28)).reshape(5000, -1)
print()
for a_, b2 in (("BG", "Gaussian"), ("Tobit", "Gaussian"), ("BG", "Tobit")):
    ca = np.mean([CR[(a_, s)] for s in SEEDS], 0); cb = np.mean([CR[(b2, s)] for s in SEEDS], 0)
    bd = ca[idx].mean(1) - cb[idx].mean(1)
    dd = np.array([CR[(a_, s)].mean() - CR[(b2, s)].mean() for s in SEEDS])
    h = 2.776445 * dd.std(ddof=1) / math.sqrt(5)
    print(f"exact CRPS {a_}-{b2}: {dd.mean():+.5f} seed-t [{dd.mean() - h:+.5f},{dd.mean() + h:+.5f}] "
          f"boot [{np.percentile(bd, 2.5):+.5f},{np.percentile(bd, 97.5):+.5f}] seeds better {int((dd < 0).sum())}/5")

print("\nrun metadata")
for lab, pre in CFG.items():
    js = [json.load(open(f"{R}/q11/runs/{pre}__s{s}.json")) for s in SEEDS]
    print(f"  {lab:9s} best {[j['best_epoch'] for j in js]} trained {[j['epochs_trained'] for j in js]} "
          f"tf {sorted(set(j['tf'] for j in js))} gpu {sorted(set(j['gpu'] for j in js))} clip {sorted(set(str(j['clipnorm']) for j in js))} "
          f"finite {all(j['finite_losses'] for j in js)} {min(j['finished_utc'] for j in js)}..{max(j['finished_utc'] for j in js)}")
