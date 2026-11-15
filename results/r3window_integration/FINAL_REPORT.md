# R3-10 — rationale for the 30-hour input history

Status: R3-10 local scientific revision complete — Git archiving deferred.

## Actual original rationale / evidence boundary
W=6 is the original modelling specification: six snapshots at t0−30/24/18/12/6/0h, not30 consecutive hours. Neither a measured Dublin storm-passage-duration justification nor a specific literature recommendation or documented original systematic optimization was found. No independently verifiable pre-experimental selection record was found. The new Methods paragraph explicitly reports this, rather than converting task14's unconfirmed “a priori” draft into historical fact. Original choice history remains unknown; the scientific answer does not depend on inventing it.30h is not established as optimal.

## Verified existing sensitivity evidence
| Model | 30 h RMSE | 12 h RMSE | Paired seed delta | Improved seeds |
|---|---:|---:|---:|---:|
|XGBoost|0.243920|0.243002|-0.000919|4/5|
|BU-LSTM|0.246970|0.245500|-0.001470|3/5|
|BiLSTM-Attention|0.242864|0.241034|-0.001830|5/5|
|Transformer|0.259990|0.246793|-0.013196|5/5|
|BU-LSTM-Attention|0.247207|0.245143|-0.002064|4/5|
|Probabilistic BiLSTM-Attention|0.249369|0.246742|-0.002626|4/5|

Six-model comparison uses3939 common W6 test targets; W3 produces3942 available test targets but is scored on that intersection. The broader six-length comparison uses3933 common W12 targets, so its reused W3/W6 results differ slightly and are not independent replications. Training/validation counts vary withW. All100 unique saved prediction files and100 matching runJSONs checked, fixed seeds42/123/7/2024/99. Recomputed only existing point scores and seed-t intervals/directions from saved predictions: maximum difference2.314229537170309e-16; no new bootstrap run or model fit.
BiLSTM-Attention and XGBoost remain the best two under12/30h, but BU/BU-Attention switch positions, so “all rankings unchanged” is not used. Two-model curves: XGBoost best numerical test12h, best recorded native validation18h; BA best test/validation6h. BA42/66h improves numerically over30h, with both all-target intervals crossing0. Some wet/upper-tail pooled-error block intervals exclude0; “longer histories never help” would be false. The widest curve is only two models. Transformer30epoch budget remains an optimization confound.

## Uncertainty definition
Seed mean RMSE difference and its seed-tCI(df4) are distinct from differences of sqrt(seed-averaged squared errors) and their saved blockCI. Neither is RMSE of ensemble-mean predictions. S55 reports both point estimates; S56 explicitly defines its separate interval estimand. Blocks28,5000 replicates,seed42,non-circular;141 complete blocks without truncation=3948 draw positions, versus3939/3933 original targets. All intervals pointwise/unadjusted, no total combined interval, no equivalence claim. See METHOD_NOTES.md.

## Changes and tables
- manuscript.tex: append one red paragraph in §3.3(p18) documenting original-window evidence boundary/design; append one red result/limitations paragraph at end of §4.2(pp57–58). Existing main paragraph/figures/tables unchanged.
- Supplementary.tex: append S55 `stab:r3window_six_models`(p63),18 model/subset rows with both RMSE means/SDs, paired estimates, separate interval types and direction counts; S56 `stab:r3window_curve`(p64),12 configuration rows with validation/all-target means, intervals and direction counts. All294 printed numeric fields mapped to original CSV fields. Existing S1–S54 and all figure source/PDFs unchanged. No new plot needed. All curve wet/upper metrics retained in evidenceCSV; main question's six-model regime effects shown in S55.
- Response letter.tex: only R3 Lines329–333 response/location plus2exact blue excerpts. R3 Lines752–758 and other replies unchanged. Formal English response below.
- No bibliography changes. No model/data changes, staging, Git commit/push or next comment.

## SHAP interpretation
Existing q10 time-game summaries/S21–S22 reviewed. Approximate temporal attribution concentration toward recent snapshots is auxiliary conditional model evidence; fixed background and finite-permutation approximation do not establish storm lifetime, advection timescale or optimal window. No temporalSHAPCI or convergence is invented.

## Evidence and PDF checks
135 old excerpts preserved exactly in order.2new excerpts extracted from current main;137/137 match latest main/Supplementary. Other responses including R3-01–09 unchanged. See VERIFICATION/EXCERPT_INDEX.
Supplementary→main→reply builds passed. Final page counts64/102/86. Main18,57–58;Supp63–64;reply68–69 actually rendered and inspected. No undefined references/citations, duplicate labels, horizontal overflow, oversizedfloat or blockingerror. Existing1.41457pt output-vbox template warning persists (101 occurrences for102-page main); no new warning type. Red prose/captions and blue excerpts intact. Git index unchanged.

## Remaining limits
Original selection motivation/timing cannot be reconstructed from available evidence. Retrospective sensitivities use one fixed split and same training protocol, not matched training-sample counts or storm-adaptive histories. Other four models lack the full six-length curve. Window sensitivity has not been repeated across rolling folds. Separate interval estimands, nonstandard retained-full-block draw lengths and multiplicity limits are disclosed. No storm-duration inference is made. These limits are explicit; no blocking conflict with closed results was found.

## Final English response (full LaTeX)

We agree that the history length requires justification. The original specification used six snapshots at $t_0-30$, $t_0-24$, $t_0-18$, $t_0-12$, $t_0-6$ and $t_0$ hours, not thirty consecutive hourly inputs. We found no verifiable record linking that choice to measured storm-passage durations or a prior systematic window search. We therefore describe it as the original modelling setting, without claiming a physically determined or optimal window.

Existing sensitivity runs compare 12 h versus 30 h for six models on 3,939 common test targets, with five matched seeds and unchanged within-model hyperparameters/training protocol (Supplementary Table~\ref{supp-stab:r3window_six_models}). All six have lower mean RMSE with 12 h; BiLSTM-Attention changes from 0.2429 to 0.2410~mm\,h$^{-1}$. It and XGBoost retain the top two positions, but the BU-LSTM variants exchange positions. The extended two-model comparison uses histories of 6, 12, 18, 30, 42 and 66 h on 3,933 common targets; BiLSTM-Attention is numerically best at 6 h and XGBoost at 12 h (Supplementary Table~\ref{supp-stab:r3window_curve}). Thus 30 h is not established as optimal. Longer histories do not give a consistent all-target gain, although some numerical and subset improvements occur.

The tables distinguish paired seed-t intervals from block intervals based on seed-averaged squared errors; these are different estimands and all intervals are pointwise, without multiplicity adjustment. Training/validation sample counts vary with the window. Transformer optimization may also be constrained by the common epoch cap. The temporal SHAP summaries in Supplementary Tables~\ref{supp-stab:r1m4_temporal_bilstm_attn} and~\ref{supp-stab:r1m4_temporal_bulstm_attn} provide auxiliary model-level evidence of concentration toward recent snapshots, but cannot identify storm duration or the physical timescale of advection. We retain the original window for the main experiments and report its sensitivity explicitly.
