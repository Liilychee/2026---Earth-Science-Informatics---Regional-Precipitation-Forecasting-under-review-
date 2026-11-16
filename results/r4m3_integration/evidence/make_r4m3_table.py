"""Build Supplementary strata table from archived q03e_convective_strata.csv (no recomputation of values)."""
import sys, pandas as pd
q = pd.read_csv(sys.argv[1]); out = sys.argv[2]
clim = q[q.Model == "Climatology (month x hour)"].set_index("Stratum").RMSE
S = [("all test", "All"), ("JJA (all hours)", "JJA"), ("non-JJA (all hours)", "Non-JJA"), ("wet", "Wet"),
     ("wet & convective-dominated", "Wet, conv."), ("wet & large-scale-dominated", "Wet, l.-s."),
     ("JJA & wet & convective-dominated", "JJA wet, conv."), ("JJA & wet & large-scale-dominated", "JJA wet, l.-s."),
     ("non-JJA & wet & convective-dominated", "Non-JJA wet, conv."), ("non-JJA & wet & large-scale-dominated", "Non-JJA wet, l.-s.")]
L = []
for m in ["XGBoost", "BiLSTM-Attention", "BU-LSTM-Attention (proposed)"]:
    L.append(r"\multicolumn{8}{@{}l}{\textbf{%s}}\\" % m.replace(" (proposed)", ""))
    t = q[q.Model == m].set_index("Stratum")
    for k, lab in S:
        r = t.loc[k]
        L.append(f"{lab} & {int(r.N):,} & ${r.Mean_obs_mm_h:.4f}$ & ${r.RMSE:.4f}$ & ${clim[k]:.4f}$ & ${r.Skill_vs_monthhour_clim:.3f}$ & ${r.RMSE_over_mean_obs:.3f}$ & ${r.Pearson_r:.3f}$\\\\".replace(",", "{,}"))
open(out, "w").write("\n".join(L) + "\n"); print("\n".join(L))
