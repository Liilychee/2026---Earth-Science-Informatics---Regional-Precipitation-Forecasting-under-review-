"""
q09_stability_check.py — R2-M3 / item 09, read-only: how stable is the lead-time selection of the original
seven predictors, for the original 11-candidate pool and for the 13-candidate pool of q09?

Reuses q09_lead_corr.py exactly (same regional series from data/04-24.csv, same training period of 18,410
times, same target tp(t+6h), same moving-block bootstrap: block 28, 2,000 resamples, seed 42, same random
draws), so the bootstrap replicates are identical to those behind q09_selection_table.csv.
Check: the per-variable top-7 frequencies of the 13-candidate pool must equal freq_top7_lead in
q09_selection_table.csv; otherwise the script stops.

Reported for each pool (11 = original candidates u10 v10 d2m t2m sp e mxtpr mntpr tcc ssr lsp;
13 = + ws, cp):
  * point-estimate top 7 by |rho_lead(k=0)| and the gap between ranks 7 and 8
  * frequency with which each candidate enters the top 7
  * frequency with which the top 7 is EXACTLY the original seven (set equality)
Read-only: data/04-24.csv is only read; only the two new output files below are written.
Run: cd /root/autodl-tmp && python3 code/q09_stability_check.py 2>&1 | tee results/metrics/q09_stability_check_output.txt
Output: results/metrics/q09_stability_check.csv
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q09_lead_corr as q  # noqa: E402

POOL11 = ["u10", "v10", "d2m", "t2m", "sp", "e", "mxtpr", "mntpr", "tcc", "ssr", "lsp"]
POOL13 = list(q.CANDS)
assert set(POOL11) < set(POOL13) and len(POOL13) == 13


def main():
    r = q.load_regional()
    tr = r.iloc[:q.N_TRAIN].copy()
    y = tr["tp"].shift(-1)
    m0 = y.notna()
    print(f"regional series {r.shape}; training times {len(tr)} ({tr.index[0]} to {tr.index[-1]}); "
          f"pairs with target {int(m0.sum())}")

    xs = {v: tr[v][m0].values for v in POOL13}
    yy = y[m0].values
    point = pd.Series({v: q.spearman(xs[v], yy) for v in POOL13})

    # identical bootstrap draws to q09_lead_corr.py (the partial correlations there use no random numbers)
    rng = np.random.default_rng(q.SEED)
    n = len(yy)
    nb = int(np.ceil(n / q.BLOCK))
    lead_bs = np.empty((q.NBOOT, len(POOL13)))
    for b in range(q.NBOOT):
        st = rng.integers(0, n - q.BLOCK + 1, nb)
        idx = (st[:, None] + np.arange(q.BLOCK)).ravel()[:n]
        for j, v in enumerate(POOL13):
            lead_bs[b, j] = q.spearman(xs[v][idx], yy[idx])

    # consistency with the archived q09 table
    ref = pd.read_csv(os.path.join(q.OUT, "q09_selection_table.csv"), index_col=0)
    top13 = np.argsort(-np.abs(lead_bs), axis=1)[:, :7]
    f13 = pd.Series([(top13 == j).any(axis=1).mean() for j in range(len(POOL13))], index=POOL13)
    assert np.allclose(f13.loc[ref.index], ref.freq_top7_lead, atol=1e-12), \
        "bootstrap does not reproduce q09_selection_table.csv"
    assert np.allclose(point.loc[ref.index], ref.rho_lead_k0, atol=1e-12)
    print("check: point estimates and 13-candidate top-7 frequencies reproduce q09_selection_table.csv exactly")

    rows, summ = [], []
    orig = set(q.ORIG7)
    for name, pool in (("11 candidates", POOL11), ("13 candidates", POOL13)):
        cols = [POOL13.index(v) for v in pool]
        sub = np.abs(lead_bs[:, cols])
        top = np.argsort(-sub, axis=1)[:, :7]
        freq = {v: float((top == k).any(axis=1).mean()) for k, v in enumerate(pool)}
        exact = float(np.mean([{pool[k] for k in row} == orig for row in top]))
        pt = point.loc[pool].abs().sort_values(ascending=False)
        top7_pt = list(pt.index[:7])
        gap = float(pt.iloc[6] - pt.iloc[7])
        summ.append({"pool": name, "n_candidates": len(pool), "point_top7": " ".join(top7_pt),
                     "point_top7_equals_original": set(top7_pt) == orig,
                     "rank7": pt.index[6], "rank8": pt.index[7], "gap_rank7_rank8": gap,
                     "freq_exact_original_set": exact, "n_boot": q.NBOOT})
        for v in pool:
            rows.append({"pool": name, "var": v, "in_original7": v in orig, "rho_lead_k0": point[v],
                         "freq_top7": freq[v]})
        print(f"\n===== {name} =====")
        print(f"point-estimate top 7: {top7_pt}  (equal to original seven: {set(top7_pt) == orig})")
        print(f"rank 7 {pt.index[6]} |rho| {pt.iloc[6]:.3f}; rank 8 {pt.index[7]} |rho| {pt.iloc[7]:.3f}; "
              f"gap {gap:.3f}")
        print(f"bootstrap: top 7 exactly equal to the original seven in {exact * 100:.1f}% of {q.NBOOT} "
              f"resamples")
        print("frequency of entering the top 7: " +
              ", ".join(f"{v} {freq[v]:.3f}" for v in sorted(pool, key=lambda v: -freq[v])))

    out = pd.concat([pd.DataFrame(summ).assign(table="summary"), pd.DataFrame(rows).assign(table="per_variable")],
                    ignore_index=True)
    out.to_csv(os.path.join(q.OUT, "q09_stability_check.csv"), index=False)
    print(f"\nsaved {os.path.join(q.OUT, 'q09_stability_check.csv')}\nCHECK COMPLETE")


if __name__ == "__main__":
    main()
