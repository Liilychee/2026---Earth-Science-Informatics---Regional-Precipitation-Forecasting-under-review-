# R3-09 — seasonal predictor influence

Status: R3-09 local scientific revision complete — Git archiving deferred.

## Verified seasonal results
| Season | n | u10 rho / partial | v10 rho / partial | t2m rho | sp rho |
|---|---:|---:|---:|---:|---:|
| DJF | 4571 | -0.123 / -0.110 | 0.278 / 0.205 | 0.204 | -0.272 |
| MAM | 4784 | 0.039 / 0.003 | 0.200 / 0.150 | -0.054 | -0.459 |
| JJA | 4686 | -0.046 / -0.050 | 0.266 / 0.190 | -0.130 | -0.424 |
| SON | 4368 | -0.145 / -0.132 | 0.261 / 0.203 | 0.029 | -0.333 |

Original eleven-variable contemporaneous ranks: v10 seventh, u10 eleventh. Annual u10 lead rho=-0.058020. v10 bootstrap top-seven frequency is1.000 in original11,0.797 in expanded13; this is candidate-pool dependence, not a seasonal frequency. Historical drafts claiming unconditional0.80 are not reused.

q09 uses only first18,410 raw training times; last origin removed so18,409 target pairs remain. DJF/MAM/JJA/SON assigned by target month (not origin month). Counts reproduced using timestamps alone. Partial Spearman ranks each variable and target within season, regresses each rank on an intercept plus rank(tp(t)), correlates residuals. Code asserts no missing regional values; no validation/test values enter these associations. Seasonal correlation point estimates have no saved seasonal intervals or between-season tests: no significant seasonal contrasts are claimed. The prediction target remains the single hour ending six hours after the origin.

## Existing versus new evidence
Existing S25 selection tables and S26/S27 upstream tables do not present these seasonal predictor associations. Existing S9–S11 seasonal performance/training summaries concern model scores, not individual predictor contribution. Existing SHAP summaries are Random/Upper-tail, not season-specific.
Added S53 (stab:r3f_seasonal_associations), Supplementary p61:16 rows for u10/v10/t2m/sp across four seasons,48 directly indexed fields. Added S54 (stab:r3f_seasonal_v10_ablation), p62:8 rows for two models across four seasons,40 indexed fields. Total88 table fields; no old table overwritten and no new plot.
q13 provides genuine model-level seasonal evidence from existing q10 matched full/no_v10 five-seed predictions. Both models have5/5 positive effects in DJF/SON,0/5 positive in MAM; JJA intervals cross0. Each seasonal interval is pointwise seed-t(df4), not block-bootstrap and not the project's three-way robust result. No seasonal SHAP result was located in archived q09/q10/q13 outputs; no claim that it exists.

Independent check of all8 ablation rows from20 saved prediction files reproduces means, seed-t bounds and direction counts, max absolute difference1.0581813203458523e-16. q13 uses the common q14 XGBoost seed42 y_true, not q10's independently serialized target: an initial direct q10-y check differed at about1.6e-10; using the actual script's target source resolves this. Source identity is explicitly disclosed in S54. No formal intervals/metrics were replaced.

## Actual changes/protection
manuscript.tex: one red paragraph appended to §4.1 (p47) differentiates positive seasonal associations from conditional model effects and rejects tropical-origin inference. Original7 inputs unchanged.
Supplementary.tex: append S53/S54 after all prior content. Existing S1–S52 and Figures S1–S3 unchanged.
Response letter.tex: replace only Section3.2(f) pending response/location; add one exact blue excerpt. Red response/blue evidence retained. Other comments including R3-01–08 unchanged. Bibliography unchanged. No Git index changes, commit or push.
134 old RevisedExcerpts preserved exactly in order;135/135 current excerpts match main/Supplementary. See VERIFICATION.json and EXCERPT_INDEX.json.

## PDF verification
Built Supplementary→manuscript→response. Final pages62/101/86. Actual main47, Supp61–62, reply67–68 rendered and inspected: legible tables, no cropping/overlap, correct references/colors. No undefined citations/refs, duplicate labels, horizontal overflow or blocking errors. Main retains existing output vbox1.41457pt (100 occurrences for101-page output); no new warning type, Supp/reply no overfull warnings.

## Remaining scientific limits
Only descriptive seasonal association estimates, no seasonal contrast test; fixed chronological split; only2–3 realizations per test season; two ablated architectures; five seeds; seed-t intervals omit test-sampling uncertainty and are unadjusted for multiplicity. No trajectories, moisture-source or circulation composites; v10 is local wind direction, not proof of tropical air-mass origin. Positive seasonal correlations do not imply uniform model benefit. These limits are explicit rather than treated as missing experiments to be invented.

## Final English response (full LaTeX)

We distinguish seasonal statistical association from model-specific predictive contribution. Training-only q09 diagnostics pair $x(t)$ with hourly precipitation at $t+6$~h and assign DJF/MAM/JJA/SON by target valid time. v10 has positive lead-time Spearman correlations in every season (0.200--0.278), and positive rank-partial correlations controlling only current precipitation (0.150--0.205). These descriptive estimates support year-round association, not a stable year-round performance gain or formally tested seasonal contrasts (Supplementary Table~\ref{supp-stab:r3f_seasonal_associations}).

The original eleven-candidate contemporaneous screening ranked v10 seventh and u10 eleventh. The annual lead-time correlation of u10 is -0.058, but DJF and SON estimates are -0.123 and -0.145; MAM/JJA estimates are +0.039/-0.046. Thus annual screening can conceal season-specific signals and does not prove that zonal flow is physically unimportant. The previously reported v10 top-seven bootstrap frequency of 0.797 applies to the expanded thirteen-candidate lead-time pool; it is 1.000 in the original eleven-candidate pool. We retain the original seven model inputs and the existing R2-M3 analysis.

Saved q13 seasonal summaries of matched q10 ablations provide model-level evidence (Supplementary Table~\ref{supp-stab:r3f_seasonal_v10_ablation}). For both attention architectures, removing v10 increases DJF/SON RMSE in all five seeds, but decreases MAM RMSE in all five; JJA seed-t intervals include zero. For BiLSTM-Attention, the four seasonal mean differences are +0.005530, -0.002521, +0.000952 and +0.004268~mm\,h$^{-1}$. These pointwise seed-t intervals are not adjusted for multiple comparisons and do not capture test-sampling uncertainty; no seasonal ablation block-bootstrap intervals were saved. The short test period and two tested architectures limit generalization. We found seasonal ablation evidence, rather than a saved season-specific SHAP analysis.

Finally, v10 is a local meridional wind component, not an air-mass source label. We did not perform trajectory, moisture-source or circulation-composite analyses and cannot attribute its signal primarily to the tropics. The results therefore qualify the year-round interpretation without establishing a remote physical mechanism. We added a compact Results paragraph and two supplementary tables; previously closed analyses remain unchanged.
