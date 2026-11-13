# ============================================================
# Item 25 (R1 M4, R4 m34): do correlation screening, SHAP and ablation rank the 7 predictors alike?
# CPU only, no training, reads existing CSVs; writes results/metrics/q25_rank_agreement.csv.
# Rankings compared (7 predictors: mxtpr, mntpr, lsp, tcc, v10, sp, d2m):
#   correlation (training period, item 09): |rho| contemporaneous, |rho| lead (x(t) vs tp(t+6h)),
#                                         |partial rho| lead given tp(t)
#   SHAP (item 10): mean|phi| grouped exact, seed mean, random 300 and upper-tail 238
#   ablation (item 10): mean dRMSE over seeds, all test samples and upper tail
# Kendall tau (scipy, tau-b) for every pair, per architecture.
# Run: cd /root/autodl-tmp && python3 code/q25_corr_vs_shap.py 2>&1 | tee results/metrics/q25_rank_agreement_output.txt
# ============================================================
import itertools, os, re
import pandas as pd
from scipy.stats import kendalltau

ROOT = "/root/autodl-tmp"
MET = f"{ROOT}/results/metrics"
FEAT = ["mxtpr", "mntpr", "lsp", "tcc", "v10", "sp", "d2m"]
pd.set_option("display.width", 220)

# ---------- correlation (q09) ----------
sel = pd.read_csv(f"{MET}/q09_selection_table.csv")
print("q09_selection_table columns:", list(sel.columns))
fcol = next(c for c in sel.columns if sel[c].astype(str).isin(FEAT).sum() >= 7)
sel = sel[sel[fcol].astype(str).isin(FEAT)].set_index(fcol)


def pick(pattern, exclude=r"rank|lo$|hi$|low|high|ci|freq|top"):
    cs = [c for c in sel.columns if re.search(pattern, c, re.I) and not re.search(exclude, c, re.I)]
    return cs[0] if cs else None


corr_cols = {"corr_contemporaneous": pick(r"contemp|same|rho0|rho_0|k0|sync"),
             "corr_lead": pick(r"^(rho_)?lead|lead_rho|rho_lead|lead$"),
             "corr_partial_lead": pick(r"partial")}
print("correlation columns used:", corr_cols)
SCORES = {}
for k, c in corr_cols.items():
    if c is None:
        print(f"  WARNING: no column found for {k}; skipped")
        continue
    SCORES[k] = sel.loc[FEAT, c].astype(float).abs()

# ---------- SHAP and ablation (q10) ----------
g = pd.read_csv(f"{MET}/q10_shap_global.csv")
a = pd.read_csv(f"{MET}/q10_ablation_summary.csv")
rows = []
for arch in ["bilstm_attn", "bulstm_attn"]:
    S = dict(SCORES)
    for sub in ["random", "upper"]:
        S[f"shap_{sub}"] = g[(g.arch == arch) & (g.subset == sub)].set_index("feature").loc[FEAT, "mean_abs_phi"]
    for sub, lab in [("all", "ablation_all"), ("upper_geQ95", "ablation_upper")]:
        S[lab] = a[(a.arch == arch) & (a.subset == sub)].set_index("removed").loc[FEAT, "dRMSE_mean"]
    print(f"\n===== {arch}: scores (higher = more important) =====")
    T = pd.DataFrame(S)
    print(T.round(4).to_string())
    print("ranks:\n" + T.rank(ascending=False).astype(int).to_string())
    for x, y in itertools.combinations(T.columns, 2):
        tau = kendalltau(T[x], T[y]).statistic
        rows.append({"arch": arch, "a": x, "b": y, "kendall_tau": tau})
R = pd.DataFrame(rows)
R.to_csv(f"{MET}/q25_rank_agreement.csv", index=False)
print("\n===== Kendall tau between rankings (7 predictors) =====")
print(R.pivot_table(index=["a", "b"], columns="arch", values="kendall_tau").round(3).to_string())
print("\nNote: with 7 items, tau steps are 1/21 (~0.048); tau has no sampling interval here (point comparison).")
print("===== q25 COMPLETE =====")
