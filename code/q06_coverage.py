# ============================================================
# Item 06, step 5: conditional interval reliability of the three probabilistic models
# in every test period (zero training).
#   periods : F1 2010-12, F2 2013-15, F3 2016-18, F4 2019-21 (25 y training), F4s 2019-21 (13 y)
#   models  : BU-LSTM, BU-LSTM-Attention, Probabilistic BiLSTM-Attention; 5 seeds each
#   subsets : all, wet (y >= 0.1 mm/h), upper (y >= training-period Q95 of the fold)
#   scores  : PICP of the central 95% and 90% Gaussian intervals, mean 95% width,
#             share of observations above / below the 95% interval, share of negative lower bounds
# Output: results/metrics/q06_conditional_coverage.csv (per seed),
#         q06_conditional_coverage_summary.csv (seed mean and SD)
# ============================================================
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from q06_common import ROOT, SEEDS, FOLDS

OUT, MET = f"{ROOT}/results/q06", f"{ROOT}/results/metrics"
PROB = {"bulstm": "BU-LSTM", "bulstm_attn": "BU-LSTM-Attention", "prob_bilstm_attn": "Probabilistic BiLSTM-Attention"}
Z95, Z90, WET = 1.959964, 1.644854, 0.1
PERIOD = {"F1": "2010-2012", "F2": "2013-2015", "F3": "2016-2018", "F4": "2019-2021 (25 y)", "F4s": "2019-2021 (13 y)"}
pd.set_option("display.width", 230)

rows = []
for f in FOLDS:
    q95 = json.load(open(f"{OUT}/folds/{f}.json"))["q95_train"]
    for m in PROB:
        for s in SEEDS:
            d = pd.read_csv(f"{OUT}/preds/{f}__{m}__s{s}.csv").query("split == 'test'")
            y, mu, sd = d.y_true.values, d.y_pred_mean.values, d.y_pred_std.values
            assert np.isfinite(sd).all() and (sd > 0).all(), f"{f} {m} {s}: missing sigma"
            lo95, hi95 = mu - Z95 * sd, mu + Z95 * sd
            for sub, mk in {"all": np.ones(len(y), bool), "wet": y >= WET, "upper": y >= q95}.items():
                yy = y[mk]
                rows.append({"fold": f, "period": PERIOD[f], "model": m, "seed": s, "subset": sub,
                             "threshold": {"all": np.nan, "wet": WET, "upper": q95}[sub], "n": int(mk.sum()),
                             "picp95": np.mean(np.abs(yy - mu[mk]) <= Z95 * sd[mk]),
                             "picp90": np.mean(np.abs(yy - mu[mk]) <= Z90 * sd[mk]),
                             "width95": np.mean(hi95[mk] - lo95[mk]),
                             "above95": np.mean(yy > hi95[mk]), "below95": np.mean(yy < lo95[mk]),
                             "neg_lower95": np.mean(lo95[mk] < 0)})
per = pd.DataFrame(rows)
per.to_csv(f"{MET}/q06_conditional_coverage.csv", index=False)
cols = ["picp95", "picp90", "width95", "above95", "below95", "neg_lower95"]
g = per.groupby(["fold", "period", "model", "subset", "n", "threshold"], dropna=False)[cols]
summ = g.mean().add_suffix("_mean").join(g.std(ddof=1).add_suffix("_sd")).reset_index()
summ.to_csv(f"{MET}/q06_conditional_coverage_summary.csv", index=False)

order = list(FOLDS)
for metric in ("picp95", "picp90", "width95", "above95"):
    print(f"\n===== {metric}: seed mean ± SD (nominal {'0.95' if metric == 'picp95' else '0.90' if metric == 'picp90' else '-'}) =====")
    for m, lab in PROB.items():
        t = summ[summ.model == m]
        cell = lambda r: f"{r[f'{metric}_mean']:.3f} ± {r[f'{metric}_sd']:.3f}"
        tab = t.assign(c=t.apply(cell, axis=1)).pivot(index="subset", columns="fold", values="c").loc[["all", "wet", "upper"], order]
        print(f"-- {lab} --"); print(tab.rename(columns=PERIOD).to_string())
print("\n===== subset sizes per period (upper threshold = training-period Q95 of each fold) =====")
print(summ[summ.model == "bulstm"].pivot(index="subset", columns="fold", values="n").loc[["all", "wet", "upper"], order]
      .rename(columns=PERIOD).to_string())
print("thresholds:", {f: round(json.load(open(f"{OUT}/folds/{f}.json"))["q95_train"], 4) for f in order})
print("===== q06 COVERAGE COMPLETE =====")
